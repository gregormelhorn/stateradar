"""Retain measured artifacts and command evidence, never credentials or a model retry."""
import hashlib,json,shutil,sys
from pathlib import Path
run=Path(sys.argv[1]);dest=Path(sys.argv[2]);arm=run/'selective'
assert not dest.exists(), 'retention destination must be new'
phase=json.loads((arm/'phase-status.json').read_text())
assert phase['controller']!='running', 'run must have finalized'
dest.mkdir(parents=True)
shutil.copyfile(run/'experiment.json',dest/'experiment.json')
for name in ('usage.json','usage-checkpoint.json','usage-history.jsonl','cost-estimate.json',
             'routing-cost.json','result.json','failure.json','acceptance.json','phase-status.json','final.txt','events.jsonl'):
    p=arm/name
    if p.exists():shutil.copyfile(p,dest/name)
shutil.copytree(arm/'logs',dest/'logs')
shutil.copytree(arm/'pool/domain-analysis',dest/'domain-analysis',ignore=shutil.ignore_patterns('__pycache__'))
hashes={str(p.relative_to(dest)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(dest.rglob('*')) if p.is_file()}
(dest/'retained-hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
print(f'RETAINED: {len(hashes)} artifacts; original run {run}')
