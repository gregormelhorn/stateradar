"""Separate optimization, validation and held-out feedback."""
from gepa_discovery_eval import require

def check_splits(dataset):
 groups=[dataset.get(k) for k in ('train','validation','test')]
 require(all(isinstance(x,list) and x for x in groups),'nonempty split lists required')
 names=[name for group in groups for name in group]
 require(all(isinstance(n,str) and n for n in names) and len(names)==len(set(names)), 'split overlap or invalid names')

def permit(dataset,component,phase,selected):
 check_splits(dataset)
 require(phase in ('optimization','final'),'unknown phase')
 if phase=='optimization':require(not selected and component in dataset['train']+dataset['validation'],'held-out or post-freeze optimization forbidden')
 else:require(selected and component in dataset['test'],'final requires frozen selection and held-out component')

def train_feedback(dataset,trajectories):
 check_splits(dataset)
 require(isinstance(trajectories,list) and trajectories,'nonempty reflection data required')
 require(all(x.get('component') in dataset['train'] for x in trajectories),'reflection contains nontraining component')
