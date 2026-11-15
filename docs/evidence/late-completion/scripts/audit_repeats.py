"""Audit every retained full mutant repetition, not just its aggregate verdict."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
from late_completion import evaluate
fixture=ROOT/'examples/grpc-addrconn/late-completion'
profile=json.loads((fixture/'profile.json').read_text())
mutants=json.loads((fixture/'fault-mutants.json').read_text())['mutants']
runs=Path(sys.argv[1])
for mutant in mutants:
    traces=json.loads((runs/mutant['id']/'observations.json').read_text())
    for repeat in range(5):
        sample=[{**t,'repeat':0} for t in traces if t['repeat']==repeat]
        failures=evaluate(profile,sample,1)
        if mutant['cell'] not in failures:raise SystemExit(f"FAIL: {mutant['id']} repeat {repeat} missed declared scenario")
    print(f"{mutant['id']}: declared scenario fails in 5/5 repetitions")
