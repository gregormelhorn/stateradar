#!/usr/bin/env python3
"""Offline verification of post-comparison Flash/Jev diagnostic."""
import hashlib
import json
import sys
from pathlib import Path
from routing_flash_eval import score
from routing_label_integrity import verify_source
from routing_ledger_check import verify as verify_ledger
from run_routing_flash_diagnostic import task
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/routing-labels'
def verify(run):
 errors=[]
 def load(path):
  if not path.is_file():errors.append('missing '+path.name);return None
  try:return json.loads(path.read_text())
  except (OSError,ValueError) as e:errors.append('invalid '+path.name+': '+str(e));return None
 status=load(run/'status.json')
 if status and status.get('status')!='complete':errors.append('status incomplete')
 frozen=load(run/'input-freeze.json');ledger=load(run/'ledger.json');results=load(run/'results.json')
 if not all(isinstance(x,(dict,list)) for x in (status,frozen,ledger,results)):return errors
 try:
  for name,digest in frozen.items():
   p=ROOT/name
   if not p.is_file():errors.append('missing frozen input: '+name)
   elif hashlib.sha256(p.read_bytes()).hexdigest()!=digest:errors.append('changed frozen input: '+name)
  manifest=json.loads((BASE/'inputs/manifest.json').read_text());names=['once','pipe','buffer','value']
  required={'docs/evidence/routing-labels/flash-diagnostic-protocol.md','tools/run_routing_flash_diagnostic.py','tools/routing_flash_eval.py'}
  for name in names:
   info=manifest['components'][name];required.update({info['source'],'docs/evidence/routing-labels/'+info['checks'],f'docs/evidence/routing-labels/frozen/{name}-labels.json'})
  for name in required:
   if name not in frozen:errors.append('missing freeze entry: '+name)
  if status['components']!=4 or [x['component'] for x in results]!=names:errors.append('diagnostic coverage mismatch')
  if any(c['status']!='settled' for c in ledger['calls']) or sum(c['amount_microdollars'] for c in ledger['calls'])!=ledger['total_microdollars'] or ledger['total_microdollars']>ledger['limit_microdollars']:errors.append('diagnostic ledger mismatch')
  try:verify_ledger(run/'provider.sqlite',ledger)
  except ValueError:errors.append('diagnostic sqlite ledger mismatch')
  if sum(x['flash_cost_microdollars']+x['jev_cost_microdollars'] for x in results)!=ledger['total_microdollars']:errors.append('diagnostic cost mismatch')
  if sum(c['provider']=='deepseek-flash' for c in ledger['calls'])!=4:errors.append('diagnostic Flash call count mismatch')
  for row in results:
   name=row['component'];info=manifest['components'][name];checks=json.loads((BASE/info['checks']).read_text());labels=json.loads((BASE/'frozen'/f'{name}-labels.json').read_text());source=(ROOT/info['source']).read_text();verify_source(source,info['sha256'],checks)
   result=json.loads((run/f'{name}-result.json').read_text())
   if result['source_sha256']!=info['sha256'] or result['source']!=info['source']:errors.append('diagnostic source mismatch: '+name)
   if (run/f'{name}-task.txt').read_text()!=task(checks):errors.append('diagnostic task mismatch: '+name)
   if score(labels,checks,result)!=row['audit']:errors.append('diagnostic score mismatch: '+name)
   if row['flash_cost_microdollars']!=result['draft']['cost_microdollars'] or row['jev_cost_microdollars']!=(result['verification']['cost_microdollars'] if result['verification'] and not result['verification'].get('error') else 0):errors.append('diagnostic per-call cost mismatch: '+name)
 except (KeyError,ValueError,TypeError,IndexError,OSError) as e:errors.append('invalid diagnostic evidence: '+str(e))
 return errors
if __name__=='__main__':
 errors=verify(Path(sys.argv[1]) if len(sys.argv)>1 else BASE/'flash-diagnostic')
 print('\n'.join(errors) if errors else 'ROUTING FLASH DIAGNOSTIC: OK');sys.exit(bool(errors))
