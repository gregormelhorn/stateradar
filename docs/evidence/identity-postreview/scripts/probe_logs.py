"""Read actual go-test command logs, including output not copied into analysis/."""
from collections import Counter
import json


def probe_runs(root):
    result = []
    for path in sorted((root / 'logs').glob('*.json')):
        metadata = json.loads(path.read_text())
        argv = metadata.get('argv', [])
        if argv[:2] != ['go', 'test']:
            continue
        if '-run' not in argv or argv[argv.index('-run') + 1] != '^TestIdentity':
            continue
        output = path.with_suffix('.stdout')
        records = [json.loads(line) for line in output.read_text().splitlines() if line.startswith('{')]
        started = Counter(r['Test'] for r in records if r.get('Action') == 'run' and 'Test' in r)
        passed = Counter(r['Test'] for r in records if r.get('Action') == 'pass' and 'Test' in r)
        failed = Counter(r.get('Test', '<package>') for r in records if r.get('Action') == 'fail')
        skipped = [r.get('Test', '<package>') for r in records if r.get('Action') == 'skip']
        complete = bool(started) and started == passed and not failed and not skipped
        result.append({'file': str(output.relative_to(root)), 'exit': metadata['exit_code'],
                       'started': dict(started), 'passed': dict(passed), 'failed': dict(failed),
                       'skipped': skipped, 'passing_three_repetitions': complete and
                       metadata['exit_code'] == 0 and all(n == 3 for n in passed.values())})
    return result
