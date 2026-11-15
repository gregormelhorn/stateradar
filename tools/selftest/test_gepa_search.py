"""Run real GEPA with a deterministic mock task; no provider work or quality claim."""
import sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_search import optimize_review
class Mock:
 def __init__(self):self.proposals=0;self.seen=[]
 def evaluate(self,batch,candidate,capture_traces=False):
  from gepa.core.adapter import EvaluationBatch
  self.seen.extend(batch)
  scores=[1.0 if candidate['review']=='short' else .5 for _ in batch]
  return EvaluationBatch(outputs=[{} for _ in batch],scores=scores,trajectories=[{'Feedback':'too long'} for _ in batch])
 def make_reflective_dataset(self,candidate,eval_batch,components_to_update):return {'review':eval_batch.trajectories}
 def propose_new_texts(self,candidate,reflective_dataset,components_to_update):
  self.proposals+=1;return {'review':'short'}
class Search(unittest.TestCase):
 def test_actual_search_and_split(self):
  adapter=Mock()
  with tempfile.TemporaryDirectory() as td:result=optimize_review(adapter,'long seed',Path(td))
  self.assertGreater(adapter.proposals,0)
  self.assertEqual(set(adapter.seen),{'context','singleflight'})
  self.assertEqual(result['candidate']['review'],'short')
  self.assertGreater(result['metric_calls'],0)
if __name__=='__main__':unittest.main()
