"""Materialize explicit final-review mappings after source/probe review.

This does not infer semantic equivalence from words. Known baseline case mappings
survive only because their exact rows and tests were preserved; qualifications
and new probe bodies are separately reviewed before this script is run.
"""
import hashlib
import json
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
PRIOR = HERE.parent / 'identity-benchmark'


def anchor(path, line):
    return {'file': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'line': line, 'quote': path.read_text().splitlines()[line - 1]}


def find(path, needle):
    return anchor(path, next(i for i, line in enumerate(path.read_text().splitlines(), 1) if needle in line))


def field(path, ident, key='outcome'):
    active = False
    for i, line in enumerate(path.read_text().splitlines(), 1):
        if '"id":' in line:
            active = json.loads('{' + line.strip().rstrip(',') + '}')['id'] == ident
        if active and f'"{key}":' in line:
            return anchor(path, i)
    raise ValueError((ident, key))


def main():
    mappings = {'gobreaker': [['F07', 'F08'], ['F02'], ['F03', 'F04', 'F05'], ['F20'], ['F22'], ['F06'], ['F12'], ['F10']],
                'transfer': [[f'F{i:02}'] for i in range(7, 13)]}
    for component in mappings:
        old_review = PRIOR / ('bounded-baseline-review.json' if component == 'gobreaker' else 'transfer-baseline-review.json')
        baseline_rows = json.loads(old_review.read_text())['rows']
        for variant in ('generic', 'identity'):
            name = component + '-' + variant
            run = HERE / 'runs' / name
            report = run / 'analysis/final.json'
            supplement_path = run / 'analysis/supplement.json'
            supplement = json.loads(supplement_path.read_text())
            assert all(r['status'] == 'qualified' for r in supplement['qualifications']), 'contradiction requires an explicit revised semantic assessment'
            final = {r['id']: r for r in json.loads(report.read_text())['findings']}
            initial = json.loads((run / 'analysis/initial.json').read_text())['findings']
            assert all(final[r['id']] == r for r in initial)
            replay = HERE / 'results' / (name + '-final.jsonl')
            package = 'github.com/sony/gobreaker' if component == 'gobreaker' else 'identityfixture'
            rows = []
            for old, ids in zip(baseline_rows, mappings[component], strict=True):
                row = {k: v for k, v in old.items() if k not in ('evidence', 'test_evidence', 'rationale')}
                row['evidence'] = [field(report, ident) for ident in ids]
                row['rationale'] = 'The original ordered case and its probe are preserved exactly. Added qualifications were reviewed and do not negate this bounded case. This score does not certify every sentence in the full report.'
                for qualification in supplement['qualifications']:
                    if qualification['id'] in ids:
                        row['evidence'].append(field(supplement_path, qualification['id'], 'rationale'))
                if component == 'transfer' and row['id'] == 'T-F':
                    row['tested'] = 'full'
                    row['test_name'] = 'TestIdentityCallerVariableRebinding'
                    binding = next(r for r in supplement['test_bindings'] if r['test'] == row['test_name'])
                    row['evidence'].append(field(supplement_path, binding['id'], 'scope'))
                    row['rationale'] = 'Direct test body reviewed: callback creation precedes reassignment of only the caller local pointer to a distinct Port. Both account counters and the old Port alias are asserted before/after delivery. This closes the earlier exact-sequence test gap; the old target-mutation case remains intact. Epoch values differ from the canonical zero example without changing a guard.'
                row['test_evidence'] = []
                if row['tested'] != 'none':
                    test = row['test_name']
                    parent = test.split('/')[0]
                    source = [p for p in (run / 'analysis').rglob('*.go') if f'func {parent}(' in p.read_text()]
                    assert len(source) == 1
                    row['test_evidence'] = [find(source[0], f'func {parent}('),
                        find(replay, '"Action":"pass","Package":"' + package + '","Test":"' + test + '"')]
                rows.append(row)
            review = {'reviewer': 'Codex supervising agent; source, supplement and public-seam probe bodies reviewed',
                      'scope': 'Preserved baseline benchmark cases plus direct caller-variable test evidence. Semantic judgments are attributed review, not inferred by the checker. Raw row retention is not endorsement of an unqualified generalization. Full-pilot gates are out of scope.',
                      'rows': rows, 'refuted_claims': []}
            (HERE / (name + '-review.json')).write_text(json.dumps(review, indent=2) + '\n')


if __name__ == '__main__':
    main()
