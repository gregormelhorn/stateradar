import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from gepa_discovery_eval import EvalError
from verify_gepa_training import verify_archive

class TrainingArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        source=ROOT/'docs/evidence/gepa-training-catalog';self.base=self.root/'docs/evidence/gepa-training-catalog'
        shutil.copytree(source,self.base)
        for name in json.loads((source/'runs/input-freeze.json').read_text()):
            src=ROOT/name;dst=self.root/name;dst.parent.mkdir(parents=True,exist_ok=True)
            if not dst.exists():shutil.copyfile(src,dst)
    def tearDown(self):self.tmp.cleanup()
    def edit(self,rel,fn):
        p=self.base/rel; x=json.loads(p.read_text());fn(x);p.write_text(json.dumps(x))
    def test_complete(self):self.assertEqual(verify_archive(self.root)['reviewed_outputs'],10)
    def test_omitted_assessment_row(self):
        self.edit('runs/assessment.json',lambda x:x['case_results'].pop('G01'))
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_missing_review_case(self):
        self.edit('runs/review-000.json',lambda x:x['cases'].pop())
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_unreviewed_finding(self):
        self.edit('runs/review-000.json',lambda x:x['findings'].pop())
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_missing_trial(self):
        self.edit('runs/trials.json',lambda x:x.pop())
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_incomplete_cost(self):
        self.edit('runs/calls.json',lambda x:x[0]['cost'].update(complete=False))
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_missing_frozen_input(self):
        self.edit('runs/input-freeze.json',lambda x:x.pop(next(iter(x))))
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_false_partial_and_full(self):
        self.edit('runs/review-000.json',lambda x:x['cases'][0].update(partial=True))
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_prompt_tampering(self):
        p=self.base/'runs/calls/000-fixed-baseline-gobreaker/prompt.md';p.write_text(p.read_text()+'leak')
        with self.assertRaises(EvalError):verify_archive(self.root)
    def test_changed_combined_source_mapping(self):
        self.edit('pool-source/input-map.json',lambda x:x['segments'][0].update(input_first_line=3))
        with self.assertRaises(EvalError):verify_archive(self.root)

if __name__=='__main__':unittest.main()
