"""Strict structured-claim evaluator. Prose entailment remains outside this checker."""
from collections import Counter

class EvalError(ValueError):pass

def require(value,message):
 if not value:raise EvalError(message)

def validate(report,public,source,baseline=None):
 require(isinstance(report,dict),'report object required')
 rows=report.get('findings');require(isinstance(rows,list),'finding list required')
 expected=[c['id'] for c in public['cases']]
 require(expected and len(set(expected))==len(expected),'empty/duplicate inventory')
 require(all(isinstance(r,dict) for r in rows),'finding objects required')
 require(Counter(r.get('id') for r in rows)==Counter(expected),'exact finding inventory required')
 lines=source.splitlines()
 for r in rows:
  require(r.get('verdict') in ('supported','contradicted','unspecified'),'invalid verdict')
  line=r.get('line');fragment=r.get('fragment')
  require(type(line)is int and 1<=line<=len(lines) and isinstance(fragment,str) and len(fragment.strip())>=4 and fragment in lines[line-1],'invalid source citation')
  require(isinstance(r.get('reason'),str) and r['reason'].strip(),'reason required')
  require(isinstance(r.get('question'),str),'question field required')
  if r['verdict']=='unspecified':require(r['question'].startswith('OPEN:') and len(r['question'])>6,'unknown policy must stay OPEN')
  else:require(r['question']=='','decided finding cannot silently retain unresolved question')
 corrections=report.get('corrections');require(isinstance(corrections,list),'correction list required')
 if baseline is None:require(not corrections,'baseline cannot claim earlier corrections')
 else:
  old={r['id']:r for r in baseline['findings']}
  changes=[{'id':r['id'],'before':old[r['id']]['verdict'],'after':r['verdict']} for r in rows if old[r['id']]['verdict']!=r['verdict']]
  require(sorted(corrections,key=lambda r:r['id'])==sorted(changes,key=lambda r:r['id']),'every verdict change must be attributed exactly once')
 return report

def score(report,oracle):
 rows={r['id']:r for r in report['findings']}
 require(set(rows)==set(oracle),'oracle inventory mismatch')
 wrong=[k for k,v in oracle.items() if rows[k]['verdict']!=v['verdict']]
 return {'correct':len(oracle)-len(wrong),'total':len(oracle),'wrong':wrong,
  'false_supported':[k for k in wrong if rows[k]['verdict']=='supported'],
  'missed_supported':[k for k in wrong if oracle[k]['verdict']=='supported'],
  'closed_policy':[k for k in wrong if oracle[k]['verdict']=='unspecified']}

def validate_splits(dataset):
 splits=dataset['splits'];require(set(splits)=={'train','validation','test'},'three splits required')
 names=[n for values in splits.values() for n in values]
 require(all(splits.values()) and len(names)==len(set(names)) and set(names)==set(dataset['components']),'components must be separated and complete')
 groups={key:{dataset['components'][n]['family'] for n in values} for key,values in splits.items()}
 for a in groups:
  for b in groups:
   if a!=b:require(not groups[a]&groups[b],'source families cross splits')

def check_access(dataset,component,phase,frozen=False):
 validate_splits(dataset)
 require(component in dataset['components'],'unknown component')
 require(phase in ('optimization','final'),'unknown evaluation phase')
 if phase=='optimization':require(component not in dataset['splits']['test'],'held-out test cannot enter optimization')
 else:require(frozen and component in dataset['splits']['test'],'final test requires frozen selection')
