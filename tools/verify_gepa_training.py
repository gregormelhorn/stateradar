#!/usr/bin/env python3
"""Replay discovery-training evidence; semantic conclusions remain reviewed data."""
import json
from collections import Counter
from pathlib import Path
from gepa_discovery_eval import require

def verify_test_log(path, expected, repeats):
    rows=[json.loads(s) for s in Path(path).read_text().splitlines() if s.startswith('{')]
    runs=Counter(r['Test'] for r in rows if r.get('Action')=='run' and r.get('Test'))
    passes=Counter(r['Test'] for r in rows if r.get('Action')=='pass' and r.get('Test'))
    require(expected and repeats>0 and set(runs)==set(expected) and runs==passes and all(v==repeats for v in runs.values()), 'missing, extra, or incomplete named test repetitions')
    require(any(r.get('Action')=='pass' and not r.get('Test') and r.get('Package') for r in rows) and not any(r.get('Action') in ('fail','build-fail') for r in rows), 'missing package completion or failure')
    return sum(passes.values())

def verify_expected_red(path, test, reason):
    rows=[json.loads(s) for s in Path(path).read_text().splitlines() if s.startswith('{')]
    require(any(r.get('Action')=='run' and r.get('Test')==test for r in rows), 'expected red test did not run')
    require(any(r.get('Action')=='fail' and r.get('Test')==test for r in rows), 'expected test did not fail')
    require(any(r.get('Test')==test and reason in r.get('Output','') for r in rows), 'expected red reason absent')
    require(any(r.get('Action')=='fail' and not r.get('Test') and r.get('Package') for r in rows), 'package failure not reported')

def verify_pool_mapping(info, merged, channel, pool):
    import hashlib
    expected='// BEGIN pinned channel.go\n'+channel+'\n// BEGIN pinned pool.go\n'+pool
    require(merged==expected, 'combined pool source differs from pinned inputs')
    segments=info.get('segments')
    require(isinstance(segments,list) and len(segments)==2, 'two source segments required')
    for entry,name,text,start in zip(segments,('channel.go','pool.go'),(channel,pool),(2,len(channel.splitlines())+4)):
        require(entry.get('file')==name and entry.get('input_first_line')==start and entry.get('lines')==len(text.splitlines()), 'bad source line mapping')
        if 'sha256' in entry: require(entry['sha256']==hashlib.sha256(text.encode()).hexdigest(), 'source hash mismatch')
    if 'input_sha256' in info: require(info['input_sha256']==hashlib.sha256(merged.encode()).hexdigest(), 'combined source hash mismatch')

def verify_trial_coverage(calls,trials,order):
    require(isinstance(calls,list) and isinstance(trials,list) and len(trials)==len(order), 'trial count mismatch')
    require([t.get('component') for t in trials]==order, 'trial order mismatch')
    require([c.get('id') for c in calls]==list(range(len(calls))), 'missing or reordered call IDs')
    seen=[]
    for trial in trials:
        ids=trial.get('call_ids')
        require(isinstance(ids,list) and 1<=len(ids)<=2 and all(type(i)is int and 0<=i<len(calls) for i in ids), 'invalid trial call IDs')
        require(all(calls[i].get('component')==trial['component'] and calls[i].get('category')=='fixed-baseline' for i in ids), 'trial/call component mismatch')
        seen.extend(ids)
    require(seen==list(range(len(calls))), 'duplicate, missing or reordered call binding')

def verify_reference_archive(base):
    b=Path(base)/'independent-review'
    specifications=[
        ('gepa-independent-b05-final.jsonl',{'TestBenchmarkWrapperReassignment','TestBenchmarkOutstandingAllow'},5),
        ('gepa-independent-rebinding.jsonl',{'TestIndependentCallerRebinding'},5),
        ('gepa-independent-controls-final.jsonl',{'TestInsideWaitClearsBeforeOutside','TestSignalWithoutHoldingLock','TestDefaultPanicNilRecoverIsNonNil'},5),
        ('gepa-independent-panicnil.jsonl',{'TestWaitGroupGoPanicNilLegacy'},5),
        ('gepa-independent-synctest.jsonl',{'TestWaitGroupSynctestOutsideWait'},5),
        ('gepa-independent-timer-overlap.jsonl',{'TestReference','TestReference/context','TestReference/singleflight','TestReference/timer','TestReference/once'},5),
        ('gepa-independent-pool-p04a.jsonl',{'TestP04aGetWaitsWhileReturnedConnectionIsIdle'},5),
    ]
    total=sum(verify_test_log(b/name,names,count) for name,names,count in specifications)
    verify_expected_red(b/'gepa-independent-pool-control.jsonl','TestP04aGetWaitsWhileReturnedConnectionIsIdle','first Get returned early')
    verify_test_log(Path(base)/'gobreaker-reference.jsonl',{'TestBenchmarkWrapperReassignment','TestTrainingUnchangedWrapper','TestTrainingCallerVariableRebinding'},5)
    return {'independent_test_and_subtest_passes':total,'pool_control':'expected red','gobreaker_controls':'3 tests x 5 pass'}

