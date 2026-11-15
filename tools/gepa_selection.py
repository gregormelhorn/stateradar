"""Report exact optimizer ties rather than treating index order as evidence."""
import math

def classify(scores):
 if not scores or not all(isinstance(x,(float,int)) and not isinstance(x,bool) and math.isfinite(x) for x in scores):
  raise ValueError('nonempty finite numeric scores required')
 top=max(scores)
 tied=[i for i,score in enumerate(scores) if score==top]
 return {'status':'unique' if len(tied)==1 else 'tie','best':tied[0] if len(tied)==1 else None,'tied':tied}
