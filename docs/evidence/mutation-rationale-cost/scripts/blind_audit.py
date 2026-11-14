"""Audit one-row-per-situation classification; never author or repair blind text."""
from collections import Counter
import json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'tools'))
from part_b_pack import _catalogue_ids


def rows(text,ids):
    result=[]
    for line in text.splitlines():
        if not line.strip().startswith('|'):continue
        cells=[x.strip().strip('*`').strip() for x in re.split(r'(?<!\\)\|',line.strip())[1:-1]]
        if cells and cells[0] in ids:result.append(cells)
    return result


def audit(expected,classified):
    if not expected:raise ValueError('zero blind situations discovered')
    keys=lambda rs:Counter(tuple(r[:2]) for r in rs)
    if keys(expected)!=keys(classified):raise ValueError('every blind situation needs exactly one classification')
    allowed={'convergent','convergent-hole','divergence','artefact','pass-B-blind-spot'}
    if any(len(r)<5 or r[3] not in allowed for r in classified):raise ValueError('invalid classification')
    if any(r[3]=='divergence' and not re.search(r'Q-\d+',r[4]) for r in classified):raise ValueError('divergence without question')


if __name__=='__main__':
    adir=Path(sys.argv[1])
    events,pairs=_catalogue_ids((adir/'event-catalogue.md').read_text())
    expected=rows((adir/'part-b-blind.md').read_text(),set(events+pairs))
    diff=(adir/'part-b-diff.md').read_text()
    headers=[[x.strip().lower() for x in line.strip().split('|')[1:-1]] for line in diff.splitlines() if line.startswith('|')]
    header=next(h for h in headers if 'class' in h or 'classification' in h)
    position=header.index('class') if 'class' in header else header.index('classification')
    classified=[r[:2]+['',r[position],r[-1]] for r in rows(diff,set(events+pairs))]
    try:audit(expected,classified[1:])
    except ValueError as exc:red=str(exc)
    else:raise AssertionError('dropped classification did not fail')
    audit(expected,classified)
    print(json.dumps({'blind_situations':len(expected),'classified_situations':len(classified),
                      'classes':dict(Counter(r[3] for r in classified)),
                      'red_probe':red,'verdict':'PASS'},indent=2))
