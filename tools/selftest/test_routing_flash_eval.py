import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from routing_flash_eval import score
class FlashAuditTest(unittest.TestCase):
 def setUp(self):
  self.c=[{'id':'A01','kind':'claim','statement':'claim','line':1,'fragment':'text'}];self.l={'checks':{'A01':{'expected':'supported'}}};self.r={'claims':{'A01':{'kind':'claim','statement':'claim','line':1,'fragment':'text','citation_check':'ok','jev':{'choice':'supported'}}},'questions':[]}
 def test_full(self):self.assertEqual(score(self.l,self.c,self.r)['matched'],1)
 def test_missing(self):self.r['claims']={};self.assertEqual(score(self.l,self.c,self.r)['missing'],['A01'])
 def test_changed_is_never_matched(self):self.r['claims']['A01']['statement']='different';self.assertEqual(score(self.l,self.c,self.r)['changed'],['A01'])
 def test_question_is_not_missing_or_accepted(self):self.r['claims']={};self.r['questions']=['A01: uncertain'];r=score(self.l,self.c,self.r);self.assertEqual(r['questions'],['A01']);self.assertEqual(r['missing'],[]);self.assertEqual(r['matched'],0)
 def test_duplicate_and_unknown_are_exposed(self):self.r['questions']=['A01: uncertain','Z99: extra'];r=score(self.l,self.c,self.r);self.assertEqual(r['duplicate_ids'],['A01']);self.assertEqual(r['unmapped_questions'],['Z99: extra'])
if __name__=='__main__':unittest.main()
