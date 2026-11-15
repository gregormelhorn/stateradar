#!/usr/bin/env python3
"""Validate reviewed late-completion applicability and replay execution evidence.

Completeness is relative to the declared inventory, not inferred from source.
The Go reader checks recorded execution, not authenticity of arbitrary producers.
Decision files in v1 use the pack's JSON-compatible YAML representation.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from late_completion import EvidenceError, evaluate, validate_profile
from gen_mutant_variants import find_block

FACTS = {'terminal', 'ownedIdleResource', 'noLateEffects', 'exactRelease'}
CAUSES = {'terminal':'terminal state violated', 'publication':'publication after termination',
          'effect':'effect emitted after termination', 'resource':'resource not released exactly once'}
INPUTS = {'profile','mutants','generation','adapter','probe','oracle','patch'}


def require(condition, message):
    if not condition: raise EvidenceError(message)


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def resolve(root, name):
    require(isinstance(name,str) and bool(name), 'missing path')
    path=(root/name).resolve()
    require(path.is_relative_to(root.resolve()),'path escapes evidence/repository root')
    return path


def check_plan(path, root):
    root=root.resolve(); path=path.resolve();plan=read(path)
    require(plan.get('formatVersion')==1,'unsupported workflow version')
    scope_path=resolve(root,plan['scope']);scope=read(scope_path)
    require(scope.get('formatVersion')==1 and scope.get('boundary') and scope.get('coverage') in ('scenario-slice','matrix'),'explicit scope boundary required')
    traces=scope['traces'];rows=plan['rows']
    require(bool(traces),'empty scope inventory')
    by_trace={t['id']:t for t in traces}
    require(len(by_trace)==len(traces) and Counter(r['trace'] for r in rows)==Counter(by_trace.keys()),'scope coverage must be exactly once')
    paths={path,scope_path};applicable=[];counts=Counter()
    for row in rows:
        t=by_trace[row['trace']];facts=t['contract']
        require(set(facts)==FACTS and all(type(v) is bool or v=='unknown' for v in facts.values()),'invalid contract facts')
        require(type(t['seamsAvailable']) is bool,'invalid seam availability')
        status=('not-applicable' if False in facts.values() else 'blocked' if 'unknown' in facts.values() or not t['seamsAvailable'] else 'applicable')
        require(row.get('status')==status,'applicability contradicts reviewed contract/seams')
        require(isinstance(row.get('reason'),str) and row['reason'].strip(),'applicability reason required')
        require(t.get('citations'),'source-grounded applicability citation required')
        for c in t['citations']:
            source=resolve(root,c['file']);paths.add(source);lines=source.read_text().splitlines()
            require(type(c['line']) is int and 1<=c['line']<=len(lines) and isinstance(c['fragment'],str) and c['fragment'].strip()
                    and any(c['fragment'] in s for s in lines[max(0,c['line']-4):c['line']+3])
                    and c.get('provenance') in ('explicit-requirement','observed-in-code','observed-in-tests','inferred','proposed'),'invalid applicability citation')
        if 'unknown' in facts.values():
            q=row.get('question',{})
            require(isinstance(q,dict) and q.get('id','').startswith('Q-') and q.get('status')=='OPEN' and q.get('text'),'unknown semantics require OPEN question')
        if status=='applicable':applicable.append((row,t))
        else:require('profileCase' not in row,'excluded/blocked row cannot claim a profile case')
        counts[status]+=1
    result={'plan':plan,'paths':paths,'applicable':len(applicable),'counts':dict(counts)}
    if not applicable:
        require('inputs' not in plan and 'execution' not in plan,'no executable profile for zero applicable scenarios')
        return result
    require(set(plan['inputs'])==INPUTS,'required workflow inputs incomplete')
    inputs={k:resolve(root,v) for k,v in plan['inputs'].items()};paths.update(inputs.values())
    profile=read(inputs['profile']);cases=validate_profile(profile);by_case={c['id']:c for c in cases}
    require(Counter(r['profileCase'] for r,t in applicable)==Counter(by_case.keys()),'profile case coverage must be exactly once')
    decision=(inputs['profile'].parent/profile['decision']).resolve()
    require(decision.is_relative_to(root),'decision outside repository')
    record=read(decision);paths.add(decision)
    require(record.get('status')=='accepted' and str(record.get('id','')).startswith('DR-'),'accepted decision required')
    for row,t in applicable:
        c=by_case[row['profileCase']]
        require(c['cell']==t['cell'] and c['order']==t['order'],'scope/profile cell/order mismatch')
        require(resolve(root,t['decision'])==decision,'scope/profile decision mismatch')
    config=read(inputs['mutants']);generation=read(inputs['generation'])
    mutants=config['mutants'];bindings=generation['bindings'];projections=generation['projections']
    require(config['expectedCells']==len(cases),'mutant suite cell count mismatch')
    require(set(projections)==set(CAUSES),'four projections with independent canaries required')
    by_id={m['id']:m for m in mutants};by_binding={b['id']:b for b in bindings}
    require(len(by_id)==len(mutants) and len(by_binding)==len(bindings) and set(by_id)==set(by_binding),'mutant binding coverage')
    canaries={k:v['provenBy'] for k,v in projections.items()}
    require(len(set(canaries.values()))==4 and set(canaries.values())<set(by_id),'four distinct canaries and behavioral mutants required')
    cells={c['cell'] for c in cases}
    for name,m in by_id.items():
        b=by_binding[name]
        require(m['cell'] in cells and b['cell']==m['cell'] and b['variant']==m['variant'],'mutant cell/variant mismatch')
        require(b['requiresProjection'] in projections,'unknown projection')
        seen=set();cursor=name
        while True:
            require(cursor not in seen,'cyclic canary prerequisites')
            seen.add(cursor);dep=canaries[by_binding[cursor]['requiresProjection']]
            require(dep in by_binding,'missing canary')
            if dep==cursor:break
            cursor=dep
        if name not in canaries.values():require(set(canaries.values())<=seen,'all four canary prerequisites required')
    execution=plan['execution']
    require(execution['reader']=='go-json-v1' and bool(execution['testRoot']),'unsupported execution reader')
    require(set(execution['counts'])=={'baseline','full','weak'} and all(type(n) is int and n>0 for n in execution['counts'].values()),'positive exact execution counts required')
    require(len(execution['sourceSha256'])==64,'pinned upstream source required')
    result.update(inputs=inputs,profile=profile,mutants=mutants,generation=generation,canaries=canaries)
    return result


def input_hashes(checked, root):
    hashes={str(p.relative_to(root.resolve())):sha(p) for p in sorted(checked['paths'])}
    hashes['$checker']=sha(Path(__file__).resolve())
    hashes['$generator']=sha(Path(__file__).resolve().with_name('gen_mutant_variants.py'))
    return hashes


def write_receipt(plan_path, root, output):
    checked=check_plan(plan_path,root)
    (output/'workflow-receipt.json').write_text(json.dumps({'formatVersion':1,'inputs':input_hashes(checked,root)},indent=2)+'\n')


def execution_traces(folder, checked, count, source_hash, weak):
    inputs=checked['inputs'];profile=checked['profile'];execution=checked['plan']['execution']
    meta=read(folder/'execution.json')
    expected={'formatVersion':1,'count':count,'weak':weak,'sourceSha256':source_hash,
              'profileSha256':sha(inputs['profile']),'adapterSha256':sha(inputs['adapter']),
              'probeSha256':sha(inputs['probe']),'oracleSha256':sha(inputs['oracle']),
              'goSha256':sha(folder/'go.jsonl'),'observationsSha256':sha(folder/'observations.json'),'goExit':0}
    require(meta==expected,'execution receipt mismatch/stale inputs')
    records=[json.loads(l) for l in (folder/'go.jsonl').read_text().splitlines() if l.startswith('{')]
    root=execution['testRoot'];wanted=Counter({root:1})
    wanted.update({f"{root}/{c['id']}/{r}":1 for c in profile['cases'] for r in range(count)})
    for action in ('run','pass'):
        require(Counter(r['Test'] for r in records if r.get('Action')==action and 'Test' in r)==wanted,'incomplete Go test discovery')
    require(not any(r.get('Action') in ('fail','skip') for r in records) and sum(r.get('Action')=='pass' and 'Test' not in r for r in records)==1,'failed/incomplete Go package execution')
    text=''.join(r.get('Output','') for r in records)
    raw=[json.loads(l[len('LATE TRACE '):]) for l in text.splitlines() if l.startswith('LATE TRACE ')]
    traces=read(folder/'observations.json')
    require(raw==traces,'raw execution/observation mismatch')
    evaluate(profile,traces,count,weak=weak) # structural validation even before verdict checks
    return traces


def replace_once(source, old, new):
    require(bool(old) and source.count(old)==1,'missing/ambiguous source binding')
    return source.replace(old,new)


def check_execution(checked, root, output):
    require(checked['applicable']>0,'no applicable scenarios: no execution claim')
    receipt=read(output/'workflow-receipt.json')
    require(receipt=={'formatVersion':1,'inputs':input_hashes(checked,root)},'stale workflow inputs')
    source=(output/'upstream-source.go.txt').read_text()
    execution=checked['plan']['execution'];counts=execution['counts'];profile=checked['profile']
    require(digest(source)==execution['sourceSha256'],'upstream source pin mismatch')
    for edit in read(checked['inputs']['patch'])['edits']:source=replace_once(source,edit['match'],edit['replace'])
    traces=execution_traces(output/'evaluation',checked,counts['baseline'],digest(source),False)
    require(not evaluate(profile,traces,counts['baseline']),'baseline behavioral failure')
    by_binding={b['id']:b for b in checked['generation']['bindings']}
    causes={name:CAUSES[k] for k,name in checked['canaries'].items()}
    for m in checked['mutants']:
        b=by_binding[m['id']]
        lines=source.splitlines(keepends=True)
        start,end=find_block([line.removesuffix('\n') for line in lines],b['match'])
        variant=''.join(lines[:start]+[line+'\n' for line in b['replace']]+lines[end:])
        folder=output/m['id'];count=counts['full']
        traces=execution_traces(folder,checked,count,digest(variant),False)
        for repeat in range(count):
            subset=[dict(t,repeat=0) for t in traces if t['repeat']==repeat]
            failed=evaluate(profile,subset,1)
            require(m['cell'] in failed,'mutant target not killed in every repetition')
            if m['id'] in causes:
                reasons={r.split(': ',1)[1] for rs in failed.values() for r in rs}
                require(set(failed)=={m['cell']} and reasons=={causes[m['id']]},'canary projection not independently isolated')
        weak=execution_traces(folder/'weak',checked,counts['weak'],digest(variant),True)
        require(not evaluate(profile,weak,counts['weak'],weak=True),'weak suite did not survive')
    return len(checked['mutants'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('plan',type=Path)
    p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--evidence',type=Path)
    a=p.parse_args()
    try:
        checked=check_plan(a.plan,a.repo)
        print('LATE PLAN: '+json.dumps(checked['counts'],sort_keys=True)+'; declared scope only')
        if a.evidence:
            n=check_execution(checked,a.repo,a.evidence)
            print(f'LATE EXECUTION PASS: baseline, {n} full/weak variants, 4 independent canaries; exact repetitions and Go discovery')
        else:print('PLAN ONLY: no execution claim')
        return 0
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print('BLOCKED: '+str(exc));return 2

if __name__=='__main__':sys.exit(main())
