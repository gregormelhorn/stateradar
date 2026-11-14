"""Readiness probe only: replay one upstream test against pinned source and one overlay."""
import argparse
from collections import Counter
import json
from pathlib import Path
import subprocess
import tempfile

PIN='a02b0774206b209466313a0b525d2c738fe407eb'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('checkout',type=Path)
p.add_argument('--output-dir',type=Path,required=True)
a=p.parse_args(); root=a.checkout.resolve(); out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
if sha!=PIN or subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip():
    raise SystemExit('BLOCKED: requires clean pinned grpc-go checkout')
source=root/'clientconn.go';text=source.read_text();anchor='\tac.cancel()\n'
if text.count(anchor)!=1:raise SystemExit('BLOCKED: cancellation anchor drift')
summary={'sha':sha,'go':subprocess.check_output(['go','version'],text=True).strip(),'runs':[]}
with tempfile.TemporaryDirectory(prefix='addrconn-readiness-') as td:
    temp=Path(td).resolve(); changed=temp/'clientconn.go'
    changed.write_text(text.replace(anchor,'\t// readiness probe: omitted addrConn cancellation\n'))
    overlay=temp/'overlay.json';overlay.write_text(json.dumps({'Replace':{str(source):str(changed)}}))
    for name,extra in [('baseline',[]),('omit-addrconn-cancel',['-overlay',str(overlay)])]:
        command=['go','test','-mod=readonly','-race','-count=10','-timeout=90s',*extra,'-run','^Test/BackoffCancel$','-json','.']
        run=subprocess.run(command,cwd=root,capture_output=True,text=True,timeout=120)
        (out/(name+'.jsonl')).write_text(run.stdout+run.stderr)
        records=[json.loads(line) for line in run.stdout.splitlines() if line.startswith('{')]
        expected=Counter({'Test':10,'Test/BackoffCancel':10})
        seen=lambda action:Counter(r['Test'] for r in records if r.get('Action')==action and 'Test' in r)
        complete=seen('run')==expected and seen('pass')+seen('fail')==expected
        passing=complete and run.returncode==0 and seen('pass')==expected
        summary['runs'].append({'name':name,'exit':run.returncode,'complete':complete,'passing':passing,'passes':dict(seen('pass'))})
        if not complete:raise SystemExit('BLOCKED: empty/incomplete upstream discovery')
        print(f'{name}: exit={run.returncode}; complete={complete}; passing={passing}; named repetitions=10')
        if not passing:raise SystemExit('Readiness changed: inspect upstream failure before interpreting it')
(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print('READINESS: upstream test passes baseline and omitted-cancel overlay; no F-09 kill proof')
