import json,sys,tempfile,unittest,shutil
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_routing_label_eval import verify
class ArchiveTest(unittest.TestCase):
 def test_missing_status(self):
  with tempfile.TemporaryDirectory() as d:self.assertIn('missing status.json',verify(Path(d)))
 def test_blocked_status(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'BLOCKED'}));self.assertIn('status incomplete',verify(p))
 def test_absent_source(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'complete'}));(p/'input-freeze.json').write_text(json.dumps({'nonexistent':'0'*64}))
   self.assertIn('missing frozen input: nonexistent',verify(p))
class ReviewedArtifactTest(unittest.TestCase):
 def exercise(self,mode):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p)
   doc=json.loads((p/'reviewed-results.json').read_text())
   if mode=='missing':doc['cases'].pop()
   else:doc['cases'][0]['jev']='fabricated'
   (p/'reviewed-results.json').write_text(json.dumps(doc))
   with patch('verify_routing_label_eval.BASE',p):
    self.assertIn('review coverage mismatch' if mode=='missing' else 'review result mismatch: '+doc['cases'][0]['id'],verify(p/'runs'))
 def test_missing_review(self):self.exercise('missing')
 def test_changed_review(self):self.exercise('changed')
class RunIntegrityTest(unittest.TestCase):
 def exercise(self,mode):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);run=p/'runs';results=json.loads((run/'results.json').read_text());row=next(x for x in results if x['component']=='value')
   if mode=='dev':
    path=run/'once-direct.json';path.write_text(path.read_text()+' ');needle='development output changed: once-direct.json'
   elif mode=='score':
    path=run/'value-jev.json';doc=json.loads(path.read_text());doc['checks']['A01']['choice']='contradicted';path.write_text(json.dumps(doc));needle='score mismatch: value'
   else:
    calls=json.loads((run/'calls.json').read_text());path=run/calls[row['direct_call_ids'][0]]['directory']/'prompt.md';path.write_text(path.read_text()+'tamper');needle='comparator prompt mismatch: value'
   with patch('verify_routing_label_eval.BASE',p):self.assertIn(needle,verify(run))
 def test_dev_output_tampering(self):self.exercise('dev')
 def test_jev_score_tampering(self):self.exercise('score')
 def test_direct_prompt_tampering(self):self.exercise('prompt')
class FreezeCoverageTest(unittest.TestCase):
 def test_missing_label_freeze_entry(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);path=p/'runs/input-freeze.json';freeze=json.loads(path.read_text());name='docs/evidence/routing-labels/frozen/value-labels.json';del freeze[name];path.write_text(json.dumps(freeze))
   with patch('verify_routing_label_eval.BASE',p):self.assertIn('missing freeze entry: '+name,verify(p/'runs'))
class OpenQuestionProbe(unittest.TestCase):
 def test_missing_question_fails(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);path=p/'reviewed-results.json';doc=json.loads(path.read_text());doc['open_questions']=[q for q in doc['open_questions'] if q['id']!='Q-R02'];path.write_text(json.dumps(doc))
   with patch('verify_routing_label_eval.BASE',p):self.assertIn('open question missing: Q-R02',verify(p/'runs'))
class ReferenceBlindTest(unittest.TestCase):
 def test_tampered_reference_prompt_fails(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);path=p/'reference-review/calls/000-reference-review-once/prompt.md';path.write_text(path.read_text()+' gold label leak')
   with patch('verify_routing_label_eval.BASE',p):self.assertIn('reference prompt mismatch: once',verify(p/'runs'))
class CheckpointCostProbe(unittest.TestCase):
 def test_coordinated_comparator_cost_tampering(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);run=p/'runs';rp=run/'results.json';rows=json.loads(rp.read_text());row=next(x for x in rows if x['component']=='value');cp=run/'calls.json';calls=json.loads(cp.read_text());calls[row['direct_call_ids'][0]]['cost']['total_usd_estimate']+=0.5;cp.write_text(json.dumps(calls));dp=run/'value-direct.json';direct=json.loads(dp.read_text());direct['cost_microdollars']+=500000;dp.write_text(json.dumps(direct));row['direct']['cost_microdollars']+=500000;rp.write_text(json.dumps(rows))
   with patch('verify_routing_label_eval.BASE',p):self.assertIn('comparator checkpoint cost mismatch: value',verify(run))
class ReferenceCostProbe(unittest.TestCase):
 def test_reference_cost_tampering(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);path=p/'reference-review/calls.json';calls=json.loads(path.read_text());calls[0]['cost']['total_usd_estimate']+=0.5;path.write_text(json.dumps(calls))
   with patch('verify_routing_label_eval.BASE',p):self.assertIn('reference checkpoint cost mismatch: 0',verify(p/'runs'))
class JevLedgerProbe(unittest.TestCase):
 def test_coordinated_jev_cost_tampering(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);run=p/'runs';lp=run/'jev-ledger.json';ledger=json.loads(lp.read_text());ledger['calls'][-1]['amount_microdollars']+=1;ledger['total_microdollars']+=1;lp.write_text(json.dumps(ledger));jp=run/'value-jev.json';jev=json.loads(jp.read_text());jev['cost_microdollars']+=1;jp.write_text(json.dumps(jev));rp=run/'results.json';rows=json.loads(rp.read_text());row=next(x for x in rows if x['component']=='value');row['jev']['cost_microdollars']+=1;rp.write_text(json.dumps(rows))
   with patch('verify_routing_label_eval.BASE',p):self.assertIn('Jev sqlite ledger mismatch',verify(run))
if __name__=='__main__':unittest.main()
