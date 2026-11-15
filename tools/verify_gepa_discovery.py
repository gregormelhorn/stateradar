#!/usr/bin/env python3
"""Replay attributed discovery assessments, frozen inputs and metered calls."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from gepa_discovery_eval import audit, require
from pilot_accounting import cost_report

def read(path):
    return json.loads(path.read_text())

def verify(root):
    root=Path(root)
    base=root/'docs/evidence/gepa-discovery'
    run=base/'runs'
    data=read(base/'benchmark.json')
    calls=read(run/'calls.json')
    results=read(run/'results.json')
    status=read(run/'status.json')
    selection=read(run/'selected-prompt.json')
    require(status.get('status')=='complete' and status.get('calls')==13 and len(calls)==13, 'expected complete 13 calls')
    require([c['id'] for c in calls]==list(range(13)), 'missing or reordered calls')
    require(len(results)==11 and status.get('metrics')==7 and status.get('proposals')==2, 'missing reviews or optimization runs')
    require(Counter(c['category'] for c in calls)==Counter({'optimization':7,'reflection':2,'final-fixed':2,'final-gepa':2}), 'wrong call categories')
    require(all(c['category'] not in ('final-fixed','final-gepa') for c in calls[:9]) and all(c['category'].startswith('final-') for c in calls[9:]),'final calls must follow optimization')
    require(selection['best_index']==0 and selection['candidate']['review']==(base/'fixed.md').read_text(), 'selected candidate differs from fixed seed')
    expected = {str((base/name).relative_to(root)) for name in ('benchmark.json','protocol.md','fixed.md')} | {'tools/gepa_discovery_eval.py','tools/run_gepa_discovery.py'} | {str((base/'upstream'/name).relative_to(root)) for name in ('cond.go','cond_test.go','go.LICENSE','gobreaker.LICENSE','gobreaker.go','timer.go','waitgroup.go','waitgroup_test.go')}
    frozen=read(run/'input-freeze.json')
    require(set(frozen)==expected, 'frozen input inventory missing or extra')
    for name,digest in frozen.items():
        path=Path(name)
        require(not path.is_absolute() and '..' not in path.parts and hashlib.sha256((root/path).read_bytes()).hexdigest()==digest, 'frozen input hash mismatch: '+name)
    costs=defaultdict(float)
    for c in calls:
        dest=run/c['directory']
        events=[json.loads(line) for line in (dest/'events.jsonl').read_text().splitlines()]
        require(not any(e.get('item',{}).get('type') in ('command_execution','mcp_tool_call','web_search','file_change') for e in events), 'forbidden task-model tool event')
        cost=cost_report(read(dest/'usage-checkpoint.json'),{'charged_microdollars':0,'reserved_microdollars':0},'gpt-6.1-sol')
        require(c['cost']['complete'] and cost['complete'] and c['cost']['total_usd_estimate']==cost['total_usd_estimate'], 'incomplete or altered cost')
        require(c.get('failure') is None and c.get('structural_valid') is True, 'failed call')
        costs[c['category']]+=cost['total_usd_estimate']
    seen=[]
    for result in results:
        ids=result['call_ids']
        require(len(ids)==1 and ids[0] not in seen, 'missing or duplicate reviewed call')
        seen+=ids
        c=calls[ids[0]]
        require(c['category']==result['category'] and c['component']==result['component'], 'review/call mismatch')
        component=data['components'][result['component']]
        source=(base/component['source']).read_text()
        actual=audit(read(run/c['directory']/'validated.json'),source,component['cases'],read(run/result['review']))
        require(actual==result['summary'], 'review totals mismatch')
    require(set(seen)=={c['id'] for c in calls if c['category']!='reflection'},'incomplete reviewed-call coverage')
    return {'reviews':len(results),'calls':len(calls),'usd_equivalent_total':sum(costs.values()),'usd_equivalent_by_category':dict(costs),'selected_same_as_fixed':True}

if __name__=='__main__':
    print(json.dumps(verify(Path(__file__).resolve().parents[1]),indent=2))
