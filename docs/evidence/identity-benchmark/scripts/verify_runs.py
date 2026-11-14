"""Independently replay final model probes; never alter a model artifact."""
from collections import Counter
import json,shutil,subprocess,sys,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]

def completed(text):
    records=[json.loads(line) for line in text.splitlines() if line.startswith('{')]
    started=Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
    passed=Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
    if not started or started!=passed or any(n!=3 for n in started.values()):
        raise ValueError('probe suite must discover and complete every test three times')
    return passed

root=Path(sys.argv[1]).resolve()
results={}
for name in ('gobreaker-baseline','gobreaker-candidate','transfer-candidate','transfer-baseline'):
    run=root/name;source=run/'pool'
    assert json.loads((run/'phase-status.json').read_text())['controller']=='completed'
    with tempfile.TemporaryDirectory(prefix='identity-verify-') as tmp:
        repo=Path(tmp).resolve()/'source';shutil.copytree(source,repo)
        overlays=[(p,json.loads(p.read_text())) for p in (repo/'analysis').rglob('overlay*.json')]
        assert overlays, 'probe overlay required'
        overlay,data=max(overlays,key=lambda item:len(item[1]['Replace']))
        assert all(d['Replace'].items() <= data['Replace'].items() for _,d in overlays), 'ambiguous non-additive overlays'
        for target in data['Replace']:
            original=Path(target) if Path(target).is_absolute() else source/target
            assert str(target).endswith('_test.go') and not original.exists(), 'overlay may only inject new tests'
        print(name,'replay overlay',overlay.relative_to(repo))
        def remap(path):
            path=Path(path)
            return str(repo/path.relative_to(source)) if path.is_absolute() else str(repo/path)
        data['Replace']={remap(k):remap(v) for k,v in data['Replace'].items()}
        overlay.write_text(json.dumps(data))
        for label,pattern in ([('zero-discovery','^TestDoesNotExist$')] if name=='gobreaker-baseline' else [])+[('final','^TestIdentity')]:
            p=subprocess.run(['go','test','-race','-count=3','-timeout=30s','-json','-overlay',str(overlay),'-run',pattern,'.'],cwd=repo,text=True,capture_output=True,timeout=120)
            target=HERE/'results'/f'{name}-{label}'
            target.with_suffix('.jsonl').write_text(p.stdout)
            target.with_suffix('.stderr').write_text(p.stderr)
            if label=='zero-discovery':
                assert p.returncode==0
                try:completed(p.stdout)
                except ValueError:print('ZERO DISCOVERY: rejected despite go test exit 0')
                else:raise AssertionError('zero discovery was accepted')
                continue
            counts=completed(p.stdout);assert p.returncode==0
            report=json.loads((repo/'analysis/final.json').read_text())
            named={r['test'] for r in report['findings'] if r['test']!='untested'}
            assert named<=counts.keys(), f'unexecuted named probes: {named-counts.keys()}'
            results[name]={'exit':p.returncode,'passes':dict(counts),'top_level_tests':sum('/' not in n for n in counts),'reported_test_names':sorted(named)}
            print(name,results[name]['top_level_tests'],'top-level tests;',sum(counts.values()),'passes; source unmodified')
(HERE/'results/independent-replay.json').write_text(json.dumps(results,indent=2)+'\n')
