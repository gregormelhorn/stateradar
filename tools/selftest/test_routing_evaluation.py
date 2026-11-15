import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from routing_evaluation import check_splits,allow,reconcile
class RoutingEvalTest(unittest.TestCase):
 def setUp(self):self.m={'splits':{'dev':['a'],'heldout':['b']},'components':{'a':{'split':'dev'},'b':{'split':'heldout'}}}
 def test_overlap_rejected(self):
  self.m['splits']['heldout'].append('a')
  with self.assertRaises(ValueError):check_splits(self.m)
 def test_holdout_cannot_run_before_dev(self):
  with self.assertRaises(ValueError):allow(self.m,'b','heldout',False)
 def test_development_cannot_run_on_heldout(self):
  with self.assertRaises(ValueError):allow(self.m,'b','dev',False)
 def test_dev_and_heldout_order(self):
  allow(self.m,'a','dev',False);allow(self.m,'b','heldout',True)
 def test_disagreement_remains_open(self):
  p={'checks':{'x':{'expected':'supported'},'y':{'expected':'unclear'}}}
  r={'cases':[{'id':'x','verdict':'contradicted','reason':'reason'},{'id':'y','verdict':'unclear','reason':'reason'}]}
  result=reconcile(p,r);self.assertEqual(set(result['agreed']),{'y'});self.assertEqual(set(result['disputes']),{'x'})
 def test_missing_or_duplicate_review_rejected(self):
  p={'checks':{'x':{'expected':'supported'}}}
  for rows in ([],[{'id':'x','verdict':'supported','reason':'r'}]*2):
   with self.assertRaises(ValueError):reconcile(p,{'cases':rows})
if __name__=='__main__':unittest.main()
