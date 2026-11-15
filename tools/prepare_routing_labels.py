#!/usr/bin/env python3
"""Freeze fragment-scoped reference labels before any measured model call."""
import hashlib
import json
from pathlib import Path
from routing_evaluation import check_splits,reconcile
from routing_label_integrity import verify_source
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/evidence/routing-labels'
def read(p):return json.loads(p.read_text())
def save(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
def main():
 manifest=read(BASE/'inputs/manifest.json');check_splits(manifest)
 status=read(BASE/'reference-review/status.json')
 if status.get('status')!='complete':raise ValueError('independent AI review incomplete')
 ref_freeze=read(BASE/'reference-review/input-freeze.json')
 for name,h in ref_freeze.items():
  if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=h:raise ValueError('reference input changed: '+name)
 out=BASE/'frozen';out.mkdir(exist_ok=False);disputes={}
 for name,info in manifest['components'].items():
  source=(ROOT/info['source']).read_text();checks=read(BASE/info['checks']);labels=read(BASE/info['proposed_labels']);review=read(BASE/'reference-review'/f'{name}.json')['review']
  verify_source(source,info['sha256'],checks)
  if labels['source_sha256']!=info['sha256']:raise ValueError('label source hash differs')
  byid={c['id']:c for c in checks}
  if set(byid)!=set(labels['checks']):raise ValueError('label/check mismatch')
  for ident,label in labels['checks'].items():
   c=byid[ident]
   if any(label[k]!=c[k] for k in ('kind','statement','line','fragment')) or label['source']!=info['source']:raise ValueError('label identity differs')
  result=reconcile(labels,review)
  for ident,label in result['agreed'].items():label['reviewer']='AI operator; separately checked by isolated Codex reference reviewer before Jev'
  disputes[name]=result['disputes'];save(out/f'{name}-labels.json',{'source_sha256':info['sha256'],'checks':result['agreed']})
 save(out/'disputes.json',disputes)
 paths=[BASE/'protocol.md',BASE/'inputs/manifest.json',ROOT/'tools/routing_evaluation.py',ROOT/'tools/routing_label_integrity.py',ROOT/'tools/prepare_routing_labels.py',ROOT/'tools/jev_eval.py',ROOT/'tools/local_models.py',ROOT/'tools/run_gepa_comparison.py']
 paths += [p for p in (BASE/'inputs').glob('*.json') if p.is_file()]
 paths += [p for p in (BASE/'reference-review').rglob('*') if p.is_file() and p.suffix!='.sqlite']
 paths += [ROOT/info['source'] for info in manifest['components'].values()]
 paths += [p for p in out.glob('*.json')]
 freeze={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))};save(out/'input-freeze.json',freeze)
 print('LABEL FREEZE:',sum(len(read(out/f'{name}-labels.json')['checks']) for name in manifest['components']),'agreed;',sum(map(len,disputes.values())),'OPEN disputes')
if __name__=='__main__':main()
