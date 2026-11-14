"""Execute immutable behavior tests with disposable scheduling/fault overlays."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
SOURCE = COMPONENT/'semaphore/semaphore.go'
SCHEDULE_TESTS = {
 'TestScheduleDR010FastLateCancel', 'TestScheduleDR010GrantedRollback',
 'TestScheduleDR010CancelSelectedRollback', 'TestScheduleDR010QueuedLateCancel',
 'TestScheduleDR011CancelBeforeMutex', 'TestScheduleDR012ReturnOrder',
}
ANCHORS = [
 ('\tdone := ctx.Done()\n', '\tdone := ctx.Done()\n\tcontractCheckpoint(s, "before-mutex", n)\n'),
 ('\tif s.size-s.cur >= n && s.waiters.Len() == 0 {', '\tcontractCheckpoint(s, "initial-checked", n)\n\tif s.size-s.cur >= n && s.waiters.Len() == 0 {'),
 ('\tcase <-done:\n\t\ts.mu.Lock()', '\tcase <-done:\n\t\tcontractCheckpoint(s, "cancel-selected", n)\n\t\ts.mu.Lock()'),
 ('\tcase <-ready:\n\t\t// Acquired', '\tcase <-ready:\n\t\tcontractCheckpoint(s, "grant-received", n)\n\t\t// Acquired'),
 ('\t\treturn nil\n\t}\n}\n\n// TryAcquire', '\t\tcontractCheckpoint(s, "queued-success", n)\n\t\treturn nil\n\t}\n}\n\n// TryAcquire'),
]
MUTATIONS = {
 'omit-grant-rollback': ('\t\t\ts.Release(n)\n', '\t\t\t// deliberately omitted grant rollback\n', 'TestScheduleDR010GrantedRollback'),
 'omit-selected-rollback': ('\t\t\ts.cur -= n\n', '\t\t\t// deliberately omitted selected rollback\n', 'TestScheduleDR010CancelSelectedRollback'),
 'try-bypass': ('success := s.size-s.cur >= n && s.waiters.Len() == 0', 'success := s.size-s.cur >= n', 'TestDR012HeadOfLineFIFO'),
 'zero-charges': ('\ts.cur -= n\n\ts.notifyWaiters()', '\tif n == 0 { s.cur++ }\n\ts.cur -= n\n\ts.notifyWaiters()', 'TestDR013ZeroRelease'),
}


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('scheduling/mutation anchor absent or ambiguous: ' + repr(old))
    return source.replace(old, new, 1)


def run(mode, count, output=None):
    source = SOURCE.read_text()
    names = SCHEDULE_TESTS
    if mode != 'baseline':
        old, new, test = MUTATIONS[mode]
        source = replace_once(source, old, new)
        names = {test}
    for old, new in ANCHORS:
        source = replace_once(source, old, new)
    with tempfile.TemporaryDirectory(prefix='semaphore-schedule-') as temp:
        root = Path(temp).resolve()
        altered = root/'semaphore.go'; altered.write_text(source)
        overlay = root/'overlay.json'
        overlay.write_text(json.dumps({'Replace': {
            str(SOURCE.resolve()): str(altered),
            str((COMPONENT/'semaphore/schedule_contract_test.go').resolve()): str((HERE/'checkpoints_test.go.txt').resolve()),
        }}))
        result = subprocess.run(['go','test','-race',f'-count={count}','-timeout=45s',
                                 '-overlay',str(overlay),'-run','^('+'|'.join(sorted(names))+')$',
                                 '-json','./semaphore'],cwd=COMPONENT,capture_output=True,text=True,timeout=90)
    if output:
        output.write_text(result.stdout + result.stderr)
    records=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
    started=Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
    passed=Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
    failed=Counter(r['Test'] for r in records if r.get('Action')=='fail' and 'Test' in r)
    expected=Counter({name:count for name in names})
    if mode == 'baseline':
        ok=result.returncode==0 and started==expected and passed==expected and not failed
    else:
        # A compiler crash, timeout, or wrong failure does not demonstrate test sensitivity.
        ok=(result.returncode!=0 and started==expected and failed==expected
            and any(r.get('Action')=='fail' and 'Test' not in r for r in records)
            and 'panic:' not in result.stdout and 'build failed' not in result.stdout)
    print(f'{mode}: exit={result.returncode}; started={dict(started)}; passed={dict(passed)}; failed={dict(failed)}')
    if not ok:
        print(result.stdout);print(result.stderr)
        raise SystemExit('BLOCKED: expected named, completed behavior verdict missing')
    print('SCHEDULE PASS' if mode=='baseline' else 'EXPECTED BEHAVIOR RED OBSERVED')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=['baseline',*MUTATIONS],default='baseline')
    parser.add_argument('--count',type=int,default=50)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    if args.count<1:parser.error('count must be positive')
    run(args.mode,args.count,args.output)
