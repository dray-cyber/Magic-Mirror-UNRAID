import sys,tempfile,unittest,json
from pathlib import Path
from unittest.mock import patch,MagicMock
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store
from services import fetch_calendar
class PrivateIcalTests(unittest.TestCase):
 def test_webcal_and_secret_backup(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Store(tmp);s.mutate({'action':'calendar','item':dict(name='Private',color='#ffffff',url='webcal://example.com/private.ics',auth_type='basic',auth_user='me',auth_password='private-password')})
   self.assertEqual(s.config['calendars'][0]['url'],'https://example.com/private.ics')
   self.assertNotIn('private-password',json.dumps(s.state()));self.assertIn('private-password',s.backup())
   self.assertEqual(Store(tmp).config['calendars'][0]['auth_password'],'private-password')
 def test_auth_request_modes(self):
  source=dict(url='https://example.com/feed',name='Private',color='#ffffff',auth_user='me',auth_password='pw',auth_token='token')
  for mode in ['none','basic','bearer']:
   response=MagicMock();response.__enter__.return_value=response;response.iter_content.return_value=[b'BEGIN:VCALENDAR\r\nVERSION:2.0\r\nEND:VCALENDAR\r\n']
   with patch('services.requests.get',return_value=response) as get:
    data,error=fetch_calendar({**source,'auth_type':mode},datetime.now(timezone.utc),14)
    self.assertIsNone(error);kwargs=get.call_args.kwargs
    if mode=='basic':self.assertEqual(kwargs['auth'],('me','pw'))
    elif mode=='bearer':self.assertEqual(kwargs['headers']['Authorization'],'Bearer token')
    else:self.assertNotIn('auth',kwargs);self.assertNotIn('Authorization',kwargs['headers'])
 def test_invalid_auth_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   s=Store(tmp)
   with self.assertRaises(ValueError):s.mutate({'action':'calendar','item':dict(name='Private',color='#ffffff',url='https://example.com/feed',auth_type='bearer',auth_token='bad\nheader')})
if __name__=='__main__':unittest.main()
