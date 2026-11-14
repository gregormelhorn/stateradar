#!/usr/bin/env python3
"""Run the focused DR-001 acceptance gate; reject empty/partial Go discovery."""
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
        raise ValueError(f'DR-001 discovery/results: expected {len(EXPECTED)} named tests x {count}; '
                         f'observed {dict(passed)}, failures={len(failures)}')
    print(f'DR-001: {len(EXPECTED)} named scenarios x {count} = {5 * count} passes; no empty discovery')


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
    result = subprocess.run(['go', 'test', '-race', f'-count={args.count}', '-timeout=60s',
                             '-run', '^TestDR001', '-json', './semaphore'],
                            cwd=HERE, text=True, capture_output=True, timeout=120)
    if result.returncode:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        result.check_returncode()
    validate_results(result.stdout, args.count)
    subprocess.run(['go', 'test', '-race', '-count=1', '-timeout=60s', './...'],
                   cwd=HERE, check=True, timeout=120)
    print('DR-001 guard proof, focused race suite and upstream regression suite passed.')


if __name__ == '__main__':
    main()
