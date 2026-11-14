"""Behavior regressions for predictable pilot artifact handling."""
import argparse
from contextlib import redirect_stdout
from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import part_b_pack
import run_sol_pilot

PACK = Path(__file__).resolve().parents[2]


class PilotArtifactsTest(unittest.TestCase):
    def test_catalogue_roundtrip_and_reject_bad_coverage(self):
        import pilot_artifacts as artifacts
        from gen_analysis_sidecar import _parse_event_annotations
        data = {'events': [
            {'id': 'Read', 'classification': 'external', 'undesired': False,
             'source': 'caller', 'description': 'Read; source.go:1 ("a | b")',
             'gate': 'service state', 'upstream_guards': ['none documented'],
             'coverage': {key: 'UV-Read' for key in artifacts.CATEGORIES}},
            {'id': 'UV-Read', 'classification': 'external', 'undesired': True,
             'source': 'caller', 'description': 'Unexpected Read', 'gate': 'service state',
             'upstream_guards': ['none documented']}],
            'pairs': [{'id': 'P-01', 'first': 'Read', 'second': 'UV-Read', 'entity': 'resource'}],
            'remembrance': 'No completed entity is retained.', 'lock_discipline': 'No lock.'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'event-catalogue.md'
            path.write_text(artifacts.render_catalogue(data))
            self.assertEqual(part_b_pack._catalogue_ids(path.read_text()),
                             (['Read', 'UV-Read'], ['P-01a', 'P-01b']))
            self.assertEqual(_parse_event_annotations(path)['Read']['coverage'], data['events'][0]['coverage'])
            self.assertIn('a \\| b', path.read_text())
            data['events'][0]['coverage']['loss'] = 'UV-Unknown'
            with self.assertRaisesRegex(ValueError, 'UV-Unknown'):
                artifacts.render_catalogue(data)
            data['events'][0]['coverage']['loss'] = 'n/a:'
            with self.assertRaises(ValueError):
                artifacts.render_catalogue(data)
            data['events'][0]['coverage']['loss'] = 'n/a: impossible at this seam'
            data['events'][1]['id'] = 'UnexpectedRead'
            with self.assertRaisesRegex(ValueError, 'UV-'):
                artifacts.render_catalogue(data)

    def test_citations_copy_exact_lines_and_reject_invalid_line(self):
        import pilot_artifacts as artifacts
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'source.go'
            source.write_text('first\n  return a | b\n\n')
            self.assertEqual(artifacts.citations(source, [2])[0]['fragment'], '  return a | b')
            for line in (0, 3, 4):
                with self.assertRaises(ValueError):
                    artifacts.citations(source, [line])

    def test_blind_duplicate_situation_fails_but_distinct_situations_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'event-catalogue.md').write_text('<!-- event-ids: Read -->')
            blind = root / 'blind.md'
            args = argparse.Namespace(repo=str(root), analysis_dir='.', check=str(blind))
            for second, expected in [('Idle', 1), ('Busy', 0)]:
                blind.write_text('| id | situation | disposition |\n|---|---|---|\n'
                                 '| Read | Idle | handle |\n'
                                 f'| Read | {second} | reject |\n- [x] Read\n')
                with redirect_stdout(StringIO()) as out:
                    result = part_b_pack.check(args)
                self.assertEqual(result, expected, out.getvalue())
            blind.write_text('| id | disposition |\n|---|---|\n'
                             '| Read | handle |\n| Read | reject |\n- [x] Read\n')
            with redirect_stdout(StringIO()):
                self.assertEqual(part_b_pack.check(args), 1)

    def test_zero_row_matrix_is_not_green(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'event-catalogue.md').write_text('<!-- event-ids: Read -->\n'
                                                   '| Read | external |\n')
            (root / 'disposition-matrix.md').write_text('<!-- states: Idle -->\nAbstraction: one mode.\n')
            result = subprocess.run([sys.executable, str(PACK / 'tools/check_matrix.py'), str(root)],
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('missing state row: Idle', result.stdout)

    def test_completion_requires_pinned_manifest_and_matching_sidecar(self):
        import pilot_artifacts as artifacts
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            subprocess.run(['git', 'init', '-q', str(repo)], check=True)
            (repo / 'source.go').write_text('package fixture\n')
            subprocess.run(['git', '-C', str(repo), 'add', 'source.go'], check=True)
            subprocess.run(['git', '-C', str(repo), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                            'commit', '-qm', 'fixture'], check=True)
            sha = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
            adir = repo / 'domain-analysis/fixture'
            adir.mkdir(parents=True)
            for name in ('extraction.md', 'as-is.machine.mmd', 'as-is-validation.md', 'catalogue-fields.json',
                         'event-catalogue.md', 'disposition-matrix.md', 'check_matrix.py', 'check_guards.py',
                         'guard-results.txt', 'invariants-and-lints.md', 'adversarial-traces.md',
                         'open-questions.md', 'summary.md', 'part-b-blind.md', 'part-b-diff.md'):
                (adir / name).write_text('fixture')
            manifest = {'component': 'fixture', 'watchPaths': ['source.go'], 'analyzedSha': sha}
            (adir / 'analysis.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'manifest'):
                artifacts.audit_pilot(adir, repo)
            (adir / 'manifest.json').write_text(json.dumps({**manifest, 'analyzedSha': 'WORKTREE'}))
            with self.assertRaisesRegex(ValueError, 'HEAD'):
                artifacts.audit_pilot(adir, repo)
            (adir / 'manifest.json').write_text(json.dumps(manifest))
            artifacts.audit_pilot(adir, repo)
            (adir / 'analysis.json').write_text(json.dumps({**manifest, 'analyzedSha': 'WORKTREE'}))
            with self.assertRaisesRegex(ValueError, 'sidecar'):
                artifacts.audit_pilot(adir, repo)
            (adir / 'analysis.json').write_text(json.dumps(manifest))
            (adir / 'summary.md').unlink()
            with self.assertRaisesRegex(ValueError, 'summary'):
                artifacts.audit_pilot(adir, repo)

    def test_model_selection_reaches_codex_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            usage = {'input_tokens': 1000, 'cached_input_tokens': 800, 'output_tokens': 80}
            with (patch('run_sol_pilot.subprocess.Popen') as run,
                  patch('run_sol_pilot.os.killpg'),
                  patch('run_sol_pilot.read_usage', return_value=usage)):
                proc = run.return_value.__enter__.return_value
                proc.poll.return_value = 0
                proc.returncode = 0
                run_sol_pilot.run_arm(root, 'selective', 'task', 'codex', Path(sys.executable), 10,
                                      model='gpt-6.1-terra')
                argv = run.call_args.args[0]
                self.assertEqual(argv[argv.index('--model') + 1], 'gpt-6.1-terra')
                self.assertEqual(argv[argv.index('--sandbox') + 1], 'workspace-write')
                self.assertIn('--ignore-user-config', argv)
                self.assertNotIn('--ephemeral', argv)

    def test_catalogue_gate_cannot_skip_missing_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'logs').mkdir()
            with patch('run_sol_pilot.execute', return_value=(1, 'missing fields', '')) as execute:
                self.assertFalse(run_sol_pilot.verify_artifacts(root, Path(sys.executable), catalogue=True))
            self.assertTrue(any('catalogue-fields.json' in ' '.join(call.args[1])
                                for call in execute.call_args_list))


if __name__ == '__main__':
    unittest.main()
