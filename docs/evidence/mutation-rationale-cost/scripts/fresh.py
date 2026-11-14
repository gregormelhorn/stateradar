"""Regenerate in a disposable copy, preserving the measured pilot artifacts."""
import hashlib,json,shutil,subprocess,sys,tempfile
from pathlib import Path
run=Path(sys.argv[1]).resolve()
original=run/'selective/pool'
name='domain-analysis/circuitBreaker'
with tempfile.TemporaryDirectory(prefix='stateradar-cost-audit-') as temp:
    repo=Path(temp)/'pool';shutil.copytree(original,repo,ignore=shutil.ignore_patterns('__pycache__'))
    before=(repo/name/'analysis.json').read_bytes()
    cmd=[sys.executable,str(run/'selective/pack/tools/gen_analysis_sidecar.py'),'--root',str(repo),'--strict','circuitBreaker']
    result=subprocess.run(cmd,capture_output=True,text=True)
    after=(repo/name/'analysis.json').read_bytes()
    unchanged=subprocess.run(['git','diff','--exit-code'],cwd=original,capture_output=True,text=True)
    report={'command':cmd,'exit':result.returncode,'stdout':result.stdout,'stderr':result.stderr,
            'byte_identical':before==after,'before_sha256':hashlib.sha256(before).hexdigest(),
            'after_sha256':hashlib.sha256(after).hexdigest(),'tracked_source_diff_exit':unchanged.returncode,
            'tracked_source_diff':unchanged.stdout+unchanged.stderr}
    print(json.dumps(report,indent=2))
    raise SystemExit(bool(result.returncode or before!=after or unchanged.returncode))
