#!/usr/bin/env python3
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finding_benchmark import audit

class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root/'report.md').write_text('A general copying concern.\n')
        self.anchor = {'file':'report.md','line':1,'quote':'A general copying concern.',
                       'sha256':hashlib.sha256((self.root/'report.md').read_bytes()).hexdigest()}
        self.spec = {'cases':[{'id':'B01','initial':'two targets','steps':['admit','replace','report'],
                              'outcome':'new target receives effect','proof':[self.anchor]}]}
        self.review = {'reviewer':'test fixture', 'scope':'synthetic', 'rows':[
            {'id':'B01','found':False,'correct':False,'tested':'none','rationale':'No sequence or effect.',
             'evidence':[self.anchor]}]}

    def test_empty_review_is_not_green(self):
        with self.assertRaisesRegex(ValueError, 'coverage'):
            audit(self.spec, {'rows': []}, self.root)

    def test_general_mention_stays_missing(self):
        result = audit(self.spec,self.review,self.root)
        self.assertEqual(result['correct'],0)
        self.assertEqual(result['missing'],['B01'])

    def test_complete_review_is_counted(self):
        row = self.review['rows'][0]
        row.update(found=True,correct=True,rationale='Explicit synthetic reviewer verdict.')
        result = audit(self.spec,self.review,self.root)
        self.assertEqual(result['correct'],1)
        self.assertEqual(result['missing'],[])

    def test_failed_test_cannot_supply_pass_evidence(self):
        row = self.review['rows'][0]
        row.update(tested='full',test_name='TestExample',test_evidence=[
            {**self.anchor,'quote':'func TestExample('},
            {**self.anchor,'quote':'{"Action":"fail","Test":"TestExample"}'}])
        with self.assertRaisesRegex(ValueError,'must pass the named test'):
            audit(self.spec,self.review,self.root)

    def test_complete_coverage_with_refuted_claim_is_rejected(self):
        self.review['rows'][0].update(found=True,correct=True)
        self.review['refuted_claims']=[{'case':'B01','rationale':'Contradictory statement remains.',
                                       'evidence':[self.anchor]}]
        spec=self.root/'spec.json';review=self.root/'review.json'
        spec.write_text(json.dumps(self.spec));review.write_text(json.dumps(self.review))
        tool=Path(__file__).resolve().parents[1]/'finding_benchmark.py'
        proc=subprocess.run([sys.executable,str(tool),str(spec),str(review),'--root',str(self.root),
                             '--require-complete'],capture_output=True,text=True)
        self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr)
        self.assertEqual(json.loads(proc.stdout)['refuted_claims'],1)

    def test_completed_subtest_can_bind_to_parent_function(self):
        source=self.root/'probe.go'
        source.write_text('func TestExample(t *testing.T) {}\n')
        log=self.root/'run.jsonl'
        log.write_text('{"Action":"pass","Test":"TestExample/sub"}\n')
        def ref(path):
            return {'file':path.name,'line':1,'quote':path.read_text().strip(),
                    'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        self.review['rows'][0].update(found=True,correct=True,tested='full',
                                     test_name='TestExample/sub',test_evidence=[ref(source),ref(log)])
        self.assertEqual(audit(self.spec,self.review,self.root)['tested_full'],1)

    def test_duplicate_row_rejected(self):
        self.review['rows'] *= 2
        with self.assertRaisesRegex(ValueError,'coverage'):
            audit(self.spec,self.review,self.root)

    def test_archive_drift_rejected(self):
        (self.root/'report.md').write_text('Rewritten to include the expected result.\n')
        with self.assertRaisesRegex(ValueError,'hash drift'):
            audit(self.spec,self.review,self.root)

    def test_fabricated_fragment_rejected(self):
        self.anchor['quote']='The new target has one success.'
        with self.assertRaisesRegex(ValueError,'fragment mismatch'):
            audit(self.spec,self.review,self.root)

    def test_tested_without_evidence_rejected(self):
        self.review['rows'][0]['tested']='full'
        with self.assertRaisesRegex(ValueError,'execution evidence'):
            audit(self.spec,self.review,self.root)

    def test_impossible_correct_flag_rejected(self):
        self.review['rows'][0]['correct']=True
        with self.assertRaisesRegex(ValueError,'missing finding'):
            audit(self.spec,self.review,self.root)

class ArchivedReviewTests(unittest.TestCase):
    def test_archived_binding_claim_was_behaviorally_refuted(self):
        root = Path(__file__).resolve().parents[2]
        path = root/'docs/evidence/identity-benchmark/results/legacy-claim-red.jsonl'
        records = [json.loads(line) for line in path.read_text().splitlines()]
        for action in ('run','fail'):
            self.assertEqual(sum(r.get('Action') == action and r.get('Test') ==
                                 'TestArchivedOriginalBindingClaim' for r in records),3)
        self.assertEqual(sum('archived original-binding claim refuted:' in r.get('Output','')
                             for r in records),3)

    def test_both_archived_reports_reject_full_coverage(self):
        root = Path(__file__).resolve().parents[2]
        base = root/'docs/evidence/identity-benchmark'
        spec = json.loads((base/'benchmark.json').read_text())
        for arm in ('routed','matrix'):
            with self.subTest(arm=arm):
                review = json.loads((base/f'{arm}-review.json').read_text())
                result = audit(spec,review,root)
                self.assertEqual(result['cases'],8)
                self.assertEqual(result['correct'],7)
                self.assertEqual(result['missing'],['B05'])
                command = [sys.executable,str(root/'tools/finding_benchmark.py'),str(base/'benchmark.json'),
                           str(base/f'{arm}-review.json'),'--root',str(root),'--require-complete']
                proc = subprocess.run(command,capture_output=True,text=True)
                self.assertEqual(proc.returncode,1,proc.stdout+proc.stderr)
                self.assertEqual(json.loads(proc.stdout)['missing'],['B05'])

if __name__ == '__main__':
    unittest.main()
