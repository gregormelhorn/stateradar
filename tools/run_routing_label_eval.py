#!/usr/bin/env python3
"""Run fixed fragment checks: dev first, then component-heldout Jev vs direct Codex."""
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from gepa_discovery_eval import require
from jev_eval import evaluate
from local_budget import Budget
from local_models import jev_batch
from routing_compare_prompt import build
from routing_evaluation import allow,check_splits
from routing_label_integrity import verify_source
from run_gepa_comparison import Experiment,read,save
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/routing-labels'
class Run(Experiment):
 def __init__(self,out):
  self.out=out;out.mkdir(exist_ok=False);self.calls=[];self.results=[]
  self.budget=Budget(out/'codex.sqlite',2_000_000);self.jev_budget=Budget(out/'jev.sqlite',2_000_000)
  self.manifest=read(BASE/'inputs/manifest.json');check_splits(self.manifest)
  self.frozen=read(BASE/'frozen/input-freeze.json')
  for path in (ROOT/'tools/run_routing_label_eval.py',ROOT/'tools/routing_compare_prompt.py'):
   self.frozen[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
  save(out/'input-freeze.json',self.frozen);self.dev_hash=None;self.assert_frozen()
 def assert_frozen(self):
  for name,h in self.frozen.items():require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==h,'input changed: '+name)
  if self.dev_hash:require(hashlib.sha256((self.out/'dev-complete.json').read_bytes()).hexdigest()==self.dev_hash,'dev freeze changed')
 def reserve_launch(self):
  super().reserve_launch();require(len(self.calls)<8,'8 comparator call cap');require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<3,'comparator soft cost cap')
 def one(self,name,phase):
  allow(self.manifest,name,phase,self.dev_hash is not None);self.assert_frozen()
  info=self.manifest['components'][name];source=(ROOT/info['source']).read_text();checks=read(BASE/info['checks']);labels=read(BASE/'frozen'/f'{name}-labels.json')
  verify_source(source,info['sha256'],checks)
  start=time.monotonic();jev=jev_batch(self.jev_budget,source,info['source'],checks,os.environ.get('TYPESAFE_API_KEY'),'jev-1.14.0')
  seconds=time.monotonic()-start;save(self.out/f'{name}-jev.json',jev);save(self.out/'jev-ledger.json',{'limit_microdollars':self.jev_budget.limit,'total_microdollars':self.jev_budget.total(),'calls':self.jev_budget.calls()})
  require(all(x['status']=='settled' for x in self.jev_budget.calls()),'unsettled Jev cost')
  prompt=build(source,checks)
  def valid(out):
   require(isinstance(out,dict) and set(out)=={'cases'} and isinstance(out['cases'],list),'cases required')
   require(sorted(x.get('id') for x in out['cases'])==sorted(x['id'] for x in checks),'case inventory mismatch')
   for x in out['cases']:require(x.get('choice') in ('supported','contradicted','unclear') and isinstance(x.get('reason'),str) and x['reason'].strip(),'verdict or reason missing')
  answer,ids=self.call(prompt,phase,name,valid);byid={x['id']:x for x in answer['cases']};calls=[self.calls[i] for i in ids]
  usage=[read(self.out/c['directory']/'usage-checkpoint.json')['usage'] for c in calls]
  require(all(isinstance(x,dict) and type(x.get('input_tokens')) is int for x in usage),'comparator usage missing')
  cost=round(sum(c['cost']['total_usd_estimate'] for c in calls)*1_000_000)
  direct={'source_sha256':info['sha256'],'model':'gpt-6.1-sol','input_tokens':sum(x['input_tokens'] for x in usage),'cost_microdollars':cost,'checks':{c['id']:{**c,'source':info['source'],'choice':byid[c['id']]['choice'],'reason':byid[c['id']]['reason']} for c in checks}}
  save(self.out/f'{name}-direct.json',direct)
  agreed=set(labels['checks']);excluded=sorted(set(jev['checks'])-agreed)
  require(agreed,'no agreed labels to evaluate')
  def subset(batch):return {**batch,'checks':{k:v for k,v in batch['checks'].items() if k in agreed}}
  metrics={'component':name,'phase':phase,'excluded_disputed':excluded,'jev':evaluate(labels,subset(jev)),'direct':evaluate(labels,subset(direct)), 'jev_seconds':round(seconds,3),'direct_seconds':round(sum(c['elapsed_seconds'] for c in calls),3),'direct_call_ids':ids}
  self.results.append(metrics);save(self.out/'results.json',self.results)
  print(name,phase,'done; excluded',len(excluded),flush=True)
 def run(self):
  for phase in ('dev','heldout'):
   for name in self.manifest['splits'][phase]:self.one(name,phase)
   if phase=='dev':
    paths=[self.out/f'{name}-{arm}.json' for name in self.manifest['splits']['dev'] for arm in ('jev','direct')]
    save(self.out/'dev-results.json',self.results);paths += [self.out/'dev-results.json'];dev={str(p.relative_to(self.out)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};save(self.out/'dev-complete.json',dev);self.dev_hash=hashlib.sha256((self.out/'dev-complete.json').read_bytes()).hexdigest()
  self.assert_frozen();save(self.out/'status.json',{'status':'complete','codex_calls':len(self.calls),'jev_calls':len(self.jev_budget.calls())})
if __name__=='__main__':
 s=Run(Path(sys.argv[1]).resolve())
 try:s.run()
 except Exception as exc:
  save(s.out/'jev-ledger.json',{'limit_microdollars':s.jev_budget.limit,'total_microdollars':s.jev_budget.total(),'calls':s.jev_budget.calls()})
  save(s.out/'status.json',{'status':'BLOCKED','error':str(exc),'codex_calls':len(s.calls),'jev_calls':len(s.jev_budget.calls())});raise
