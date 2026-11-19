import unittest
from pathlib import Path

class StaticAssetTests(unittest.TestCase):
 def test_stylesheet_is_css_and_contains_dashboard_and_pairing_rules(self):
  css=(Path(__file__).resolve().parents[1]/'app/static/style.css').read_text()
  self.assertTrue(css.lstrip().startswith(':root{'))
  self.assertNotIn("'use strict'",css)
  for selector in ['#pair','#board','.widget','[hidden]']:
   self.assertIn(selector,css)
 def test_no_automatic_mode_command_or_shutdown_handoff(self):
  root=Path(__file__).resolve().parents[1]/'app'
  self.assertNotIn("['raw','0x30','0x30','0x01','0x01']",(root/'idrac.py').read_text())
  shutdown=(root/'mirror.py').read_text().split('except KeyboardInterrupt:pass')[-1]
  self.assertNotIn('restore_automatic',shutdown)
