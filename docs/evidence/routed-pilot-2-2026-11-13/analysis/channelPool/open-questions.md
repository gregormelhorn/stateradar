# channelPool — Step 7 open domain questions

Every hole cell, contradiction, invariant violation, lint finding, voided control verdict and adversarial question, consolidated. Nothing is resolved here; every recommendation is `proposed`. Each question records its fault class (`formats/rules.toml`) and the trigger that found it. Draft-verify contributions are named in the text where Flash raised the same question independently (Step-1 draft questions, see the disposition table in `extraction.md`).

## Q-01: What must Release do with Gets that are blocked waiting for a connection?
**Question:** When Release runs while Gets wait at capacity, should they be woken, and with which result?
**Current behaviour:** they are never woken and block forever: Release leaves `connReqs` untouched (observed-in-code channel.go:225-232) and no code closes a request channel, so the `ErrMaxActiveConnReached` branch (channel.go:138-139) is unreachable. Executed: `as-is-tests.md` T1.
**Cells:** Open_AtCapacity_Waiting × E-RELEASE, Open_Waiting_Stranded × E-RELEASE, Released × UV-GET-DELAY. Invariant SYS-4. Lints L-6, L-9, L-11. Traces P-01a.
**Options:** wake every waiter with `ErrClosed` | wake with `ErrMaxActiveConnReached` | leave blocked (document it)
**Proposed:** wake with `ErrClosed` — Release ends the pool, and `ErrClosed` is the documented post-release error (pool.go:6).
**Fault:** F-20, F-07
**Trigger:** step-1 extraction
**Part B:** Part B (blind): convergent-hole on P-01a and UV-GET-DELAY (leak-dependent).
**Status:** OPEN — human decision required (Flash's channel.go draft raised the same question)

## Q-02: Must a waiting Get be bounded or cancellable?
**Question:** "support for connection waiting (like the go db connection pool)" (README.md:15) — should a Get at capacity wait forever, wait up to a configured timeout, or accept a context?
**Current behaviour:** waits without bound and cannot be cancelled (channel.go:137); the field `waitTimeOut` is declared and never used (channel.go:46); the waiter queue has no bound (channel.go:135).
**Cells:** Open_AtCapacity_Waiting × UV-GET-DELAY, Open_Waiting_Stranded × UV-GET-DELAY; related Open_AtCapacity × E-GET, Open_AtCapacity_Waiting × E-GET. Lints L-1, L-4, L-7, L-11. Traces T-01, T-09, T-13.
**Options:** unbounded wait (document) | wait timeout from Config (new field or the unused `waitTimeOut`) | context-aware Get | fail fast at capacity (see Q-03)
**Proposed:** a configurable wait timeout returning `ErrMaxActiveConnReached` on expiry, plus a bound on the queue — reconciles the error name with the waiting feature.
**Fault:** F-13, F-09
**Trigger:** step-5 lint
**Part B:** Part B (blind): convergent-hole on UV-GET-DELAY (UNSPECIFIED: requirement silent).
**Status:** OPEN — human decision required (Flash raised the unused `waitTimeOut` and the unbounded queue)

## Q-03: Is a Get at capacity supposed to fail with ErrMaxActiveConnReached?
**Question:** The test `TestPool_Get` expects `ErrMaxActiveConnReached` from a Get at capacity (channel_rpc_test.go:93-95); the error's doc says "pool limit exceeded" (channel.go:13); the README promises waiting (README.md:15); the code waits. Which is intended?
**Current behaviour:** the Get waits (channel.go:137). Executed: the existing suite hangs in `TestPool_Get` until the test timeout (`panic: test timed out after 1m0s`, goroutine at channel.go:137), so the six later tests never run in a plain `go test ./...`.
**Cells:** Open_AtCapacity × E-GET (DOC-13 maps to Open_AtCapacity_Waiting × UV-GET-DELAY). Lint L-5.
**Options:** waiting is intended: fix the test, document the error's real use | fail fast is intended: return the error at capacity | both: wait with timeout, then the error (Q-02)
**Proposed:** decide together with Q-02; the test is the deviation report of whichever behaviour is chosen.
**Fault:** F-19
**Trigger:** step-2 test replay
**Status:** OPEN — human decision required

## Q-04: When capacity becomes free by Close, must waiting Gets be served?
**Question:** Close at capacity decrements the open count; should a queued waiter then get a newly created connection, or keep waiting for a Put? And may a new Get overtake queued waiters?
**Current behaviour:** Close wakes nobody (channel.go:211); the waiters stay blocked although capacity is free (state Open_Waiting_Stranded), while a newly arriving Get creates a connection ahead of them (channel.go:154). z3: SYS-3 is not preserved by E-CLOSE with waiters. Executed: `as-is-tests.md` T3.
**Cells:** Open_AtCapacity_Waiting × E-CLOSE (→ Open_Waiting_Stranded), Open_Waiting_Stranded × E-CLOSE, Open_Waiting_Stranded × E-GET; also UV-CLOSE-DUP / UV-CLOSE-FOREIGN in Open_AtCapacity_Waiting. Invariant SYS-3. Lint L-9. Traces P-03a.
**Options:** Close signals the oldest waiter, which then creates a connection | leave as is (waiters wait for a Put) | Close with waiters creates a replacement and hands it over
**Proposed:** Close signals the oldest waiter (FIFO), so waiters are never overtaken while capacity is free.
**Fault:** F-12, F-01
**Trigger:** step-4 matrix walk
**Part B:** Part B (blind): convergent-hole on P-03a (leak-dependent).
**Status:** OPEN — human decision required

## Q-05: May a Get queue itself while an idle connection is available?
**Question:** A Get that saw no idle connection and a Put that lands before that Get takes the lock leave the Get queued while a connection sits idle. Is that acceptable?
**Current behaviour:** the Get queues (channel.go:130-137) after the Put enqueued without a waiter (channel.go:189-190); a later Get takes the idle connection first; the queued Get waits for another Put (trace P-02a; inferred from the code structure; executed statistically in `as-is-tests.md` T4).
**Cells:** state Open_Waiting_Stranded (reached from Open_AtCapacity by the interleaving); Open_Waiting_Stranded × E-PUT, × I-IDLE-EXPIRE. Invariant SYS-3. Lint L-12.
**Options:** re-check the idle channel under the lock before queueing | accept and document | let Put prefer idle-channel delivery that wakes waiters
**Proposed:** re-check under the lock before queueing.
**Fault:** F-15, F-01
**Trigger:** adversarial trace
**Part B:** Part B (blind): divergence on P-02a folded here — the blind pass expects the Get to be served from the idle store (the option "re-check before queueing"); independent of the catalogue's leaks.
**Status:** OPEN — human decision required

## Q-06: What do Put, Close and Get mean after Release, and does Release cover checked-out connections?
**Question:** "Release all connections in the connection pool" (README.md:55): only the idle ones, or every connection the pool created? What should a late Put or Close do, and is `ErrClosed` from a late Get the intended contract?
**Current behaviour:** Release closes idle connections only (channel.go:238-242). A later Put or Close returns nil and calls no close function, so a connection checked out at Release is never closed by the pool and the caller is not told (channel.go:176, channel.go:208). A late Get returns `ErrClosed` (channel.go:106). Executed: `as-is-tests.md` T2, T12.
**Cells:** Released × E-PUT, Released × E-CLOSE, Released × UV-PUT-LOSS / UV-PUT-DUP / UV-PUT-FOREIGN / UV-PUT-BROKEN / UV-PUT-CLOSE-SAME / UV-CLOSE-DUP / UV-CLOSE-FOREIGN / UV-CLOSE-IDLE (all `ignore (accidental)`); related: the E-RELEASE cells of the four Open states without waiters. Invariant SYS-5. Lints L-5, L-6, L-9. Traces P-01a, P-05a, P-06b, P-07b. Voided control verdicts folded here: P-06a (README.md:55, scope no; Jev unclear, scope 0.03) and T-04 (pool.go:6, scope no; Jev unclear, scope 0.02).
**Options:** a late Put/Close closes the connection with the original close function | a late Put/Close returns `ErrClosed` and the caller closes | Release waits for checked-out connections | leave as is (document that the caller owns closing after Release)
**Proposed:** keep the close function after Release so late Put/Close close the connection, and return `ErrClosed` from Put; confirm `ErrClosed` for late Get.
**Fault:** F-07
**Trigger:** step-4 matrix walk
**Status:** OPEN — human decision required (Flash raised "are connections held by callers leaked on Release?")

## Q-07: What must a Get that runs concurrently with Release return?
**Question:** A Get in progress when Release starts can (a) receive a connection Release is draining and return it, (b) be inside Factory and return a new connection after Release was called, (c) in the window before the idle channel is closed, queue itself at capacity on a released pool and wait forever, or (d) return `ErrClosed`. Which outcomes are allowed?
**Current behaviour:** timing decides (cell UNSPECIFIED): the Get's channel snapshot (channel.go:104) outlives Release's field clearing (channel.go:227); the capacity test precedes the released test (channel.go:133 before channel.go:150; z3 G-04 ordering witness); Factory under the lock delays Release (channel.go:154). Executed: `as-is-tests.md` T13 (case b).
**Cells:** Released × UV-GET-STALE (UNSPECIFIED). Invariant SYS-13. Lint L-12. Traces P-04a, P-05a, T-11.
**Options:** every Get not yet returned when Release starts returns `ErrClosed` (and closes what it obtained) | connections obtained during Release are allowed but must be closed by the pool on return | leave as is
**Proposed:** check the released flag under the lock before queueing and after Factory returns; close and refuse what was obtained during Release.
**Fault:** F-15, F-07
**Trigger:** adversarial trace
**Part B:** Part B (blind): divergence on UV-GET-STALE folded here — the blind pass expects a stale Get to run to completion with the connection it took (handle).
**Status:** OPEN — human decision required (Flash asked whether Get's receive from a channel closed by Release is safe)

## Q-08: Is the unlocked read of the ping function a defect to fix?
**Question:** Get reads `c.ping` without the lock (channel.go:123) while Release writes it under the lock (channel.go:229). A Get that passed the nil check can then call a nil function (channel.go:220) and panic.
**Current behaviour:** data race; possible nil-function panic in the caller (trace P-04a). Executed: `as-is-tests.md` T5 (race detector report).
**Cells:** Released × UV-GET-STALE (one of its outcomes). Invariant SYS-14.
**Options:** read `ping` under the lock with the snapshot | keep `ping` immutable (do not clear it on Release) | accept and document "do not Release concurrently with Get"
**Proposed:** keep the callbacks immutable after construction and gate on a released flag instead.
**Fault:** F-05
**Trigger:** step-3 lock-discipline annotation
**Status:** OPEN — human decision required

## Q-09: May user callbacks run while the pool mutex is held, and what are callbacks allowed to do?
**Question:** Factory runs under `mu` (channel.go:154) and the Close callback runs under `mu` (channel.go:212). A slow callback stalls every pool operation including Len and Release; a callback that calls any pool method deadlocks. The README and doc comments say nothing (README.md:21-27, channel.go:25-30). Is this the contract?
**Current behaviour:** stall and deadlock as described. Executed: `as-is-tests.md` T8 (deadlock), T9 (Len blocked by Factory).
**Cells:** UV-FACTORY-SLOW, UV-CLOSEFN-SLOW, UV-CB-REENTER in every Open state where the callback runs. Invariant SYS-12. Traces T-07, T-08, P-05a, M-03.
**Options:** call callbacks outside the lock (reserve the slot first) | document "callbacks must not block or call the pool" | both
**Proposed:** call Factory and Close outside the lock (reserve the capacity slot under the lock), and document the reentrancy rule.
**Fault:** F-11
**Trigger:** step-3 lock-discipline annotation
**Part B:** Part B (blind): convergent-hole on UV-CB-REENTER; UV-FACTORY-SLOW, UV-CLOSEFN-SLOW and P-05a were catalogue artefacts (lock table misread), repaired.
**Status:** OPEN — human decision required (Flash raised "if the user factory blocks or calls back into the pool, does that deadlock?")

## Q-10: Must the pool track which connections it handed out?
**Question:** Close and Put accept any non-nil value. Close of a duplicate, foreign or idle connection decrements the open count; Put of a foreign connection adds it uncounted; Put plus Close of the same connection leaves a closed connection in circulation. Should the pool detect these, and what should it do?
**Current behaviour:** no ownership record (channel.go:183, 190, 211). The open count can go negative and the pool then creates more than MaxCap live connections (z3 witness in `invariant-results.txt`; executed `as-is-tests.md` T6).
**Cells:** UV-CLOSE-DUP, UV-CLOSE-FOREIGN, UV-CLOSE-IDLE, UV-PUT-FOREIGN, UV-PUT-CLOSE-SAME in the Open states. Invariants SYS-1, SYS-2. Lint L-10. Traces P-08a, P-08b, T-05.
**Options:** track handed-out connections (set or wrapper type) and reject unknown or repeated returns with an error | clamp the counter at zero | document NAT-4 as a caller obligation
**Proposed:** track ownership and return an error for unknown or repeated returns.
**Fault:** F-05, F-17
**Trigger:** step-3 checklist
**Status:** OPEN — human decision required

## Q-11: Must a duplicate Put be prevented from handing one connection to two callers?
**Question:** Putting the same connection twice stores it twice; two later Gets (or two waiters) receive the same connection. Is the caller solely responsible?
**Current behaviour:** both copies are stored or handed off (channel.go:190, channel.go:183); with a full idle store the duplicate is closed while the first copy stays idle (channel.go:196). Executed: `as-is-tests.md` T7.
**Cells:** UV-PUT-DUP in the Open states. Invariant SYS-6. Lint L-10. Trace T-06.
**Options:** detect duplicates (with Q-10's ownership record) | document as a caller obligation
**Proposed:** decide with Q-10.
**Fault:** F-14
**Trigger:** step-3 checklist
**Status:** OPEN — human decision required

## Q-12: What happens to capacity when a caller never returns a connection?
**Question:** A connection that is neither Put nor Closed keeps its slot forever. Should the pool detect or reclaim lost connections (lease timeout), or is this the caller's obligation?
**Current behaviour:** the slot is lost for the pool's lifetime (channel.go:159); enough losses leave the pool at capacity and every Get waits forever (trace T-13).
**Cells:** UV-PUT-LOSS in the Open states (Released row → Q-06).
**Options:** document as a caller obligation | lease timeout with reclaim | diagnostics only (count of checked-out connections)
**Proposed:** document the obligation and expose the checked-out count for diagnostics.
**Fault:** F-12
**Trigger:** step-3 checklist
**Status:** OPEN — human decision required

## Q-13: Must expired idle connections be closed when they expire?
**Question:** "the timeout connection will be closed and discarded" (README.md:13, channel.go:31): is closing at the next Get enough, or must an expired idle connection be closed once its idle time passes?
**Current behaviour:** no timer; an expired connection stays open until a Get receives it (channel.go:116-119) or Release drains it. Executed: `as-is-tests.md` T14. Idle age counts from the last Put or from creation (channel.go:88, 190). Voided control verdict folded here: P-09a (README.md:13, scope no; Jev unclear, scope 0.05).
**Cells:** Open_IdleAvailable × I-IDLE-EXPIRE, Open_IdleFull × I-IDLE-EXPIRE, Open_Waiting_Stranded × I-IDLE-EXPIRE. Invariant SYS-15. Traces P-09a, T-15.
**Options:** lazy closing at Get (document) | background reaper at IdleTimeout granularity | close on Put/Get of any connection (sweep)
**Proposed:** document lazy closing; add a reaper only if remote resources must be freed promptly.
**Fault:** F-13
**Trigger:** doctrine mapping
**Part B:** Part B (blind): divergence on I-IDLE-EXPIRE folded here — the blind pass read lazy expiry as documented (leak-dependent).
**Status:** OPEN — human decision required

## Q-14: Must every connection handed out pass Ping, including handoffs to waiters?
**Question:** "invalid connection will be discarded" (README.md:14): Get pings connections taken from the idle store, but a connection handed directly to a waiter is not pinged. Should it be?
**Current behaviour:** the handoff path checks only expiry (channel.go:141-148); Put never pings (channel.go:167-198). Executed: `as-is-tests.md` T10.
**Cells:** UV-PUT-BROKEN in Open_AtCapacity_Waiting and Open_Waiting_Stranded; related E-PUT in those states. Invariant SYS-7. Trace T-10.
**Options:** ping on the waiter path too | ping on Put | document that only idle-store connections are checked
**Proposed:** ping on the waiter path (consistent with the idle path).
**Fault:** F-19
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

## Q-15: Is InitialCap an initial fill or a maintained minimum?
**Question:** The Config comment calls InitialCap "the minimum number of connections the pool holds" (channel.go:19); both READMEs call it the initial number (README.md:30, README_ZH_CN.md:30). Which is intended?
**Current behaviour:** filled once at construction (channel.go:82-89); never replenished. Executed: `as-is-tests.md` T15.
**Cells:** initial transition; invariants SYS-9 (holds), SYS-11 (violated under the "minimum" reading).
**Options:** initial fill only (fix the comment) | maintained minimum (replenish on Close/discard)
**Proposed:** initial fill only; correct the comment.
**Fault:** F-19
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

## Q-16: What number should Len report?
**Question:** "View the number of connections in the current connection pool" (README.md:58) and "the connections already in the pool" (channel.go:245): idle connections only, or all open connections?
**Current behaviour:** returns the idle count (channel.go:247); the tests assert the idle count (channel_rpc_test.go:69); Len takes the mutex and so blocks during a slow callback (T-08).
**Cells:** E-LEN in every state (DOC-7 → Open_IdleAvailable × E-LEN).
**Options:** idle count (document) | open count | both (two methods)
**Proposed:** idle count, documented as such.
**Fault:** F-03
**Trigger:** doctrine mapping
**Status:** OPEN — human decision required

## Q-17: Is fail-fast on Factory errors intended?
**Question:** A Factory error during Get is returned at once, unwrapped, without retry; during construction one Factory error releases the pool and fails `NewChannelPool`. Are both intended, and should a Factory error affect queued waiters?
**Current behaviour:** Get returns the error, open count unchanged (channel.go:155-157); construction releases and wraps the error (channel.go:84-86). Queued waiters are unaffected.
**Cells:** UV-FACTORY-ERR in Open_IdleAvailable, Open_IdleFull, Open_Empty, Open_Waiting_Stranded. Lint L-6.
**Options:** keep fail-fast (document) | retry with backoff inside the pool | construction tolerates partial fill
**Proposed:** keep fail-fast and document it.
**Fault:** F-12
**Trigger:** seam-contract sweep
**Status:** OPEN — human decision required

## Q-18: What must happen to Close-callback errors?
**Question:** The open count is decremented before the Close callback runs; its error is returned by Close and by an overflowing Put, but dropped on Get's discard paths and in Release. Is that the contract?
**Current behaviour:** as described (channel.go:211-212, channel.go:118, channel.go:241). Trace T-14.
**Cells:** UV-CLOSEFN-ERR in the Open states. Lint L-3.
**Options:** drop silently (document) | report through a hook or logger | return from Release
**Proposed:** document; optionally log on the discard paths.
**Fault:** F-03
**Trigger:** seam-contract sweep
**Status:** OPEN — human decision required

## Q-19: What must Get do when Factory returns a nil connection without an error?
**Question:** A `(nil, nil)` result is counted and returned; Put and Close reject nil, so the slot can never be released.
**Current behaviour:** open count incremented (channel.go:159); Put(nil) and Close(nil) return "connection is nil. rejecting" (channel.go:169, 204). Executed: `as-is-tests.md` T16.
**Cells:** UV-FACTORY-NILCONN in the Open states where Factory runs. Invariant SYS-2. Trace T-09.
**Options:** treat as a Factory error (do not count, return an error) | document NAT-5 as a Factory obligation
**Proposed:** treat as an error.
**Fault:** F-18
**Trigger:** step-3 checklist
**Part B:** Part B (blind): convergent-hole on UV-FACTORY-NILCONN.
**Status:** OPEN — human decision required

## Q-20: Which configurations are valid, and what do the edge values mean?
**Question:** `MaxCap == 0` is accepted (every Get waits forever, T-12); `MaxIdle == 0` makes every Put without a waiter close the connection; `IdleTimeout <= 0` disables expiry; a nil `*Config` panics in the constructor (channel.go:59). None of this is documented.
**Current behaviour:** as described (channel.go:59, 70, 115; G-01 witness MaxCap = 0). Executed: `as-is-tests.md` T11.
**Cells:** initial transition (G-01); Open_AtCapacity × E-GET for MaxCap = 0. NAT-6.
**Options:** reject MaxCap < 1 and nil config with errors | document the edge semantics
**Proposed:** reject MaxCap < 1 and a nil config; document IdleTimeout ≤ 0 = no expiry and MaxIdle = 0 = no idle pooling.
**Fault:** F-19
**Trigger:** step-1 extraction
**Status:** OPEN — human decision required

## Q-21: Must the pool protect a shared server against synchronised reconnects?
**Question:** N instances started together expire their initial connections together and reconnect together; Factory errors return at once with no backoff, so callers' retries synchronise. Is any decorrelation (jitter on idle timestamps, backoff on Factory errors) the pool's job?
**Current behaviour:** no backoff, no jitter (channel.go:88, 154-157). Multi-instance probes M-01 … M-03. Lint L-8.
**Cells:** none directly (aggregate behaviour across instances); related UV-FACTORY-ERR, I-IDLE-EXPIRE.
**Options:** leave to callers (document) | jitter idle timestamps | backoff after Factory errors
**Proposed:** leave to callers and document; reconsider if Q-02 adds a wait timeout.
**Fault:** F-10
**Trigger:** multi-instance probes
**Status:** OPEN — human decision required

## Q-22: What should the exported Ping method do when no Ping function is configured?
**Question:** `(*channelPool).Ping` is exported (reachable by a type assertion, not in the `Pool` interface) and calls `c.ping(conn)` without a nil check.
**Current behaviour:** nil-function panic when Ping is not configured or after Release (channel.go:220). Executed: `as-is-tests.md` T17.
**Cells:** none (method outside the `Pool` interface; API-contract issue, PA-20).
**Options:** return nil (treat as valid) | return an error | unexport the method
**Proposed:** return nil, matching Get's "no ping, no check" rule (channel.go:122).
**Fault:** F-03
**Trigger:** step-1 extraction
**Status:** OPEN — human decision required (Flash's channel.go draft raised it)

## Q-23: Does "the pool is full" in Put mean the idle store or MaxCap? (voided control verdict T-02)
**Question:** The comment at channel.go:195 ("连接池已满，直接关闭该连接": "the pool is full; close the connection directly") justifies closing a returned connection. As-is, "full" is the idle store (MaxIdle), not MaxCap: a Put closes the connection even when the open count is below MaxCap. Is that the intended meaning?
**Current behaviour:** Put closes when the idle channel is full (channel.go:189-196), regardless of MaxCap. Executed: `as-is-tests.md` T18.
**Why this is a question:** my scope line for control trace T-02 said yes; Jev answered `supported` with scope probability 0.30 (`routing/jev-order-channel.json`, check CT-B), below the 0.5 cut-off of routing rule 4, so the ordering is not source-backed and the control verdict is void (rule 5). This question cites both.
**Cells:** Open_IdleFull × E-PUT (DOC-20).
**Options:** "full" = idle store full (current; document it) | "full" = MaxCap reached
**Proposed:** idle store full, documented — it matches MaxIdle's meaning (DOC-10).
**Fault:** F-19
**Trigger:** jev check
**Status:** OPEN — human decision required

## Q-24: What does "discard" mean for a connection that fails Ping? (voided control verdict T-03)
**Question:** The comment at channel.go:122 ("判断是否失效，失效则丢弃": "check whether it is invalid; if so, discard it") justifies the discard on a failed Ping. As-is, discarding means: call the user's Close callback, decrement the open count, and take the next connection (channel.go:124-126). Is that the intended meaning, and does the rule cover every connection Get hands out (see Q-14)?
**Current behaviour:** as described; the handoff path has no Ping (channel.go:141-148).
**Why this is a question:** my scope line for control trace T-03 said yes; Jev answered `supported` with scope probability 0.31 (`routing/jev-order-channel.json`, check CT-C), below 0.5, so the ordering is not source-backed and the control verdict is void (routing rules 4 and 5).
**Cells:** Open_IdleAvailable × E-GET (DOC-17; G-03).
**Options:** discard = close via the Close callback and retry (current; document) | discard = drop without closing
**Proposed:** close and retry (current), documented.
**Fault:** F-19
**Trigger:** jev check
**Status:** OPEN — human decision required

## Q-25: Is an idle connection whose age equals IdleTimeout expired?
**Question:** At exactly `age == IdleTimeout`, should Get discard the connection or hand it out?
**Current behaviour:** handed out: the test is `t.Add(timeout).Before(now)`, strict (channel.go:116, channel.go:142); G-02 boundary probe: age = IdleTimeout → keep, IdleTimeout + 1 → discard (`guard-results.txt`).
**Why this is a question:** the blind Part B expects discard at age ≥ IdleTimeout (row E-GET); README.md:13 ("the timeout connection will be closed and discarded") and channel.go:31 ("超过该事件则将失效": "beyond this time … becomes invalid") do not settle the equality case.
**Cells:** Open_IdleAvailable × E-GET (G-02 boundary), Open_AtCapacity_Waiting × E-PUT (G-05 boundary on the handoff path).
**Options:** strictly greater expires (current; "beyond") | greater-or-equal expires
**Proposed:** keep strict ("超过" = "exceed"), document it.
**Fault:** F-13
**Trigger:** part-B diff
**Status:** OPEN — human decision required

## Summary count

states 7 / events incl. undesired variants 22 (6 base + 16 undesired) / interaction pairs 9 (18 orderings) / matrix cells 154 / UNSPECIFIED 1 / accidental ignores 22 / guard groups proven 8 / guard violations 0 / not-formalizable 1 / findings 25 / open questions 25
