import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import run_fresh_routing_pair as pair

class RecoveryTest(unittest.TestCase):
 def test_runtime_cli_is_forwarded_to_both_arms(self):
  self.assertIn('CODEX_APP_RUNTIME_CLI_PATH',pair.pilot_env_vars('direct'))
  self.assertIn('CODEX_APP_RUNTIME_CLI_PATH',pair.pilot_env_vars('routed'))
  self.assertNotIn('DEEPSEEK_API_KEY',pair.pilot_env_vars('direct'))
 def test_failed_blind_is_not_priced_as_zero_while_controller_runs(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'blind-output';p.mkdir()
   (p/'001.jsonl').write_text(json.dumps({'type':'turn.failed','error':{'message':'model_not_found'}})+'\n')
   with self.assertRaisesRegex(ValueError,'blind.*unknown'):pair.blind_cost(Path(d))
 def test_inflight_blind_can_continue(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'blind-output';p.mkdir()
   (p/'001.jsonl').write_text(json.dumps({'type':'turn.started'})+'\n')
   self.assertEqual(pair.blind_cost(Path(d)),(0.0,True))
if __name__=='__main__':unittest.main()
