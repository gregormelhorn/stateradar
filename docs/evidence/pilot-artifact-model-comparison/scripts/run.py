from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import datetime
import time
ROOT=Path(__file__).resolve().parent
REPO=Path('/Users/gregormelhorn/workspace/domain-statechart')
PYTHON=str(REPO/'.venv/bin/python')
SHA=subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO,text=True).strip()
BASE=Path('/tmp/stateradar-routing-threeway.GBCgIc')
def run(component,variants):
    if component == 'pool':
        while not Path('/tmp/stateradar-controller-4us5gpyo/pool-terra.exit').exists():
            time.sleep(15)
    for variant in variants:
        name=f'{component}-{variant}'
        args=[PYTHON,'tools/run_sol_pilot.py','--component',component,'--component-repo',str(BASE/f'{component}-routed/selective/pool'),'--pack-sha',SHA,'--output',str(ROOT/name),'--routing-variant','routed','--model',f'gpt-6.1-{variant}','--output-mode','selective','--timeout','2700']
        print(datetime.datetime.now().isoformat(), 'START',name,flush=True)
        with (ROOT/f'{name}.log').open('w') as log:
            completed=subprocess.run(args,cwd=REPO,stdout=log,stderr=subprocess.STDOUT)
        (ROOT/f'{name}.exit').write_text(str(completed.returncode)+'\n')
        print(datetime.datetime.now().isoformat(),'END',name,completed.returncode,flush=True)
with ThreadPoolExecutor(max_workers=2) as executor:
    futures=[executor.submit(run,'pool',('sol','terra')),executor.submit(run,'gobreaker',('terra','sol'))]
    for future in futures: future.result()
