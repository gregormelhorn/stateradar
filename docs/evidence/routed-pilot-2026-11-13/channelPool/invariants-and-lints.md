# Invariants and lint findings — channelPool

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 DOC-14 DOC-15 DOC-16 -->

## NAT invariants (environment assumptions)

| id | assumption | citation | status |
|---|---|---|---|
| NAT-1 | The Factory callback returns within bounded time. | channel.go:25 ("生成连接的方法") — no timing contract | unproven; the factory runs under the pool mutex (channel.go:154), so a violation blocks every pool call (UV-12, Q-12) |
| NAT-2 | Calling the Close callback once per connection is safe; a second call is unknown. | channel.go:27 ("关闭连接的方法") — no idempotency contract | unproven (UV-07) |
| NAT-3 | No callback calls a pool method (no reentrancy). | no documentation in README.md or Config comments | unproven; a violation deadlocks (Q-12) |
| NAT-4 | Every connection obtained by Get is returned exactly once, by Put or by Close, and only connections obtained from this pool are returned. | not documented; README.md:52 says only "Put the connection back … when the connection is no longer in use" | assumption the counter relies on; violated by UV-02..UV-05, UV-07, UV-08 (Q-10, Q-11) |
| NAT-5 | Release is called after all users have stopped using the pool. | not documented; README.md:55 "when resources need to be destroyed" | assumption; its violation is the pairs P-01..P-05 |
| NAT-6 | MaxCap > 0. | not enforced: G-01 accepts MaxCap = 0 | violated by a valid configuration (Q-14) |
| NAT-SYS-1 | Several pool instances (processes) share one server; a server outage invalidates their idle connections near-simultaneously. | inferred (multi-instance assumption) | environment assumption for the multi-instance probes |

## SYS invariants (obligations), checked state by state

| id | predicate | Open_Idle | Open_Empty_BelowCap | Open_Empty_AtCap | Open_Waiting | Open_Waiting_CapacityFree | Released | Released_WaitersStranded |
|---|---|---|---|---|---|---|---|---|
| SYS-1 | openingConns = idle + checked-out | holds under NAT-4 | holds under NAT-4 | holds under NAT-4 | holds under NAT-4 | holds under NAT-4 | not maintained (no reset; inferred, channel.go:224-243) | not maintained |
| SYS-2 | live connections ≤ MaxCap (DOC-8) | holds under NAT-4 | holds (create only when o < m, G-02) | holds | holds | holds | n/a | n/a |
| SYS-3 | waiters > 0 ⇒ idle = 0 ∧ openingConns ≥ maxActive | holds (vacuous) | holds (vacuous) | holds (vacuous) | holds on entry; **not preserved by Close** (z3 witness, guard-results.txt) | **violated** (definition of the state) | holds (vacuous) | n/a (conns nil) |
| SYS-4 | conns = nil ⇒ no blocked waiter | n/a | n/a | n/a | n/a | n/a | holds | **violated** (Release leaves connReqs, z3) |
| SYS-5 | Get never returns a connection older than IdleTimeout (DOC-2, DOC-9) | holds (channel.go:116) | holds | holds | holds on the handoff path (channel.go:142) | holds | holds (Get rejected) | holds |
| SYS-6 | Get never returns a connection that fails the configured Ping (DOC-3) | holds (channel.go:124) | holds (new connection; no Ping on create — inferred) | holds | **violated**: handoff path has no Ping (channel.go:141-148) | violated on the handoff path | holds | holds |
| SYS-7 | Release closes every connection of the pool exactly once (DOC-6, DOC-15) | **violated** for checked-out connections (only the idle set is drained, channel.go:239-242) | violated | violated | violated | violated | violated (late Put/Close do not close, Q-04) | violated |
| SYS-8 | idle ≤ MaxIdle (DOC-13) | holds (channel capacity, channel.go:70) | holds | holds | holds | holds | holds | holds |
| SYS-9 | Close(conn) closes the connection (DOC-14) | holds (channel.go:212) | holds | holds | holds | holds | **violated** (channel.go:208-209) | **violated** |
| SYS-10 | Get on a released pool returns ErrClosed (DOC-10) | n/a | n/a | n/a | n/a | n/a | holds (channel.go:105), except the drain race (Q-17) | holds, except Gets already blocked (Q-01) |
| SYS-11 | the pool holds at least InitialCap connections (DOC-12) | **violated** (no refill; idle drops below InitialCap by Get or expiry) | violated | violated | violated | violated | n/a | n/a |

Violations → findings: SYS-3 (Q-02, Q-03), SYS-4 (Q-01), SYS-6 (Q-07), SYS-7 (Q-06, Q-04), SYS-9 (Q-04), SYS-10 race (Q-17), SYS-11 (Q-13).

## Doctrine mapping

