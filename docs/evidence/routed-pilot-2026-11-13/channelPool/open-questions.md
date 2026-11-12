# Open domain questions — channelPool

Only the human owner can answer these. Recommendations are `proposed` and held loosely.
Every hole cell of the matrix carries a `→ Q-nn` that resolves here.

Q-01 — Release while Gets are waiting
**Status:** OPEN
Fault: F-07 (lifecycle coupling), F-20 (blocked progress after terminal event)
Trigger: step-4 matrix walk (also adversarial trace T-P01a, step-5 lint PA-21/PA-24)
Cells: Open_Waiting × release, Open_Waiting_CapacityFree × release, Open_Waiting × UV-10, Open_Waiting_CapacityFree × UV-10, Released_WaitersStranded × handoff, Released_WaitersStranded × UV-01
Question: What must a Get that is blocked waiting for a connection experience when the pool is released?
Current behaviour: it blocks forever. Release clears conns, factory, ping and close but never touches connReqs (observed-in-code channel.go:224-243); later Puts take the conns-nil branch before the waiter check (channel.go:174, :179); the `!ok` branch that would return ErrMaxActiveConnReached (channel.go:138-139) has no producer.
Options: (a) Release closes every waiter channel and waiters return ErrClosed | (b) waiters return ErrMaxActiveConnReached via the existing `!ok` branch | (c) Release blocks until all waiters are served | (d) document that Release must not be called while any Get is in flight
Proposed: (a) — ErrClosed is the pool's documented closed error (pool.go:6-7); a silent permanent block has no diagnostic.
Status line: OPEN — human decision required

Q-02 — Freed capacity does not wake waiters (lost wake-up)
**Status:** OPEN
Fault: F-01 (missing transition), F-20
Trigger: step-5 lint (PA-21; SYS-3 z3 violation)
Cells: Open_Waiting × close_conn, Open_Waiting_CapacityFree × close_conn, Open_Waiting_CapacityFree × UV-01; also idle_expired / ping_failed discards in Open_Waiting_CapacityFree
Question: When Close (or an expiry/Ping discard inside Get) frees capacity while Gets wait, must a waiter be woken (to create a connection), or does it wait for the next Put?
Current behaviour: `openingConns--` only (channel.go:211); no signal to connReqs. The waiter stays blocked; a newer Get creates a connection immediately (T-F01).
Options: wake the oldest waiter to create a connection | hand the freed slot to the oldest waiter | keep waiting for Put (document it)
Proposed: wake the oldest waiter — the waiting doctrine (DOC-4) waits for capacity, not specifically for a Put.
Status line: OPEN — human decision required

Q-03 — Waiter fairness and the enqueue race
**Status:** OPEN
Fault: F-04 (sneak path)
Trigger: adversarial trace (T-F03, T-F01)
Cells: Open_Waiting_CapacityFree × get
Question: May a new Get obtain a connection (idle or newly created) while older Gets are still queued? May a Get enqueue as a waiter while an idle connection is available?
Current behaviour: yes to both. The `select … default` (channel.go:130) runs without the mutex; a Put between it and channel.go:131 leaves an idle connection while the Get waits. New Gets take idle connections or create one ahead of the queue (channel.go:110, :154).
Options: strict FIFO (new Gets queue behind waiters) | re-check the idle set under the lock before enqueueing | accept and document
Proposed: re-check under the lock and queue behind existing waiters.
Status line: OPEN — human decision required

Q-04 — Put and Close after Release
**Status:** OPEN
Fault: F-15 (out-of-order / stale), F-09 (cancellation leak)
Trigger: step-4 matrix walk (pairs P-02b, P-03b)
Cells: Released × put, Released × close_conn, Released_WaitersStranded × put, Released_WaitersStranded × close_conn, Released/Released_WaitersStranded × UV-03, UV-04, UV-05, UV-07, UV-08
Question: What must Put(c) and Close(c) do for a connection returned after Release?
Current behaviour: both return nil and the connection is never closed: Put calls Close (channel.go:176), Close finds the close callback nil and returns before closing (channel.go:208-209). DOC-14 "Close closes a single connection" is contradicted.
Options: close it with the configured callback (keep the callback after Release) | return ErrClosed and leave closing to the caller | both
Proposed: close it and return ErrClosed for Put — no connection leaks, and the caller learns the pool is gone.
Status line: OPEN — human decision required

