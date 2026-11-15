import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from local_budget import Budget
from routing_ledger_check import verify
class LedgerTest(unittest.TestCase):
 def test_detects_altered_summary(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'ledger.sqlite';b=Budget(p,1000);i=b.reserve('jev',100);b.settle(i,23)
   summary={'limit_microdollars':1000,'total_microdollars':24,'calls':b.calls()}
   with self.assertRaisesRegex(ValueError,'ledger mismatch'):verify(p,summary)
 def test_missing_database_fails(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaisesRegex(ValueError,'ledger missing'):verify(Path(d)/'missing.sqlite',{})
 def test_matching_ledger(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'ledger.sqlite';b=Budget(p,1000);i=b.reserve('jev',100);b.settle(i,23)
   verify(p,{'limit_microdollars':1000,'total_microdollars':23,'calls':b.calls()})
if __name__=='__main__':unittest.main()
