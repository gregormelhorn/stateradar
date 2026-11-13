# channelPool — Open domain questions (Step 7)

Every hole cell, contradiction, invariant violation, doctrine finding, lint finding and adversarial question, consolidated. None is resolved here. Recommendations are `proposed` and carry no authority. Each question carries the ODC fields `fault` (formats/rules.toml fault catalogue) and `trigger` (the detector that found it).

### Q-01 — Get when MaxCap connections are live: wait, or fail with ErrMaxActiveConnReached?
Question: When MaxCap conns are live and none is idle, should Get wait (README) or return `ErrMaxActiveConnReached` (error comment "连接池超限", and the repository test)? Should MaxCap = 0 be accepted?
Current behaviour: waits without bound (observed-in-code, channel.go:133-137); the only `return nil, ErrMaxActiveConnReached` (channel.go:139) needs a closed waiter channel and no code closes one, so it is unreachable (guard group G-07). TestPool_Get expects the error (channel_rpc_test.go:93-95) and hangs (run R0). MaxCap = InitialCap = MaxIdle = 0 passes validation (G-01 probe) and every Get then waits forever (as-is test T17).
Cells: Open_Empty_AtCap x GET, Open_Waiting x GET. Doctrine: DOC-4 (README.md:15) vs DOC-12 (channel.go:13). Traces: T-01, T-14. Contradiction C-1.
Options: wait (fix the test, delete or repurpose the error) | fail fast with ErrMaxActiveConnReached | wait with a bound, then ErrMaxActiveConnReached (see Q-02)
Proposed: wait with a bound, then return ErrMaxActiveConnReached; reject MaxCap = 0 at construction
**Fault:** F-19
**Trigger:** step-2 test replay
**Status:** OPEN — human decision required

### Q-02 — Is a waiting Get bounded or cancellable?
Question: How long may a Get wait at MaxCap, and can the caller cancel it? Is the number of waiting Gets bounded?
Current behaviour: no timeout, no cancellation, no limit on waiters (observed-in-code, channel.go:134-137); the `waitTimeOut` field exists and is never set or read (channel.go:46). README promises waiting "like the go db connection pool" (README.md:15), whose waits are context-cancellable — the README does not say that explicitly. A late Put (UV-02) leaves waiters blocked for the whole delay.
Cells (holes): Open_Waiting x UV-02, Open_Waiting_BelowCap x UV-02, Open_Waiting_IdleStranded x UV-02. Related cells: Open_Empty_AtCap x GET, Open_Waiting x GET. Lints L-01, L-04, L-07, L-11. Trace T-01.
Options: unbounded wait (document it) | a configured wait timeout (use waitTimeOut) | a context-taking Get variant | both
Proposed: a configured wait timeout that returns ErrMaxActiveConnReached, plus a context variant
**Fault:** F-13
**Trigger:** step-5 lint
**Status:** OPEN — human decision required

