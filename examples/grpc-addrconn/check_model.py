"""Scoped guard and decision/source checks; no claim about the full addrConn model."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import shutil
from z3 import Int, Or, And, Solver, sat, unsat

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import addrconn_f09 as fixture

p=argparse.ArgumentParser();p.add_argument('checkout',type=Path);a=p.parse_args()
fixture.verify_records(a.checkout.resolve())
s=Int('projected_state');domain=Or(s==0,s==1,s==2)
# Waiting maps to TransientFailure; Pending and Stopped map to Shutdown.
perform=s==0;already_shutdown=Or(s==1,s==2)
def prove(skip):
 overlap=Solver();overlap.add(domain,And(perform,skip))
 uncovered=Solver();uncovered.add(domain,~Or(perform,skip))
 return overlap.check(),uncovered.check()
red=prove(perform)
if red!=(sat,sat):raise SystemExit('guard red probe did not expose overlap and gap')
print('GUARD RED: duplicate dispatch guard produces overlap and uncovered states')
if prove(already_shutdown)!=(unsat,unsat):raise SystemExit('guard partition failed')
print('GUARD GREEN: shutdown dispatch disjoint and exhaustive over all 3 scoped states')
for state in range(3):
 assert (state==0) != (state in (1,2))
# Exercise the actual record validator on a disposable incomplete index.
with tempfile.TemporaryDirectory() as td:
    copy=Path(td)/'analysis';shutil.copytree(fixture.ANALYSIS,copy)
    record_path=copy/'resolution.json';data=json.loads(record_path.read_text())
    data['records'].pop();record_path.write_text(json.dumps(data))
    try:fixture.verify_records(a.checkout.resolve(),copy)
    except ValueError as exc:
        if 'Q-01..Q-16' not in str(exc):raise
        print('QUESTION RED: actual validator rejects omitted Q-16')
    else:raise SystemExit('question omission accepted')
print('SCOPED MODEL PASS: 16 attributed answers; 3 projected states; no broad conformance claim')
