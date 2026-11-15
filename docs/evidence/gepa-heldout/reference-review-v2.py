import json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'tools')
from run_gepa_comparison import Experiment, save
from gepa_discovery_eval import require
from local_budget import Budget
ROOT=Path.cwd();HERE=ROOT/'docs/evidence/gepa-heldout';OUT=HERE/'reference-review-v2'
OUT.mkdir(exist_ok=False)
class Review(Experiment):
 def __init__(self):self.out=OUT;self.calls=[];self.budget=Budget(OUT/'provider.sqlite',2_000_000)
 def assert_frozen(self):pass
r=Review();data=json.loads((HERE/'dataset.json').read_text());test=(HERE/'reference/reference_test.go').read_text()
for component in ['pipe','scanner','atomic']:
 source=(ROOT/data['components'][component]['source']).read_text(); cases=data['components'][component]['cases']
 prompt='Independently review whether each proposed behavioral observation follows from the source and what its supplied executable test actually proves. Do not decide domain intent. A finite timeout proves only bounded nonreturn. Return JSON {"cases":[{"id":"...","verdict":"confirmed|refuted|unclear","reason":"...","line":1,"fragment":"exact source substring"}]}. Assess every case exactly once.\nCANDIDATE OBSERVATIONS:\n'+json.dumps(cases)+'\nSOURCE:\n'+'\n'.join(f'{i}: {s}' for i,s in enumerate(source.splitlines(),1))+'\nREFERENCE TEST SOURCE:\n'+test
 def validator(out):
  require(isinstance(out,dict) and set(out)=={'cases'} and isinstance(out['cases'],list),'expected cases')
  require(sorted(x.get('id') for x in out['cases'])==sorted(x['id'] for x in cases),'exact case inventory')
  lines=source.splitlines()
  for x in out['cases']:
   require(x.get('verdict') in ('confirmed','refuted','unclear') and isinstance(x.get('reason'),str) and x['reason'].strip(),'review reason/verdict required')
   n=x.get('line');frag=x.get('fragment');require(type(n)is int and 1<=n<=len(lines) and isinstance(frag,str) and len(frag.strip())>=4 and frag in lines[n-1],'invalid source citation')
 value,ids=r.call(prompt,'reference-review',component,validator)
 save(OUT/f'{component}.json',{'review':value,'call_ids':ids})
