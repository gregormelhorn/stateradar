from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "pack" / "tools"))
import guard_proofs as gp
import z3

limit, requests, streak, duration, before, current = z3.Ints("limit requests streak duration before current")
state, target = z3.Ints("state target")
is_nil, success = z3.Bools("is_nil success")
uint32 = 2**32 - 1
uint64 = 2**64 - 1
limit_domain = [limit >= 1, limit <= uint32]
state_domain = [state >= 0, state <= 2]
results = []


def proof(name, branches, assumptions, probes, evidence):
    result = gp.check_group(name, branches, assumptions)
    result.findings.append(f"Evidence and domain: {evidence}. Assumptions: {assumptions}")
    for sample, fired in gp.boundary_probe(branches, probes):
        note = "" if len(fired) == 1 else " (outside domain or no unique branch)"
        result.findings.append(f"Boundary {sample}: {fired}{note}")
    results.append(result)


def binary(name, pred, yes, no, assumptions, probes, evidence):
    proof(name, [(yes, pred), (no, z3.Not(pred))], assumptions, probes, evidence)


binary("G-01 admission default", limit == 0, "default one", "configured", [limit >= 0, limit <= uint32],
       [{limit: x} for x in [-1, 0, 1]], "uint32 Settings.MaxRequests; gobreaker.go:108,147")
for name, default, line in [("G-02 interval default", "zero", 153), ("G-03 timeout default", "60s", 159)]:
    binary(name, duration <= 0, default, "configured", [duration >= -(2**63), duration < 2**63],
           [{duration: x} for x in [-1, 0, 1]], f"time.Duration signed; gobreaker.go:{line}")

proof("G-04 admission", [("open refusal", state == 2), ("capacity refusal", z3.And(state == 1, requests >= limit)),
                         ("admit", z3.Or(state == 0, z3.And(state == 1, requests < limit)))],
      state_domain + limit_domain + [requests >= 0, requests <= uint32],
      [{state: s, limit: 2, requests: r} for s in range(3) for r in [1, 2, 3]],
      "state enum 0 Closed, 1 HalfOpen, 2 Open and uint32 admissions; gobreaker.go:17-19,48,283-289. Above-limit HalfOpen is a defensive predicate probe")
binary("G-05 generation", before == current, "apply", "discard", [before >= 0, before <= uint64, current >= 0, current <= uint64],
       [{current: 4, before: x} for x in [3, 4, 5]], "uint64 generation; gobreaker.go:128,299")
binary("G-06 success", success, "success", "failure", [], [{success: x} for x in [False, True]], "Go bool; gobreaker.go:293,303")
binary("G-07 half-open close", streak >= limit, "close", "stay", limit_domain + [streak >= 0, streak <= uint32],
       [{limit: 2, streak: x} for x in [1, 2, 3]], "post-increment uint32 streak; gobreaker.go:51,61,316")
binary("G-08 default trip", streak > 5, "trip", "stay", [streak >= 0, streak <= uint32],
       [{streak: x} for x in [4, 5, 6]], "uint32 streak; gobreaker.go:52,193")
binary("G-09 default classifier", is_nil, "success", "failure", [], [{is_nil: x} for x in [False, True]], "interface nil comparison; gobreaker.go:197")
binary("G-10 same state", state == target, "unchanged", "set", state_domain + [target >= 0, target <= 2],
       [{state: 1, target: x} for x in range(3)], "state enum; gobreaker.go:17-19,349")
binary("G-11 hook presence", is_nil, "default or skip", "call supplied", [], [{is_nil: x} for x in [False, True]],
       "nil function projection for each hook; gobreaker.go:165,171,358")
delta = z3.Int("sample_minus_deadline")
armed = z3.Bool("has_closed_deadline")
refresh_closed = z3.And(state == 0, armed, delta > 0)
refresh_open = z3.And(state == 2, delta > 0)
proof("G-12 sampled expiry", [("clear", refresh_closed), ("half-open", refresh_open),
                              ("stay", z3.Not(z3.Or(refresh_closed, refresh_open)))], state_domain,
      [{state: s, armed: a, delta: dt} for s in range(3) for a in [False, True] for dt in [-1, 0, 1]],
      "integer ordering projection only, based on strict time.Time.Before; gobreaker.go:337,341")
binary("G-14 panic payload", is_nil, "skip", "account and rethrow if accounting returns", [],
       [{is_nil: x} for x in [False, True]], "projection of recover value, independent of runtime rules that choose it; gobreaker.go:235-238")
closed_no_expiry = z3.And(state == 0, duration == 0)
closed_expiry = z3.And(state == 0, duration > 0)
proof("G-15 generation expiry", [("no expiry", z3.Or(state == 1, closed_no_expiry)),
                                 ("interval", closed_expiry), ("timeout", state == 2)],
      state_domain + [duration >= 0], [{state: s, duration: x} for s in range(3) for x in [0, 1]],
      "normalized closed interval, positive open timeout; gobreaker.go:153,159,370-378")
print(gp.render(results))
print("group G-13 custom trip: not-formalizable: external-call: caller-supplied policy may return true, false or fail to return; branch projection does not prove callback behavior (gobreaker.go:326)")
raise SystemExit(any(r.outcome != "proven" for r in results))