| DOC | mapping | target |
|---|---|---|
| DOC-1 | rejected | describes the value type (interface{}) for versatility; prescribes no behaviour of the pool's state machine |
| DOC-2 | invariant | SYS-5 |
| DOC-3 | invariant | SYS-6 |
| DOC-4 | cell | Open_Empty_AtCap x get |
| DOC-5 | cell | Open_Waiting x put |
| DOC-6 | invariant | SYS-7 |
| DOC-7 | cell | Open_Idle x len |
| DOC-8 | invariant | SYS-2 |
| DOC-9 | invariant | SYS-5 |
| DOC-10 | cell | Released x get |
| DOC-11 | cell | Open_Waiting x UV-01 |
| DOC-12 | invariant | SYS-11 |
| DOC-13 | invariant | SYS-8 |
| DOC-14 | invariant | SYS-9 |
| DOC-15 | invariant | SYS-7 |
| DOC-16 | rejected | implementation-efficiency remark (README_ZH_CN.md:13); prescribes no behaviour |

PA-22 requirement → cell check:

* DOC-4 → Open_Empty_AtCap × get = transition → Open_Waiting: implemented. The parenthesis "like the go db connection pool" is not adopted as a requirement (requirement-scope rule: it names no behaviour); see Q-09.
* DOC-5 → Open_Waiting × put = handle (handoff): implemented.
* DOC-7 → Open_Idle × len = handle (idle count): implemented for one reading of "connections in the pool"; Q-08.
* DOC-10 → Released × get = reject ErrClosed: implemented.
* DOC-11 → Open_Waiting × UV-01 = defer (queued) with no timeout: the error "pool limit exceeded" is never produced (G-07) — **violated / unimplemented** → Q-09.
* DOC-6/DOC-15 via SYS-7: violated for checked-out connections → Q-06.
* DOC-12 via SYS-11: unimplemented → Q-13.

## Lint checklist (Step 5)

| lint | finding | provenance | → |
|---|---|---|---|
| waiting states without timeout | Open_Waiting and Open_Waiting_CapacityFree block at channel.go:137 ("ret, ok := <-req") with no timeout; `waitTimeOut` is declared (channel.go:46) and never used | observed-in-code | Q-09 |
| retries without maximum | the Get loop retries after each discarded connection (channel.go:119, :126, :145) with no bound; bounded only by the supply of idle connections and the factory | observed-in-code / inferred | Q-18 |
| external operations without explicit failure outcome | Close-callback errors are dropped when Get discards an expired or failed connection (channel.go:118, :125, :144 — return values unused); Release ignores closeFun errors (channel.go:241) | observed-in-code | Q-16 |
| operations without cancellation | Get has no cancellation (no context, no deadline); a waiter can only be released by a Put | observed-in-code channel.go:103 | Q-09 |
| terminal states without diagnostic | Released_WaitersStranded is silent: blocked Gets get neither a connection nor an error | observed-in-code | Q-01 |
| undefined startup / shutdown | shutdown with users still active (NAT-5) is undocumented: waiters strand (Q-01), checked-out connections are never closed (Q-06), late Put/Close leak (Q-04), late Ping panics (Q-05) | observed-in-code | Q-01, Q-04, Q-05, Q-06 |
| unbounded queues | `connReqs` grows without bound (channel.go:135); no limit on waiters | observed-in-code | Q-09 |
| synchronized reset points | none in the component: no backoff or penalty state exists. Related aggregate concern: all idle connections created together (initial fill, channel.go:82-89) expire together under one IdleTimeout, and a server outage invalidates all of them at once — every Get then reconnects with no backoff | inferred | Q-18 |
| lifecycle disagreement (PA-21) | `connReqs` is accessed from two lifecycles: the waiter's (Get enqueues, channel.go:135) and the pool's (Release). Release — the pool's terminal transition — performs no cleanup in the waiter track. Close and idle expiry — terminal for one connection — free capacity (channel.go:211) without a transition in the waiter track | observed-in-code | Q-01, Q-02 |
| dual ownership cleanup (PA-23) | a connection has two explicit release paths, Put and Close, plus Release's drain for idle ones. Nothing enforces exactly one logical release per connection: Put+Close (UV-04), double Close (UV-07), and Put after Release (no close at all) are all accepted | observed-in-code | Q-11, Q-04 |
| async cancellation isolation (PA-24) | the waiter channel `req` is shared between the pool (sender side, Put) and the waiting Get (receiver). When the pool's lifecycle ends (Release), no synchronization reaches the receiver: no close(req), no send | observed-in-code channel.go:224-243 | Q-01 |
| user-model gap | (1) Released × put/close_conn return nil silently — a single-threaded reader expects either an error or a closed connection; (2) Open_Waiting_CapacityFree × get: a new Get succeeds while an older Get keeps waiting — visible only with concurrent callers; (3) P-01a: a Get blocked before Release never returns | observed-in-code | Q-04, Q-03, Q-01 |

## Lock-discipline findings

* Factory and Close callbacks run with `mu` held (channel.go:154, :212); reentrancy is undocumented (channel.go:25-30, README.md) → deadlock if a callback calls the pool (NAT-3) → Q-12.
* `sync.RWMutex` is only used as a mutex (`Lock` everywhere, no `RLock`): Len and getConns serialize with the factory call → a slow factory blocks Len (UV-12) → Q-12.
