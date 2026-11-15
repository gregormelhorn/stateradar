import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa.core.result import GEPAResult
from gepa_selection import classify

class UpstreamTieTest(unittest.TestCase):
 def test_gepa_014_picks_first_among_ties_but_audit_exposes_both(self):
  result=GEPAResult(candidates=[{'review':'seed'},{'review':'candidate'}],parents=[[None],[0]],val_aggregate_scores=[2/3,2/3],val_subscores=[{},{}],per_val_instance_best_candidates={},discovery_eval_counts=[0,1])
  self.assertEqual(result.best_idx,0)
  self.assertEqual(classify(result.val_aggregate_scores),{'status':'tie','best':None,'tied':[0,1]})
if __name__=='__main__':unittest.main()
