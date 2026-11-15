"""Budget and blind-dispatch guards for the matched pilot."""
from pilot_accounting import cost_report

def tally(prior,checkpoint,provider,blind):
 if prior is None or not isinstance(prior,(int,float)) or prior<0:raise ValueError('unknown prior cost')
 if not isinstance(checkpoint,dict) or checkpoint.get('usage') is None:raise ValueError('unknown controller usage')
 if any(c.get('status')!='settled' for c in provider):raise ValueError('unsettled provider cost')
 base=cost_report(checkpoint,{'charged_microdollars':sum(c['amount_microdollars'] for c in provider),'reserved_microdollars':0},'gpt-6.1-sol')
 if base['reported_codex_usd_estimate'] is None:raise ValueError('unknown controller cost')
 total=prior+base['known_subtotal_usd_estimate']
 for item in blind:
  if not item.get('complete') or item.get('usage') is None:raise ValueError('unknown blind usage')
  out=cost_report(item,{'charged_microdollars':0,'reserved_microdollars':0},'gpt-6.1-sol')
  if not out['complete']:raise ValueError('unknown blind cost')
  total+=out['total_usd_estimate']
 return total

def allow_blind(args,output):
 if not isinstance(args,list) or not args or args[0]!='blind' or args.count('--output')!=1 or args[-2:]!=['--output',output] or '--package-only' in args or '--requirements' not in args or '--contracts' not in args:
  raise ValueError('blind requires requirements, contracts and one exact output path')

def route_policy(arm,command,package_only):
 if arm=='routed':return 'normal'
 if arm!='direct':raise ValueError('unknown arm')
 if command=='blind':return 'package' if package_only else 'blind'
 if command=='status':return 'status'
 return 'deny'

def enforce_cap(amount,cap):
 import math
 if not isinstance(amount,(int,float)) or not isinstance(cap,(int,float)) or not math.isfinite(amount) or not math.isfinite(cap) or amount<0 or cap<=0:raise ValueError('unknown or invalid budget')
 if amount>=cap:raise ValueError('budget reached')

def live_budget(prior,usage,calls,blind,elapsed,cap):
 if not isinstance(calls,list) or any(c.get('status') not in ('settled','reserved') or type(c.get('amount_microdollars')) is not int or c['amount_microdollars']<0 for c in calls):raise ValueError('unknown provider cost')
 total=prior+blind+sum(c['amount_microdollars'] for c in calls)/1_000_000
 if usage is not None:
  report=cost_report({'usage':usage,'complete':False},{'charged_microdollars':0,'reserved_microdollars':0},'gpt-6.1-sol')
  if report['reported_codex_usd_estimate'] is None:raise ValueError('unknown controller cost')
  total+=report['reported_codex_usd_estimate']
 enforce_cap(total,cap)
 if usage is None and elapsed>180:raise ValueError('unknown controller usage after 180 seconds')
 return total
