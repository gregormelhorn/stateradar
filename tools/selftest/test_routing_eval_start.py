import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from run_routing_label_eval import Run
class StartTest(unittest.TestCase):
 def test_constructor_initializes_freeze_before_check(self):
  with tempfile.TemporaryDirectory() as d:
   run=Run(Path(d)/'run');self.assertIsNone(run.dev_hash);self.assertTrue((Path(d)/'run/input-freeze.json').is_file())
if __name__=='__main__':unittest.main()
