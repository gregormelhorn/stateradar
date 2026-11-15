#!/usr/bin/env python3
"""Bounded GEPA training with frozen selection and held-out components."""
import hashlib
import json
import sys
import time
from pathlib import Path
import gepa
from gepa.core.adapter import EvaluationBatch
from gepa_discovery_eval import audit, require, EvalError
from gepa_heldout_eval import check_splits, permit, train_feedback
from local_budget import Budget
from run_gepa_comparison import Experiment, save, read
from run_gepa_discovery import Study, TASK
from gepa_training_catalog import build_prompt

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/evidence/gepa-heldout'
TRAIN=ROOT/'docs/evidence/gepa-training-catalog'
FIXED=ROOT/'docs/evidence/gepa-discovery/fixed.md'
OLD_IDS={'gobreaker':0,'cond':1,'waitgroup':2,'timer':3,'pool':4}

class Heldout(Experiment):
 def __init__(self,out):
  self.out=out;out.mkdir(parents=True,exist_ok=False)
  self.dataset=read(HERE/'dataset.json');check_splits(self.dataset)
  self.train=read(TRAIN/'catalog.json')
  require(set(self.dataset['train'])==set(self.train['components']),'training component coverage differs')
  for comp in self.dataset['validation']+self.dataset['test']:
   ref=read(HERE/'reference-review-v3'/f'{comp}.json')['review']['cases']
   require({x['id'] for x in ref}=={x['id'] for x in self.dataset['components'][comp]['cases']} and all(x['verdict']=='confirmed' for x in ref),'held-out AI reference review incomplete')
  self.calls=[];self.results=[];self.budget=Budget(out/'provider.sqlite',2_000_000)
  self.metric_calls=0;self.proposals=0;self.selection_hash=None
  paths={HERE/'dataset.json',HERE/'protocol.md',HERE/'reference/reference_test.go',HERE/'reference-v2.jsonl',FIXED,TRAIN/'catalog.json',TRAIN/'runs/calls.json',TRAIN/'runs/trials.json',ROOT/'tools/gepa_heldout_eval.py',ROOT/'tools/run_gepa_heldout.py',ROOT/'tools/run_gepa_discovery.py',ROOT/'tools/gepa_discovery_eval.py',ROOT/'tools/run_gepa_comparison.py',ROOT/'tools/gepa_training_catalog.py'}
  paths.update(p for p in (HERE/'upstream').glob('*') if p.is_file())
  paths.update(p for p in (HERE/'reference-review-v3').rglob('*') if p.is_file() and p.suffix!='.sqlite')
  paths.update(p for p in HERE.glob('*jev*.json'))
  previous=read(TRAIN/'runs/calls.json')
  for comp,n in OLD_IDS.items():
   paths.add(ROOT/self.train['components'][comp]['source'])
   paths.add(TRAIN/'runs'/f'review-{n:03}.json')
   paths.add(TRAIN/'runs'/previous[n]['directory']/'validated.json')
  self.frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}
  save(out/'input-freeze.json',self.frozen)
 def assert_frozen(self):
  for name,h in self.frozen.items():require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'frozen input changed: '+name)
  if self.selection_hash:require(hashlib.sha256((self.out/'selected-prompt.json').read_bytes()).hexdigest()==self.selection_hash,'selection changed')
 def reserve_launch(self):
  super().reserve_launch();require(len(self.calls)<25,'25-launch cap')
  require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<6,'$6 controller soft cap')
 def component(self,name):
  return self.train['components'][name] if name in self.dataset['train'] else self.dataset['components'][name]
 def source(self,name,phase):
  permit(self.dataset,name,phase,self.selection_hash is not None)
  return (ROOT/self.component(name)['source']).read_text()
 def fresh(self,name,phase,paragraph,category):
  source=self.source(name,phase);prompt=build_prompt(source,paragraph,TASK)
  report,ids=self.call(prompt,category,name,lambda x:Study.validate_report(None,x,source))
  dest=self.out/f'review-{ids[-1]:03}.json'; cases=self.component(name)['cases']
  save(dest,{'reviewer':'AI operator:source-reviewed','cases':[{'id':c['id'],'finding_ids':[],'reason':'REVIEW REQUIRED'} for c in cases], 'findings':[{'id':f['id'],'verdict':'unreviewed','reason':'REVIEW REQUIRED'} for f in report['findings']]})
  print(f'REVIEW REQUIRED {name} call={ids[-1]} report={self.out}/calls/{ids[-1]:03}-{category}-{name}/validated.json review={dest}',flush=True)
  ready=dest.with_suffix('.ready');start=time.monotonic()
  while not ready.exists():
   if time.monotonic()-start>1800:raise EvalError('review timeout')
   time.sleep(.25)
  review=read(dest);require(all(x.get('reason')!='REVIEW REQUIRED' for x in review['cases']+review['findings']),'unfinished review')
  summary=audit(report,source,cases,review)
  rec={'component':name,'phase':phase,'category':category,'call_ids':ids,'review':dest.name,'summary':summary}
  self.results.append(rec);save(self.out/'results.json',self.results)
  return report,review,summary,ids
 def historical(self,name):
  source=self.source(name,'optimization');n=OLD_IDS[name];calls=read(TRAIN/'runs/calls.json')
  report=read(TRAIN/'runs'/calls[n]['directory']/'validated.json');review=read(TRAIN/'runs'/f'review-{n:03}.json')
  summary=audit(report,source,self.component(name)['cases'],review)
  return report,review,summary,[]
 def evaluate(self,batch,candidate,capture_traces=False):
  require(self.metric_calls+len(batch)<=14,'14 metric cap');outs=[];scores=[];traces=[]
  for name in batch:
   self.metric_calls+=1
   if name in self.dataset['train'] and candidate['review']==FIXED.read_text():
    report,review,summary,ids=self.historical(name);category='historical-seed'
   else:
    report,review,summary,ids=self.fresh(name,'optimization',candidate['review'],'optimization');category='fresh'
   score=max(0,summary['found']/summary['total']-.1*summary['false'])
   feedback={'summary':summary}
   if name in self.dataset['train']:
    feedback['reviewed_cases']=[{'id':x['id'],'description':x['expected'],'kind':x['kind']} for x in self.component(name)['cases'] if x['id'] in summary['missing']]
    feedback['finding_reviews']=review['findings']
   trace={'component':name,'Generated Outputs':report,'Feedback':feedback,'call_ids':ids,'mode':category}
   outs.append(trace);scores.append(score);traces.append(trace)
   save(self.out/f'metric-{self.metric_calls:02}.json',{'candidate':candidate,'trace':trace,'score':score})
  return EvaluationBatch(outputs=outs,scores=scores,trajectories=traces if capture_traces else None)
 def make_reflective_dataset(self,candidate,eval_batch,components_to_update):
  train_feedback(self.dataset,eval_batch.trajectories)
  return {'review':eval_batch.trajectories}
 def propose_new_texts(self,candidate,reflective_dataset,components_to_update):
  self.proposals+=1;require(self.proposals<=1,'one-proposal cap')
  prompt='Improve this source-grounded discovery review paragraph using only the reviewed TRAIN feedback. Generalize failures without case IDs, API or component names or hidden answers. Preserve valid controls, source scope, event order, and OPEN policy questions. Return JSON {"review":"..."}.\nCURRENT:\n'+candidate['review']+'\nTRAIN FEEDBACK:\n'+json.dumps(reflective_dataset)
  def valid(x):
   require(isinstance(x,dict) and set(x)=={'review'} and isinstance(x['review'],str) and 40<=len(x['review'])<=4000,'invalid proposal')
   require(not any(w in x['review'].lower() for w in ('gobreaker','waitgroup','afterfunc','channelpool','synctest','scanlines','io.pipe','atomic.value')),'benchmark-specific name in proposal')
  result,ids=self.call(prompt,'reflection','train',valid);save(self.out/'proposal.json',{'candidate':result,'call_ids':ids});return result
 def run(self):
  fixed=FIXED.read_text()
  result=gepa.optimize(seed_candidate={'review':fixed},trainset=self.dataset['train'],valset=self.dataset['validation'],adapter=self,
    skip_perfect_score=False,reflection_minibatch_size=5,max_metric_calls=11,seed=17,run_dir=str(self.out/'gepa'),cache_evaluation=False,
    display_progress_bar=False,raise_on_exception=True,use_merge=False,candidate_selection_strategy='current_best',acceptance_criterion='improvement_or_equal')
  require(result.total_metric_calls==self.metric_calls,'metric count mismatch')
  selection={'candidate':result.best_candidate,'metric_calls':result.total_metric_calls,'best_index':result.best_idx,'candidates':result.candidates,'validation_scores':result.val_aggregate_scores,'parents':result.parents}
  save(self.out/'selected-prompt.json',selection);self.selection_hash=hashlib.sha256((self.out/'selected-prompt.json').read_bytes()).hexdigest()
  for i,name in enumerate(self.dataset['test']):
   for repeat in range(2):
    order=['fixed','gepa'] if (i+repeat)%2==0 else ['gepa','fixed']
    for arm in order:self.fresh(name,'final',fixed if arm=='fixed' else selection['candidate']['review'],f'final-{arm}-r{repeat}')
  self.assert_frozen();save(self.out/'status.json',{'status':'complete','calls':len(self.calls),'metrics':self.metric_calls,'proposals':self.proposals})

if __name__=='__main__':
 s=Heldout(Path(sys.argv[1]).resolve())
 try:s.run()
 except Exception as exc:
  save(s.out/'status.json',{'status':'blocked','error':str(exc),'calls':len(s.calls),'metrics':s.metric_calls});raise
