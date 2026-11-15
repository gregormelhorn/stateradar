#!/usr/bin/env python3
"""Replay frozen inputs, reference results, model prompts and attributed scores."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from gepa_discovery_eval import audit
from gepa_selection import classify
from gepa_training_catalog import build_prompt
from run_gepa_discovery import TASK
from verify_gepa_training import verify_test_log
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'docs/evidence/gepa-prospective'

def verify(run):
 errors=[]
 def load(path):
  if not path.exists():errors.append('missing '+path.name);return None
  try:return json.loads(path.read_text())
  except (OSError,ValueError) as e:errors.append(f'invalid {path.name}: {e}');return None
 status=load(run/'status.json')
 if status and status.get('status')!='complete':errors.append('status incomplete')
 frozen=load(run/'input-freeze.json')
 if isinstance(frozen,dict):
  for name,want in frozen.items():
   path=ROOT/name
   if not path.is_file():errors.append('missing frozen input: '+name)
   elif hashlib.sha256(path.read_bytes()).hexdigest()!=want:errors.append('changed frozen input: '+name)
  for name in ('docs/evidence/gepa-prospective/dataset.json','docs/evidence/gepa-prospective/protocol.md','docs/evidence/gepa-prospective/reference.jsonl','docs/evidence/gepa-prospective/upstream/once.go','docs/evidence/gepa-prospective/upstream/buffer.go','docs/evidence/gepa-heldout/runs/selected-prompt.json','tools/run_gepa_prospective.py'):
   if name not in frozen:errors.append('missing freeze entry: '+name)
 calls=load(run/'calls.json');results=load(run/'results.json')
 if not all(isinstance(x,(list,dict)) for x in (status,frozen,calls,results)):return errors
 try:
  verify_test_log(HERE/'reference.jsonl',{'TestOncePanicDone','TestOnceConcurrentWait','TestBufferEmptyReads','TestBufferZeroReadInvalidatesUnread'},3)
  refs_status=json.loads((HERE/'reference-review/status.json').read_text());refs_calls=json.loads((HERE/'reference-review/calls.json').read_text())
  if refs_status.get('status')!='complete' or refs_status.get('calls')!=len(refs_calls) or len(refs_calls)>4:errors.append('reference review call count mismatch')
  if any(not c['cost']['complete'] or c['failure'] for c in refs_calls) or sum(c['cost']['total_usd_estimate'] for c in refs_calls)>3:errors.append('reference review cost or call failure')
  data=json.loads((HERE/'dataset.json').read_text());selection=json.loads((ROOT/'docs/evidence/gepa-heldout/runs/selected-prompt.json').read_text())
  if classify(selection['validation_scores'])['status']!='tie':errors.append('prior selection is not tied')
  paragraphs={'fixed':(ROOT/'docs/evidence/gepa-discovery/fixed.md').read_text(),'candidate':selection['candidates'][1]['review']}
  if len(calls)!=status['calls'] or len(calls)>12:errors.append('call count mismatch')
  if any(not c['cost']['complete'] or c['failure'] for c in calls):errors.append('unsettled or failed call')
  if sum(c['cost']['total_usd_estimate'] for c in calls)>3:errors.append('cost cap exceeded')
  expected=Counter((name,arm,repeat) for name in ('once','buffer') for arm in ('fixed','candidate') for repeat in range(2))
  if Counter((r['component'],r['arm'],r['repeat']) for r in results)!=expected:errors.append('trial coverage mismatch')
  from gepa_provenance import validate as validate_provenance
  provenance=json.loads((HERE/'provenance.json').read_text());errors.extend(validate_provenance(provenance,ROOT))
  if Counter(x['id'] for x in provenance['cases'])!=Counter(c['id'] for info in data['components'].values() for c in info['cases']):errors.append('provenance case coverage mismatch')
  expected_findings=Counter()
  for rec in results:
   info=data['components'][rec['component']];source=(ROOT/info['source']).read_text()
   first=calls[rec['call_ids'][0]];last=calls[rec['call_ids'][-1]]
   report=json.loads((run/last['directory']/'validated.json').read_text());review=json.loads((run/rec['review']).read_text())
   expected_findings.update((last['id'],f['id']) for f in report['findings'])
   if audit(report,source,info['cases'],review)!=rec['summary']:errors.append('score mismatch: '+rec['review'])
   if (run/first['directory']/'prompt.md').read_text()!=build_prompt(source,paragraphs[rec['arm']],TASK):errors.append('prompt mismatch: '+rec['review'])
   for cid in rec['call_ids']:
    for line in (run/calls[cid]['directory']/'events.jsonl').read_text().splitlines():
     if json.loads(line).get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change'):errors.append('forbidden tool event')
  if Counter((f['call_id'],f['id']) for f in provenance['findings'])!=expected_findings:errors.append('provenance finding coverage mismatch')
  for name,info in data['components'].items():
   refs=json.loads((HERE/'reference-review'/f'{name}.json').read_text())['review']['cases'];lines=(ROOT/info['source']).read_text().splitlines()
   if {r['id'] for r in refs}!={c['id'] for c in info['cases']} or any(r['verdict']!='confirmed' or r['fragment'] not in lines[r['line']-1] for r in refs):errors.append('reference review incomplete: '+name)
 except (KeyError,ValueError,TypeError,IndexError,OSError) as e:errors.append('invalid evidence: '+str(e))
 return errors
if __name__=='__main__':
 errors=verify(Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'runs')
 print('\n'.join(errors) if errors else 'GEPA prospective archive: OK')
 sys.exit(bool(errors))
