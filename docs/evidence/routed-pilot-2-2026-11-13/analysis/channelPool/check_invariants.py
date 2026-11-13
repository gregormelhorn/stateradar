#!/usr/bin/env python3
"""channelPool SYS-invariant step checks with z3 (Step 5, per-run checker).
Each transition is encoded from the code; each query asks whether an
invariant-satisfying pre-state can step to a violating post-state.
sat = violation witness, unsat = the step preserves the invariant."""
import sys
from pathlib import Path
import z3

opening, idle, out, maxc, max_idle, waiters, live = z3.Ints("openingConns idle checkedOut MaxCap MaxIdle waiters liveConns")
o2, i2, out2, w2, live2 = z3.Ints("openingConns' idle' checkedOut' waiters' liveConns'")
dom = [maxc >= 0, max_idle >= 0, max_idle <= maxc, idle >= 0, idle <= max_idle, out >= 0, waiters >= 0]
SYS1 = lambda o: z3.And(o >= 0, o <= maxc)                       # 0 <= openingConns <= MaxCap
SYS2 = lambda o, i, c: o == i + c                                  # openingConns == idle + checked out
SYS3 = lambda w, i, o: z3.Implies(w > 0, z3.And(i == 0, o >= maxc))  # no waiter while capacity is free
LIVE = lambda l: l <= maxc                                         # live connections created by the pool <= MaxCap
rows = []

def query(name, pre, step, post_ok):
    s = z3.Solver(); s.add(*dom, *pre, *step, z3.Not(post_ok))
    r = s.check()
    rows.append(f"{name}: {'violation, witness ' + str(s.model()) if r == z3.sat else 'preserved (unsat)'}")

inv = [SYS1(opening), SYS2(opening, idle, out)]
# E-CLOSE without NAT-4: the closed value may be foreign (checkedOut unchanged), channel.go:211
query("SYS-1 under E-CLOSE without NAT-4 (foreign or duplicate Close)", inv,
      [o2 == opening - 1, out2 == out], SYS1(o2))
# E-CLOSE with NAT-4: the value is a checked-out connection of this pool
query("SYS-1 and SYS-2 under E-CLOSE with NAT-4", inv + [out >= 1],
      [o2 == opening - 1, out2 == out - 1], z3.And(SYS1(o2), SYS2(o2, idle, out2)))
# UV-PUT-FOREIGN into a non-full idle channel, channel.go:190
query("SYS-2 under UV-PUT-FOREIGN (enqueue)", inv + [idle < max_idle, waiters == 0],
      [i2 == idle + 1, o2 == opening, out2 == out], SYS2(o2, i2, out2))
# E-GET create below the cap, channel.go:154-159
query("SYS-1 and SYS-2 under E-GET create", inv + [idle == 0, opening < maxc],
      [o2 == opening + 1, out2 == out + 1], z3.And(SYS1(o2), SYS2(o2, idle, out2)))
# Two steps: phantom decrement then create; liveConns counts connections the pool created and nobody closed
s = z3.Solver()
o1, o3 = z3.Ints("o_after_close o_after_get")
s.add(*dom, opening == maxc, maxc >= 1, live == opening, idle == 0, SYS2(opening, idle, out),
      o1 == opening - 1,            # foreign Close: counter drops, no pool connection closed (live unchanged)
      o1 < maxc, o3 == o1 + 1,      # Get below the cap creates one more
      live2 == live + 1, z3.Not(LIVE(live2)))
rows.append("live connections <= MaxCap after foreign Close then Get create: "
            + ("violation, witness " + str(s.model()) if s.check() == z3.sat else "preserved (unsat)"))
# SYS-3 under E-CLOSE with waiters queued at capacity, channel.go:211 (no wake-up)
query("SYS-3 under E-CLOSE with waiters (NAT-4 holds)", inv + [out >= 1, waiters >= 1, idle == 0, opening >= maxc, SYS3(waiters, idle, opening)],
      [o2 == opening - 1, out2 == out - 1, w2 == waiters], SYS3(w2, idle, o2))
# SYS-3 under E-PUT with waiters: handoff, channel.go:183
query("SYS-3 under E-PUT handoff (one waiter leaves)", inv + [waiters >= 1, idle == 0, opening >= maxc, out >= 1],
      [w2 == waiters - 1, o2 == opening], SYS3(w2, idle, o2))
text = "\n".join(rows)
(Path(__file__).resolve().parent / "invariant-results.txt").write_text(text + "\n", encoding="utf-8")
print(text)
