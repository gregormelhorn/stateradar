import json,shutil,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_routing_flash_diagnostic import verify
class FlashArchiveTest(unittest.TestCase):
 def test_missing(self):
  with tempfile.TemporaryDirectory() as d:self.assertIn('missing status.json',verify(Path(d)))
 def test_blocked(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'BLOCKED'}));self.assertIn('status incomplete',verify(p))
 def test_changed_score(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);run=p/'flash-diagnostic';path=run/'results.json';data=json.loads(path.read_text());data[0]['audit']['matched']=999;path.write_text(json.dumps(data))
   with patch('verify_routing_flash_diagnostic.BASE',p):self.assertIn('diagnostic score mismatch: once',verify(run))
class FlashLedgerProbe(unittest.TestCase):
 def test_coordinated_cost_tampering(self):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/routing-labels'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p);run=p/'flash-diagnostic';lp=run/'ledger.json';ledger=json.loads(lp.read_text());ledger['calls'][0]['amount_microdollars']+=1;ledger['total_microdollars']+=1;lp.write_text(json.dumps(ledger));rp=run/'results.json';rows=json.loads(rp.read_text());rows[0]['flash_cost_microdollars']+=1;rp.write_text(json.dumps(rows));op=run/'once-result.json';out=json.loads(op.read_text());out['draft']['cost_microdollars']+=1;op.write_text(json.dumps(out))
   with patch('verify_routing_flash_diagnostic.BASE',p):self.assertIn('diagnostic sqlite ledger mismatch',verify(run))
if __name__=='__main__':unittest.main()
