import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_provenance import validate
class ProvenanceTests(unittest.TestCase):
 def test_wrong_fragment_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source.txt').write_text('actual\n')
   rows={'cases':[],'findings':[{'id':'f','provenance':'observed-in-code','citation':{'file':'source.txt','line':1,'fragment':'wrong'}}]}
   self.assertIn('invalid citation: f',validate(rows,p))
 def test_invalid_label_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'source.txt').write_text('actual\n')
   rows={'cases':[],'findings':[{'id':'f','provenance':'guessed','citation':{'file':'source.txt','line':1,'fragment':'actual'}}]}
   self.assertIn('invalid provenance: f',validate(rows,p))
if __name__=='__main__':unittest.main()
