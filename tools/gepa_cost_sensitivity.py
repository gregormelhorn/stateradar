"""Separate actual metered cost equivalents from cache/rate sensitivity."""
import argparse,json
from datetime import datetime
from pathlib import Path
from gepa_eval import require
from run_gepa_comparison import read,save
from run_sol_pilot import read_usage


def flash_weekend_bounds(draft):
 inputs=draft['input_tokens'];outputs=draft['output_tokens']
 require(type(inputs)is int and type(outputs)is int and inputs>=0 and outputs>=0,'invalid Flash usage')
 return ((inputs*.003+outputs*.6)/1e6,(inputs*.15+outputs*.6)/1e6)


def analyze(out):
 calls=read(out/'calls.json');providers=read(out/'providers.json');rows=read(out/'comparison.json');summary=read(out/'audited-summary.json')
 # The correction is only valid for this weekend experiment, not an evergreen rate card.
 for c in calls:
  records=[json.loads(l) for l in (out/c['directory']/'usage-history.jsonl').read_text().splitlines()]
  require(records and all(datetime.fromisoformat(r['timestamp'].replace('Z','+00:00')).weekday()>=5 for r in records),'weekend pricing premise not observed')
 bounds={};provider_low=provider_high=opt_low=opt_high=0.
 for p in providers:
  low,high=flash_weekend_bounds(p['response']['draft'])
  jev=sum(c['amount_microdollars'] for c in p['calls'] if c['provider']=='jev')/1e6
  low+=jev;high+=jev;provider_low+=low;provider_high+=high
  if p['phase']=='optimization':opt_low+=low;opt_high+=high
  bounds[(p['component'],p['repeat'],p['phase'])]=(low,high)
 arms={}
 for arm in ('none','fixed','gepa'):
  low=high=normalized=review=review_uncached=0.
  for row in [r for r in rows if r['arm']==arm]:
   pl,ph=bounds[(row['component'],row['repeat'],'final')]
   charged=row['total_usd_estimate']-row['provider_usd'];low+=charged+pl;high+=charged+ph
   for i in row['baseline_call_ids']+row['review_call_ids']:
    usage=read_usage(out/calls[i]['directory']/'events.jsonl')
    full=(usage['input_tokens']*50+usage['output_tokens']*250)/1e6*.04
    normalized+=full
    if i in row['review_call_ids']:
     review+=calls[i]['cost']['total_usd_estimate'];review_uncached+=full
  arms[arm]={'weekend_strategy_cost_equivalent_range':[low,high],
   'controller_cost_if_no_cache_discount':normalized,'actual_review_controller_equivalent':review,
   'review_controller_if_no_cache_discount':review_uncached}
 actual_codex=sum(c['cost']['total_usd_estimate'] for c in calls)
 opt_codex=sum(c['cost']['total_usd_estimate'] for c in calls if c['category']in ('optimization','reflection') or c['category']=='baseline' and c['component']in ('context','singleflight'))
 result={'arms':arms,'actual_experiment_equivalent_range':[actual_codex+provider_low,actual_codex+provider_high],
  'optimization_equivalent_range':[opt_codex+opt_low,opt_codex+opt_high],
  'flash_source':'https://api-docs.deepseek.com/quick_start/pricing/','jev_source':'https://help.typesafe.ai/articles/5187202169-how-much-does-jev-cost',
  'observed_date':'2026-11-15','flash_offpeak_per_million':{'cached_input':.003,'uncached_input':.15,'output':.6},
  'limitation':'Flash cache split absent; range assumes all inputs cached versus uncached. Codex is a $0.04/credit equivalent, not an account debit. No-cache sensitivity is not actual spend. Unmetered supervising/human work remains excluded.'}
 save(out/'cost-sensitivity.json',result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args();print(json.dumps(analyze(a.run),indent=2))
