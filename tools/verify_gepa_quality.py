"""Replay supplementary controls and validate attributed scope-review evidence."""
import json,runpy,tempfile
from pathlib import Path
from run_gepa_comparison import HERE,read,sha
from gepa_eval import require

def main():
 scope=read(HERE/'scope-review.json');require(scope['comparison_sha256']==sha(HERE/'runs/comparison.json'),'scope comparison drift')
 require(scope['probe_sha256']==sha(HERE/'reference/scope_extension_test.go') and scope['execution_sha256']==sha(HERE/'scope-reference.jsonl'),'scope evidence drift')
 rows=[r for r in read(HERE/'runs/comparison.json') if r['component']=='timer']
 require(len(scope['rows'])==len(rows)==9,'scope annotation coverage')
 for annotation in scope['rows']:
  row=next(r for r in rows if r['arm']==annotation['arm'] and r['repeat']==annotation['repeat'])
  finding=next(f for f in row['report']['findings'] if f['id']=='timer-03')
  require(annotation['reason']==finding['reason'] and annotation['reviewer'] and annotation['rationale'],'scope annotation anchor')
 require({(a['arm'],a['repeat']) for a in scope['rows']}=={(r['arm'],r['repeat']) for r in rows},'scope duplicate annotation')
 script=runpy.run_path(str(HERE/'scripts/scope_review.py'))
 with tempfile.TemporaryDirectory(prefix='gepa-scope-replay-') as td:script['run'](Path(td)/'go.jsonl')
 print('SCOPE ANNOTATIONS PASS: exact original reasons; semantic judgments remain attributed review')
if __name__=='__main__':main()
