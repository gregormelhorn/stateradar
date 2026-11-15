#!/usr/bin/env python3
"""Metered, isolated three-arm claim-review experiment with a locked final split."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from gepa_eval import validate, score, check_access, validate_splits, EvalError, require
from gepa_search import optimize_review
from local_budget import Budget
from local_models import draft_verify
from pilot_accounting import UsageCheckpoint, cost_report
from run_sol_pilot import codex_environment, read_usage, stop_controller

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/evidence/gepa-bounded'
MODEL='gpt-6.1-sol'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def read(path):return json.loads(path.read_text())
def decode(text):
 text=text.strip()
 if text.startswith('```'):
  lines=text.splitlines();require(lines[-1]=='```','incomplete JSON fence');text='\n'.join(lines[1:-1])
 return json.loads(text)

def inputs():
 paths=list(HERE.glob('*-public.json'))+list(HERE.glob('*-oracle.json'))+list((HERE/'prompts').glob('*'))+list((HERE/'upstream').rglob('*'))
 paths += [HERE/'dataset.json',HERE/'upstream-pins.json',HERE/'protocol.md',HERE/'requirements.txt',HERE/'reference/reference_test.go',HERE/'scripts/reference.py',HERE/'reference-output.jsonl']
 paths += [ROOT/'tools'/n for n in ('run_gepa_comparison.py','gepa_eval.py','gepa_search.py','local_models.py','local_budget.py','jev_local.py','pilot_accounting.py','run_sol_pilot.py')]
 return {str(p.relative_to(ROOT)):sha(p) for p in paths if p.is_file()}

class Experiment:
 def __init__(self,out):
  self.out=out;out.mkdir(parents=True,exist_ok=False)
  self.dataset=read(HERE/'dataset.json');validate_splits(self.dataset)
  self.frozen=inputs();save(out/'input-freeze.json',self.frozen)
  self.budget=Budget(out/'routing.sqlite',2_000_000)
  self.calls=[];self.providers=[];self.baselines={};self.results=[];self.metric_calls=0;self.proposals=0
 def assert_frozen(self):require(inputs()==self.frozen,'frozen experiment inputs changed')
 def reserve_launch(self):
  require(len(self.calls)<40,'40-launch limit reached')
  require(all(c['cost']['complete'] for c in self.calls),'unsettled Codex usage; no more launches')
  require(sum(c['cost']['total_usd_estimate'] for c in self.calls)<10,'controller soft cost ceiling reached')
  require(not any(c['status']=='reserved' for c in self.budget.calls()),'unsettled provider usage')
 def call(self,prompt,category,component,validator):
  self.assert_frozen();errors=[];start=len(self.calls)
  for attempt in range(2):
   self.reserve_launch();index=len(self.calls);dest=self.out/'calls'/f'{index:03}-{category}-{component}';dest.mkdir(parents=True)
   actual=prompt if not attempt else prompt+'\nYour preceding output failed structural validation. Correct the structure without new external evidence.\nERROR: '+errors[-1]+'\nPREVIOUS OUTPUT:\n'+text
   (dest/'prompt.md').write_text(actual)
   checkpoint=UsageCheckpoint(dest);usage=None;began=time.monotonic();failure=None
   with tempfile.TemporaryDirectory(prefix='gepa-isolated-task-') as td:
    # Empty cwd, no user config, no shell tools or web. Check emitted events too.
    argv=[os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or shutil.which('codex'),'-a','never','exec','--ignore-user-config','--skip-git-repo-check',
     '--disable','shell_tool','--disable','unified_exec','-c','forced_login_method="chatgpt"',
     '-c','model_reasoning_effort="medium"','-c','web_search="disabled"',
     '--model',MODEL,'--json','--sandbox','read-only','-C',td,'-o',str((dest/'final.txt').resolve()),'-']
    try:
     with (dest/'events.jsonl').open('w') as stdout,(dest/'stderr.txt').open('w') as stderr:
      with subprocess.Popen(argv,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,env=codex_environment(),start_new_session=True) as proc:
       try:
        proc.stdin.write(actual);proc.stdin.close()
        while proc.poll() is None:
         checkpoint.poll()
         if time.monotonic()-began>240:raise TimeoutError('240 second task timeout')
         time.sleep(.2)
       finally:stop_controller(proc)
     require(proc.returncode==0,'Codex process failed')
     usage=read_usage(dest/'events.jsonl')
     events=[json.loads(l) for l in (dest/'events.jsonl').read_text().splitlines()]
     forbidden=[e for e in events if e.get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change')]
     require(not forbidden,'task attempted forbidden tool access')
    except Exception as exc:failure=str(exc)
    finally:checkpoint.finish(usage)
   cost=cost_report(read(dest/'usage-checkpoint.json'),{'charged_microdollars':0,'reserved_microdollars':0},MODEL)
   row={'id':index,'category':category,'component':component,'attempt':attempt,'repair':bool(attempt),'directory':str(dest.relative_to(self.out)),
    'elapsed_seconds':round(time.monotonic()-began,3),'cost':cost,'failure':failure}
   self.calls.append(row);save(self.out/'calls.json',self.calls)
   if failure:raise EvalError(failure)
   text=(dest/'final.txt').read_text()
   try:
    value=decode(text);validator(value);save(dest/'validated.json',value)
    row['structural_valid']=True;save(self.out/'calls.json',self.calls)
    return value,list(range(start,len(self.calls)))
   except (ValueError,KeyError,TypeError,AttributeError) as exc:
    errors.append(str(exc));row['structural_valid']=False;row['validation_error']=str(exc);save(self.out/'calls.json',self.calls)
  raise EvalError('structural repair exhausted: '+errors[-1])
 def public(self,component,phase):
  check_access(self.dataset,component,phase,(self.out/'selected-prompt.json').exists())
  if phase=='final':require(sha(self.out/'selected-prompt.json')==self.selection_hash,'selected candidate changed after freeze')
  public=read(HERE/self.dataset['components'][component]['public']);source=(HERE/public['source']).read_text()
  return public,source
 def baseline(self,component,phase,repeat):
  public,source=self.public(component,phase);self.reserve_launch()
  before={c['id'] for c in self.budget.calls()};began=time.monotonic()
  task='Draft at most seven narrow cited behavioral claims and OPEN application-policy questions relevant to this inventory. Never assume its claims are true.\n'+json.dumps(public['cases'])
  provider=draft_verify(self.budget,source,public['source'],task,os.environ['DEEPSEEK_API_KEY'],os.environ['TYPESAFE_API_KEY'],model='jev-1.14.0',max_tokens=8192)
  calls=[c for c in self.budget.calls() if c['id'] not in before]
  require(all(c['status']=='settled' for c in calls),'unsettled draft costs')
  provider_cost=sum(c['amount_microdollars'] for c in calls)/1_000_000
  p={'component':component,'phase':phase,'repeat':repeat,'calls':calls,'cost_usd':provider_cost,'seconds':time.monotonic()-began,'response':provider}
  self.providers.append(p);save(self.out/'providers.json',self.providers)
  prompt=self.task(public,source)+'\nADVISORY DRAFT (not truth):\n'+json.dumps(provider)
  result,ids=self.call(prompt,'baseline',component,lambda r:validate(r,public,source))
  baseline={'report':result,'call_ids':ids,'provider_index':len(self.providers)-1,'provider_cost':provider_cost,'public':public,'source':source,'phase':phase,'repeat':repeat}
  save(self.out/f'baseline-{component}-{repeat}.json',baseline)
  return baseline
 def task(self,public,source):
  return (HERE/'prompts/task.md').read_text()+'\nINVENTORY:\n'+json.dumps(public['cases'])+'\nSOURCE:\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1))
 def review(self,component,paragraph,baseline,category):
  public,source=self.public(component,baseline['phase'])
  prompt=self.task(public,source)+'\nIMMUTABLE BASELINE:\n'+json.dumps(baseline['report'])+'\nREVIEW INSTRUCTIONS:\n'+paragraph
  result,ids=self.call(prompt,category,component,lambda r:validate(r,public,source,baseline['report']))
  return result,ids
 def evaluate(self,batch,candidate,capture_traces=False):
  from gepa.core.adapter import EvaluationBatch
  require(self.metric_calls+len(batch)<=8,'eight-metric hard cap')
  outputs=[];scores=[];traces=[]
  for component in batch:
   self.metric_calls+=1
   self.public(component,'optimization') # reject held-out access before launch
   baseline=self.baselines[component]
   result,ids=self.review(component,candidate['review'],baseline,'optimization')
   oracle=read(HERE/self.dataset['components'][component]['oracle']);judgment=score(result,oracle)
   value=judgment['correct']/judgment['total']+0.001*(1-min(len(candidate['review']),4000)/4000)
   trace={'component':component,'Generated Outputs':result,'Feedback':judgment,'call_ids':ids}
   # Validation labels never enter reflection; only train outputs are eligible.
   if component in self.dataset['splits']['train']:
    trace['Feedback']={**judgment,'expected_for_errors':{i:oracle[i] for i in judgment['wrong']}}
   outputs.append(trace);scores.append(value);traces.append(trace)
   save(self.out/f'metric-{self.metric_calls:02}.json',{'candidate':candidate,'trace':trace,'score':value})
  return EvaluationBatch(outputs=outputs,scores=scores,trajectories=traces if capture_traces else None)
 def make_reflective_dataset(self,candidate,eval_batch,components_to_update):
  require(all(t['component'] in self.dataset['splits']['train'] for t in eval_batch.trajectories),'reflection must use train only')
  return {'review':eval_batch.trajectories}
 def propose_new_texts(self,candidate,reflective_dataset,components_to_update):
  require(self.proposals<3,'three-proposal cap');self.proposals+=1
  prompt='Improve only the English final-review paragraph for a source-grounded behavioral-claim reviewer. Keep it short and transferable. Preserve ordinary controls, distinct identities, lifecycle order and OPEN policy questions. Use feedback but never embed case IDs, expected labels, component/API names or benchmark-specific answers. Return JSON {"review":"..."}.\nCURRENT:\n'+candidate['review']+'\nTRAIN FEEDBACK:\n'+json.dumps(reflective_dataset)
  def validator(r):
   require(set(r)=={'review'} and isinstance(r['review'],str) and 40<=len(r['review'])<=4000,'bounded review paragraph required')
   require(not any(c['id'] in r['review'] for c in read(HERE/'context-public.json')['cases']),'benchmark IDs in candidate')
  result,ids=self.call(prompt,'reflection','train',validator)
  save(self.out/f'proposal-{self.proposals}.json',{'candidate':result,'call_ids':ids})
  return result
 def run(self):
  fixed=(HERE/'prompts/fixed.md').read_text()
  for c in self.dataset['splits']['train']+self.dataset['splits']['validation']:
   self.baselines[c]=self.baseline(c,'optimization',0)
  selection=optimize_review(self,fixed,self.out/'gepa')
  require(selection['metric_calls']==self.metric_calls,'GEPA/adapter metric count mismatch')
  save(self.out/'selected-prompt.json',{**selection,'input_hashes':self.frozen,'selected_before_final':True})
  self.selection_hash=sha(self.out/'selected-prompt.json')
  paragraph=selection['candidate']['review']
  for ci,component in enumerate(self.dataset['splits']['test']):
   for repeat in range(3):
    baseline=self.baseline(component,'final',repeat)
    arms={'none':(baseline['report'],[])}
    order=['fixed','gepa'] if (ci+repeat)%2==0 else ['gepa','fixed']
    for arm in order:arms[arm]=self.review(component,fixed if arm=='fixed' else paragraph,baseline,'final-'+arm)
    oracle=read(HERE/self.dataset['components'][component]['oracle'])
    for arm,(report,ids) in arms.items():
     quality=score(report,oracle);allids=baseline['call_ids']+ids
     total=baseline['provider_cost']+sum(self.calls[i]['cost']['total_usd_estimate'] for i in allids)
     self.results.append({'component':component,'repeat':repeat,'arm':arm,'review_order':order,'quality':quality,'report':report,
      'baseline_call_ids':baseline['call_ids'],'review_call_ids':ids,'total_usd_estimate':total,
      'review_usd_estimate':sum(self.calls[i]['cost']['total_usd_estimate'] for i in ids),'provider_usd':baseline['provider_cost'],
      'repair_calls':sum(self.calls[i]['repair'] for i in allids),'residual_wrong':quality['wrong']})
    save(self.out/'comparison.json',self.results)
  self.assert_frozen();save(self.out/'status.json',{'status':'complete','metric_calls':self.metric_calls,'proposals':self.proposals,'codex_calls':len(self.calls)})

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);a=p.parse_args()
 experiment=Experiment(a.output.resolve())
 try:experiment.run()
 except Exception as exc:
  save(experiment.out/'status.json',{'status':'blocked','error':str(exc),'codex_calls':len(experiment.calls)})
  raise
if __name__=='__main__':main()
