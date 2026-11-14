import json,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
result={}
for component in ('pool','gobreaker'):
 for model in ('sol','terra'):
  name=f'{component}-{model}'
  arm=root/name/'selective'
  if not arm.exists():continue
  stats={'catalogue_renders':[], 'catalogue_identity_checks':[], 'blind_dispatches':[], 'command_failures':[]}
  for path in sorted((arm/'logs').glob('[0-9]*.json')):
   entry=json.loads(path.read_text());argv=entry.get('argv',[])
   row={'log':path.stem,'exit':entry.get('exit_code')}
   if '--help' not in argv:
    if 'catalogue' in argv and any(x.endswith('pilot_artifacts.py') for x in argv):
     stats['catalogue_identity_checks' if '--check' in argv else 'catalogue_renders'].append(row)
    if len(argv)>4 and argv[4]=='blind' and '--package-only' not in argv:stats['blind_dispatches'].append(row)
   if entry.get('exit_code',0)!=0:
    row['argv']=[part[:220] for part in argv]
    row['diagnostic']=(path.with_suffix('.stderr').read_text()+'\n'+path.with_suffix('.stdout').read_text())[:400]
    stats['command_failures'].append(row)
  result[name]=stats
print(json.dumps(result,indent=2))
