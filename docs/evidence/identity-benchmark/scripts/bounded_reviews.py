"""Explicit post-run review mappings; no keyword-based semantic grading."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parents[1]

def anchor(path,line):
    lines=path.read_text().splitlines()
    return {'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'line':line,'quote':lines[line-1]}

def find(path,needle):
    return anchor(path,next(i for i,line in enumerate(path.read_text().splitlines(),1) if needle in line))

def finding(path,ident):
    active=False
    for i,line in enumerate(path.read_text().splitlines(),1):
        if '"id":' in line:active=json.loads('{'+line.strip().rstrip(',')+'}')['id']==ident
        if active and '"outcome":' in line:return anchor(path,i)
    raise ValueError(ident)

mappings={
'baseline':[['F07','F08'],['F02'],['F03','F04','F05'],['F20'],['F22'],['F06'],['F12'],['F10']],
'candidate':[['F04','F21'],['F10'],['F11'],['F22'],['F01'],['F12'],['F16'],['F15']]}
for variant,ids in mappings.items():
    run=HERE/'runs'/('gobreaker-'+variant);report=run/'analysis/final.json'
    final={r['id']:r for r in json.loads(report.read_text())['findings']}
    replay=HERE/'results'/f'gobreaker-{variant}-final.jsonl'
    rows=[]
    for i,identifiers in enumerate(ids,1):
        ident=f'B{i:02}'
        evidence=[finding(report,f) for f in identifiers]
        test=final[identifiers[0]]['test']
        found=not (variant=='candidate' and ident=='B06')
        tested='none' if test=='untested' or not found else 'full'
        rationale='The final report explicitly preserves the condition, order and observable consequence; linked probe assertions were reviewed.'
        if ident=='B04':rationale='The lock/reentry mechanism is correctly retained as a source-only finding; no reentry probe was executed in this bounded session.'
        if variant=='candidate' and ident=='B01':
            tested='partial'
            evidence.append(find(run/'analysis/summary.md','A stale report can run expiry and notification'))
            rationale='The summary explicitly retains expiry/notification before stale discard. F04 executes it with wrapper replacement; F21 uses the original breaker but a panicking notification. Neither is the complete ordinary same-instance reference schedule. This is retained behavior with narrower/different executable coverage, not a missing finding.'
        if variant=='candidate' and ident=='B06':
            rationale='F12 admits two callbacks but reports FAILURE first, opening a new generation. It does not trace first SUCCESS, retained Requests=2, third refusal and second success closing. Generic cumulative-count claims C8/C9 do not supply that concrete sequence. This is a missing benchmark case, not a falsely reported runtime outcome.'
            evidence.append(find(run/'analysis/review.md','**C8**'))
        test_evidence=[]
        if tested!='none':
            probes=[p for p in (run/'analysis').rglob('*.go') if f'func {test}(' in p.read_text()]
            assert len(probes)==1
            test_evidence=[find(probes[0],f'func {test}('),find(replay,'"Action":"pass","Package":"github.com/sony/gobreaker","Test":"'+test+'"')]
        rows.append({'id':ident,'found':found,'correct':found,'tested':tested,'test_name':test if tested!='none' else None,
                     'rationale':rationale,'evidence':evidence,'test_evidence':test_evidence})
    value={'reviewer':'Codex supervising agent; final reports and probe bodies reviewed 2026-11-14',
           'scope':'Bounded final reports only. Scores cover eight predeclared cases, not every claim in the component. Independent replay supplies execution evidence, not new findings. No domain intent is decided.',
           'rows':rows,'refuted_claims':[]}
    (HERE/f'bounded-{variant}-review.json').write_text(json.dumps(value,indent=2)+'\n')

expected=json.loads((HERE/'fixtures/transfer/expected.json').read_text())
cases=[]
for method,item in expected.items():
    cases.append({'id':'T-'+method,'title':'Deferred recipient for '+method,
                  'initial':'Two distinct accounts; canonical zero counters and the epochs specified in the retained scenario.',
                  'steps':item['steps'].split('; '),'outcome':json.dumps({k:v for k,v in item.items() if k!='steps'}),
                  'proof':[find(HERE/'fixtures/transfer/oracle_test.go.txt','case "'+method+'":'),
                           find(HERE/'results/transfer-proof.jsonl','"Action":"pass","Package":"identityfixture","Test":"TestTransferOracle/'+method+'"')]})
(HERE/'transfer-benchmark.json').write_text(json.dumps({'cases':cases,'scope':'Two redirection positives and four no-redirection controls. The frozen expected.json retains canonical example values; review may use the same identity/equality guard class and effect deltas, with differences explicit.'},indent=2)+'\n')
transfer_ids={'baseline':dict(zip('ABCDEF',['F07','F08','F09','F10','F11','F12'])),
              'candidate':dict(zip('ABCDEF',['F02','F09','F16','F22','F10','F11']))}
for variant,mapping in transfer_ids.items():
    run=HERE/'runs'/('transfer-'+variant);report=run/'analysis/final.json'
    final={r['id']:r for r in json.loads(report.read_text())['findings']}
    replay=HERE/'results'/f'transfer-{variant}-final.jsonl'
    rows=[]
    for method,ident in mapping.items():
        test=final[ident]['test'];parent=test.split('/')[0]
        probes=[p for p in (run/'analysis').rglob('*.go') if f'func {parent}(' in p.read_text()]
        assert len(probes)==1
        rationale='The reported recipient and success effect match the frozen control. Probe uses the same identity/equality guard class; chosen epoch values do not introduce a different source branch.'
        tested='full'
        if method=='C' and variant=='candidate':
            rationale+=' The replacement is an account-value copy, so Requests starts at one rather than zero; no success is added to either object. The counter starting value is not a guard. The independent canonical oracle separately checks a new zero-counter replacement.'
        if method=='F':
            tested='partial'
            rationale='The report explicitly retains F as a stable captured-target completion, correctly excluding redirection after a stronger mutation of the original Port.Target. The generated probe does not separately execute caller-variable rebinding from the canonical F control. Recipient-class coverage is retained, exact-sequence test coverage is partial. No claim that the generated probe ran that missing schedule.'
        rows.append({'id':'T-'+method,'found':True,'correct':True,'tested':tested,'test_name':test,
                     'rationale':rationale,'evidence':[finding(report,ident)],
                     'test_evidence':[find(probes[0],f'func {parent}('),find(replay,'"Action":"pass","Package":"identityfixture","Test":"'+test+'"')]})
    value={'reviewer':'Codex supervising agent, final reports and generated public-seam probes reviewed 2026-11-14',
           'scope':'Recipient/effect classes for six untuned synthetic controls, including two redirection positives. Four no-redirection classes have no false redirection claim in the mapped final findings. No universal false-positive rate or independent held-out result is claimed. Canonical F sequence remains unexecuted by either generated suite.',
           'rows':rows,'refuted_claims':[]}
    (HERE/f'transfer-{variant}-review.json').write_text(json.dumps(value,indent=2)+'\n')
