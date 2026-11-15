import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from routing_compare_prompt import build
class PromptTest(unittest.TestCase):
 def test_includes_source_and_check(self):
  p=build('source line',[{'id':'A','kind':'claim','statement':'claim','line':1,'fragment':'source'}]);self.assertIn('source line',p);self.assertIn('claim',p)
 def test_rejects_gold_and_review(self):
  for extra in ({'expected':'supported'},{'reviewer':'hidden'},{'reason':'gold'}):
   c={'id':'A','kind':'claim','statement':'claim','line':1,'fragment':'source',**extra}
   with self.assertRaises(ValueError):build('source line',[c])
if __name__=='__main__':unittest.main()
