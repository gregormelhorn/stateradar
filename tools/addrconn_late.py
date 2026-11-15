#!/usr/bin/env python3
"""Reference binding for the shared late-completion oracle, pinned to grpc-go."""
from __future__ import annotations
import argparse
from collections import Counter
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from addrconn_f09 import PIN, ROOT, COMPONENT, command, verify_records, verify_harness
from check_fault_mutants import copy_component, load_config, run_command, classify_result
from late_completion import evaluate
from mutation_verdict import cell_verdict

FIXTURE = COMPONENT / 'late-completion'


def verify_anchor():
    m = json.loads((COMPONENT / 'late-completion-manifest.json').read_text())
    if m['upstreamSha'] != PIN or not m['watchPaths'] or m['analyzedSha'] == 'WORKTREE':
        raise ValueError('unanchored late-completion fixture')
    changed = command(['git','diff','--name-only',m['analyzedSha']+'..HEAD','--',*m['watchPaths']]).strip()
    if changed:
        raise ValueError('stale late-completion manifest: '+changed)
    print('LATE HARNESS ANCHOR: '+m['analyzedSha'], flush=True)


def apply_evaluation_patch(source):
    patch = json.loads((FIXTURE / 'evaluation-patch.json').read_text())
    if patch['upstreamSha'] != PIN or patch['decision'] != 'DR-001':
        raise ValueError('patch source/decision mismatch')
    for edit in patch['edits']:
        if source.count(edit['match']) != 1:
            raise ValueError('missing/ambiguous evaluation patch anchor')
        source = source.replace(edit['match'],edit['replace'])
    return source


def execute(args, cwd=ROOT):
    return subprocess.run(list(map(str,args)),cwd=cwd,text=True,capture_output=True,timeout=180)


def require_adapter(root, output, count, expected_exit):
    run = execute([sys.executable,root/'late/run.py','--analysis',root/'late','--count',str(count),'--output-dir',output])
    output.mkdir(parents=True,exist_ok=True)
    (output/'verdict.txt').write_text(run.stdout+run.stderr)
    if run.returncode != expected_exit:
        raise RuntimeError(run.stdout+run.stderr)
    return cell_verdict(run.stdout,3)


