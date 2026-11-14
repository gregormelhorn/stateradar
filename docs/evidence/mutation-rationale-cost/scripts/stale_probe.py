"""Post-run quality diagnostic: can each unchanged pilot suite detect stale-accounting corruption?"""
from collections import Counter
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
run=Path(sys.argv[1]).resolve();out=Path(sys.argv[2]);out.mkdir(parents=True,exist_ok=True)
original=run/'selective/pool';adir=Path('domain-analysis/circuitBreaker')
phase=json.loads((run/'selective/phase-status.json').read_text())
assert phase['controller']!='running', 'audit only a finalized pilot'
with tempfile.TemporaryDirectory(prefix='stateradar-stale-probe-') as tmp:
    repo=Path(tmp)/'pool';shutil.copytree(original,repo,ignore=shutil.ignore_patterns('__pycache__'))
    repo=repo.resolve() # Go resolves macOS /var aliases before matching overlay keys.
    overlays=list((repo/adir).rglob('overlay.json'))
    assert len(overlays)==1, 'expected one retained probe overlay'
    overlay=overlays[0];data=json.loads(overlay.read_text())
    def remap(value):
        p=Path(value)
        return str(repo/p.relative_to(original)) if p.is_absolute() else str(repo/p)
    data['Replace']={remap(k):remap(v) for k,v in data['Replace'].items()}
    overlay.write_text(json.dumps(data))
    source=repo/'gobreaker.go';before=source.read_text()
    anchor='if generation != before {'
    assert before.count(anchor)==1, 'generation guard anchor drift'
    rows={}
    for name in ('baseline','generation-guard-disabled'):
        if name!='baseline':source.write_text(before.replace(anchor,'if false && generation != before {'))
        cmd=['go','test','-race','-count=5','-timeout=60s','-json','-overlay',str(overlay),'-run','^TestPilot','.']
        result=subprocess.run(cmd,cwd=repo,capture_output=True,text=True,timeout=90)
        (out/f'{name}.jsonl').write_text(result.stdout)
        (out/f'{name}.stderr').write_text(result.stderr)
        records=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        started=Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
        passed=Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
        failed=Counter(r['Test'] for r in records if r.get('Action')=='fail' and 'Test' in r)
        if not started or started!=passed+failed or any(n!=5 for n in started.values()):
            raise ValueError('incomplete test discovery or compile/runtime failure; not a behavioral verdict')
        if name=='baseline':
            assert result.returncode==0 and not failed, 'baseline must pass'
            expected=started
        else:assert started==expected, 'mutant changed test discovery'
        rows[name]={'exit':result.returncode,'started':dict(started),'passed':dict(passed),'failed':dict(failed)}
    rows['diagnostic']='KILLED' if rows['generation-guard-disabled']['failed'] else 'SURVIVED'
    rows['mutation']={'source':'gobreaker.go','old':anchor,'new':'if false && generation != before {'}
    rows['scope']='Post-run diagnostic only; not a predeclared primary control. No pilot artifact was repaired.'
    (out/'result.json').write_text(json.dumps(rows,indent=2)+'\n')
    print(json.dumps({'diagnostic':rows['diagnostic'],'failed':rows['generation-guard-disabled']['failed']},indent=2))
