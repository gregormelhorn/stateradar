import copy
import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import EvalError
from gepa_training_catalog import validate_catalog, build_prompt, validate_independent_review

class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.root=Path(self.temp.name)
        (self.root/'s.go').write_text('package fixture\nfunc A() {}\n')
        digest=hashlib.sha256((self.root/'s.go').read_bytes()).hexdigest()
        self.c={'components':{'x':{'source':'s.go','cases':[{'id':'C1','kind':'historical_miss','question_required':False,'situation':'before','expected':'after','historical':'prior','evidence':[{'file':'s.go','line':2,'fragment':'func A()', 'sha256':digest}]}]}}}
    def tearDown(self):self.temp.cleanup()
    def test_valid(self): self.assertEqual(validate_catalog(self.c,self.root),1)
    def test_missing_case_evidence(self):
        self.c['components']['x']['cases'][0]['evidence']=[]
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root)
    def test_bad_fragment(self):
        self.c['components']['x']['cases'][0]['evidence'][0]['fragment']='fake source'
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root)
    def test_drifted_hash(self):
        self.c['components']['x']['cases'][0]['evidence'][0]['sha256']='0'*64
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root)
    def test_omitted_expected_case(self):
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root,{'C1','C2'})
    def test_duplicate_case(self):
        self.c['components']['x']['cases'].append(copy.deepcopy(self.c['components']['x']['cases'][0]))
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root)
    def test_parent_path(self):
        self.c['components']['x']['cases'][0]['evidence'][0]['file']='../s.go'
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root)
    def test_invalid_question_marker(self):
        self.c['components']['x']['cases'][0]['question_required']='false'
        with self.assertRaises(EvalError):validate_catalog(self.c,self.root)
    def test_review_missing_case(self):
        with self.assertRaises(EvalError):validate_independent_review(self.c,{'reviewer':'independent','cases':[]})
    def test_review_rejected_case(self):
        review={'reviewer':'independent','cases':[{'id':'C1','verdict':'reject','reason':'wrong'}]}
        with self.assertRaises(EvalError):validate_independent_review(self.c,review)
    def test_review_accepts_complete(self):
        review={'reviewer':'independent','cases':[{'id':'C1','verdict':'accepted','reason':'checked'}]}
        validate_independent_review(self.c,review)
    def test_prompt_only_contains_task_source_and_fixed(self):
        prompt=build_prompt('SOURCE ONLY\n','FIXED ONLY','TASK ONLY')
        self.assertIn('SOURCE ONLY',prompt);self.assertIn('FIXED ONLY',prompt);self.assertIn('TASK ONLY',prompt)
        self.assertNotIn('hidden expected',prompt)

if __name__=='__main__':unittest.main()