def upstream_regressions(root, output, label):
    # Original test files stay unchanged. The public registry selects an isolated
    # recorder per ClientConn, avoiding the pinned helper's shared-builder race.
    overlay = {'Replace': {str(root/'zz_late_regression_test.go'): str(root/'late/regression_fixture_test.go.txt')}}
    path = root/'late/regression-overlay.json'; path.write_text(json.dumps(overlay))
    run = execute(['go','test','-mod=readonly','-race','-count=5','-timeout=90s','-overlay',path,
                   '-run','^Test/(BackoffCancel|StateTransitions_)','-json','.'],root)
    (output/(label+'-upstream.go.jsonl')).write_text(run.stdout+run.stderr)
    expected = {'Test', 'Test/BackoffCancel', 'Test/StateTransitions_SingleAddress',
                'Test/StateTransitions_ReadyToTransientFailure', 'Test/StateTransitions_TriesAllAddrsBeforeTransientFailure',
                'Test/StateTransitions_MultipleAddrsEntersReady'}
    records = [json.loads(l) for l in run.stdout.splitlines() if l.startswith('{')]
    passed = Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
    started = Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
    if run.returncode or passed != Counter({n:5 for n in expected}) or started != passed:
        raise RuntimeError('upstream regression discovery/failure; see '+label+'-upstream.go.jsonl')
    print('UPSTREAM REGRESSIONS ('+label+'): 5 named subtests x 5, race detector, isolated recording builder',flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--checkout',type=Path);p.add_argument('--output-dir',type=Path)
    args = p.parse_args()
    with tempfile.TemporaryDirectory(prefix='addrconn-late-') as td:
        tmp = Path(td).resolve()
        checkout = args.checkout.resolve() if args.checkout else tmp/'upstream'
        if not args.checkout:
            command(['git','clone','--depth','1','--branch','v1.18.0','https://github.com/grpc/grpc-go.git',checkout])
        if command(['git','rev-parse','HEAD'],checkout).strip()!=PIN or command(['git','status','--porcelain'],checkout).strip():
            raise ValueError('reference checkout must be clean and exactly pinned')
        verify_harness();verify_anchor();verify_records(checkout)
        output = args.output_dir.resolve() if args.output_dir else tmp/'evidence'
        output.mkdir(parents=True,exist_ok=True)
        root = tmp/'component'
        shutil.copytree(checkout,root,ignore=shutil.ignore_patterns('.git'))
        shutil.copytree(FIXTURE,root/'late')
        shutil.copyfile(ROOT/'tools/late_completion.py',root/'late/late_completion.py')
        historical = require_adapter(root,output/'historical',5,1)
        if historical.failed != frozenset({'Shutdown x CompleteTransport','Shutdown x NotifyReady'}):
            raise ValueError('historical defect was not reproduced at both declared scenarios')
        print('HISTORICAL RED: both shutdown/completion races observed in 5 repetitions',flush=True)
        upstream_regressions(root,output,'historical')
        source = root/'clientconn.go';source.write_text(apply_evaluation_patch(source.read_text()))
        require_adapter(root,output/'evaluation',10,0)
        print('EVALUATION GREEN: 3 scenarios x 10 repetitions',flush=True)
        upstream_regressions(root,output,'evaluation')
        # The prior backoff seam also runs against the corrected evaluation source.
        shutil.copytree(COMPONENT/'tests',root/'stateradar')
        shutil.copytree(COMPONENT/'domain-analysis/addrConnBackoff',root/'domain-analysis/addrConnBackoff')
        backoff = command([sys.executable,root/'stateradar/run.py','--analysis',root/'domain-analysis/addrConnBackoff','--count','10','--output',output/'backoff.go.jsonl'])
        (output/'backoff.txt').write_text(backoff)
        print('BACKOFF REGRESSION: 6 cells x 10 repetitions on corrected source',flush=True)
        generated = command([sys.executable,ROOT/'tools/gen_mutant_variants.py',root/'late'])
        generated += command([sys.executable,ROOT/'tools/gen_mutant_variants.py',root/'late','--check'])
        (output/'generation.txt').write_text(generated)
        generic = execute([sys.executable,ROOT/'tools/check_fault_mutants.py',root/'late'])
        (output/'generic.txt').write_text(generic.stdout+generic.stderr)
        print(generic.stdout,end='',flush=True)
        if generic.returncode:
            raise RuntimeError('generic late-completion mutations failed')
        weak_root = copy_component(root,tmp,'weak-canary-control')
        weak_config = weak_root/'late/fault-mutants.json'
        data = json.loads(weak_config.read_text()); data['testCommand'].append('--weak')
        weak_config.write_text(json.dumps(data))
        blocked = execute([sys.executable,ROOT/'tools/check_fault_mutants.py',weak_root/'late'])
        (output/'weak-canary-control.txt').write_text(blocked.stdout+blocked.stderr)
        if blocked.returncode != 1 or 'killed=0 survived=1 errors=0 blocked=5' not in blocked.stdout:
            raise RuntimeError('weak canary did not block all dependents')
        print('WEAK CANARY CONTROL: 1 survived, 5 dependents BLOCKED without execution',flush=True)
        config, mutants = load_config(root/'late')
        profile = json.loads((FIXTURE/'profile.json').read_text())
        causes = {'state-canary':'terminal state violated',
                  'publication-canary':'publication after termination',
                  'effect-canary':'effect emitted after termination',
                  'resource-canary':'resource not released exactly once'}
        rows = []
        for mutant in mutants:
            mutant_root = copy_component(root,tmp,'replay-'+mutant.identifier)
            (mutant_root/mutant.target).write_text((mutant_root/mutant.variant).read_text())
            dest = output/mutant.identifier
            require_adapter(mutant_root,dest,5,1)
            traces = json.loads((dest/'observations.json').read_text())
            failures = evaluate(profile,traces,5)
            if mutant.cell not in failures:
                raise RuntimeError('wrong-cell replay')
            if mutant.identifier in causes:
                reasons = {r.split(': ',1)[1] for rs in failures.values() for r in rs}
                if set(failures) != {mutant.cell} or reasons != {causes[mutant.identifier]}:
                    raise RuntimeError('canary did not independently isolate its projection: '+str(reasons))
            weak = run_command(replace(config,command=config.command+('--weak','--count','10','--output-dir',str(dest/'weak'))),mutant_root)
            (dest/'weak.txt').write_text(weak.output)
            verdict = classify_result(weak,mutant.cell,3)[0]
            if verdict != 'SURVIVED':
                raise RuntimeError('weak suite failed/incomplete: '+weak.output)
            rows.append({'id':mutant.identifier,'full':'KILLED','weak':verdict})
            print(f'REPLAY {mutant.identifier}: full KILLED (5 repeats), weak SURVIVED (10 repeats)',flush=True)
        (output/'results.json').write_text(json.dumps({'upstreamSha':PIN,'results':rows},indent=2)+'\n')
        print('LATE COMPLETION PASS: 2 F-04 mutants; 4 independent canaries; both orders; prior backoff and upstream controls pass')


if __name__=='__main__':
    main()
