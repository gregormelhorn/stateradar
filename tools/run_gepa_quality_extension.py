"""Post-selection seeded correction diagnostic; never used for GEPA selection."""
import argparse,copy,hashlib
from pathlib import Path
from run_gepa_comparison import Experiment,HERE,read,save,sha
from local_budget import Budget
from gepa_eval import score,validate,require

SEEDS={
 'timer':{
  'timer-02':('supported','Stop establishes a completion barrier and cannot return until the previous callback finishes.'),
  'timer-03':('contradicted','Reset only changes a pending deadline; after the callback starts it cannot schedule another invocation.'),
  'timer-07':('supported','The timer contract requires the application to retry a timed-out operation exactly three times.')},
 'once':{
  'once-01':('contradicted','Copying the returned function creates separate once state, so the original callback runs once per copied value.'),
  'once-03':('contradicted','A panic leaves initialization incomplete, so the wrapper retries the original function on its next call.'),
  'once-07':('supported','The component requires the application to retry initialization after every panic.')}}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('run',type=Path);a=p.parse_args();out=a.run.resolve()
 require(read(out/'status.json')['status']=='complete','primary experiment must finish first')
 require(not (out/'quality-extension.json').exists(),'refuse to overwrite measured extension')
 e=Experiment.__new__(Experiment);e.out=out;e.dataset=read(HERE/'dataset.json');e.frozen=read(out/'input-freeze.json')
 e.budget=Budget(out/'routing.sqlite');e.calls=read(out/'calls.json');e.selection_hash=sha(out/'selected-prompt.json')
 fixed=(HERE/'prompts/fixed.md').read_text();gepa=read(out/'selected-prompt.json')['candidate']['review']
 results=[];first=len(e.calls)
 declaration={'protocol_sha256':sha(HERE/'quality-extension.md'),'script_sha256':sha(Path(__file__)), 'selection_sha256':e.selection_hash,'seeds':SEEDS,'first_call_id':first}
 save(out/'quality-extension-declaration.json',declaration)
 for ci,component in enumerate(('timer','once')):
  baseline=copy.deepcopy(read(out/f'baseline-{component}-0.json'))
  for row in baseline['report']['findings']:
   if row['id'] in SEEDS[component]:
    row['verdict'],row['reason']=SEEDS[component][row['id']];row['question']=''
  baseline['report']['corrections']=[]
  validate(baseline['report'],baseline['public'],baseline['source'])
  oracle=read(HERE/e.dataset['components'][component]['oracle']);before=score(baseline['report'],oracle)
  require(set(before['wrong'])==set(SEEDS[component]),'diagnostic baseline was not originally correct')
  save(out/f'diagnostic-input-{component}.json',baseline['report'])
  order=('fixed','gepa') if ci==0 else ('gepa','fixed')
  for arm in order:
   report,ids=e.review(component,fixed if arm=='fixed' else gepa,baseline,'quality-'+arm)
   after=score(report,oracle);wrong=set(after['wrong']);seeded=set(SEEDS[component])
   results.append({'component':component,'arm':arm,'quality':after,'corrected':sorted(seeded-wrong),
    'introduced':sorted(wrong-seeded),'retained_correct_controls':4-len(wrong-seeded),'call_ids':ids,'report':report,
    'incremental_usd_estimate':sum(e.calls[i]['cost']['total_usd_estimate'] for i in ids),
    'repair_calls':sum(e.calls[i]['repair'] for i in ids)})
   save(out/'quality-extension.json',results)
 e.assert_frozen();require(sha(out/'selected-prompt.json')==e.selection_hash,'selection changed')
 save(out/'quality-extension-status.json',{'status':'complete','calls':len(e.calls)-first,'rows':len(results)})
 print('QUALITY EXTENSION PASS: measured four reviews of identical seeded inputs; selection unchanged')
if __name__=='__main__':main()
