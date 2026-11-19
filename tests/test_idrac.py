import unittest,sys,tempfile,json,time
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from idrac import parse_energy,parse_temperatures,parse_fans,fetch_idrac
from mirror import Store,DEFAULT
ENERGY='Statistic : Cumulative Energy Consumption\nStart Time : x\nFinish Time : y\nReading : 2128.3 kWh\nStatistic : System Peak Power\nPeak Reading : 3726 W'
class IdracTests(unittest.TestCase):
 def test_parser(self):
  self.assertEqual(parse_energy(ENERGY),2128.3)
  self.assertEqual(parse_temperatures('Inlet Temp | 4h | ok | 7.1 | 20 degrees C\nTemp | 0Eh | ok | 3.1 | 48 degrees C')[0]['celsius'],48)
  self.assertEqual(parse_fans('Fan1 | 4000 RPM')[0]['unit'],'RPM')
 def test_read_only_commands(self):
  c={**DEFAULT,'idrac_enabled':True,'idrac_host':'192.168.1.10','idrac_user':'monitor','idrac_password':'SECRET'}
  def run(args,**kwargs):
   self.assertNotIn('SECRET',args);self.assertIn('-E',args);self.assertFalse(kwargs['shell']);self.assertEqual(kwargs['env']['IPMI_PASSWORD'],'SECRET');self.assertNotIn('raw',args)
   return MagicMock(stdout=ENERGY if 'powermonitor' in args else 'CPU1 Temp | 48 degrees C' if 'temperature' in args else 'Fan1 | 4000 RPM')
  with patch('idrac.shutil.which',return_value='/usr/bin/ipmitool'),patch('idrac.subprocess.run',side_effect=run):
   data,error=fetch_idrac(c);self.assertIsNone(error);self.assertEqual(data['kwh'],2128.3)
 def test_secrets_and_persistence(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Store(tmp);s.mutate({'action':'settings','values':{'idrac_enabled':True,'idrac_host':'192.168.1.10','idrac_user':'monitor','idrac_password':'SECRET'}})
   self.assertNotIn('SECRET',json.dumps(s.state()));self.assertIn('SECRET',s.backup());self.assertEqual(Store(tmp).config['idrac_password'],'SECRET')
 def test_calendar_refresh_with_idrac_disabled(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(tmp)
   store.mutate({'action':'calendar','item':dict(name='Classes',url='https://example.com/calendar.ics',color='#ffffff',enabled=True)})
   failures=[]
   with patch('mirror.fetch_news',return_value=([],None)),patch('mirror.fetch_calendar',return_value=([],None)) as fetch,patch('threading.excepthook',side_effect=lambda error:failures.append(error)):
    store.refresh()
    for _ in range(200):
     if not store.busy:break
     time.sleep(.01)
    self.assertFalse(store.busy);self.assertEqual(failures,[])
    fetch.assert_called_once()
    key='calendar:'+store.config['calendars'][0]['id']
    self.assertIsNone(store.connections[key]['error'])
 def test_missing_tool(self):
  with patch('idrac.shutil.which',return_value=None):self.assertIn('unavailable',fetch_idrac({**DEFAULT,'idrac_enabled':True})[1])
if __name__=='__main__':unittest.main()



class FanControlTests(unittest.TestCase):
 def tearDown(self):
  import idrac
  idrac._controlled=None
 def test_fan_labels_are_not_readings(self):
  rows=parse_fans('Fan1 RPM | 30h | ok | 7.1 | 4200 RPM\nFan2 RPM | 31h | ok | 7.2 | 4400 RPM')
  self.assertEqual([r['value'] for r in rows],[4200,4400])
  self.assertEqual(parse_fans('Fan3 RPM | no reading'),[])
 def test_target_and_limit(self):
  from idrac import fan_target
  self.assertEqual(fan_target(DEFAULT,[48]),25)
  self.assertEqual(fan_target(DEFAULT,[80]),None)
  self.assertEqual(fan_target({**DEFAULT,'fan_gain':10},[74]),100)
 def test_write_percent_and_restore_on_sensor_failure(self):
  import idrac
  c={**DEFAULT,'idrac_enabled':True,'fan_control_enabled':True,'idrac_host':'192.168.1.10','idrac_user':'monitor','idrac_password':'SECRET'}
  with patch('idrac.command') as cmd:
   r=idrac.apply_control(c,[{'celsius':48}],[{'value':4200,'unit':'RPM'}])
   self.assertEqual(r['percent'],25)
   self.assertEqual(cmd.call_args.args[1][-1],'0x19')
   r=idrac.apply_control(c,[],[])
   self.assertEqual(r['mode'],'automatic');self.assertIsNone(idrac._controlled)
   self.assertEqual(cmd.call_args.args[1],['raw','0x30','0x30','0x01','0x01'])
 def test_command_failure_attempts_auto(self):
  import idrac
  c={**DEFAULT,'fan_control_enabled':True,'idrac_host':'192.168.1.10','idrac_user':'monitor','idrac_password':'SECRET'}
  with patch('idrac.command',side_effect=[None,RuntimeError('failure'),None]) as cmd:
   r=idrac.apply_control(c,[{'celsius':48}],[{'value':4200}]);self.assertEqual(r['mode'],'automatic');self.assertEqual(cmd.call_count,3)
 def test_disabling_restores_auto(self):
  import idrac
  idrac._controlled=dict(DEFAULT)
  with patch('idrac.command') as cmd:
   self.assertEqual(idrac.apply_control(DEFAULT,[],[])['mode'],'automatic');cmd.assert_called_once()


class FanApprovalTests(unittest.TestCase):
 def setUp(self):
  import idrac
  idrac._controlled=None;idrac._last_percent=None;idrac._pending=None;idrac._approved=50;idrac._denied=False;idrac._fingerprint=None
  self.config={**DEFAULT,'fan_control_enabled':True,'idrac_host':'192.168.1.10','idrac_user':'monitor','idrac_password':'SECRET'}
 def tearDown(self):self.setUp()
 def test_hold_approve_and_higher_request(self):
  import idrac
  with patch('idrac.command') as command:
   result=idrac.apply_control(self.config,[{'celsius':60}],[{'value':4200}])
   self.assertEqual(result['percent'],50);request=idrac.fan_approval();self.assertEqual(request['percent'],55)
   idrac.decide_fan(request['id'],True)
   self.assertEqual(idrac.apply_control(self.config,[{'celsius':60}],[{'value':4200}])['percent'],55)
   result=idrac.apply_control(self.config,[{'celsius':64}],[{'value':4200}]);self.assertEqual(result['percent'],50);self.assertEqual(idrac.fan_approval()['percent'],65)
 def test_deny_and_no_repeat_commands(self):
  import idrac
  with patch('idrac.command') as command:
   idrac.apply_control(self.config,[{'celsius':60}],[{'value':4200}]);idrac.decide_fan(idrac.fan_approval()['id'],False)
   before=command.call_count
   self.assertEqual(idrac.apply_control(self.config,[{'celsius':60}],[{'value':4200}])['percent'],50)
   self.assertIsNone(idrac.fan_approval());self.assertEqual(command.call_count,before)
 def test_emergency_auto_not_blocked(self):
  import idrac
  with patch('idrac.command') as command:
   idrac.apply_control(self.config,[{'celsius':60}],[{'value':4200}]);idrac.decide_fan(idrac.fan_approval()['id'],False)
   self.assertEqual(idrac.apply_control(self.config,[{'celsius':80}],[{'value':4200}])['mode'],'automatic')
   self.assertEqual(command.call_args.args[1],['raw','0x30','0x30','0x01','0x01'])
 def test_manual_mode_enabled_once_across_speed_changes(self):
  import idrac
  with patch('idrac.command') as command:
   idrac.apply_control(self.config,[{'celsius':48}],[{'value':4200}])
   idrac.apply_control(self.config,[{'celsius':50}],[{'value':4300}])
   idrac.apply_control(self.config,[{'celsius':50}],[{'value':4300}])
   commands=[call.args[1] for call in command.call_args_list]
   self.assertEqual(commands.count(['raw','0x30','0x30','0x01','0x00']),1)
   self.assertEqual(len(commands),3)
 def test_stale_decision_rejected(self):
  from idrac import decide_fan
  with self.assertRaises(ValueError):decide_fan('expired',True)
