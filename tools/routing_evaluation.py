"""Gates and label reconciliation for bounded routing evaluation."""
from collections import Counter
VERDICTS={'supported','contradicted','unclear'}
def check_splits(manifest):
 splits=manifest.get('splits',{});dev=splits.get('dev');held=splits.get('heldout');components=manifest.get('components',{})
 if not isinstance(dev,list) or not dev or not isinstance(held,list) or not held:raise ValueError('nonempty splits required')
 all_names=dev+held
 if len(set(all_names))!=len(all_names) or set(all_names)!=set(components):raise ValueError('split overlap or component mismatch')
 if any(components[n].get('split')!=s for s,group in (('dev',dev),('heldout',held)) for n in group):raise ValueError('component split mismatch')
def allow(manifest,component,phase,dev_complete):
 check_splits(manifest)
 if phase not in ('dev','heldout') or component not in manifest['splits'][phase]:raise ValueError('component outside requested split')
 if phase=='dev' and dev_complete:raise ValueError('development is frozen')
 if phase=='heldout' and not dev_complete:raise ValueError('heldout locked until development complete')
def reconcile(proposed,review):
 cases=proposed.get('checks');rows=review.get('cases')
 if not isinstance(cases,dict) or not cases or not isinstance(rows,list) or Counter(r.get('id') for r in rows)!=Counter(list(cases)):raise ValueError('exact independent review coverage required')
 agreed={};disputes={}
 for r in rows:
  ident=r['id'];label=cases[ident];verdict=r.get('verdict')
  if verdict not in VERDICTS or label.get('expected') not in VERDICTS or not isinstance(r.get('reason'),str) or not r['reason'].strip():raise ValueError('invalid verdict or reason')
  if verdict==label['expected']:agreed[ident]=label
  else:disputes[ident]={'proposed':label['expected'],'reviewed':verdict,'proposed_reason':label.get('reason',''),'review_reason':r['reason'],'status':'OPEN'}
 return {'agreed':agreed,'disputes':disputes}
