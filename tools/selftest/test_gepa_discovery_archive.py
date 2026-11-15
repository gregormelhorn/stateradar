import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from verify_gepa_discovery import verify
from gepa_discovery_eval import EvalError

class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        source=ROOT/'docs/evidence/gepa-discovery'
        self.base=self.root/'docs/evidence/gepa-discovery'
        shutil.copytree(source,self.base)
        for name in json.loads((source/'runs/input-freeze.json').read_text()):
            src=ROOT/name; dest=self.root/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.copyfile(src,dest)
    def tearDown(self): self.temp.cleanup()
    def edit(self,relative,change):
        p=self.base/relative; value=json.loads(p.read_text());change(value);p.write_text(json.dumps(value))
    def test_complete(self):
        self.assertEqual(verify(self.root)['reviews'],11)
    def test_corrupt_review_rejected(self):
        self.edit('runs/review-009.json',lambda v:v['cases'].pop())
        with self.assertRaises(EvalError): verify(self.root)
    def test_missing_call_rejected(self):
        self.edit('runs/calls.json',lambda v:v.pop())
        with self.assertRaises(EvalError): verify(self.root)
    def test_incomplete_cost_rejected(self):
        self.edit('runs/calls.json',lambda v:v[0]['cost'].update(complete=False))
        with self.assertRaises(EvalError): verify(self.root)
    def test_summary_forgery_rejected(self):
        self.edit('runs/results.json',lambda v:v[0]['summary'].update(found=3))
        with self.assertRaises(EvalError): verify(self.root)
    def test_omitted_frozen_input_rejected(self):
        self.edit('runs/input-freeze.json', lambda v:v.pop(next(iter(v))))
        with self.assertRaises(EvalError): verify(self.root)
    def test_frozen_input_tamper_rejected(self):
        p=self.base/'fixed.md';p.write_text(p.read_text()+'tamper')
        with self.assertRaises(EvalError): verify(self.root)

if __name__=='__main__': unittest.main()
