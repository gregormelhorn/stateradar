import json
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_gepa_prospective import verify

class ArchiveTest(unittest.TestCase):
 def test_missing_status(self):
  with tempfile.TemporaryDirectory() as d:self.assertIn('missing status.json',verify(Path(d)))
 def test_blocked_status(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'blocked'}));self.assertIn('status incomplete',verify(p))
 def test_missing_frozen_input(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'complete'}));(p/'input-freeze.json').write_text(json.dumps({'missing':'0'*64}))
   self.assertIn('missing frozen input: missing',verify(p))
class RealArchiveProbe(unittest.TestCase):
 def exercise(self,kind):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/gepa-prospective/runs'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'run';shutil.copytree(original,p)
   self.assertEqual(verify(p),[])
   calls=json.loads((p/'calls.json').read_text());results=json.loads((p/'results.json').read_text());row=results[0]
   if kind=='prompt':
    path=p/calls[row['call_ids'][0]]['directory']/'prompt.md';path.write_text(path.read_text()+'tamper')
    self.assertIn('prompt mismatch: '+row['review'],verify(p))
   else:
    row['summary']['found']=999;(p/'results.json').write_text(json.dumps(results))
    self.assertIn('score mismatch: '+row['review'],verify(p))
 def test_prompt_tamper(self):self.exercise('prompt')
 def test_score_tamper(self):self.exercise('score')
class ProvenanceCoverageProbe(unittest.TestCase):
 def exercise(self,kind):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/gepa-prospective'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'evidence';shutil.copytree(original,p)
   doc=json.loads((p/'provenance.json').read_text());doc[kind].pop();(p/'provenance.json').write_text(json.dumps(doc))
   with patch('verify_gepa_prospective.HERE',p):
    self.assertIn('provenance '+('case' if kind=='cases' else 'finding')+' coverage mismatch',verify(p/'runs'))
 def test_missing_case(self):self.exercise('cases')
 def test_missing_finding(self):self.exercise('findings')
if __name__=='__main__':unittest.main()
