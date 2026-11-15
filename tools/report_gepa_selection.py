#!/usr/bin/env python3
"""Expose recorded GEPA tie and index-based fallback without promoting a prompt."""
import json
import sys
from pathlib import Path
from gepa_selection import classify

def report(path):
 selected=json.loads(Path(path).read_text());result=classify(selected['validation_scores'])
 index=selected['best_index']
 if index not in result['tied'] or selected['candidate']!=selected['candidates'][index]:
  raise ValueError('recorded best candidate does not match scores')
 return {'selection':result,'gepa_returned_index':index,'interpretation':'exact tie; index alone is not evidence of superiority' if result['status']=='tie' else 'unique recorded score; uncertainty is not quantified'}
if __name__=='__main__':
 default=Path(__file__).resolve().parents[1]/'docs/evidence/gepa-heldout/runs/selected-prompt.json'
 print(json.dumps(report(sys.argv[1] if len(sys.argv)>1 else default),indent=2))
