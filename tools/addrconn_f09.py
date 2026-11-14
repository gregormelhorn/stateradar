#!/usr/bin/env python3
"""Pinned addrConn backoff slice; no implementation changes or broad pilot claim."""
import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from check_fault_mutants import copy_component, load_config, run_command, classify_result

ROOT=Path(__file__).resolve().parents[1]
COMPONENT=ROOT/'examples/grpc-addrconn'
ANALYSIS=COMPONENT/'domain-analysis/addrConnBackoff'
PIN='a02b0774206b209466313a0b525d2c738fe407eb'
CELL='BackoffWaiting x TearDown'


def command(args, cwd=ROOT):
    run=subprocess.run(list(map(str,args)),cwd=cwd,capture_output=True,text=True,timeout=180)
    if run.returncode:raise RuntimeError(run.stdout+run.stderr)
    return run.stdout+run.stderr


def verify_records(checkout, analysis=ANALYSIS):
    records=json.loads((analysis/'resolution.json').read_text())['records']
    if [r['source_question'] for r in records]!=[f'Q-{i:02}' for i in range(1,17)]:
        raise ValueError('decision coverage is not exactly Q-01..Q-16')
    for r in records:
        if (r['status']!='accepted' or r['question_status']!='ANSWERED' or
                r['implementation_status']!='pending' or not r['authorization'] or not r['rationale']):
            raise ValueError('decision attribution/status missing')
        if json.loads((analysis/'decisions'/(r['id']+'.yaml')).read_text())!=r:
            raise ValueError('decision record/index drift')
        for c in r['evidence']:
            lines=(checkout/c['file']).read_text().splitlines();n=c['line']
            if not any(c['fragment'] in l for l in lines[max(0,n-4):n+3]):
                raise ValueError('decision citation drift: '+str(c))
    print('DECISIONS: 16 ANSWERED with delegated attribution; implementation pending',flush=True)


def verify_harness():
    manifest=json.loads((COMPONENT/'harness-manifest.json').read_text())
    sha=manifest['analyzedSha'];paths=manifest['watchPaths']
    if not paths or sha=='WORKTREE':raise ValueError('unanchored harness manifest')
    changed=command(['git','diff','--name-only',sha+'..HEAD','--',*paths]).strip()
    if changed:raise ValueError('stale harness manifest: '+changed.replace('\n',', '))
    print('HARNESS ANCHOR: committed watched paths unchanged since '+sha[:8],flush=True)


def prepare(checkout, destination):
    if command(['git','rev-parse','HEAD'],checkout).strip()!=PIN:
        raise ValueError('wrong grpc-go revision')
    if command(['git','status','--porcelain'],checkout).strip():
        raise ValueError('upstream checkout must be clean')
    shutil.copytree(checkout,destination,ignore=shutil.ignore_patterns('.git'))
    shutil.copytree(COMPONENT/'tests',destination/'stateradar')
    shutil.copytree(ANALYSIS,destination/'domain-analysis/addrConnBackoff')
    return destination/'domain-analysis/addrConnBackoff'


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--checkout',type=Path);p.add_argument('--output-dir',type=Path);p.add_argument('--prepare-only',type=Path)
    a=p.parse_args()
    with tempfile.TemporaryDirectory(prefix='addrconn-f09-') as td:
        tmp=Path(td).resolve();checkout=a.checkout.resolve() if a.checkout else tmp/'upstream'
        if not a.checkout:command(['git','clone','--depth','1','--branch','v1.18.0','https://github.com/grpc/grpc-go.git',checkout])
        verify_harness()
        verify_records(checkout)
        print(command([sys.executable,COMPONENT/"check_model.py",checkout]),end="")
        print(command([sys.executable,ROOT/'tools/dsc_check.py',ANALYSIS,'--repo',checkout,'--model','as-is.machine.mmd']),end='')
        print(command([sys.executable,ROOT/'tools/check_reachability.py',ANALYSIS]),end='')
        analysis=prepare(checkout,a.prepare_only.resolve() if a.prepare_only else tmp/'component')
        print(command([sys.executable,ROOT/'tools/gen_mutant_variants.py',analysis]),end='')
        print(command([sys.executable,ROOT/'tools/gen_mutant_variants.py',analysis,'--check']),end='')
        if a.prepare_only:return
        output=a.output_dir.resolve() if a.output_dir else tmp/'evidence';output.mkdir(parents=True,exist_ok=True)
        # Baseline repeated independently of the one-loop mutation protocol.
        repeated=command([sys.executable,analysis.parents[1]/'stateradar/run.py','--analysis',analysis,'--count','10','--output',output/'baseline.go.jsonl'])
        (output/'baseline.txt').write_text(repeated)
        config,mutants=load_config(analysis)
        generic=subprocess.run([sys.executable,ROOT/'tools/check_fault_mutants.py',analysis],capture_output=True,text=True,timeout=180)
        (output/'generic.txt').write_text(generic.stdout+generic.stderr);print(generic.stdout,end='',flush=True)
        if generic.returncode:raise RuntimeError('generic canary/fault comparison failed')
        rows=[]
        for mutant in mutants:
            copy=copy_component(config.component_root,tmp,'weak-'+mutant.identifier)
            (copy/mutant.target).write_text((copy/mutant.variant).read_text())
            cfg=replace(config,command=config.command+('--weak','--count','10','--output',str(output/(mutant.identifier+'.weak.go.jsonl'))))
            result=run_command(cfg,copy)
            verdict=classify_result(result,CELL,1)[0]
            rows.append({'id':mutant.identifier,'weak':verdict,'exit':result.returncode})
            print(f'WEAK {mutant.identifier}: {verdict} (10 repeats)',flush=True)
            if verdict!='SURVIVED':raise RuntimeError('weak control did not survive with complete discovery')
        (output/'results.json').write_text(json.dumps({'upstreamSha':PIN,'weak':rows,'genericExit':generic.returncode},indent=2)+'\n')
        print('ADDRCONN F-09 PASS: 6 cells x 10 baseline repetitions; 3/3 generic mutants killed; weak controls survive')


if __name__=='__main__':main()
