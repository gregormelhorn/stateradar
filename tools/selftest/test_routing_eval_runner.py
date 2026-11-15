import hashlib,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import EvalError
from run_gepa_comparison import Experiment
from run_routing_label_eval import Run
class RunnerTest(unittest.TestCase):
 def test_launch_cap(self):
  r=Run.__new__(Run);r.calls=[{}]*8
  with patch.object(Experiment,'reserve_launch',return_value=None):
   with self.assertRaisesRegex(EvalError,'8 comparator call cap'):r.reserve_launch()
 def test_cost_cap(self):
  r=Run.__new__(Run);r.calls=[{'cost':{'total_usd_estimate':3}}]
  with patch.object(Experiment,'reserve_launch',return_value=None):
   with self.assertRaisesRegex(EvalError,'comparator soft cost cap'):r.reserve_launch()
 def test_frozen_source_change(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'x').write_text('old');h=hashlib.sha256(b'old').hexdigest();r=Run.__new__(Run);r.frozen={'x':h};r.dev_hash=None;(p/'x').write_text('new')
   with patch('run_routing_label_eval.ROOT',p):
    with self.assertRaisesRegex(EvalError,'input changed'):r.assert_frozen()
if __name__=='__main__':unittest.main()
