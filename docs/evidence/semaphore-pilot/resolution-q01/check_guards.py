"""DR-001 cancellation guard and progress proof; source form is checked explicitly."""
from pathlib import Path
import argparse
import sys

import z3

PACK = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PACK / 'tools'))
from guard_proofs import check_group, boundary_probe, render

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, default=PACK/'examples/weighted-semaphore/semaphore/semaphore.go')
args = parser.parse_args()
source = args.source.read_text()
old = 'if isFront && s.size > s.cur {'
new = 'if isFront {'
if source.count(old) == 1:
    form = 'upstream'
elif source.count(new) == 1:
    form = 'DR-001'
else:
    raise SystemExit('BLOCKED: cancellation guard no longer matches either reviewed source form')
size, cur, head = z3.Ints('size cur head')
front = z3.Bool('front')
free = size-cur
nat = [size >= 1, cur >= 0, cur <= size, head >= 0, head <= size]
notify = z3.And(front, free > 0) if form == 'upstream' else front
branches = [('notify', notify), ('skip', z3.Not(notify))]
proof = check_group('G-Q01 cancellation rescan', branches, nat)
print(render([proof]))
for assignment, taken in boundary_probe(branches, [
    {size: 2, cur: value, front: f} for value in (3, 2, 1) for f in (False, True)
]):
    print(f'{assignment} {taken}' + (' (cur=3 outside NAT; diagnostic only)' if assignment['cur'] == 3 else ''))
progress = z3.Solver()
progress.add(*nat, front, head == 0, z3.Not(notify))
result = progress.check()
print('DR-001 eligible-zero progress:', result, '(unsat required)')
if result == z3.sat:
    print('Counterexample:', progress.model())
# The FIFO notifier still selects the head only: a positive head at full capacity cannot fit.
fifo = z3.Solver()
fifo.add(*nat, cur == size, head > 0, free >= head)
print('DR-001 positive-head fit at full capacity:', fifo.check(), '(unsat required)')
print('Source form:', form)
sys.exit(0 if proof.outcome == 'proven' and result == z3.unsat and fifo.check() == z3.unsat else 1)