### Q-03 — Should freed capacity serve a waiting Get?
Question: When a Close (or Get's discard of an expired or Ping-failed conn) frees capacity while Gets wait, should the oldest waiting Get be served (a new conn created for it, or it is woken to create one)? May a new Get create a conn ahead of older waiters?
Current behaviour: Close decrements the count and returns; no waiter is woken (observed-in-code, channel.go:202-213). The waiters stay blocked (state Open_Waiting_BelowCap) until a Put; a newly arriving Get creates a conn ahead of them (channel.go:154). If holders always Close instead of Put, waiters never return (as-is test T2).
Cells: Open_Waiting x CLOSE, Open_Waiting_BelowCap x CLOSE, Open_Waiting_BelowCap x GET, Open_Waiting x UV-04. Invariants SYS-3, SYS-10 violated. Lints L-09, L-12. Trace P-04b.
Options: wake/serve the oldest waiter on every decrement | let waiters re-check on any decrement, FIFO kept | keep as is and document (Put is the only way to serve waiters)
Proposed: on every decrement while waiters exist, create a conn for the oldest waiter (FIFO), so no Get waits while capacity is free
Part B: the blind pass expected freed capacity to serve waiters (CLOSE row, P-04b) — divergence from the as-is matrix, folded here (part-b-diff.md).
**Fault:** F-01
**Trigger:** step-1 extraction
**Status:** OPEN — human decision required

### Q-04 — May a Get wait while an idle conn exists?
Question: A Put that lands between a Get's empty idle check and its lock leaves an idle conn while that Get waits. Is that acceptable? May later Gets take the idle conn ahead of the waiter?
Current behaviour: the Get registers as waiter and blocks; the idle conn stays (state Open_Waiting_IdleStranded); a new Get takes it ahead of the waiter (observed-in-code, channel.go:130-137, channel.go:110). Reproduced with real Put/Get calls (as-is test T10).
Cells: Open_Waiting_IdleStranded x GET, x PUT, x CLOSE. Invariants SYS-3, SYS-10. Trace P-01b.
Options: re-check the idle store under the lock before waiting | serve waiters first on every Get | accept and document
Proposed: re-check the idle store under the lock before registering as waiter
**Fault:** F-01
**Trigger:** pairs table + z3 proof
**Status:** OPEN — human decision required

### Q-05 — What happens to waiting Gets at Release?
Question: Gets that wait when Release runs: should they return ErrClosed (or another error)? And a Get that saw the pool open but takes the lock after Release while MaxCap conns are live — should it wait?
Current behaviour: Release leaves the waiter list untouched and closes no waiter channel (observed-in-code, channel.go:224-243); waiters block forever (as-is test T1); a later Put serves no one because the released check precedes the waiter check (channel.go:174, channel.go:179). A Get racing Release at MaxCap appends itself as waiter after Release, because the at-cap test precedes the released test (channel.go:133, channel.go:150; G-02 probe).
Cells: Open_Waiting x RELEASE, Open_Waiting_BelowCap x RELEASE, Open_Waiting_IdleStranded x RELEASE. Invariant SYS-4. Lints L-06, L-09, L-11, L-12. Traces T-02, P-02b. Doctrine DOC-6, DOC-13.
Options: Release wakes every waiter with ErrClosed | Release waits for waiters to be served | leave and document
Proposed: Release closes every waiter channel and waiting Gets return ErrClosed; test the released flag before the at-cap test
**Fault:** F-20
**Trigger:** step-5 lint
**Status:** OPEN — human decision required

### Q-06 — What happens to checked-out conns at and after Release?
Question: README says Release releases "all connections in the connection pool". Should conns that are checked out at Release be closed when they come back (Put or Close after Release)? Should Release wait for them, or track them? What should a Get that obtains a conn from a pool being released (during the drain, or from a Factory call in flight) do?
Current behaviour: Release closes only idle conns (channel.go:238-242). Put after Release calls Close, which returns nil without closing because the Close callback was cleared (channel.go:174-176, channel.go:208-209; as-is test T3); Close after Release likewise closes nothing and returns nil (as-is test T4). A Get that captured the idle store before Release can receive an idle conn during the drain; a Factory call in flight completes after Release and its conn is returned to the caller (P-02b, P-06b). An expired conn discarded by such a Get is not closed. Conns never given back (UV-01) are never closed by the pool.
Cells (holes): Released x PUT, CLOSE, UV-01, UV-02, UV-03, UV-04, UV-05, UV-06, UV-07, UV-08, UV-10. Related: Open_* x RELEASE, Open_Creating x RELEASE. Invariant SYS-5. Doctrine DOC-6, DOC-14 (violated). Lints L-05, L-06, L-09. Traces P-02a, P-02b, P-03b, P-06a, P-06b. Contradictions C-3, C-4.
Options: keep the Close callback after Release so returned conns are closed | Release also closes checked-out conns it tracks | Release waits for all conns | document that returned conns leak after Release
Proposed: keep the Close callback after Release, so Put and Close after Release close the conn and return ErrClosed or nil
**Fault:** F-07
**Trigger:** step-4 matrix walk
**Status:** OPEN — human decision required

### Q-07 — What may Factory return?
Question: Is a Factory result of (conn, err) with both non-nil allowed, and what should the pool do with the conn? Is (nil, nil) allowed?
Current behaviour: (conn, err) → Get returns (nil, err) and the conn is dropped without the Close callback (observed-in-code, channel.go:155-157; as-is test T8). (nil, nil) → the count is incremented and (nil, nil) returned; nil cannot be Put or Closed, so the slot is lost for good (channel.go:159-161, channel.go:168-169; as-is test T9). No contract text (channel.go:25-26, README.md:21).
Cells (holes): Open_Creating x UV-13, Open_Creating x UV-14. NAT-1. Lint L-03. Traces T-05, T-06. Seam-contract sweep: Factory.
Options: document NAT-1 as a contract on the user | close a conn that comes with an error | treat (nil, nil) as an error | both defensive measures
Proposed: document NAT-1, close a conn that comes with an error, and turn (nil, nil) into an error without counting it
**Fault:** F-18
**Trigger:** step-3 checklist
**Status:** OPEN — human decision required

### Q-08 — Callback contract: may Factory and the Close callback block or re-enter the pool?
Question: May Factory or the Close callback call methods of the same pool? May they block without bound? What should the pool guarantee if they do?
Current behaviour: both run while the pool mutex is held — Factory in Get (channel.go:131, channel.go:154), the Close callback in Close and therefore in Put-when-full and Get's discard (channel.go:206-212). A re-entrant locking call deadlocks (as-is test T14); a hanging callback blocks Put, Close, Release, Len and every Get (Get locks the mutex first when it reads the idle store, channel.go:96, channel.go:104). Release runs the callback without the lock (channel.go:232, channel.go:241). No doc states a contract (README.md:17-62; Config comments channel.go:25-30).
Cells (holes): Open_Creating x UV-12; Open_Idle, Open_IdleFull, Open_Empty_BelowCap, Open_Empty_AtCap, Open_Waiting, Open_Waiting_BelowCap, Open_Waiting_IdleStranded x UV-16. Related: Open_Creating x UV-17, Open_* x UV-18. NAT-2, NAT-3. Lints L-01, L-03. Trace T-08.
Options: document "callbacks must not call the pool and must return promptly" | call callbacks outside the mutex | add timeouts
Proposed: call Factory and the Close callback outside the mutex (reserve the slot first), and document that callbacks must return promptly
**Fault:** F-11
**Trigger:** step-3 lock-discipline annotation
**Status:** OPEN — human decision required

### Q-09 — Should the pool protect its count against caller misuse?
Question: Double Close, Close after Put, a racing Put and Close, Put of a conn twice, and Put or Close of a conn the pool never created all corrupt the live count or hand one conn to two callers. Should the pool detect any of these, or is NAT-4 / NAT-5 a documented caller obligation?
Current behaviour: no identity tracking. Each Close decrements (channel.go:211), so double or foreign Close lets the pool exceed MaxCap (as-is tests T5, T6); duplicate Put stores the conn twice and two Gets receive it (channel.go:190; as-is test T7); Close after Put closes a conn that is still idle or held by another caller.
Cells: UV-03, UV-04, UV-05, UV-06, UV-07, UV-08 in the open rows. Invariants SYS-1, SYS-8. Lint L-10. Traces T-03, T-04, P-05a, P-05b.
Options: document caller obligations only | track checked-out conns (set keyed by conn) and reject misuse with an error | wrap conns in a pool-owned handle whose release is idempotent
Proposed: document the obligations now; a tracking handle is the robust option if the API may change
**Fault:** F-08
**Trigger:** step-3 checklist
**Status:** OPEN — human decision required

### Q-10 — Unsynchronized Ping reference while Release runs
Question: Get reads the Ping reference without the lock while Release clears it under the lock. Is a Get that runs concurrently with Release supposed to be safe?
Current behaviour: data race on `c.ping` (read channel.go:123 and channel.go:220, write channel.go:229). The race detector reports it on the repository's own TestPoolConcurrent (run R0b) and on as-is test T11. If the second read sees nil after the first saw non-nil, the call at channel.go:220 is a nil-function panic (scheduling-dependent; unverifiable-runtime, PA-19).
Cells: Open_Idle x GET (idle path with Ping), Released x GET. Traces P-08a, P-08b, P-02b.
Options: read the Ping reference under the lock (or once, into a local) | never clear it in Release | document that Release must not run concurrently with Get
Proposed: copy the Ping reference under the lock once per Get and never call through the field
**Fault:** F-05
**Trigger:** step-2 test replay
**Status:** OPEN — human decision required

### Q-11 — Is `Ping` public API, and what should it do without a Ping function?
Question: `(*channelPool).Ping` is exported but not in the `Pool` interface. Is it API? What should it return when no Ping is configured, or after Release?
Current behaviour: calls `c.ping(conn)` with no nil check (channel.go:220): panics when no Ping is configured and always after Release (as-is test T12). Guard group G-09: violation (no branch for "no Ping configured").
Cells: PING column (all rows). Scope doubt from Step 0.
Options: unexport it | return nil when no Ping is configured | return an error | add it to the Pool interface
Proposed: return nil when no Ping is configured and ErrClosed after Release
**Fault:** F-03
**Trigger:** pairs table + z3 proof
**Status:** OPEN — human decision required

### Q-12 — When is an expired idle conn closed?
Question: README: "the timeout connection will be closed and discarded". Must that happen when the idle time passes (a reaper), or is "on the next Get" enough? Is a conn whose idle age equals IdleTimeout still valid? Does the idle timeout say anything about checked-out conns? Does IdleTimeout ≤ 0 mean "no idle timeout" (the code treats it so, G-03; no doc says it — Part-B divergence folded here)?
Current behaviour: expiry is checked only when a Get dequeues the conn (channel.go:115-120); without Gets, expired conns stay open and counted until Release (as-is test T13). Age = IdleTimeout is not expired (strict `Before`, G-03 probe). Checked-out conns are not timed.
Cells (holes): Open_Idle, Open_IdleFull, Open_Waiting_IdleStranded, Open_Creating x IDLE_TIMEOUT. Doctrine DOC-2 (timing violated), DOC-11 (scope line "no" on P-07b). Traces P-07a, P-07b, T-10.
Options: lazy on Get (document it) | background reaper | lazy plus a reaper at an interval
Proposed: keep lazy expiry and document it; age = IdleTimeout counts as valid
**Fault:** F-13
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

### Q-13 — Must a conn handed to a waiting Get pass Ping?
Question: With Ping configured, a conn that Put hands straight to a waiting Get is returned without Ping. Is that intended?
Current behaviour: the hand-off path checks only the age (channel.go:141-148); the idle path checks age and Ping (channel.go:115-129). A broken conn Put while Gets wait reaches a caller unvalidated (UV-10).
Cells: Open_Waiting, Open_Waiting_BelowCap, Open_Waiting_IdleStranded x UV-10; Open_Waiting x PUT. Invariant SYS-7, doctrine DOC-3 (violated). Contradiction C-6. Trace T-11.
Options: ping on the hand-off path too | document that Ping applies to idle conns only
Proposed: ping on the hand-off path too
**Fault:** F-04
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

### Q-14 — Is InitialCap a minimum?
Question: The Config comment calls InitialCap the minimum number of conns ("连接池中拥有的最小连接数"); the README calls it the initial number. Should the pool replenish to InitialCap?
Current behaviour: pre-fills InitialCap at construction (channel.go:82-89); never replenishes; expiry and Close drop below it (as-is test T16).
Cells: invariant SYS-9 (violated in open rows). Doctrine DOC-10. Contradiction C-2. Trace T-12.
Options: initial only (fix the comment) | minimum, with replenishment
Proposed: initial only; fix the comment
**Fault:** F-19
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

### Q-15 — What does Len count?
Question: README: "View the number of connections in the current connection pool". Idle conns only, or all live conns?
Current behaviour: the idle count (channel.go:247); TestPool_Get asserts that (channel_rpc_test.go:69, observed-in-tests).
Cells: LEN column. Doctrine DOC-7.
Options: idle count (document) | live count | both, as two methods
Proposed: idle count, documented as such
**Fault:** F-03
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

### Q-16 — Conns that are never given back
Question: A caller that never Puts or Closes a conn consumes one unit of MaxCap for good; at MaxCap every later Get waits forever. Should the pool detect or bound this (leak detection, a maximum lifetime for checked-out conns), or is it purely a caller obligation?
Current behaviour: no record of checked-out conns (channel.go:159 counts, nothing tracks); nothing happens.
Cells (holes): UV-01 in Open_Idle, Open_IdleFull, Open_Empty_BelowCap, Open_Empty_AtCap, Open_Waiting, Open_Waiting_BelowCap, Open_Waiting_IdleStranded, Open_Creating. NAT-4.
Options: caller obligation (document) | optional leak detection (log) | bounded checkout lifetime
Proposed: caller obligation, documented; combine with a bounded wait (Q-02) so the symptom is an error, not a hang
**Fault:** F-12
**Trigger:** step-3 checklist
**Status:** OPEN — human decision required

### Q-17 — Close-callback errors and the count
Question: The count is decremented before the Close callback runs, and the callback's error is discarded on Get's discard path and in Release. Is that intended?
Current behaviour: channel.go:211 decrements, channel.go:212 calls; Get ignores `c.Close`'s result (channel.go:118, channel.go:125, channel.go:144); Release ignores closeFun's result (channel.go:241).
Cells: UV-15 column. Lint L-03. Trace T-13.
Options: keep (a failed close still counts as gone) and document | surface the error (log or hook)
Proposed: keep the decrement; surface discarded errors through an optional hook
**Fault:** F-03
**Trigger:** step-5 lint
**Status:** OPEN — human decision required

### Q-18 — Re-dial bursts across pools
Question: After a server restart, or when conns created together expire together, every pool re-dials on its next Gets with no backoff and no jitter, and Factory errors are returned immediately. Should the pool add jitter to expiry or backoff to Factory errors, or leave that to callers?
Current behaviour: no backoff, no jitter (channel.go:115-120, channel.go:155-157); pre-filled conns share a construction timestamp (channel.go:88).
Cells: UV-11 (Open_Creating), IDLE_TIMEOUT column. NAT-SYS-1. Lint L-08. Traces M-01, M-02, M-03.
Options: leave to callers (document) | jitter on IdleTimeout | backoff after consecutive Factory errors
Proposed: leave to callers and document; reconsider if a real outage shows a herd
**Fault:** F-10
**Trigger:** multi-instance probes
**Status:** OPEN — human decision required

### Q-19 — The mutex is held while Factory runs
Question: While any Get runs Factory, every Put, Close, Len, Release and every other Get waits (Get locks the mutex first in getConns, channel.go:96, channel.go:104), and creations are serialized one at a time. Is that intended?
Current behaviour: Factory is called between `c.mu.Lock()` and `c.mu.Unlock()` (channel.go:131, channel.go:154, channel.go:160); as-is test T15 shows Put blocked for the Factory's duration.
Cells: Open_Creating x GET, PUT, CLOSE, LEN, RELEASE, CLOSEFN_OK, UV-02, UV-03, UV-04, UV-05, UV-06, UV-07, UV-08, UV-10, UV-15, UV-16, UV-18 (`defer (queued)`). Lint L-12 (user-model gap). Traces T-07, M-03.
Options: keep and document | reserve the slot (count+1) under the lock and call Factory outside it, undoing on error
Proposed: reserve the slot under the lock, call Factory outside it
Part B: "must Release wait for a Factory call in flight?" (P-06b) is folded here; as-is, Release waits on the mutex (Open_Creating x RELEASE).
**Fault:** F-13
**Trigger:** step-3 lock-discipline annotation
**Status:** OPEN — human decision required

### Q-20 — Is a second Release a documented no-op?
Question: Release on an already released pool (and concurrent Release calls): is "no-op, nothing closed twice" the intended contract?
Current behaviour: returns early when the idle store is already cleared (observed-in-code, channel.go:234-235); the matrix cell Released x RELEASE is `ignore (documented)` on the strength of that explicit check only — no requirement or doc states it. The blind pass marked it UNSPECIFIED (divergence, part-b-diff.md).
Cells: Released x RELEASE. Traces P-09a, P-09b.
Options: document idempotent Release | return/raise an error on a second Release
Proposed: document idempotent Release
**Fault:** F-19
**Trigger:** part-B diff
**Status:** OPEN — human decision required

## Summary count

Filled in `summary.md` after Step 8 and Part B.
