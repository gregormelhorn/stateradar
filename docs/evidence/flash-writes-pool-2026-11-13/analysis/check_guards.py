#!/usr/bin/env python3
"""z3 guard proofs for channelPool (delegates the proof loop to the pack library).

Run: python3 check_guards.py  (needs z3-solver; STATERADAR_PACK points at the pack checkout)
Writes guard-results.txt next to this file.
"""
import os, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
PACK = Path(os.environ.get("STATERADAR_PACK", HERE.parents[2] / "stateradar"))
sys.path.insert(0, str(PACK / "tools"))
import z3, guard_proofs as gp

Int, Bool, And, Or, Not = z3.Int, z3.Bool, z3.And, z3.Or, z3.Not
results, notes = [], []

# ---- G-01 Get: idle-timeout test (channel.go:115-121, 141-147) -----------------
timeout, t, now = Int("timeout"), Int("t"), Int("now")
nat1 = [timeout >= 0, t <= now]            # NAT-05 (config), NAT-07 (clock does not go backwards; abstract integer ticks)
expired = And(timeout > 0, t + timeout < now)           # wrapConn.t.Add(timeout).Before(time.Now())
fresh_untimed = timeout <= 0
fresh_timed = And(timeout > 0, t + timeout >= now)
g1 = [("expired", expired), ("fresh-untimed", fresh_untimed), ("fresh-timed", fresh_timed)]
results.append(gp.check_group("G-01 get-idle-timeout", g1, assumptions=nat1))
for a, lab in [({timeout: 10, t: 0, now: 9}, "below"), ({timeout: 10, t: 0, now: 10}, "at"), ({timeout: 10, t: 0, now: 11}, "above"), ({timeout: 0, t: 0, now: 99}, "timeout=0")]:
    for asg, fired in gp.boundary_probe(g1, [a]):
        notes.append(f"probe G-01 {lab}: {asg} -> {fired}")

# ---- G-02 Get: default branch after an empty idle channel (channel.go:133-161) --
oc, mx, factory_nil = Int("openingConns"), Int("maxActive"), Bool("factoryNil")
nat2 = [oc >= 0, mx >= 0]                  # NAT-05 (maxActive >= MaxIdle >= 0); openingConns >= 0 holds while NAT-02 holds
g2 = [("wait", oc >= mx), ("closed", And(oc < mx, factory_nil)), ("create", And(oc < mx, Not(factory_nil)))]
results.append(gp.check_group("G-02 get-default-branch", g2, assumptions=nat2))
for a, lab in [({oc: 4, mx: 5, factory_nil: False}, "below"), ({oc: 5, mx: 5, factory_nil: False}, "at"), ({oc: 6, mx: 5, factory_nil: False}, "above"), ({oc: 0, mx: 0, factory_nil: False}, "zero-cap")]:
    for asg, fired in gp.boundary_probe(g2, [a]):
        notes.append(f"probe G-02 {lab}: {asg} -> {fired}")

# ---- G-03 Put (channel.go:168-198) ---------------------------------------------
nilc, conns_nil, waiters, idle, maxidle = Bool("connIsNil"), Bool("connsNil"), Int("waiters"), Int("idle"), Int("MaxIdle")
nat3 = [waiters >= 0, maxidle >= 0, idle >= 0, idle <= maxidle]       # channel capacity bounds the idle count (NAT-06)
open_ = And(Not(nilc), Not(conns_nil))
g3 = [("reject-nil", nilc), ("closed-pool", And(Not(nilc), conns_nil)), ("hand-to-waiter", And(open_, waiters > 0)),
      ("store-idle", And(open_, waiters == 0, idle < maxidle)), ("channel-full", And(open_, waiters == 0, idle >= maxidle))]
results.append(gp.check_group("G-03 put-branches", g3, assumptions=nat3))
for a, lab in [({nilc: False, conns_nil: False, waiters: 0, idle: 2, maxidle: 3}, "below"), ({nilc: False, conns_nil: False, waiters: 0, idle: 3, maxidle: 3}, "at"),
               ({nilc: False, conns_nil: False, waiters: 1, idle: 3, maxidle: 3}, "waiter+full"), ({nilc: False, conns_nil: False, waiters: 0, idle: 0, maxidle: 0}, "MaxIdle=0")]:
    for asg, fired in gp.boundary_probe(g3, [a]):
        notes.append(f"probe G-03 {lab}: {asg} -> {fired}")

# ---- G-04 NewChannelPool capacity validation (channel.go:59) --------------------
init, mi, mc = Int("InitialCap"), Int("MaxIdle"), Int("MaxCap")
valid = And(init <= mi, mc >= mi, init >= 0)
g4 = [("accepted", valid), ("rejected", Not(valid))]
results.append(gp.check_group("G-04 new-capacity-validation", g4, assumptions=[]))
for a, lab in [({init: 1, mi: 1, mc: 1}, "at"), ({init: 2, mi: 1, mc: 1}, "init>idle"), ({init: 0, mi: 2, mc: 1}, "cap<idle"), ({init: -1, mi: 0, mc: 0}, "init<0"), ({init: 0, mi: 0, mc: 0}, "all-zero")]:
    for asg, fired in gp.boundary_probe(g4, [a]):
        notes.append(f"probe G-04 {lab}: {asg} -> {fired}")
s = z3.Solver(); s.add(valid, mc == 0)
notes.append(f"z3 invariant check: validation accepts MaxCap = 0: {s.check()} (witness {s.model() if s.check()==z3.sat else None}) -> Q-17")
s = z3.Solver(); s.add(valid, mi == 0)
notes.append(f"z3 invariant check: validation accepts MaxIdle = 0: {s.check()} -> Q-17")

# ---- G-05 Close (channel.go:203-212) -------------------------------------------
close_nil = Bool("closeFnNil")
g5 = [("reject-nil", nilc), ("no-close-func", And(Not(nilc), close_nil)), ("close-and-decrement", And(Not(nilc), Not(close_nil)))]
results.append(gp.check_group("G-05 close-branches", g5, assumptions=[]))

# ---- SYS-01 as a z3 check: Close below zero without NAT-02 ----------------------
oc2 = Int("openingConns_after")
s = z3.Solver(); s.add(oc == 0, oc2 == oc - 1, oc2 < 0)
notes.append(f"z3 invariant check: SYS-01 (0 <= openingConns) after one Close at openingConns = 0 is {'violated' if s.check()==z3.sat else 'kept'} without NAT-02 -> Q-12, Q-14")

text = gp.render(results)
# guards that never reach z3 (PA-3b)
text += "\n" + "\n".join([
 "group G-06 get-ping-verdict (channel.go:124): not-formalizable: external-call: the Ping callback's error result decides",
 "group G-07 get-factory-result (channel.go:154-158): not-formalizable: external-call: the Factory callback's (conn, err) result decides",
 "group G-08 get-waiter-receive (channel.go:137-140): not-formalizable: dynamic-state: whether the req channel is closed or delivered depends on runtime scheduling",
])
text += "\n\n" + "\n".join(notes) + "\n"
(HERE / "guard-results.txt").write_text(text)
print(text)
sys.exit(1 if any(r.outcome != "proven" for r in results) else 0)
