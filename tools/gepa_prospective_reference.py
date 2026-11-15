#!/usr/bin/env python3
"""Independent AI reference review before prospective comparison."""
import json
from pathlib import Path
from run_gepa_comparison import Experiment, save
from gepa_discovery_eval import require
from local_budget import Budget
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'docs/evidence/gepa-prospective';OUT=HERE/'reference-review'
class Review(Experiment):
 def __init__(self):
  self.out=OUT;OUT.mkdir(exist_ok=False);self.calls=[];self.budget=Budget(OUT/'provider.sqlite',2_000_000)
 def assert_frozen(self):pass
 def reserve_launch(self):
  super().reserve_launch();require(len(self.calls)<4,'reference call cap');require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<3,'reference cost cap')
r=Review();data=json.loads((HERE/'dataset.json').read_text());test=(HERE/'reference/reference_test.go').read_text()
for component in ('once','buffer'):
 source=(ROOT/data['components'][component]['source']).read_text();cases=data['components'][component]['cases']
 prompt='Independently check each proposed behavior against the cited source and the supplied executable test. No domain decisions. A finite timeout proves only bounded nonreturn and may miss an unscheduled thread. Return JSON {"cases":[{"id":"...","verdict":"confirmed|refuted|unclear","reason":"...","line":1,"fragment":"exact source substring"}]}. Assess every case.\nCANDIDATE OBSERVATIONS:\n'+json.dumps(cases)+'\nSOURCE:\n'+'\n'.join(f'{i}: {s}' for i,s in enumerate(source.splitlines(),1))+'\nREFERENCE TEST SOURCE:\n'+test
 def valid(out):
  require(isinstance(out,dict) and set(out)=={'cases'} and isinstance(out['cases'],list),'expected cases')
  require(sorted(x.get('id') for x in out['cases'])==sorted(x['id'] for x in cases),'case coverage')
  lines=source.splitlines()
  for x in out['cases']:
   require(x.get('verdict') in ('confirmed','refuted','unclear') and isinstance(x.get('reason'),str) and x['reason'].strip(),'verdict/reason')
   n=x.get('line');frag=x.get('fragment');require(type(n)is int and 1<=n<=len(lines) and isinstance(frag,str) and len(frag.strip())>=4 and frag in lines[n-1],'citation')
 value,ids=r.call(prompt,'reference-review',component,valid);save(OUT/f'{component}.json',{'review':value,'call_ids':ids})
save(OUT/'status.json',{'status':'complete','calls':len(r.calls)})
