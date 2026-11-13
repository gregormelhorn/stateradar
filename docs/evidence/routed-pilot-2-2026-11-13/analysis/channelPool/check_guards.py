#!/usr/bin/env python3
"""channelPool guard proofs (02-pilot Step 4). Component-specific part only:
typed variables, NAT domains, guard expressions. The proof procedure is the
pack library tools/guard_proofs.py. Run: python3 check_guards.py [PACK_TOOLS]"""
import sys
from pathlib import Path
PACK_TOOLS = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / "pack" / "tools"
sys.path.insert(0, str(PACK_TOOLS))
import guard_proofs as gp  # noqa: E402
import z3  # noqa: E402

results, probes, extra = [], [], []

# G-01 construction validation, channel.go:59-67
init, idle_max, cap_ = z3.Ints("InitialCap MaxIdle MaxCap")
fac_nil, close_nil = z3.Bools("FactoryNil CloseNil")
bad_cap = z3.Not(z3.And(init <= idle_max, cap_ >= idle_max, init >= 0))
g01 = [("invalid-capacity", bad_cap),
       ("nil-factory", z3.And(z3.Not(bad_cap), fac_nil)),
       ("nil-close", z3.And(z3.Not(bad_cap), z3.Not(fac_nil), close_nil)),
       ("valid", z3.And(z3.Not(bad_cap), z3.Not(fac_nil), z3.Not(close_nil)))]
results.append(gp.check_group("G-01 construction validation", g01))
valid_cap = z3.Not(bad_cap)
s = z3.Solver(); s.add(valid_cap, z3.Not(z3.And(idle_max >= 0, cap_ >= init, cap_ >= 0)))
extra.append(f"G-01 implication valid => MaxIdle>=0 and MaxCap>=InitialCap>=0: {'proven' if s.check() == z3.unsat else 'violation ' + str(s.model())}")
s = z3.Solver(); s.add(valid_cap, cap_ == 0)
extra.append(f"G-01 witness: MaxCap == 0 accepted by validation: {'yes ' + str(s.model()) if s.check() == z3.sat else 'no'}")
probes.append(("G-01", g01, [{init: i, idle_max: 5, cap_: 10, fac_nil: False, close_nil: False} for i in (-1, 0, 1, 4, 5, 6)]
               + [{init: 0, idle_max: 5, cap_: m, fac_nil: False, close_nil: False} for m in (4, 5, 6)]))

# G-02 idle-expiry decision, channel.go:115-116 (and 141-142); age = now - t in ns (Int), NAT age >= 0
timeout, age = z3.Ints("IdleTimeout age")
nat02 = [age >= 0]
discard = z3.And(timeout > 0, age > timeout)  # t.Add(timeout).Before(now) <=> now - t > timeout
g02 = [("discard", discard), ("keep", z3.Not(discard))]
results.append(gp.check_group("G-02 idle-expiry decision", g02, assumptions=nat02))
probes.append(("G-02", g02, [{timeout: 100, age: a} for a in (99, 100, 101)] + [{timeout: t, age: 50} for t in (-1, 0, 1)]))

# G-04 Get slow path, channel.go:133, 150, 155
opening, max_active = z3.Ints("openingConns maxActive")
factory_nil, factory_err = z3.Bools("factoryNil factoryErr")
below = opening < max_active
g04 = [("wait", z3.Not(below)),
       ("ErrClosed", z3.And(below, factory_nil)),
       ("factory-error", z3.And(below, z3.Not(factory_nil), factory_err)),
       ("create", z3.And(below, z3.Not(factory_nil), z3.Not(factory_err)))]
results.append(gp.check_group("G-04 Get slow path", g04, assumptions=[max_active >= 0]))
probes.append(("G-04", g04, [{opening: o, max_active: 10, factory_nil: False, factory_err: False} for o in (9, 10, 11)]
               + [{opening: 10, max_active: 10, factory_nil: True, factory_err: False}]))
s = z3.Solver(); s.add(max_active >= 0, factory_nil, z3.Not(below))
extra.append("G-04 ordering: released (factoryNil) and at capacity selects 'wait', not 'ErrClosed': "
             + ("witness " + str(s.model()) if s.check() == z3.sat else "unreachable"))

# G-05 waiter wake-up, channel.go:138-148
ok = z3.Bool("reqOpen")
expired = z3.And(timeout > 0, age > timeout)
g05 = [("ErrMaxActiveConnReached", z3.Not(ok)), ("discard-retry", z3.And(ok, expired)), ("deliver", z3.And(ok, z3.Not(expired)))]
results.append(gp.check_group("G-05 waiter wake-up", g05, assumptions=nat02))
probes.append(("G-05", g05, [{ok: True, timeout: 100, age: a} for a in (99, 100, 101)] + [{ok: False, timeout: 100, age: 0}]))

# G-06 Put routing, channel.go:168, 174, 179, 189-196
conn_nil, released = z3.Bools("connNil released")
waiters, idle = z3.Ints("waiters idle")
nat06 = [idle >= 0, idle <= idle_max, waiters >= 0, idle_max >= 0]
live = z3.And(z3.Not(conn_nil), z3.Not(released))
g06 = [("reject-nil", conn_nil),
       ("released-close", z3.And(z3.Not(conn_nil), released)),
       ("handoff", z3.And(live, waiters > 0)),
       ("enqueue", z3.And(live, waiters == 0, idle < idle_max)),
       ("overflow-close", z3.And(live, waiters == 0, idle >= idle_max))]
results.append(gp.check_group("G-06 Put routing", g06, assumptions=nat06))
probes.append(("G-06", g06, [{conn_nil: False, released: False, waiters: 0, idle: i, idle_max: 10} for i in (9, 10)]
               + [{conn_nil: False, released: False, waiters: w, idle: 0, idle_max: 10} for w in (0, 1)]
               + [{conn_nil: False, released: False, waiters: 0, idle: 0, idle_max: 0}]))

# G-07 Close routing, channel.go:203, 208
closefn_nil = z3.Bool("closeFnNil")
g07 = [("reject-nil", conn_nil), ("released-noop", z3.And(z3.Not(conn_nil), closefn_nil)),
       ("decrement-close", z3.And(z3.Not(conn_nil), z3.Not(closefn_nil)))]
results.append(gp.check_group("G-07 Close routing", g07))

# G-08 Release routing, channel.go:234
conns_nil = z3.Bool("connsNil")
g08 = [("already-released", conns_nil), ("release", z3.Not(conns_nil))]
results.append(gp.check_group("G-08 Release routing", g08))

# G-09 Get entry, channel.go:105, 111
snap_nil, recv_nil = z3.Bools("snapshotNil receivedNil")
g09 = [("ErrClosed-snapshot", snap_nil), ("ErrClosed-closed-channel", z3.And(z3.Not(snap_nil), recv_nil)),
       ("proceed", z3.And(z3.Not(snap_nil), z3.Not(recv_nil)))]
results.append(gp.check_group("G-09 Get entry", g09))

lines = [gp.render(results),
         "group G-03 ping validity: not-formalizable: external-call: the branch depends on the user Ping callback result (channel.go:123-124)"]
lines += extra
lines.append("boundary probes:")
for name, guards, assigns in probes:
    for a, fired in gp.boundary_probe(guards, assigns):
        lines.append(f"  {name} {a} -> {fired}")
text = "\n".join(lines)
(Path(__file__).resolve().parent / "guard-results.txt").write_text(text + "\n", encoding="utf-8")
print(text)
sys.exit(1 if any(r.outcome == "violation" for r in results) else 0)