Q-05 — Ping without a Ping callback, and Ping after Release
**Status:** OPEN
Fault: F-15, F-03 (output fault)
Trigger: step-4 matrix walk (pairs P-04a, P-04b)
Cells: Released × ping, Released_WaitersStranded × ping; note on every Open × ping cell
Question: What must Ping return when no Ping callback is configured or the pool is released? Is Ping meant to be safe concurrently with Release?
Current behaviour: calls the nil function (channel.go:220): runtime panic. Ping reads `c.ping` without the mutex while Release writes it under the mutex (channel.go:229) — an unsynchronized access (T-P04a).
Options: return nil when no callback | return an error (ErrClosed after Release) | document as caller error
Proposed: ErrClosed after Release, nil when no callback was configured; read the callback under the mutex.
Status line: OPEN — human decision required

Q-06 — What "Release all connections" covers
**Status:** OPEN
Fault: F-19 (unimplemented requirement), F-07
Trigger: doctrine mapping (DOC-6, DOC-15 → SYS-7)
Cells: × release in every Open state
Question: Must Release close checked-out connections too (now or when they come back), and must it reset openingConns?
Current behaviour: only the idle set is drained and closed (channel.go:238-242); checked-out connections are never closed by the pool; openingConns is not reset.
Options: close checked-out connections when they are returned (Q-04) | track and close them at Release | document "Release closes idle connections only"
Proposed: close them when returned (combined with Q-04); document it.
Status line: OPEN — human decision required

Q-07 — Handed-off connections skip the Ping check; age restarts on Put
**Status:** OPEN
Fault: F-19
Trigger: doctrine mapping (DOC-3 → SYS-6)
Cells: Open_Waiting × ping_failed
Question: Must a connection handed from Put to a waiting Get pass the configured Ping before it is returned? Does a connection's idle age restart on every Put?
Current behaviour: the handoff path checks only idle expiry (channel.go:141-148); Put stamps `time.Now()` on both paths (channel.go:184, :190), so a handed-off connection is never expired in practice.
Options: Ping on the handoff path too | leave the handoff path unchecked and document it
Proposed: Ping on both paths — DOC-3 states invalid connections are discarded, without restriction to the idle path.
Status line: OPEN — human decision required

Q-08 — What Len counts
**Status:** OPEN
Fault: F-03
Trigger: doctrine mapping (DOC-7)
Cells: × len (all states)
Question: Is Len the number of idle connections, or of all live connections (idle + checked out)? What must Len return after Release?
Current behaviour: idle count only, expired-but-not-yet-discarded included (channel.go:247); 0 after Release (channel_rpc_test.go:161).
Options: idle count (document) | live count (openingConns) | both via two methods
Proposed: keep idle count and document it — the tests assert it (channel_rpc_test.go:69, :121, :134).
Status line: OPEN — human decision required

Q-09 — Waiting without timeout; the unreachable ErrMaxActiveConnReached
**Status:** OPEN
Fault: F-13 (delay / late), F-19
Trigger: step-5 lint (waiting without timeout; unbounded queue; no cancellation)
Cells: Open_Waiting × UV-01 (defer), Open_Waiting_CapacityFree × UV-01; DOC-11
Question: Must a waiting Get time out (or be cancellable), and is ErrMaxActiveConnReached the signal for it? Is the waiter queue bounded?
Current behaviour: no timeout or cancellation; `waitTimeOut` is declared (channel.go:46) and never set or read; ErrMaxActiveConnReached (documented "pool limit exceeded", channel.go:13) is produced only behind `!ok` (channel.go:138-139), which no code triggers; connReqs grows without bound (channel.go:135) and keeps popped channels in the backing array until overwritten (channel.go:181-182). TestPool_Get expects the error at channel_rpc_test.go:94 (as-is-validation.md). README.md:15 advertises waiting "like the go db connection pool"; README_ZH_CN.md:10-13 does not list waiting at all (contradiction folded here).
Part B (row get) expects ErrMaxActiveConnReached as the refusal when no further waiting is possible — independent support for the reading that the error is meant to be produced.
Options: configurable wait timeout returning ErrMaxActiveConnReached | fail fast at the cap (no waiting) | context-based Get | keep indefinite waiting and remove the error
Proposed: configurable timeout returning ErrMaxActiveConnReached (matches the test and the declared field).
Status line: OPEN — human decision required

Q-10 — Connections that are never returned
**Status:** OPEN
Fault: F-12 (loss / omission)
Trigger: step-3 checklist (UV-02)
Cells: × UV-02 (all states)
Question: Is the pool responsible for detecting or reclaiming connections that a user never returns (leaks), which otherwise consume capacity forever?
Current behaviour: nothing happens; openingConns keeps the slot (channel.go:159); at the cap every later Get waits forever (T-F06).
Options: document the obligation (NAT-4) | leak detection / max lifetime | expose live count for monitoring
Proposed: document NAT-4 explicitly; consider exposing the live count (Q-08).
Status line: OPEN — human decision required

