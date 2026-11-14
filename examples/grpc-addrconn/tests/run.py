"""Run real pinned grpc-go with a scheduling/clock-only overlay; exact Go discovery."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',type=Path,required=True);p.add_argument('--weak',action='store_true');p.add_argument('--count',type=int,default=1);p.add_argument('--output',type=Path)
a=p.parse_args();root=Path(__file__).resolve().parent.parent
if a.count<1:raise SystemExit('positive count required')
source=(root/'clientconn.go').read_text()
anchors=[('func (ac *addrConn) resetTransport() {','func (ac *addrConn) resetTransport() {\n\tdefer radarDone(ac)'),
 ('timer := time.NewTimer(backoffFor)','timer := radarNewTimer(ac, backoffFor)'),
 ('acctx := ac.ctx\n\t\tac.mu.Unlock()','acctx := ac.ctx\n\t\tac.mu.Unlock()\n\t\tradarReady(ac)')]
for old,new in anchors:
 if source.count(old)!=1:raise SystemExit('BLOCKED: scheduling anchor absent/ambiguous: '+old)
 source=source.replace(old,new)
with tempfile.TemporaryDirectory(prefix='addrconn-overlay-') as td:
 temp=Path(td).resolve();(temp/'clientconn.go').write_text(source)
 overlay={'Replace':{str(root/'clientconn.go'):str(temp/'clientconn.go'),str(root/'radar_backoff_test.go'):str(root/'stateradar/backoff_test.go.txt')}}
 (temp/'overlay.json').write_text(json.dumps(overlay))
 name='TestRadarWeak' if a.weak else 'TestRadarCells'
 run=subprocess.run(['go','test','-mod=readonly','-race',f'-count={a.count}','-timeout=90s','-overlay',str(temp/'overlay.json'),'-run','^'+name+'$','-json','.'],cwd=root,env={**os.environ,'STATERADAR_ANALYSIS':str(a.analysis.resolve())},capture_output=True,text=True,timeout=120)
if a.output:a.output.write_text(run.stdout+run.stderr)
records=[json.loads(l) for l in run.stdout.splitlines() if l.startswith('{')]
names={name}
if not a.weak:
 names|={name+'/'+c['state']+'/'+c['event'] for c in json.loads((a.analysis/'analysis.json').read_text())['cells']}
expected=Counter({n:a.count for n in names})
seen=lambda action:Counter(r['Test'] for r in records if r.get('Action')==action and 'Test'in r)
completed=seen('run')==expected and seen('pass')+seen('fail')==expected
output=''.join(r.get('Output','') for r in records)
if not completed or 'panic:' in output or not any(r.get('Action')in('pass','fail') and 'Test'not in r for r in records):
 print(run.stdout);print(run.stderr);raise SystemExit('BLOCKED: incomplete Go discovery/verdict')
if a.weak:
 if run.returncode==0:print('CELL SUITE: 1 cells checked, 0 failed')
else:
 if output.count('CELL SUITE: 6 cells checked,')!=a.count:raise SystemExit('BLOCKED: missing complete cell loop')
 for l in output.splitlines():
  if l.startswith(('CELL FAIL ','CELL SUITE: ')):print(l)
raise SystemExit(run.returncode)
