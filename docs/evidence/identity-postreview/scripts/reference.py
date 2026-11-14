"""Standalone exact caller-variable schedule; never supplies answers to models."""
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='caller-rebind-reference-') as tmp:
    root = Path(tmp)
    for name in ('go.mod', 'component.go'):
        shutil.copyfile(HERE.parent / 'identity-benchmark/fixtures/transfer' / name, root / name)
    shutil.copyfile(HERE / 'fixtures/caller_rebinding_test.go.txt', root / 'caller_test.go')
    result = subprocess.run(['go', 'test', '-race', '-count=5', '-timeout=30s', '-json',
                             '-run', '^TestIdentityCallerVariableRebinding$', '.'],
                            cwd=root, capture_output=True, text=True, timeout=120)
    (HERE / 'results/caller-reference.jsonl').write_text(result.stdout)
    (HERE / 'results/caller-reference.stderr').write_text(result.stderr)
    records = [json.loads(s) for s in result.stdout.splitlines()]
    for action in ('run', 'pass'):
        assert sum(r.get('Action') == action and r.get('Test') == 'TestIdentityCallerVariableRebinding' for r in records) == 5
    assert result.returncode == 0
    print('CALLER REBINDING REFERENCE: 5/5 race repetitions pass; local pointer reassigned, original Port unchanged, both accounts checked.')
