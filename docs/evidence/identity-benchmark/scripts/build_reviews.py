"""Materialize the explicitly reviewed eight-case annotations with exact anchors.

This is not a semantic classifier. Q/test mappings and judgments below are the
reviewer's inputs; absence was assessed by reading the complete retained reports.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parents[1]
OLD=ROOT/'docs/evidence/mutation-rationale-cost/runs'

def evidence(path,needle):
    lines=path.read_text().splitlines()
    matches=[(n,line) for n,line in enumerate(lines,1) if needle in line]
    if not matches:raise ValueError((path,needle))
    n,line=matches[0]
    return {'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'line':n,'quote':line}

def question(path,q):
    lines=path.read_text().splitlines();active=False
    for line in lines:
        if line.startswith('## '):active=line.startswith('## '+q) and (len(line)==len('## '+q) or line[len('## '+q)]==' ')
        if active and line.startswith('**Current behaviour:**'):return evidence(path,line)
    raise ValueError(q)

cases=[
('B01','Stale completion accounting','Open after one current failure; an older callback remains; timeout elapses',['invoke old callback before a new admission','observe notifications and counters'],'Expiry can move Open to HalfOpen, but stale success/failure is not counted','TestPilotExpiryAndStaleReport'),
('B02','Duplicate completion','HalfOpen, MaxRequests=2, one admitted callback',['report true','report true again'],'The same callback closes HalfOpen without two distinct admissions','TestPilotDuplicateDone'),
('B03','Abandoned HalfOpen allowance','HalfOpen, MaxRequests=1, admitted callback retained',['omit completion','attempt additional admissions','deliver a late outcome'],'Further admissions are refused without autonomous recovery; late success/failure can close/reopen','TestPilotAbandonAndLateReport'),
('B04','Callback reentry','ReadyToTrip or OnStateChange executes under the breaker mutex',['callback enters Counts or State','observe bounded nonreturn'],'Same-breaker locking reentry blocks; source lock establishes the mechanism beyond the finite probe','TestPilotCallbackReentry'),
('B05','Serialized wrapper reassignment','Two new wrappers a and b with matching initial generation',['done=a.Allow()','*a=*b','done(true)'],'b.Counts has Requests=0 and TotalSuccesses=1; closure dereferences the changed wrapper','TestBenchmarkWrapperReassignment'),
('B06','Two outstanding Allow calls below budget','HalfOpen, MaxRequests=2',['admit first and second','report first true','attempt third admission','report second true'],'Requests stays 2 after first success; third refused; second distinct success closes','TestBenchmarkOutstandingAllow'),
('B07','Classifier panic','Closed with a classifier that panics; request itself returns normally',['Execute request','classifier panics','recover at caller and read counters'],'Classifier panic propagates through Execute recovery; one failure is recorded','TestPilotCallbackPanics'),
('B08','Stale classification and original return','Execute classifier paused on original error; another execution trips breaker',['let second execution open breaker','resume classifier returning success','observe original return and counts'],'Original value and error are returned; stale classification adds no current-generation success','TestBenchmarkStaleResultAndError')]
rows=[]
for ident,title,initial,steps,outcome,test in cases:
    source=(HERE/'fixtures/additional_test.go.txt') if test.startswith('TestBenchmark') else OLD/'routed/domain-analysis/circuitBreaker/_probe/as_is_test.go'
    rows.append({'id':ident,'title':title,'initial':initial,'steps':steps,'outcome':outcome,
                 'proof':[evidence(source,'func '+test+'('),evidence(HERE/'results/benchmark-proof.jsonl','"Action":"pass","Package":"github.com/sony/gobreaker","Test":"'+test+'"')]})
(HERE/'benchmark.json').write_text(json.dumps({'version':1,'source_sha':'27b8e2cfc65aacd09abb3968455e4b01df4a83fa','scope':'Regression observations, not desired behavior or owner decisions','cases':rows},indent=2)+'\n')
for arm in ('routed','matrix'):
    qpath=OLD/arm/'domain-analysis/circuitBreaker/open-questions.md'
    qs=['Q-09','Q-03','Q-04','Q-01','Q-08','Q-15','Q-07','Q-09'] if arm=='routed' else ['Q-05','Q-03','Q-06','Q-09','Q-17','Q-07','Q-10','Q-05']
    tests=['TestPilotExpiryAndStaleReport','TestPilotDuplicateDone','TestPilotAbandonAndLateReport','TestPilotCallbackReentry',None,None,'TestPilotCallbackPanics','TestPilotStaleClassifierAndReturn'] if arm=='routed' else ['TestPilotStaleReportReconcilesOpen','TestPilotDuplicateAndAbandoned','TestPilotDuplicateAndAbandoned','TestPilotReentryBounded',None,'TestPilotSameOwnerOutstandingBelowBudget',None,None]
    probe=OLD/arm/'domain-analysis/circuitBreaker/_probe'/('as_is_test.go' if arm=='routed' else 'pilot_test.go')
    reviews=[]
    for index,case in enumerate(rows):
        ident=case['id']; test=tests[index]
        rationale='The cited report describes this ordered consequence; grouping into a shared Q does not remove it.'
        anchors=[question(qpath,qs[index])]
        if ident=='B04' and arm=='routed':anchors.append(question(qpath,'Q-02'))
        if arm=='matrix' and ident=='B03':anchors.append(question(qpath,'Q-04'))
        if arm=='matrix' and ident=='B07':
            anchors.append(evidence(OLD/arm/'domain-analysis/circuitBreaker/extraction.md','the recovery scope includes classifier and accounting'))
        if arm=='matrix' and ident=='B08':anchors.append(question(qpath,'Q-16'))
        if ident=='B05':rationale=('The unconditional original-breaker binding claim is too broad; no serialized wrapper assignment trace or resulting counters.' if arm=='routed' else 'Wrapper capture and ordinary copying are discussed, but not serialized assignment through the captured wrapper or the resulting counters.')
        if ident=='B06' and arm=='routed':
            anchors.append(evidence(OLD/arm/'domain-analysis/circuitBreaker/adversarial-traces.md','A single B report consumes one outcome only'))
            anchors.append(question(qpath,'Q-10'))
            rationale='T-06 explicitly retains Requests=2 after one outcome; Q-10 gives refusal at equality. Together they describe no refund, but no archived test executes this complete two-Allow sequence.'
        tested='full' if test else 'none'
        if arm=='matrix' and ident in ('B01','B03'):
            tested='partial';rationale+=' The archived probe does not execute both late success and failure branches from this starting condition.'
        if ident=='B08' and arm=='routed':
            tested='partial';rationale+=' The archived test asserts the original error and stale counters but discards the returned value; full value+error proof is new reference evidence only.'
        testsources=[]
        if test:testsources=[evidence(probe,'func '+test+'('),evidence(HERE/'results'/f'{arm}-replay.jsonl','"Action":"pass","Package":"github.com/sony/gobreaker","Test":"'+test+'"')]
        reviews.append({'id':ident,'found':ident!='B05','correct':ident!='B05','tested':tested,'rationale':rationale,'evidence':anchors,'test_name':test,'test_evidence':testsources})
    value={'reviewer':'Codex supervising agent, source and archived final reports reviewed 2026-11-14','scope':'Post-run review of immutable final artifacts. Test labels describe archived probe assertions replayed now; not new pilot discoveries. Semantic absence is a reviewer judgment. No Q is resolved.','rows':reviews}
    value['refuted_claims'] = []
    if arm=='routed':
        value['refuted_claims'] = [{'case':'B05', 'rationale':'Q-08 overstates original-breaker binding; serialized wrapper reassignment falsifies it without a data race.', 'evidence':[question(qpath,'Q-08'), evidence(HERE/'fixtures/legacy_claim_test.go.txt','archived original-binding claim refuted:'), evidence(HERE/'results/legacy-claim-red.jsonl','archived original-binding claim refuted:')]}]
    (HERE/f'{arm}-review.json').write_text(json.dumps(value,indent=2)+'\n')
