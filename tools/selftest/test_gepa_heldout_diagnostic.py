import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import EvalError
from run_gepa_heldout import Heldout
from run_gepa_heldout_exploratory import Diagnostic

class CombinedBudgetTests(unittest.TestCase):
 def test_primary_calls_count_toward_cap(self):
  subject=Diagnostic.__new__(Diagnostic);subject.previous=[{}]*25;subject.calls=[]
  with patch.object(Heldout,'reserve_launch',return_value=None):
   with self.assertRaisesRegex(EvalError,'combined 25-launch cap'):subject.reserve_launch()
 def test_primary_cost_counts_toward_cap(self):
  subject=Diagnostic.__new__(Diagnostic);subject.previous=[{'cost':{'total_usd_estimate':6}}];subject.calls=[]
  with patch.object(Heldout,'reserve_launch',return_value=None):
   with self.assertRaisesRegex(EvalError,'combined \\$6 soft cap'):subject.reserve_launch()
if __name__=='__main__':unittest.main()
