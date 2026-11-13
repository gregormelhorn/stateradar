# Adversarial traces — channelPool

Configuration unless stated: InitialCap 2, MaxIdle 4, MaxCap 5, IdleTimeout 15 s
(the example configuration, example/main.go:37-45 — used only as numbers).

Model routing (Step 6): every control trace whose verdict cites a requirement or doc
line was checked with `jev-batch` against the original source, one `ordering` check
per cited fragment (`step6-readme.out.json`, `step6-pool.out.json`, model jev-1.14.0).
Jev backed none of them (all `unclear`, scope 0.02-0.05). Under routing rules 4 and 5
the cited verdicts are not source-backed: each voided verdict raises a question.

## Systematic traces (interaction pairs)

**T-P01a — Get waiting, then Release (pair P-01a)**

1. Open_Empty_AtCap (5 checked out, 0 idle). User U1 calls Get → transition → Open_Waiting: U1 appends `req` to connReqs and blocks (channel.go:135 ("c.connReqs = append(c.connReqs, req)"), channel.go:137 ("ret, ok := <-req")).
2. Owner calls Release → transition → Released_WaitersStranded: conns, factory, ping, close set to nil; the idle set (empty) closed; connReqs untouched (channel.go:225-243).
3. Users return their 5 connections with Put → each takes the conns-nil branch (channel.go:174 ("if c.conns == nil {")) before the waiter check: no handoff; Close returns nil without closing (channel.go:208-209).
4. U1 stays blocked forever. Neither a connection nor an error ever arrives.

(b) Code: Release has no statement for connReqs; the `!ok` branch that would return ErrMaxActiveConnReached (channel.go:138-139) has no producer. observed-in-code.
(c) Q-01: what must a waiting Get experience when the pool is released? (and Q-04 for the returned connections).

Variant T-P01a-2 — Get inside the factory call: U1's Get holds `mu` while the factory dials (channel.go:131, :154). Release blocks at channel.go:225 until the factory returns; U1 then gets a new connection and `openingConns++` (channel.go:159); Release runs after it. U1 holds a connection of a released pool that the pool will never close (Q-04, Q-06).

Variant T-P01a-3 — Get racing the drain: U1's Get took the conns snapshot before Release (channel.go:104). Release closes the channel and drains it outside the lock (channel.go:238-242) while U1's select receives from the same channel (channel.go:110). U1 may receive a buffered connection before the drain does: the ping callback is now nil, so no Ping (channel.go:123); U1 returns a connection of a released pool. Which goroutine receives is decided by the Go scheduler. (c) Q-17.

**T-P01b — Release, then Get (pair P-01b)**

1. Open_Idle. Owner calls Release → Released.
2. U1 calls Get → reject: `ErrClosed` (channel.go:105-106 ("return nil, ErrClosed")); observed-in-tests channel_rpc_test.go:156-157 ("_, err := p.Get()").

(b) reject ErrClosed. Verdict cites DOC-10 (pool.go:6-7, ErrClosed "pool is closed").
**cited text contemplates this ordering: no** — the comment names the error for a closed pool; it does not mention Release or Get. jev: unclear, scope 0.03 (O6).
The control verdict is void → Q-22.

**T-P02a — Put, then Release (pair P-02a)**

1. Open_Idle with 2 idle. U1 returns a connection: Put → enqueued (channel.go:190). 3 idle.
2. Owner calls Release → Released; the drain closes all 3 idle connections with the saved callback (channel.go:239-241 ("closeFun(wrapConn.conn)")).

(b) transition → Released; idle connections closed. Verdict cites DOC-6 (README.md:55 "Release all connections in the connection pool, when resources need to be destroyed").
**cited text contemplates this ordering: yes** — the usage example calls Put (README.md:53) and then Release (README.md:56) in this order. jev: unclear, scope 0.03 (O1).
Jev does not back the ordering under routing rule 4 → the control verdict is void → Q-20, citing both.

**T-P02b — Release, then Put of a checked-out connection (pair P-02b)**

1. Open_Empty_BelowCap; U1 holds connection c (checked out).
2. Owner calls Release → Released (c is not touched: the pool keeps no identity of checked-out connections).
3. U1 calls Put(c) → conns nil → Close(c) → close callback nil → returns nil (channel.go:174-176, :208-209).

(b) ignore (accidental): c is never closed; Put reports success. Jev O5 (README.md:55, "Release, then Put of an earlier connection; the connection is closed"): unclear, scope 0.02 — no source covers the ordering.
(c) Q-04.

**T-P03a — Close, then Release (pair P-03a)**

1. Open_Empty_BelowCap; U1 holds c. U1 calls Close(c) → `openingConns--`, close callback (channel.go:211-212).
2. Owner calls Release → Released; drains the idle set.

(b) both handled; c closed once by Close. No requirement is cited (code only).
none — control trace

**T-P03b — Release, then Close (pair P-03b)**

