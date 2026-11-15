"""Audit exploratory Flash proposals without accepting model claims."""
import re
from collections import Counter

def score(labels,checks,result):
 expected={c['id']:c for c in checks};gold=labels['checks'];claims=result['claims'];questions=result['questions']
 if len(expected)!=len(checks) or set(gold)!=set(expected) or not isinstance(claims,dict) or not isinstance(questions,list):raise ValueError('incomplete or duplicate inventory')
 seen=[];unmapped=[]
 for q in questions:
  m=re.match(r'^([A-Z][0-9]{2}):',q) if isinstance(q,str) else None
  if m and m.group(1) in expected:seen.append(m.group(1))
  else:unmapped.append(q)
 duplicates=sorted(k for k,v in Counter(list(claims)+seen).items() if v>1)
 matched=[];changed=[];extra=[];verified=[]
 for ident,claim in claims.items():
  if ident not in expected:extra.append(ident);continue
  source=expected[ident]
  if ident in duplicates or any(claim.get(k)!=source[k] for k in ('kind','statement','line','fragment')) or claim.get('citation_check')!='ok':changed.append(ident);continue
  matched.append(ident)
  if isinstance(claim.get('jev'),dict) and claim['jev'].get('choice')=='supported':verified.append(ident)
 return {'matched':len(matched),'matched_ids':sorted(matched),'supported_reference_matched':sorted(i for i in matched if gold[i]['expected']=='supported'),'nonsupported_reference_matched':sorted(i for i in matched if gold[i]['expected']!='supported'),'jev_supported_ids':sorted(verified),'changed':sorted(changed),'extra_claims':sorted(extra),'questions':sorted(seen),'unmapped_questions':unmapped,'duplicate_ids':duplicates,'missing':sorted(set(expected)-set(claims)-set(seen))}
