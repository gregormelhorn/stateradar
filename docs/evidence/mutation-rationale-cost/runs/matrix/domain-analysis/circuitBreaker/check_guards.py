from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'pack/tools'))
from guard_proofs import boundary_probe, check_group, render
from z3 import And, Bool, Int, Not, Solver, sat

mode, requests, limit, successes, failures, before, current, duration = [
    Int(name) for name in ('mode', 'requests', 'limit', 'successes', 'failures', 'before', 'current', 'duration')]
u32 = 2**32 - 1
u64 = 2**64 - 1
groups = []

def group(name, guards, assumptions, probes):
    result = check_group(name, guards, assumptions)
    result.findings.append('Assumptions: ' + ', '.join(map(str, assumptions)))
    for assignment, branches in boundary_probe(guards, probes):
        result.findings.append(f'{assignment}: {", ".join(branches)}')
    groups.append(result)

modes = [mode >= 0, mode <= 2]
budget = [limit >= 1, limit <= u32, requests >= 0, requests <= u32]
open_guard = mode == 2
full_guard = And(mode == 1, requests >= limit)
group('G-01 admission', [('open', open_guard), ('full', full_guard),
      ('admit', And(Not(open_guard), Not(full_guard)))], modes + budget,
      [{mode:m, requests:r, limit:2} for m in range(3) for r in (1,2,3)])
group('G-02 generation', [('apply', before == current), ('discard', before != current)],
      [before >= 0, before <= u64, current >= 0, current <= u64],
      [{before:b,current:2} for b in (1,2,3)])
group('G-03 successful half-open completion', [('stay', successes < limit), ('close', successes >= limit)],
      [successes >= 0, successes <= u32, limit >= 1, limit <= u32],
      [{successes:s,limit:2} for s in (1,2,3)] + [{successes:0,limit:1},{successes:u32,limit:u32}])
group('G-04 default trip', [('stay', failures <= 5), ('trip', failures > 5)],
      [failures >= 0, failures <= u32], [{failures:f} for f in (4,5,6)])
group('G-07 duration defaults', [('default', duration <= 0), ('custom', duration > 0)],
      [duration >= -(2**63), duration < 2**63], [{duration:d} for d in (-1,0,1)])
group('G-13 request budget default', [('default', limit == 0), ('custom', limit != 0)],
      [limit >= 0, limit <= u32], [{limit:0},{limit:1}])
for ident, name in [('G-08','successful'), ('G-09','callbackPresent'), ('G-11','constructorPolicyPresent'),
                    ('G-16','errorNil'), ('G-12','intervalZero')]:
    flag = Bool(name)
    group(ident + ' ' + name, [('yes',flag), ('no',Not(flag))], [], [{flag:False},{flag:True}])
group('G-14 same-state suppression', [('no transition', mode == current), ('transition', mode != current)],
      modes + [current >= 0,current <= 2],
      [{mode:m,current:c} for m in range(3) for c in range(3)])
group('G-10 final available slot', [('stay', requests + 1 < limit), ('saturate', requests + 1 == limit)],
      budget + [requests < limit], [{requests:0,limit:2},{requests:1,limit:2}])
group('G-15 mode dispatch', [('closed',mode == 0), ('half-open',mode == 1), ('open',mode == 2)],
      modes, [{mode:m} for m in range(3)])

report = render(groups) + '\n'
report += 'group G-05 time reconciliation: not-formalizable: clock: real Go time.Time clock samples, zero sentinel, and strict Before. Below or equal expiry stays; above reconciles.\n'
report += 'group G-06 custom trip policy liveness: not-formalizable: external-call: user callback may panic or never return under the mutex.\n'
witness = Solver()
witness.add(requests == 1, successes == 2, limit == 2)
witness.add(successes > requests, successes >= limit)
status = witness.check()
assert status == sat, 'expected duplicate-completion witness'
report += f'SYS-6 distinct admission accounting counterexample: {witness.model()}\n'
Path(__file__).with_name('guard-results.txt').write_text(report)
print(report,end='')
raise SystemExit(any(group.outcome != 'proven' for group in groups))
