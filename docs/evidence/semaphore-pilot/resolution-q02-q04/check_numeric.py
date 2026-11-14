"""Check the partial coverage map, reviewed guards and bounded arithmetic."""
import argparse
import json
from pathlib import Path
import sys
import z3

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[3]
sys.path.insert(0, str(PACK/'tools'))
from guard_proofs import check_group, render

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--coverage', type=Path, default=HERE/'matrix-coverage.json')
args = parser.parse_args()
rows = json.loads(args.coverage.read_text())['cells']
original = json.loads((HERE.parent/'analysis/analysis.json').read_text())['cells']
assert len(rows) == len(original) == 57
assert {(r['state'],r['event']) for r in rows} == {(r['state'],r['event']) for r in original}
source = (PACK/'examples/weighted-semaphore/semaphore/semaphore.go').read_text()
tests = (PACK/'examples/weighted-semaphore/semaphore/decision_numeric_test.go').read_text()
for row in rows:
    if row['status'] == 'guarded-refinement':
        assert row['tests'] and row['decisions'], 'decided branch missing test or DR'
        for name in row['tests']:
            assert f'func {name}(t *testing.T)' in tests, name
        for dr in row['decisions']:
            record = (HERE/'decisions'/f'{dr}.yaml').read_text().splitlines()
            assert f'id: {dr}' in record and 'status: accepted' in record
    else:
        assert row['status'] == 'outside-this-resolution' and not row['tests'] and not row['decisions']
assert {dr for row in rows for dr in row['decisions']} == {'DR-002', 'DR-003', 'DR-004'}, 'accepted DR lacks reverse coverage'
assert {name for row in rows for name in row['tests']} == {
    'TestDR002NegativeConstructor', 'TestDR002NegativeAcquire',
    'TestDR002NegativeTryAcquire', 'TestDR002NegativeRelease',
    'TestDR002ZeroAndMaxBoundaries', 'TestDR003OverReleaseEmptyPartialFull',
    'TestDR003OverReleaseQueued', 'TestDR003OverReleaseMax',
    'TestDR004OversizedImmediateError', 'TestDR004PreCanceledOversized',
}, 'accepted scenario missing from coverage map'
print('COVERAGE: 57 historical cells accounted for; numeric refinements have tests and accepted DRs')
# Audit the reviewed guard forms. Arithmetic proofs below are conditional on
# these reviewed operations; behavior tests, not text matching, exercise code.
for signature in ('func NewWeighted(', 'func (s *Weighted) Acquire(', 'func (s *Weighted) TryAcquire(', 'func (s *Weighted) Release('):
    body = source.split(signature, 1)[1].split('\nfunc ', 1)[0]
    assert 'if n < 0 {' in body, signature
    if 's.mu.Lock()' in body:
        assert body.index('if n < 0 {') < body.index('s.mu.Lock()'), signature
release = source.split('func (s *Weighted) Release(',1)[1].split('\nfunc ',1)[0]
assert release.index('if n > s.cur {') < release.index('s.cur -= n'), 'over-release must check before mutation'
assert '<-done\n\t\treturn ctx.Err()' not in source, 'oversized context wait remains'
maximum = 2**63-1
size, cur, n = z3.Ints('size cur n')
nat = [size >= 0, size <= maximum, cur >= 0, cur <= size, n >= -(2**63), n <= maximum]
groups = [
 check_group('numeric sign', [('reject',n<0),('valid',n>=0)],nat),
 check_group('release bound', [('reject',n>cur),('accept',n<=cur)],nat+[n>=0]),
 check_group('acquire bound', [('oversized',n>size),('fits',n<=size-cur),('wait',z3.And(n<=size,n>size-cur))],nat+[n>=0]),
]
print(render(groups))
assert all(g.outcome == 'proven' for g in groups)
for label, assumptions, value in [
 ('grant', [n>=0,n<=size-cur],cur+n),
 ('release/rollback', [n>=0,n<=cur],cur-n),
 ('rejected operation', [],cur),
 ('free capacity', [],size-cur),
]:
    solver=z3.Solver();solver.add(*nat,*assumptions,z3.Or(value<0,value>size,value>maximum))
    result=solver.check();print(f'ARITHMETIC {label}: {result} (unsat required)');assert result==z3.unsat
print('NUMERIC CHECK: PASS; no whole-model or scheduler proof claimed')
