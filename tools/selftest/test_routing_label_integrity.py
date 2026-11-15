import hashlib,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from routing_label_integrity import verify_source
class SourceIntegrityTests(unittest.TestCase):
 def setUp(self):self.source='first line\nactual fragment\n';self.h=hashlib.sha256(self.source.encode()).hexdigest();self.checks=[{'id':'c','line':2,'fragment':'actual fragment'}]
 def test_good(self):verify_source(self.source,self.h,self.checks)
 def test_wrong_hash(self):
  with self.assertRaisesRegex(ValueError,'source hash'):verify_source(self.source,'0'*64,self.checks)
 def test_wrong_fragment(self):
  self.checks[0]['fragment']='not present'
  with self.assertRaisesRegex(ValueError,'citation'):verify_source(self.source,self.h,self.checks)
 def test_duplicate_ids(self):
  with self.assertRaisesRegex(ValueError,'duplicate'):verify_source(self.source,self.h,self.checks*2)
if __name__=='__main__':unittest.main()
