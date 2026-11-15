import copy
import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gepa_discovery_eval import audit, EvalError, check_phase

class DiscoveryAuditTests(unittest.TestCase):
    def setUp(self):
        self.report = {'findings': [{'id':'F1','text':'Effect after stop.', 'citation': {'line':1,'fragment':'source evidence'}, 'question':'OPEN: intended?'}]}
        self.source = 'source evidence\n'
        self.cases = [{'id':'C1', 'question_required':True}, {'id':'C2', 'question_required':False}]
        self.review = {'reviewer':'operator', 'cases':[{'id':'C1','finding_ids':['F1'], 'reason':'ordered effect and open intent'},{'id':'C2','finding_ids':[], 'reason':'not reported'}], 'findings':[{'id':'F1','verdict':'valid','reason':'matches evidence'}]}
    def test_complete(self):
        self.assertEqual(audit(self.report,self.source,self.cases,self.review)['found'],1)
    def test_missing_case(self):
        self.review['cases'].pop()
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_missing_finding_review(self):
        self.review['findings'].clear()
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_wrong_citation(self):
        self.report['findings'][0]['citation']['fragment']='fabricated'
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_unreviewed_is_not_credit(self):
        self.review['findings'][0]['verdict']='unreviewed'
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_false_finding_cannot_score(self):
        self.review['findings'][0]['verdict']='false'
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_open_question_required_for_credit(self):
        self.report['findings'][0]['question']=''
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_duplicate_finding(self):
        self.report['findings'].append(copy.deepcopy(self.report['findings'][0]))
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)
    def test_unknown_case_reference(self):
        self.review['cases'][0]['finding_ids']=['F2']
        with self.assertRaises(EvalError): audit(self.report,self.source,self.cases,self.review)

class PhaseTests(unittest.TestCase):
    def test_final_cannot_enter_optimization(self):
        data={'train':['a'],'validation':['b'],'test':['c']}
        with self.assertRaises(EvalError): check_phase(data,'c','optimization',False)
    def test_final_needs_frozen_selection(self):
        data={'train':['a'],'validation':['b'],'test':['c']}
        with self.assertRaises(EvalError): check_phase(data,'c','final',False)
    def test_split_overlap_rejected(self):
        data={'train':['a'],'validation':['a'],'test':['c']}
        with self.assertRaises(EvalError): check_phase(data,'a','optimization',False)
    def test_eligible(self):
        data={'train':['a'],'validation':['b'],'test':['c']}
        check_phase(data,'a','optimization',False)
        check_phase(data,'c','final',True)

if __name__ == '__main__': unittest.main()
