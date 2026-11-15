"""Audit immutable measured GEPA calls and aggregate costs without double counting."""
import argparse,json
from pathlib import Path
from gepa_eval import validate,score,require
from run_gepa_comparison import read,save,sha,decode,HERE,ROOT,MODEL
from run_sol_pilot import read_usage
from pilot_accounting import cost_report
from local_budget import Budget


def summarize(rows,calls,providers):
 ids={c['id']:c for c in calls};require(len(ids)==len(calls),'duplicate charged call')
 require(all(c['cost']['complete'] for c in calls),'incomplete cost: no total')
 totals={}
 for arm in ('none','fixed','gepa'):
  subset=[r for r in rows if r['arm']==arm];require(bool(subset),'missing comparison arm')
  trials={(r['component'],r['repeat']) for r in subset};require(len(trials)==len(subset),'duplicate comparison trial')
  if totals:require(trials==previous,'unmatched comparison trials')
  previous=trials
  cost=review=0.;correct=total=repairs=0
  for row in subset:
   all_ids=row['baseline_call_ids']+row['review_call_ids'];require(len(set(all_ids))==len(all_ids),'duplicate call within strategy')
   expected=row['provider_usd']+sum(ids[i]['cost']['total_usd_estimate'] for i in all_ids)
   require(abs(expected-row['total_usd_estimate'])<1e-9,'strategy omitted cost/rework')
   require(row['repair_calls']==sum(ids[i]['repair'] for i in all_ids),'repair work omitted')
   cost+=expected;review+=sum(ids[i]['cost']['total_usd_estimate'] for i in row['review_call_ids'])
   correct+=row['quality']['correct'];total+=row['quality']['total'];repairs+=row['repair_calls']
  totals[arm]={'trials':len(subset),'correct':correct,'total_case_observations':total,'strategy_cost_usd_estimate':cost,'incremental_review_usd_estimate':review,'repair_calls':repairs}
 experiment=sum(c['cost']['total_usd_estimate'] for c in calls)+sum(p['cost_usd'] for p in providers)
 optimization=sum(c['cost']['total_usd_estimate'] for c in calls if c['category'] in ('optimization','reflection') or c['category']=='baseline' and c['component'] in ('context','singleflight'))+sum(p['cost_usd'] for p in providers if p['phase']=='optimization')
 saving=(totals['fixed']['strategy_cost_usd_estimate']-totals['gepa']['strategy_cost_usd_estimate'])/totals['fixed']['trials']
 return {'arms':totals,'actual_experiment_usd_estimate':experiment,'optimization_usd_estimate':optimization,
  'break_even_uses_vs_fixed':optimization/saving if saving>0 and totals['gepa']['correct']>=totals['fixed']['correct'] else None,
  'cost_basis':'Metered Codex credit equivalents at $0.04/credit plus settled provider ledger. Not invoice debit.',
  'unmetered':'Supervising implementation/review chat and human effort; not zero. Residual incorrect findings are unresolved, not repaired for free.',
  'unit':'14 unique held-out claims on two components, three paired repeats; 42 observations per arm, not 42 independent cases'}


def audit(out):
 require(read(out/'status.json')['status']=='complete','experiment incomplete')
 freeze=read(out/'input-freeze.json')
 for name,digest in freeze.items():require(sha(ROOT/name)==digest,'frozen input drift: '+name)
 calls=read(out/'calls.json');providers=read(out/'providers.json');rows=read(out/'comparison.json')
 require([c['id'] for c in calls]==list(range(len(calls))),'call IDs are not consecutive and ordered')
 require({c['directory'] for c in calls}=={str(d.relative_to(out)) for d in (out/'calls').iterdir() if d.is_dir()},'charged call directory omitted')
 ledger=Budget(out/'routing.sqlite').calls()
 flattened=[c for p in providers for c in p['calls']]
 require(sorted(flattened,key=lambda c:c['id'])==ledger,'provider calls omitted/duplicated')
 require(all(c['status']=='settled' for c in ledger),'unsettled provider cost')
 for p in providers:require(abs(sum(c['amount_microdollars'] for c in p['calls'])/1e6-p['cost_usd'])<1e-10,'provider total drift')
 for c in calls:
  d=out/c['directory'];require(c['failure']is None,'failed call still needs review')
  expected=cost_report({'usage':read_usage(d/'events.jsonl'),'complete':True},{'charged_microdollars':0,'reserved_microdollars':0},MODEL)
  require(expected==c['cost'],'Codex cost drift')
  records=[json.loads(l) for l in (d/'events.jsonl').read_text().splitlines()]
  kinds={r['item']['type'] for r in records if 'item'in r}
  require(kinds<= {'agent_message','reasoning'},'unexpected task tool access: '+str(kinds))
  if c.get('structural_valid'):require(decode((d/'final.txt').read_text())==read(d/'validated.json'),'model output changed')
 dataset=read(HERE/'dataset.json');selected=read(out/'selected-prompt.json')
 expected_trials={(component,repeat,arm) for component in dataset['splits']['test'] for repeat in range(3) for arm in ('none','fixed','gepa')}
 require(len(rows)==len(expected_trials) and {(r['component'],r['repeat'],r['arm']) for r in rows}==expected_trials,'primary trial coverage incomplete')
 require(selected['input_hashes']==freeze,'selected candidate/input mismatch')
 first_final=min(c['id'] for c in calls if c['component'] in dataset['splits']['test'])
 require(all(c['id']<first_final for c in calls if c['category'] in ('optimization','reflection')),'test leaked into later search')
 for row in rows:
  component=row['component'];baseline=read(out/f"baseline-{component}-{row['repeat']}.json")
  provider=providers[baseline['provider_index']]
  require((provider['component'],provider['repeat'],provider['phase'])==(component,row['repeat'],'final'),'wrong baseline provider')
  require(row['provider_usd']==baseline['provider_cost']==provider['cost_usd'],'strategy provider cost differs from settled ledger')
  public=read(HERE/dataset['components'][component]['public']);source=(HERE/public['source']).read_text();oracle=read(HERE/dataset['components'][component]['oracle'])
  require(row['baseline_call_ids']==baseline['call_ids'],'baseline call mismatch')
  baseline_dir=out/calls[baseline['call_ids'][-1]]['directory']
  require(baseline['report']==read(baseline_dir/'validated.json'),'baseline differs from actual model output')
  if row['arm']=='none':require(row['report']==baseline['report'] and not row['review_call_ids'],'no-review baseline changed')
  else:
   last=calls[row['review_call_ids'][-1]];d=out/last['directory']
   require(row['report']==read(d/'validated.json'),'review output mismatch')
   paragraph=(HERE/'prompts/fixed.md').read_text() if row['arm']=='fixed' else selected['candidate']['review']
   require(paragraph in (d/'prompt.md').read_text(),'wrong review paragraph')
  validate(row['report'],public,source,None if row['arm']=='none' else baseline['report'])
  require(score(row['report'],oracle)==row['quality'],'quality score drift')
 summary=summarize(rows,calls,providers)
 if (out/'quality-extension.json').exists():summary['quality_extension']=audit_quality(out,calls)
 save(out/'audited-summary.json',summary)
 return summary

