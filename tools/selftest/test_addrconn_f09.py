"""The new fixture rejects empty Go discovery and incomplete decision coverage."""
import json
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import addrconn_f09 as f


class AddrConnFixture(unittest.TestCase):
    def test_empty_go_discovery_is_not_success(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td).resolve();(root/'stateradar').mkdir();(root/'analysis').mkdir();(root/'bin').mkdir()
            (root/'clientconn.go').write_text('func (ac *addrConn) resetTransport() {\ntimer := time.NewTimer(backoffFor)\nacctx := ac.ctx\n\t\tac.mu.Unlock()\n}')
            (root/'stateradar/run.py').write_text((f.COMPONENT/'tests/run.py').read_text())
            (root/'analysis/analysis.json').write_text(json.dumps({'cells':[{'state':'BackoffWaiting','event':'TearDown'}]}))
            fake=root/'bin/go';fake.write_text('#!/usr/bin/env python3\nprint("PASS, no tests")\n');fake.chmod(0o755)
            run=subprocess.run([sys.executable,root/'stateradar/run.py','--analysis',root/'analysis'],
                capture_output=True,text=True,env={**os.environ,'PATH':str(root/'bin')+os.pathsep+os.environ['PATH']})
            self.assertNotEqual(run.returncode,0)
            self.assertIn('BLOCKED: incomplete Go discovery/verdict',run.stdout+run.stderr)

    def test_omitted_question_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'resolution.json').write_text('{"records":[]}')
            with self.assertRaisesRegex(ValueError,'Q-01..Q-16'):f.verify_records(root,root)

    def test_historical_questions_are_all_preserved(self):
        records=json.loads((f.ANALYSIS/'resolution.json').read_text())['records']
        self.assertEqual([r['source_question'] for r in records],[f'Q-{i:02}' for i in range(1,17)])
        for r in records:
            self.assertEqual(r['question_status'],'ANSWERED')
            self.assertEqual(r['implementation_status'],'pending')
            self.assertIn('delegated',r['acceptance_basis'])
            self.assertEqual(json.loads((f.ANALYSIS/'decisions'/(r['id']+'.yaml')).read_text()),r)


if __name__=='__main__':unittest.main()
