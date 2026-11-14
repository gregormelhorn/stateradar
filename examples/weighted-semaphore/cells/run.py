"""Run public-seam cell scenarios against the supplied matrix, with exact discovery."""
import argparse
from collections import Counter
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
DEFAULT = COMPONENT / 'domain-analysis/weightedSemaphore'
spec = importlib.util.spec_from_file_location('schedule_overlay', COMPONENT/'schedule/run.py')
assert spec and spec.loader
schedule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(schedule)


def run(analysis=DEFAULT, count=10, output=None, red_probe=False, mutation_check=False):
    analysis = analysis.resolve()
    model = json.loads((analysis/'analysis.json').read_text())
    tests = {'TestStateCells/'+c['state']+'/'+c['event'] for c in model['cells']
             if c['event'] not in ('UV-Delay', 'UV-ContextFault')}
    if len(tests) != 34 or len(model['cells']) != 38:
        raise SystemExit('BLOCKED: cell discovery requires 34 tests and four declared contract limits')
    source = schedule.SOURCE.read_text()
    for old, new in schedule.ANCHORS:
        source = schedule.replace_once(source, old, new)
    with tempfile.TemporaryDirectory(prefix='semaphore-cells-') as tmp:
        root = Path(tmp).resolve()
        if red_probe:
            for c in model['cells']:
                if (c['state'], c['event']) == ('Acquire_NoWaiters', 'TryAcquire'):
                    c['disposition'] = 'reject'
            (root/'analysis.json').write_text(json.dumps(model))
            analysis = root
        (root/'semaphore.go').write_text(source)
        (root/'overlay.json').write_text(json.dumps({'Replace': {
            str(schedule.SOURCE): str(root/'semaphore.go'),
            str(COMPONENT/'semaphore/schedule_contract_test.go'): str(COMPONENT/'schedule/checkpoints_test.go.txt'),
            str(COMPONENT/'semaphore/state_cells_test.go'): str(HERE/'state_cells_test.go.txt'),
        }}))
        result = subprocess.run(['go','test','-race',f'-count={count}','-timeout=90s',
            '-overlay',str(root/'overlay.json'),'-run','^TestState(Cells|Pairs)$','-json','./semaphore'],
            cwd=COMPONENT, env={**os.environ, 'STATERADAR_CELL_ANALYSIS':str(analysis)},
            capture_output=True, text=True, timeout=150)
    if output:
        Path(output).write_text(result.stdout+result.stderr)
    records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    # Slash-separated names are a single t.Run invocation, not parent tests.
    names = tests | {'TestStateCells','TestStatePairs'} | {f'TestStatePairs/P-{i:02}{o}' for i in range(1,9) for o in 'ab'}
    started = Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
    passed = Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
    failed = Counter(r['Test'] for r in records if r.get('Action')=='fail' and 'Test' in r)
    expected = Counter({n:count for n in names})
    complete = (sum('CELL SUITE: 34 cells checked,' in r.get('Output','') for r in records)==count
                and sum('PAIR SUITE: 16 orderings completed' in r.get('Output','') for r in records)==count)
    if mutation_check:
        # Only completed, exactly discovered Go verdicts reach the generic checker.
        # Compiler failures, panics, truncated loops and missing tests emit no completion marker.
        if count!=1 or started!=expected or passed+failed!=expected or not complete:
            print(result.stdout); print(result.stderr)
            raise SystemExit('BLOCKED: incomplete Go behavior verdict')
        for record in records:
            line=record.get('Output','').strip()
            if line.startswith(('CELL FAIL ','CELL SUITE: ')):print(line)
        raise SystemExit(result.returncode)
    if red_probe:
        bad = {'TestStateCells/Acquire_NoWaiters/TryAcquire', 'TestStateCells'}
        # testing.T.Run with slashes does not create independent parent invocations.
        bad |= {n for n in failed if n == 'TestStateCells/Acquire_NoWaiters'}
        ok = result.returncode != 0 and started == expected and complete and failed == Counter({n:count for n in bad})
    else:
        ok = result.returncode == 0 and started == expected and passed == expected and complete and not failed
    print(f'CELL {"RED PROBE" if red_probe else "BASELINE"}: exit={result.returncode}; executable=34; contract-limits=4; repeats={count}; completed={complete}; failures={dict(failed)}')
    if not ok:
        print('started:',dict(started)); print(result.stdout); print(result.stderr)
        raise SystemExit('BLOCKED: expected complete cell verdict missing')
    print('EXPECTED CELL RED OBSERVED' if red_probe else f'CELL PASS: {34*count} cell and {16*count} pair-ordering executions')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--analysis',type=Path,default=DEFAULT)
    p.add_argument('--count',type=int,default=10)
    p.add_argument('--output',type=Path)
    p.add_argument('--red-probe',action='store_true')
    p.add_argument('--mutation-check',action='store_true',help='emit completed behavior markers and preserve the Go exit code')
    a=p.parse_args()
    if a.count<1: p.error('positive count required')
    run(a.analysis,a.count,a.output,a.red_probe,a.mutation_check)
