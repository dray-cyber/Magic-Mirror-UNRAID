import copy,json,sys,tempfile,threading,time,unittest
from pathlib import Path
from datetime import datetime,timedelta,timezone
from unittest.mock import patch,MagicMock
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store,Server,DEFAULT,THEMES,assignment_summary,schedule_events,effective_display,fetch_alerts,fetch_radar,validate

class DashboardTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name);self.now=datetime(2026,11,16,12,tzinfo=ZoneInfo('America/Chicago'))
 def tearDown(self):self.temp.cleanup()
 def test_all_seven_themes_save(self):
  for theme in THEMES:
   self.store.mutate({'action':'settings','values':{'theme':theme}})
   self.assertEqual(Store(self.temp.name).config['theme'],theme)
 def test_unknown_theme_rejected(self):
  with self.assertRaises(ValueError):self.store.mutate({'action':'settings','values':{'theme':'bad'}})
 def test_invalid_zip_rejected(self):
  with self.assertRaises(ValueError):self.store.mutate({'action':'settings','values':{'zip_code':'ABC'}})
 def test_calendars_private_and_url_preserved(self):
  self.store.mutate({'action':'calendar','item':dict(name='Classes',url='https://example.com/private-secret',color='#aabbcc')})
  cal=self.store.config['calendars'][0]
  self.assertNotIn('url',self.store.public_config()['calendars'][0])
  self.store.mutate({'action':'calendar','item':{**cal,'url':'','name':'Updated'}})
  self.assertIn('private-secret',self.store.config['calendars'][0]['url'])
  self.store.mutate({'action':'calendar','item':{'id':cal['id']},'delete':True})
  self.assertEqual(self.store.config['calendars'],[])
 def test_calendar_insecure_url_rejected(self):
  with self.assertRaises(ValueError):self.store.mutate({'action':'calendar','item':dict(name='Bad',url='http://example.com/feed',color='#aabbcc')})
 def test_layout_save_reset_and_bounds(self):
  layout={'clock':{'x':0,'y':10,'w':33,'h':200}}
  self.store.mutate({'action':'layout','page':'daily','layout':layout,'hidden':['weather']})
  self.assertEqual(Store(self.temp.name).config['layouts']['daily'],layout)
  with self.assertRaises(ValueError):self.store.mutate({'action':'layout','page':'daily','layout':{'clock':{'x':99,'y':0,'w':50,'h':200}}})
  for preset in ['portrait','night','landscape']:
   self.store.mutate({'action':'preset','preset':preset});self.assertEqual(self.store.config['layouts'],{})
 def test_assignment_priorities(self):
  events=[]
  for key,delta in [('past',-2),('today',.1),('week',3),('later',10)]:
   events.append(dict(key=key,assignment=True,all_day=False,start=(self.now+timedelta(days=delta)).isoformat()))
  rows=assignment_summary(events,{},self.now)
  self.assertEqual([r['priority'] for r in rows],['overdue','today','week','later'])
  self.assertEqual(assignment_summary(events,{'past':True},self.now)[0]['priority'],'completed')
 def test_all_day_not_overdue_until_next_date(self):
  event=dict(key='x',assignment=True,all_day=True,start=self.now.replace(hour=0).isoformat())
  self.assertEqual(assignment_summary([event],{},self.now)[0]['priority'],'today')
 def test_class_schedule_building_room(self):
  item=dict(id='a',title='Calc',days=[0,2,4],time='13:00',end='14:00',building='Shelby',room='214')
  result=schedule_events([item],self.now)
  self.assertEqual(len(result),4);self.assertEqual(result[0]['location'],'Shelby • 214')
  self.assertEqual(datetime.fromisoformat(result[0]['start']).hour,13)
 def test_overnight_class(self):
  item=dict(id='a',title='Lab',days=[0],time='23:00',end='01:00')
  result=schedule_events([item],self.now)
  self.assertGreater(result[0]['end'],result[0]['start'])
 def test_night_schedule_cross_midnight(self):
  c=copy.deepcopy(DEFAULT)
  self.assertEqual(effective_display(c,None,[],[],self.now.replace(hour=23))['theme'],'warm-night')
  self.assertEqual(effective_display(c,None,[],[],self.now)['theme'],'lcars')
 def test_sunrise_sunset_and_stale_fallback(self):
  c=copy.deepcopy(DEFAULT)
  w={'timezone':'America/Chicago','daily':{'sunrise':['2026-11-16T06:20'],'sunset':['2026-11-16T16:40']}}
  self.assertTrue(effective_display(c,w,[],[],self.now.replace(hour=18))['night'])
  w['daily']['sunrise']=['2026-11-15T06:20']
  self.assertFalse(effective_display(c,w,[],[],self.now.replace(hour=18))['night'])
 def test_red_alert_overrides_night(self):
  c={**DEFAULT,'urgent_red':True}
  self.assertEqual(effective_display(c,None,[{'severity':'Severe'}],[],self.now.replace(hour=23))['theme'],'red-alert')
 def test_collection_crud_and_dates(self):
  entries={'countdowns':dict(title='Exam',target='2026-12-01T09:00'), 'classes':dict(title='Math',days=[0],time='09:00',end='10:00'), 'workshop':dict(title='Oil change',kind='Maintenance',due='2026-12-01'), 'manual_shipments':dict(title='Parts',stage='Ordered')}
  for collection,item in entries.items():
   self.store.mutate({'action':'item','collection':collection,'item':item});saved=self.store.config[collection][0]
   self.store.mutate({'action':'item','collection':collection,'item':{**saved,'title':'Updated'}})
   self.assertEqual(self.store.config[collection][0]['title'],'Updated')
   if collection=='countdowns':self.assertTrue(saved['target'].endswith('-06:00'))
   self.store.mutate({'action':'item','collection':collection,'item':saved,'delete':True});self.assertEqual(self.store.config[collection],[])
 def test_delivered_cleanup(self):
  self.store.config['manual_shipments']=[dict(id='old',title='Old',stage='Delivered',updated=(datetime.now(timezone.utc)-timedelta(days=5)).isoformat()),dict(id='new',title='New',stage='Delivered',updated=datetime.now(timezone.utc).isoformat())]
  self.assertEqual([s['id'] for s in self.store.state()['shipments']],['new'])
 def test_sensors_validation_and_transient_state(self):
  self.store.mutate({'action':'sensors','values':[{'name':'Oil','value':32,'unit':'psi'}]})
  self.assertEqual(self.store.state()['sensors'][0]['value'],32)
  with self.assertRaises(ValueError):self.store.mutate({'action':'sensors','values':[{'name':'x','value':{}}]})
 def test_stale_connection_flag(self):
  self.store.connections['weather']={'success':(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(),'error':None,'label':'Weather'}
  self.assertTrue(self.store.state()['connections']['weather']['stale'])
 def test_failed_refresh_retains_data_and_timestamp(self):
  self.store.record('weather','Weather',({'value':58},None));success=self.store.connections['weather']['success']
  self.store.record('weather','Weather',(None,'Offline'))
  self.assertEqual(self.store.data['weather'],{'value':58});self.assertEqual(self.store.connections['weather']['success'],success)
 def test_save_failure_rolls_back(self):
  with patch.object(self.store,'save',side_effect=OSError('disk')):
   with self.assertRaises(OSError):self.store.mutate({'action':'settings','values':{'theme':'expanse'}})
  self.assertEqual(self.store.config['theme'],'lcars')
 def test_demo_survives_theme_changes(self):
  store=Store(self.temp.name,True)
  store.mutate({'action':'settings','values':{'theme':'expanse'}})
  self.assertEqual(len(store.state()['assignments']),3) # Completed sample is hidden.
 def test_demo_never_refreshes_services(self):
  store=Store(self.temp.name,True)
  with patch('mirror.fetch_weather') as fetch:store.refresh();fetch.assert_not_called()
 def test_expired_alert_removed(self):
  self.store.data['alerts']=[{'expires':(datetime.now(timezone.utc)-timedelta(hours=1)).isoformat(),'severity':'Severe'}]
  self.assertEqual(self.store.state()['alerts'],[])
 def test_weather_alert_request(self):
  response=MagicMock();response.json.return_value={'features':[{'properties':{'event':'Watch','severity':'Moderate','expires':'2099-01-01T00:00:00+00:00'}}]}
  with patch('mirror.requests.get',return_value=response) as get:
   data,error=fetch_alerts({'latitude':34.7,'longitude':-86.5})
  self.assertIsNone(error);self.assertEqual(data[0]['event'],'Watch');self.assertEqual(get.call_args.kwargs['params']['point'],'34.7,-86.5')
 def test_radar_manifest_validation(self):
  response=MagicMock();response.json.return_value={'radar':{'past':[{'time':1,'path':'/v2/radar/12345'}]}}
  with patch('mirror.requests.get',return_value=response):
   data,error=fetch_radar({'latitude':34,'longitude':-86});self.assertIsNone(error)
   response.json.return_value={'radar':{'past':[{'time':1,'path':'/v2/radar/a9bf129c'}]}}
   self.assertIsNone(fetch_radar({'latitude':34,'longitude':-86})[1])
   response.json.return_value={'radar':{'past':[{'time':1,'path':'https://evil.example'}]}}
   self.assertIsNotNone(fetch_radar({'latitude':34,'longitude':-86})[1])
 def test_disabled_inputs_do_not_connect(self):
  with patch('mirror.fetch_news',return_value=([],None)),patch('mirror.fetch_weather') as w,patch('mirror.fetch_shipments') as e:
   self.store.refresh()
   for _ in range(100):
    if not self.store.busy:break
    time.sleep(.01)
   w.assert_not_called();e.assert_not_called()

class HTTPTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.temp=tempfile.TemporaryDirectory();cls.store=Store(cls.temp.name);cls.server=Server(('127.0.0.1',0),cls.store)
  cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start();cls.url='http://127.0.0.1:'+str(cls.server.server_port)
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();cls.temp.cleanup()
 def request(self,path,body=None,token=True,headers=None):
  h={'Authorization':'Bearer '+self.store.token} if token else {}
  h.update(headers or {})
  request=Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=h)
  return urlopen(request,timeout=3)
 def test_credentials_require_auth(self):
  with self.assertRaises(HTTPError) as caught:self.request('/api/credentials',token=False)
  self.assertEqual(caught.exception.code,401)
 def test_settings_credentials_visible_only_on_demand(self):
  self.store.mutate({'action':'settings','values':{'email_password':'settings-only-secret'}})
  self.store.mutate({'action':'email_account','item':dict(name='Test',host='imap.example.com',user='test@example.com',folder='INBOX',password='second-secret',enabled=False)})
  result=json.load(self.request('/api/credentials'))
  self.assertEqual(result['primary'],'settings-only-secret');self.assertIn('second-secret',result['accounts'].values())
  self.assertNotIn('settings-only-secret',self.request('/api/state').read().decode())
 def test_error_log_redaction_and_bound(self):
  self.store.password='never-log-me'
  self.store.log_error('Test','Failure never-log-me https://example.com/private')
  row=self.store.error_log[-1]
  self.assertNotIn('never-log-me',row['message']);self.assertNotIn('https://',row['message'])
  count=len(self.store.error_log);self.store.log_error('Test','Failure never-log-me https://example.com/private');self.assertEqual(len(self.store.error_log),count)
  for i in range(40):self.store.log_error('Test',str(i))
  self.assertEqual(len(self.store.error_log),30)
 def test_static_frontend_served(self):
  response=self.request('/',token=False);self.assertIn(b'Personal Operations',response.read())
 def test_state_requires_pairing_token(self):
  with self.assertRaises(HTTPError) as caught:self.request('/api/state',token=False)
  self.assertEqual(caught.exception.code,401)
 def test_backup_requires_token(self):
  with self.assertRaises(HTTPError) as caught:self.request('/api/backup',token=False)
  self.assertEqual(caught.exception.code,401)
 def test_backup_import_http_roundtrip(self):
  self.request('/api/action',{'action':'settings','values':{'theme':'blueprint','email_password':'test-backup-secret'}})
  saved=json.load(self.request('/api/backup'))['csv']
  self.assertIn('test-backup-secret',saved)
  self.assertNotIn('test-backup-secret',self.request('/api/state').read().decode())
  self.request('/api/action',{'action':'settings','values':{'theme':'minimal','clear_email_password':True}})
  self.request('/api/action',{'action':'import_csv','csv':saved})
  self.assertEqual(self.store.config['theme'],'blueprint')
  self.assertEqual(self.store.password,'test-backup-secret')
 def test_invalid_csv_http_rejected(self):
  previous=self.store.backup()
  with self.assertRaises(HTTPError) as caught:self.request('/api/action',{'action':'import_csv','csv':'invalid'})
  self.assertEqual(caught.exception.code,400)
  self.assertEqual(self.store.backup(),previous)
 def test_cross_origin_mutation_rejected(self):
  with self.assertRaises(HTTPError) as caught:self.request('/api/action',{'action':'settings','values':{'theme':'expanse'}},headers={'Origin':'https://evil.example'})
  self.assertEqual(caught.exception.code,401)
 def test_dns_rebinding_host_rejected(self):
  with self.assertRaises(HTTPError) as caught:self.request('/api/state',headers={'Host':'evil.example'})
  self.assertEqual(caught.exception.code,401)
 def test_phone_and_display_share_saved_settings(self):
  self.request('/api/action',{'action':'settings','values':{'theme':'mission-control','page':'workshop'}})
  response=json.load(self.request('/api/state'));self.assertEqual(response['config']['theme'],'mission-control');self.assertEqual(response['config']['page'],'workshop')
 def test_http_invalid_settings_returns_400(self):
  with self.assertRaises(HTTPError) as caught:self.request('/api/action',{'action':'settings','values':{'refresh':0}})
  self.assertEqual(caught.exception.code,400)
 def test_path_traversal_not_served(self):
  with self.assertRaises(HTTPError) as caught:self.request('/../settings.json')
  self.assertEqual(caught.exception.code,404)
 def test_secrets_not_in_state(self):
  self.request('/api/action',{'action':'calendar','item':{'name':'Test','url':'https://example.com/private-feed-secret','color':'#aabbcc'}})
  self.assertNotIn('private-feed-secret',self.request('/api/state').read().decode())

if __name__=='__main__':unittest.main()
