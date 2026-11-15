#!/usr/bin/env python3
"""Verify evidence completeness, frozen inputs, and reproducible scores."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from gepa_discovery_eval import audit
ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/evidence/gepa-heldout'
def verify(run):
 errors=[]
 def load(p):
  if not p.exists():errors.append('missing '+p.name);return None
  try:return json.loads(p.read_text())
  except (ValueError,OSError) as e:errors.append(f'invalid {p.name}: {e}');return None
 status=load(run/'status.json')
 if status and status.get('status')!='complete':errors.append('status incomplete')
 frozen=load(run/'input-freeze.json')
 if isinstance(frozen,dict):
  for name,want in frozen.items():
   path=ROOT/name
   if not path.is_file():errors.append('missing frozen input: '+name)
   elif hashlib.sha256(path.read_bytes()).hexdigest()!=want:errors.append('changed frozen input: '+name)
  for required in ('docs/evidence/gepa-heldout/dataset.json','docs/evidence/gepa-heldout/protocol.md','docs/evidence/gepa-heldout/upstream/scan.go','docs/evidence/gepa-heldout/upstream/value.go','docs/evidence/gepa-heldout/upstream/pipe.go','docs/evidence/gepa-discovery/fixed.md','tools/run_gepa_heldout.py'):
   if required not in frozen:errors.append('missing freeze entry: '+required)
 calls=load(run/'calls.json');results=load(run/'results.json');sel=load(run/'selected-prompt.json')
 if not all(isinstance(x,(dict,list)) for x in (calls,results,sel)):return errors
 try:
  from verify_gepa_training import verify_test_log
  reference_tests={'TestPipeFirstWriterError','TestPipePartialWriteClose','TestPipeZeroWriteHandshake','TestScannerFinalTokenVariants','TestScannerLateConfiguration','TestValueTypedNilAndNil','TestValueEmptyCompareAndSwap','TestScannerFinalTokenPreservesPriorError','TestValueCompareAndSwapMismatchedTypes'}
  verify_test_log(HERE/'reference-v2.jsonl',reference_tests,3)
  dataset=json.loads((HERE/'dataset.json').read_text());train=json.loads((ROOT/'docs/evidence/gepa-training-catalog/catalog.json').read_text())
  if len(calls)!=status['calls'] or len(calls)>25:errors.append('call count mismatch or cap exceeded')
  if any(not c['cost']['complete'] or c['failure'] for c in calls):errors.append('incomplete or failed call')
  if [c['id'] for c in calls]!=list(range(len(calls))):errors.append('call ids not contiguous')
  for c in calls:
   events=(run/c['directory']/'events.jsonl').read_text().splitlines()
   if any(json.loads(e).get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change') for e in events):errors.append('forbidden tool event: '+str(c['id']))
  if sum(c['cost']['total_usd_estimate'] for c in calls)>6:errors.append('cost cap exceeded')
  expected=Counter((name,arm,rep) for name in dataset['test'] for arm in ('fixed','gepa') for rep in range(2))
  actual=Counter()
  for rec in results:
   call=calls[rec['call_ids'][-1]];report=load(run/call['directory']/'validated.json');review=load(run/rec['review'])
   comp=dataset['components'].get(rec['component']) or train['components'][rec['component']]
   source=(ROOT/comp['source']).read_text()
   if report and review and audit(report,source,comp['cases'],review)!=rec['summary']:errors.append('score mismatch: '+rec['review'])
   if rec['phase']=='final':
    from gepa_training_catalog import build_prompt
    from run_gepa_discovery import TASK
    _,arm,repeat=rec['category'].split('-');actual[(rec['component'],arm,int(repeat[1:]))]+=1
    paragraph=(ROOT/'docs/evidence/gepa-discovery/fixed.md').read_text() if arm=='fixed' else sel['candidate']['review']
    first=calls[rec['call_ids'][0]]
    if (run/first['directory']/'prompt.md').read_text()!=build_prompt(source,paragraph,TASK):errors.append('final prompt mismatch: '+rec['review'])
  if actual!=expected:errors.append('final trial coverage mismatch')
  if sel['candidate']!=sel['candidates'][sel['best_index']]:errors.append('selection mismatch')
 except (KeyError,ValueError,TypeError,IndexError,OSError) as e:errors.append('invalid evidence: '+str(e))
 return errors
def verify_diagnostic(run):
 errors=[]
 if not (run/'status.json').exists():return ['missing diagnostic status']
 try:
  status=json.loads((run/'status.json').read_text())
  if status.get('status')!='complete':errors.append('diagnostic incomplete')
  if errors:return errors
  dataset=json.loads((HERE/'dataset.json').read_text());declaration=json.loads((HERE/'exploratory-declaration.json').read_text())
  selection=json.loads((HERE/'runs/selected-prompt.json').read_text());paragraph=selection['candidates'][declaration['candidate_index']]['review']
  if hashlib.sha256(paragraph.encode()).hexdigest()!=declaration['candidate_sha256']:errors.append('diagnostic candidate mismatch')
  if selection!=json.loads((run/'selected-prompt.json').read_text()):errors.append('diagnostic selection mismatch')
  calls=json.loads((run/'calls.json').read_text());results=json.loads((run/'results.json').read_text())
  prior=json.loads((HERE/'runs/calls.json').read_text())
  if len(calls)!=status['calls'] or len(calls)+len(prior)>25:errors.append('diagnostic call count mismatch')
  if any(not c['cost']['complete'] or c['failure'] for c in calls+prior):errors.append('diagnostic unsettled call')
  if sum(c['cost']['total_usd_estimate'] for c in calls+prior)>6:errors.append('diagnostic cost cap exceeded')
  expected=Counter((name,f'diagnostic-r{repeat}') for name in dataset['test'] for repeat in range(2))
  if Counter((r['component'],r['category']) for r in results)!=expected:errors.append('diagnostic coverage mismatch')
  from gepa_training_catalog import build_prompt
  from run_gepa_discovery import TASK
  for r in results:
   component=dataset['components'][r['component']];source=(ROOT/component['source']).read_text()
   call=calls[r['call_ids'][-1]];first=calls[r['call_ids'][0]]
   report=json.loads((run/call['directory']/'validated.json').read_text());review=json.loads((run/r['review']).read_text())
   if audit(report,source,component['cases'],review)!=r['summary']:errors.append('diagnostic score mismatch: '+r['review'])
   if (run/first['directory']/'prompt.md').read_text()!=build_prompt(source,paragraph,TASK):errors.append('diagnostic prompt mismatch: '+r['review'])
   for cid in r['call_ids']:
    events=(run/calls[cid]['directory']/'events.jsonl').read_text().splitlines()
    if any(json.loads(e).get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change') for e in events):errors.append('diagnostic forbidden tool')
 except (KeyError,ValueError,TypeError,IndexError,OSError) as e:errors.append('invalid diagnostic evidence: '+str(e))
 return errors

if __name__=='__main__':
 failures=verify(Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'runs')
 if len(sys.argv)==1:failures+=verify_diagnostic(HERE/'exploratory')
 print('\n'.join(failures) if failures else 'GEPA held-out archive: OK')
 sys.exit(bool(failures))
