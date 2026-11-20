import unittest,tempfile,sys
from pathlib import Path
from datetime import datetime,timedelta,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store
class ShipmentSettingsTests(unittest.TestCase):
 def test_delivery_assumption_and_age(self):
  with tempfile.TemporaryDirectory() as d:
   s=Store(d);s.config.update(assume_delivered_days=7,hide_delivered_days=3,email_days=30)
   now=datetime.now(timezone.utc)
   def notice(id,days):return dict(id=id,date=(now-timedelta(days=days)).isoformat(),status='In transit',carrier='UPS')
   s.data['email']=[notice('assumed',8),notice('hidden',12),notice('too-old',40),notice('recent',2)]
   rows={r['id']:r for r in s.state()['shipments']}
   self.assertEqual(set(rows),{'assumed','recent'});self.assertTrue(rows['assumed']['assumed_delivered']);self.assertEqual(rows['recent']['stage'],'Shipped')
   self.assertIsInstance(s.state()['local_ip'],str)
if __name__=='__main__':unittest.main()
