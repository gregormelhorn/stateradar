#!/usr/bin/env python3
"""Post-comparison bounded Flash-to-Jev diagnostic; no automatic acceptance."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from local_budget import Budget
from local_models import draft_verify,InvalidDraft
from routing_flash_eval import score
from routing_label_integrity import verify_source
from run_gepa_comparison import read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/routing-labels'
def task(checks):
 return ('For every supplied check, decide whether the quoted fragment explicitly supports the exact statement. If it does, output an identical claim with the same id, kind, statement, line, and fragment. Otherwise put a question beginning with the exact id followed by a colon. Keep every id; do not use reference labels or decide domain policy. Checks:\n'+json.dumps(checks))
def run(out):
 out.mkdir(exist_ok=False);budget=Budget(out/'provider.sqlite',2_000_000);manifest=read(BASE/'inputs/manifest.json');frozen=read(BASE/'frozen/input-freeze.json')
 for p in (BASE/'flash-diagnostic-protocol.md',ROOT/'tools/run_routing_flash_diagnostic.py',ROOT/'tools/routing_flash_eval.py'):
  frozen[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 save(out/'input-freeze.json',frozen);results=[];current=None
 def check():
  for name,digest in frozen.items():
   if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest:raise ValueError('frozen input changed: '+name)
  if any(c['status']!='settled' for c in budget.calls()):raise ValueError('unsettled provider cost')
 try:
  for name in ('once','pipe','buffer','value'):
   current=name;check();info=manifest['components'][name];source=(ROOT/info['source']).read_text();checks=read(BASE/info['checks']);labels=read(BASE/'frozen'/f'{name}-labels.json');verify_source(source,info['sha256'],checks)
   (out/f'{name}-task.txt').write_text(task(checks));start=time.monotonic()
   result=draft_verify(budget,source,info['source'],task(checks),os.environ['DEEPSEEK_API_KEY'],os.environ['TYPESAFE_API_KEY'],model='jev-1.14.0',max_tokens=6000)
   elapsed=round(time.monotonic()-start,3);save(out/f'{name}-result.json',result)
   metric=score(labels,checks,result);results.append({'component':name,'seconds':elapsed,'audit':metric,'flash_cost_microdollars':result['draft']['cost_microdollars'],'jev_cost_microdollars':result['verification']['cost_microdollars'] if result['verification'] and not result['verification'].get('error') else 0})
   save(out/'results.json',results);save(out/'ledger.json',{'limit_microdollars':budget.limit,'total_microdollars':budget.total(),'calls':budget.calls()})
   if result['verification'] and result['verification'].get('error'):raise ValueError('Jev verification failed: '+result['verification']['error'])
   check();print(name,'diagnostic done',flush=True)
  save(out/'status.json',{'status':'complete','components':len(results)})
 except Exception as exc:
  if isinstance(exc,InvalidDraft):(out/f'{current}-invalid-draft.txt').write_text(exc.text)
  save(out/'ledger.json',{'limit_microdollars':budget.limit,'total_microdollars':budget.total(),'calls':budget.calls()})
  save(out/'status.json',{'status':'BLOCKED','component':current,'error':str(exc),'components':len(results)});raise
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
