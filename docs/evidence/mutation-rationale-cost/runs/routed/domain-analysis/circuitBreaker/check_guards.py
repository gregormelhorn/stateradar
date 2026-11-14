from pathlib import Path
import sys

import z3

here = Path(__file__).resolve().parent
sys.path.insert(0, str(here.parents[2] / "pack" / "tools"))
from guard_proofs import boundary_probe, check_group, render

setting, duration, count, limit, state, target, epoch, before = z3.Ints(
    "setting duration count limit state target epoch before"
)
nil, success = z3.Bools("nil success")
u32 = 2**32 - 1
u64 = 2**64 - 1
uint = [0 <= count, count <= u32]
duration_domain = [-(2**63) <= duration, duration < 2**63]
limit_domain = [1 <= limit, limit <= u32]
modes = [0 <= state, state <= 2]
groups = []
details = []

def group(number, name, guards, assumptions, probes):
    label = f"G-{number:02} {name}"
    groups.append(check_group(label, guards, assumptions))
    details.append(f"{label} assumptions: {assumptions or 'typed Boolean'}")
    for assignments, fired in boundary_probe(guards, probes):
        details.append(f"  {assignments} -> {', '.join(fired) or 'outside branch partition'}")

def binary(number, name, predicate, assumptions, probes):
    group(number, name, [("first", predicate), ("otherwise", z3.Not(predicate))], assumptions, probes)

def samples(variable, *values):
    return [{variable: value} for value in values]

binary(1, "request limit default", setting == 0, [0 <= setting, setting <= u32], samples(setting, 0, 1, u32))
binary(2, "interval default", duration <= 0, duration_domain, samples(duration, -1, 0, 1))
binary(3, "timeout default", duration <= 0, duration_domain, samples(duration, -1, 0, 1))
binary(4, "trip policy default", nil, [], samples(nil, True, False))
binary(5, "classifier default", nil, [], samples(nil, True, False))
group(6, "admission", [
    ("open refusal", state == 2),
    ("half-open refusal", z3.And(state == 1, count >= limit)),
    ("accept", z3.Or(state == 0, z3.And(state == 1, count < limit))),
], modes + uint + limit_domain,
    [{state: s, count: n, limit: 2} for s in range(3) for n in (1, 2, 3)])
binary(7, "matching generation", epoch == before,
       [0 <= epoch, epoch <= u64, 0 <= before, before <= u64],
       [{epoch: e, before: 2} for e in (1, 2, 3)])
binary(8, "default trip", count > 5, uint, samples(count, 4, 5, 6))
binary(9, "half-open success threshold", count >= limit, uint + limit_domain,
       [{count: n, limit: 2} for n in (1, 2, 3)])
binary(10, "closed interval sentinel", duration == 0, [duration >= 0] + duration_domain, samples(duration, 0, 1))
binary(13, "configured observer", z3.Not(nil), [], samples(nil, True, False))
binary(14, "same target", state == target, modes + [0 <= target, target <= 2],
       [{state: s, target: 1} for s in range(3)])
binary(16, "recover returned a value", z3.Not(nil), [], samples(nil, True, False))
binary(17, "completion dispatch", success, [], samples(success, True, False))
group(18, "mode dispatch", [("closed", state == 0), ("half-open", state == 1), ("open", state == 2)],
      modes, samples(state, 0, 1, 2))
binary(19, "default classification", nil, [], samples(nil, True, False))
binary(20, "admission error", z3.Not(nil), [], samples(nil, True, False))

clock = [
    "group G-11 sampled expiry: not-formalizable: clock: Go Time comparison uses live sampled time and monotonic or wall representations",
    "  Inspection: now before or equal expiry stays, strictly after changes; zero Closed expiry disables. gobreaker.go:337 and gobreaker.go:341.",
    "group G-12 custom policy: not-formalizable: external-call: arbitrary callback can block or panic before yielding a Boolean",
    "  Inspection: true trips, false stays with incremented failure count; runtime exit uses deferred unlock. gobreaker.go:295 and gobreaker.go:325-327.",
    "group G-15 classifier and request: not-formalizable: external-call: workload and classifier may not return or may report arbitrary results",
    "  Inspection: normal error is classified, panic recovery can bypass the normal classification, and matching generation controls accounting. gobreaker.go:234-244 and gobreaker.go:299.",
]
report = render(groups) + "\n" + "\n".join(clock + ["", "Boundary probes and assumptions"] + details) + "\n"
(here / "guard-results.txt").write_text(report)
print(report, end="")
raise SystemExit(any(result.outcome != "proven" for result in groups))
