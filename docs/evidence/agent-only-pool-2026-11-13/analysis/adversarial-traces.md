# channelPool — Adversarial traces (Step 6)

Format per trace: (a) sequence, (b) what the code does, with provenance, (c) the domain question, or `none — control trace`. Config defaults unless stated: MaxIdle M = 2, MaxCap X = 2, IdleTimeout T = 0 (off), no Ping. "As-is test Tn" refers to `as-is-tests.md` (executed in the scratch copy).

## Systematic traces (one per pair ordering)

### P-01a — Get registers as waiting, then Put
(a) o = X = 2, i = 0 (Open_Empty_AtCap). G1: Get → no idle conn → lock → o ≥ X → waiter appended → unlock → blocks. A: Put(c1).
(b) Put sees a waiter, hands c1 over with a fresh timestamp (channel.go:179-185); G1 receives it and returns c1 (channel.go:137, channel.go:148). State Open_Empty_AtCap. observed-in-code.
(c) none — control trace.

### P-01b — Put lands between Get's empty select and Get's lock
(a) Open_Empty_AtCap. G1: Get → `select` finds no idle conn → `default` (channel.go:130). Before G1 reaches `c.mu.Lock()` (channel.go:131), A: Put(c1) → lock → no waiter → enqueue c1 (channel.go:190) → unlock. G1: lock → o ≥ X → appends itself as waiter → blocks on its channel.
(b) G1 waits while c1 sits idle: state Open_Waiting_IdleStranded. G1 is served only by a later Put; a new Get takes c1 ahead of G1 (channel.go:110). observed-in-code; executed as as-is test T10 (real Put and Get, ordered by holding the mutex).
(c) Q-04: may a Get wait while an idle conn exists, and may later Gets be served before it?

### P-02a — Get completes, then Release
(a) Open_Idle. G1: Get → returns c1. B: Release.
(b) Release closes the idle conns (channel.go:238-242) and clears the pool; c1 stays checked out and open. A later Put(c1) closes nothing (P-03b). observed-in-code.
(c) Q-06 (fate of checked-out conns at Release).

### P-02b — Release starts while a Get is in progress
(a) Variant 1, Open_Idle with i = 2: G1: Get → captured the idle store (channel.go:104). B: Release → clears fields, unlocks, closes the channel, starts draining. G1: `select` receives an idle conn the drain has not reached yet.
(b) Variant 1: G1 returns a conn from a released pool; if it was expired, G1's `c.Close` finds the Close callback cleared and does not close it (channel.go:208-209), then, once the drain has emptied the closed channel, the next receive yields nil → ErrClosed (channel.go:111-112) — the expired conn is neither returned nor closed. Variant 2, Open_Empty_AtCap: G1 passed the empty `select`, B: Release clears the fields under the lock, G1 then takes the lock: `o ≥ X` is tested before `factory == nil` (channel.go:133 before channel.go:150), so G1 appends itself as waiter and blocks forever on a released pool. Variant 3, below cap: G1 sees `factory == nil` → ErrClosed (channel.go:150-152). Also: G1 reads `c.ping` without the lock (channel.go:123) while B writes it (channel.go:229) — see P-08. observed-in-code; guard probe G-02 (released ∧ o ≥ X → wait).
(c) Q-05 (a Get that races Release can block forever), Q-06 (conns obtained from, or discarded by, a pool being released).

### P-03a — Put, then Release
(a) Open_Idle with c1 checked out. A: Put(c1) → enqueued. B: Release.
(b) Release drains and closes c1 with the captured Close callback (channel.go:241). observed-in-code.
(c) none — control trace. Verdict rests on DOC-6 ("Release all connections in the connection pool", README.md:55); cited text contemplates this ordering: yes (an idle conn present at Release is one of "all connections in the connection pool").

### P-03b — Release, then Put
(a) Open_Idle with c1 checked out. B: Release. A: Put(c1).
(b) Put sees `conns == nil` and calls Close (channel.go:174-176); Close finds the Close callback cleared and returns nil without closing (channel.go:208-209). c1 stays open; Put reports success. observed-in-code; as-is test T3.
(c) Q-06: should a conn returned after Release be closed (README: "Release all connections")?

