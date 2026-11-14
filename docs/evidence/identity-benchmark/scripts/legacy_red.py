"""Falsify the archived unqualified binding claim with public observations."""
import json,subprocess,tempfile,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
source=Path(sys.argv[1]).resolve()
with tempfile.TemporaryDirectory(prefix='identity-legacy-red-') as tmp:
    repo=Path(tmp).resolve()
    packed=subprocess.check_output(['git','archive','27b8e2cfc65aacd09abb3968455e4b01df4a83fa'],cwd=source)
    subprocess.run(['tar','-xf','-'],cwd=repo,input=packed,check=True)
    shutil.copyfile(HERE/'fixtures/legacy_claim_test.go.txt',repo/'legacy_claim_test.go')
    proc=subprocess.run(['go','test','-race','-count=3','-timeout=30s','-json','-run','^TestArchivedOriginalBindingClaim$','.'],cwd=repo,text=True,capture_output=True,timeout=90)
    (HERE/'results/legacy-claim-red.jsonl').write_text(proc.stdout)
    (HERE/'results/legacy-claim-red.stderr').write_text(proc.stderr)
    records=[json.loads(s) for s in proc.stdout.splitlines() if s.startswith('{')]
    for action in ('run','fail'):
        assert sum(r.get('Action')==action and r.get('Test')=='TestArchivedOriginalBindingClaim' for r in records)==3
    assert proc.returncode==1 and proc.stdout.count('archived original-binding claim refuted: replacement counts=')==3
    print('EXPECTED RED: archived original-binding claim refuted in 3/3 race runs; Requests=0, TotalSuccesses=1')
