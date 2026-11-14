#!/usr/bin/env python3
"""Rebuild the pinned component and rerun retained checks without model calls."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[2]
SOURCE_SHA = '04914c200cb38d4ea960ee6a4c314a028c632991'
TOOL_SHA = '9458923'


def run(argv, cwd, logdir, name, env=None):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, timeout=120)
    (logdir / (name + '.stdout')).write_text(result.stdout)
    (logdir / (name + '.stderr')).write_text(result.stderr)
    print(name, result.returncode)
    if result.returncode:
        raise RuntimeError(f'{name} failed; see {logdir}')
    return result.stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='new disposable directory')
    parser.add_argument('--source-repo', default='https://github.com/golang/sync.git')
    args = parser.parse_args()
    root = args.output.resolve()
    root.mkdir()
    repo, pack, logs = root / 'pool', root / 'pack', root / 'logs'
    for folder in (repo, pack, logs):
        folder.mkdir()
    run(['git', 'init', '-q'], repo, logs, 'git-init')
    run(['git', 'fetch', '--depth=1', args.source_repo, SOURCE_SHA], repo, logs, 'git-fetch')
    run(['git', 'checkout', '--detach', 'FETCH_HEAD'], repo, logs, 'git-checkout')
    archive = subprocess.check_output(['git', '-C', str(PACK), 'archive', TOOL_SHA, 'tools', 'formats'])
    subprocess.run(['tar', '-xf', '-'], cwd=pack, input=archive, check=True)
    adir = repo / 'domain-analysis/weightedSemaphore'
    shutil.copytree(HERE / 'analysis', adir)
    probe = adir / '_probe/weighted_pilot_test.go'
    control = adir / '_probe/independent_control_test.go'
    shutil.copy2(HERE / 'controls/control_test.go.txt', control)
    overlay = {'Replace': {str(repo / 'semaphore/weighted_pilot_test.go'): str(probe),
                           str(repo / 'semaphore/independent_control_test.go'): str(control)}}
    (adir / '_probe/overlay.json').write_text(json.dumps(overlay) + '\n')
    env = dict(os.environ, STATERADAR_PACK=str(pack), GOTOOLCHAIN='local')
    base = str(adir)
    commands = {
        'catalogue': ['../pack/tools/pilot_artifacts.py', 'catalogue', base+'/catalogue-fields.json', base+'/event-catalogue.md', '--check'],
        'matrix': [base+'/check_matrix.py'], 'guards': [base+'/check_guards.py'],
        'sidecar': ['../pack/tools/dsc_check.py', base, '--repo', '.', '--model', 'as-is.machine.mmd'],
        'reachability': ['../pack/tools/check_reachability.py', base, '--repo', '.'],
        'blind-coverage': ['../pack/tools/part_b_pack.py', base, '--repo', '.', '--check', base+'/part-b-blind.md'],
        'deliverables': ['../pack/tools/pilot_artifacts.py', 'audit', base, '--repo', '.'],
    }
    for name, command in commands.items():
        run([sys.executable, *command], repo, logs, name, env)
    run(['go', 'test', '-race', '-count=1', '-timeout=60s', './semaphore'], repo, logs, 'upstream-race', env)
    output = run(['go', 'test', '-race', '-count=5', '-timeout=45s', '-v',
                  '-overlay', str(adir/'_probe/overlay.json'), '-run', '^Test(Pilot|Control)', './semaphore'],
                 repo, logs, 'observation-probes', env)
    runs = [line for line in output.splitlines() if line.startswith('=== RUN   Test')]
    if len(runs) != 50:
        raise RuntimeError(f'expected 10 distinct probes x 5 repetitions, observed {len(runs)} executions')
    if len(set(runs)) != 10:
        raise RuntimeError('probe discovery did not cover all ten distinct observations')
    print('REPRODUCTION: 7/7 gates, upstream race suite, 10 observation probes x 5 passed. No domain decisions.')


if __name__ == '__main__':
    main()
