"""Validate pinned source and exact check citations before model calls."""
import hashlib
from local_models import _citation_error

def verify_source(source,digest,checks):
 if not isinstance(source,str) or hashlib.sha256(source.encode('utf-8')).hexdigest()!=digest:raise ValueError('source hash mismatch')
 if not isinstance(checks,list) or not checks:raise ValueError('nonempty checks required')
 ids=[c.get('id') for c in checks]
 if any(not isinstance(x,str) or not x for x in ids) or len(ids)!=len(set(ids)):raise ValueError('duplicate or missing check ID')
 for check in checks:
  error=_citation_error(source.splitlines(),check.get('line'),check.get('fragment'))
  if error:raise ValueError('citation: '+error)
