#!/usr/bin/env python3
"""channelPool guard proofs (02-pilot Step 4). Component-specific part only:
typed variables, NAT domains, guard expressions. The proof procedure is the
pack library tools/guard_proofs.py.

Run: uv run --with-requirements <pack>/tools/requirements-dev.txt \
         python3 domain-analysis/channelPool/check_guards.py
Writes guard-results.txt next to this file. Exit 1 on any violation
(a violation is a finding, recorded in the matrix guard notes).
"""
from __future__ import annotations

import sys
from pathlib import Path

PACK_TOOLS = Path(__file__).resolve().parents[3] / "stateradar" / "tools"
sys.path.insert(0, str(PACK_TOOLS))
import guard_proofs  # noqa: E402
import z3  # noqa: E402

HERE = Path(__file__).resolve().parent
results = []
probes: list[str] = []

# Context variables (Go ints; durations in ns as Int)
i = z3.Int("idle")            # len(conns)
M = z3.Int("maxIdle")         # cap(conns) = MaxIdle
o = z3.Int("openingConns")
X = z3.Int("maxCap")
w = z3.Int("waiters")
released = z3.Bool("released")
age = z3.Int("idleAge")
T = z3.Int("idleTimeout")
pingSet = z3.Bool("pingConfigured")
pingErr = z3.Bool("pingError")
isNil = z3.Bool("connIsNil")
errNil = z3.Bool("factoryErrNil")
ok = z3.Bool("waiterChanOpen")

# NAT domains (invariants-and-lints.md): NAT-7 config domain after G-01,
# channel capacity bounds the idle count, counts are non-negative.
NAT_CFG = [M >= 0, X >= M]
NAT_IDLE = [i >= 0, i <= M]
NAT_W = [w >= 0]
NAT_AGE = [age >= 0]

# G-01 NewChannelPool validation (channel.go:59)
ic, mi, mc = z3.Ints("InitialCap MaxIdle MaxCap")
valid = z3.And(ic <= mi, mc >= mi, ic >= 0)
g01 = [("accept", valid), ("reject", z3.Not(valid))]
results.append(guard_proofs.check_group("G-01 NewChannelPool validation", g01))
for row in guard_proofs.boundary_probe(g01, [
        {ic: 0, mi: 0, mc: 0}, {ic: -1, mi: 0, mc: 0}, {ic: 1, mi: 0, mc: 0},
        {ic: 2, mi: 2, mc: 2}, {ic: 2, mi: 3, mc: 2}, {ic: 2, mi: 2, mc: 3}]):
    probes.append(f"G-01 {row[0]} -> {row[1]}")

# G-02 GET dispatch (channel.go:105-161). Idle path first (select receive
# ready iff i >= 1); default branch: at-cap test precedes the released test.
g02 = [
    ("idle-path", i >= 1),
    ("wait", z3.And(i == 0, o >= X)),
    ("reject-closed", z3.And(i == 0, o < X, released)),
    ("create", z3.And(i == 0, o < X, z3.Not(released))),
]
# released=True here means: the Get captured the idle store before Release
# (P-02b window). It can still dequeue an idle conn during Release's drain,
# so the idle path does not depend on released.
nat02 = NAT_CFG + NAT_IDLE
results.append(guard_proofs.check_group("G-02 GET dispatch", g02, assumptions=nat02))
for row in guard_proofs.boundary_probe(g02, [
        {i: 1, o: 5, X: 5, released: False}, {i: 1, o: 5, X: 5, released: True},
        {i: 0, o: 4, X: 5, released: False},
        {i: 0, o: 5, X: 5, released: False}, {i: 0, o: 6, X: 5, released: False},
        {i: 0, o: 4, X: 5, released: True}, {i: 0, o: 5, X: 5, released: True},
        {i: 0, o: 0, X: 0, released: False}]):
    probes.append(f"G-02 {row[0]} -> {row[1]}")

