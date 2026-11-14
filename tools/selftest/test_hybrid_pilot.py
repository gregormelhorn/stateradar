import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hybrid_pilot import render_matrix, review_windows


class HybridPilotTest(unittest.TestCase):
    def test_render_checks_fragments_totality_and_questions(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder)
            (repo / 'pool.go').write_text('state = Ready\n')
            cell = {'state': 'Ready', 'event': 'Get', 'disposition': 'handle',
                    'citation': {'file': 'pool.go', 'line': 1, 'fragment': 'state = Ready'},
                    'note': 'Return the value'}
            task = {'states': ['Ready'], 'events': ['Get'], 'abstraction': 'Track availability.',
                    'cells': [cell]}
            self.assertIn('handle pool.go:1 ("state = Ready") — Return the value',
                          render_matrix(task, repo))
            with self.assertRaisesRegex(ValueError, 'missing'):
                render_matrix({**task, 'cells': []}, repo)
            with self.assertRaisesRegex(ValueError, 'duplicate'):
                render_matrix({**task, 'cells': [cell, cell]}, repo)
            cell['citation']['fragment'] = 'state = Closed'
            with self.assertRaisesRegex(ValueError, 'fragment'):
                render_matrix(task, repo)
            cell['disposition'] = 'UNSPECIFIED'
            with self.assertRaisesRegex(ValueError, 'question'):
                render_matrix(task, repo)

    def test_flash_citations_are_checked_per_step(self):
        source = 'read the queue\nwait for work\n'
        step = {'actor': 'A', 'action': 'Reads the queue', 'line': 1, 'fragment': 'read the queue'}
        row = {'observation': 'no work', 'mutator': 'B puts a value', 'branch': 'at capacity',
               'steps': [step, {**step, 'actor': 'B', 'fragment': 'invents action'}],
               'caller_outcomes': 'A still waits', 'inventory': 'one value',
               'pending': 'one waiter', 'later_effect': 'another caller receives the value'}
        result = review_windows(json.dumps({'candidates': [row]}), source)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['problems'])
        row['steps'][1]['fragment'] = 'wait for work'
        self.assertEqual(review_windows(json.dumps({'candidates': [row]}), source)[0]['problems'], [])


if __name__ == '__main__':
    unittest.main()
