import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import EvalError
from gepa_heldout_eval import check_splits, permit, train_feedback

class SplitTests(unittest.TestCase):
 def setUp(self): self.d={'train':['t1','t2'],'validation':['v'],'test':['h1','h2']}
 def test_good(self):check_splits(self.d)
 def test_overlap(self):
  self.d['test'].append('t1')
  with self.assertRaises(EvalError):check_splits(self.d)
 def test_empty(self):
  self.d['validation']=[]
  with self.assertRaises(EvalError):check_splits(self.d)
 def test_heldout_blocked(self):
  with self.assertRaises(EvalError):permit(self.d,'h1','optimization',False)
 def test_final_needs_freeze(self):
  with self.assertRaises(EvalError):permit(self.d,'h1','final',False)
 def test_validation_labels_never_reflect(self):
  with self.assertRaises(EvalError):train_feedback(self.d,[{'component':'v'}])
 def test_final_labels_never_reflect(self):
  with self.assertRaises(EvalError):train_feedback(self.d,[{'component':'h1'}])
 def test_train_reflection_allowed(self):train_feedback(self.d,[{'component':'t1'}])

if __name__=='__main__':unittest.main()
