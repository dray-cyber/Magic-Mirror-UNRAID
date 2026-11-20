import unittest,sys,tempfile,json
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store,DEFAULT,fetch_commutes
class RoutesTests(unittest.TestCase):
 def test_manual_theme_pauses_overrides(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(d);s.mutate({'action':'settings','values':{'theme':'blueprint','auto_night':True,'urgent_red':True}})
   state=s.state();self.assertEqual(state['display']['theme'],'blueprint');self.assertFalse(state['config']['auto_night']);self.assertFalse(state['config']['urgent_red'])
 def test_two_routes(self):
  c={**DEFAULT,'routes_key':'secret','commute_origin':'A','commute_destination':'B','school_origin':'C','school_destination':'D'}
  r=MagicMock();r.json.return_value={'routes':[{'duration':'1440s'}]}
  with patch('mirror.requests.post',return_value=r) as post:
   data,error=fetch_commutes(c)
   self.assertEqual(post.call_count,2);self.assertEqual(data['work']['minutes'],24)
   self.assertEqual(post.call_args.kwargs['json']['routingPreference'],'TRAFFIC_AWARE')
 def test_failure_and_empty(self):
  c={**DEFAULT,'commute_origin':'A','commute_destination':'B'}
  with patch('mirror.requests.post',side_effect=Exception('secret')):
   data,error=fetch_commutes(c);self.assertNotIn('secret',str(data));self.assertIn('error',data['work']);self.assertNotIn('school',data)
 def test_key_redaction_and_csv(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(d);s.mutate({'action':'settings','values':{'routes_key':'privatekey','school_origin':'A'}})
   self.assertNotIn('privatekey',json.dumps(s.state()));self.assertIn('privatekey',s.backup())
if __name__=='__main__':unittest.main()
