"""The executed canary gates F-09; malformed or unrelated failures cannot prove it."""
import contextlib
import io
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import semaphore_f09 as f
from check_fault_mutants import CommandResult


class F09Gate(unittest.TestCase):
    def result(self, cell=None, count=34, code=None):
        output = (f'CELL FAIL {cell}\n' if cell else '')
        output += f'CELL SUITE: {count} cells checked, {int(cell is not None)} failed\n'
        return CommandResult(int(cell is not None) if code is None else code, output, 0)

    def test_canary_survival_blocks_dependent_execution(self):
        calls = []
        def execute(label, mutant, suite):
            calls.append(label)
            return self.result(count=34 if suite == 'full' else 1)
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, 'BLOCKED: capacity canary'):
                f.compare(execute)
        self.assertEqual(calls, ['full-baseline', 'weak-baseline', 'capacity-canary'])

    def test_only_executed_correct_cell_kill_authorizes(self):
        for verdict in ('SURVIVED', 'BLOCKED'):
            with self.subTest(verdict=verdict), self.assertRaises(RuntimeError):
                f.require_canary(verdict)
        f.require_canary('KILLED')

    def test_invalid_kill_evidence_is_blocked(self):
        for result in (self.result('Other x Event'), self.result(count=0),
                       CommandResult(1, 'compile error', 0),
                       CommandResult(1, f'CELL FAIL {f.CELL}\n', 0),
                       self.result(f.CELL, code=0), self.result(f.CELL, code=2),
                       CommandResult(None, '', 0, timed_out=True)):
            self.assertEqual(f.classify(result, f.CELL, 34), 'BLOCKED')

    def test_expected_comparison(self):
        def execute(label, mutant, suite):
            cell = f.CANARY_CELL if label == 'capacity-canary' else f.CELL if label == 'full-f09' else None
            return self.result(cell, 34 if suite == 'full' else 1)
        with contextlib.redirect_stdout(io.StringIO()):
            rows = f.compare(execute)
        self.assertEqual([r['verdict'] for r in rows], ['SURVIVED', 'SURVIVED', 'KILLED', 'SURVIVED', 'SURVIVED', 'KILLED'])


if __name__ == '__main__':
    unittest.main()
