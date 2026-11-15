"""Record attributed scope review and execute the extra ordering it identifies."""
from pathlib import Path
import json,hashlib,subprocess,tempfile,shutil
from collections import Counter
HERE=Path(__file__).resolve().parents[1]

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(output):
 with tempfile.TemporaryDirectory(prefix='gepa-scope-') as td:
  root=Path(td);shutil.copyfile(HERE/'reference/scope_extension_test.go',root/'scope_test.go')
  (root/'go.mod').write_text('module reference.local\n\ngo 1.24\n')
  p=subprocess.run(['go','test','-race','-count=5','-timeout=30s','-json','.'],cwd=root,capture_output=True,text=True,timeout=90)
  output.write_text(p.stdout+p.stderr)
  events=[json.loads(l) for l in p.stdout.splitlines() if l.startswith('{')]
  for action in ('run','pass'):
   assert Counter(e['Test'] for e in events if e.get('Action')==action and 'Test'in e)==Counter({'TestRearmedWhilePriorCallbackRuns':5,'TestRepeatedStopFalseBeforeCallback':5})
  assert p.returncode==0 and not any(e.get('Action')in ('fail','skip') for e in events)
 print('SCOPE CONTROL PASS: intervening rearm and repeated Stop, 2 controls x 5 repetitions with race detector')

if __name__=='__main__':
 output=HERE/'scope-reference.jsonl';run(output)
 rows=[]
 for r in json.loads((HERE/'runs/comparison.json').read_text()):
  if r['component']!='timer':continue
  finding=next(f for f in r['report']['findings'] if f['id']=='timer-03')
  # Attributed manual judgments after reading all nine reasons; not NLP entailment.
  rows.append({'repeat':r['repeat'],'arm':r['arm'],'reason':finding['reason'],
   'explicit_intervening_rearm_qualification':r['arm']!='none',
   'reviewer':'Codex, supervising source/trace review',
   'rationale':'Names the intervening rearm/active case and its true return.' if r['arm']!='none' else 'Explains the expired scheduling but does not explicitly examine a separate intervening Reset.'})
 result={'status':'supplementary post-selection review; no optimization feedback',
  'primary_scope_limit':'timer-03 primary label assumes Reset of the expired firing without an intervening rearm. The claim inventory does not spell that exclusion out. The additional review exposes this evaluation-scope limitation; the frozen label/score is not retrospectively rewritten.',
  'comparison_sha256':digest(HERE/'runs/comparison.json'),'probe_sha256':digest(HERE/'reference/scope_extension_test.go'),'execution_sha256':digest(output),
  'rows':rows,'meaning':'This is a review benefit shared by fixed and GEPA, not a GEPA-specific quality win. Annotation integrity does not prove prose entailment.'}
 (HERE/'scope-review.json').write_text(json.dumps(result,indent=2)+'\n')
