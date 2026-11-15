# channelPool — invariants and lint findings (Step 5)

## Assumptions (NAT)

| id | assumption | source |
|---|---|---|
| NAT-01 | Factory, Close and Ping callbacks are safe to call from several goroutines | not documented (channel.go:25-30) |
| NAT-02 | callers pass to Put/Close only connections obtained from this pool's Get, each at most once | not documented; the code cannot check it (Q-11..Q-14) |
| NAT-03 | callers do not use a connection after Put/Close | not documented |
| NAT-04 | callbacks return and do not panic | not documented |
| NAT-05 | configuration satisfies channel.go:59-67 | enforced by NewChannelPool (G-04) |
| NAT-06 | Go semantics: Mutex is not reentrant; send on a closed channel panics; receive on a closed channel yields the zero value; len/cap of a nil channel is 0 | Go language and standard library |
| NAT-07 | the clock does not go backwards | time.Now monotonic reading |
| NAT-08 | callers return every borrowed connection | not documented (Q-20) |
| NAT-SYS-01 | N pool instances share one server and observe its degradation together | multi-instance assumption, used in Q-22 |

## Invariants (SYS), checked state by state

| id | predicate | verdict |
|---|---|---|
| SYS-01 | 0 <= openingConns | holds under NAT-02; violated by UV-Close-dup and UV-Close-foreign (z3 invariant check in guard-results.txt; Q-12, Q-14) |
| SYS-02 | open connections (idle + borrowed) <= MaxCap | holds under NAT-02; violated by UV-Put-foreign and double Close (Q-12, Q-13; TestAsIs_Close_Twice_ExceedsMaxCap) |
| SYS-03 | idle count <= MaxIdle | holds in every state: the idle channel has capacity MaxIdle (channel.go:70) and Put sends non-blocking (channel.go:189-196) |
| SYS-04 | Closed implies factory, close and ping are nil; Open implies factory and close are non-nil | holds: Release sets them together under the lock (channel.go:225-231) |
| SYS-05 | a caller blocked in Get is eventually served or fails | violated in Closed (Q-01) and in Open_Waiting_BelowCap (Q-03): nothing wakes the waiter without a Put |
| SYS-06 | idle count >= InitialCap | violated after any Get (DOC-9, Q-23) |
| SYS-07 | waiters queued implies no idle connection | violated in Open_Waiting_IdleAvailable (pair P-04a, Q-04) |
| SYS-08 | after Release completes, no new Get returns a connection | holds for a Get that starts after Release (channel.go:105-107); a Get holding a snapshot taken earlier can still receive a buffered connection (channel.go:104, 110; Q-07) |

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 DOC-10 DOC-11 DOC-12 DOC-13 -->

| DOC | kind | target |
|---|---|---|
| DOC-1 | structural | connection type is interface{} in Factory, Get, Put (channel.go:26, pool.go:12-14), enforced by the Go compiler |
| DOC-2 | guard | G-01 |
| DOC-3 | cell | Open_IdleAvailable x Get |
| DOC-4 | cell | Open_NoIdle_AtCap x Get |
| DOC-5 | cell | Open_IdleAvailable x Get |
| DOC-6 | cell | Open_NoIdle_BelowCap x Put |
| DOC-7 | cell | Open_IdleAvailable x Release |
| DOC-8 | cell | Open_IdleAvailable x Len |
| DOC-9 | invariant | SYS-06 |
| DOC-10 | invariant | SYS-02 |
| DOC-11 | invariant | SYS-03 |
| DOC-12 | cell | Closed x Get |
| DOC-13 | rejected | efficiency adjective, a performance claim outside the statechart (PA-19), no behaviour to check |

Mapping findings (PA-22): DOC-9 is violated (SYS-06, Q-23). DOC-10 is violated under NAT-02 breaches (Q-12, Q-13). DOC-4 maps to a cell that waits; how long and how it ends is unspecified (Q-02). DOC-7 maps to a cell whose effect on waiters and borrowed connections is not stated (Q-01, Q-05). DOC-8 is ambiguous (Q-18). DOC-3's ping applies on the idle path only (Q-15).

## Step-5 lint checklist

| lint | result |
|---|---|
| waiting states without timeout behaviour | Open_Waiting_* have none (channel.go:137): Q-02 |
| retries without a maximum | Get's loop retries after each discarded connection (channel.go:108-163); each pass consumes an idle connection or creates one, so it ends when the idle channel is empty and capacity or the factory answers: no finding |
| invoked external operations without explicit failure outcome | Factory error returned (channel.go:155-158); Ping failure discards (channel.go:125-127); Close callback errors are dropped in Get and Release: Q-10 |
| externally initiated operations without cancellation handling | Get has no cancellation (channel.go:137): Q-02 |
| terminal or error states without documented meaning | Closed: Get returns ErrClosed (pool.go:7); Put/Close/Ping give silent success or a panic: Q-05, Q-06 |
| undefined startup or shutdown behaviour | startup fill failure: Q-19; shutdown does not release waiters or borrowed connections: Q-01, Q-05 |
| unbounded queues or buffers | connReqs grows without bound (channel.go:135): Q-02 |
| synchronized reset points | idle connections created together expire together and are replaced without jitter; startup fills InitialCap at once: Q-22 (multi-instance probes M-01..M-03) |
| lifecycle disagreement (PA-21) | borrower lifecycle versus pool lifecycle: Release is terminal for the pool but neither wakes waiters nor takes back borrowed connections: Q-01, Q-05 |
| dual ownership cleanup (PA-23) | explicit Put and Close are two release paths for one connection, no record of which happened: exactly-one release not provable: Q-11, Q-12 |
| async cancellation isolation (PA-24) | a waiter (receiver region) has no explicit synchronization with the pool's Release (sender region): Q-01 |
| user-model gap | Put after Release (silent), a Get that queues while an idle connection exists, a waiter that outlives capacity: dispositions reachable only under concurrency: Q-01, Q-03, Q-04 |

## Guard-proof scope note

G-01..G-05 guard groups mirror the code's if-chains, so disjointness and coverage are close to structural; the value of the proofs is the explicit NAT domains and boundary probes (guard-results.txt), and the z3 invariant checks that G-04 accepts MaxCap = 0 and that SYS-01 is violable without NAT-02. G-06..G-08 are not-formalizable (external-call, dynamic-state) and stay inspection-only, unproven.
