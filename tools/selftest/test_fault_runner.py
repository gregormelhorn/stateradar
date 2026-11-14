"""Executed regression controls for generic discovery, counts and canary ordering."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_fault_mutants as f


class FaultRunner(unittest.TestCase):
    def fixture(self, root):
        (root/'source.py').write_text('baseline')
        for name in ('dependent', 'canary', 'independent'):
            (root/(name+'.py')).write_text(name)
        (root/'fault-mutants.json').write_text(json.dumps({
            'formatVersion': 1, 'expectedCells': 2,
            'testCommand': [sys.executable, 'suite.py', '{analysis_dir}'],
            'mutants': [{'id': name, 'fault': 'F-09', 'cell': 'Idle x Call',
                'target': 'source.py', 'variant': name+'.py'}
                for name in ('dependent', 'canary', 'independent')]}))
        (root/'mutant-generation.json').write_text(json.dumps({
            'projections': {'resource': {'provenBy': 'canary'}},
            'bindings': [{'id': name, 'requiresProjection': 'resource'}
                         for name in ('dependent', 'canary')]}))

    def result(self, cell=None, count=2, code=None):
        return f.CommandResult(int(bool(cell)) if code is None else code,
            (f'CELL FAIL {cell}\n' if cell else '')+
            f'CELL SUITE: {count} cells checked, {int(bool(cell))} failed\n', 0)

    def run_fixture(self, results, baseline=None, edit=None):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve(); self.fixture(root)
            if edit: edit(root)
            calls=[]
            def execute(config, copy):
                name=(copy/'source.py').read_text(); calls.append(name)
                return (baseline or self.result()) if name=='baseline' else results.get(name, self.result('Idle x Call'))
            out=io.StringIO()
            with patch.object(f, 'run_command', execute), contextlib.redirect_stdout(out):
                code=f.run(root)
            return code, out.getvalue(), calls

    def test_surviving_canary_blocks_without_running_dependent(self):
        code,out,calls=self.run_fixture({'canary': self.result()})
        self.assertNotEqual(code,0)
        self.assertNotIn('dependent',calls)
        self.assertEqual(calls,['baseline','canary','independent'])
        self.assertIn('killed=1 survived=1 errors=0 blocked=1',out)

    def test_success_executes_canary_once_before_dependent(self):
        code,out,calls=self.run_fixture({})
        self.assertEqual(code,0,out)
        self.assertEqual(calls,['baseline','canary','dependent','independent'])
        self.assertIn('killed=3 survived=0 errors=0 blocked=0',out)

    def test_bad_canary_evidence_never_unlocks_or_counts_as_kill(self):
        cases=[f.CommandResult(0,'CELL FAIL malformed\nCELL SUITE: 2 cells checked, 0 failed\n',0),
               self.result('Other x Call'), self.result(count=0),
               self.result('Idle x Call',count=1), self.result('Idle x Call',code=0),
               self.result('Idle x Call',code=2), f.CommandResult(1,'compile error',0),
               f.CommandResult(1,'CELL FAIL Idle x Call\n',0),
               f.CommandResult(None,'',0,timed_out=True),
               f.CommandResult(1,'CELL FAIL Idle x Call\nCELL FAIL Idle x Call\nCELL SUITE: 2 cells checked, 2 failed\n',0)]
        for result in cases:
            with self.subTest(result=result):
                code,out,calls=self.run_fixture({'canary':result})
                self.assertNotEqual(code,0); self.assertNotIn('dependent',calls)
                self.assertIn('killed=1 survived=0',out)
                self.assertIn('blocked=2',out)

    def test_invalid_baseline_runs_no_mutants(self):
        for baseline in (self.result(count=0), self.result(count=1),
                         f.CommandResult(0,'',0), self.result('Idle x Call',code=0)):
            with self.subTest(baseline=baseline):
                code,out,calls=self.run_fixture({},baseline)
                self.assertNotEqual(code,0); self.assertEqual(calls,['baseline'])
                self.assertIn('BLOCKED: baseline',out)

    def test_incomplete_success_is_blocked_not_survived(self):
        code,out,calls=self.run_fixture({'independent':f.CommandResult(0,'',0)})
        self.assertNotEqual(code,0); self.assertIn('killed=2 survived=0 errors=0 blocked=1',out)

    def test_projection_contract_errors_stop_before_execution(self):
        def mutate(root,case):
            p=root/'mutant-generation.json';d=json.loads(p.read_text())
            if case=='missing': d['projections']={}
            if case=='unknown': d['projections']['resource']['provenBy']='absent'
            if case=='unproven': d['projections']['resource'].pop('provenBy')
            if case=='cycle':
                d['projections']['other']={'provenBy':'dependent'}
                d['bindings'][1]['requiresProjection']='other'
            if case=='duplicate': d['bindings'].append(d['bindings'][0])
            p.write_text(json.dumps(d))
        for case in ('missing','unknown','unproven','cycle','duplicate'):
            with self.subTest(case=case), self.assertRaises(f.ConfigError):
                self.run_fixture({},edit=lambda root:mutate(root,case))

    def test_transitive_failure_blocks_entire_dependency_chain(self):
        def edit(root):
            p=root/'mutant-generation.json';d=json.loads(p.read_text())
            d['projections']['second']={'provenBy':'independent'}
            d['bindings'][1]['requiresProjection']='second'
            p.write_text(json.dumps(d))
        code,out,calls=self.run_fixture({'independent':self.result()},edit=edit)
        self.assertNotEqual(code,0);self.assertEqual(calls,['baseline','independent'])
        self.assertIn('killed=0 survived=1 errors=0 blocked=2',out)

    def test_required_count_and_unique_ids(self):
        for value in (None,0,-1,True,1.5):
            def edit(root):
                p=root/'fault-mutants.json';d=json.loads(p.read_text());d['expectedCells']=value
                p.write_text(json.dumps(d))
            with self.subTest(value=value),self.assertRaises(f.ConfigError):
                self.run_fixture({},edit=edit)
        def duplicate(root):
            p=root/'fault-mutants.json';d=json.loads(p.read_text());d['mutants'].append(d['mutants'][0])
            p.write_text(json.dumps(d))
        with self.assertRaises(f.ConfigError):self.run_fixture({},edit=duplicate)

    def test_real_process_canary_controls_execution(self):
        for killed in (False,True):
            with self.subTest(killed=killed),tempfile.TemporaryDirectory() as td:
                root=Path(td).resolve();self.fixture(root)
                audit=root/'audit.txt'
                (root/'suite.py').write_text(
                    "from pathlib import Path\n"
                    "name=Path('source.py').read_text()\n"
                    f"with Path({str(audit)!r}).open('a') as f: f.write(name+'\\n')\n"
                    f"failed=name!='baseline' and (name!='canary' or {killed!r})\n"
                    "if failed: print('CELL FAIL Idle x Call')\n"
                    "print(f'CELL SUITE: 2 cells checked, {int(failed)} failed')\n"
                    "raise SystemExit(int(failed))\n")
                out=io.StringIO()
                with contextlib.redirect_stdout(out):code=f.run(root)
                self.assertEqual(code,0 if killed else 1,out.getvalue())
                self.assertEqual(audit.read_text().splitlines(),
                    ['baseline','canary','dependent','independent'] if killed else
                    ['baseline','canary','independent'])


if __name__=='__main__': unittest.main()
