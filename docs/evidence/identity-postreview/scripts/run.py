"""Matched metered final reviews of immutable baseline findings and probes."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'tools'))
from run_sol_pilot import prepare, run_checked_arm
HERE = Path(__file__).resolve().parents[1]
PRIOR = HERE.parent / 'identity-benchmark'
PACK = 'f76591e06757a4520f49871e092c6e702861887c'
SOURCE = '27b8e2cfc65aacd09abb3968455e4b01df4a83fa'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def setup(out, source_repo):
    out.mkdir()
    fixture = out / 'transfer-source'
    fixture.mkdir()
    for name in ('go.mod', 'component.go', 'README.md'):
        shutil.copyfile(PRIOR / 'fixtures/transfer' / name, fixture / name)
    for command in (['git', 'init', '-q'], ['git', 'add', '.'],
                    ['git', '-c', 'user.name=Fixture', '-c', 'user.email=fixture@localhost', 'commit', '-qm', 'Freeze unchanged transfer input']):
        subprocess.run(command, cwd=fixture, check=True)
    transfer_sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=fixture, text=True).strip()
    frozen = json.loads((HERE / 'freeze.json').read_text())
    for name, expected in frozen.items():
        assert sha(ROOT / name) == expected, 'frozen experiment changed: ' + name
    for component in ('gobreaker', 'transfer'):
        old = PRIOR / 'runs' / (component + '-baseline')
        for variant in ('generic', 'identity'):
            run = out / (component + '-' + variant)
            source = 'gobreaker.go' if component == 'gobreaker' else 'component.go'
            source_sha = SOURCE if component == 'gobreaker' else transfer_sha
            prepare(run, ROOT, PACK, source_repo if component == 'gobreaker' else fixture, source_sha)
            pool = run / 'pool'
            assert sha(pool / source) == sha(old / 'input' / source)
            (pool / 'analysis').mkdir()
            (pool / 'baseline').mkdir()
            shutil.copyfile(old / 'analysis/final.json', pool / 'analysis/initial.json')
            for name in ('open-questions.md', 'review.md', 'summary.md'):
                shutil.copyfile(old / 'analysis' / name, pool / 'baseline' / name)
            shutil.copytree(old / 'analysis/_probe', pool / 'analysis/_probe')
            original_overlays = [json.loads(p.read_text())['Replace'] for p in (old / 'analysis').glob('overlay*.json')]
            original = max(original_overlays, key=len)
            assert all(x.items() <= original.items() for x in original_overlays)
            overlay = {Path(k).name: 'analysis/_probe/' + Path(v).name for k, v in original.items()}
            (pool / 'analysis/overlay.json').write_text(json.dumps({'Replace': overlay}, indent=2) + '\n')
            shutil.copyfile(PRIOR / 'scripts/validate_report.py', pool / 'validate_report.py')
            shutil.copyfile(HERE / 'scripts/validate_postreview.py', pool / 'validate_postreview.py')
            shutil.copyfile(ROOT / 'tools/finding_preservation.py', pool / 'finding_preservation.py')
            immutable = {str(p.relative_to(pool)): sha(p) for p in sorted(pool.rglob('*')) if p.is_file() and '.git' not in p.parts}
            (pool / 'immutable.json').write_text(json.dumps(immutable, indent=2) + '\n')
            requirement = ('For this transfer source, add TestIdentityCallerVariableRebinding. Obtain F\'s saved callback using a local *Port variable, then reassign ONLY that caller variable to a distinct Port and Account before invoking the saved callback. Do not substitute mutation of the original Port.Target for this operation. Keep an alias to the original Port and observe the old/new accounts and unchanged original Port through the public fields before and after delivery. Derive expected effects from source; keep intent open. Bind the test to the relevant preserved or additional finding in supplement.json.'
                           if component == 'transfer' else 'Probe material additional findings through the public API; preserve all existing probes.')
            prompt = (HERE / 'prompts/task.md').read_text().replace('SOURCE', source).replace('DIRECT_REBIND_REQUIREMENT', requirement)
            if variant == 'identity':
                prompt += '\n' + (HERE / 'prompts/identity.md').read_text()
            (run / 'prompt.md').write_text(prompt)
            settings = {'component': component, 'variant': variant, 'pack': PACK, 'source_sha': source_sha,
                        'source_sha256': sha(pool / source), 'baseline_sha256': sha(pool / 'analysis/initial.json'),
                        'immutable_sha256': sha(pool / 'immutable.json'), 'prompt_sha256': sha(run / 'prompt.md'),
                        'model': 'gpt-6.1-sol', 'effort': 'medium', 'output': 'selective', 'timeout': 900}
            (run / 'experiment.json').write_text(json.dumps(settings, indent=2) + '\n')
        a, b = [out / (component + '-' + v) for v in ('generic', 'identity')]
        assert (a / 'pool/immutable.json').read_bytes() == (b / 'pool/immutable.json').read_bytes()
        assert (b / 'prompt.md').read_text() == (a / 'prompt.md').read_text() + '\n' + (HERE / 'prompts/identity.md').read_text()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--source-repo', type=Path, default=Path('/tmp/stateradar-mutation-cost-routed/selective/pool'))
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--execute-prepared', action='store_true')
    args = parser.parse_args()
    out = args.output.resolve()
    if not args.execute_prepared:
        setup(out, args.source_repo.resolve())
    if args.prepare_only:
        return
    for name in ('gobreaker-generic', 'gobreaker-identity', 'transfer-identity', 'transfer-generic'):
        run = out / name
        assert not (run / 'events.jsonl').exists(), 'refuse to overwrite a measured session'
        print('START ' + name, flush=True)
        try:
            run_checked_arm(run, 'selective', (run / 'prompt.md').read_text(),
                            os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or shutil.which('codex'),
                            ROOT / '.venv/bin/python', 900, output_name='postreview', smoke=True)
        except Exception as exc:
            print('FAILED ' + name + ': ' + str(exc), flush=True)
        print('END ' + name, flush=True)


if __name__ == '__main__':
    main()
