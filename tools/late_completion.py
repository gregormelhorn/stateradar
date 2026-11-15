#!/usr/bin/env python3
"""Language-neutral, cause-specific oracle for recorded late-completion traces.

Adapters must establish discovery/execution before calling evaluate. The CLI
validates recorded evidence only; it does not authenticate arbitrary producers.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import Any


class EvidenceError(ValueError):
    """Incomplete or invalid evidence: BLOCKED, never a behavioral kill."""


def validate_profile(profile: Any) -> list[dict[str, Any]]:
    if not isinstance(profile, dict) or type(profile.get('formatVersion')) is not int or profile['formatVersion'] != 1:
        raise EvidenceError('unsupported late-completion profile')
    for field in ('terminalState', 'acceptedState', 'acceptanceEffect'):
        if not isinstance(profile.get(field), str) or not profile[field]:
            raise EvidenceError('missing ' + field)
    if profile['terminalState'] == profile['acceptedState']:
        raise EvidenceError('accepted and terminal states must differ')
    cases = profile.get('cases')
    if not isinstance(cases, list) or not cases:
        raise EvidenceError('empty scenario discovery')
    ids, cells, orders = set(), set(), set()
    allowed = [('start', 'terminate', 'complete', 'observe'), ('start', 'complete', 'terminate', 'observe')]
    for case in cases:
        if not isinstance(case, dict):
            raise EvidenceError('scenario must be an object')
        for field in ('id', 'cell'):
            if not isinstance(case.get(field), str) or not case[field]:
                raise EvidenceError('invalid scenario ' + field)
        if ' x ' not in case['cell'] or case['id'] in ids or case['cell'] in cells:
            raise EvidenceError('invalid or duplicate scenario/cell')
        order = case.get('order')
        if not isinstance(order, list) or not all(isinstance(s, str) for s in order) or tuple(order) not in allowed:
            raise EvidenceError('unsupported completion ordering')
        ids.add(case['id']); cells.add(case['cell']); orders.add(tuple(order))
    if orders != set(allowed):
        raise EvidenceError('both late and positive-control orderings required')
    return cases


def evaluate(profile: Any, traces: Any, repetitions: int, weak: bool = False) -> dict[str, list[str]]:
    cases = validate_profile(profile)
    if type(repetitions) is not int or repetitions < 1 or not isinstance(traces, list):
        raise EvidenceError('invalid repetition count or traces')
    expected = {(c['id'], r) for c in cases for r in range(repetitions)}
    by_id = {c['id']: c for c in cases}
    seen = set()
    failures: dict[str, list[str]] = {}
    for trace in traces:
        if not isinstance(trace, dict) or not isinstance(trace.get('case'), str) or type(trace.get('repeat')) is not int:
            raise EvidenceError('invalid trace identity')
        key = (trace['case'], trace['repeat'])
        if key not in expected or key in seen:
            raise EvidenceError('unexpected/duplicate trace')
        seen.add(key)
        case = by_id[trace['case']]
        steps = trace.get('steps')
        if not isinstance(steps, list) or len(steps) != 4:
            raise EvidenceError('incomplete trace')
        resource = None
        prior_effects: list[str] = []
        prior_closes = 0
        for action, step in zip(case['order'], steps):
            if not isinstance(step, dict) or step.get('action') != action:
                raise EvidenceError('wrong event order')
            if not isinstance(step.get('state'), str) or not step['state'] or type(step.get('published')) is not bool:
                raise EvidenceError('invalid state/publication observation')
            if step.get('parentAlive') is not True:
                raise EvidenceError('parent cancellation invalidates isolation')
            if not isinstance(step.get('resource'), str) or not step['resource']:
                raise EvidenceError('missing resource identity')
            if resource is not None and step['resource'] != resource:
                raise EvidenceError('resource identity changed')
            resource = step['resource']
            closes = step.get('releaseCount')
            effects = step.get('effects')
            if type(closes) is not int or closes < prior_closes:
                raise EvidenceError('invalid/nonmonotonic resource releases')
            if not isinstance(effects, list) or not all(isinstance(e, str) for e in effects) or effects[:len(prior_effects)] != prior_effects:
                raise EvidenceError('invalid/nonmonotonic effect history')
            prior_closes, prior_effects = closes, effects
        by_action = {s['action']: s for s in steps}
        terminal = by_action['terminate']
        errors = []
        if terminal['state'] != profile['terminalState']:
            errors.append('termination did not establish terminal state')
        if not weak:
            start = by_action['start']
            if start['state'] in (profile['terminalState'], profile['acceptedState']) or start['releaseCount'] != 0 or profile['acceptanceEffect'] in start['effects']:
                errors.append('invalid pending operation setup')
            if terminal['published']:
                errors.append('termination retained publication')
            late = case['order'][1] == 'terminate'
            if not late:
                completed = by_action['complete']
                if (completed['state'] != profile['acceptedState'] or not completed['published'] or
                        completed['releaseCount'] != 0 or completed['effects'].count(profile['acceptanceEffect']) <= start['effects'].count(profile['acceptanceEffect'])):
                    errors.append('positive control did not observe accepted/live completion')
            for final in ([by_action['complete'], by_action['observe']] if late else [by_action['observe']]):
                if final['state'] != profile['terminalState']:
                    errors.append('terminal state violated')
                if final['published']:
                    errors.append('publication after termination')
                if final['releaseCount'] != 1:
                    errors.append('resource not released exactly once')
                if final['effects'] != terminal['effects']:
                    errors.append('effect emitted after termination')
        if errors:
            failures.setdefault(case['cell'], []).extend(f'repeat {key[1]}: {e}' for e in errors)
    if seen != expected:
        raise EvidenceError('empty/incomplete scenario discovery')
    return failures


def report(profile: Any, traces: Any, repetitions: int, weak: bool = False) -> int:
    failures = evaluate(profile, traces, repetitions, weak)
    for cell, reasons in failures.items():
        print('CELL FAIL ' + cell)
        for reason in sorted(set(reasons)):
            print('  ' + reason)
    print(f"CELL SUITE: {len(profile['cases'])} cells checked, {len(failures)} failed")
    return int(bool(failures))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('profile', type=Path); p.add_argument('observations', type=Path)
    p.add_argument('--count', type=int, default=1); p.add_argument('--weak', action='store_true')
    args = p.parse_args()
    try:
        return report(json.loads(args.profile.read_text()), json.loads(args.observations.read_text()), args.count, args.weak)
    except (EvidenceError, OSError, ValueError) as exc:
        print('BLOCKED: ' + str(exc)); return 2


if __name__ == '__main__':
    raise SystemExit(main())