### P-04a — Close, then Get at the former cap
(a) Open_Empty_AtCap (o = X = 2). A: Close(c1) → o = 1. G1: Get.
(b) G1 finds no idle conn, o < X → creates (channel.go:154-161). Open_Empty_AtCap again. observed-in-code.
(c) none — control trace.

### P-04b — Get waits, then Close frees capacity
(a) Open_Empty_AtCap. G1: Get → waits (Open_Waiting). A: Close(c1) → o = 1.
(b) Close decrements o and calls the Close callback (channel.go:211-212); it does not look at the waiter list. G1 stays blocked (Open_Waiting_BelowCap) until some Put; a new Get G2 creates a conn ahead of G1 (channel.go:154). If every holder closes instead of putting, G1 never returns. observed-in-code; as-is test T2.
(c) Q-03: should freed capacity serve the oldest waiting Get (create a conn for it, or signal it)?

### P-05a — Put(c), then Close(c) by another goroutine
(a) Open_Empty_BelowCap. A: Put(c1) → idle (Open_Idle). B: Close(c1).
(b) Close decrements o and closes c1 while c1 stays in the idle store (channel.go:211-212). The next Get returns the closed c1 unless Ping or expiry catches it; if caught, the discard decrements o a second time (channel.go:118). observed-in-code.
(c) Q-09.

### P-05b — Close(c), then Put(c)
(a) Open_Empty_BelowCap. B: Close(c1) → o−1, c1 closed. A: Put(c1).
(b) Put stores the closed c1 (channel.go:190) or hands it to a waiter (channel.go:183), which returns it without Ping. observed-in-code.
(c) Q-09.

### P-06a — Factory returns, then Release
(a) Open_Empty_BelowCap. G1: Get → Open_Creating → Factory returns c1 → o+1, unlock → G1 has c1. B: Release.
(b) Same as P-02a: c1 is checked out at Release and is not closed by it. observed-in-code.
(c) Q-06.

### P-06b — Release called while Factory runs
(a) Open_Creating (G1 holds the mutex inside Factory). B: Release → blocks on `c.mu.Lock()` (channel.go:225).
(b) When Factory returns, G1 increments o and returns the new conn (channel.go:159-161); then Release proceeds. The caller of G1 holds a fresh conn of a released pool; giving it back closes nothing (P-03b). observed-in-code.
(c) Q-06.

### P-07a — Idle time passes, then a Get dequeues the conn
(a) T = 100 ms, Open_Idle with c1 idle since t0. At t0+150 ms G1: Get.
(b) c1's age > T → `c.Close(c1)` (o−1, Close callback) → loop → next idle or create (channel.go:115-120). Between t0+100 ms and t0+150 ms c1 was expired but open and counted. observed-in-code; as-is test T13.
(c) Q-12 for the interval before the Get. The discard itself: none — control trace. Verdict rests on DOC-2 ("the timeout connection will be closed and discarded", README.md:13); cited text contemplates this ordering: yes (expiry first, then the conn is not handed out but closed).

### P-07b — Get dequeues the conn just before the idle time passes
(a) T = 100 ms, c1 idle since t0. G1: Get at t0+100 ms exactly (age = T), or at t0+99 ms.
(b) `Before` is strict: age = T is not expired → c1 returned (G-03 boundary probe, guard-results.txt). The conn may pass T while checked out; the idle timeout does not apply to checked-out conns. observed-in-code.
(c) none — control trace. Verdict rests on DOC-11 (IdleTimeout = maximum *idle* time, channel.go:31); cited text contemplates this ordering: no — it defines a maximum idle time but not whether a conn whose age equals the limit is still valid, nor what happens when the limit passes while it is checked out. The control verdict is void → Q-12 (boundary and checked-out conns added to it).

