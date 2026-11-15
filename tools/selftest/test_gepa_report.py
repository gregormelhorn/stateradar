"""Cost totals include repair calls and keep missing usage unknown."""
import copy,json,shutil,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gepa_report import summarize,audit,HERE
from gepa_eval import EvalError
class Costs(unittest.TestCase):
 def setUp(self):
  self.calls=[{'id':i,'category':'baseline' if i==0 else 'final-fixed','component':'timer','repair':i==2,'cost':{'complete':True,'total_usd_estimate':v}} for i,v in enumerate((1.,2.,3.))]
  self.rows=[{'arm':a,'component':'timer','repeat':0,'baseline_call_ids':[0],'review_call_ids':[] if a=='none' else [1,2],'provider_usd':.5,'total_usd_estimate':1.5 if a=='none' else 6.5,'repair_calls':0 if a=='none' else 1,'quality':{'correct':7,'total':7}} for a in ('none','fixed','gepa')]
  self.providers=[{'cost_usd':.5,'phase':'final'}]
 def test_unique_experiment_and_shared_baseline(self):
  result=summarize(self.rows,self.calls,self.providers)
  self.assertEqual(result['actual_experiment_usd_estimate'],6.5)
  self.assertEqual(result['arms']['fixed']['strategy_cost_usd_estimate'],6.5)
  self.assertIsNone(result['break_even_uses_vs_fixed'])
 def test_repair_cost_cannot_disappear(self):
  self.rows[1]['total_usd_estimate']-=3
  with self.assertRaises(EvalError):summarize(self.rows,self.calls,self.providers)
 def test_repair_count_cannot_disappear(self):
  self.rows[1]['repair_calls']=0
  with self.assertRaises(EvalError):summarize(self.rows,self.calls,self.providers)
 def test_unknown_is_not_free(self):
  self.calls[0]['cost']['complete']=False
  with self.assertRaises(EvalError):summarize(self.rows,self.calls,self.providers)
 def test_missing_pair(self):
  self.rows[1]['repeat']=1
  with self.assertRaises(EvalError):summarize(self.rows,self.calls,self.providers)
class ArchivedCosts(unittest.TestCase):
 def mutate_and_reject(self,change):
  with tempfile.TemporaryDirectory(prefix='gepa-audit-red-') as td:
   out=Path(td)/'runs';shutil.copytree(HERE/'runs',out)
   path=out/'comparison.json';rows=json.loads(path.read_text());change(rows)
   path.write_text(json.dumps(rows))
   with self.assertRaises(EvalError):audit(out)
 def test_whole_trial_cannot_disappear_from_all_arms(self):
  self.mutate_and_reject(lambda rows:rows.__setitem__(slice(None),[r for r in rows if not(r['component']=='timer' and r['repeat']==0)]))
 def test_provider_cost_cannot_disappear_from_every_strategy(self):
  def remove(rows):
   for row in rows:
    row['total_usd_estimate']-=row['provider_usd'];row['provider_usd']=0
  self.mutate_and_reject(remove)
if __name__=='__main__':unittest.main()
