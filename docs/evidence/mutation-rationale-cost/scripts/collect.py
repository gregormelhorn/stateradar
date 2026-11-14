"""Summarize completed runs without repairing their evidence or pricing unknowns."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def read(path):
    return json.loads(path.read_text()) if path.is_file() else None


def collect(run):
    arm=run/'selective'
    settings=read(run/'experiment.json')
    assert settings is not None, 'missing experiment settings'
    cost=read(arm/'cost-estimate.json')
    assert cost is not None, 'run has not finalized accounting'
    events=[json.loads(line) for line in (arm/'events.jsonl').read_text().splitlines() if line.strip()]
    completed=[e['usage'] for e in events if e.get('type')=='turn.completed']
    checkpoint=read(arm/'usage-checkpoint.json')
    if cost['complete']:
        assert len(completed)==1, 'complete costs require exactly one completed turn'
        assert completed[0]==read(arm/'usage.json')==checkpoint['usage'], 'usage counters disagree'
        assert checkpoint['complete'], 'checkpoint incomplete'
    else:
        assert cost['total_usd_estimate'] is None, 'unknown total must remain null'
    calls=[e['item'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='mcp_tool_call']
    rows=[]
    for path in sorted((arm/'logs').glob('[0-9]*.json')):
        d=read(path)
        if 'exit_code' not in d:continue # Preflight metadata is not a controller command.
        argv=d['argv']
        rows.append({'log':path.stem,'exit':d['exit_code'],'argv':argv})
    model_commands=[r for r in rows if len(r['argv'])>4 and Path(r['argv'][1]).name=='local_models.py']
    ledger=read(arm/'routing-cost.json')
    assert ledger is not None, 'missing provider ledger'
    if cost['complete']:assert ledger['reserved_microdollars']==0, 'unsettled provider reservations'
    by_provider=Counter()
    for call in ledger['calls']:by_provider[call['provider']+'/'+call['status']]+=call['amount_microdollars']
    flash_usage=[]
    for row in model_commands:
        try:payload=read(arm/'logs'/f"{row['log']}.stdout")
        except json.JSONDecodeError:continue
        if not isinstance(payload,dict):continue
        usage=payload.get('draft',payload)
        if isinstance(usage,dict) and usage.get('model')=='deepseek-flash' and 'input_tokens' in usage:
            flash_usage.append(usage)
    paid_flash=[c for c in ledger['calls'] if c['provider']=='deepseek-flash' and c['status']=='settled']
    range_estimate=None
    if paid_flash and Counter(c['amount_microdollars'] for c in paid_flash)==Counter(c['cost_microdollars'] for c in flash_usage):
        inputs=sum(c['input_tokens'] for c in flash_usage)
        outputs=sum(c['output_tokens'] for c in flash_usage)
        other=(ledger['charged_microdollars']-sum(c['amount_microdollars'] for c in paid_flash))/1_000_000
        low=other+(inputs*.003+outputs*.6)/1_000_000
        high=other+(inputs*.15+outputs*.6)/1_000_000
        codex=cost['reported_codex_usd_estimate']
        range_estimate={'basis':'All recorded calls ran on Saturday, off-peak; cache split not retained.',
                        'reconciled_flash_calls':len(flash_usage),'provider_usd_min':low,'provider_usd_max':high,
                        'combined_usd_min':codex+low if cost['complete'] else None,
                        'combined_usd_max':codex+high if cost['complete'] else None}
    analysis=arm/'pool/domain-analysis/circuitBreaker'
    sidecar=read(analysis/'analysis.json')
    return {
        'settings':settings,'cost':cost,'off_peak_estimate':range_estimate,'result':read(arm/'result.json'),
        'failure':read(arm/'failure.json'),'gates':read(arm/'acceptance.json'),
        'controller_commands':len(rows),'completed_tool_calls':len(calls),
        'mcp_tool_errors':[{'id':c['id'],'argv':c.get('arguments',{}).get('argv'),
                            'error':c.get('error')} for c in calls if c.get('status')=='failed' or c.get('error')],
        'retained_log_reads':sum(c.get('arguments',{}).get('argv',[])[:1]==['read-log'] for c in calls),
        'nonzero_commands':[r for r in rows if r['exit']!=0],
        'model_commands_by_exit':dict(Counter(r['argv'][4]+'/exit-'+str(r['exit']) for r in model_commands)),
        'actual_blind_dispatches':[{'log':r['log'],'exit':r['exit']} for r in model_commands if r['argv'][4]=='blind' and '--help' not in r['argv'] and '--package-only' not in r['argv']],
        'provider_microdollars_by_status':dict(by_provider),
        'sidecar_counts':{k:len(sidecar.get(k,[])) for k in ('states','events','cells','pairs','guardGroups','questions')} if sidecar else None,
        'artifact_sha256':{str(p.relative_to(analysis)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(analysis.rglob('*')) if p.is_file() and '__pycache__' not in p.parts},
    }


def matched(left,right):
    a={k:v for k,v in left['settings'].items() if k!='routing_variant'}
    b={k:v for k,v in right['settings'].items() if k!='routing_variant'}
    if a!=b:raise ValueError('unmatched experiment settings')


if __name__=='__main__':
    if len(sys.argv)!=4:raise SystemExit('collect.py ROUTED_ROOT MATRIX_ROOT OUTPUT_JSON')
    result={name:collect(Path(path)) for name,path in zip(('routed','matrix'),sys.argv[1:3])}
    matched(result['routed'],result['matrix'])
    # Negative control: the comparison must reject a different source revision.
    broken=json.loads(json.dumps(result['matrix']));broken['settings']['component_sha']='wrong-source'
    try:matched(result['routed'],broken)
    except ValueError:pass
    else:raise AssertionError('mismatched-source red probe did not fail')
    Path(sys.argv[3]).write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('MATCHED SETTINGS: PASS; mismatched-source red probe rejected')
    for name,row in result.items():
        print(name,'cost',row['cost']['total_usd_estimate'],'gates',row['gates'],
              'rereads',row['retained_log_reads'],'nonzero commands',len(row['nonzero_commands']))
