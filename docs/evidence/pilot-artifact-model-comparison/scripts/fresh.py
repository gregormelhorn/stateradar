import hashlib,json,sys
from pathlib import Path
REPO=Path('/Users/gregormelhorn/workspace/domain-statechart')
sys.path.insert(0,str(REPO/'tools'))
from run_sol_pilot import execute,verify_artifacts
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
out=REPO/'docs/evidence/pilot-artifact-model-comparison/fresh-regeneration.json'
results=json.loads(out.read_text()) if out.exists() else {}
for component,name in [('pool','channelPool'),('gobreaker','circuitBreaker')]:
 key=f'{component}-sol'
 if key in results or not (ROOT/f'{key}.exit').exists():continue
 arm=(ROOT/key/'selective').resolve()
 sidecar=arm/'pool/domain-analysis'/name/'analysis.json'
 if not sidecar.exists():continue
 before=hashlib.sha256(sidecar.read_bytes()).hexdigest()
 code,stdout,stderr=execute(arm,['python3','../pack/tools/gen_analysis_sidecar.py',f'domain-analysis/{name}','--strict'],0,REPO/'.venv/bin/python')
 after=hashlib.sha256(sidecar.read_bytes()).hexdigest()
 passed=verify_artifacts(arm,REPO/'.venv/bin/python',name,catalogue=True)
 results[key]={'strict_regeneration_exit':code,'stdout':stdout,'stderr':stderr,
               'sidecar_unchanged':before==after,'sha256':after,'six_postflight_gates_pass':passed}
 assert code==0 and before==after and passed,results[key]
out.write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results,indent=2))
