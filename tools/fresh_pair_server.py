#!/usr/bin/env python3
"""MCP command server for a no-provider direct arm and a normal routed arm."""
import os
import shutil
import sys
from pathlib import Path
import run_sol_pilot as core
import run_flash_pilot as blind_helper
from fresh_pair_gates import allow_blind,route_policy
OUTPUT='domain-analysis/lruCache/part-b-blind.md'

def run(root,arm):
 if arm not in ('direct','routed'):raise ValueError('unknown arm')
 if arm=='direct':
  for name in ('DEEPSEEK_API_KEY','TYPESAFE_API_KEY'):os.environ.pop(name,None)
  original=core.command_result
  def offline_package(root,mode,argv,sequence,python):
   # The generic sandbox only allows the pack tool when key-shaped values
   # exist. These noncredentials are used only for local package/status calls;
   # provider calls are refused by route_policy before this function runs.
   keys=('DEEPSEEK_API_KEY','TYPESAFE_API_KEY');before={k:os.environ.get(k) for k in keys}
   try:
    for k in keys:os.environ[k]='offline-package-only-not-a-credential'
    return original(root,mode,argv,sequence,python)
   finally:
    for k,v in before.items():
     if v is None:os.environ.pop(k,None)
     else:os.environ[k]=v
  def command_result(root,mode,argv,sequence,python):
   isrouting=(len(argv)>=5 and argv[0]=='python3' and (root/'pool'/argv[1]).resolve()==root/'pack/tools/local_models.py')
   if not isrouting:return original(root,mode,argv,sequence,python)
   if argv[2:4]!=['--ledger','../routing.sqlite']:return {'exit_code':2,'stderr':'Use the pilot ledger.'}
   action=route_policy('direct',argv[4],'--package-only' in argv)
   if action=='deny':return {'exit_code':2,'stderr':'Model providers are unavailable in the direct arm.'}
   if action in ('package','status'):return offline_package(root,mode,argv,sequence,python)
   try:allow_blind(argv[4:],OUTPUT)
   except ValueError as exc:return {'exit_code':2,'stderr':str(exc)}
   codex=shutil.which(os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or 'codex')
   if not codex:return {'exit_code':2,'stderr':'Fresh blind Codex unavailable.'}
   blind_helper.OUTPUT=OUTPUT;blind_helper.command_result=offline_package
   return blind_helper.blind_dispatch(root,argv,sequence,python,codex)
  core.command_result=command_result
 core.serve_tools(root,'selective')
if __name__=='__main__':
 if len(sys.argv)!=4 or sys.argv[1]!='--serve-tools':raise SystemExit('usage: fresh_pair_server.py --serve-tools ROOT direct|routed')
 run(Path(sys.argv[2]).resolve(),sys.argv[3])
