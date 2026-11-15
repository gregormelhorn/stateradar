"""Adversarial plan and execution tests; no claim of real component execution."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_late_workflow as w
from test_late_completion import PROFILE, evidence

class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'plan.json'
        self.write('contract.txt','The component remains stopped and disposes late resources.\n')
        self.write('decision.yaml',{'id':'DR-001','status':'accepted'})
        self.profile=copy.deepcopy(PROFILE);self.profile['decision']='decision.yaml'
        self.write('profile.json',self.profile)
        citation={'file':'contract.txt','line':1,'fragment':'remains stopped','provenance':'explicit-requirement'}
        self.scope={'formatVersion':1,'boundary':'test fixture','coverage':'scenario-slice','traces':[]}
        for c in self.profile['cases']:
            self.scope['traces'].append({'id':c['id'],'cell':c['cell'],'order':c['order'],
                'decision':'decision.yaml','contract':{k:True for k in ('terminal','ownedIdleResource','noLateEffects','exactRelease')},
                'seamsAvailable':True,'citations':[citation]})
        self.plan={'formatVersion':1,'scope':'scope.json','rows':[{'trace':c['id'],'status':'applicable','reason':'Accepted terminal contract.', 'profileCase':c['id']} for c in self.profile['cases']],
            'inputs':{'profile':'profile.json','mutants':'fault.json','generation':'generation.json','adapter':'adapter.py','probe':'probe.txt','oracle':'oracle.py','patch':'patch.json'},
            'execution':{'reader':'go-json-v1','testRoot':'TestEvidence','counts':{'baseline':1,'full':1,'weak':1},'sourceSha256':'0'*64}}
        projections=['terminal','publication','effect','resource']
        self.mutants=[{'id':k,'cell':'Stopped x Complete','target':'source.go','variant':k+'.go'} for k in projections+['guard']]
        self.generation={'projections':{k:{'provenBy':k} for k in projections},'bindings':[
            {'id':m['id'],'cell':m['cell'],'variant':m['variant'],'requiresProjection':projections[max(0,i-1)] if i<4 else 'resource',
             'match':['original'],'replace':[m['id']]} for i,m in enumerate(self.mutants)]}
        self.write('fault.json',{'expectedCells':2,'mutants':self.mutants})
        self.write('generation.json',self.generation)
        for f in ('adapter.py','probe.txt','oracle.py'):self.write(f,'fixture')
        self.write('patch.json',{'edits':[]})
        self.save()
    def write(self,name,value):
        p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(value if isinstance(value,str) else json.dumps(value))
    def save(self):
        self.write('scope.json',self.scope);self.write('plan.json',self.plan)
    def reject(self,pattern):
        self.save()
        with self.assertRaisesRegex(w.EvidenceError,pattern):w.check_plan(self.path,self.root)
    def test_valid_plan(self):w.check_plan(self.path,self.root)
    def test_omitted_scope_row(self):
        self.plan['rows'].pop();self.reject('scope coverage')
    def test_duplicate_row(self):
        self.plan['rows'].append(self.plan['rows'][0]);self.reject('scope coverage')
    def test_wrong_cell(self):
        self.scope['traces'][0]['cell']='Other x Complete';self.reject('cell/order')
    def test_wrong_order(self):
        self.scope['traces'][0]['order']=self.profile['cases'][1]['order'];self.reject('cell/order')
    def test_wrong_dr(self):
        self.write('other.yaml',{'id':'DR-002','status':'accepted'})
        self.scope['traces'][0]['decision']='other.yaml';self.reject('decision')
    def test_unaccepted_dr(self):
        self.write('decision.yaml',{'id':'DR-001','status':'proposed'});self.reject('accepted decision')
    def test_missing_positive_control(self):
        self.profile['cases'].pop();self.write('profile.json',self.profile);self.reject('both late')
    def test_false_exemption(self):
        self.plan['rows'][0].update(status='not-applicable');self.reject('applicability')
    def test_unknown_requires_open_question(self):
        self.scope['traces'][0]['contract']['terminal']='unknown'
        self.plan['rows'][0]={'trace':'late','status':'blocked','reason':'Awaiting owner'};self.reject('OPEN question')
    def test_missing_seam_is_blocked(self):
        self.scope['traces'][0]['seamsAvailable']=False;self.reject('applicability')
    def test_bad_citation(self):
        self.scope['traces'][0]['citations'][0]['fragment']='invented';self.reject('citation')
    def test_missing_canary(self):
        del self.generation['projections']['resource'];self.write('generation.json',self.generation);self.reject('four projections')
    def test_canary_dependency_bypass(self):
        self.generation['bindings'][-1]['requiresProjection']='terminal'
        self.write('generation.json',self.generation);self.reject('canary prerequisites')
    def test_excluded_plan_reports_no_execution(self):
        for t in self.scope['traces']:t['contract']['terminal']=False
        for r in self.plan['rows']:
            r['status']='not-applicable';r.pop('profileCase')
        self.plan.pop('inputs');self.plan.pop('execution');self.save()
        result=w.check_plan(self.path,self.root)
        self.assertEqual(result['applicable'],0)

class Execution(Workflow):
    def setUp(self):
        super().setUp()
        self.out=self.root/'runs';self.out.mkdir()
        self.plan['execution']['sourceSha256']=w.digest('original')
        self.plan['execution']['counts']={k:2 for k in ('baseline','full','weak')}
        self.save();self.checked=w.check_plan(self.path,self.root)
        (self.out/'upstream-source.go.txt').write_text('original')
        self.bundle('evaluation',self.repeated(), 'original',False)
        for m in self.mutants:
            traces=self.repeated()
            field,value={'terminal':('state','Active'),'publication':('published',True),
                'effect':('effects',['accepted']),'resource':('releaseCount',0),'guard':('published',True)}[m['id']]
            for t in traces:
                if t['case']=='late':
                    for step in t['steps'][2:]:step[field]=value
            self.bundle(m['id'],traces,m['id']+'\n',False)
            self.bundle(m['id']+'/weak',traces,m['id']+'\n',True)
        w.write_receipt(self.path,self.root,self.out)
    def repeated(self):
        return [dict(t,repeat=r) for r in range(2) for t in evidence()]
    def bundle(self,name,traces,source,weak):
        folder=self.out/name;folder.mkdir(parents=True,exist_ok=True)
        names=['TestEvidence']+[f"TestEvidence/{c['id']}/{r}" for c in self.profile['cases'] for r in range(2)]
        records=[{'Action':a,'Test':n} for n in names for a in ('run','pass')]
        records.extend({'Action':'output','Output':'LATE TRACE '+json.dumps(t)+'\n'} for t in traces)
        records.append({'Action':'pass'})
        (folder/'go.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
        (folder/'observations.json').write_text(json.dumps(traces))
        inputs=self.checked['inputs']
        meta={'formatVersion':1,'count':2,'weak':weak,'sourceSha256':w.digest(source),'goExit':0}
        for key in ('profile','adapter','probe','oracle'):meta[key+'Sha256']=w.sha(inputs[key])
        for key,file in [('go','go.jsonl'),('observations','observations.json')]:meta[key+'Sha256']=w.sha(folder/file)
        (folder/'execution.json').write_text(json.dumps(meta))
    def execute(self):return w.check_execution(self.checked,self.root,self.out)
    def test_valid_execution(self):self.assertEqual(self.execute(),5)
    def test_stale_inputs(self):
        self.write('adapter.py','changed')
        with self.assertRaisesRegex(w.EvidenceError,'stale workflow'):self.execute()
    def test_missing_canary_execution(self):
        (self.out/'resource/execution.json').unlink()
        with self.assertRaises(OSError):self.execute()
    def test_empty_discovery_even_with_matching_hash(self):
        folder=self.out/'evaluation';(folder/'go.jsonl').write_text('{}\n')
        meta=w.read(folder/'execution.json');meta['goSha256']=w.sha(folder/'go.jsonl')
        (folder/'execution.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(w.EvidenceError,'discovery'):self.execute()
    def test_incomplete_observations_even_with_matching_hashes(self):
        self.bundle('evaluation',self.repeated()[:-1],'original',False)
        with self.assertRaisesRegex(w.EvidenceError,'incomplete'):self.execute()
    def test_target_must_fail_every_repeat(self):
        traces=self.repeated()
        for step in traces[0]['steps'][2:]:step['published']=True
        self.bundle('guard',traces,'guard\n',False)
        with self.assertRaisesRegex(w.EvidenceError,'every repetition'):self.execute()
    def test_canary_cannot_change_two_projections(self):
        traces=self.repeated()
        for t in traces:
            if t['case']=='late':
                for step in t['steps'][2:]:step.update(state='Active',published=True)
        self.bundle('terminal',traces,'terminal\n',False)
        with self.assertRaisesRegex(w.EvidenceError,'independently isolated'):self.execute()
    def test_source_mismatch(self):
        self.bundle('evaluation',self.repeated(),'wrong source',False)
        with self.assertRaisesRegex(w.EvidenceError,'receipt mismatch'):self.execute()
    def test_raw_observations_must_match(self):
        folder=self.out/'evaluation';traces=self.repeated();traces[0]['steps'][0]['resource']='different'
        (folder/'observations.json').write_text(json.dumps(traces))
        meta=w.read(folder/'execution.json');meta['observationsSha256']=w.sha(folder/'observations.json')
        (folder/'execution.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(w.EvidenceError,'raw execution'):self.execute()

if __name__=='__main__':unittest.main()