Q-11 — Ownership misuse corrupts the live-connection count
**Status:** OPEN
Fault: F-14 (duplication), F-18 (subtle value fault), F-08 (double release)
Trigger: step-3 checklist (UV-03, UV-04, UV-05, UV-07, UV-08)
Cells: Open × UV-03, UV-04, UV-05, UV-07, UV-08 (handle cells)
Question: Must the pool defend against a duplicate Put, Put+Close of one connection, double Close, and Put/Close of foreign connections — or is correct ownership a caller obligation?
Current behaviour: all accepted (no connection identity is kept). A duplicate Put lets two Gets share one connection (T-F04); double Close lets the pool exceed MaxCap (T-F05, DOC-8).
Part B (UV-08) adds: Close of a connection that is currently idle closes it but leaves it in the idle set, so a later Get can take a closed connection (caught only if a Ping callback is configured).
Options: track checked-out identities and reject misuse | document as undefined caller behaviour
Proposed: document as caller obligation (NAT-4); optionally guard openingConns from going negative.
Status line: OPEN — human decision required

Q-12 — Callbacks run under the pool mutex
**Status:** OPEN
Fault: F-11 (callback deadlock)
Trigger: step-3 lock-discipline annotation
Cells: Open_Empty_BelowCap × UV-12, Open_Waiting_CapacityFree × UV-12
Question: May the Factory and Close callbacks block, and may they call pool methods? Must a slow factory block every other pool operation?
Current behaviour: factory runs with `mu` held (channel.go:131, :154); the Close callback runs with `mu` held from Close (channel.go:206, :212) but without it from Release's drain (channel.go:241). Reentrancy is undocumented; a callback that calls a pool method deadlocks (T-F08); a slow factory stalls Put, Close, Len and Release (T-F07). Put's send to a waiter under the lock never blocks (capacity 1, one send per waiter) — checked, no deadlock there.
Options: call callbacks outside the lock (reserve the slot first) | document "callbacks must not block or call the pool"
Proposed: call the factory outside the lock with a reserved slot; document the reentrancy rule.
Status line: OPEN — human decision required

Q-13 — InitialCap documented as a minimum
**Status:** OPEN
Fault: F-19
Trigger: doctrine mapping (DOC-12 → SYS-11)
Question: Is InitialCap a minimum the pool maintains (channel.go:19 "minimum number of connections the pool holds") or only an initial fill?
Current behaviour: initial fill only (channel.go:82-89); nothing refills.
Options: maintain the minimum (refill) | correct the comment to "initial"
Proposed: correct the comment — no code path suggests a refill was intended.
Status line: OPEN — human decision required

Q-14 — MaxCap = 0 passes validation
**Status:** OPEN
Fault: F-06 (trap door)
Trigger: pairs table + z3 proof (G-01)
Question: Is MaxCap = 0 (with MaxIdle = InitialCap = 0) a valid configuration?
Current behaviour: accepted (G-01 fact, guard-results.txt); every Get then waits forever (T-F09).
Options: reject MaxCap < 1 | treat 0 as unlimited | accept and document
Proposed: reject MaxCap < 1.
Status line: OPEN — human decision required

Q-15 — Undocumented API contract (thread safety, errors, overflow)
**Status:** OPEN
Fault: F-19
Trigger: step-1 extraction (draft questions on pool.go and README.md)
Question: Is the Pool safe for concurrent use? Which errors may each method return? What happens on Put when the idle set is full (MaxIdle vs MaxCap)?
Current behaviour: every method except Ping takes the mutex (inferred: designed for concurrent use); errors are undocumented on the interface (pool.go:11-21); Put overflow closes the connection (channel.go:193-196).
Options: document the contract in the interface comments
Proposed: document it.
Status line: OPEN — human decision required

Q-16 — Dropped close errors; counter after a fill failure
**Status:** OPEN
Fault: F-03
Trigger: step-5 lint (external operations without failure outcome)
Question: Must errors from the Close callback during internal discards (expiry, Ping failure) and during Release's drain be surfaced or logged?
Current behaviour: discarded (channel.go:118, :125, :144 return values unused; channel.go:241). A fill failure in NewChannelPool leaves openingConns at InitialCap in the discarded object (channel.go:75, :85) — no effect, since the object is not returned.
Options: log them | ignore and document
Proposed: log at debug level (the code already logs via logrus, channel.go:132).
Status line: OPEN — human decision required

