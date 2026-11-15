"""No spend after uncertain usage, cap exhaustion or frozen input drift."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_gepa_comparison import Experiment,EvalError
class Budget(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.e=Experiment(Path(self.tmp.name)/'run')
 def test_initial(self):self.e.reserve_launch()
 def test_unsettled_codex(self):
  self.e.calls=[{'cost':{'complete':False}}]
  with self.assertRaisesRegex(EvalError,'unsettled Codex'):self.e.reserve_launch()
 def test_unsettled_provider(self):
  self.e.budget.reserve('test',1)
  with self.assertRaisesRegex(EvalError,'unsettled provider'):self.e.reserve_launch()
 def test_cost_ceiling(self):
  self.e.calls=[{'cost':{'complete':True,'total_usd_estimate':10}}]
  with self.assertRaisesRegex(EvalError,'ceiling'):self.e.reserve_launch()
 def test_launch_limit(self):
  self.e.calls=[{}]*40
  with self.assertRaisesRegex(EvalError,'launch limit'):self.e.reserve_launch()
 def test_input_drift(self):
  self.e.frozen={}
  with self.assertRaisesRegex(EvalError,'inputs changed'):self.e.assert_frozen()
 def test_test_phase_forbidden(self):
  with self.assertRaises(EvalError):self.e.public('timer','optimization')
  with self.assertRaises(EvalError):self.e.public('timer','final')
if __name__=='__main__':unittest.main()
