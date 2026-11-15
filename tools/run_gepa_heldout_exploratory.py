#!/usr/bin/env python3
"""Run the predeclared, post-selection candidate diagnostic (not a holdout)."""
import hashlib
import sys
from pathlib import Path
from run_gepa_heldout import Heldout, HERE, TRAIN, FIXED
from run_gepa_comparison import read, save
from gepa_discovery_eval import require
from local_budget import Budget

class Diagnostic(Heldout):
 def __init__(self,out):
  main=HERE/'runs'; status=read(main/'status.json');require(status['status']=='complete','primary incomplete')
  declaration=read(HERE/'exploratory-declaration.json');selection=read(main/'selected-prompt.json')
  self.candidate=selection['candidates'][declaration['candidate_index']]['review']
  require(hashlib.sha256(self.candidate.encode()).hexdigest()==declaration['candidate_sha256'],'candidate differs from declaration')
  require(hashlib.sha256(FIXED.read_bytes()).hexdigest()==declaration['fixed_sha256'],'fixed prompt differs from declaration')
  require(self.candidate!=selection['candidate']['review'],'diagnostic candidate was selected')
  self.previous=read(main/'calls.json'); self.out=out;out.mkdir(parents=True,exist_ok=False)
  self.dataset=read(HERE/'dataset.json');self.train=read(TRAIN/'catalog.json')
  self.calls=[];self.results=[];self.budget=Budget(out/'provider.sqlite',2_000_000)
  self.metric_calls=0;self.proposals=0;self.frozen=read(main/'input-freeze.json')
  (out/'selected-prompt.json').write_bytes((main/'selected-prompt.json').read_bytes())
  self.selection_hash=hashlib.sha256((out/'selected-prompt.json').read_bytes()).hexdigest()
  self.assert_frozen()
 def reserve_launch(self):
  require(len(self.previous)+len(self.calls)<25,'combined 25-launch cap')
  require(sum(c['cost']['total_usd_estimate'] for c in self.previous+self.calls)<6,'combined $6 soft cap')
  super().reserve_launch()
 def run(self):
  for name in ('scanner','atomic'):
   for repeat in range(2):self.fresh(name,'final',self.candidate,f'diagnostic-r{repeat}')
  self.assert_frozen();save(self.out/'status.json',{'status':'complete','calls':len(self.calls),'scope':'post-selection exploratory'})
if __name__=='__main__':
 s=Diagnostic(Path(sys.argv[1]).resolve())
 try:s.run()
 except Exception as exc:
  save(s.out/'status.json',{'status':'blocked','error':str(exc),'calls':len(s.calls)});raise
