"""Replay immutable archived probes and the eight-case executable reference."""
from collections import Counter
import argparse, json, shutil, subprocess, tempfile
from pathlib import Path
REPO=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parents[1]
OLD=REPO/'docs/evidence/mutation-rationale-cost/runs'
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-repo',type=Path,default=Path('/tmp/stateradar-mutation-cost-routed/selective/pool'))
SOURCE=parser.parse_args().source_repo.resolve()
SHA='27b8e2cfc65aacd09abb3968455e4b01df4a83fa'

def run(repo,label,pattern,count,expected,overlay=None):
    cmd=['go','test','-race',f'-count={count}','-timeout=60s','-json','-run',pattern]
    if overlay:cmd+=['-overlay',str(overlay)]
    cmd+=['.']
    p=subprocess.run(cmd,cwd=repo,text=True,capture_output=True,timeout=120)
    (HERE/'results'/f'{label}.jsonl').write_text(p.stdout)
    (HERE/'results'/f'{label}.stderr').write_text(p.stderr)
    records=[json.loads(line) for line in p.stdout.splitlines() if line.startswith('{')]
    runs=Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
    passes=Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
    names={n for n in runs if '/' not in n}
    assert expected and runs and p.returncode==0 and runs==passes and names==set(expected) and all(n==count for n in runs.values()),(label,p.returncode,runs,passes,p.stderr)
    print(f'{label}: {len(names)} top-level tests, {sum(passes.values())} test/subtest passes, {count} race repetitions')

with tempfile.TemporaryDirectory(prefix='identity-proof-') as tmp:
    repo=Path(tmp).resolve()/'source';repo.mkdir()
    subprocess.run(['tar','-xf','-'],cwd=repo,input=subprocess.check_output(['git','archive',SHA],cwd=SOURCE),check=True)
    for arm,filename in [('routed','as_is_test.go'),('matrix','pilot_test.go')]:
        probe=OLD/arm/'domain-analysis/circuitBreaker/_probe'/filename
        target=repo/'benchmark_test.go';shutil.copyfile(probe,target)
        import re
        names=re.findall(r'^func (TestPilot\w+)\(',probe.read_text(),re.M)
        run(repo,arm+'-replay','^TestPilot',5,names)
        target.unlink()
    shutil.copyfile(OLD/'routed/domain-analysis/circuitBreaker/_probe/as_is_test.go',repo/'routed_test.go')
    shutil.copyfile(HERE/'fixtures/additional_test.go.txt',repo/'additional_test.go')
    names=['TestPilotExpiryAndStaleReport','TestPilotDuplicateDone','TestPilotAbandonAndLateReport','TestPilotCallbackReentry','TestPilotCallbackPanics','TestBenchmarkWrapperReassignment','TestBenchmarkOutstandingAllow','TestBenchmarkStaleResultAndError']
    run(repo,'benchmark-proof','^('+'|'.join(names)+')$',5,names)
    fixture=Path(tmp).resolve()/'transfer';shutil.copytree(HERE/'fixtures/transfer',fixture)
    shutil.copyfile(fixture/'oracle_test.go.txt',fixture/'oracle_test.go')
    run(fixture,'transfer-proof','^TestTransferOracle$',5,['TestTransferOracle'])