### P-08a — Release clears the Ping reference before the Get reads it
(a) Ping configured. B: Release → `c.ping = nil` (channel.go:229). G1 (captured the idle store earlier) dequeues c1 during the drain, reads `c.ping == nil` → skips Ping → returns c1.
(b) A conn of a released pool is returned unvalidated. The read at channel.go:123 is not synchronized with the write at channel.go:229 (no lock on the read side): a data race in the Go memory model. observed-in-code.
(c) Q-10.

### P-08b — Get reads the Ping reference, Release clears it, Get calls Ping
(a) Ping configured. G1: dequeues c1, reads `c.ping != nil` (channel.go:123). B: Release sets `c.ping = nil`. G1: `c.Ping(c1)` → `c.ping(conn)` (channel.go:220).
(b) G1 calls a nil function value → runtime panic, if the second read observes the write. Both reads are unsynchronized with the write: the race detector reports this pair (as-is run R0b on the repository's own TestPoolConcurrent: "WARNING: DATA RACE … channel.go:229 … channel.go:123"; as-is test T11). The panic itself depends on scheduling; it was not forced in this run. observed-in-code (unsynchronized access), unverifiable-runtime for the panic (PA-19).
(c) Q-10.

### P-09a — Release by caller 1, then Release by caller 2
(a) Open_Idle. R1: Release → clears under the lock. R2: Release → finds `conns == nil` → returns (channel.go:234-235).
(b) Idle conns closed once. observed-in-code.
(c) none — control trace.

### P-09b — Release by caller 2, then Release by caller 1
(a)/(b) Symmetric to P-09a: the lock makes exactly one caller capture the idle store; the other returns early. observed-in-code.
(c) none — control trace.

## Free probes

### T-01 — Get at MaxCap with nobody returning
(a) Open_Empty_AtCap; G1: Get; no Put ever.
(b) G1 blocks forever (channel.go:137); `ErrMaxActiveConnReached` is never returned because no waiter channel is ever closed (G-07). The repository's TestPool_Get expects the error and hangs (run R0). observed-in-code, observed-in-tests (channel_rpc_test.go:93-95).
(c) Q-01, Q-02.

### T-02 — Release with waiting Gets
(a) Open_Waiting with G1, G2 blocked. Release.
(b) Release clears the pool and closes idle conns; `connReqs` is left as is and no waiter channel is closed (channel.go:224-243). G1 and G2 block forever; a later Put closes nothing and serves no one (`conns == nil` is tested before the waiter list, channel.go:174 before channel.go:179). observed-in-code; as-is test T1.
(c) Q-05.

### T-03 — Double Close drives the pool past MaxCap
(a) X = 2. Get c1, Get c2 (o = 2). Close(c1), Close(c1) (o = 0). Get, Get (o = 2, live conns = 3: c2 and two new).
(b) Each Close decrements unconditionally (channel.go:211); the pool creates past MaxCap. observed-in-code; as-is test T5.
(c) Q-09.

### T-04 — Duplicate Put hands one conn to two callers
(a) Get c1; Put(c1); Put(c1); Get → c1; Get → c1.
(b) No identity check at Put (channel.go:190); both Gets receive c1. observed-in-code; as-is test T7.
(c) Q-09.

### T-05 — Factory returns a conn and an error
(a) Open_Empty_BelowCap; Factory returns (c1, err).
(b) Get returns (nil, err); c1 is never closed (channel.go:155-157). observed-in-code; as-is test T8.
(c) Q-07.

### T-06 — Factory returns (nil, nil)
(a) Open_Empty_BelowCap, X = 1; Factory returns (nil, nil).
(b) o+1, Get returns (nil, nil) (channel.go:159-161). Put(nil) and Close(nil) are rejected (channel.go:168-169, channel.go:203-204), so o can never come down: every later Get waits forever. observed-in-code; as-is test T9.
(c) Q-07.

### T-07 — Slow Factory stalls Put
(a) Factory sleeps 300 ms. G1: Get → Open_Creating. A: Put(c0) during the sleep.
(b) Put blocks on the mutex until Factory returns (channel.go:172 vs channel.go:154). observed-in-code; as-is test T15.
(c) Q-19 (and Q-08 for an unbounded Factory).

### T-08 — Close callback re-enters the pool
(a) Close callback calls `p.Len()`. Caller: Close(c1).
(b) Close holds the mutex while calling the callback (channel.go:206-212); Len locks the same mutex (channel.go:96) → deadlock. Same for Factory calling Len during Get (channel.go:131, channel.go:154). observed-in-code; as-is test T14.
(c) Q-08.

### T-09 — Ping method without a configured Ping, and after Release
(a) Pool without Ping: `p.(*channelPool).Ping(c1)`; pool after Release: same.
(b) `c.ping(conn)` with `c.ping == nil` → panic (channel.go:220). observed-in-code; as-is test T12.
(c) Q-11.

### T-10 — Expired idle conns stay open without traffic
(a) T = 50 ms, InitialCap = 2. No Get for 200 ms.
(b) Nothing closes the two expired conns (no timer); the next Get closes both, then creates (channel.go:115-120). observed-in-code; as-is test T13.
(c) Q-12.

### T-11 — Broken conn handed straight to a waiter
(a) Ping configured. Open_Waiting (G1 waits). A: Put(dead conn).
(b) Put hands it over (channel.go:183); G1 checks only the age (channel.go:141-147) and returns the dead conn without Ping. observed-in-code.
(c) Q-13.

### T-12 — Pool drops below InitialCap and stays there
(a) InitialCap = 5; Get all five; Close all five.
(b) o = 0, Len = 0; nothing replenishes (no code path creates without a Get). observed-in-code; as-is test T16.
(c) Q-14.

### T-13 — Close-callback error on the discard path
(a) T = 10 ms; the Close callback returns an error; an idle conn expires; Get.
(b) Get discards: `c.Close(conn)` returns the error, which is ignored (channel.go:118); o is already decremented (channel.go:211 precedes channel.go:212). observed-in-code.
(c) Q-17.

### T-14 — MaxCap = 0 accepted
(a) Config InitialCap = MaxIdle = MaxCap = 0. NewChannelPool succeeds (G-01 accepts). Get.
(b) o = 0 ≥ X = 0 → wait forever (channel.go:133-137). observed-in-code; as-is test T17.
(c) Q-01.

## Multi-instance probes

### M-01 — Shared-fate reset: server restart with N pools
(a) N pools (one per process) against one server, each with i idle conns, Ping configured. The server restarts; all idle conns die at once. Over 3 restart cycles, each pool's next Gets ping-fail and discard every idle conn (channel.go:123-126), then call Factory.
(b) Each pool re-dials at most X conns, but immediately and without backoff: Factory errors go straight back to the caller (channel.go:155-157), so a caller retry loop re-dials at its own rate. Per cycle the server sees up to N·X dials concentrated in the first Gets after restart. Without Ping, dead conns are handed out until callers Close them. inferred from the code paths cited.
(c) Q-18.

### M-02 — Backoff dispersion
(a) N pools, same IdleTimeout T, started by one deploy: each pre-fills InitialCap conns at the same instant (channel.go:82-89, timestamps from construction time).
(b) The pool has no backoff and no jitter. Idle conns that were never used expire together at t0+T and are replaced together on the next Gets; conns that were used get fresh timestamps at Put (channel.go:190), which disperses them by traffic only. No mechanism makes expiry diverge. inferred.
(c) Q-18.

### M-03 — Degraded-recovery herd
(a) The server comes back at partial capacity. Pool A's Gets dial and succeed for some conns; the server fails again; pool B's Gets dial, fail, return errors.
(b) Each failed Factory call holds pool B's mutex for the dial duration (channel.go:131-157) and returns the error; no circuit breaking, no backoff, no limit on dial attempts per unit time. A slow-failing dial serializes all of B's Get/Put/Close (Q-19). Amplification depends on caller retry policy, which is outside the pool. inferred.
(c) Q-18, Q-19.
