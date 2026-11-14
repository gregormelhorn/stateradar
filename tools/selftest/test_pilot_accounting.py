"""Behavioral failure probes for persisted controller usage and abort auditing."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import signal
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import run_sol_pilot as runner
from pilot_accounting import cost_report, UsageCheckpoint

USAGE = {'input_tokens': 1000, 'cached_input_tokens': 800, 'output_tokens': 80}
THREAD = '01234567-1234-1234-1234-012345678901'


class AccountingTest(unittest.TestCase):
    def fake(self, root, ending):
        script = root / 'fake-codex'
        script.write_text('#!' + sys.executable + '\n' + f'''
import json, os, pathlib, sys, time
root = pathlib.Path(os.environ['CODEX_HOME'])
sessions = root / 'sessions/2026/11/14'
sessions.mkdir(parents=True)
log = sessions / 'rollout-{THREAD}.jsonl'
print(json.dumps({{'type':'thread.started','thread_id':'{THREAD}'}}), flush=True)
log.write_text(json.dumps({{'type':'event_msg','payload':{{'type':'token_count','info':{{'total_token_usage':{USAGE!r}}}}}}})+'\\n')
{ending}
''')
        script.chmod(0o700)
        return str(script)

    def run_fake(self, ending, *, timeout=5):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex = self.fake(root, ending)
            with patch.dict(os.environ, {'CODEX_HOME': str(root)}):
                with self.assertRaises((ValueError, subprocess.TimeoutExpired)):
                    runner.run_arm(root, 'selective', 'task', codex, Path(sys.executable), timeout)
            checkpoint = json.loads((root / 'usage-checkpoint.json').read_text())
            self.assertEqual(checkpoint['status'], 'partial')
            self.assertEqual(checkpoint['usage'], USAGE)
            self.assertFalse((root / 'usage.json').exists())
            return json.loads((root / 'failure.json').read_text())

    def test_service_failure_retains_usage_without_claiming_final_bill(self):
        self.run_fake("print(json.dumps({'type':'turn.failed','error':{'message':'service unavailable'}}), flush=True)\nsys.exit(1)")

    def test_timeout_retains_usage(self):
        result = self.run_fake('time.sleep(10)', timeout=1)
        self.assertIn('timed out', result['error'])

    def test_timeout_stops_a_command_in_its_own_process_group(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ending = "import subprocess\nchild = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'], start_new_session=True)\n(root / 'child.pid').write_text(str(child.pid))\ntime.sleep(30)"
            codex = self.fake(root, ending)
            try:
                with patch.dict(os.environ, {'CODEX_HOME': str(root)}), self.assertRaises(subprocess.TimeoutExpired):
                    runner.run_arm(root, 'selective', 'task', codex, Path(sys.executable), 1)
                pid = int((root / 'child.pid').read_text())
                state = subprocess.run(['ps', '-o', 'stat=', '-p', str(pid)], capture_output=True, text=True).stdout.strip()
                self.assertTrue(not state or state.startswith('Z'), 'detached command must not keep writing after audit starts')
            finally:
                if (root / 'child.pid').exists():
                    try:
                        os.kill(int((root / 'child.pid').read_text()), signal.SIGKILL)
                    except ProcessLookupError:
                        pass

    def test_checkpoint_exists_before_controller_finishes(self):
        ending = '''
for _ in range(80):
    path = root / 'usage-checkpoint.json'
    if path.exists() and json.loads(path.read_text()).get('usage'):
        (root / 'observed-live').write_text('yes')
        break
    time.sleep(.05)
sys.exit(1)
'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex = self.fake(root, ending)
            with patch.dict(os.environ, {'CODEX_HOME': str(root)}), self.assertRaises(ValueError):
                runner.run_arm(root, 'selective', 'task', codex, Path(sys.executable), 6)
            self.assertTrue((root / 'observed-live').exists(), 'usage must be saved while controller is running')

    def test_costs_subtract_cached_input_and_never_complete_partial_usage(self):
        routing = {'charged_microdollars': 12000, 'reserved_microdollars': 0}
        checkpoint = {'usage': USAGE, 'complete': False}
        partial = cost_report(checkpoint, routing, runner.MODEL)
        self.assertAlmostEqual(partial['reported_codex_credits'], .032)
        self.assertAlmostEqual(partial['known_subtotal_usd_estimate'], .01328)
        self.assertIsNone(partial['total_usd_estimate'])
        checkpoint['complete'] = True
        self.assertEqual(cost_report(checkpoint, routing, runner.MODEL)['total_usd_estimate'], .01328)
        routing['reserved_microdollars'] = 100
        self.assertIsNone(cost_report(checkpoint, routing, runner.MODEL)['total_usd_estimate'])
        self.assertIsNone(cost_report({}, routing, runner.MODEL)['reported_codex_usd_estimate'])

    def test_cumulative_duplicates_and_partial_json_are_not_double_counted(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sessions = root / 'sessions/2026/11/14'
            sessions.mkdir(parents=True)
            (root / 'events.jsonl').write_text(json.dumps({'type': 'thread.started', 'thread_id': THREAD}) + '\n')
            path = sessions / f'rollout-{THREAD}.jsonl'
            event = json.dumps({'type': 'event_msg', 'payload': {'type': 'token_count',
                               'info': {'total_token_usage': USAGE}}}) + '\n'
            path.write_text(event + event + '{')
            with patch.dict(os.environ, {'CODEX_HOME': str(root)}):
                checkpoint = UsageCheckpoint(root)
                checkpoint.poll()
                checkpoint.poll()
                self.assertEqual(checkpoint.usage, USAGE)
                self.assertEqual(len((root / 'usage-history.jsonl').read_text().splitlines()), 1)
                checkpoint.finish(USAGE)
                self.assertEqual(json.loads((root / 'usage-checkpoint.json').read_text())['status'], 'complete')

    def test_abort_still_runs_gates_and_records_separate_outcomes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (patch('run_sol_pilot.run_arm', side_effect=ValueError('service unavailable')),
                  patch('run_sol_pilot.verify_artifacts', return_value=True) as gates):
                with self.assertRaisesRegex(ValueError, 'service unavailable'):
                    runner.run_checked_arm(root, 'selective', 'task', 'codex', Path(sys.executable), 5,
                                           output_name='example', model=runner.MODEL)
            gates.assert_called_once()
            status = json.loads((root / 'phase-status.json').read_text())
            self.assertEqual(status['controller'], 'failed')
            self.assertEqual(status['artifact_gates'], 'passed')
            self.assertFalse(status['complete'])


if __name__ == '__main__':
    unittest.main()
