"""Retain and measure bounded runs; all semantic scoring remains an explicit review."""
from collections import Counter
import hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'tools'))
from pilot_accounting import cost_report
HERE=Path(__file__).resolve().parents[1]

def read(p):return json.loads(p.read_text())
def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def collect(root):
    settings=read(root/'experiment.json')
    events=[json.loads(s) for s in (root/'events.jsonl').read_text().splitlines()]
    completed=[e['usage'] for e in events if e.get('type')=='turn.completed']
    checkpoint=read(root/'usage-checkpoint.json'); ledger=read(root/'routing-cost.json')
    cost=read(root/'cost-estimate.json')
    assert cost==cost_report(checkpoint,ledger,'gpt-6.1-sol'), 'cost report drift'
    if cost['complete']:
        assert len(completed)==1 and completed[0]==checkpoint['usage']==read(root/'usage.json')
        assert ledger['reserved_microdollars']==0
    else:assert cost['total_usd_estimate'] is None
    calls=[e['item'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='mcp_tool_call']
    commands=[]
    for path in sorted((root/'logs').glob('*.json')):
        value=read(path)
        if 'exit_code' in value:commands.append(dict(log=path.stem,**value))
    initial=read(root/'pool/analysis/initial.json') if (root/'pool/analysis/initial.json').is_file() else None
    final=read(root/'pool/analysis/final.json') if (root/'pool/analysis/final.json').is_file() else None
    changes=None
    if initial and final:
        before={r['id']:r for r in initial['findings']};after={r['id']:r for r in final['findings']}
        # Edits are not automatically errors: provenance/test upgrades are expected.
        changes={'initial':len(before),'final':len(after),'added':sorted(after.keys()-before.keys()),
                 'removed':sorted(before.keys()-after.keys()),
                 'changed_fields':{k:[f for f in after[k] if after[k].get(f)!=before[k].get(f)] for k in before.keys()&after.keys() if before[k]!=after[k]}}
    source='gobreaker.go' if settings['component']=='gobreaker' else 'component.go'
    assert hashfile(root/'pool'/source)==settings['source_sha256'],'source changed'
    assert subprocess.run(['git','diff','--exit-code'],cwd=root/'pool',capture_output=True).returncode==0,'tracked source changed'
    validation=subprocess.run([sys.executable,str(HERE/'scripts/validate_report.py'),'analysis/initial.json','analysis/final.json'],cwd=root/'pool',capture_output=True,text=True)
    probe_runs = []
    for path in sorted((root/'pool/analysis').rglob('*.jsonl')):
        records = []
        for line in path.read_text().splitlines():
            try: record=json.loads(line)
            except json.JSONDecodeError: continue
            if isinstance(record,dict) and record.get('Action') in ('run','pass','fail','skip'):
                records.append(record)
        if not records: continue
        started=Counter(r['Test'] for r in records if r.get('Action')=='run' and 'Test' in r)
        passed=Counter(r['Test'] for r in records if r.get('Action')=='pass' and 'Test' in r)
        failed=Counter(r['Test'] for r in records if r.get('Action')=='fail' and 'Test' in r)
        skipped=[r.get('Test') for r in records if r.get('Action')=='skip']
        probe_runs.append({'file':str(path.relative_to(root/'pool')), 'started':dict(started),
                           'passed':dict(passed),'failed':dict(failed),'skipped':skipped,
                           'complete_nonempty':bool(started) and started==passed+failed and not skipped})
    model_review = {}
    for path in sorted((root/'pool/analysis').glob('*.json')):
        payload=read(path)
        if isinstance(payload,dict) and ('checks' in payload or ('draft' in payload and 'verification' in payload)):
            model_review[path.name]={'keys':list(payload), 'counts':dict(Counter(c.get('choice','missing') for c in payload.get('checks',{}).values())),
                                    'draft_judgments':dict(Counter(c.get('jev',{}).get('choice','missing') for c in payload.get('claims',{}).values())),
                                    'questions':len(payload.get('questions',[])),
                                    'claims':len(payload.get('claims',{}))}
    probe_gate=bool(probe_runs) and probe_runs[-1]['complete_nonempty'] and not probe_runs[-1]['failed'] and all(n==3 for n in probe_runs[-1]['passed'].values())
    result={'settings':settings,'cost':cost,'result':read(root/'result.json') if (root/'result.json').exists() else None,
            'controller_complete':len(completed)==1,'probe_gate':probe_gate,'bounded_acceptance':len(completed)==1 and validation.returncode==0 and probe_gate and cost['complete'],'structure_gate':{'exit':validation.returncode,'stdout':validation.stdout,'stderr':validation.stderr},
            'source_unchanged':True,'validator_sha256':hashfile(root/'pool/validate_report.py'),'tool_calls':len(calls),'commands':len(commands),
            'log_rereads':sum(c['arguments']['argv'][0]=='read-log' for c in calls),
            'nonzero_commands':[c for c in commands if c['exit_code']],
            'mcp_errors':[c['id'] for c in calls if c.get('error') or c.get('status')=='failed'],
            'report_edits':changes,'model_review':model_review,'probe_runs':probe_runs}
    return result

def matched(a,b,pa,pb):
    if {k:v for k,v in a.items() if k not in ('variant','prompt_sha256')}!={k:v for k,v in b.items() if k not in ('variant','prompt_sha256')}:
        raise ValueError('unmatched input/settings')
    delta=(HERE/'prompts/candidate.md').read_text()
    if pb.replace(delta,'',1)!=pa or pb.count(delta)!=1:raise ValueError('unexpected prompt difference')

if __name__=='__main__':
    root=Path(sys.argv[1]);dest=HERE/'runs'
    if dest.exists():raise SystemExit('refuse to overwrite retained runs')
    dest.mkdir();rows={}
    for component in ('gobreaker','transfer'):
        for variant in ('baseline','candidate'):
            name=component+'-'+variant;src=root/name
            rows[name]=collect(src)
            target=dest/name;target.mkdir()
            for path in src.iterdir():
                if path.is_file() and path.suffix in ('.json','.jsonl','.md','.txt','.stderr'):
                    shutil.copyfile(path,target/path.name)
            shutil.copytree(src/'logs',target/'logs')
            shutil.copytree(src/'pool/analysis',target/'analysis')
            (target/'input').mkdir()
            for file in ('gobreaker.go','component.go','README.md','go.mod','go.sum','LICENSE','validate_report.py'):
                if (src/'pool'/file).exists():shutil.copyfile(src/'pool'/file,target/'input'/file)
            hashes={str(p.relative_to(target)):hashfile(p) for p in sorted(target.rglob('*')) if p.is_file()}
            (target/'hashes.json').write_text(json.dumps(hashes,indent=2)+'\n')
        baseline=root/(component+'-baseline');candidate=root/(component+'-candidate')
        assert rows[baseline.name]['validator_sha256']==rows[candidate.name]['validator_sha256'], 'validator changed between arms'
        a=rows[baseline.name]['settings'];b=rows[candidate.name]['settings']
        matched(a,b,(baseline/'prompt.md').read_text(),(candidate/'prompt.md').read_text())
        bad={**b,'source_sha256':'different'}
        try:matched(a,bad,(baseline/'prompt.md').read_text(),(candidate/'prompt.md').read_text())
        except ValueError:pass
        else:raise AssertionError('mismatched-input negative probe passed')
    (HERE/'measurements.json').write_text(json.dumps(rows,indent=2)+'\n')
    for name,row in rows.items():
        print(name, 'cost',row['cost']['total_usd_estimate'],'rereads',row['log_rereads'],'failed commands',len(row['nonzero_commands']),'MCP errors',len(row['mcp_errors']))
    print('Identical settings/input and exact candidate-only prompt delta: PASS; changed-source red probe rejected')
