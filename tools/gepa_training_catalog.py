"""Validate attributed training case anchors; do not infer semantic truth."""
import hashlib
from pathlib import Path
from gepa_discovery_eval import require

KINDS = {'historical_miss', 'historical_false_claim', 'positive_control', 'negative_control'}

def safe_file(root, name):
    require(isinstance(name,str) and name, 'file path required')
    rel=Path(name)
    require(not rel.is_absolute() and '..' not in rel.parts, 'repository-relative path required')
    path=(root/rel).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), 'missing or outside repository')
    return path

def validate_catalog(catalog, root, expected_ids=None):
    root=Path(root)
    components=catalog.get('components')
    require(isinstance(components,dict) and components, 'nonempty component map required')
    ids=[]
    for component in components.values():
        safe_file(root,component.get('source'))
        cases=component.get('cases')
        require(isinstance(cases,list) and cases, 'nonempty cases required')
        for case in cases:
            cid=case.get('id'); require(isinstance(cid,str) and cid, 'case id required'); ids.append(cid)
            require(case.get('kind') in KINDS, 'unknown case kind')
            require(type(case.get('question_required')) is bool, 'boolean question marker required')
            require(all(isinstance(case.get(k),str) and case[k].strip() for k in ('situation','expected','historical')), 'case context and historical classification required')
            evidence=case.get('evidence');require(isinstance(evidence,list) and evidence, 'source evidence required')
            for anchor in evidence:
                path=safe_file(root,anchor.get('file')); raw=path.read_bytes()
                require(hashlib.sha256(raw).hexdigest()==anchor.get('sha256'), 'anchor hash mismatch')
                lines=raw.decode().splitlines(); line=anchor.get('line'); fragment=anchor.get('fragment')
                require(type(line)is int and 1<=line<=len(lines) and isinstance(fragment,str) and len(fragment.strip())>=4 and fragment in lines[line-1], 'anchor fragment mismatch')
    require(len(ids)==len(set(ids)), 'duplicate case IDs')
    if expected_ids is not None:
        require(set(ids)==set(expected_ids), 'case inventory missing or extra')
    return len(ids)

def build_prompt(source, fixed, task):
    numbered='\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1))
    return task+'\nREVIEW PARAGRAPH:\n'+fixed+'\nSOURCE:\n'+numbered

def validate_independent_review(catalog, review):
    from collections import Counter
    require(isinstance(review.get('reviewer'),str) and review['reviewer'].strip(), 'reviewer attribution required')
    rows=review.get('cases')
    require(isinstance(rows,list), 'review case list required')
    ids=[c['id'] for component in catalog['components'].values() for c in component['cases']]
    require(Counter(r.get('id') for r in rows)==Counter(ids), 'every catalog case needs exactly one review')
    require(all(r.get('verdict')=='accepted' and isinstance(r.get('reason'),str) and r['reason'].strip() for r in rows), 'all cases need attributed acceptance and reasons')
