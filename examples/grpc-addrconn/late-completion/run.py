"""Adapter: controlled real addrConn execution; verdicts come from the shared oracle."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

# A prepared component contains a copy of the shared oracle, never a private fork.
from late_completion import EvidenceError, report, validate_profile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--analysis',type=Path,required=True);p.add_argument('--weak',action='store_true')
p.add_argument('--count',type=int,default=1);p.add_argument('--output-dir',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parents[1]
try:
 profile=json.loads((a.analysis/'profile.json').read_text());cases=validate_profile(profile)
 if a.count<1:raise EvidenceError('positive repetitions required')
 source=(root/'clientconn.go').read_text()
 anchors=[
 ('func (ac *addrConn) resetTransport() {','func (ac *addrConn) resetTransport() {\n\tdefer lateReturned(ac)'),
 ('transport.NewClientTransport(connectCtx, ac.cc.ctx, target, copts, onPrefaceReceipt, onGoAway, onClose)',
  'lateFactory(ac, connectCtx, ac.cc.ctx, target, copts, onPrefaceReceipt, onGoAway, onClose)'),
 ('newTr, err := ac.createTransport(addr, copts, connectDeadline, reconnect, prefaceReceived)',
  'newTr, err := ac.createTransport(addr, copts, connectDeadline, reconnect, prefaceReceived)\n\t\t\tlateCheckpoint(ac, "after-create")'),
 ('healthCheckConfig := ac.cc.healthCheckConfig()', 'lateCheckpoint(ac, "before-ready")\n\t\t\t\thealthCheckConfig := ac.cc.healthCheckConfig()'),
 ('\t\t\tac.mu.Lock()\n\t\t\treqHandshake := ac.dopts.reqHandshake', '\t\t\tlateSettled(ac)\n\t\t\tac.mu.Lock()\n\t\t\treqHandshake := ac.dopts.reqHandshake'),
 ('func (cc *ClientConn) handleSubConnStateChange(sc balancer.SubConn, s connectivity.State) {',
  'func (cc *ClientConn) handleSubConnStateChange(sc balancer.SubConn, s connectivity.State) {\n\tlateEffect(s)')]
 for old,new in anchors:
  if source.count(old)!=1:raise EvidenceError('missing/ambiguous adapter anchor: '+old)
  source=source.replace(old,new)
 with tempfile.TemporaryDirectory(prefix='late-overlay-') as td:
  temp=Path(td).resolve();(temp/'clientconn.go').write_text(source)
  overlay={'Replace':{str(root/'clientconn.go'):str(temp/'clientconn.go'),str(root/'late_completion_test.go'):str(root/'late/probe_test.go.txt')}}
  (temp/'overlay.json').write_text(json.dumps(overlay))
  run=subprocess.run(['go','test','-mod=readonly','-race','-count=1','-timeout=90s','-overlay',str(temp/'overlay.json'),'-run','^TestLateCompletionEvidence$','-json','.'],cwd=root,
       env={**os.environ,'LATE_PROFILE':str((a.analysis/'profile.json').resolve()),'LATE_REPEATS':str(a.count)},capture_output=True,text=True,timeout=120)
 if a.output_dir:
  a.output_dir.mkdir(parents=True,exist_ok=True);(a.output_dir/'go.jsonl').write_text(run.stdout+run.stderr)
 records=[json.loads(l) for l in run.stdout.splitlines() if l.startswith('{')]
 expected=Counter({'TestLateCompletionEvidence':1})
 expected.update({f"TestLateCompletionEvidence/{c['id']}/{r}":1 for c in cases for r in range(a.count)})
 seen=lambda action:Counter(r['Test'] for r in records if r.get('Action')==action and 'Test'in r)
 if run.returncode or seen('run')!=expected or seen('pass')!=expected or not any(r.get('Action')=='pass' and 'Test'not in r for r in records):
  print(run.stdout);print(run.stderr);raise EvidenceError('incomplete/failed adapter execution')
 output=''.join(r.get('Output','') for r in records)
 traces=[json.loads(l[len('LATE TRACE '):]) for l in output.splitlines() if l.startswith('LATE TRACE ')]
 if a.output_dir:(a.output_dir/'observations.json').write_text(json.dumps(traces,indent=2)+'\n')
 code=report(profile,traces,a.count,a.weak)
except (EvidenceError,ValueError,OSError,subprocess.TimeoutExpired) as exc:
 print('BLOCKED: '+str(exc));code=2
raise SystemExit(code)