def verify_prompt_and_events(expected, recorded, events):
    require(expected==recorded, 'recorded task prompt differs from source-only input')
    forbidden={'command_execution','mcp_tool_call','web_search','file_change'}
    require(not any(e.get('item',{}).get('type') in forbidden for e in events), 'forbidden task-model event')

def verify_archive(root):
    import hashlib
    from collections import defaultdict
    from gepa_discovery_eval import audit
    from gepa_training_catalog import validate_catalog, validate_independent_review, build_prompt
    from pilot_accounting import cost_report
    from run_gepa_discovery import TASK
    from run_gepa_training_baseline import IDS, ORDER
    root=Path(root).resolve();base=root/'docs/evidence/gepa-training-catalog';run=base/'runs'
    read=lambda p:json.loads(p.read_text())
    catalog=read(base/'catalog.json'); validate_catalog(catalog,root,IDS)
    review=read(base/'independent-review/review.json');validate_independent_review(catalog,review)
    references=verify_reference_archive(base)
    pool=base/'pool-source';verify_pool_mapping(read(pool/'input-map.json'),(pool/'pool-input.txt').read_text(),(pool/'channel.go').read_text(),(pool/'pool.go').read_text())
    files={base/'catalog.json',base/'protocol.md',base/'independent-review/review.json',pool/'input-map.json',root/'docs/evidence/gepa-discovery/fixed.md',root/'tools/gepa_training_catalog.py',root/'tools/run_gepa_training_baseline.py',root/'tools/run_gepa_discovery.py',root/'tools/gepa_discovery_eval.py',root/'tools/run_gepa_comparison.py'}
    for component in catalog['components'].values():
        files.add(root/component['source'])
        for case in component['cases']:
            for anchor in case['evidence']: files.add(root/anchor['file'])
    frozen=read(run/'input-freeze.json')
    expected={str(p.relative_to(root)) for p in files}
    require(set(frozen)==expected,'frozen input inventory mismatch')
    for name,digest in frozen.items():require(hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,'frozen input hash mismatch: '+name)
    status=read(run/'status.json');trials=read(run/'trials.json');calls=read(run/'calls.json')
    require(status=={'status':'complete','calls':10,'trials':10},'baseline not complete or unexpected repairs')
    verify_trial_coverage(calls,trials,ORDER)
    fixed=(root/'docs/evidence/gepa-discovery/fixed.md').read_text()
    scores=defaultdict(list); results=[]; total_cost=0.0
    for trial in trials:
        ids=trial['call_ids'];require(len(ids)==1,'unexpected repair; retained run needs explicit support')
        c=calls[ids[0]];require(c.get('attempt')==0 and c.get('structural_valid') is True and c.get('failure') is None,'failed or unvalidated call')
        dest=run/c['directory'];component=catalog['components'][trial['component']];source=(root/component['source']).read_text()
        expected_prompt=build_prompt(source,fixed,TASK);recorded=(dest/'prompt.md').read_text()
        events=[json.loads(x) for x in (dest/'events.jsonl').read_text().splitlines()]
        verify_prompt_and_events(expected_prompt,recorded,events)
        require(hashlib.sha256(expected_prompt.encode()).hexdigest()==trial['prompt_sha256'],'prompt hash mismatch')
        computed_cost=cost_report(read(dest/'usage-checkpoint.json'),{'charged_microdollars':0,'reserved_microdollars':0},'gpt-6.1-sol')
        require(computed_cost['complete'] and c['cost']['complete'] and computed_cost['total_usd_estimate']==c['cost']['total_usd_estimate'],'unsettled or altered call cost')
        total_cost+=computed_cost['total_usd_estimate']
        report=read(dest/'validated.json');require(len(report['findings'])==trial['finding_count'],'finding count mismatch')
        assessment=read(run/f"review-{ids[0]:03}.json");summary=audit(report,source,component['cases'],assessment)
        require('independent_review' in assessment['reviewer'],'separate reviewer attribution required')
        for row in assessment['cases']:
            partial=row.get('partial',False)
            require(type(partial)is bool and not (partial and row['finding_ids']),'invalid partial marker')
            state='found' if row['finding_ids'] else ('partial' if partial else 'missing')
            scores[row['id']].append(state)
        results.append({'call':ids[0],'component':trial['component'],'found':summary['found'],'total':summary['total'],'false':summary['false'],'uncertain':summary['uncertain']})
    calculated={'catalog_cases':len(IDS),'reviewed_outputs':len(results),'findings_reviewed':sum(t['finding_count'] for t in trials),'case_results':dict(scores),'outputs':results,'reference_checks':references,'model_cost_equivalent_usd':total_cost,'limitations':['two repetitions per component','separate AI review, no independent human review','training/regression cases, not held out','semantic grades are attributed judgments']}
    require(read(run/'assessment.json')==calculated,'archived assessment differs from replay')
    return calculated

if __name__=='__main__':
    import sys
    print(json.dumps(verify_archive(Path(__file__).resolve().parents[1]),indent=2))
