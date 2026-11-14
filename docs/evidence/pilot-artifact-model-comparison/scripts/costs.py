import json,sys
from pathlib import Path
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).parent))
import collect
result={c:{v:collect.collect(c,n,v) for v in collect.VARIANTS} for c,n in collect.COMPONENTS.items()}
for component,arms in result.items():
    settings=[arm['settings'] for arm in arms.values() if arm and arm['settings']]
    if settings:
        assert len({json.dumps({k:v for k,v in s.items() if k!='model'},sort_keys=True) for s in settings})==1
    for variant,arm in arms.items():
        if not arm:continue
        assert arm['settings']['model']==f'gpt-6.1-{variant}'
        counters=arm['codex']['counters']
        arm['cost']={'codex_standard_credits':None,'assumed_usd_per_credit':0.04,'codex_usd_equivalent':None,'provider_conservative_usd':(arm['provider_ledger_microdollars']['settled']/1000000 if 'provider_ledger_microdollars' in arm else None),'combined_conservative_usd_equivalent':None}
        if counters:
            assert counters.get('cache_write_input_tokens',0)==0
            assert counters['input_tokens']>=counters['cached_input_tokens']
            factor=Decimal('0.5') if variant=='terra' else Decimal(1)
            credits=factor*(Decimal(counters['input_tokens']-counters['cached_input_tokens'])*50+Decimal(counters['cached_input_tokens'])*Decimal('2.5')+Decimal(counters['output_tokens'])*250)/1000000
            provider=arm.get('provider_ledger_microdollars',{}).get('settled')
            arm['cost']={'codex_standard_credits':float(credits),'assumed_usd_per_credit':0.04,'codex_usd_equivalent':float(credits*Decimal('0.04')),'provider_conservative_usd':provider/1000000 if provider is not None else None,'combined_conservative_usd_equivalent':float(credits*Decimal('0.04')+Decimal(provider)/1000000) if provider is not None else None}
        folder=collect.ROOT/f'{component}-{variant}'/'selective'
        events=collect.load_events(folder/'events.jsonl')
        failures=[];reads=[]
        for event in events:
            item=event.get('item',{})
            if event.get('type')!='item.completed' or item.get('type')!='mcp_tool_call':continue
            argv=item.get('arguments',{}).get('argv',[])
            if item.get('error'):failures.append({'item':item['id'],'argv':argv,'error':item['error']})
            if argv[:1]==['read-log']:
                original=collect.read_json(folder/'logs'/(argv[1].split('.')[0]+'.json'))
                reads.append({'item':item['id'],'argv':argv,'failed':bool(item.get('error')),'original_argv':original.get('argv',[]) if original else None})
        arm['failed_tool_requests']=failures
        arm['retained_log_request_details']=reads
        arm['nonzero_commands']=[{'log':p.stem,'exit_code':entry['exit_code'],'argv':[part[:250] for part in entry.get('argv',[])]} for p in sorted((folder/'logs').glob('[0-9]*.json')) if (entry:=collect.read_json(p)) and entry.get('exit_code',0)!=0]
print(json.dumps(result,indent=2))
