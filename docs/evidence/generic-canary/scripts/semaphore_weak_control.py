"""Execute the generic runner with the real semaphore's deliberately weak suite."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
from check_fault_mutants import copy_component

with tempfile.TemporaryDirectory(prefix='generic-canary-weak-') as td:
    component=copy_component(ROOT/'examples/weighted-semaphore',Path(td).resolve(),'semaphore')
    analysis=component/'domain-analysis/weightedSemaphore'
    config_path=analysis/'fault-mutants.json';config=json.loads(config_path.read_text())
    ids={'omit-cancel-unlink','zero-charges'}
    config['mutants']=[m for m in config['mutants'] if m['id'] in ids]
    config['expectedCells']=1
    config['testCommand']=[sys.executable,'weak_runner.py','{analysis_dir}']
    config_path.write_text(json.dumps(config))
    binding_path=analysis/'mutant-generation.json';bindings=json.loads(binding_path.read_text())
    bindings['bindings']=[b for b in bindings['bindings'] if b['id'] in ids]
    binding_path.write_text(json.dumps(bindings))
    (component/'weak_runner.py').write_text(
        'from pathlib import Path\nimport sys\n'+
        f'sys.path.insert(0,{str(ROOT/"tools")!r})\n'+
        'from semaphore_f09 import weak_command\n'+
        'r=weak_command(Path.cwd())\nprint(r.output)\nraise SystemExit(r.returncode)\n')
    run=subprocess.run([sys.executable,str(ROOT/'tools/check_fault_mutants.py'),str(analysis)],
                       capture_output=True,text=True,timeout=120)
    print(run.stdout,end='');print(run.stderr,end='')
    if (run.returncode!=1 or 'killed=0 survived=1 errors=0 blocked=1' not in run.stdout or
            'canary=zero-charges verdict=SURVIVED; not executed' not in run.stdout):
        raise SystemExit('BLOCKED: generic semaphore weak control did not match')
print('EXPECTED GENERIC CONTROL: unobservable capacity blocks F-09 without execution')
