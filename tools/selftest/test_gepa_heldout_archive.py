#!/usr/bin/env python3
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_gepa_heldout import verify, verify_diagnostic

class ArchiveTests(unittest.TestCase):
 def test_absent_archive_is_failure(self):
  with tempfile.TemporaryDirectory() as d:self.assertIn('missing status.json',verify(Path(d)))
 def test_incomplete_status_is_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'blocked'}));self.assertIn('status incomplete',verify(p))
 def test_missing_declared_evidence_is_failure(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'complete'}));(p/'input-freeze.json').write_text(json.dumps({'missing':'0'*64}));self.assertIn('missing frozen input: missing',verify(p))
class DiagnosticProbe(unittest.TestCase):
 def test_missing_diagnostic_fails(self):
  with tempfile.TemporaryDirectory() as d:self.assertIn('missing diagnostic status',verify_diagnostic(Path(d)))
 def test_blocked_diagnostic_fails(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d);(p/'status.json').write_text(json.dumps({'status':'blocked'}));self.assertIn('diagnostic incomplete',verify_diagnostic(p))
class DiagnosticIntegrityProbe(unittest.TestCase):
 def exercise(self,kind):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/gepa-heldout/exploratory'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'diagnostic';shutil.copytree(original,p)
   self.assertEqual(verify_diagnostic(p),[])
   calls=json.loads((p/'calls.json').read_text());results=json.loads((p/'results.json').read_text());row=results[0]
   if kind=='prompt':
    prompt=p/calls[row['call_ids'][0]]['directory']/'prompt.md';prompt.write_text(prompt.read_text()+'tamper')
    self.assertIn('diagnostic prompt mismatch: '+row['review'],verify_diagnostic(p))
   else:
    row['summary']['found']=999;(p/'results.json').write_text(json.dumps(results))
    self.assertIn('diagnostic score mismatch: '+row['review'],verify_diagnostic(p))
 def test_tampered_prompt_fails(self):self.exercise('prompt')
 def test_tampered_score_fails(self):self.exercise('score')
class RealArchiveProbe(unittest.TestCase):
 def exercise(self,kind):
  original=Path(__file__).resolve().parents[2]/'docs/evidence/gepa-heldout/runs'
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'run';shutil.copytree(original,p)
   self.assertEqual(verify(p),[])
   calls=json.loads((p/'calls.json').read_text());results=json.loads((p/'results.json').read_text())
   row=next(x for x in results if x['phase']=='final')
   if kind=='prompt':
    prompt=p/calls[row['call_ids'][0]]['directory']/'prompt.md';prompt.write_text(prompt.read_text()+'tamper')
    self.assertIn('final prompt mismatch: '+row['review'],verify(p))
   else:
    row['summary']['found']=999;(p/'results.json').write_text(json.dumps(results))
    self.assertIn('score mismatch: '+row['review'],verify(p))
 def test_tampered_prompt_fails(self):self.exercise('prompt')
 def test_tampered_score_fails(self):self.exercise('score')
if __name__=='__main__':unittest.main()
