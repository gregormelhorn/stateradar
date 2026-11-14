#!/usr/bin/env python3
"""Audit explicit reviewed findings, not prose semantics or keyword matches.

The reviewer owns entailment and absence judgments. This checker validates their
coverage and immutable anchors, and can reject a claim of full finding coverage.
"""
import argparse
import hashlib
import json
from pathlib import Path


def anchor(value, root):
    relative = Path(value['file'])
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('anchor must be repository relative')
    path = root / relative
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != value['sha256']:
        raise ValueError(f'anchor hash drift: {relative}')
    lines = raw.decode().splitlines()
    line = value['line']
    if type(line) is not int or not 1 <= line <= len(lines) or not value['quote'].strip() or value['quote'] not in lines[line - 1]:
        raise ValueError(f'anchor fragment mismatch: {relative}')


def audit(spec, review, root):
    cases = spec['cases']
    ids = [c['id'] for c in cases]
    rows = review['rows']
    if not ids or len(ids) != len(set(ids)) or len(rows) != len(ids) or {r['id'] for r in rows} != set(ids):
        raise ValueError('review coverage must contain every distinct case exactly once')
    if not review.get('reviewer') or not review.get('scope'):
        raise ValueError('attributed review and scope required')
    for case in cases:
        for key in ('initial', 'steps', 'outcome', 'proof'):
            if not case.get(key):
                raise ValueError(f'incomplete case {case["id"]}: {key}')
        for evidence in case['proof']:
            anchor(evidence, root)
    for row in rows:
        if type(row.get('found')) is not bool or type(row.get('correct')) is not bool or row.get('tested') not in ('full','partial','none'):
            raise ValueError('explicit found/correct/tested verdicts required')
        if row['correct'] and not row['found']:
            raise ValueError('a missing finding cannot be correct')
        if not row.get('rationale') or not row.get('evidence'):
            raise ValueError('review rationale and anchors required, including near-miss evidence')
        if row['tested'] != 'none':
            evidence = row.get('test_evidence', [])
            name = row.get('test_name')
            if not isinstance(name, str) or not name or len(evidence) != 2 or f'func {name.split("/")[0]}(' not in evidence[0]['quote']:
                raise ValueError('tested verdict requires source and execution evidence')
            execution = json.loads(evidence[1]['quote'])
            if execution.get('Action') != 'pass' or execution.get('Test') != name:
                raise ValueError('execution evidence must pass the named test')
        for evidence in row['evidence'] + row.get('test_evidence', []):
            anchor(evidence, root)
    for claim in review.get('refuted_claims', []):
        if claim.get('case') not in ids or not claim.get('rationale') or not claim.get('evidence'):
            raise ValueError('refuted claim needs case, rationale and evidence')
        for evidence in claim['evidence']:
            anchor(evidence, root)
    return {'refuted_claims': len(review.get('refuted_claims', [])), 'cases': len(ids), 'found': sum(r['found'] for r in rows),
            'correct': sum(r['correct'] for r in rows),
            'tested_full': sum(r['tested'] == 'full' for r in rows),
            'tested_partial': sum(r['tested'] == 'partial' for r in rows),
            'missing': [r['id'] for r in rows if not r['found']],
            'incorrect': [r['id'] for r in rows if r['found'] and not r['correct']],
            'limitation': 'Semantic verdicts are attributed review judgments; anchors do not prove entailment.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spec', type=Path)
    parser.add_argument('review', type=Path)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--require-complete', action='store_true')
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.spec.read_text()), json.loads(args.review.read_text()), args.root)
    except (ValueError, KeyError, OSError, TypeError) as exc:
        print(f'INVALID: {exc}')
        return 2
    print(json.dumps(result, indent=2))
    return int(args.require_complete and (result['correct'] != result['cases'] or result['refuted_claims']))


if __name__ == '__main__':
    raise SystemExit(main())
