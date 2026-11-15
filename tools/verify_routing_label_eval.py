#!/usr/bin/env python3
"""Replay source-fragment routing evidence and meter records offline."""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from jev_eval import evaluate
from routing_compare_prompt import build
from routing_evaluation import check_splits,reconcile
from routing_label_integrity import verify_source
from pilot_accounting import cost_report
from routing_ledger_check import verify as verify_ledger
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/routing-labels'
def verify(run):
 errors=[]
 def load(p):
  if not p.is_file():errors.append('missing '+p.name);return None
  try:return json.loads(p.read_text())
  except (OSError,ValueError) as e:errors.append('invalid '+p.name+': '+str(e));return None
 status=load(run/'status.json')
 if status and status.get('status')!='complete':errors.append('status incomplete')
 frozen=load(run/'input-freeze.json')
 if isinstance(frozen,dict):
  for path,digest in frozen.items():
   target=ROOT/path
   if not target.is_file():errors.append('missing frozen input: '+path)
   elif hashlib.sha256(target.read_bytes()).hexdigest()!=digest:errors.append('changed frozen input: '+path)
  for path in ('docs/evidence/routing-labels/protocol.md','docs/evidence/routing-labels/inputs/manifest.json','tools/run_routing_label_eval.py','tools/routing_compare_prompt.py','tools/jev_eval.py'):
   if path not in frozen:errors.append('missing freeze entry: '+path)
 calls=load(run/'calls.json');results=load(run/'results.json');ledger=load(run/'jev-ledger.json');dev=load(run/'dev-complete.json')
 if not all(isinstance(x,(list,dict)) for x in (status,frozen,calls,results,ledger,dev)):return errors
 try:
  manifest=json.loads((BASE/'inputs/manifest.json').read_text());check_splits(manifest)
  required={'docs/evidence/routing-labels/reference-review/status.json','docs/evidence/routing-labels/frozen/disputes.json'}
  for name,info in manifest['components'].items():
   required.update({info['source'],'docs/evidence/routing-labels/'+info['checks'],'docs/evidence/routing-labels/'+info['proposed_labels'],f'docs/evidence/routing-labels/frozen/{name}-labels.json',f'docs/evidence/routing-labels/reference-review/{name}.json'})
  for name in required:
   if name not in frozen:errors.append('missing freeze entry: '+name)
  if status['codex_calls']!=len(calls) or len(calls)>8 or any(not c['cost']['complete'] or c['failure'] for c in calls):errors.append('invalid comparator calls')
  if status['jev_calls']!=len(ledger['calls']) or any(c['status']!='settled' for c in ledger['calls']):errors.append('invalid Jev ledger')
  try:verify_ledger(run/'jev.sqlite',ledger)
  except ValueError:errors.append('Jev sqlite ledger mismatch')
  if sum(c['amount_microdollars'] for c in ledger['calls'])!=ledger['total_microdollars'] or ledger['total_microdollars']>ledger['limit_microdollars']:errors.append('Jev ledger mismatch')
  expected=[(name,phase) for phase in ('dev','heldout') for name in manifest['splits'][phase]]
  if [(r['component'],r['phase']) for r in results]!=expected:errors.append('trial order or coverage mismatch')
  expected_dev={f'{name}-{arm}.json' for name in manifest['splits']['dev'] for arm in ('jev','direct')}|{'dev-results.json'}
  if set(dev)!=expected_dev:errors.append('development freeze coverage mismatch')
  for name,digest in dev.items():
   if hashlib.sha256((run/name).read_bytes()).hexdigest()!=digest:errors.append('development output changed: '+name)
  refstatus=json.loads((BASE/'reference-review/status.json').read_text());refcalls=json.loads((BASE/'reference-review/calls.json').read_text())
  if refstatus['status']!='complete' or refstatus['calls']!=len(refcalls) or any(c['failure'] or not c['cost']['complete'] for c in refcalls):errors.append('reference calls incomplete')
  for call in refcalls:
   checkpoint=json.loads((BASE/'reference-review'/call['directory']/'usage-checkpoint.json').read_text());recomputed=cost_report(checkpoint,{'charged_microdollars':0,'reserved_microdollars':0},call['cost']['model'])
   if recomputed!=call['cost']:errors.append('reference checkpoint cost mismatch: '+str(call['id']))
  total_jev=0;expected_review={}
  for row in results:
   name=row['component'];info=manifest['components'][name];source=(ROOT/info['source']).read_text();checks=json.loads((BASE/info['checks']).read_text());verify_source(source,info['sha256'],checks)
   proposed=json.loads((BASE/info['proposed_labels']).read_text());ref_record=json.loads((BASE/'reference-review'/f'{name}.json').read_text());review=ref_record['review'];agreed=reconcile(proposed,review)
   refcall=refcalls[ref_record['call_ids'][0]]
   reference_prompt=('Independently classify each check using ONLY whether its quoted fragment explicitly supports, contradicts, or leaves unclear the exact statement. Surrounding source may clarify meaning, but cannot add unquoted material conditions, actors, events, ordering or outcomes. For ordering, every material detail must be contemplated by the fragment; an unmentioned ordering is unclear. Treat code comments as quoted statements, not automatically as runtime behavior. A call site does not establish the callee error contract. Do not decide domain policy. You receive no proposed labels or Jev results. Return JSON {"cases":[{"id":"...","verdict":"supported|contradicted|unclear","reason":"..."}]} with every id exactly once.\nCHECKS:\n'+json.dumps(checks)+'\nSOURCE:\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1)))
   if (BASE/'reference-review'/refcall['directory']/'prompt.md').read_text()!=reference_prompt:errors.append('reference prompt mismatch: '+name)
   if 'docs/evidence/routing-labels/reference-review/'+refcall['directory']+'/prompt.md' not in frozen:errors.append('reference prompt not frozen: '+name)
   labels=json.loads((BASE/'frozen'/f'{name}-labels.json').read_text());
   if set(labels['checks'])!=set(agreed['agreed']):errors.append('reviewed label coverage mismatch: '+name)
   for ident,label in labels['checks'].items():
    original=agreed['agreed'][ident]
    if any(label[k]!=original[k] for k in ('kind','statement','source','line','fragment','expected')):errors.append('reference label changed: '+ident)
   j=json.loads((run/f'{name}-jev.json').read_text());direct=json.loads((run/f'{name}-direct.json').read_text());total_jev+=j['cost_microdollars']
   for ident,label in labels['checks'].items():
    expected_review[ident]={'reference':label['expected'],'jev':j['checks'][ident]['choice'],'direct':direct['checks'][ident]['choice'],'citation':{'file':label['source'],'line':label['line'],'fragment':label['fragment']}}
   ids=set(labels['checks']);excluded=sorted(set(j['checks'])-ids)
   if excluded!=row['excluded_disputed'] or set(excluded)!=set(agreed['disputes']):errors.append('dispute coverage mismatch: '+name)
   def subset(batch):return {**batch,'checks':{k:v for k,v in batch['checks'].items() if k in ids}}
   if evaluate(labels,subset(j))!=row['jev'] or evaluate(labels,subset(direct))!=row['direct']:errors.append('score mismatch: '+name)
   direct_calls=[calls[i] for i in row['direct_call_ids']];first=direct_calls[0];last=direct_calls[-1]
   if (run/first['directory']/'prompt.md').read_text()!=build(source,checks):errors.append('comparator prompt mismatch: '+name)
   raw=json.loads((run/last['directory']/'validated.json').read_text());choices={x['id']:x['choice'] for x in raw['cases']}
   if choices!={k:v['choice'] for k,v in direct['checks'].items()}:errors.append('comparator output mismatch: '+name)
   if direct['cost_microdollars']!=round(sum(c['cost']['total_usd_estimate'] for c in direct_calls)*1_000_000):errors.append('comparator cost mismatch: '+name)
   for call in direct_calls:
    checkpoint=json.loads((run/call['directory']/'usage-checkpoint.json').read_text());recomputed=cost_report(checkpoint,{'charged_microdollars':0,'reserved_microdollars':0},call['cost']['model'])
    if recomputed!=call['cost']:errors.append('comparator checkpoint cost mismatch: '+name)
    for line in (run/call['directory']/'events.jsonl').read_text().splitlines():
     if json.loads(line).get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change'):errors.append('forbidden comparator tool')
  if total_jev!=ledger['total_microdollars']:errors.append('Jev output cost mismatch')
  reviewed=json.loads((BASE/'reviewed-results.json').read_text());rows=reviewed['cases']
  if Counter(x['id'] for x in rows)!=Counter(list(expected_review)):errors.append('review coverage mismatch')
  for x in rows:
   ident=x['id'];expected=expected_review.get(ident)
   if expected is None or any(x.get(k)!=v for k,v in expected.items()) or not x.get('review_note') or not x.get('reviewer'):errors.append('review result mismatch: '+ident)
  for ident in ('Q-R01','Q-R02','Q-R03'):
   if not any(q.get('id')==ident and q.get('status')=='OPEN' for q in reviewed['open_questions']):errors.append('open question missing: '+ident)
  from verify_gepa_training import verify_test_log,verify_expected_red
  verify_test_log(BASE/'runtime-green.jsonl',{'TestBufferEmptyReadByte','TestValueSwapWithoutStore'},3)
  verify_expected_red(BASE/'runtime-red.jsonl','TestBufferEmptyReadByte','red probe: EOF observed')
  verify_expected_red(BASE/'runtime-red.jsonl','TestValueSwapWithoutStore','red probe: Load observes Swap')
 except (KeyError,ValueError,TypeError,IndexError,OSError) as e:errors.append('invalid evidence: '+str(e))
 return errors
if __name__=='__main__':
 errors=verify(Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'runs')
 print('\n'.join(errors) if errors else 'ROUTING LABEL EVALUATION: OK');sys.exit(bool(errors))
