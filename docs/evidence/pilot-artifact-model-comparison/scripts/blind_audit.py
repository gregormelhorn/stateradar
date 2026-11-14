import json,re,sys
from pathlib import Path
REPO=Path('/Users/gregormelhorn/workspace/domain-statechart')
sys.path.insert(0,str(REPO/'tools'))
from part_b_pack import _catalogue_ids
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
out=REPO/'docs/evidence/pilot-artifact-model-comparison/blind-row-audit.json'
result=json.loads(out.read_text()) if out.exists() else {}
def audit(expected, classified):
 if sorted(expected)!=sorted(classified):raise ValueError('every blind row must have exactly one classification')
for component,name in [('pool','channelPool'),('gobreaker','circuitBreaker')]:
 key=f'{component}-sol'
 if key in result or not (ROOT/f'{key}.exit').exists():continue
 adir=ROOT/key/'selective/pool/domain-analysis'/name
 events,pairs=_catalogue_ids((adir/'event-catalogue.md').read_text())
 expected=[]
 for number,line in enumerate((adir/'part-b-blind.md').read_text().splitlines(),1):
  cells=re.split(r'(?<!\\)\|',line)
  if line.strip().startswith('|') and len(cells)>1:
   cell=cells[1].strip().strip('*`').strip()
   if any(re.match(re.escape(ident)+r'(?![\w-])',cell) for ident in events+pairs):expected.append(number)
 classified=[int(n) for n in re.findall(r'^\|\s*(\d+)\s*\|',(adir/'part-b-diff.md').read_text(),re.M)]
 assert expected,'no blind rows discovered'
 try:audit(expected,classified[1:])
 except ValueError as err:red=str(err)
 else:raise AssertionError('red probe accepted a dropped classification')
 audit(expected,classified)
 result[key]={'blind_rows':len(expected),'classified_rows':len(classified),
              'red_probe_dropped_classification':red,'actual':'PASS'}
out.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
