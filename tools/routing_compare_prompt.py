"""Prepare source-only comparator inputs without reference labels."""
import json

def build(source,checks):
 if not isinstance(source,str) or not source or not isinstance(checks,list) or not checks:raise ValueError('source and checks required')
 for c in checks:
  if not isinstance(c,dict) or set(c)!={'id','kind','statement','line','fragment'}:raise ValueError('check must not include reference or extra fields')
 return ('For each check, judge only whether the quoted fragment explicitly supports, contradicts, or leaves unclear the exact statement. Context may identify the subject but cannot add missing event ordering, conditions or callee error contracts. Treat comments as comments, not guaranteed runtime behavior. Return JSON {"cases":[{"id":"...","choice":"supported|contradicted|unclear","reason":"..."}]} exactly once per check.\nCHECKS:\n'+json.dumps(checks)+'\nSOURCE:\n'+'\n'.join(f'{i}: {line}' for i,line in enumerate(source.splitlines(),1)))
