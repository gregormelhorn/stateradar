#!/usr/bin/env python3
"""Run two isolated full pilots with measured provider/controller costs."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
import run_sol_pilot as core
from fresh_pair_gates import enforce_cap,live_budget
from local_budget import Budget
from pilot_accounting import UsageCheckpoint,cost_report
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/evidence/routing-fresh-pair'
SOURCE_SHA='2bb29091a6c341aba625d23fea354c4fbaef5d6f'
PACK_SHA='6c87676f5e1289a42211c58d20daaceae111670a'
MODEL='gpt-6.1-sol';OUTPUT='lruCache';CAP=5.0;TIMEOUT=1200
core.COMPONENTS['fresh-lru']=(SOURCE_SHA,'github.com/hashicorp/golang-lru/v2',OUTPUT,'one Cache instance in lru.go and its simplelru/internal callees','lru_test.go')

def source_clean(root):
 p=subprocess.run(['git','status','--porcelain','--untracked-files=all'],cwd=root/'pool',capture_output=True,text=True,check=True)
 unexpected=[x for x in p.stdout.splitlines() if not (x.startswith('?? domain-analysis/') or x.startswith('?? _probe/'))]
 return unexpected

def pilot_env_vars(arm):
 if arm not in ('direct','routed'):raise ValueError('unknown arm')
 return ['CODEX_APP_RUNTIME_CLI_PATH']+(['DEEPSEEK_API_KEY','TYPESAFE_API_KEY'] if arm=='routed' else [])

def blind_cost(root,final=False):
 directory=root/'blind-output'
 if not directory.exists():return 0.0,True
 events=sorted(directory.glob('*.jsonl'));total=0.0;complete=True
 for p in events:
  usagefile=p.with_suffix('.usage.json')
  if not usagefile.is_file():
   complete=False
   if not final:
    for line in p.read_text().splitlines():
     try:event=json.loads(line)
     except json.JSONDecodeError:continue
     if event.get('type') in ('turn.failed','error'):
      raise ValueError('blind failed with unknown usage')
   continue
  usage=json.loads(usagefile.read_text());report=cost_report({'usage':usage,'complete':True},{'charged_microdollars':0,'reserved_microdollars':0},MODEL)
  if not report['complete']:complete=False
  else:total+=report['total_usd_estimate']
 return total,complete if final else True

def prompt(pack,arm):
 b=core.brief(pack,'fresh-lru','routed' if arm=='routed' else 'agent-only')
 if arm=='direct':
  b=b.replace('- Model routing is configured through the pilot command tool. Credentials are\n  provided only when it runs python3 ../pack/tools/local_models.py with the\n  pilot ledger. Generic environment inspection cannot check routing access.\n  Attempt the prescribed routing calls and report actual provider failures.', '- This direct comparison arm has no configured model-provider credentials.\n  Follow the prompt path for routing not configured. The tool dispatches\n  Part B to a separate isolated Codex session. Build and inspect the blind\n  package with --package-only, then run the blind command with --output last.\n  Never write or repair the blind table yourself.')
 return b+'\n- Compare nothing to external benchmarks. Work only from this checkout and the full pilot prompt. Retain every failed check and open question.\n'

def run_arm(root,arm,prior,python,codex,server):
 (root/'logs').mkdir(exist_ok=True);events=root/'events.jsonl';checkpoint=UsageCheckpoint(root);usage=None;start=time.monotonic();error=None
 args=[codex,'-a','never','exec','--ignore-user-config','--disable','shell_tool','--disable','unified_exec','-c','forced_login_method="chatgpt"','-c','model_reasoning_effort="medium"','-c','web_search="disabled"','-c',f'mcp_servers.pilot.command={json.dumps(str(python))}','-c',f'mcp_servers.pilot.args={json.dumps([str(server),"--serve-tools",str(root),arm])}','-c','mcp_servers.pilot.required=true','-c','mcp_servers.pilot.tool_timeout_sec=300','-c','mcp_servers.pilot.tools.command.approval_mode="approve"','-c','mcp_servers.pilot.tools.command.output_token_limit=60000']
 args+=['-c','mcp_servers.pilot.env_vars='+json.dumps(pilot_env_vars(arm))]
 args+=['--model',MODEL,'--json','--sandbox','workspace-write','-C',str(root/'pool'),'-o',str(root/'final.txt'),'-']
 ledger=Budget(root/'routing.sqlite');core.save(root/'phase-status.json',{'controller':'running','artifact_gates':'pending','complete':False})
 try:
  with events.open('w') as stdout,(root/'codex.stderr').open('w') as stderr:
   with subprocess.Popen(args,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,env=core.codex_environment(),start_new_session=True) as proc:
    try:
     proc.stdin.write(prompt(root/'pack',arm));proc.stdin.close()
     while proc.poll() is None:
      checkpoint.poll();elapsed=time.monotonic()-start
      calls=ledger.calls();blind,_=blind_cost(root)
      live_budget(prior,checkpoint.usage,calls,blind,elapsed,CAP)
      if elapsed>TIMEOUT:raise TimeoutError(f'{TIMEOUT}s pilot cap')
      time.sleep(.3)
    finally:core.stop_controller(proc)
  if proc.returncode:raise ValueError(f'controller exited {proc.returncode}')
  usage=core.read_usage(events);core.save(root/'usage.json',usage)
 except Exception as exc:
  error=str(exc);core.save(root/'failure.json',{'error':error,'elapsed_seconds':round(time.monotonic()-start,3)})
 finally:checkpoint.finish(usage)
 calls=ledger.calls();settled=sum(x['amount_microdollars'] for x in calls if x['status']=='settled');reserved=sum(x['amount_microdollars'] for x in calls if x['status']=='reserved')
 core.save(root/'routing-cost.json',{'calls':calls,'charged_microdollars':settled,'reserved_microdollars':reserved})
 report=cost_report(json.loads((root/'usage-checkpoint.json').read_text()),{'charged_microdollars':settled,'reserved_microdollars':reserved},MODEL);blind,blind_complete=blind_cost(root,True)
 report.update({'blind_usd_equivalent':blind,'blind_complete':blind_complete,'elapsed_seconds':round(time.monotonic()-start,3),'total_with_blind':round(report['total_usd_estimate']+blind,9) if report['complete'] and blind_complete else None})
 core.save(root/'cost-estimate.json',report)
 unexpected=source_clean(root);core.save(root/'source-status.json',{'unexpected':unexpected})
 gates=False
 try:gates=core.verify_artifacts(root,python,OUTPUT,catalogue=True)
 except Exception as exc:core.save(root/'acceptance-error.json',{'error':str(exc)})
 completed=error is None and report['total_with_blind'] is not None and gates and not unexpected
 core.save(root/'phase-status.json',{'controller':'completed' if error is None else 'failed','error':error,'artifact_gates':'passed' if gates else 'failed','source_clean':not unexpected,'complete':completed})
 return report,completed

def main(out,prepare_only=False):
 out=Path(out).resolve()
 if not out.is_relative_to('/private/tmp') or out==Path('/private/tmp'):raise ValueError('output must be new directory under /tmp')
 if sys.platform!='darwin':raise ValueError('requires macOS sandbox')
 python=Path(sys.executable).absolute();codex=shutil.which(os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or 'codex')
 if not codex or not all(os.environ.get(k) for k in ('DEEPSEEK_API_KEY','TYPESAFE_API_KEY')):raise ValueError('missing pilot tools or configured providers')
 freeze=json.loads((EVIDENCE/'reference/freeze.json').read_text());smoke=json.loads((EVIDENCE/'preflight-model-smoke.json').read_text())
 if not smoke.get('complete') or not smoke.get('cost',{}).get('complete'):raise ValueError('unknown preflight smoke cost')
 expected_smoke=cost_report(json.loads((EVIDENCE/'model-preflight/usage-checkpoint.json').read_text()),{'charged_microdollars':0,'reserved_microdollars':0},MODEL)
 if expected_smoke!=smoke['cost']:raise ValueError('smoke cost disagrees with checkpoint')
 if hashlib.sha256((ROOT/'tools/fresh_pair_server.py').read_bytes()).hexdigest()!=smoke['server_sha256']:raise ValueError('server differs from model preflight')
 prior=freeze['reference_cost_usd_equivalent']+smoke['cost']['total_usd_estimate'];enforce_cap(prior,CAP)
 for name,digest in freeze['files'].items():
  if hashlib.sha256((EVIDENCE/name).read_bytes()).hexdigest()!=digest:raise ValueError('reference changed: '+name)
 server=ROOT/'tools/fresh_pair_server.py';guard=ROOT/'tools/fresh_pair_gates.py';out.mkdir()
 core.save(out/'experiment.json',{'pack_sha':PACK_SHA,'component_sha':SOURCE_SHA,'reserve_component_sha':'f167a9d53145b661d05ac28b5702b6f29ea9c502','arm_order':['direct','routed'],'model':MODEL,'timeout_seconds':TIMEOUT,'soft_cap_usd_equivalent':CAP,'reference_cost_usd_equivalent':freeze['reference_cost_usd_equivalent'],'preflight_smoke_cost_usd_equivalent':smoke['cost']['total_usd_estimate'],'preflight_smoke_sha256':hashlib.sha256((EVIDENCE/'preflight-model-smoke.json').read_bytes()).hexdigest(),'reference_freeze_sha256':hashlib.sha256((EVIDENCE/'reference/freeze.json').read_bytes()).hexdigest(),'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'server_sha256':hashlib.sha256(server.read_bytes()).hexdigest(),'guard_sha256':hashlib.sha256(guard.read_bytes()).hexdigest()})
 for arm in ('direct','routed'):
  core.prepare(out/arm,ROOT,PACK_SHA,Path('/tmp/stateradar-lru-benchmark'),SOURCE_SHA);Budget(out/arm/'routing.sqlite',2_000_000)
  status,_,err=core.execute(out/arm,['python3','-c','import jsonschema,z3'],0,python)
  if status:raise ValueError('isolated dependency check: '+err)
  status,_,_=core.execute(out/arm,['cat',str(out/'experiment.json')],0,python)
  if status==0:raise ValueError('sandbox exposes parent experiment')
  status,_,_=core.execute(out/arm,['cat',str(EVIDENCE/'reference/cases.json')],0,python)
  if status==0:raise ValueError('sandbox exposes hidden reference')
 if prepare_only:
  core.save(out/'status.json',{'status':'prepared','note':'No model calls'});print('PREFLIGHT: isolated checkouts and hidden reference OK');return 0
 for arm in ('direct','routed'):

  for p,want in ((Path(__file__),json.loads((out/'experiment.json').read_text())['runner_sha256']),(server,json.loads((out/'experiment.json').read_text())['server_sha256']),(guard,json.loads((out/'experiment.json').read_text())['guard_sha256'])):
   if hashlib.sha256(p.read_bytes()).hexdigest()!=want:raise ValueError('runner changed before arm')
  enforce_cap(prior,CAP);print('START',arm,flush=True);report,complete=run_arm(out/arm,arm,prior,python,codex,server);print('END',arm,'complete',complete,'cost',report['total_with_blind'],flush=True)
  if report['total_with_blind'] is None:core.save(out/'status.json',{'status':'BLOCKED','arm':arm,'reason':'unknown or unsettled model cost'});return 1
  prior+=report['total_with_blind']
  if prior>=CAP:core.save(out/'status.json',{'status':'BLOCKED','arm':arm,'reason':'budget reached','known_total':prior});return 1
 core.save(out/'status.json',{'status':'complete-pair','known_total_usd_equivalent':prior,'note':'Arm completion depends on phase-status; no automatic quality claim.'});return 0
if __name__=='__main__':
 try:raise SystemExit(main(sys.argv[1],len(sys.argv)>2 and sys.argv[2]=='--prepare-only'))
 except Exception as exc:
  print('BLOCKED(fresh-pair):',exc,file=sys.stderr);raise
