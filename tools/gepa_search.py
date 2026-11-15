"""Optional GEPA integration; task/provider execution belongs to the adapter."""
import importlib.metadata

def optimize_review(adapter,seed,run_dir):
 import gepa
 if importlib.metadata.version('gepa')!='0.1.4':raise ValueError('experiment requires gepa==0.1.4')
 result=gepa.optimize(seed_candidate={'review':seed},trainset=['context'],valset=['singleflight'],
  adapter=adapter,skip_perfect_score=False,reflection_minibatch_size=1,
  max_metric_calls=6,seed=17,run_dir=str(run_dir),cache_evaluation=False,
  display_progress_bar=False,raise_on_exception=True,use_merge=False,
  candidate_selection_strategy='current_best',acceptance_criterion='improvement_or_equal')
 return {'candidate':result.best_candidate,'metric_calls':result.total_metric_calls,
  'best_index':result.best_idx,'candidates':result.candidates,'validation_scores':result.val_aggregate_scores,
  'parents':result.parents,'version':importlib.metadata.version('gepa')}
