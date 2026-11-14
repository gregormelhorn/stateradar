#!/usr/bin/env python3
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
SCRIPT = Path(__file__).resolve().parents[2] / 'docs/evidence/identity-postreview/scripts/probe_logs.py'
spec = importlib.util.spec_from_file_location('postreview_probe_logs', SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ProbeLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'logs').mkdir()
        self.meta = {'argv': ['go', 'test', '-race', '-count=3', '-run', '^TestIdentity', '.'], 'exit_code': 0}
        self.events = [{'Action': action, 'Test': 'TestIdentityExample'} for _ in range(3) for action in ('run', 'pass')]

    def write(self):
        (self.root / 'logs/001.json').write_text(json.dumps(self.meta))
        (self.root / 'logs/001.stdout').write_text('\n'.join(json.dumps(x) for x in self.events))

    def test_tool_log_alone_proves_execution(self):
        self.write()
        rows = module.probe_runs(self.root)
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]['passing_three_repetitions'])

    def test_empty_exit_zero_is_rejected(self):
        self.events = []
        self.write()
        self.assertFalse(module.probe_runs(self.root)[0]['passing_three_repetitions'])

    def test_fail_does_not_count_as_pass(self):
        self.events[-1]['Action'] = 'fail'
        self.meta['exit_code'] = 1
        self.write()
        self.assertFalse(module.probe_runs(self.root)[0]['passing_three_repetitions'])

    def test_skip_is_not_completion(self):
        self.events[-1]['Action'] = 'skip'
        self.write()
        self.assertFalse(module.probe_runs(self.root)[0]['passing_three_repetitions'])

    def test_reading_a_log_does_not_run_tests(self):
        self.meta['argv'] = ['cat', 'old-log.jsonl']
        self.write()
        self.assertEqual(module.probe_runs(self.root), [])


if __name__ == '__main__':
    unittest.main()
