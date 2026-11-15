"""Evaluator failure paths, including split leakage and correction laundering."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import gepa_eval as e
class Eval(unittest.TestCase):
 def setUp(self):
  self.public={'cases':[{'id':'A','claim':'claim'},{'id':'B','claim':'policy'}]}
  self.source='contract\nother line\n'
  self.report={'findings':[{'id':'A','verdict':'supported','line':1,'fragment':'contract','reason':'source','question':''},{'id':'B','verdict':'unspecified','line':2,'fragment':'other line','reason':'not defined','question':'OPEN: policy?'}],'corrections':[]}
  self.oracle={'A':{'verdict':'supported'},'B':{'verdict':'unspecified'}}
  self.dataset={'components':{n:{'family':n} for n in ('a','b','c')},'splits':{'train':['a'],'validation':['b'],'test':['c']}}
 def test_good(self):
  e.validate(self.report,self.public,self.source);self.assertEqual(e.score(self.report,self.oracle)['correct'],2)
 def test_missing(self):
  self.report['findings'].pop()
  with self.assertRaises(e.EvalError):e.validate(self.report,self.public,self.source)
 def test_duplicate(self):
  self.report['findings'][1]=self.report['findings'][0]
  with self.assertRaises(e.EvalError):e.validate(self.report,self.public,self.source)
 def test_fake_citation(self):
  self.report['findings'][0]['fragment']='fabricated'
  with self.assertRaises(e.EvalError):e.validate(self.report,self.public,self.source)
 def test_closed_unknown(self):
  self.report['findings'][1]['question']='resolved'
  with self.assertRaises(e.EvalError):e.validate(self.report,self.public,self.source)
 def test_unlogged_correction(self):
  changed=copy.deepcopy(self.report);changed['findings'][0]['verdict']='contradicted'
  with self.assertRaises(e.EvalError):e.validate(changed,self.public,self.source,self.report)
 def test_laundered_correction(self):
  self.report['corrections']=[{'id':'A','before':'contradicted','after':'supported'}]
  with self.assertRaises(e.EvalError):e.validate(self.report,self.public,self.source,copy.deepcopy(self.report))
 def test_wrong_verdict_is_not_green(self):
  self.report['findings'][0]['verdict']='contradicted'
  self.assertEqual(e.score(self.report,self.oracle)['correct'],1)
  self.assertEqual(e.score(self.report,self.oracle)['wrong'],['A'])
 def test_component_overlap(self):
  self.dataset['splits']['test']=['a']
  with self.assertRaises(e.EvalError):e.validate_splits(self.dataset)
 def test_family_overlap(self):
  self.dataset['components']['c']['family']='a'
  with self.assertRaises(e.EvalError):e.validate_splits(self.dataset)
 def test_test_is_never_optimization_input(self):
  for frozen in (False,True):
   with self.assertRaises(e.EvalError):e.check_access(self.dataset,'c','optimization',frozen)
 def test_no_final_before_freeze(self):
  with self.assertRaises(e.EvalError):e.check_access(self.dataset,'c','final',False)
 def test_final_after_freeze(self):e.check_access(self.dataset,'c','final',True)
if __name__=='__main__':unittest.main()
