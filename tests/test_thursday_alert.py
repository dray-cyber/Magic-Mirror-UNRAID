import unittest,sys,copy
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import DEFAULT,effective_display
class ThursdayTests(unittest.TestCase):
 def test_window_completion_and_restore(self):
  c=copy.deepcopy(DEFAULT);c['auto_night']=False
  now=datetime(2026,11,19,12,tzinfo=ZoneInfo('America/Chicago'))
  rows=[dict(start=f'2026-11-{day}T18:00:00-06:00',done=done,priority='later') for day,done in [(20,False),(21,False),(22,False),(22,True),(23,False)]]
  result=effective_display(c,None,[],rows,now)
  self.assertEqual(result['weekend_count'],3);self.assertEqual(result['theme'],'red-alert')
  self.assertEqual(effective_display(c,None,[],rows,now.replace(day=20))['theme'],'lcars')
  c['thursday_alert']=False;self.assertEqual(effective_display(c,None,[],rows,now)['weekend_count'],0)
 def test_manual_theme_preserves_alert_and_expires(self):
  c=copy.deepcopy(DEFAULT);c.update(theme='ocean',auto_night=False,manual_theme_day='2026-11-19')
  now=datetime(2026,11,19,12,tzinfo=ZoneInfo('America/Chicago'))
  rows=[dict(start='2026-11-20T18:00:00-06:00',done=False,priority='later')]
  result=effective_display(c,None,[],rows,now)
  self.assertEqual(result['theme'],'ocean')
  self.assertEqual(result['weekend_count'],1)
  c['manual_theme_day']='2026-11-18'
  self.assertEqual(effective_display(c,None,[],rows,now)['theme'],'red-alert')
if __name__=='__main__':unittest.main()
