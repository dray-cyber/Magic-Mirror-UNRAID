import tempfile,unittest,sys
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store
from services import parse_events
class ScheduleVisibilityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
  self.s.mutate({'action':'calendar','item':dict(name='Canvas',url='https://example.com/feed',color='#ffffff',assignments=True)})
  self.cal=self.s.config['calendars'][0];self.now=datetime.now(ZoneInfo('America/Chicago'))
 def tearDown(self):self.tmp.cleanup()
 def event(self,offset):
  start=self.now+timedelta(days=offset)
  return dict(key=str(offset),title='Task',start=start.isoformat(),end=(start+timedelta(hours=1)).isoformat(),assignment=True,all_day=False,source='Canvas',color='#ffffff')
 def test_hide_schedule_retains_assignment_and_csv(self):
  self.s.data['calendar:'+self.cal['id']]=[self.event(1)]
  self.s.mutate({'action':'calendar','item':{'id':self.cal['id'],'show_schedule':False}})
  self.assertEqual(self.s.state()['schedule_events'],[])
  self.assertEqual(len(self.s.state()['assignments']),1)
  self.assertFalse(Store(self.tmp.name).config['calendars'][0]['show_schedule'])
  self.s.mutate({'action':'calendar','item':{'id':self.cal['id'],'show_schedule':True}})
  self.assertEqual(len(self.s.state()['schedule_events']),1)
 def test_past_future_bounds_independent(self):
  self.s.mutate({'action':'settings','values':{'schedule_past_days':3,'schedule_future_days':2,'days':14}})
  self.s.data['calendar:'+self.cal['id']]=[self.event(i) for i in [-5,-2,1,8]]
  self.assertEqual([e['key'] for e in self.s.state()['schedule_events']],['-2','1'])
  self.assertEqual(len(self.s.state()['assignments']),4)
 def test_history_fetch_for_non_assignment_calendar(self):
  date=(self.now-timedelta(days=2)).strftime('%Y%m%dT120000')
  raw=f'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nBEGIN:VEVENT\r\nUID:past\r\nDTSTART:{date}\r\nSUMMARY:Past\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n'.encode()
  source={**self.cal,'assignments':False,'schedule_past_days':3}
  self.assertEqual(len(parse_events(raw,source,self.now,14)),1)
 def test_class_calendar_independent_of_schedule(self):
  self.s.data['calendar:'+self.cal['id']]=[self.event(1)]
  self.s.mutate({'action':'calendar','item':{'id':self.cal['id'],'class_times':True,'show_schedule':False}})
  self.assertEqual(len(self.s.state()['class_events']),1)
  self.assertEqual(self.s.state()['schedule_events'],[])
  self.assertTrue(Store(self.tmp.name).config['calendars'][0]['class_times'])
  self.s.mutate({'action':'calendar','item':{'id':self.cal['id'],'class_times':False}})
  self.assertEqual(self.s.state()['class_events'],[])
 def test_invalid_range_rejected(self):
  with self.assertRaises(ValueError):self.s.mutate({'action':'settings','values':{'schedule_past_days':-1}})
if __name__=='__main__':unittest.main()
