import csv,io,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from datetime import datetime,timedelta,timezone
from mirror import Store,DEFAULT
from portable import export_csv,parse_csv
from aerospace import parse_feed,daily_trivia

class PortableTests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory();self.store=Store(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def test_roundtrip_all_settings_and_credentials(self):
  self.store.mutate({'action':'settings','values':{'email_password':'ab,cd"ef\nΩ','theme':'blueprint'}})
  self.store.mutate({'action':'calendar','item':{'name':'Personal, school','url':'https://example.com/private-key','color':'#abcdef'}})
  self.store.mutate({'action':'complete','key':'hw','done':True})
  self.store.mutate({'action':'layout','page':'daily','layout':{'notes':dict(x=0,y=100,w=100,h=250)},'hidden':['clock']})
  exported=self.store.backup()
  with tempfile.TemporaryDirectory() as other:
   target=Store(other);target.import_backup(exported)
   self.assertEqual(target.config,self.store.config);self.assertEqual(target.password,self.store.password)
   self.assertEqual(Store(other).password,self.store.password)
 def test_invalid_import_does_not_change_anything(self):
  original=self.store.backup();bad={**DEFAULT,'theme':'invalid'}
  with self.assertRaises(ValueError):self.store.import_backup(export_csv(bad,'secret'))
  self.assertEqual(self.store.backup(),original)
 def test_previous_setup_retained(self):
  before=self.store.backup();self.store.import_backup(export_csv({**DEFAULT,'theme':'expanse'},'password'))
  self.assertEqual((Path(self.temp.name)/'settings.before-import.csv').read_text().splitlines(),before.splitlines())
 def test_password_clear_and_disabled_retention(self):
  self.store.mutate({'action':'settings','values':{'email_password':'save-me','email_enabled':False}})
  self.assertEqual(Store(self.temp.name).password,'save-me')
  self.store.mutate({'action':'settings','values':{'clear_email_password':True}})
  self.assertEqual(Store(self.temp.name).password,'')
 def test_credentials_never_leak_in_state(self):
  self.store.mutate({'action':'settings','values':{'email_password':'NOT-PUBLIC'}})
  self.assertNotIn('NOT-PUBLIC',json.dumps(self.store.state()))
  self.assertTrue(self.store.state()['config']['email_password_saved'])
 def test_failed_save_rolls_back_password(self):
  with patch.object(self.store,'save',side_effect=OSError('failed')):
   with self.assertRaises(OSError):self.store.mutate({'action':'settings','values':{'email_password':'bad-save'}})
  self.assertEqual(self.store.password,'')
 def test_legacy_json_migrates(self):
  with tempfile.TemporaryDirectory() as d:
   (Path(d)/'settings.json').write_text(json.dumps({**DEFAULT,'theme':'mirror','zip_code':'35801'}))
   migrated=Store(d);self.assertEqual(migrated.config['theme'],'minimal');self.assertEqual(migrated.config['zip_code'],'35801');self.assertTrue((Path(d)/'settings.csv').exists())
 def test_duplicate_rows_rejected(self):
  text=export_csv(DEFAULT,'')+'settings,theme,"""lcars"""\r\n'
  with self.assertRaises(ValueError):parse_csv(text)
 def test_bom_supported(self):self.assertEqual(parse_csv('\ufeff'+export_csv(DEFAULT,'p'))[1],'p')
 def test_wrong_type_rejected_without_partial_import(self):
  with self.assertRaises(ValueError):self.store.import_backup(export_csv({**DEFAULT,'calendars':'not a list'},''))
 def test_private_file_permissions(self):
  if os.name!='posix':self.skipTest('POSIX only')
  self.assertEqual(self.store.file.stat().st_mode&0o777,0o600)

class TriviaTests(unittest.TestCase):
 def setUp(self):
  self.now=datetime(2026,11,17,12,tzinfo=timezone.utc)
  self.raw=b'<rss><channel><item><title>NASA Tests Artemis Rocket Engines</title><link>https://www.nasa.gov/news/test/</link><pubDate>Mon, 16 Nov 2026 12:00:00 GMT</pubDate></item></channel></rss>'
 def test_feed_and_sourced_quiz(self):
  rows=parse_feed(self.raw);q=daily_trivia(rows,self.now)
  self.assertIn(q['answer'],q['title']);self.assertIn('________',q['masked']);self.assertEqual(q['source'],'NASA');self.assertFalse(q['older'])
 def test_same_day_stable(self):
  rows=parse_feed(self.raw);self.assertEqual(daily_trivia(rows,self.now),daily_trivia(rows,self.now+timedelta(hours=2)))
 def test_date_changes_question_selection(self):
  rows=parse_feed(self.raw);a=daily_trivia(rows,self.now);b=daily_trivia(rows,self.now+timedelta(days=1));self.assertNotEqual(a['day'],b['day']);self.assertNotEqual(a['answer'],b['answer'])
 def test_stale_news_labeled(self):self.assertTrue(daily_trivia(parse_feed(self.raw),self.now+timedelta(days=30))['older'])
 def test_future_article_not_shown(self):self.assertIsNone(daily_trivia(parse_feed(self.raw),self.now-timedelta(days=3)))
 def test_external_article_rejected(self):
  with self.assertRaises(ValueError):parse_feed(self.raw.replace(b'www.nasa.gov',b'evil.example'))
 def test_xml_entities_rejected(self):
  with self.assertRaises(ValueError):parse_feed(b'<!DOCTYPE rss>'+self.raw)
 def test_empty_feed_no_invented_trivia(self):self.assertIsNone(daily_trivia([],self.now))

if __name__=='__main__':unittest.main()
