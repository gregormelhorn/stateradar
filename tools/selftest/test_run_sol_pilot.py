from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_sol_pilot import command_result, codex_environment, read_log, read_usage, serve_tools


class SolPilotTest(unittest.TestCase):
    def test_preserves_raw_log_and_uses_compact_tool_result(self):
        full = '=== RUN   TestPool_Get\n' + 'trace\n' * 8000
        full += 'panic: test timed out after 1m\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for arm in ('standard', 'compact'):
                folder = root / arm
                folder.mkdir()
                with patch('run_sol_pilot.execute', return_value=(1, full, '')):
                    result = command_result(folder, arm, ['go', 'test'], 1, Path(sys.executable))
                self.assertEqual((folder / 'logs/001.stdout').read_text(), full)
                self.assertEqual(result['exit_code'], 1)
                self.assertIn('TestPool_Get', result['stdout'])
                self.assertIn('test timed out', result['stdout'])
                if arm == 'standard':
                    self.assertEqual(result['stdout'], full)
                else:
                    self.assertLess(len(result['stdout']), 2200)

    def test_compact_timeout_keeps_the_blocked_test_stack_and_raw_log(self):
        header = 'panic: test timed out after 35s\n\trunning tests:\n\t\tTestPool_Get (35s)\n'
        noise = '\n'.join(f'goroutine {i} [sleep]:\ntime.Sleep()\n\truntime/time.go:1\n'
                          for i in range(2, 70))
        blocked = ('goroutine 70 [chan receive]:\nexample/pool.(*channelPool).Get()\n'
                   '\t/work/channel.go:137 +0x1\nexample/pool.TestPool_Get()\n'
                   '\t/work/channel_rpc_test.go:93 +0x2\n')
        full = header + '\n' + noise + '\n' + blocked + '\n' + noise
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('run_sol_pilot.execute', return_value=(1, full, '')):
                result = command_result(root, 'compact', ['go', 'test'], 1, Path(sys.executable))
            self.assertEqual((root / 'logs/001.stdout').read_text(), full)
            self.assertIn('TestPool_Get (35s)', result['stdout'])
            self.assertIn('channel.go:137', result['stdout'])
            self.assertIn('Full log, stack starts at line', result['stdout'])
            self.assertNotIn('time.Sleep()', result['stdout'])
            self.assertIn('001', result['read_more']['argv_prefix'][1])

    def test_compact_long_table_can_be_read_by_exact_key(self):
        rows = ''.join(f'| E-{i:03} | ' + 'evidence ' * 45 + '|\n' for i in range(50))
        full = '| Event / pair | Behaviour |\n| --- | --- |\n' + rows + '\nCoverage checklist:\n\n- [x] E-025\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('run_sol_pilot.execute', return_value=(0, full, '')):
                result = command_result(root, 'compact', ['cat', 'table.md'], 1, Path(sys.executable))
            self.assertIn('E-025', result['stdout'])
            self.assertNotIn('evidence ' * 10, result['stdout'])
            found = read_log(root, ['read-log', '001', 'rows', 'E-025'])
            self.assertEqual(found['matches'], 1)
            self.assertEqual(found['lines'][0], (28, full.splitlines()[27]))
            with self.assertRaises(ValueError):
                read_log(root, ['read-log', '../001', 'rows', 'E-025'])

    def test_live_dispatch_preserves_numbered_function_body(self):
        code = '     1\tpackage pool\n     2\tfunc (c *Pool) Put() {\n     3\t\tif ready {\n'
        code += '     4\t\t\treturn\n     5\t\t}\n     6\t\tconsume()\n     7\t}\n'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request = lambda i, argv: json.dumps({
                'id': i, 'method': 'tools/call',
                'params': {'name': 'command', 'arguments': {'argv': argv}},
            })
            calls = '\n'.join((request(1, ['nl', '-ba', 'pool.go']),
                               request(2, ['read-log', '001', 'function', 'Put'])))
            replies = StringIO()
            with (patch('run_sol_pilot.execute', return_value=(0, code, '')) as run,
                  patch('sys.stdin', StringIO(calls)), redirect_stdout(replies)):
                serve_tools(root, 'compact')
            run.assert_called_once()
            result = json.loads(replies.getvalue().splitlines()[1])
            body = json.loads(result['result']['content'][0]['text'])
            self.assertIn([6, '     6\t\tconsume()'], body['lines'])
            self.assertEqual(body['lines'][-1], [7, '     7\t}'])

    def test_selective_preserves_complete_source_and_table_and_compacts_timeout(self):
        source = 'package pool\nfunc Get() {\n' + '\t// inspect source\n' * 140 + '}\n'
        table = '| ID | Evidence |\n| --- | --- |\n' + ''.join(
            f'| E-{i:03} | exact evidence for this row |\n' for i in range(90))
        timeout = ('panic: test timed out after 10s\n\trunning tests:\n\t\tTestPool_Get (10s)\n\n'
                   'goroutine 1 [sleep]:\n' + '\tnoise\n' * 900 +
                   '\ngoroutine 2 [chan receive]:\npool.TestPool_Get()\n\t/work/channel.go:137\n')
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('run_sol_pilot.execute', side_effect=[
                (0, source, ''), (0, table, ''), (1, timeout, 'short stderr\n'),
            ]):
                source_result = command_result(root, 'selective', ['cat', 'pool.go'], 1, Path(sys.executable))
                table_result = command_result(root, 'selective', ['cat', 'table.md'], 2, Path(sys.executable))
                failure_result = command_result(root, 'selective', ['go', 'test'], 3, Path(sys.executable))
            self.assertEqual(source_result['stdout'], source)
            self.assertEqual(table_result['stdout'], table)
            self.assertEqual(read_log(root, ['read-log', '002', 'rows', 'E-042'])['matches'], 1)
            self.assertIn('channel.go:137', failure_result['stdout'])
            self.assertNotIn('noise', failure_result['stdout'])
            self.assertEqual(failure_result['stderr'], 'short stderr\n')
            self.assertEqual((root / 'logs/003.stdout').read_text(), timeout)

    def test_selective_long_document_continues_without_skipping_lines(self):
        full = ''.join(f'{i:04}: ' + 'evidence ' * 21 + '\n' for i in range(120))
        full += 'long table row ' * 1600 + '\nlast line without a trailing newline'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch('run_sol_pilot.execute', return_value=(0, full, '')):
                result = command_result(root, 'selective', ['cat', 'requirements.md'], 1, Path(sys.executable))
            prefix = result['stdout']
            self.assertLess(len(prefix), len(full))
            self.assertTrue(full.startswith(prefix))
            followup = result['read_more']['next_stdout']
            pages = [prefix]
            for _ in range(10):
                if not followup:
                    break
                response = read_log(root, followup)
                pages.append(response['text'])
                followup = response['next']
            self.assertIsNone(followup)
            self.assertEqual(''.join(pages), full)

    def test_usage_preserves_codex_counters_and_requires_completed_turn(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'events.jsonl'
            usage = {'input_tokens': 1000, 'cached_input_tokens': 800,
                     'cache_write_input_tokens': 100, 'output_tokens': 80,
                     'reasoning_output_tokens': 30}
            path.write_text(json.dumps({'type': 'turn.failed'}) + '\n')
            with self.assertRaisesRegex(ValueError, 'completed'):
                read_usage(path)
            path.write_text(json.dumps({'type': 'turn.completed', 'usage': usage}) + '\n')
            self.assertEqual(read_usage(path), usage)

    def test_codex_environment_uses_login_without_openai_key_overrides(self):
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'dummy', 'CODEX_API_KEY': 'dummy',
                                      'CODEX_ACCESS_TOKEN': 'dummy', 'TYPESAFE_API_KEY': 'routing'}):
            env = codex_environment()
        self.assertFalse({'OPENAI_API_KEY', 'CODEX_API_KEY', 'CODEX_ACCESS_TOKEN'} & env.keys())
        self.assertEqual(env['TYPESAFE_API_KEY'], 'routing')


if __name__ == '__main__':
    unittest.main()
