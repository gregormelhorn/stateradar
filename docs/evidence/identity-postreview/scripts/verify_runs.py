"""Independently replay complete old and new suites; retain every named result."""
from collections import Counter
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]


def completed(text):
    records = [json.loads(line) for line in text.splitlines() if line.startswith('{')]
    started = Counter(r['Test'] for r in records if r.get('Action') == 'run' and 'Test' in r)
    passed = Counter(r['Test'] for r in records if r.get('Action') == 'pass' and 'Test' in r)
    if not started or started != passed or any(n != 3 for n in started.values()):
        raise ValueError('every discovered test must pass exactly three times; empty discovery rejected')
    return passed


def main():
    root = Path(sys.argv[1]).resolve()
    report_path = HERE / 'results/independent-replay.json'
    results = json.loads(report_path.read_text()) if report_path.exists() else {}
    all_names = ('gobreaker-generic', 'gobreaker-identity', 'transfer-identity', 'transfer-generic')
    names = sys.argv[2:] or all_names
    assert all(name in all_names and name not in results for name in names), 'unknown or already replayed session'
    for name in names:
        run = root / name
        assert json.loads((run / 'phase-status.json').read_text())['controller'] == 'completed'
        with tempfile.TemporaryDirectory(prefix='postreview-replay-') as tmp:
            repo = Path(tmp).resolve() / 'source'
            shutil.copytree(run / 'pool', repo)
            check = subprocess.run([sys.executable, 'validate_postreview.py'], cwd=repo, capture_output=True, text=True)
            assert check.returncode == 0, check.stdout + check.stderr
            for label, pattern in ([('zero', '^TestDoesNotExist$')] if name == 'gobreaker-generic' else []) + [('final', '^TestIdentity')]:
                command = ['go', 'test', '-race', '-count=3', '-timeout=30s', '-json',
                           '-overlay', 'analysis/overlay-final.json', '-run', pattern, '.']
                result = subprocess.run(command, cwd=repo, capture_output=True, text=True, timeout=150)
                target = HERE / 'results' / (name + '-' + label)
                target.with_suffix('.jsonl').write_text(result.stdout)
                target.with_suffix('.stderr').write_text(result.stderr)
                if label == 'zero':
                    assert result.returncode == 0
                    try:
                        completed(result.stdout)
                    except ValueError:
                        print('ZERO DISCOVERY: rejected despite go test exit 0')
                    else:
                        raise AssertionError('empty discovery accepted')
                    continue
                assert result.returncode == 0, result.stderr
                counts = completed(result.stdout)
                report = json.loads((repo / 'analysis/final.json').read_text())
                supplement = json.loads((repo / 'analysis/supplement.json').read_text())
                named = {r['test'] for r in report['findings'] if r['test'] != 'untested'}
                named |= {r['test'] for r in supplement['test_bindings']}
                assert named <= counts.keys(), 'unexecuted named probe'
                if name.startswith('transfer'):
                    assert counts['TestIdentityCallerVariableRebinding'] == 3
                results[name] = {'exit': result.returncode, 'passes': dict(counts),
                                 'top_level_tests': sum('/' not in n for n in counts),
                                 'reported_test_names': sorted(named)}
                print(name, results[name]['top_level_tests'], 'top-level tests;', sum(counts.values()),
                      'pass events; original and new probes executed; inputs unchanged')
    report_path.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
