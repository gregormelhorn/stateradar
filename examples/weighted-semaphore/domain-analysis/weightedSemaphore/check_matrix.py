"""Check matrix/sidecar/coverage equality and all active fragment anchors."""
import argparse
import copy
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
EXCLUDED={'UV-Delay','UV-ContextFault'}


def render(model):
    out=['# Disposition matrix','', '<!-- states: '+ ' '.join(model['states'])+' -->', '',
         'Abstraction: queue projection at mutex-release boundaries. Each primary disposition describes the representative guarded scenario in cells/state_cells_test.go.txt. Guarded alternatives in the notes are part of the contract and covered by the mandatory decision/scenario suites. This is not an unconditional outcome table for every argument.', '']
    events=[e['id'] for e in model['events']]
    by={(c['state'],c['event']):c for c in model['cells']}
    for offset in range(0,len(events),5):
        chunk=events[offset:offset+5]
        out+=['| State | '+' | '.join(chunk)+' |','|---|'+'---|'*len(chunk)]
        for state in model['states']:
            cells=[]
            for event in chunk:
                c=by[state,event]; d=c['disposition']
                if d=='transition':d+=' → '+c['target']
                cells.append(d+' ('+c['dr']+')')
            out+=['| **'+state+'** | '+' | '.join(cells)+' |']
        out+=['']
    out+=['## Guarded cell notes and evidence','']
    for c in model['cells']:
        cite=c['citation']
        out += ['### '+c['state']+' × '+c['event'], '', c['note'], '',
                'Authority: '+c['dr']+'; resolved '+c['q']+'. Provenance: '+c['provenance']+'.', '',
                f'{cite["file"]}:{cite["line"]} ("{cite["fragment"]}")', '']
    return '\n'.join(out)


def citations(obj):
    if isinstance(obj,dict):
        if {'file','line','fragment'}<=obj.keys():yield obj
        else:
            for v in obj.values():yield from citations(v)
    elif isinstance(obj,list):
        for v in obj:yield from citations(v)


def validate(model,coverage,scenarios,matrix,root=ROOT):
    def require(ok,message):
        if not ok:raise ValueError(message)
    states=model['states']; events=[e['id'] for e in model['events']]
    require(len(states)==2 and len(events)==19,'state/event discovery drift')
    keys={(s,e) for s in states for e in events}
    cells={(c['state'],c['event']):c for c in model['cells']}
    cov={(c['state'],c['event']):c for c in coverage['cells']}
    require(len(model['cells'])==len(coverage['cells'])==38 and set(cells)==set(cov)==keys,'38-cell totality/coverage')
    require(matrix==render(model),'matrix text differs from sidecar')
    require({c['dr'] for c in cells.values()}==set(model['behaviouralDrs']) and len(model['behaviouralDrs'])==13,'DR reverse coverage')
    require(len(model['questions'])==13 and all(q['status']=='RESOLVED' for q in model['questions']),'question register drift')
    for key,c in cells.items():
        cv=cov[key]
        require(all(cv[k]==c[k] for k in ('dr','disposition')),'coverage authority/outcome mismatch: '+str(key))
        if c['event'] in EXCLUDED:
            require('test' not in cv and len(cv.get('untestable-via-seam',''))>40,'invalid contract-limit entry')
        else:
            require(cv.get('test')=='TestStateCells/'+c['state']+'/'+c['event'] and 'untestable-via-seam' not in cv,'missing/misnamed executable cell')
    expected={f'P-{i:02}{order}' for i in range(1,9) for order in 'ab'}|{f'T-{i:02}' for i in range(1,15)}
    traces=scenarios['traces']
    require(len(traces)==30 and {t['id'] for t in traces}==expected,'trace consolidation dropped or duplicated an identity')
    for t in traces:
        if t['id'] in ('T-08','T-09'):
            require(t.get('untestable-via-seam','').startswith('DR-009'),'unsupported Context trace asserted as pass')
        else:
            require(t.get('test') and t['test'].split('/')[0] in t['testCitation']['fragment'],'missing scenario anchor')
    require({d['dr'] for d in model['decisionEvidence']}==set(model['behaviouralDrs']) and len(model['decisionEvidence'])==13,'missing per-decision implementation evidence')
    for dr in model['behaviouralDrs']:
        text=(HERE/'decisions'/f'{dr}.yaml').read_text()
        canonical=re.search(r'^canonical_record: (.+)$',text,re.M)
        require(canonical is not None,'canonical owner record absent')
        path=root/canonical.group(1)
        original=path.read_text()
        evidence=re.search(r'^implementation_evidence: (.+)$',original,re.M)
        if evidence:
            resolved=(path.parent/evidence.group(1)).resolve().relative_to(root)
            original=original.replace(evidence.group(0),'implementation_evidence: '+str(resolved))
        require(text==original+'\ncanonical_record: '+canonical.group(1)+'\n','decision attribution or scope differs from accepted record: '+dr)
    count=0
    for c in citations([model,scenarios]):
        path=root/c['file']; require(path.is_file(),'citation file absent: '+str(path))
        lines=path.read_text().splitlines(); line=c['line']
        require(c['fragment'] and any(c['fragment'] in x for x in lines[max(0,line-4):line+3]),'broken fragment: '+str(c))
        count+=1
    # Coverage n/a prose citations are validated too, not only the matrix anchors.
    for categories in model['coverage'].values():
        for value in categories.values():
            for file,line,fragment in re.findall(r'([\w./-]+):([0-9]+) \("([^\n]+?)"\)',value):
                lines=(root/file).read_text().splitlines()
                require(any(fragment in x for x in lines[max(0,int(line)-4):int(line)+3]),'coverage fragment drift')
                count+=1
    return count


def run(adir=HERE, selftest=False):
    model=json.loads((adir/'analysis.json').read_text())
    coverage=json.loads((adir/'matrix-coverage.json').read_text())
    scenarios=json.loads((adir/'scenario-coverage.json').read_text())
    matrix=(adir/'disposition-matrix.md').read_text()
    if selftest:
        probes=[('missing DR evidence',lambda m,c,s: m['decisionEvidence'].pop()),
                ('missing cell',lambda m,c,s: m['cells'].pop()),
                ('missing coverage',lambda m,c,s:c['cells'].pop()),
                ('broken fragment',lambda m,c,s:m['cells'][0]['citation'].update(fragment='NONEXISTENT_SOURCE_ANCHOR')),
                ('false exclusion',lambda m,c,s:c['cells'][0].update(test=None,**{'untestable-via-seam':'unsupported'})),
                ('lost trace',lambda m,c,s:s['traces'].pop())]
        for label,mutate in probes:
            mm,cc,ss=copy.deepcopy((model,coverage,scenarios));mutate(mm,cc,ss)
            # Regenerate text where possible: red must survive a synchronized bad model.
            try: text=render(mm)
            except KeyError:text=matrix
            try:validate(mm,cc,ss,text)
            except ValueError as e:print('EXPECTED ARTIFACT RED:',label,'=>',e)
            else:raise SystemExit('red probe unexpectedly passed: '+label)
        try:validate(model,coverage,scenarios,matrix+'unreviewed drift')
        except ValueError as e:print('EXPECTED ARTIFACT RED: text drift =>',e)
        else:raise SystemExit('matrix drift passed')
    count=validate(model,coverage,scenarios,matrix)
    print(f'ARTIFACT PASS: 38 cells; 34 executable; 4 contract limits; 30 traces; 13 resolved DRs; {count} verified fragment citations')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--selftest',action='store_true')
    run(selftest=parser.parse_args().selftest)
