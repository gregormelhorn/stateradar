#!/usr/bin/env python3
"""Run two source-only fixed-prompt baseline samples per reviewed component."""
import hashlib
import json
import sys
from pathlib import Path
from gepa_discovery_eval import require
from gepa_training_catalog import validate_catalog, validate_independent_review, build_prompt
from local_budget import Budget
from run_gepa_comparison import Experiment, save, read
from run_gepa_discovery import Study, TASK

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/evidence/gepa-training-catalog'
FIXED=ROOT/'docs/evidence/gepa-discovery/fixed.md'
IDS={'G01','G02','C01','C02','W01','W02','W03','W04','T01','T02','P01','P02'}
ORDER=['gobreaker','cond','waitgroup','timer','pool','pool','timer','waitgroup','cond','gobreaker']

class Baseline(Experiment):
    def __init__(self,out):
        self.out=out
        out.mkdir(parents=True,exist_ok=False)
        self.catalog=read(HERE/'catalog.json')
        validate_catalog(self.catalog,ROOT,IDS)
        validate_independent_review(self.catalog,read(HERE/'independent-review/review.json'))
        require(set(ORDER)==set(self.catalog['components']) and all(ORDER.count(c)==2 for c in set(ORDER)), 'two calls per component required')
        self.calls=[]; self.budget=Budget(out/'provider.sqlite',2_000_000)
        names={HERE/'catalog.json',HERE/'protocol.md',HERE/'independent-review/review.json',HERE/'pool-source/input-map.json',FIXED,
               ROOT/'tools/gepa_training_catalog.py',ROOT/'tools/run_gepa_training_baseline.py',ROOT/'tools/run_gepa_discovery.py',ROOT/'tools/gepa_discovery_eval.py',ROOT/'tools/run_gepa_comparison.py'}
        for component in self.catalog['components'].values():
            names.add(ROOT/component['source'])
            for case in component['cases']:
                for anchor in case['evidence']:names.add(ROOT/anchor['file'])
        self.frozen={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(names)}
        save(out/'input-freeze.json',self.frozen)
        self.trials=[]
    def assert_frozen(self):
        for path,digest in self.frozen.items():
            require(hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'frozen input changed: '+path)
    def reserve_launch(self):
        super().reserve_launch()
        require(len(self.calls)<20,'20-launch cap')
        require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<3,'$3 controller soft cap')
    def run(self):
        fixed=FIXED.read_text()
        for component in ORDER:
            source=(ROOT/self.catalog['components'][component]['source']).read_text()
            prompt=build_prompt(source,fixed,TASK)
            report,ids=self.call(prompt,'fixed-baseline',component,lambda x:Study.validate_report(None,x,source))
            self.trials.append({'component':component,'call_ids':ids,'finding_count':len(report['findings']), 'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest()})
            save(self.out/'trials.json',self.trials)
        self.assert_frozen()
        save(self.out/'status.json',{'status':'complete','calls':len(self.calls),'trials':len(self.trials)})

if __name__=='__main__':
    runner=Baseline(Path(sys.argv[1]).resolve())
    try: runner.run()
    except Exception as exc:
        save(runner.out/'status.json',{'status':'blocked','error':str(exc),'calls':len(runner.calls),'trials':len(runner.trials)})
        raise
