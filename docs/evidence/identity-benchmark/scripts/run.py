"""Bounded prompt comparison using the existing isolated, metered pilot transport."""
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
REPO=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(REPO/'tools'))
from run_sol_pilot import prepare, run_checked_arm, execution_env
HERE=Path(__file__).resolve().parents[1]
PACK='f76591e06757a4520f49871e092c6e702861887c'
SOURCE='27b8e2cfc65aacd09abb3968455e4b01df4a83fa'

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output',type=Path)
    parser.add_argument('--source-repo',type=Path,default=Path('/tmp/stateradar-mutation-cost-routed/selective/pool'))
    args=parser.parse_args()
    out=args.output.resolve(); out.mkdir()
    fixture=out/'transfer-source'; fixture.mkdir()
    for name in ('go.mod','component.go','README.md'):
        shutil.copyfile(HERE/'fixtures/transfer'/name,fixture/name)
    for argv in (['git','init','-q'],['git','add','.'],['git','-c','user.name=Fixture','-c','user.email=fixture@localhost','commit','-qm','Freeze transfer input']):
        subprocess.run(argv,cwd=fixture,check=True)
    transfer_sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=fixture,text=True).strip()
    candidate=(HERE/'prompts/candidate.md').read_bytes()
    assert hashlib.sha256(candidate).hexdigest()==(HERE/'results/candidate-freeze.txt').read_text().split()[0], 'candidate changed after freeze'
    pilot=subprocess.check_output(['git','show',PACK+':prompts/02-pilot.md'],cwd=REPO,text=True)
    # Verbatim existing instructions, bounded task replaces deliverables/full-step scope.
    baseline=pilot[pilot.index('### Hard rules'):pilot.index('### Model routing')]
    baseline+='\n'+pilot[pilot.index('For cancellation and teardown'):pilot.index('For each trace give')]
    baseline+='\n'+pilot[pilot.index('### Step 8'):pilot.index('## PART B')]
    baseline_path=HERE/'prompts/baseline-excerpt.md'
    if baseline_path.exists():
        assert baseline_path.read_text()==baseline, 'frozen baseline changed'
    else:
        baseline_path.write_text(baseline)
    for component,variant in [('gobreaker','baseline'),('gobreaker','candidate'),('transfer','candidate'),('transfer','baseline')]:
        name=component+'-'+variant; root=out/name
        src=args.source_repo.resolve() if component=='gobreaker' else fixture
        prepare(root,REPO,PACK,src,SOURCE if component=='gobreaker' else transfer_sha)
        shutil.copyfile(HERE/'scripts/validate_report.py',root/'pool/validate_report.py')
        source='gobreaker.go' if component=='gobreaker' else 'component.go'
        prompt=baseline+'\n'+((HERE/'prompts/candidate.md').read_text() if variant=='candidate' else '')
        prompt+='\n'+(HERE/'prompts/task.md').read_text().replace('SOURCE',source)
        (root/'prompt.md').write_text(prompt)
        manifest={'component':component,'variant':variant,'pack':PACK,'source_sha':SOURCE if component=='gobreaker' else transfer_sha,
                  'model':'gpt-6.1-sol','effort':'medium','output':'selective','timeout':900,
                  'prompt_sha256':hashlib.sha256(prompt.encode()).hexdigest(),
                  'source_sha256':hashlib.sha256((root/'pool'/source).read_bytes()).hexdigest()}
        (root/'experiment.json').write_text(json.dumps(manifest,indent=2)+'\n')
        print('START '+name,flush=True)
        try:
            run_checked_arm(root,'selective',prompt,os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or shutil.which('codex'),
                            REPO/'.venv/bin/python',900,output_name='bounded',smoke=True)
        except Exception as exc:
            print('FAILED '+name+': '+str(exc),flush=True)
        print('END '+name,flush=True)

if __name__=='__main__': main()
