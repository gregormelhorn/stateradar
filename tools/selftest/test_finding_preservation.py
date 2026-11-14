#!/usr/bin/env python3
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from finding_preservation import audit


class PreservationTests(unittest.TestCase):
    def setUp(self):
        self.base = {'findings': [{'id': 'F01', 'steps': ['admit', 'success', 'refuse'],
                                  'outcome': 'capacity remains charged', 'question': 'open'}]}
        self.final = copy.deepcopy(self.base)
        self.supplement = {'qualifications': [], 'test_bindings': []}

    def test_changed_order_is_rejected(self):
        self.final['findings'][0]['steps'] = ['admit', 'failure', 'stale']
        with self.assertRaisesRegex(ValueError, 'changed baseline finding'):
            audit(self.base, self.final, self.supplement)

    def test_deleted_finding_is_rejected(self):
        self.final['findings'] = []
        with self.assertRaisesRegex(ValueError, 'missing baseline finding'):
            audit(self.base, self.final, self.supplement)

    def test_changed_question_is_rejected(self):
        self.final['findings'][0]['question'] = 'resolved by model'
        with self.assertRaisesRegex(ValueError, 'changed baseline finding'):
            audit(self.base, self.final, self.supplement)

    def test_duplicate_cannot_hide_loss(self):
        self.final['findings'] *= 2
        with self.assertRaisesRegex(ValueError, 'distinct'):
            audit(self.base, self.final, self.supplement)

    def test_addition_and_separate_qualification_preserve_original(self):
        self.final['findings'].append({'id': 'N01', 'outcome': 'additional consequence'})
        self.supplement['qualifications'].append({'id': 'F01', 'status': 'qualified',
            'rationale': 'Only after this ordering.', 'citation': {'file': 'source.go', 'line': 1, 'fragment': 'guard'}})
        self.supplement['test_bindings'].append({'id': 'F01', 'test': 'TestIdentityCallerVariableRebinding',
                                                'scope': 'Exact caller-variable change.'})
        result = audit(self.base, self.final, self.supplement)
        self.assertEqual(result, {'retained': 1, 'added': 1, 'qualified': 1, 'test_bindings': 1})

    def test_unknown_supplement_target_is_rejected(self):
        self.supplement['test_bindings'].append({'id': 'absent', 'test': 'TestIdentityX', 'scope': 'x'})
        with self.assertRaisesRegex(ValueError, 'unknown finding'):
            audit(self.base, self.final, self.supplement)

    def test_empty_baseline_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonempty baseline'):
            audit({'findings': []}, {'findings': []}, self.supplement)


if __name__ == '__main__':
    unittest.main()
