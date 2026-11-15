"""Execute public-seam controls independently of model reports."""
import json,hashlib,subprocess,tempfile,shutil
from pathlib import Path
from collections import Counter
HERE=Path(__file__).resolve().parents[1]

def run(output):
    pins=json.loads((HERE/'upstream-pins.json').read_text())
    for name,expected in pins['files'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
    goroot=Path(subprocess.check_output(['go','env','GOROOT'],text=True).strip())
    assert subprocess.check_output(['go','version'],text=True).split()[2]==pins['goVersion']
    for component,source in [('context','context/context.go'),('timer','time/sleep.go'),('once','sync/oncefunc.go')]:
        assert (goroot/'src'/source).read_bytes()==(HERE/'upstream'/component/Path(source).name).read_bytes()
    with tempfile.TemporaryDirectory(prefix='gepa-reference-') as td:
        root=Path(td);(root/'singleflight').mkdir()
        shutil.copyfile(HERE/'upstream/singleflight/singleflight.go',root/'singleflight/singleflight.go')
        shutil.copyfile(HERE/'reference/reference_test.go',root/'reference_test.go')
        (root/'go.mod').write_text('module reference.local\n\ngo 1.24\n')
        proc=subprocess.run(['go','test','-race','-count=5','-timeout=30s','-json','.'],cwd=root,text=True,capture_output=True,timeout=90)
        output.write_text(proc.stdout+proc.stderr)
        events=[json.loads(l) for l in proc.stdout.splitlines() if l.startswith('{')]
        expected=Counter({s:5 for s in ['TestReference']+['TestReference/'+c for c in ('context','singleflight','timer','once')]})
        for action in ('run','pass'):
            assert Counter(e['Test'] for e in events if e.get('Action')==action and 'Test'in e)==expected
        assert proc.returncode==0 and not any(e.get('Action') in ('skip','fail') for e in events)
        assert sum(e.get('Action')=='pass' and 'Test'not in e for e in events)==1
    print('REFERENCE PASS: 4 components x 5 repetitions; exact discovery; race detector; pinned source')
if __name__=='__main__':run(HERE/'reference-output.jsonl')