# G-03 idle-conn acceptance on the GET idle path (channel.go:115-129)
expired = z3.And(T > 0, age > T)          # t+T before now  <=>  age > T
g03 = [
    ("discard-expired", expired),
    ("discard-ping", z3.And(z3.Not(expired), pingSet, pingErr)),
    ("return", z3.And(z3.Not(expired), z3.Not(z3.And(pingSet, pingErr)))),
]
results.append(guard_proofs.check_group("G-03 GET idle-conn acceptance", g03, assumptions=NAT_AGE))
for row in guard_proofs.boundary_probe(g03, [
        {T: 100, age: 99, pingSet: False, pingErr: False},
        {T: 100, age: 100, pingSet: False, pingErr: False},
        {T: 100, age: 101, pingSet: False, pingErr: False},
        {T: 0, age: 10**12, pingSet: False, pingErr: False},
        {T: -1, age: 10**12, pingSet: False, pingErr: False},
        {T: 100, age: 50, pingSet: True, pingErr: True},
        {T: 100, age: 50, pingSet: False, pingErr: True}]):
    probes.append(f"G-03 {row[0]} -> {row[1]}")

# G-04 PUT dispatch (channel.go:168-197)
g04 = [
    ("reject-nil", isNil),
    ("released-close", z3.And(z3.Not(isNil), released)),
    ("hand-off", z3.And(z3.Not(isNil), z3.Not(released), w >= 1)),
    ("enqueue", z3.And(z3.Not(isNil), z3.Not(released), w == 0, i < M)),
    ("close-full", z3.And(z3.Not(isNil), z3.Not(released), w == 0, i >= M)),
]
results.append(guard_proofs.check_group("G-04 PUT dispatch", g04, assumptions=NAT_CFG + NAT_IDLE + NAT_W))
for row in guard_proofs.boundary_probe(g04, [
        {isNil: False, released: False, w: 0, i: 9, M: 10},
        {isNil: False, released: False, w: 0, i: 10, M: 10},
        {isNil: False, released: False, w: 1, i: 0, M: 10},
        {isNil: False, released: False, w: 0, i: 0, M: 0},
        {isNil: False, released: True, w: 3, i: 0, M: 10}]):
    probes.append(f"G-04 {row[0]} -> {row[1]}")

# G-05 CLOSE (channel.go:203-212); close callback cleared <=> released
# (NewChannelPool requires a Close callback, channel.go:65).
g05 = [
    ("reject-nil", isNil),
    ("released-noop", z3.And(z3.Not(isNil), released)),
    ("decrement-and-close", z3.And(z3.Not(isNil), z3.Not(released))),
]
results.append(guard_proofs.check_group("G-05 CLOSE", g05))

# G-06 Factory result (channel.go:154-161); connection nil-ness is not a guard.
connNil = z3.Bool("factoryConnNil")
g06 = [("return-error", z3.Not(errNil)), ("count-and-return", errNil)]
results.append(guard_proofs.check_group("G-06 Factory result", g06))
for row in guard_proofs.boundary_probe(g06, [
        {errNil: True, connNil: True}, {errNil: False, connNil: False}]):
    probes.append(f"G-06 {row[0]} -> {row[1]} (conn value never inspected)")

# G-07 woken waiting Get (channel.go:138-148)
g07 = [
    ("err-max-active", z3.Not(ok)),
    ("discard-expired", z3.And(ok, expired)),
    ("return", z3.And(ok, z3.Not(expired))),
]
results.append(guard_proofs.check_group("G-07 woken waiter", g07, assumptions=NAT_AGE))
probes.append("G-07 reachability: no statement closes a waiter channel "
              "(grep 'close(req' in channel.go: none), so 'err-max-active' is dead")

# G-08 RELEASE (channel.go:234-242)
g08 = [("already-released", released), ("clear-and-drain", z3.Not(released))]
results.append(guard_proofs.check_group("G-08 RELEASE", g08))

# G-09 PING method (channel.go:216-220): non-nil conn calls c.ping without a
# nil check; calling it requires a configured Ping. No else branch exists.
g09 = [("reject-nil", isNil), ("call-ping", z3.And(z3.Not(isNil), pingSet))]
results.append(guard_proofs.check_group("G-09 PING method", g09))

text = guard_proofs.render(results)
text += "\n\nBoundary probes (assignment -> guards that fire):\n" + "\n".join(probes) + "\n"
text += "\nNot-formalizable groups: none.\n"
(HERE / "guard-results.txt").write_text(text, encoding="utf-8")
print(text)
sys.exit(1 if any(r.outcome == "violation" for r in results) else 0)
