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

