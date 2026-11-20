import tempfile,time,unittest,json
from unittest.mock import patch
from pathlib import Path
from datetime import datetime,timezone
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import Store
from services import parse_shipment
from email.message import EmailMessage

def message(subject,body,**headers):
 m=EmailMessage();m['Subject']=subject;m['From']='orders@shop.example'
 for k,v in headers.items():m[k]=v
 m.set_content(body);return m.as_bytes()

class MultipleEmailTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def add(self,name='Second'):
  self.store.mutate({'action':'email_account','item':dict(name=name,host='imap.example.com',user=name+'@example.com',folder='INBOX',password='secret-'+name,enabled=True)})
  return self.store.config['email_accounts'][-1]['id']
 def test_multiple_accounts_backup_and_redaction(self):
  self.add();self.add('Third');backup=self.store.backup()
  self.assertIn('secret-Second',backup);self.assertNotIn('secret-Second',json.dumps(self.store.state()))
  self.assertEqual(len(Store(self.tmp.name).config['email_accounts']),2)
  self.store.import_backup(backup);self.assertEqual(self.store.config['email_accounts'][1]['password'],'secret-Third')
 def test_edit_keep_clear_disable_remove(self):
  id=self.add();self.store.mutate({'action':'email_account','item':{'id':id,'password':'','enabled':False}})
  self.assertEqual(self.store.config['email_accounts'][0]['password'],'secret-Second')
  self.store.mutate({'action':'email_account','item':{'id':id,'clear_password':True}})
  self.assertEqual(self.store.config['email_accounts'][0]['password'],'')
  self.store.mutate({'action':'email_account','item':{'id':id},'delete':True})
  self.assertEqual(self.store.config['email_accounts'],[])
 def test_independent_mailboxes_and_deduplication(self):
  a=self.add();b=self.add('Third')
  notice=dict(id='UPS:123',date=datetime.now(timezone.utc),status='In transit',carrier='UPS')
  with patch('mirror.fetch_news',return_value=([],None)),patch('mirror.fetch_shipments',return_value=([notice],None)) as fetch:
   self.store.refresh()
   for _ in range(200):
    if not self.store.busy:break
    time.sleep(.01)
   self.assertFalse(self.store.busy);self.assertEqual(fetch.call_count,2)
  self.assertIn('email:'+a,self.store.connections);self.assertIn('email:'+b,self.store.connections)
  self.assertEqual(len(self.store.state()['shipments']),1)
 def test_invalid_account_unchanged(self):
  before=self.store.backup()
  with self.assertRaises(ValueError):self.store.mutate({'action':'email_account','item':{'name':'Bad'}})
  self.assertEqual(before,self.store.backup())
 def test_rollback_on_save_failure(self):
  with patch.object(self.store,'save',side_effect=OSError):
   with self.assertRaises(OSError):self.add()
  self.assertEqual(self.store.config['email_accounts'],[])

class ShipmentFilterTests(unittest.TestCase):
 def test_real_shipment(self):
  self.assertEqual(len(parse_shipment(message('Your order has shipped','Tracking: 1Z999AA10123456784'),strict=True)),1)
 def test_marketing_without_tracking(self):
  self.assertEqual(parse_shipment(message('Free shipping this weekend','Shop our package deals'),strict=True),[])
 def test_marketing_with_tracking(self):
  self.assertEqual(parse_shipment(message('Free shipping sale','Your package shipped. Tracking: 1Z999AA10123456784'),strict=True),[])
 def test_tracking_alone_insufficient(self):
  self.assertEqual(parse_shipment(message('Your receipt','Tracking: 1Z999AA10123456784'),strict=True),[])
 def test_provider_spam_flag(self):
  self.assertEqual(parse_shipment(message('Your order shipped','Tracking: 1Z999AA10123456784',**{'X-Spam-Flag':'YES'}),strict=True),[])
 def test_block_sender_and_domain(self):
  raw=message('Your order shipped','Tracking: 1Z999AA10123456784')
  for rule in ['shop.example','orders@shop.example','example']:
   self.assertEqual(parse_shipment(raw,strict=True,blocked=rule),[])
  self.assertEqual(len(parse_shipment(raw,strict=True,blocked='other.example')),1)
 def test_relaxed_retains_unrecognized_notice(self):
  raw=message('Your package shipped','Check your account for details')
  self.assertEqual(parse_shipment(raw,strict=True),[])
  self.assertEqual(len(parse_shipment(raw,strict=False)),1)

if __name__=='__main__':unittest.main()