def audit_quality(out,calls):
 from run_gepa_quality_extension import SEEDS
 require(read(out/'quality-extension-status.json')['status']=='complete','quality extension incomplete')
 declaration=read(out/'quality-extension-declaration.json')
 require(declaration['protocol_sha256']==sha(HERE/'quality-extension.md') and declaration['script_sha256']==sha(ROOT/'tools/run_gepa_quality_extension.py'),'quality extension declaration drift')
 require(declaration['selection_sha256']==sha(out/'selected-prompt.json'),'quality extension changed selection')
 rows=read(out/'quality-extension.json');require({(r['component'],r['arm']) for r in rows}=={(c,a) for c in SEEDS for a in ('fixed','gepa')} and len(rows)==4,'quality extension coverage')
 totals={a:{'corrected':0,'seeded_errors':6,'retained_correct_controls':0,'controls':8,'introduced':0,'incremental_usd_estimate':0.,'repair_calls':0} for a in ('fixed','gepa')}
 used=[]
 for row in rows:
  component=row['component'];original=read(out/f'baseline-{component}-0.json');baseline=read(out/f'diagnostic-input-{component}.json')
  expected=__import__('copy').deepcopy(original['report'])
  for finding in expected['findings']:
   if finding['id'] in SEEDS[component]:
    finding['verdict'],finding['reason']=SEEDS[component][finding['id']];finding['question']=''
  expected['corrections']=[];require(expected==baseline,'unexpected diagnostic injection')
  public=read(HERE/f'{component}-public.json');source=(HERE/public['source']).read_text();oracle=read(HERE/f'{component}-oracle.json')
  validate(row['report'],public,source,baseline);require(score(row['report'],oracle)==row['quality'],'diagnostic score drift')
  ids=row['call_ids'];used+=ids
  require(all(i>=declaration['first_call_id'] and calls[i]['category']=='quality-'+row['arm'] and calls[i]['component']==component for i in ids),'wrong diagnostic calls')
  d=out/calls[ids[-1]]['directory'];require(read(d/'validated.json')==row['report'],'diagnostic differs from model output')
  require(json.dumps(baseline) in (d/'prompt.md').read_text(),'diagnostic input not actually supplied')
  wrong=set(row['quality']['wrong']);seeded=set(SEEDS[component]);introduced=wrong-seeded
  require(row['corrected']==sorted(seeded-wrong) and row['introduced']==sorted(introduced) and row['retained_correct_controls']==4-len(introduced),'diagnostic correction count drift')
  amount=sum(calls[i]['cost']['total_usd_estimate'] for i in ids);repairs=sum(calls[i]['repair'] for i in ids)
  require(abs(amount-row['incremental_usd_estimate'])<1e-9 and repairs==row['repair_calls'],'diagnostic repair costs omitted')
  total=totals[row['arm']];total['corrected']+=len(seeded-wrong);total['retained_correct_controls']+=4-len(introduced)
  total['introduced']+=len(introduced);total['incremental_usd_estimate']+=amount;total['repair_calls']+=repairs
 require(len(used)==len(set(used)) and set(used)=={c['id'] for c in calls if c['category'].startswith('quality-')},'diagnostic charged calls omitted/duplicated')
 return totals

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args()
 print(json.dumps(audit(a.run),indent=2))
