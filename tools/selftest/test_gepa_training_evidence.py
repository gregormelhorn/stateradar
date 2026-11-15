import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import EvalError
from verify_gepa_training import verify_test_log, verify_expected_red, verify_pool_mapping, verify_trial_coverage, verify_prompt_and_events

class EvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.p=Path(self.temp.name)/'log.jsonl'
        self.rows=[{'Action':'run','Test':'TestA'},{'Action':'pass','Test':'TestA'},{'Action':'run','Test':'TestA'},{'Action':'pass','Test':'TestA'},{'Action':'pass','Package':'example'}]
        self.write()
    def tearDown(self):self.temp.cleanup()
    def write(self):self.p.write_text(''.join(json.dumps(r)+'\n' for r in self.rows))
    def test_good_nonempty(self):self.assertEqual(verify_test_log(self.p,{'TestA'},2),2)
    def test_missing_test(self):
        self.rows=[{'Action':'pass','Package':'example'}];self.write()
        with self.assertRaises(EvalError):verify_test_log(self.p,{'TestA'},2)
    def test_missing_repetition(self):
        self.rows=self.rows[2:];self.write()
        with self.assertRaises(EvalError):verify_test_log(self.p,{'TestA'},2)
    def test_missing_package_completion(self):
        self.rows=self.rows[:-1];self.write()
        with self.assertRaises(EvalError):verify_test_log(self.p,{'TestA'},2)
    def test_wrong_test_failure(self):
        self.rows=[{'Action':'run','Test':'TestB'},{'Action':'output','Test':'TestB','Output':'intended reason'},{'Action':'fail','Test':'TestB'},{'Action':'fail','Package':'example'}];self.write()
        with self.assertRaises(EvalError):verify_expected_red(self.p,'TestA','intended reason')
    def test_red_without_reason(self):
        self.rows=[{'Action':'run','Test':'TestA'},{'Action':'fail','Test':'TestA'},{'Action':'fail','Package':'example'}];self.write()
        with self.assertRaises(EvalError):verify_expected_red(self.p,'TestA','intended reason')
    def test_pool_mapping_drift(self):
        info={'segments':[{'file':'channel.go','input_first_line':2,'lines':1},{'file':'pool.go','input_first_line':5,'lines':1}]}
        with self.assertRaises(EvalError):verify_pool_mapping(info,'// BEGIN pinned channel.go\na\n\n// BEGIN pinned pool.go\nb\n','changed\n','b\n')
    def test_pool_mapping_line_number(self):
        info={'segments':[{'file':'channel.go','input_first_line':2,'lines':1},{'file':'pool.go','input_first_line':4,'lines':1}]}
        with self.assertRaises(EvalError):verify_pool_mapping(info,'// BEGIN pinned channel.go\na\n\n// BEGIN pinned pool.go\nb\n','a\n','b\n')
    def test_trial_missing_component(self):
        calls=[{'id':0,'category':'fixed-baseline','component':'a'}]
        trials=[{'component':'a','call_ids':[0]}]
        with self.assertRaises(EvalError):verify_trial_coverage(calls,trials,['a','b'])
    def test_trial_duplicate_call(self):
        calls=[{'id':0,'category':'fixed-baseline','component':'a'}]
        trials=[{'component':'a','call_ids':[0]},{'component':'a','call_ids':[0]}]
        with self.assertRaises(EvalError):verify_trial_coverage(calls,trials,['a','a'])
    def test_prompt_leak_rejected(self):
        with self.assertRaises(EvalError):verify_prompt_and_events('safe','safe\nSECRET',[])
    def test_forbidden_tool_event_rejected(self):
        with self.assertRaises(EvalError):verify_prompt_and_events('safe','safe',[{'item':{'type':'command_execution'}}])
    def test_correct_red(self):
        self.rows=[{'Action':'run','Test':'TestA'},{'Action':'output','Test':'TestA','Output':'intended reason'},{'Action':'fail','Test':'TestA'},{'Action':'fail','Package':'example'}];self.write()
        verify_expected_red(self.p,'TestA','intended reason')

if __name__=='__main__':unittest.main()
