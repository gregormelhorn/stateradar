#!/usr/bin/env python3
"""Run all accepted semaphore decisions; reject empty/partial Go discovery."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parents[1] / 'docs/evidence/semaphore-pilot/resolution-q01'
EXPECTED = {
    'TestDR001FullSingleZero', 'TestDR001FullZeroPrefix',
    'TestDR001SpareCapacity', 'TestDR001RetainedHeadPreservesFIFO',
    'TestDR001ZeroTryDoesNotBypass',
}


NUMERIC_EVIDENCE = EVIDENCE.parent / 'resolution-q02-q04'
EXPECTED.update({
    'TestDR002NegativeConstructor', 'TestDR002NegativeAcquire',
    'TestDR002NegativeTryAcquire', 'TestDR002NegativeRelease',
    'TestDR002ZeroAndMaxBoundaries', 'TestDR003OverReleaseEmptyPartialFull',
    'TestDR003OverReleaseQueued', 'TestDR003OverReleaseMax',
    'TestDR004OversizedImmediateError', 'TestDR004PreCanceledOversized',
})
TOP_LEVEL_COUNT = len(EXPECTED)
for name in ('MinusOne', 'MinInt64'):
    EXPECTED.add('TestDR002NegativeConstructor/' + name)
    for method in ('Acquire', 'TryAcquire', 'Release'):
        prefix = f'TestDR002Negative{method}/{name}'
        for setup in ('Empty', 'Full', 'Queued', 'PreCanceled'):
            EXPECTED.add(prefix + '/' + setup)
for test, cases in {
    'TestDR002ZeroAndMaxBoundaries': ('Zero', 'MaxInt64', 'QueuedMaxInt64'),
    'TestDR003OverReleaseEmptyPartialFull': ('Empty', 'Partial', 'Full'),
    'TestDR004OversizedImmediateError': ('Empty', 'Queued'),
}.items():
    EXPECTED.update(test + '/' + case for case in cases)


def validate_results(output, count):
    records = [json.loads(line) for line in output.splitlines() if line.strip()]
    failures = [r for r in records if r.get('Action') == 'fail']
    passed = Counter(r['Test'] for r in records if r.get('Action') == 'pass' and 'Test' in r)
    started = Counter(r['Test'] for r in records if r.get('Action') == 'run' and 'Test' in r)
    expected = Counter({name: count for name in EXPECTED})
    package = 'golang.org/x/sync/semaphore'
    if (failures or passed != expected or started != expected
            or any(r.get('Package') != package for r in records)
            or not any(r.get('Action') == 'pass' and 'Test' not in r for r in records)):
        raise ValueError(f'Decision discovery/results: expected {len(EXPECTED)} named tests x {count}; '
                         f'observed {dict(passed)}, failures={len(failures)}')
    print(f'DR-001..004: {TOP_LEVEL_COUNT} test groups x {count} = {TOP_LEVEL_COUNT * count} group passes; '
          f'all {len(EXPECTED)} test/subtest names verified; no empty discovery')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--results', type=Path, help='validate a retained Go JSON stream only')
    parser.add_argument('--count', type=int, default=50)
    args = parser.parse_args()
    if args.count < 1:
        parser.error('--count must be positive')
    if args.results:
        validate_results(args.results.read_text(), args.count)
        return
    # Exercise the discovery failure path on every CI run.
    try:
        validate_results('', args.count)
    except ValueError:
        print('RED-PROBE: empty discovery rejected')
    else:
        raise RuntimeError('empty discovery unexpectedly accepted')
    subprocess.run([sys.executable, str(EVIDENCE / 'check_guards.py')], check=True, timeout=30)
    subprocess.run([sys.executable, str(NUMERIC_EVIDENCE / 'check_numeric.py')], check=True, timeout=30)
    result = subprocess.run(['go', 'test', '-race', f'-count={args.count}', '-timeout=60s',
                             '-run', '^TestDR00[1234]', '-json', './semaphore'],
                            cwd=HERE, text=True, capture_output=True, timeout=120)
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
    validate_results(result.stdout, args.count)
    subprocess.run(['go', 'test', '-race', '-count=1', '-timeout=60s', './...'],
                   cwd=HERE, check=True, timeout=120)
    print('All accepted decision guard checks, focused race suite and upstream regression suite passed.')


if __name__ == '__main__':
    main()
