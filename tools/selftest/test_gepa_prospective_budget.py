import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import EvalError
from run_gepa_comparison import Experiment
from run_gepa_prospective import Prospective

class BudgetTests(unittest.TestCase):
 def test_launch_cap(self):
  s=Prospective.__new__(Prospective);s.calls=[{}]*12
  with patch.object(Experiment,'reserve_launch',return_value=None):
   with self.assertRaisesRegex(EvalError,'12-launch cap'):s.reserve_launch()
 def test_cost_cap(self):
  s=Prospective.__new__(Prospective);s.calls=[{'cost':{'total_usd_estimate':3}}]
  with patch.object(Experiment,'reserve_launch',return_value=None):
   with self.assertRaisesRegex(EvalError,'\\$3 soft cap'):s.reserve_launch()
if __name__=='__main__':unittest.main()