1. U1 holds c; owner calls Release → Released.
2. U1 calls Close(c) → close callback nil → returns nil without closing c (channel.go:208-209 ("return nil")).

(b) ignore (accidental). DOC-14 ("Close closes a single connection", channel.go:201) is contradicted.
(c) Q-04.

**T-P04a — Ping, then Release (pair P-04a)**

1. Open_Idle. U1 calls Ping(c): Ping reads `c.ping` without the mutex (channel.go:220 ("return c.ping(conn)")).
2. Concurrently the owner's Release writes `c.ping = nil` under the mutex (channel.go:229).

(b) The read in Ping and the write in Release are not ordered by any lock: a data race under the Go memory model (inferred from the absent lock). If Ping reads the old value it calls the callback, possibly on a connection the drain is closing; if it reads nil it panics.
(c) Q-05.

**T-P04b — Release, then Ping (pair P-04b)**

1. Owner calls Release → Released (`c.ping = nil`, channel.go:229).
2. U1 calls Ping(c) → calls a nil function value (channel.go:220): runtime panic.

(b) UNSPECIFIED (panic). (c) Q-05.

**T-P05a — Len, then Release (pair P-05a)**

1. Open_Idle with 3 idle. U1 calls Len → 3 (channel.go:247).
2. Owner calls Release → Released.

(b) Len returned a snapshot that is stale once Release runs; no state changed. Code only, no requirement cited.
none — control trace

**T-P05b — Release, then Len (pair P-05b)**

1. Owner calls Release → Released.
2. U1 calls Len → `len(nil channel)` = 0 (channel.go:247); observed-in-tests channel_rpc_test.go:161 ("if p.Len() != 0 {").

(b) handle, returns 0. Rests on code and a test, no requirement.
none — control trace

## Free probes

**T-F01 — Close frees capacity while a Get waits (lost wake-up)**

1. Open_Empty_AtCap (5 checked out). U1 Get → Open_Waiting (blocked).
2. U2 finds its connection broken and calls Close(c2) → `openingConns` 4 (channel.go:211) → Open_Waiting_CapacityFree. No signal to connReqs.
3. U1 stays blocked although the pool could create a connection. A later Get by U3 creates one immediately (channel.go:154-161) and overtakes U1.

(b) observed-in-code. (c) Q-02 (and Q-03 for the overtaking).

**T-F02 — Handoff delivers a dead connection**

1. Open_Waiting; the server restarts; all checked-out connections are now dead.
2. U2 returns its dead connection with Put → handed to U1 (channel.go:183) with a fresh timestamp (channel.go:184).
3. U1 returns it without Ping (channel.go:141-148), although a Ping callback is configured.

(b) observed-in-code. (c) Q-07 (DOC-3 "invalid connection will be discarded" — applied by the code only on the idle path).

**T-F03 — Enqueue race: waiting although a connection is idle**

1. Open_Empty_AtCap. U1 Get: `select` finds conns empty and takes `default` (channel.go:130) — no lock held yet.
2. U2 Put(c2): no waiters → c2 enqueued into conns (channel.go:190) → Open_Idle.
3. U1 locks (channel.go:131), sees openingConns ≥ maxActive, enqueues itself and blocks → Open_Waiting_CapacityFree (idle 1, waiters 1).
4. U3 Get takes c2 at once. U1 waits for the next Put.

(b) observed-in-code; the window lies between channel.go:130 and :131. (c) Q-03.

**T-F04 — Duplicate Put**

1. U1 holds c; calls Put(c) twice (error-handling path runs twice) → c is twice in the idle set (channel.go:190).
2. U2 and U3 both Get c and use one connection concurrently.

(b) observed-in-code (no identity check). (c) Q-11.

**T-F05 — Double Close drives openingConns below the live count**

1. Open_Empty_AtCap (5 live). U1 calls Close(c1) twice → `openingConns` 3 although 4 connections live (channel.go:211).
2. Two Gets create two new connections → 6 live connections > MaxCap 5.

(b) observed-in-code. DOC-8 (max concurrent connections) violated under a NAT-4 breach. (c) Q-11.

**T-F06 — Leaked connections exhaust the pool**

1. Users take connections and, on an error path, drop them without Put or Close (UV-02), 5 times.
2. `openingConns` stays 5; Open_Empty_AtCap forever; every later Get waits forever (no timeout).

(b) observed-in-code. (c) Q-10 (and Q-09).

**T-F07 — Slow factory blocks the whole pool**

1. Open_Empty_BelowCap; the server is unreachable; the factory's dial takes 30 s.
2. U1 Get holds `mu` for 30 s (channel.go:131, :154). U2 Put, U3 Close, U4 Len, and the owner's Release all block on `mu` for that time.

(b) observed-in-code. (c) Q-12.

**T-F08 — Callback reentrancy deadlock**

1. The Close callback logs pool statistics by calling `p.Len()`.
2. U1 Close(c) holds `mu` (channel.go:206) and calls the callback (channel.go:212) → Len → getConns → `mu.Lock()` (channel.go:96) → deadlock (Go mutexes are not reentrant).
3. The same callback called from Release's drain (channel.go:241, no lock) does not deadlock.

