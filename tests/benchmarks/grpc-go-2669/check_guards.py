#!/usr/bin/env python3
"""Guard proofs for grpc-go v1.18.0 addrConn (disposition-matrix.md G-01..G-12).

Component-specific encodings only; proof procedures delegated to the
pack library tools/guard_proofs.py (02-pilot v1.15).

Run:
  uv run --with-requirements <pack>/tools/requirements-dev.txt \
      python3 check_guards.py > guard-results.txt

State encoding (connectivity/connectivity.go:52-63):
  Idle=0 Connecting=1 Ready=2 TransientFailure=3 Shutdown=4
GoAwayReason (internal/transport/transport.go:714-724):
  Invalid=0 NoReason=1 TooManyPings=2
RequireHandshake (internal/envconfig/envconfig.go:37-46):
  Hybrid=0 On=1 Off=2
"""
from __future__ import annotations

import sys
from pathlib import Path

PACK_TOOLS = Path(__file__).resolve().parents[3] / "tools"
sys.path.insert(0, str(PACK_TOOLS))

import guard_proofs  # noqa: E402
import z3  # noqa: E402

results = []

# NAT domain: state is one of the five enum values.
s = z3.Int("state")
state_dom = [s >= 0, s <= 4]

# G-01 connect() dispatch (clientconn.go:671-679)
results.append(guard_proofs.check_group(
    "G-01 connect-state-dispatch",
    [("shutdown->reject", s == 4),
     ("non-idle->noop", z3.And(s != 4, s != 0)),
     ("idle->dial", s == 0)],
    assumptions=state_dom))

# G-02 tryUpdateAddrs dispatch (clientconn.go:698-721)
found = z3.Bool("curAddrFound")
results.append(guard_proofs.check_group(
    "G-02 tryUpdateAddrs-dispatch",
    [("shutdown->mutate-true", s == 4),
     ("not-ready->false", z3.And(s != 4, s != 2)),
     ("ready-found->keep", z3.And(s == 2, found)),
     ("ready-notfound->false", z3.And(s == 2, z3.Not(found)))],
    assumptions=state_dom))

# G-03 getReadyTransport dispatch (clientconn.go:1304-1318)
t = z3.Bool("transportSet")
g3 = [("ready-with-transport", z3.And(s == 2, t)),
      ("idle->connect", z3.And(z3.Not(z3.And(s == 2, t)), s == 0)),
      ("else->nil", z3.And(z3.Not(z3.And(s == 2, t)), s != 0))]
results.append(guard_proofs.check_group(
    "G-03 getReadyTransport-dispatch", g3, assumptions=state_dom))
G3_BOUNDARY = guard_proofs.boundary_probe(
    g3, [{s: 2, t: True}, {s: 2, t: False}, {s: 0, t: False}, {s: 4, t: False}])

# G-04 dial deadline max (clientconn.go:991-995), seconds as Real
b = z3.Real("backoffForSec")
m = z3.Real("minConnectTimeoutSec")
nat4 = [b >= 0, m == 20]
g4 = [("min-wins", b <= m), ("backoff-wins", b > m)]
results.append(guard_proofs.check_group(
    "G-04 dial-deadline-max", g4, assumptions=nat4))
G4_BOUNDARY = guard_proofs.boundary_probe(
    g4, [{b: 19.9, m: 20.0}, {b: 20.0, m: 20.0}, {b: 20.1, m: 20.0}])

# G-05 updateConnectivityState terminality (clientconn.go:936-942).
# The code's only guard is s_new == s_cur. SYS-1 demands: no write when
# s_cur == Shutdown. Prove the write guard does NOT entail the terminal
# guard: sat(s_cur==4 and s_new != s_cur) => violation with witness.
s_cur, s_new = z3.Int("s_cur"), z3.Int("s_new")
solver = z3.Solver()
solver.add(s_cur >= 0, s_cur <= 4, s_new >= 0, s_new <= 4)
solver.add(s_cur == 4, s_new != s_cur)  # write proceeds (only guard: inequality)
if solver.check() == z3.sat:
    mdl = solver.model()
    results.append(guard_proofs.GroupResult(
        name="G-05 updateConnectivityState-terminality",
        outcome="violation",
        findings=[
            "SYS-1: write guard (s_new != s_cur) admits transitions out of "
            f"Shutdown — witness s_cur={mdl[s_cur]}, s_new={mdl[s_new]} "
            "(clientconn.go:936-942 has no terminal guard; contrast "
            "clientconn.go:340-342). Reached via cell (Shutdown, UV08) -> Q-01."]))
