"""Audit attributed discovery assessments; never infer semantic truth from text."""
from collections import Counter

class EvalError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise EvalError(message)

def audit(report, source, cases, review):
    findings = report.get('findings')
    require(isinstance(findings, list), 'findings list required')
    ids = [f.get('id') for f in findings]
    require(all(isinstance(i, str) and i for i in ids) and len(ids) == len(set(ids)), 'distinct finding IDs required')
    lines = source.splitlines()
    for f in findings:
        c = f.get('citation', {})
        line, fragment = c.get('line'), c.get('fragment')
        require(isinstance(f.get('text'), str) and f['text'].strip(), 'finding text required')
        require(isinstance(f.get('question'), str), 'question field required')
        require(type(line) is int and 1 <= line <= len(lines) and isinstance(fragment, str) and len(fragment.strip()) >= 4 and fragment in lines[line-1], 'citation does not match source')
    require(isinstance(review.get('reviewer'), str) and review['reviewer'].strip(), 'review attribution required')
    case_ids = [c['id'] for c in cases]
    rows = review.get('cases', [])
    reviewed = review.get('findings', [])
    require(case_ids and len(case_ids) == len(set(case_ids)) and Counter(r.get('id') for r in rows) == Counter(case_ids), 'exact distinct case review required')
    require(Counter(r.get('id') for r in reviewed) == Counter(ids), 'every finding must be reviewed exactly once')
    by_id = {f['id']: f for f in findings}
    verdict = {}
    for r in reviewed:
        require(r.get('verdict') in ('valid','false','uncertain') and isinstance(r.get('reason'),str) and r['reason'].strip(), 'review verdict and reason required')
        verdict[r['id']] = r['verdict']
    case_map = {c['id']: c for c in cases}
    for row in rows:
        targets = row.get('finding_ids')
        require(isinstance(targets,list) and len(targets)==len(set(targets)) and all(t in by_id for t in targets), 'unknown or duplicate finding reference')
        require(isinstance(row.get('reason'),str) and row['reason'].strip(), 'case rationale required')
        require(all(verdict[t]=='valid' for t in targets), 'only valid findings can receive case credit')
        if targets and case_map[row['id']].get('question_required'):
            require(any(by_id[t]['question'].startswith('OPEN:') and len(by_id[t]['question'])>5 for t in targets), 'open policy question required')
    return {'found':sum(bool(r['finding_ids']) for r in rows), 'total':len(case_ids), 'false':sum(x=='false' for x in verdict.values()), 'uncertain':sum(x=='uncertain' for x in verdict.values()), 'missing':[r['id'] for r in rows if not r['finding_ids']], 'limitation':'Semantic classifications are attributed reviewer judgments, not proof of entailment.'}

def check_phase(dataset, component, phase, selected):
    groups = [dataset.get(k) for k in ('train','validation','test')]
    require(all(isinstance(g,list) and g for g in groups), 'three nonempty splits required')
    names = [n for group in groups for n in group]
    require(len(names) == len(set(names)), 'component appears in multiple splits')
    require(phase in ('optimization','final'), 'unknown phase')
    if phase == 'optimization':
        require(component in dataset['train'] + dataset['validation'] and not selected, 'optimization cannot access final')
    else:
        require(selected and component in dataset['test'], 'final requires frozen selection and held-out component')
