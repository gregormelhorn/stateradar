"""Retain immutable final-review sessions and complete incremental/total costs."""
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[2]
PRIOR = HERE.parent / 'identity-benchmark'
spec = importlib.util.spec_from_file_location('prior_collect', PRIOR / 'scripts/collect.py')
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure(run):
    result = prior.collect(run)
    sys.path.insert(0, str(HERE / 'scripts'))
    from probe_logs import probe_runs
    result['probe_runs'] = probe_runs(run)
    result['probe_gate'] = bool(result['probe_runs']) and result['probe_runs'][-1]['passing_three_repetitions']
    result['bounded_acceptance'] = result['controller_complete'] and result['probe_gate'] and result['cost']['complete'] and result['structure_gate']['exit'] == 0
    pool = run / 'pool'
    assert sha(run / 'prompt.md') == result['settings']['prompt_sha256']
    assert sha(pool / 'immutable.json') == result['settings']['immutable_sha256']
    for name, expected in json.loads((pool / 'immutable.json').read_text()).items():
        assert sha(pool / name) == expected, 'immutable input drift: ' + name
    validation = subprocess.run([sys.executable, 'validate_postreview.py'], cwd=pool, capture_output=True, text=True)
    result['postreview_validation'] = {'exit': validation.returncode, 'stdout': validation.stdout, 'stderr': validation.stderr}
    result['bounded_acceptance'] = result['bounded_acceptance'] and validation.returncode == 0
    # Validate independently with the committed implementation too, rather than
    # trusting the child-local invocation's success message alone.
    sys.path.insert(0, str(ROOT / 'tools'))
    from finding_preservation import audit
    baseline = json.loads((pool / 'analysis/initial.json').read_text())
    final = json.loads((pool / 'analysis/final.json').read_text())
    supplement = json.loads((pool / 'analysis/supplement.json').read_text())
    result['preservation'] = audit(baseline, final, supplement)
    component = result['settings']['component']
    old = json.loads((PRIOR / 'measurements.json').read_text())[component + '-baseline']
    result['baseline_cost'] = old['cost']
    result['strategy_total_usd_estimate'] = (
        old['cost']['total_usd_estimate'] + result['cost']['total_usd_estimate']
        if old['cost']['complete'] and result['cost']['complete'] else None)
    result['new_findings'] = [r for r in final['findings'] if r['id'] not in {b['id'] for b in baseline['findings']}]
    result['supplement'] = supplement
    return result


def main():
    root = Path(sys.argv[1])
    dest = HERE / 'runs'
    if dest.exists():
        raise SystemExit('refuse to overwrite measured evidence')
    rows = {}
    for component in ('gobreaker', 'transfer'):
        for variant in ('generic', 'identity'):
            name = component + '-' + variant
            run = root / name
            rows[name] = measure(run)
            target = dest / name
            target.mkdir(parents=True)
            for path in run.iterdir():
                if path.is_file() and path.suffix in ('.json', '.jsonl', '.md', '.txt', '.stderr'):
                    shutil.copyfile(path, target / path.name)
            for folder in ('analysis', 'baseline'):
                shutil.copytree(run / 'pool' / folder, target / folder)
            shutil.copytree(run / 'logs', target / 'logs')
            (target / 'input').mkdir()
            for name in ('gobreaker.go', 'component.go', 'README.md', 'go.mod', 'go.sum', 'LICENSE',
                         'validate_report.py', 'validate_postreview.py', 'finding_preservation.py', 'immutable.json'):
                if (run / 'pool' / name).is_file():
                    shutil.copyfile(run / 'pool' / name, target / 'input' / name)
            hashes = {str(p.relative_to(target)): sha(p) for p in sorted(target.rglob('*')) if p.is_file()}
            (target / 'hashes.json').write_text(json.dumps(hashes, indent=2) + '\n')
        a, b = [root / (component + '-' + v) for v in ('generic', 'identity')]
        excluded = ('variant', 'prompt_sha256')
        assert {k: v for k, v in rows[a.name]['settings'].items() if k not in excluded} == {k: v for k, v in rows[b.name]['settings'].items() if k not in excluded}
        assert (b / 'prompt.md').read_text() == (a / 'prompt.md').read_text() + '\n' + (HERE / 'prompts/identity.md').read_text()
    (HERE / 'measurements.json').write_text(json.dumps(rows, indent=2) + '\n')
    for name, row in rows.items():
        print(name, 'preservation', row['preservation'], 'incremental', row['cost']['total_usd_estimate'],
              'strategy total', row['strategy_total_usd_estimate'], 'rereads', row['log_rereads'],
              'failed commands', len(row['nonzero_commands']), 'bounded acceptance', row['bounded_acceptance'])
    print('Matched source/baseline/validator/settings and candidate-only prompt delta: PASS')


if __name__ == '__main__':
    main()
