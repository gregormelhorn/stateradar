#!/usr/bin/env python3
"""Prospective paired-order model comparison on frozen distinct components."""
import hashlib
import json
import sys
import time
from pathlib import Path
from local_budget import Budget
from gepa_discovery_eval import audit,require,EvalError
from gepa_selection import classify
from gepa_training_catalog import build_prompt
from run_gepa_comparison import Experiment,read,save
from run_gepa_discovery import Study,TASK
from verify_gepa_training import verify_test_log

ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'docs/evidence/gepa-prospective'
class Prospective(Experiment):
 def __init__(self,out):
  self.out=out;out.mkdir(parents=True,exist_ok=False);self.calls=[];self.results=[];self.budget=Budget(out/'provider.sqlite',2_000_000)
  self.data=read(HERE/'dataset.json');self.selection=read(ROOT/'docs/evidence/gepa-heldout/runs/selected-prompt.json')
  require(classify(self.selection['validation_scores'])['status']=='tie','prior selection must be reported as a tie')
  verify_test_log(HERE/'reference.jsonl',{'TestOncePanicDone','TestOnceConcurrentWait','TestBufferEmptyReads','TestBufferZeroReadInvalidatesUnread'},3)
  require(read(HERE/'reference-review/status.json')['status']=='complete','reference AI review incomplete')
  for name in self.data['components']:
   cases=self.data['components'][name]['cases'];review=read(HERE/'reference-review'/f'{name}.json')['review']['cases']
   require({c['id'] for c in review}=={c['id'] for c in cases} and all(c['verdict']=='confirmed' for c in review),'reference case unconfirmed')
  paths=[HERE/'dataset.json',HERE/'protocol.md',HERE/'reference/reference_test.go',HERE/'reference.jsonl',ROOT/'docs/evidence/gepa-heldout/runs/selected-prompt.json',ROOT/'docs/evidence/gepa-discovery/fixed.md',ROOT/'tools/run_gepa_prospective.py',ROOT/'tools/gepa_selection.py',ROOT/'tools/gepa_discovery_eval.py',ROOT/'tools/gepa_training_catalog.py',ROOT/'tools/run_gepa_discovery.py',ROOT/'tools/run_gepa_comparison.py']
  paths += [p for p in (HERE/'upstream').glob('*') if p.is_file()]
  paths += [p for p in (HERE/'reference-review').rglob('*') if p.is_file() and p.suffix!='.sqlite']
  self.frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)};save(out/'input-freeze.json',self.frozen)
  self.paragraph={'fixed':(ROOT/'docs/evidence/gepa-discovery/fixed.md').read_text(),'candidate':self.selection['candidates'][1]['review']}
  require(self.paragraph['fixed']==self.selection['candidate']['review'] and self.paragraph['candidate']!=self.paragraph['fixed'],'unexpected prompt selection')
 def assert_frozen(self):
  for name,digest in self.frozen.items():require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'frozen input changed: '+name)
 def reserve_launch(self):
  super().reserve_launch();require(len(self.calls)<12,'12-launch cap');require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<3,'$3 soft cap')
 def run(self):
  for i,name in enumerate(('once','buffer')):
   comp=self.data['components'][name];source=(ROOT/comp['source']).read_text()
   for repeat in range(2):
    arms=('fixed','candidate') if (i+repeat)%2==0 else ('candidate','fixed')
    for arm in arms:
     report,ids=self.call(build_prompt(source,self.paragraph[arm],TASK),f'{arm}-r{repeat}',name,lambda x:Study.validate_report(None,x,source))
     dest=self.out/f'review-{ids[-1]:03}.json'
     save(dest,{'reviewer':'AI operator:source-reviewed','cases':[{'id':x['id'],'finding_ids':[],'reason':'REVIEW REQUIRED'} for x in comp['cases']], 'findings':[{'id':f['id'],'verdict':'unreviewed','reason':'REVIEW REQUIRED'} for f in report['findings']]})
     print(f'REVIEW REQUIRED {name} call={ids[-1]} report={self.out}/calls/{ids[-1]:03}-{arm}-r{repeat}-{name}/validated.json review={dest}',flush=True)
     start=time.monotonic()
     while not dest.with_suffix('.ready').exists():
      if time.monotonic()-start>1800:raise EvalError('review timeout')
      time.sleep(.25)
     review=read(dest);require(all(x.get('reason')!='REVIEW REQUIRED' for x in review['cases']+review['findings']),'unfinished review')
     summary=audit(report,source,comp['cases'],review);self.results.append({'component':name,'arm':arm,'repeat':repeat,'call_ids':ids,'review':dest.name,'summary':summary});save(self.out/'results.json',self.results)
  self.assert_frozen();save(self.out/'status.json',{'status':'complete','calls':len(self.calls)})
if __name__=='__main__':
 s=Prospective(Path(sys.argv[1]).resolve())
 try:s.run()
 except Exception as exc:
  save(s.out/'status.json',{'status':'blocked','error':str(exc),'calls':len(s.calls)});raise
