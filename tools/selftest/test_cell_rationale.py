"""Structured cell rationale must not silently accept missing or invented evidence."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


class RationaleTests(unittest.TestCase):
    def test_generator_preserves_bindings_and_refuses_silent_loss_or_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'fixture';shutil.copytree(ROOT/'tests/golden-mini',root)
            adir=root/'domain-analysis/mini'
            cmd=[sys.executable,str(ROOT/'tools/gen_analysis_sidecar.py'),'--root',str(root)]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stdout+first.stderr)
            data=json.loads((adir/'analysis.json').read_text())
            rows=[]
            for cell in data['cells']:
                row={k:cell[k] for k in ('state','event','disposition','target') if k in cell}
                row['rationale']={'kind':'required-behavior','claim':'Explicit fixture behavior.','scope':'The synthetic contract scope.','evidence':[]}
                rows.append(row)
            binding=adir/'cell-rationale.json'
            binding.write_text(json.dumps({'formatVersion':1,'cells':rows}))
            generated=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(generated.returncode,0,generated.stdout+generated.stderr)
            saved=(adir/'analysis.json').read_text()
            refreshed=json.loads(saved)
            self.assertEqual(refreshed['rationaleVersion'],1)
            self.assertEqual([c['rationale'] for c in refreshed['cells']],[c['rationale'] for c in rows])
            rows[0]['disposition']='UNSPECIFIED'
            binding.write_text(json.dumps({'formatVersion':1,'cells':rows}))
            drift=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(drift.returncode,0);self.assertIn('outcome changed',drift.stderr)
            self.assertEqual((adir/'analysis.json').read_text(),saved)
            binding.unlink()
            lost=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(lost.returncode,0);self.assertIn('refusing silent loss',lost.stderr)
            self.assertEqual((adir/'analysis.json').read_text(),saved)

    def run_case(self, change):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/'fixture';shutil.copytree(ROOT/'tests/golden-mini',root)
            adir=root/'domain-analysis/mini'
            data=json.loads((adir/'analysis.json').read_text());data['rationaleVersion']=1
            (adir/'decisions').mkdir(exist_ok=True)
            (adir/'decisions/DR-900.yaml').write_text('id: DR-900\nstatus: accepted\nscope: Every fixture cell follows its declared behavior.\n')
            reason={'kind':'required-behavior','claim':'The fixture declares this behavior.','scope':'This is the synthetic fixture contract.',
                    'evidence':[{'kind':'decision','dr':'DR-900','citation':{'file':'domain-analysis/mini/decisions/DR-900.yaml','line':3,'fragment':'scope: Every fixture cell follows its declared behavior.'}}]}
            for c in data['cells']:c['rationale']=copy.deepcopy(reason)
            change(data)
            (adir/'analysis.json').write_text(json.dumps(data))
            r=subprocess.run([sys.executable,str(ROOT/'tools/dsc_check.py'),str(adir),'--repo',str(root)],capture_output=True,text=True)
            return r.returncode,r.stdout+r.stderr

    def test_complete_rationale_passes(self):
        code,out=self.run_case(lambda d:None);self.assertEqual(code,0,out)

    def test_missing_rationale_fails(self):
        code,out=self.run_case(lambda d:d['cells'][0].pop('rationale'))
        self.assertNotEqual(code,0,out);self.assertIn('rationale',out)

    def test_missing_fragment_fails(self):
        code,out=self.run_case(lambda d:d['cells'][0]['rationale']['evidence'][0]['citation'].pop('fragment'))
        self.assertNotEqual(code,0,out);self.assertIn('rationale',out)

    def test_broken_fragment_fails(self):
        code,out=self.run_case(lambda d:d['cells'][0]['rationale']['evidence'][0]['citation'].update(fragment='invented guarantee'))
        self.assertNotEqual(code,0,out);self.assertIn('rationale',out)

    def test_upstream_claim_needs_callee_contract(self):
        code,out=self.run_case(lambda d:d['cells'][0]['rationale'].update(kind='upstream-guarantee'))
        self.assertNotEqual(code,0,out);self.assertIn('rationale',out)

    def test_outside_contract_needs_decision(self):
        def change(d):
            r=d['cells'][0]['rationale'];r['kind']='outside-contract'
            r['evidence'][0]={'kind':'upstream-contract','source':'synthetic external contract','citation':r['evidence'][0]['citation']}
        code,out=self.run_case(change)
        self.assertNotEqual(code,0,out);self.assertIn('rationale',out)

    def test_missing_decision_fails(self):
        code,out=self.run_case(lambda d:d['cells'][0]['rationale']['evidence'][0].update(dr='DR-999'))
        self.assertNotEqual(code,0,out);self.assertIn('rationale',out)

    def test_decision_citation_must_reference_that_decision(self):
        def change(d):
            cite=d['cells'][0]['rationale']['evidence'][0]['citation']
            cite.update(file='src/mini.py',line=1,fragment='class')
        code,out=self.run_case(change)
        self.assertNotEqual(code,0,out);self.assertIn('decision citation',out)


if __name__=='__main__':unittest.main()
