"""Mutation kills require completed behavior verdicts and the actual JSON oracle."""
import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import check_matrix_mutation as matrix


class MutationBinding(unittest.TestCase):
    def fixture(self, path, oracle='markdown'):
        (path/'disposition-matrix.md').write_text('<!-- states: Idle Busy -->\n| state | Call |\n|---|---|\n| **Idle** | transition →Busy |\n| **Busy** | handle |\n')
        (path/'analysis.json').write_text(json.dumps({'states':['Idle','Busy'],'events':[{'id':'Call'}], 'cells':[
            {'state':'Idle','event':'Call','disposition':'transition','target':'Busy'},
            {'state':'Busy','event':'Call','disposition':'handle'}]}))
        (path/'matrix-mutation.json').write_text(json.dumps({'formatVersion':1,'oracle':oracle,
            'testCommand':[sys.executable,'suite.py','{analysis_dir}'],'workingDirectory':'.'}))

    def simulated(self, mutant_output, mutant_code=1, baseline_output='CELL SUITE: 2 cells checked, 0 failed'):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);self.fixture(path)
            calls=[0]
            def command(config,adir):
                calls[0]+=1
                return matrix.CommandResult(0 if calls[0]==1 else mutant_code,
                    baseline_output if calls[0]==1 else mutant_output,0)
            out=io.StringIO()
            with patch.object(matrix,'run_command',command),contextlib.redirect_stdout(out):code=matrix.run(path)
            return code,out.getvalue()

    def test_crash_is_not_kill(self):
        code,out=self.simulated('Traceback: compile failure')
        self.assertNotEqual(code,0);self.assertNotIn(' KILLED ',out);self.assertIn('BLOCKED',out)

    def test_wrong_cell_is_not_success(self):
        code,out=self.simulated('CELL FAIL Other x Call\nCELL SUITE: 2 cells checked, 1 failed')
        self.assertNotEqual(code,0);self.assertIn('wrong cell',out)

    def test_zero_discovery_is_blocked(self):
        code,out=self.simulated('CELL FAIL Idle x Call\nCELL SUITE: 2 cells checked, 1 failed',
                                baseline_output='CELL SUITE: 0 cells checked, 0 failed')
        self.assertNotEqual(code,0);self.assertIn('BLOCKED: baseline',out)

    def test_json_oracle_reaches_real_test(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td);self.fixture(path,'sidecar')
            (path/'suite.py').write_text('''import json,sys
from pathlib import Path
m=json.loads((Path(sys.argv[1])/'analysis.json').read_text())
failed=0
for c in m['cells']:
    want=('transition','Busy') if c['state']=='Idle' else ('handle',None)
    if (c['disposition'],c.get('target'))!=want:
        failed+=1;print('CELL FAIL '+c['state']+' x '+c['event'])
print(f'CELL SUITE: 2 cells checked, {failed} failed')
sys.exit(bool(failed))
''')
            out=io.StringIO()
            with contextlib.redirect_stdout(out):code=matrix.run(path)
            self.assertEqual(code,0,out.getvalue());self.assertIn('killed=3',out.getvalue())


if __name__=='__main__':unittest.main()
