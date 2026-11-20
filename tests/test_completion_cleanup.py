import unittest,tempfile,sys
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store
class CleanupTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.s=Store(self.tmp.name)
  self.s.mutate({'action':'calendar','item':dict(name='Tasks',url='https://example.com/feed',color='#ffffff',assignments=True)})
  self.s.config['schedule_past_days']=30
  self.id='calendar:'+self.s.config['calendars'][0]['id']
 def tearDown(self):self.tmp.cleanup()
 def event(self,key,days,all_day=False,assignment=True):
  due=datetime.now(ZoneInfo('America/Chicago'))-timedelta(days=days)
  return dict(key=key,title=key,start=due.isoformat(),end=(due+timedelta(hours=1)).isoformat(),assignment=assignment,all_day=all_day,source='Tasks',color='#ffffff')
 def test_checked_hidden_everywhere(self):
  self.s.data[self.id]=[self.event('done',-1)]
  self.s.mutate({'action':'complete','key':'done','done':True})
  state=self.s.state()
  for key in ['events','schedule_events','assignments']:self.assertEqual(state[key],[])
 def test_old_auto_completed_and_saved(self):
  self.s.data[self.id]=[self.event('old',8),self.event('recent',6)]
  state=self.s.state();self.assertEqual([x['key'] for x in state['assignments']],['recent'])
  self.assertTrue(Store(self.tmp.name).config['completed']['old'])
 def test_all_day_seven_days_kept(self):
  self.s.data[self.id]=[self.event('seven',7,True),self.event('eight',8,True)]
  self.assertEqual([x['key'] for x in self.s.state()['assignments']],['seven'])
 def test_regular_event_not_auto_completed(self):
  self.s.data[self.id]=[self.event('meeting',8,assignment=False)]
  self.assertEqual(len(self.s.state()['schedule_events']),1)
  self.assertNotIn('meeting',self.s.config['completed'])
if __name__=='__main__':unittest.main()
