import sys,unittest
from pathlib import Path
from unittest.mock import patch,MagicMock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from service_health import gmail_status,microsoft_status,fetch_service_health,GOOGLE,MICROSOFT
import requests

class ServiceHealthTests(unittest.TestCase):
 def test_google_ongoing_and_resolved(self):
  incident={'affected_products':[{'title':'Gmail'}],'status_impact':'SERVICE_DISRUPTION'}
  self.assertEqual(gmail_status([incident]),'degraded')
  self.assertEqual(gmail_status([{**incident,'end':'2026-11-19T10:00:00Z'}]),'operational')
  self.assertEqual(gmail_status([{'service_name':'Google Calendar'}]),'operational')
  with self.assertRaises(ValueError):gmail_status({})
 def test_microsoft_known_unknown(self):
  for source,expected in [('Available','operational'),('ServiceDegradation','degraded'),('new value','unknown')]:self.assertEqual(microsoft_status({'Status':source}),expected)
 def test_separate_vendor_health_and_reachability(self):
  def get(url,**kwargs):
   response=MagicMock(status_code=200)
   response.json.return_value=[] if url==GOOGLE else {'Status':'ServiceDegradation'}
   return response
  with patch('service_health.requests.get',side_effect=get):
   result=fetch_service_health()
  self.assertEqual(set(result),{'gmail','outlook','teams'})
  self.assertEqual(result['gmail']['status'],'operational')
  self.assertEqual(result['teams']['status'],'degraded')
  self.assertEqual(result['teams']['reachability'],'reachable')
  self.assertIn('broad',result['teams']['scope'])
 def test_timeout_is_unknown_not_healthy(self):
  with patch('service_health.requests.get',side_effect=requests.Timeout()):result=fetch_service_health()
  for row in result.values():
   self.assertEqual(row['status'],'unknown');self.assertEqual(row['reachability'],'unreachable')
