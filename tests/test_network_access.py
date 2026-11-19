import sys,unittest,tempfile,threading,json
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from mirror import dashboard_request_allowed,Store,Server

class NetworkAccessTests(unittest.TestCase):
 def test_tailscale_addresses_and_https(self):
  for host,origin in [('tower:8765','http://tower:8765'),('100.101.102.103:8765','http://100.101.102.103:8765'),('tower.tailnet.ts.net','https://tower.tailnet.ts.net'),('tower.tailnet.ts.net:443','https://tower.tailnet.ts.net'),('[fd7a:115c:a1e0::12]:8765','http://[fd7a:115c:a1e0::12]:8765'),('localhost:8765','http://localhost:8765')]:
   with self.subTest(host=host):self.assertTrue(dashboard_request_allowed(host,origin))
 def test_foreign_origin_and_unlisted_public_host_rejected(self):
  for host,origin in [('100.101.102.103:8765','https://evil.example'),('tower.tailnet.ts.net','https://other.tailnet.ts.net'),('tower.tailnet.ts.net','null'),('evil.example',None),('100.63.0.1',None),('user@localhost',None),('localhost/path',None)]:
   with self.subTest(host=host,origin=origin):self.assertFalse(dashboard_request_allowed(host,origin))
 def test_explicit_proxy_origin(self):
  self.assertTrue(dashboard_request_allowed('127.0.0.1:8765','https://mirror.example.com','https://mirror.example.com'))
  self.assertTrue(dashboard_request_allowed('mirror.example.com','https://mirror.example.com','https://mirror.example.com'))
  self.assertFalse(dashboard_request_allowed('mirror.example.com','https://wrong.example.com','https://mirror.example.com'))
 def test_tailscale_http_auth_and_actions(self):
  with tempfile.TemporaryDirectory() as tmp:
   store=Store(tmp);server=Server(('127.0.0.1',0),store);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
   try:
    base='http://127.0.0.1:'+str(server.server_port)
    headers={'Host':'tower.tailnet.ts.net','Origin':'https://tower.tailnet.ts.net','Authorization':'Bearer '+store.token}
    self.assertEqual(urlopen(Request(base+'/api/state',headers=headers),timeout=3).status,200)
    body=json.dumps({'action':'settings','values':{'theme':'blueprint'}}).encode()
    self.assertEqual(urlopen(Request(base+'/api/action',headers=headers,data=body),timeout=3).status,200)
    self.assertEqual(store.config['theme'],'blueprint')
    for change in [{'Authorization':'Bearer wrong'},{'Origin':'https://evil.example'}]:
     with self.assertRaises(HTTPError) as error:urlopen(Request(base+'/api/state',headers={**headers,**change}),timeout=3)
     self.assertEqual(error.exception.code,401)
   finally:server.shutdown();server.server_close()