(b) observed-in-code + inferred (Go mutex semantics). (c) Q-12.

**T-F09 — MaxCap = 0 is a valid configuration**

1. Config InitialCap 0, MaxIdle 0, MaxCap 0 passes validation (G-01 fact in guard-results.txt).
2. [*] → Open_Empty_AtCap. Every Get enqueues and blocks forever; no Put can occur, since no connection was ever handed out.

(b) observed-in-code + z3. (c) Q-14.

**T-F10 — Fill failure during construction**

1. NewChannelPool with InitialCap 5; the factory fails on the third call.
2. Release closes the 2 created connections (channel.go:85, :238-242); the constructor returns nil and an error (channel.go:86). `openingConns` is 5 in the discarded object.

(b) observed-in-code. The discarded pool is unreachable by the caller; the stale counter has no effect. No requirement cited.
none — control trace

**T-F11 — Concurrent Release (UV-10)**

1. Owner goroutines O1 and O2 call Release together. O1 takes the lock, snapshots conns, sets it to nil (channel.go:226-227). O2 then snapshots nil and returns (channel.go:234-235).

(b) Only one drain and one `close(conns)`; no double-close panic. Code only.
none — control trace

**T-F12 — The (MaxCap+1)-th Get in the test suite**

1. TestPool_Get drives the pool to openingConns = MaxCap with 0 idle (channel_rpc_test.go:59-91).
2. Get at channel_rpc_test.go:93 → Open_Empty_AtCap × get = transition → Open_Waiting: blocks at channel.go:137.
3. The test expects ErrMaxActiveConnReached (channel_rpc_test.go:94).

(b) The model predicts a hang until the test timeout; not executed in this run. (c) Q-09, Q-19.

**T-F13 — Idle timeout boundary**

1. A connection idles exactly IdleTimeout, then Get takes it: `t.Add(timeout).Before(now)` is false at equality → kept and returned (G-03 boundary probe: age = timeout → keep).
2. At age > IdleTimeout it is closed and the Get loops (channel.go:116-119).

(b) Verdict cites DOC-2 (README.md:13 "the timeout connection will be closed and discarded").
**cited text contemplates this ordering: yes** — the sentence describes a connection exceeding the idle time and being closed and discarded. jev: unclear, scope 0.05 (O3).
Jev does not back the ordering → the control verdict is void → Q-21 (also: the text does not say that expiry is lazy, on retrieval only).

**T-F14 — Steady-state waiting and handoff**

1. Open_Empty_AtCap; U1 Get → Open_Waiting.
2. U2 Put(c2) → handoff to U1 (channel.go:179-187); U1 returns c2 (channel.go:148) → Open_Empty_AtCap.

(b) Verdict cites DOC-4 (README.md:15 "When the connection pool is full, support for connection waiting").
**cited text contemplates this ordering: no** — the sentence names waiting when full; it does not say what ends the wait (Put handoff, FIFO order, timeout). jev: unclear, scope 0.04 (O2).
The control verdict is void → Q-23.

## Multi-instance probes

The pool connects to a shared external resource (the server behind the factory).
Assumption NAT-SYS-1.

**T-M1 — Shared-fate invalidation (server restart), 3 cycles**

N = 20 processes, each pool with 4 idle connections.

1. Cycle 1: the server restarts; all 80 idle connections are dead. With a Ping callback, each Get pings, fails, closes, loops (channel.go:123-126) until its pool's idle set is empty, then calls the factory under its pool mutex (one dial at a time per pool). Aggregate: up to 20 concurrent dials, one per pool; every caller whose dial fails gets the factory error at once and retries at its own rate — the pool adds no delay or backoff.
2. Without a Ping callback, dead connections are returned to callers until IdleTimeout discards them.
3. Cycles 2-3: identical; nothing in the pool remembers previous failures.

(b) observed-in-code: no failure memory, no backoff. (c) Q-18.

**T-M2 — Backoff dispersion / synchronized expiry**

No backoff exists. All pools started together (deploy) fill InitialCap connections at the same instant (channel.go:82-89) with one IdleTimeout; the first Gets after t0 + IdleTimeout discard and recreate them in every instance in the same window. Expiry is lazy, so the alignment follows the request load, not a timer.

(b) inferred from channel.go:88 ("c.conns <- &idleConn{conn: conn, t: time.Now()}") and :116. (c) Q-18.

**T-M3 — Degraded-recovery herd**

1. The server recovers partially (accepts some connections, refuses others).
2. Pool A: factory succeeds for U1 (openingConns++), fails for U2 (error returned, counter unchanged). Pool B does the same. A failed dial leaves no pool state, so every Get in every pool dials again on the next call.
3. The server fails again under the load; idle connections created in step 2 die; T-M1 repeats.

(b) observed-in-code (channel.go:155-157: failure returns without state change). (c) Q-18.