else:
    results.append(guard_proofs.GroupResult(
        name="G-05 updateConnectivityState-terminality", outcome="proven"))

# G-06 reportHealth dispatch (clientconn.go:1262-1273)
same_tr, ok = z3.Bool("transportIsNewTr"), z3.Bool("healthOk")
results.append(guard_proofs.check_group(
    "G-06 reportHealth-dispatch",
    [("stale->noop", z3.Not(same_tr)),
     ("ok->ready", z3.And(same_tr, ok)),
     ("bad->transient-failure", z3.And(same_tr, z3.Not(ok)))]))

# G-07 adjustParams (clientconn.go:955-963)
r = z3.Int("goAwayReason")
v, mkp = z3.Real("twoXKeepalive"), z3.Real("mkpTime")
nat7 = [r >= 0, r <= 2, v >= 0, mkp >= 0]
g7 = [("too-many-pings-bump", z3.And(r == 2, v > mkp)),
      ("too-many-pings-nobump", z3.And(r == 2, v <= mkp)),
      ("other-reason-noop", r != 2)]
results.append(guard_proofs.check_group(
    "G-07 adjustParams-dispatch", g7, assumptions=nat7))
G7_BOUNDARY = guard_proofs.boundary_probe(
    g7, [{r: 2, v: 9.0, mkp: 10.0}, {r: 2, v: 10.0, mkp: 10.0},
         {r: 2, v: 11.0, mkp: 10.0}, {r: 1, v: 11.0, mkp: 10.0}])

# G-08 health-managing gate (clientconn.go:1039-1043)
dis, cfg, en, fn = (z3.Bool("disableHealthCheck"), z3.Bool("healthCfgSet"),
                    z3.Bool("scoptsEnabled"), z3.Bool("healthFuncSet"))
managing = z3.And(z3.Not(dis), cfg, en, fn)
results.append(guard_proofs.check_group(
    "G-08 health-managing-gate",
    [("managing", managing), ("not-managing", z3.Not(managing))]))

# G-09 reqHandshake mode dispatch (clientconn.go:1073/1104, 1190/1202)
h = z3.Int("reqHandshake")
results.append(guard_proofs.check_group(
    "G-09 reqHandshake-mode-dispatch",
    [("hybrid", h == 0), ("on", h == 1), ("off", h == 2)],
    assumptions=[h >= 0, h <= 2]))

# G-10 backoff first-retry branch (internal/backoff/backoff.go:60-62)
retries = z3.Int("retries")
g10 = [("first->baseDelay", retries == 0), ("later->exponential", retries > 0)]
results.append(guard_proofs.check_group(
    "G-10 backoff-first-retry", g10, assumptions=[retries >= 0]))
G10_BOUNDARY = guard_proofs.boundary_probe(
    g10, [{retries: 0}, {retries: 1}, {retries: 2}])

print(guard_proofs.render(results))

# Not-formalizable groups (PA-3b) — appended by the per-run script.
print("group G-11 envconfig-requirehandshake-parse: not-formalizable")
print("  - unstructured-payload: env-string switch "
      "(internal/envconfig/envconfig.go:58-68); inspection: case \"on\" has "
      "an empty body, so \"on\" -> zero value Hybrid while unset -> On; "
      "contradicts envconfig.go:41-43 -> Q-05. Unproven inspection reasoning.")
print("group G-12 backoff-select-ordering: not-formalizable")
print("  - dynamic-state: select over timer.C / resetBackoff / ctx.Done "
      "(clientconn.go:1133-1143) depends on runtime channel readiness; "
      "dispositions carried by cells (TransientFailure_Backoff, E11/E05/E02) "
      "and pair P-02.")

print()
print("boundary probes:")
for name, rows in (("G-03", G3_BOUNDARY), ("G-04", G4_BOUNDARY),
                   ("G-07", G7_BOUNDARY), ("G-10", G10_BOUNDARY)):
    for assignment, labels in rows:
        print(f"  {name} {assignment} -> {labels}")
