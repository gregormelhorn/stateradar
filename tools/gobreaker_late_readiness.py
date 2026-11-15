#!/usr/bin/env python3
"""Bounded public-API readiness probe; not a second terminal/resource adapter."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from check_late_workflow import check_plan, sha, require

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/evidence/identity-postreview/runs/gobreaker-identity/input'
FIXTURE=ROOT/'examples/gobreaker/late-completion-readiness'
PIN='09a38e4ec94ee22405cea8a64bce908bfa764a5e8bc65a69016e1cf86bf3b1cc'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',type=Path)
    a=p.parse_args()
    require(sha(SOURCE/'gobreaker.go')==PIN,'archived source content pin mismatch')
    check_plan(FIXTURE/'workflow.json',ROOT)
    with tempfile.TemporaryDirectory(prefix='gobreaker-late-readiness-') as td:
        root=Path(td);out=a.output_dir.resolve() if a.output_dir else root/'evidence';out.mkdir(parents=True,exist_ok=True)
        for name in ('gobreaker.go','go.mod','go.sum'):shutil.copyfile(SOURCE/name,root/name)
        shutil.copyfile(FIXTURE/'probe_test.go.txt',root/'late_readiness_test.go')
        source=(root/'gobreaker.go').read_text();guard='\tif generation != before {\n\t\treturn\n\t}'
        require(source.count(guard)==1,'ambiguous generation guard')
        for label,count in [('baseline',10),('without-generation-guard',5)]:
            if label!='baseline':
                # Keep unused locals compilable without changing other behavior.
                changed=source.replace(guard,'\t_ = generation // readiness mutant: stale completions count')
                (root/'gobreaker.go').write_text(changed)
            run=subprocess.run(['go','test','-mod=readonly','-race','-count='+str(count),'-timeout=30s','-run','^TestStaleCompletionReadiness$','-json','.'],cwd=root,text=True,capture_output=True,timeout=90)
            (out/(label+'.go.jsonl')).write_text(run.stdout+run.stderr)
            records=[json.loads(l) for l in run.stdout.splitlines() if l.startswith('{')]
            seen=lambda action:Counter(r['Test'] for r in records if r.get('Action')==action and 'Test' in r)
            expected=Counter({'TestStaleCompletionReadiness':count})
            require(seen('run')==expected,'incomplete readiness discovery')
            verdict='pass' if label=='baseline' else 'fail'
            require(run.returncode==(0 if label=='baseline' else 1) and seen(verdict)==expected,'unexpected readiness verdict')
            require(not seen('skip') and not seen('fail' if verdict=='pass' else 'pass'),'mixed readiness results')
            require(sum(r.get('Action')==verdict and 'Test' not in r for r in records)==1,'incomplete package result')
            if label!='baseline':
                output=''.join(r.get('Output','') for r in records)
                require(output.count('stale completion changed current trial:')==count,'wrong readiness failure cause')
            print(f'GOBREAKER {label}: {count}/{count} {verdict}, public API, race detector',flush=True)
        (out/'receipt.json').write_text(json.dumps({'sourceSha256':PIN,'probeSha256':sha(FIXTURE/'probe_test.go.txt'),
            'baselinePass':10,'guardRemovalFail':5,'classification':'not-applicable',
            'scope':'generation rollover; no terminal/owned-resource contract; not a v1 oracle adapter'},indent=2)+'\n')
        print('GOBREAKER READINESS: stale completion observable; terminal/resource v1 not applicable')

if __name__=='__main__':main()
