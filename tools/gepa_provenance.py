"""Check labeled claim citations against their recorded source fragments."""
from pathlib import Path
LABELS={'explicit-requirement','observed-in-code','observed-in-tests','inferred','proposed'}
def validate(document,root):
 errors=[]
 for kind in ('cases','findings'):
  rows=document.get(kind)
  if not isinstance(rows,list):errors.append('missing '+kind);continue
  for row in rows:
   name=row.get('id','?')
   if row.get('provenance') not in LABELS:errors.append('invalid provenance: '+name)
   citations=[row.get('citation')]
   if kind=='cases':citations.append(row.get('test_citation'))
   for citation in citations:
    try:
     path=Path(root)/citation['file'];lines=path.read_text().splitlines();n=citation['line'];frag=citation['fragment']
     if type(n)is not int or not 1<=n<=len(lines) or not isinstance(frag,str) or not frag or frag not in lines[n-1]:raise ValueError()
    except (KeyError,TypeError,ValueError,OSError):errors.append('invalid citation: '+name)
 return errors
