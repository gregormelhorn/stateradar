"""Explicit rationale bindings and source validation, without semantic auto-acceptance."""
from pathlib import Path
import json
import re
from typing import Any

KINDS={'required-behavior','documented-no-action','upstream-guarantee','outside-contract'}


def rationale_errors(data: dict[str,Any], adir: Path, repo: Path | None) -> list[str]:
    errors=[]
    enabled=data.get('rationaleVersion')==1
    for cell in data.get('cells',[]):
        label=f"rationale {cell.get('state')} x {cell.get('event')}"
        reason=cell.get('rationale')
        if reason is None:
            if enabled:errors.append(label+': missing rationale')
            continue
        if not enabled:errors.append(label+': rationaleVersion=1 required')
        if not isinstance(reason,dict) or reason.get('kind') not in KINDS:
            errors.append(label+': invalid kind');continue
        for key in ('claim','scope'):
            if not isinstance(reason.get(key),str) or len(reason[key])<12:
                errors.append(label+': missing explicit '+key)
        evidence=reason.get('evidence')
        if not isinstance(evidence,list) or not evidence:
            errors.append(label+': missing evidence');continue
        kinds={e.get('kind') for e in evidence if isinstance(e,dict)}
        if reason['kind']=='upstream-guarantee' and 'upstream-contract' not in kinds:
            errors.append(label+': upstream guarantee requires a cited callee contract')
        if reason['kind'] in ('outside-contract','documented-no-action') and 'decision' not in kinds:
            errors.append(label+': contract limit/no-action requires an owner decision')
        if reason['kind']=='documented-no-action' and cell.get('disposition')!='ignore (documented)':
            errors.append(label+': no-action rationale contradicts disposition')
        for entry in evidence:
            if not isinstance(entry,dict):errors.append(label+': invalid evidence');continue
            kind=entry.get('kind')
            if kind=='decision':
                dr=entry.get('dr','')
                if not isinstance(dr,str) or not re.fullmatch(r'DR-\d+',dr):
                    errors.append(label+': invalid decision id')
                else:
                    path=adir/'decisions'/f'{dr}.yaml'
                    if not path.is_file() or not re.search(r'^status: accepted\s*$',path.read_text(),re.M):
                        errors.append(label+': decision not present and accepted: '+dr)
            elif kind=='upstream-contract':
                if not isinstance(entry.get('source'),str) or len(entry['source'])<3:
                    errors.append(label+': callee identity required')
            else:errors.append(label+': invalid evidence kind')
            cite=entry.get('citation',{})
            if not isinstance(cite,dict) or not isinstance(cite.get('file'),str) or type(cite.get('line')) is not int or not cite.get('fragment'):
                errors.append(label+': evidence requires file, line and fragment');continue
            if repo is None:
                errors.append(label+': --repo required for evidence verification');continue
            path=repo/cite['file']; line=cite['line'];fragment=cite['fragment']
            if kind=='decision' and path.resolve()!=(adir/'decisions'/f"{entry.get('dr')}.yaml").resolve():
                errors.append(label+': decision citation must reference the named decision')
            if not path.is_file() or line<1:
                errors.append(label+': cited source absent');continue
            lines=path.read_text().splitlines()
            if not isinstance(fragment,str) or not any(fragment in s for s in lines[max(0,line-4):line+3]):
                errors.append(label+': citation fragment not found')
    bindings=adir/'cell-rationale.json'
    if bindings.is_file():
        try:
            entries=read_bindings(bindings,data)
            if not enabled or any(c.get('rationale')!=entries[c['state'],c['event']] for c in data['cells']):
                errors.append('rationale: sidecar differs from explicit rationale bindings')
        except (ValueError,KeyError,TypeError) as exc:errors.append('rationale: '+str(exc))
    return errors


def read_bindings(path: Path, data: Any) -> dict[tuple[str,str],Any]:
    raw=json.loads(path.read_text())
    if raw.get('formatVersion')!=1:raise ValueError('invalid rationale binding version')
    rows=raw.get('cells',[])
    mapped={(c['state'],c['event']):c for c in rows}
    cells={(c['state'],c['event']):c for c in data['cells']}
    if not rows or len(mapped)!=len(rows) or set(mapped)!=set(cells):
        raise ValueError('rationale bindings must cover every cell exactly once')
    for key,row in mapped.items():
        if any(row.get(field)!=cells[key].get(field) for field in ('disposition','target')):
            raise ValueError('rationale binding outcome changed; re-review '+str(key))
        if 'rationale' not in row:raise ValueError('rationale binding missing reason')
    return {key:row['rationale'] for key,row in mapped.items()}
