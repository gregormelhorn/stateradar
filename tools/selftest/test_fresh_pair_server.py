import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
SERVER=Path(__file__).resolve().parents[1]/'fresh_pair_server.py'
class ServerTest(unittest.TestCase):
 def test_direct_refuses_provider_even_if_parent_has_keys(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);(root/'pool').mkdir();(root/'pack/tools').mkdir(parents=True);(root/'logs').mkdir()
   request={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'command','arguments':{'argv':['python3','../pack/tools/local_models.py','--ledger','../routing.sqlite','flash','secret-check']}}}
   env=os.environ.copy();env['DEEPSEEK_API_KEY']='sentinel-secret';env['TYPESAFE_API_KEY']='sentinel-secret'
   p=subprocess.run([sys.executable,str(SERVER),'--serve-tools',str(root),'direct'],input=json.dumps(request)+'\n',text=True,capture_output=True,env=env,timeout=10)
   self.assertEqual(p.returncode,0,p.stderr);self.assertIn('providers are unavailable',p.stdout);self.assertNotIn('sentinel-secret',p.stdout+p.stderr)
if __name__=='__main__':unittest.main()
