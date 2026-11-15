import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_cost_sensitivity import flash_weekend_bounds
from gepa_eval import EvalError
class Rates(unittest.TestCase):
 def test_bounds(self):
  low,high=flash_weekend_bounds({'input_tokens':1_000_000,'output_tokens':1_000_000})
  self.assertAlmostEqual(low,.603);self.assertAlmostEqual(high,.75)
 def test_output_only(self):
  self.assertEqual(flash_weekend_bounds({'input_tokens':0,'output_tokens':1_000_000}),(.6,.6))
 def test_no_unknown_as_zero(self):
  with self.assertRaises(EvalError):flash_weekend_bounds({'input_tokens':None,'output_tokens':10})
if __name__=='__main__':unittest.main()
