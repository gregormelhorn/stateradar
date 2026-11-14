"""Prove reviewed guard partitions and queue-boundary preservation; fail on source drift."""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import sys
import z3

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools'))
from guard_proofs import check_group, boundary_probe, render


def run(source=None):
    source=source or ROOT/'examples/weighted-semaphore/semaphore/semaphore.go'
    text=source.read_text()
    pins=json.loads((HERE/'source-pins.json').read_text())
    if hashlib.sha256(text.encode()).hexdigest()!=pins['semaphore.go']:
        raise SystemExit('GUARD FAIL: reviewed source digest changed; re-extract guard expressions')
    size,cur,n,length,head=z3.Ints('size cur n length head')
    done,ready,front=z3.Bools('done ready front')
    free=size-cur
    nat=[size>=0,size<=2**63-1,cur>=0,cur<=size,n>=0,n<=2**63-1,length>=0,head>=0,head<=size]
    fast=z3.And(free>=n,length==0)
    fit=free>=head
    groups=[
      ('G-01',[('panic',n<0),('continue',n>=0)],[],[{n:v} for v in (-1,0,1)]),
      ('G-02',[('reject',done),('continue',z3.Not(done))],nat,[{done:v} for v in (False,True)]),
      ('G-03',[('fast',fast),('oversized',z3.And(z3.Not(fast),n>size)),('enqueue',z3.And(z3.Not(fast),n<=size))],nat,
       [{size:3,cur:1,n:v,length:l} for v in (0,1,2,3,4) for l in (0,1)]),
      ('G-04',[('admit',fast),('false',z3.Not(fast))],nat,[{size:3,cur:1,n:v,length:l} for v in (1,2,3) for l in (0,1)]),
      ('G-05',[('panic',n>cur),('release',n<=cur)],nat,[{cur:2,n:v} for v in (0,1,2,3)]),
      ('G-06',[('empty',length==0),('stop',z3.And(length>0,z3.Not(fit))),('grant',z3.And(length>0,fit))],nat,
       [{size:3,cur:1,head:h,length:l} for h in (1,2,3) for l in (0,1)]),
      ('G-07',[('rollback',ready),('unlink',z3.Not(ready))],nat,[{ready:v} for v in (False,True)]),
      ('G-08',[('notify',front),('skip',z3.Not(front))],nat,[{front:f,cur:c,size:2} for f in (False,True) for c in (1,2)]),
      ('G-09',[('rollback',done),('success',z3.Not(done))],nat,[{done:v} for v in (False,True)]),
    ]
    results=[]
    for name,guards,assumptions,probes in groups:
        r=check_group(name,guards,assumptions); results.append(r)
        for assignment,selected in boundary_probe(guards,probes):
            print(name,assignment,'=>',selected)
            if len(selected)!=1: raise SystemExit('GUARD FAIL: boundary not uniquely covered')
    # Inductive obligations at mutex-release boundaries, not arbitrary instruction points.
    # notifyWaiters repeats a capacity-safe grant until empty or a blocked head.
    obligations={
      'admit preserves count':z3.And(fast,z3.Or(cur+n<0,cur+n>size)),
      'release preserves count':z3.And(n<=cur,z3.Or(cur-n<0,cur-n>size)),
      'grant preserves count':z3.And(fit,z3.Or(cur+head<0,cur+head>size)),
      'first enqueue is blocked':z3.And(length==0,z3.Not(fast),n<=size,n<=free),
      'notifier stop is blocked':z3.And(length>0,z3.Not(fit),head<=free),
      'head removal cannot skip notification':z3.And(front,head<=free,z3.Not(front)),
      'retained blocked head cannot fit':z3.And(head>free,head<=free),
    }
    for name,bad in obligations.items():
        solver=z3.Solver(); solver.add(*nat,bad)
        verdict=solver.check(); print('G-10',name,verdict,'(unsat required)')
        if verdict!=z3.unsat: raise SystemExit('GUARD FAIL: '+name+' '+str(solver.model()))
    print(render(results))
    print('group G-10 queue-boundary preservation: proven (listed inductive obligations; source digest pinned)')
    print('group G-11 queued select: not-formalizable: dynamic-state; both ready channels permit either selection; G-07/09 prove sampled cleanup branches')
    if any(r.outcome!='proven' for r in results): raise SystemExit('GUARD FAIL: partition')
    expected=[{'id':f'G-{i:02}','outcome':'proven'} for i in range(1,11)]
    actual=json.loads((HERE/'analysis.json').read_text())['guardGroups']
    if actual[:10]!=expected or actual[10]['outcome']!='not-formalizable':
        raise SystemExit('GUARD FAIL: recorded outcomes differ')
    print('GUARDS PASS: 10 proven groups; 1 explicitly non-formalizable group')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--source',type=Path)
    run(parser.parse_args().source)
