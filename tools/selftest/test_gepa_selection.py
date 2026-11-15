import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_selection import classify

class SelectionTest(unittest.TestCase):
 def test_exact_tie_is_not_unique(self):
  self.assertEqual(classify([2/3,2/3]),{'status':'tie','best':None,'tied':[0,1]})
 def test_unique_can_select_any_index(self):
  self.assertEqual(classify([.4,.7,.1]),{'status':'unique','best':1,'tied':[1]})
 def test_ties_containing_later_winners(self):
  self.assertEqual(classify([.1,.5,.5]),{'status':'tie','best':None,'tied':[1,2]})
 def test_reject_empty_and_nonfinite(self):
  for scores in ([],[float('nan')],[float('inf')]):
   with self.subTest(scores=scores):
    with self.assertRaises(ValueError):classify(scores)
if __name__=='__main__':unittest.main()
