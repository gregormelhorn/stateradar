#!/usr/bin/env python3
"""Meter a neutral direct-arm MCP smoke without inspecting component source."""
import hashlib,json,os,shutil,sys
from pathlib import Path
import run_sol_pilot as core
from pilot_accounting import cost_report
from fresh_pair_smoke_check import verify
ROOT=Path(__file__).resolve().parents[1];EVIDENCE=ROOT/'docs/evidence/routing-fresh-pair';PAIR=Path('/tmp/stateradar-lru-pair-preflight').resolve();OUT=PAIR/'direct';SERVER=ROOT/'tools/fresh_pair_server.py'
codex=shutil.which(os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or 'codex')
if not codex:raise SystemExit('BLOCKED(smoke): Codex CLI missing')
task='Use the pilot command tool to read go.mod and report the module name. Then call the pilot command tool with ["python3","../pack/tools/local_models.py","--ledger","../routing.sqlite","jev","go.mod","Does this name a Go module?","--model","jev-1.14.0"] and report its exit status. Do not make other model calls.'
if '--audit' not in sys.argv:core.run_arm(OUT,'direct',task,codex,Path(sys.executable).absolute(),180,replay_server=SERVER)
final=(OUT/'final.txt').read_text();events=[json.loads(line) for line in (OUT/'events.jsonl').read_text().splitlines()]
verify(final,events)
report=cost_report(json.loads((OUT/'usage-checkpoint.json').read_text()),{'charged_microdollars':0,'reserved_microdollars':0},'gpt-6.1-sol')
if not report['complete']:raise ValueError('unknown smoke cost')
core.save(EVIDENCE/'preflight-model-smoke.json',{'complete':True,'cost':report,'usage':json.loads((OUT/'usage.json').read_text()),'server_sha256':hashlib.sha256(SERVER.read_bytes()).hexdigest(),'task':task,'result':final,'note':'Direct MCP smoke only; no provider model call.'})
print('MODEL PREFLIGHT: source read; direct provider denied; cost',report['total_usd_estimate'])
