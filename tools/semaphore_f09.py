#!/usr/bin/env python3
"""Executed F-09 slice: independent capacity canary, weak survivor, full cell kill."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import tempfile

from check_fault_mutants import CommandResult, copy_component, load_config, run_command
from mutation_verdict import cell_verdict

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / 'examples/weighted-semaphore/domain-analysis/weightedSemaphore'
CELL = 'Acquire_WaitersPending x ContextDone'
CANARY_CELL = 'Acquire_NoWaiters x Release'


def classify(result: CommandResult, cell: str, count: int) -> str:
    if result.timed_out or result.launch_error:
        return 'BLOCKED'
    try:
        verdict = cell_verdict(result.output, count)
    except ValueError:
        return 'BLOCKED'
    if result.returncode == 0 and not verdict.failed:
        return 'SURVIVED'
    if result.returncode == 1 and cell in verdict.failed:
        return 'KILLED'
    return 'BLOCKED'


def require_canary(verdict: str) -> None:
    if verdict != 'KILLED':
        raise RuntimeError('BLOCKED: capacity canary '+verdict+'; dependent F-09 not executed')


def compare(execute):
    rows = []
    for label, mutant, suite, cell, expected in (
        ('full-baseline', None, 'full', CELL, 'SURVIVED'),
        ('weak-baseline', None, 'weak', CELL, 'SURVIVED'),
        ('capacity-canary', 'zero-charges', 'full', CANARY_CELL, 'KILLED'),
        ('weak-canary-control', 'zero-charges', 'weak', CELL, 'SURVIVED'),
        ('weak-f09', 'omit-cancel-unlink', 'weak', CELL, 'SURVIVED'),
        ('full-f09', 'omit-cancel-unlink', 'full', CELL, 'KILLED'),
    ):
        result = execute(label, mutant, suite)
        verdict = classify(result, cell, 34 if suite == 'full' else 1)
        row = {'run': label, 'mutant': mutant, 'suite': suite,
               'verdict': verdict, 'expected': expected, 'exit': result.returncode,
               'seconds': round(result.duration_seconds, 3)}
        rows.append(row)
        print(f'{label}: {verdict} (expected {expected})', flush=True)
        if label == 'capacity-canary':
            require_canary(verdict)
        elif verdict != expected:
            raise RuntimeError(f'BLOCKED: {label}: expected {expected}, got {verdict}')
        if label == 'weak-canary-control':
            try:
                require_canary(verdict)
            except RuntimeError as exc:
                print('EXPECTED CONTROL '+str(exc), flush=True)
            else:
                raise RuntimeError('weak canary incorrectly authorized F-09')
    return rows


def weak_command(component: Path, count: int = 10) -> CommandResult:
    import time
    started = time.monotonic()
    component = component.resolve()
    overlay = component / 'f09-overlay.json'
    overlay.write_text(json.dumps({'Replace': {
        str(component/'semaphore/f09_weak_test.go'): str(component/'faults/weak_test.go.txt'),
    }}))
    try:
        run = subprocess.run(['go', 'test', '-race', f'-count={count}', '-timeout=30s',
            '-overlay', str(overlay), '-run', '^TestF09WeakCancelResult$', '-json', './semaphore'],
            cwd=component, capture_output=True, text=True, timeout=45)
    except subprocess.TimeoutExpired:
        return CommandResult(None, 'weak suite timeout', time.monotonic()-started, timed_out=True)
    records = [json.loads(line) for line in run.stdout.splitlines() if line.startswith('{')]
    names = Counter({'TestF09WeakCancelResult': count})
    seen = lambda action: Counter(r['Test'] for r in records if r.get('Action') == action and 'Test' in r)
    output = run.stdout + run.stderr
    if (run.returncode == 0 and seen('run') == names and seen('pass') == names
            and not seen('fail') and any(r.get('Action') == 'pass' and 'Test' not in r for r in records)):
        output += '\nCELL SUITE: 1 cells checked, 0 failed\n'
    # Compilation failures, zero discovery and partial runs never become survivors.
    return CommandResult(run.returncode, output, time.monotonic()-started)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path)
    args = parser.parse_args()
    config, mutants = load_config(ANALYSIS)
    by_id = {m.identifier: m for m in mutants}
    if (by_id['omit-cancel-unlink'].fault != 'F-09' or
            by_id['omit-cancel-unlink'].cell != CELL or by_id['zero-charges'].cell != CANARY_CELL):
        raise RuntimeError('BLOCKED: declared mutant fault/cell changed')
    bindings = json.loads((ANALYSIS/'mutant-generation.json').read_text())
    binding = next(b for b in bindings['bindings'] if b['id'] == 'omit-cancel-unlink')
    if (binding['requiresProjection'] != 'available_capacity' or
            bindings['projections']['available_capacity']['provenBy'] != 'zero-charges'):
        raise RuntimeError('BLOCKED: F-09 projection/canary binding changed')
    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='semaphore-f09-') as td:
        def execute(label, identifier, suite):
            component = copy_component(config.component_root, Path(td), label)
            if identifier:
                mutant = by_id[identifier]
                (component/mutant.target).write_text((component/mutant.variant).read_text())
            full_config = config
            if args.output_dir and suite == 'full':
                full_config = replace(config, command=config.command +
                    ('--output', str((args.output_dir/(label+'.go.jsonl')).resolve())))
            result = run_command(full_config, component) if suite == 'full' else weak_command(component)
            if args.output_dir:
                (args.output_dir/(label+'.txt')).write_text(result.output)
            return result
        rows = compare(execute)
    if args.output_dir:
        (args.output_dir/'results.json').write_text(json.dumps(rows, indent=2)+'\n')
    print('F-09 PASS: canary killed; weak mutant survived; full mutant killed at '+CELL)


if __name__ == '__main__':
    main()
