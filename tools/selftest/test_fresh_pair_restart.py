import json,shutil,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_fresh_routing_pair as pair
SMOKE=Path(__file__).resolve().parents[2]/'docs/evidence/routing-fresh-pair/restart/blind-smoke'
class RestartTest(unittest.TestCase):
 def test_known_smoke_cost_is_prior(self):
  self.assertAlmostEqual(pair.restart_prior(SMOKE),.071886)
 def test_incomplete_usage_stops(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'smoke';shutil.copytree(SMOKE,p)
   j=json.loads((p/'usage-checkpoint.json').read_text());j['complete']=False;(p/'usage-checkpoint.json').write_text(json.dumps(j))
   with self.assertRaisesRegex(ValueError,'smoke'):pair.restart_prior(p)
 def test_changed_blind_usage_stops(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'smoke';shutil.copytree(SMOKE,p)
   u=next((p/'blind-output').glob('*.usage.json'));j=json.loads(u.read_text());j['output_tokens']+=100;u.write_text(json.dumps(j))
   with self.assertRaisesRegex(ValueError,'smoke'):pair.restart_prior(p)
if __name__=='__main__':unittest.main()
