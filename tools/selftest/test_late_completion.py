"""Behavioral red probes for the language-neutral late-completion oracle."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from late_completion import evaluate, EvidenceError

PROFILE = {'formatVersion': 1, 'terminalState': 'Stopped', 'acceptedState': 'Active',
           'acceptanceEffect': 'accepted', 'cases': [
               {'id': 'late', 'cell': 'Stopped x Complete', 'order': ['start', 'terminate', 'complete', 'observe']},
               {'id': 'early', 'cell': 'Starting x Complete', 'order': ['start', 'complete', 'terminate', 'observe']}]}

def evidence():
    def snap(action, state, owned=False, closed=0, effects=None):
        return dict(action=action, state=state, published=owned, releaseCount=closed,
                    effects=effects or [], resource='resource-1', parentAlive=True)
    return [dict(case='late', repeat=0, steps=[snap('start','Starting'), snap('terminate','Stopped'),
                snap('complete','Stopped',closed=1), snap('observe','Stopped',closed=1)]),
            dict(case='early', repeat=0, steps=[snap('start','Starting'),snap('complete','Active',True,effects=['accepted']),
                snap('terminate','Stopped',closed=1,effects=['accepted']),snap('observe','Stopped',closed=1,effects=['accepted'])])]

class Oracle(unittest.TestCase):
    def test_positive(self):
        self.assertEqual(evaluate(PROFILE,evidence(),1), {})
    def test_independent_coordinates(self):
        for field, value in [('state','Active'),('published',True),('releaseCount',0),('effects',['accepted'])]:
            with self.subTest(field=field):
                traces=evidence()
                for s in traces[0]['steps'][2:]:s[field]=value
                self.assertIn('Stopped x Complete',evaluate(PROFILE,traces,1))
                self.assertEqual(evaluate(PROFILE,traces,1,weak=True),{})
    def test_positive_control_cannot_be_vacuous(self):
        traces=evidence();traces[1]['steps'][1]['published']=False
        self.assertIn('Starting x Complete',evaluate(PROFILE,traces,1))
    def test_empty_missing_duplicate_wrong_order_identity_and_parent_block(self):
        variants=[[], evidence()[:-1], evidence()+[evidence()[0]]]
        for field,value in [('action','observe'),('resource','foreign'),('parentAlive',False),('releaseCount',True)]:
            traces=evidence();traces[0]['steps'][2][field]=value;variants.append(traces)
        for traces in variants:
            with self.subTest(traces=traces),self.assertRaises(EvidenceError):evaluate(PROFILE,traces,1)
    def test_count_must_match(self):
        with self.assertRaises(EvidenceError):evaluate(PROFILE,evidence(),2)
    def test_no_effects_can_disappear(self):
        traces=evidence();traces[1]['steps'][-1]['effects']=[]
        with self.assertRaises(EvidenceError):evaluate(PROFILE,traces,1)
    def test_no_duplicate_profile_ids_or_cells(self):
        for field in ['id','cell']:
            p=copy.deepcopy(PROFILE);p['cases'][1][field]=p['cases'][0][field]
            with self.assertRaises(EvidenceError):evaluate(p,evidence(),1)

if __name__=='__main__':unittest.main()
