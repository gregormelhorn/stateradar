"""Reproducible current-model acceptance; no model calls and no artifact writes."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PYTHON=sys.executable


def command(args,expected=0,contains=None):
    result=subprocess.run([PYTHON,*map(str,args)],cwd=ROOT,capture_output=True,text=True)
    print('$ python '+' '.join(map(str,args)),flush=True)
    print(result.stdout,end='',flush=True)
    if result.stderr:print(result.stderr,end='',flush=True)
    if result.returncode!=expected or (contains and contains not in result.stdout+result.stderr):
        raise SystemExit('BLOCKED: acceptance command did not produce the required verdict')


def main():
    command([HERE/'check_matrix.py','--selftest'])
    command(['tools/check_matrix.py',HERE])
    command([HERE/'check_guards.py'])
    with tempfile.TemporaryDirectory(prefix='semaphore-guard-red-') as temp:
        source=ROOT/'examples/weighted-semaphore/semaphore/semaphore.go'
        old=Path(temp)/'old.go'
        text=source.read_text()
        if text.count('if isFront {')!=1:raise SystemExit('head guard anchor drift')
        old.write_text(text.replace('if isFront {','if isFront && s.size > s.cur {'))
        command(['docs/evidence/semaphore-pilot/resolution-q01/check_guards.py','--source',old],1,'Counterexample:')
        command([HERE/'check_guards.py','--source',old],1,'GUARD FAIL: reviewed source digest changed')
    command(['examples/weighted-semaphore/cells/run.py','--red-probe','--count','1'])
    command(['examples/weighted-semaphore/cells/run.py'])
    model='to-be.machine.mmd' if (HERE/'to-be.machine.mmd').is_file() else 'as-is.machine.mmd'
    command(['tools/dsc_check.py',HERE,'--repo','.', '--model',model])
    command(['tools/check_reachability.py',HERE])
    frozen=ROOT/'docs/evidence/semaphore-pilot'
    retained=json.loads((frozen/'retained-hashes.json').read_text())
    for name,expected in retained.items():
        raw=(frozen/name).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected['sha256'] or len(raw)!=expected['bytes']:
            raise SystemExit('BLOCKED: historical artifact changed: '+name)
    print(f'HISTORY PASS: {len(retained)} retained artifacts unchanged')
    print('CURRENT MODEL PASS: full matrix; explicit limits; guards; red probes; cells; pair scenarios; sidecar; reachability')


if __name__=='__main__':main()