Q-17 — A Get racing Release's drain can obtain a connection
**Status:** OPEN
Fault: F-15, F-07
Trigger: adversarial trace (T-P01a-3)
Cells: Released × idle_expired (race exception note)
Question: May a Get that started before Release return a connection of the released pool?
Current behaviour: possible. The Get's snapshot of conns (channel.go:104) races with Release's drain outside the lock (channel.go:238-242); whichever receives first wins. The returned connection is then never closed by the pool (Q-04).
Options: Get re-checks the released state under the lock before returning | accept and close on return (Q-04)
Proposed: re-check under the lock and close the connection.
Status line: OPEN — human decision required

Q-18 — Behaviour under a shared-server outage (multi-instance)
**Status:** OPEN
Fault: F-10 (synchronized reset herd)
Trigger: multi-instance probes (T-M1..T-M3; step-5 lint: retries without maximum)
Question: Should the pool add any protection when the server fails (backoff on factory errors, jittered idle expiry, a bound on discard-and-retry loops), or is that the caller's job?
Current behaviour: no failure memory, no backoff; the Get loop discards and retries without bound (channel.go:119, :126, :145); all initially filled connections share one expiry instant.
Options: caller's responsibility (document) | backoff/jitter in the pool
Proposed: caller's responsibility, documented — the pool keeps no server state today.
Status line: OPEN — human decision required

Q-19 — Test oracle gaps
**Status:** OPEN
Fault: F-21 (mirroring test, structure-bound)
Trigger: step-2 test replay
Question: Which behaviours must the tests assert? (a) TestPool_Get expects ErrMaxActiveConnReached where the model predicts a block (channel_rpc_test.go:93-94); (b) TestPoolConcurrent and TestPoolConcurrent2 assert nothing and do not wait for their goroutines (:166-189, :206-235); TestPoolConcurrent3 is commented out (:238-254); (c) TestPool_Close asserts unexported fields (:146-153); (d) failure messages disagree with the asserted values (:89-90, :122-123); TestPool_Get_Impl type-asserts a possibly nil connection after a failed Get (:48-53); TestNew/TestPoolWriteRead assert little and never release; no race-detector run is configured.
Current behaviour: as described (observed-in-tests).
Options: rewrite against the decided matrix (04-testgen) | keep
Proposed: regenerate from the decided matrix after Q-01..Q-09 are answered.
Status line: OPEN — human decision required

Q-20 — Voided control verdict: Put then Release closes the idle connection
**Status:** OPEN
Fault: F-19
Trigger: adversarial trace (T-P02a; routing rule 5)
Question: Does README.md:55 ("Release all connections in the connection pool, when resources need to be destroyed") cover a connection that was Put back before Release, closed with the configured Close function?
Current behaviour: yes in code (channel.go:239-241). My scope line says the text contemplates the ordering (README example Put at :53, Release at :56); Jev O1: unclear (supported 0.38), scope 0.03 — not source-backed.
Options: confirm | restate the requirement
Proposed: confirm.
Status line: OPEN — human decision required

Q-21 — Voided control verdict: idle expiry, lazily on Get
**Status:** OPEN
Fault: F-19
Trigger: adversarial trace (T-F13; routing rule 5)
Question: Does README.md:13 ("the timeout connection will be closed and discarded") mean expiry on retrieval only (lazy), with age = IdleTimeout still valid, and IdleTimeout = 0 meaning "never expire"? Is the Ping check applied after the expiry check?
Current behaviour: lazy, strict comparison, 0 disables (channel.go:115-116, G-03); expiry before Ping (channel.go:115-128). Scope line: yes for "exceeds → closed and discarded"; Jev O3: unclear (supported 0.24), scope 0.05.
Options: confirm lazy expiry | require a background reaper
Proposed: confirm lazy expiry and document it.
Status line: OPEN — human decision required

Q-22 — Voided control verdict: Get after Release returns ErrClosed
**Status:** OPEN
Fault: F-19
Trigger: adversarial trace (T-P01b; routing rule 5)
Question: Is ErrClosed (pool.go:6-7) the specified result of every Get after Release?
Current behaviour: yes (channel.go:105-106; channel_rpc_test.go:156-157). Scope line: no — the comment does not describe Release or Get; Jev O6: unclear, scope 0.03.
Options: confirm | another error
Proposed: confirm.
Status line: OPEN — human decision required

