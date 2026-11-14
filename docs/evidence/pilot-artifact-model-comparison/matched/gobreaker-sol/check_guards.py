from pathlib import Path
import sys

import z3

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pack" / "tools"))
from guard_proofs import boundary_probe, check_group, render

state, requests, limit, streak, generation, captured, duration, maximum = z3.Ints(
    "state requests limit streak generation captured duration maximum"
)
success, callback, changed, nil_value = z3.Bools("success callback changed nil_value")
uint32 = 2**32 - 1
uint64 = 2**64 - 1
closed, opened, half_open = 0, 1, 2

def group(name, guards, assumptions, assignments):
    result = check_group(name, guards, assumptions=assumptions)
    result.findings.append("NAT domain: " + ", ".join(map(str, assumptions or ["Boolean sort"])))
    for assignment, branches in boundary_probe(guards, assignments):
        result.findings.append(f"boundary {assignment}: {', '.join(branches)}")
    return result

cap = [limit >= 1, limit <= uint32]
results = [
    group("G-01 admission", [
        ("open", state == opened),
        ("budget", z3.And(state == half_open, requests >= limit)),
        ("admit", z3.Or(state == closed, z3.And(state == half_open, requests < limit))),
    ], cap + [requests >= 0, requests <= uint32, state >= 0, state <= 2],
       [{state: mode, requests: n, limit: 2} for mode in range(3) for n in (1, 2, 3)]),
    group("G-02 generation", [("apply", generation == captured), ("skip", generation != captured)],
          [generation >= 0, generation <= uint64, captured >= 0, captured <= uint64],
          [{generation: n, captured: 2} for n in (1, 2, 3)]),
    group("G-03 success threshold", [("stay", streak < limit), ("close", streak >= limit)],
          cap + [streak >= 0, streak <= uint32], [{streak: n, limit: 2} for n in (1, 2, 3)]),
    group("G-04 default trip", [("stay", streak <= 5), ("open", streak > 5)],
          [streak >= 0, streak <= uint32], [{streak: n} for n in (4, 5, 6)]),
    group("G-05 duration", [("default", duration <= 0), ("configured", duration > 0)],
          [duration >= -(2**63), duration <= 2**63-1], [{duration: n} for n in (-1, 0, 1)]),
    group("G-06 maximum", [("default", maximum == 0), ("configured", maximum > 0)],
          [maximum >= 0, maximum <= uint32], [{maximum: n} for n in (0, 1)]),
    group("G-09 outcome", [("success", success), ("failure", z3.Not(success))],
          [], [{success: b} for b in (False, True)]),
    group("G-10 callback dispatch", [("same", z3.Not(changed)),
          ("notify", z3.And(changed, callback)), ("skip", z3.And(changed, z3.Not(callback)))],
          [], [{changed: x, callback: y} for x in (False, True) for y in (False, True)]),
    group("G-11 nil test", [("nil", nil_value), ("non-nil", z3.Not(nil_value))],
          [], [{nil_value: b} for b in (False, True)]),
]
report = render(results) + "\n" + "\n".join([
    "  - G-06 below zero is outside the uint32 domain.",
    "group G-07 expiry: not-formalizable: clock: time.Time.Before depends on sampled monotonic or wall time and zero sentinel.",
    "  - Inspection: below and equality stay. Above refreshes only for armed Closed or Open. HalfOpen does not sample an expiry. gobreaker.go:337 and 341.",
    "group G-08 custom trip: not-formalizable: external-call: ReadyToTrip can return either Boolean, hang, panic or terminate its goroutine.",
    "  - Inspection following normal return: true opens; false stays. gobreaker.go:326 and 327.",
]) + "\n"
Path(__file__).with_name("guard-results.txt").write_text(report)
print(report, end="")
sys.exit(any(r.outcome == "violation" for r in results))
