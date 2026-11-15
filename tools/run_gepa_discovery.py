#!/usr/bin/env python3
"""Supervised GEPA discovery comparison; blocks for attributed case reviews."""
import hashlib
import json
import sys
import time
from pathlib import Path
import gepa
from gepa.core.adapter import EvaluationBatch
from gepa_discovery_eval import audit, check_phase, require, EvalError
from local_budget import Budget
from run_gepa_comparison import Experiment, save, read

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/evidence/gepa-discovery'
TASK = '''Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.\n'''

class Study(Experiment):
    def __init__(self, out):
        self.out = out
        out.mkdir(parents=True, exist_ok=False)
        self.dataset = read(HERE/'benchmark.json')
        self.budget = Budget(out/'provider.sqlite', 2_000_000)
        self.calls = []
        self.selection_hash = None
        self.results = []
        self.metric_calls = 0
        self.proposals = 0
        paths = [HERE/'benchmark.json',HERE/'protocol.md',HERE/'fixed.md',ROOT/'tools/gepa_discovery_eval.py',Path(__file__).resolve()] + sorted((HERE/'upstream').glob('*'))
        self.frozen = {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
        save(out/'input-freeze.json',self.frozen)
    def assert_frozen(self):
        for name, digest in self.frozen.items():
            require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,'frozen input changed: '+name)
        if self.selection_hash:
            require(hashlib.sha256((self.out/'selected-prompt.json').read_bytes()).hexdigest()==self.selection_hash,'selection changed')
    def reserve_launch(self):
        super().reserve_launch()
        require(len(self.calls)<20, '20-call cap')
        require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<5, '$5 controller soft cap')
    def source(self, component, phase):
        check_phase(self.dataset,component,phase,self.selection_hash is not None)
        return (HERE/self.dataset['components'][component]['source']).read_text()
    def validate_report(self, report, source):
        require(isinstance(report,dict) and set(report)=={'findings'},'report object must contain findings only')
        fs=report.get('findings')
        require(isinstance(fs,list) and len(fs)<=6,'at most six findings')
        dummy={'reviewer':'structural-only','cases':[{'id':'_structural','finding_ids':[],'reason':'not scoring'}], 'findings':[{'id':f.get('id'),'verdict':'valid','reason':'structural validation only'} for f in fs]}
        audit(report,source,[{'id':'_structural','question_required':False}],dummy)
    def review(self, component, phase, paragraph, category):
        source=self.source(component,phase)
        numbered='\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1))
        prompt=TASK+'\nREVIEW PARAGRAPH:\n'+paragraph+'\nSOURCE:\n'+numbered
        result, ids=self.call(prompt,category,component,lambda r:self.validate_report(r,source))
        dest=self.out/f'review-{ids[-1]:03}.json'
        cases=self.dataset['components'][component]['cases']
        skeleton={'reviewer':'operator:source-reviewed', 'cases':[{'id':c['id'],'finding_ids':[],'reason':'REVIEW REQUIRED'} for c in cases], 'findings':[{'id':f['id'],'verdict':'unreviewed','reason':'REVIEW REQUIRED'} for f in result['findings']]}
        save(dest,skeleton)
        print(f'REVIEW REQUIRED {component} call={ids[-1]} report={self.out}/calls/{ids[-1]:03}-{category}-{component}/validated.json review={dest}',flush=True)
        ready=dest.with_suffix('.ready')
        start=time.monotonic()
        while not ready.exists():
            if time.monotonic()-start>1800: raise EvalError('review timed out; incomplete')
            time.sleep(.25)
        assessment=read(dest)
        require(all(r.get('reason')!='REVIEW REQUIRED' for r in assessment['cases']+assessment['findings']),'unfinished review')
        summary=audit(result,source,cases,assessment)
        rec={'component':component,'phase':phase,'category':category,'call_ids':ids,'review':dest.name,'summary':summary}
        self.results.append(rec);save(self.out/'results.json',self.results)
        return result,ids,summary
    def evaluate(self,batch,candidate,capture_traces=False):
        require(self.metric_calls+len(batch)<=8,'metric cap')
        outputs=[];scores=[];traces=[]
        for component in batch:
            self.metric_calls+=1
            report,ids,summary=self.review(component,'optimization',candidate['review'],'optimization')
            score=max(0,summary['found']/summary['total']-.1*summary['false'])
            feedback={'summary':summary}
            if component in self.dataset['train']:
                feedback['missed']=[c['description'] for c in self.dataset['components'][component]['cases'] if c['id'] in summary['missing']]
            trace={'component':component,'Generated Outputs':report,'Feedback':feedback,'call_ids':ids}
            outputs.append(trace);scores.append(score);traces.append(trace)
        return EvaluationBatch(outputs=outputs,scores=scores,trajectories=traces if capture_traces else None)
    def make_reflective_dataset(self,candidate,eval_batch,components_to_update):
        require(all(x['component'] in self.dataset['train'] for x in eval_batch.trajectories),'reflection must use training only')
        return {'review':eval_batch.trajectories}
    def propose_new_texts(self,candidate,reflective_dataset,components_to_update):
        self.proposals+=1;require(self.proposals<=3,'proposal cap')
        prompt='Improve the review paragraph for source-grounded discovery. Keep it broadly transferable; do not include component names, case IDs, expected answers or example-specific facts. Preserve uncertain intent as OPEN. Return JSON {"review":"..."}.\nCURRENT:\n'+candidate['review']+'\nREVIEWED TRAIN FEEDBACK:\n'+json.dumps(reflective_dataset)
        def valid(x):
            require(isinstance(x,dict) and set(x)=={'review'} and isinstance(x['review'],str) and 40<=len(x['review'])<=4000,'bounded review paragraph required')
            require(not any(w in x['review'].lower() for w in ['afterfunc','gobreaker','waitgroup','cond.signal','timer.stop']),'benchmark-specific reference in proposal')
        result,ids=self.call(prompt,'reflection','train',valid)
        save(self.out/f'proposal-{self.proposals:02}.json',{'candidate':result,'call_ids':ids})
        return result
    def run(self):
        fixed=(HERE/'fixed.md').read_text()
        result=gepa.optimize(seed_candidate={'review':fixed},trainset=self.dataset['train'],valset=self.dataset['validation'],adapter=self,
          skip_perfect_score=False,reflection_minibatch_size=1,max_metric_calls=6,seed=17,run_dir=str(self.out/'gepa'),cache_evaluation=False,
          display_progress_bar=False,raise_on_exception=True,use_merge=False,candidate_selection_strategy='current_best',acceptance_criterion='improvement_or_equal')
        require(result.total_metric_calls==self.metric_calls,'GEPA metric count mismatch')
        selection={'candidate':result.best_candidate,'metric_calls':result.total_metric_calls,'best_index':result.best_idx,'candidates':result.candidates,'validation_scores':result.val_aggregate_scores,'parents':result.parents}
        save(self.out/'selected-prompt.json',selection)
        self.selection_hash=hashlib.sha256((self.out/'selected-prompt.json').read_bytes()).hexdigest()
        for i,component in enumerate(self.dataset['test']):
            arms=['fixed','gepa'] if i%2==0 else ['gepa','fixed']
            for arm in arms:
                self.review(component,'final',fixed if arm=='fixed' else selection['candidate']['review'],'final-'+arm)
        self.assert_frozen()
        save(self.out/'status.json',{'status':'complete','calls':len(self.calls),'metrics':self.metric_calls,'proposals':self.proposals})

if __name__=='__main__':
    s=Study(Path(sys.argv[1]).resolve())
    try:
        s.run()
    except Exception as exc:
        save(s.out/'status.json',{'status':'blocked','error':str(exc),'calls':len(s.calls),'metrics':s.metric_calls})
        raise