Q-23 — Voided control verdict: how waiting ends
**Status:** OPEN
Fault: F-19
Trigger: adversarial trace (T-F14; routing rule 5)
Question: README.md:15 says waiting is supported when the pool is full. Is the wait ended only by a Put handing its connection to the oldest waiter (FIFO)? What happens when the handed-off connection turns out expired (the Get loops and may create a new connection, channel.go:141-146)?
Current behaviour: FIFO handoff from Put (channel.go:179-187). Scope line: no — the sentence does not say what ends the wait; Jev O2: unclear (supported 0.23), scope 0.04.
Options: confirm FIFO handoff | other policy (see Q-02, Q-03, Q-09)
Proposed: confirm FIFO handoff, combined with Q-02.
Status line: OPEN — human decision required

## Draft-question disposition (routing rule 6)

Every question from the Step-1 drafts ends in a Q above. `dv-<file>.json`, entry n in its `questions` list:

| draft | → | reason |
|---|---|---|
| readme 1 (waiting, connection becomes available) | Q-23 | |
| readme 2 (after Release) | Q-06 | also Q-04 |
| readme 3 (Ping before returning) | Q-07 | |
| readme 4 (Ping failure vs idle timeout) | Q-21 | |
| readme 5 (when idle timeout is checked) | Q-21 | |
| readme 6 (lazy vs proactive expiry) | Q-21 | |
| readme 7 (ordering Get vs Ping discard) | Q-07 | |
| readme 8 (Put at MaxCap) | Q-15 | code answers it (overflow closes); contract undocumented |
| readme 9 (Release uses Close function) | Q-20 | |
| readme 10 (MaxIdle vs MaxCap) | Q-15 | |
| readme 11 (Len after Release) | Q-08 | |
| readme 12 (expiry before or after Ping) | Q-21 | |
| pool 1 (error semantics) | Q-15 | |
| pool 2 (when ErrClosed) | Q-22 | |
| pool 3 (concurrency safety) | Q-15 | |
| pool 4 (behaviour after Release) | Q-04 | also Q-05, Q-01 |
| pool 5 (Release vs Close) | Q-06 | |
| pool 6 (what Len counts) | Q-08 | |
| pool 7 (Put ownership / blocking) | Q-11 | |
| pool 8 (Close ownership) | Q-11 | |
| pool 9 (ordering Put/Get/Release) | Q-01 | the pairs P-01..P-05 cover the orderings |
| tests 1-9, 11-13 | Q-19 | test-oracle gaps |
| tests 10 (ErrMaxActiveConnReached only in TestPool_Get) | Q-09 | |
| channel 1 (UpdateMaxActive absent) | Q-15 | no source mentions such a method; maxActive is immutable (channel.go:74); folded as API-surface documentation |
| channel 2 (fill failure cleanup) | Q-16 | |
| channel 3 (waitTimeOut) | Q-09 | |
| channel 4 (Release vs blocked waiter) | Q-01 | |
| channel 5 (connReqs tail retention) | Q-09 | |
| channel 6 (waiter receives timed-out connection) | Q-23 | |
| channel 7 (Put sends under the lock) | Q-12 | checked: never blocks |
| channel 8 (factory under the lock) | Q-12 | |
| channel 9 (Close after Release, counter) | Q-04 | |
| channel 10 (openingConns vs maxActive under races) | Q-11 | |
| channel 11 (snapshot then Release closes channel) | Q-17 | the nil-value branch returns ErrClosed (channel.go:111-112) |
| channel 12 (Put after Release silent) | Q-04 | |
| channel 13 (Len vs Release) | Q-08 | |
| channel 14 (openingConns before fill) | Q-16 | |
| channel 15 (lazy expiry) | Q-21 | |
| channel 16 (Ping reentrancy) | Q-12 | |
| channel 17 (timestamp reset on Put) | Q-07 | |
| channel 18 (IdleTimeout 0) | Q-21 | |
| channel 19 (MaxCap 0) | Q-14 | |
| channel 20 (drain vs Get on the closed channel) | Q-17 | |
| channel 21 (Ping nil callback) | Q-05 | |
| channel 22 (looping after repeated Ping failures) | Q-18 | |
| channel 23 (who closes connReqs channels) | Q-09 | and Q-01 |

## Summary count (Step 7)

states 7 / events incl. undesired variants 22 (10 + 12) / interaction pairs 5 (10 orderings) /
matrix cells 154 / UNSPECIFIED 2 / accidental ignores 24 / guard groups proven 6 /
guard violations 0 (SYS-invariant checks: 2 violations) / not-formalizable 2 /
findings 23 / open questions 23 (before Part B).
