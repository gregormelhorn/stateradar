#!/usr/bin/env python3
"""Independent isolated AI review of source-fragment labels, before Jev."""
import hashlib
import json
from pathlib import Path
from gepa_discovery_eval import require
from local_budget import Budget
from run_gepa_comparison import Experiment,read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/routing-labels';OUT=BASE/'reference-review'
class Review(Experiment):
 def __init__(self):
  self.out=OUT;OUT.mkdir(exist_ok=False);self.calls=[];self.budget=Budget(OUT/'provider.sqlite',2_000_000)
  self.frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((BASE/'inputs').glob('*.json'))}
  save(OUT/'input-freeze.json',self.frozen)
 def assert_frozen(self):
  for p,h in self.frozen.items():require(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,'input changed: '+p)
 def reserve_launch(self):
  super().reserve_launch();require(len(self.calls)<8,'8 review call cap');require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<3,'review cost cap')
r=Review();manifest=read(BASE/'inputs/manifest.json')
for name in ('once','pipe','buffer','value'):
 info=manifest['components'][name];source=(ROOT/info['source']).read_text();checks=read(BASE/info['checks'])
 prompt=('Independently classify each check using ONLY whether its quoted fragment explicitly supports, contradicts, or leaves unclear the exact statement. Surrounding source may clarify meaning, but cannot add unquoted material conditions, actors, events, ordering or outcomes. For ordering, every material detail must be contemplated by the fragment; an unmentioned ordering is unclear. Treat code comments as quoted statements, not automatically as runtime behavior. A call site does not establish the callee error contract. Do not decide domain policy. You receive no proposed labels or Jev results. Return JSON {"cases":[{"id":"...","verdict":"supported|contradicted|unclear","reason":"..."}]} with every id exactly once.\nCHECKS:\n'+json.dumps(checks)+'\nSOURCE:\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1)))
 def valid(value):
  require(isinstance(value,dict) and set(value)=={'cases'} and isinstance(value['cases'],list),'cases required')
  require(sorted(x.get('id') for x in value['cases'])==sorted(x['id'] for x in checks),'case inventory')
  for x in value['cases']:require(x.get('verdict') in ('supported','contradicted','unclear') and isinstance(x.get('reason'),str) and x['reason'].strip(),'verdict and reason')
 value,ids=r.call(prompt,'reference-review',name,valid);save(OUT/f'{name}.json',{'review':value,'call_ids':ids})
r.assert_frozen();save(OUT/'status.json',{'status':'complete','calls':len(r.calls)})
