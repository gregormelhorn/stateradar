from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'pack' / 'tools'))
from guard_proofs import check_group, boundary_probe, render
from z3 import And, Or, Not, Ints, Bools, BitVecs, BitVecVal, simplify, BV2Int
import struct

n, cap, size, j, diff = Ints('n cap size j diff')
has_cb, work = Bools('has_callback work_present')
bits = 8 * struct.calcsize('P')
ln, requested = BitVecs('ln requested', bits)
signed_diff = ln - requested
scases = [('clamp', signed_diff < 0), ('loop-bound', signed_diff >= 0)]
groups = [
 ('G-01 New', [('reject', size<=0), ('construct',size>0)], [], [{size:k} for k in (-1,0,1)], 'NAT-01; finite signed Go int projected to Int because only comparison with zero'),
 ('G-02 Resize occupancy', [('shrink',n>size),('equal',n==size),('expand',n<size)], [n>=0,size>=0], [{n:2,size:k} for k in (0,1,2,3)], 'NAT-01; requested size nonnegative; diff cannot wrap'),
 ('G-03 Add miss', [('evict',n+1>cap),('retain',n+1<=cap)], [n>=0], [{n:k,cap:2} for k in (0,1,2)] + [{n:0,cap:k} for k in (-1,0,1)], 'NAT-01; feasible list length (excludes int overflow on list insert)'),
 ('G-04 Oldest and removal', [('empty',n==0),('last',n==1),('multiple',n>1)], [n>=0], [{n:k} for k in (-1,0,1,2)], 'NAT-01; negative count outside domain'),
 ('G-05 Capture and delivery', [('deliver',And(has_cb,work)),('no delivery',Or(Not(has_cb),Not(work)))], [], [{has_cb:a, work:b} for a in (False,True) for b in (False,True)], 'NAT-02; work is operation-specific boolean, not a guarantee of nonempty batch if reported diff exceeds removals'),
 ('G-08 Loop index', [('next',j<diff),('stop',j>=diff)], [j>=0,diff>=0], [{j:k,diff:2} for k in (1,2,3)] + [{j:0,diff:k} for k in (0,1)], 'NAT-01; loop indices nonnegative, diff clamped'),
 ('G-09 Resize signed difference', scases, [ln>=0], [{ln:1,requested:k} for k in (-(1<<(bits-1)),-2,-1,0,1,2)], 'NAT-01; BitVec signed subtraction/comparison, Go int width on this checkout runtime'),
 ('G-10 Resize target sign', [('negative',size<0),('disabled',size==0),('positive',size>0)], [], [{size:k} for k in (-1,0,1)], 'NAT-01; classify target by written size'),
]
results = [check_group(name, guards, assumptions) for name, guards, assumptions, _, _ in groups]
out = [render(results),
       'group G-06 membership/equality: not-formalizable: dynamic-state: map hash/equality and list membership depend on runtime key and stored entries; UV-08/09 probe faults',
       'group G-07 callback completion: not-formalizable: external-call: injected callback controls return, panic, exit, reentry and waiting']
for name, guards, _, samples, note in groups:
 if name.startswith('G-09'):
  samples = [{k:BitVecVal(v,bits) for k,v in item.items()} for item in samples]
 out.append(f'{name} boundary probes ({note}):')
 for assignment, labels in boundary_probe(guards,samples):
  out.append(f'  {assignment}: {", ".join(labels)}')
for requested_size in [-2,-(1<<(bits-1))]:
 value = simplify(BV2Int(BitVecVal(1,bits)-BitVecVal(requested_size,bits),is_signed=True))
 out.append(f'G-09 n=1 requested={requested_size} signed difference={value}')
output='\n'.join(out)+'\n'
Path(__file__).with_name('guard-results.txt').write_text(output)
print(output,end='')
sys.exit(any(r.outcome=='violation' for r in results))
