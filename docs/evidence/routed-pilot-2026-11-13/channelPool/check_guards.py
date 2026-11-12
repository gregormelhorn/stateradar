#!/usr/bin/env python3
"""Guard proofs for channelPool (silenceper/pool, channel.go).

Component-specific part only: typed variables, NAT domains, guard
expressions. The proof procedure is the pack library tools/guard_proofs.py.
Also runs two SYS-invariant preservation checks (not guard groups) with z3.

Run: python3 check_guards.py  (needs z3-solver; writes guard-results.txt)
Set STATERADAR_PACK to the pack checkout (default: ../../../../pack).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PACK = Path(os.environ.get("STATERADAR_PACK", HERE.parents[2] / "pack"))
sys.path.insert(0, str(PACK / "tools"))
import guard_proofs  # noqa: E402
import z3  # noqa: E402

results = []
probes_out = []

# ---------------------------------------------------------------- G-01
ic, mi, mc = z3.Ints("InitialCap MaxIdle MaxCap")
valid = z3.And(ic <= mi, mc >= mi, ic >= 0)          # channel.go:59
g01 = [("valid", valid), ("invalid", z3.Not(valid))]
results.append(guard_proofs.check_group("G-01 config validation", g01, has_else=True))
probes_out.append(("G-01", guard_proofs.boundary_probe(g01, [
    {ic: 5, mi: 5, mc: 5}, {ic: 6, mi: 5, mc: 5}, {ic: 4, mi: 5, mc: 5},
    {ic: 0, mi: 5, mc: 4}, {ic: 0, mi: 5, mc: 5}, {ic: 0, mi: 5, mc: 6},
    {ic: -1, mi: 0, mc: 0}, {ic: 0, mi: 0, mc: 0},
])))
# Finding probe: is MaxCap == 0 accepted?  (every Get would wait)
s = z3.Solver(); s.add(valid, mc == 0)
maxcap0 = s.check() == z3.sat
# Implication: valid ⇒ InitialCap ≤ MaxCap
s = z3.Solver(); s.add(valid, ic > mc)
ic_le_mc = s.check() == z3.unsat

# ---------------------------------------------------------------- G-02
o, m = z3.Ints("openingConns maxActive")
fnil = z3.Bool("factoryNil")
nat02 = [m >= 0]                                       # MaxCap >= MaxIdle >= 0 (G-01)
g02 = [("wait", o >= m),                               # channel.go:133
       ("closed", z3.And(o < m, fnil)),                # channel.go:150
       ("create", z3.And(o < m, z3.Not(fnil)))]        # channel.go:154
results.append(guard_proofs.check_group("G-02 Get default branch", g02, assumptions=nat02))
probes_out.append(("G-02", guard_proofs.boundary_probe(g02, [
    {o: 99, m: 100, fnil: False}, {o: 100, m: 100, fnil: False},
    {o: 101, m: 100, fnil: False}, {o: 0, m: 0, fnil: False},
    {o: 99, m: 100, fnil: True},
])))

# ---------------------------------------------------------------- G-03
age, to = z3.Ints("ageMs idleTimeoutMs")
nat03 = [age >= 0]
expired = z3.And(to > 0, age > to)                     # channel.go:115-116 (strict Before)
g03 = [("expired", expired), ("keep", z3.Not(expired))]
results.append(guard_proofs.check_group("G-03 idle expiry", g03, assumptions=nat03, has_else=True))
probes_out.append(("G-03", guard_proofs.boundary_probe(g03, [
    {age: 14999, to: 15000}, {age: 15000, to: 15000}, {age: 15001, to: 15000},
    {age: 10**9, to: 0},
])))

# ---------------------------------------------------------------- G-04
cnil = z3.Bool("connsNil")
w, idle, cap = z3.Ints("waiters idle maxIdle")
nat04 = [w >= 0, idle >= 0, cap >= 0, idle <= cap]
g04 = [("closed", cnil),                                               # channel.go:174
       ("handoff", z3.And(z3.Not(cnil), w > 0)),                       # channel.go:179
       ("enqueue", z3.And(z3.Not(cnil), w == 0, idle < cap)),          # channel.go:190
       ("overflow", z3.And(z3.Not(cnil), w == 0, idle >= cap))]        # channel.go:193
results.append(guard_proofs.check_group("G-04 Put branches", g04, assumptions=nat04))
probes_out.append(("G-04", guard_proofs.boundary_probe(g04, [
    {cnil: False, w: 0, idle: 9, cap: 10}, {cnil: False, w: 0, idle: 10, cap: 10},
    {cnil: False, w: 1, idle: 0, cap: 10}, {cnil: True, w: 3, idle: 0, cap: 10},
    {cnil: False, w: 0, idle: 0, cap: 0},
])))

# ---------------------------------------------------------------- G-05
clnil = z3.Bool("closeNil")
g05 = [("skip", clnil), ("count", z3.Not(clnil))]      # channel.go:208-211
results.append(guard_proofs.check_group("G-05 Close counting", g05, has_else=True))

# ---------------------------------------------------------------- G-08
snil = z3.Bool("connsSnapshotNil")
g08 = [("early-return", snil), ("drain", z3.Not(snil))]  # channel.go:234
results.append(guard_proofs.check_group("G-08 Release re-entry", g08, has_else=True))

# ------------------------------------------------ SYS invariant checks
# SYS-3: waiters > 0  ⇒  idle == 0 ∧ openingConns ≥ maxActive
# (a waiter exists only when no capacity is free).  Is it preserved by
# Close (o' = o - 1, w' = w, idle' = idle)?  channel.go:211
def sys3(w_, idle_, o_, m_):
    return z3.Implies(w_ > 0, z3.And(idle_ == 0, o_ >= m_))

s = z3.Solver()
s.add(w >= 0, idle >= 0, m >= 0, sys3(w, idle, o, m), z3.Not(sys3(w, idle, o - 1, m)))
sys3_close = s.check()
sys3_witness = s.model() if sys3_close == z3.sat else None

# SYS-4: after Release (conns nil) no waiter remains (w' == 0).
# Release sets connsNil and leaves connReqs unchanged: w' = w.  channel.go:225-232
s = z3.Solver()
s.add(w >= 0, w > 0)          # any pre-state with a waiter
sys4_release = s.check()      # sat ⇒ post-state has w' = w > 0 with conns nil

# ---------------------------------------------------------------- render
lines = [guard_proofs.render(results)]
lines.append("group G-06 Get receive gate: not-formalizable: external-call: "
             "the Ping callback result (channel.go:124) decides one branch; "
             "inspection (unproven): branches are checked in sequence nil -> expired -> ping -> accept, "
             "so they are disjoint by order; coverage by the final return (channel.go:129)")
lines.append("group G-07 waiter wake: not-formalizable: dynamic-state: ok depends on whether any "
             "goroutine closes the waiter channel; inspection (unproven): no statement in channel.go "
             "closes a req channel, so the !ok branch (channel.go:138-139) is unreachable as-is")
lines.append("")
lines.append("boundary probes:")
for gid, rows in probes_out:
    for assignment, labels in rows:
        lines.append(f"  {gid} {assignment} -> {labels}")
lines.append("")
lines.append("facts:")
lines.append(f"  G-01 MaxCap == 0 accepted by validation: {maxcap0}  (finding -> Q-14)")
lines.append(f"  G-01 valid => InitialCap <= MaxCap: {ic_le_mc}")
lines.append("")
lines.append("SYS invariant checks (z3, assumptions: waiters>=0, idle>=0, maxActive>=0):")
lines.append(f"  SYS-3 preserved by Close: {'violation' if sys3_close == z3.sat else 'proven'}"
             + (f" (witness: {guard_proofs._witness(sys3_witness, None)})" if sys3_witness is not None else ""))
lines.append(f"  SYS-4 established by Release: {'violation' if sys4_release == z3.sat else 'proven'}"
             " (Release leaves connReqs unchanged; any pre-state with waiters > 0 keeps them)")
text = "\n".join(lines) + "\n"
(HERE / "guard-results.txt").write_text(text, encoding="utf-8")
print(text)
bad = [r for r in results if r.outcome != "proven"]
sys.exit(1 if bad else 0)
