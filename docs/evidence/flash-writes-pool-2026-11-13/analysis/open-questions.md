# channelPool — open questions (Step 7)

Every question is OPEN: only the human owner can decide. Proposals are `proposed` and carry no authority. ODC fields: Fault = fault class (formats/rules.toml), Trigger = detector.

## Q-01: Should Release wake or fail the callers blocked in Get, and what should Put do for them afterwards?

**Fault:** F-20

**Trigger:** step-4 matrix walk

Question: Should Release wake or fail the callers blocked in Get, and what should Put do for them afterwards?

Current behaviour: Release nils conns, factory, ping and close (channel.go:225-231) and closes the idle channel, but never touches connReqs; a caller blocked at channel.go:137 stays blocked, and a later Put in the Closed state returns before reaching connReqs (channel.go:174-176). Also a Get that registered as waiter after Release (it passed the closed check earlier, P-02b) can block in the closed pool. (observed-in-code; as-is test TestAsIs_Release_DoesNotWakeWaiter, observed-in-tests)

Options: wake waiters with ErrClosed | leave as is (callers must not call Get concurrently with Release) | wake waiters with ErrMaxActiveConnReached

Proposed: wake waiters with ErrClosed (proposed)

**Status:** OPEN — human decision required

## Q-02: What is the intended bound on waiting for capacity: timeout, cancellation, or none?

**Fault:** F-19

**Trigger:** step-5 lint

Question: What is the intended bound on waiting for capacity: timeout, cancellation, or none?

Current behaviour: Get blocks at `ret, ok := <-req` with no timeout or cancellation (channel.go:137); the field waitTimeOut is declared and never used (channel.go:46); the branch for a closed req returns ErrMaxActiveConnReached (channel.go:139) but no code closes any req, so that branch is unreachable. README.md:15 says only that connection waiting is supported. (observed-in-code, explicit-requirement)

Options: unbounded wait | configurable wait timeout using waitTimeOut | fail fast with ErrMaxActiveConnReached

Part-B fold: the blind pass proposed `defer (queued)` for Get in the Open_Waiting states (README.md:15); the matrix labels those cells `handle`/`transition` because the request is queued in connReqs but has no bound, no cancellation and no serve rule. Which label is right depends on this question.

Proposed: configurable wait timeout (proposed)

**Status:** OPEN — human decision required

## Q-03: Should capacity freed by Close (or by discarding an expired or invalid connection) serve a queued waiter?

**Fault:** F-07

**Trigger:** step-4 matrix walk

Question: Should capacity freed by Close (or by discarding an expired or invalid connection) serve a queued waiter?

Current behaviour: Close and the discard paths in Get lower openingConns (channel.go:211, 118, 125, 144) and do not look at connReqs; only Put serves waiters (channel.go:179-185). A new Get meanwhile creates a connection and passes the waiters (channel.go:133, 154). State Open_Waiting_BelowCap exists for this reason. (observed-in-code; TestAsIs_Close_DoesNotServeWaiter)

Part-B fold: pair P-03b (Close, then Get at capacity): the blind pass finds no requirement on whether freed capacity lets a later Get create a connection; the matrix control trace rests on code only.

Options: Close/discard creates or signals for a waiter | leave as is | reject new Gets while waiters exist (FIFO)

Proposed: signal a waiter when capacity frees (proposed)

**Status:** OPEN — human decision required

## Q-04: May a Get take an idle connection ahead of queued waiters, and may a Get register as waiter although an idle connection exists?

**Fault:** F-16

**Trigger:** adversarial trace

Question: May a Get take an idle connection ahead of queued waiters, and may a Get register as waiter although an idle connection exists?

Current behaviour: Get's select at channel.go:109 and its lock at channel.go:131 are separate critical sections; Put can store an idle connection between them (P-04a), after which the Get queues although the channel is not empty. A later Get takes the idle connection ahead of the queued waiters (channel.go:110). State Open_Waiting_IdleAvailable. (observed-in-code, inferred from interleaving)

Options: re-check the idle channel under the lock before queueing | leave as is | serve waiters before any Get

Proposed: re-check under the lock (proposed)

**Status:** OPEN — human decision required

## Q-05: What must happen to a connection passed to Put or Close after Release, and to a borrowed connection when Release is called?

**Fault:** F-09

**Trigger:** step-4 matrix walk

Question: What must happen to a connection passed to Put or Close after Release, and to a borrowed connection when Release is called?

Current behaviour: After Release, Put calls Close (channel.go:174-176), which returns nil without calling the close callback or changing openingConns because c.close is nil (channel.go:208-210). The connection is neither stored nor closed. Release itself touches only idle entries (channel.go:238-241). (observed-in-code; TestAsIs_Put_AfterRelease_NoClose). README.md:55 says Release is for when resources must be destroyed.

Options: close the connection with the saved close callback | return an error (ErrClosed) | leave as is (leak)

Proposed: close it and return ErrClosed (proposed)

**Status:** OPEN — human decision required

## Q-06: What should Ping do when no ping function is configured, or after Release?

**Fault:** F-01

**Trigger:** step-4 matrix walk

Question: What should Ping do when no ping function is configured, or after Release?

Current behaviour: Ping calls c.ping(conn) with no nil check (channel.go:216-221). c.ping is nil when Config.Ping is unset (channel.go:78) and after Release (channel.go:229): the call panics. Get guards with `c.ping != nil` (channel.go:123). Ping is not in the Pool interface (pool.go:11-21). (observed-in-code)

Options: return nil | return an error | panic (document)

Proposed: return an error (proposed)

**Status:** OPEN — human decision required

## Q-07: Is Get concurrent with Release supported, given the unlocked read of the ping field?

**Fault:** F-16

**Trigger:** adversarial trace

Question: Is Get concurrent with Release supported, given the unlocked read of the ping field?

Current behaviour: Get reads c.ping without c.mu (channel.go:123) and Ping reads it again (channel.go:220) while Release writes it under the lock (channel.go:229): a data race, and a nil function call is reachable if Release runs between the check and the call (pair P-06a). Get also keeps selecting on its pre-Release channel snapshot (channel.go:104, 110). (observed-in-code; Go memory model is NAT-06; the as-is test did not reproduce a panic in 200 rounds)

Options: supported: read ping under the lock | unsupported: document that Release must follow all Gets

Proposed: read under the lock (proposed)

**Status:** OPEN — human decision required

## Q-08: May the Factory and Close callbacks call back into the pool, and may they block?

**Fault:** F-11

**Trigger:** step-3 lock-discipline annotation

Question: May the Factory and Close callbacks call back into the pool, and may they block?

Current behaviour: Factory runs under c.mu in Get (channel.go:154) and the Close callback runs under c.mu in Close (channel.go:212). A callback that calls Get, Put, Close, Release or Len blocks forever; a slow callback blocks every call. The Config comments (channel.go:25-30) state no contract. (observed-in-code; no callee contract exists in the repository)

Options: document no-reentrancy and no-blocking | call callbacks outside the lock | leave as is

Proposed: call the callbacks outside the lock (proposed)

**Status:** OPEN — human decision required

## Q-09: What should Get do when the Factory returns a nil connection without error?

**Fault:** F-18

**Trigger:** seam-contract sweep

Question: What should Get do when the Factory returns a nil connection without error?

Current behaviour: Get increments openingConns and returns (nil, nil) (channel.go:154-161); Put(nil) is rejected (channel.go:168) so the caller cannot return it. NewChannelPool stores a nil conn as idle (channel.go:88). (observed-in-code)

Options: treat as error | accept | document

Proposed: treat as error (proposed)

**Status:** OPEN — human decision required

## Q-10: What should the pool do with errors from the Close callback?

**Fault:** F-03

**Trigger:** seam-contract sweep

Question: What should the pool do with errors from the Close callback?

Current behaviour: Close lowers openingConns before it calls the callback and returns the callback's error (channel.go:211-212); Get's discard paths ignore the result (channel.go:118, 125, 144) and so does Release (channel.go:241); Put returns it (channel.go:196). (observed-in-code)

Options: count only after success | ignore everywhere | surface everywhere

Proposed: document the current mixed behaviour (proposed)

**Status:** OPEN — human decision required

## Q-11: What should happen when the same connection is passed to Put twice?

**Fault:** F-14

**Trigger:** step-3 checklist

Question: What should happen when the same connection is passed to Put twice?

Current behaviour: There is no borrowed-connection record; the second Put stores the same connection again (channel.go:190) or hands it to a waiter (channel.go:183), so two Gets can receive one connection. (observed-in-code; NAT-02 excludes it)

Options: detect and reject | ignore | document NAT-02

Proposed: detect and reject (proposed)

**Status:** OPEN — human decision required

## Q-12: What should happen when the same connection is passed to Close twice?

**Fault:** F-08

**Trigger:** step-3 checklist

Question: What should happen when the same connection is passed to Close twice?

Current behaviour: Each Close lowers openingConns and calls the callback again (channel.go:211-212); the counter can fall below the number of live connections or below zero, letting more than MaxCap connections exist (TestAsIs_Close_Twice_ExceedsMaxCap). (observed-in-code)

Options: detect and reject | ignore | document NAT-02

Proposed: detect and reject (proposed)

**Status:** OPEN — human decision required

## Q-13: What should Put do with a connection that this pool did not create?

**Fault:** F-17

**Trigger:** step-3 checklist

Question: What should Put do with a connection that this pool did not create?

Current behaviour: Put accepts any non-nil value (channel.go:167-198): it is stored or handed on without being counted in openingConns, so the pool can hold or lend more than MaxCap connections, and a full channel closes it and lowers the counter for a connection never counted. (observed-in-code)

Options: reject foreign values | accept | document NAT-02

Proposed: document NAT-02 (proposed)

**Status:** OPEN — human decision required

## Q-14: What should Close do with a connection that this pool did not create?

**Fault:** F-17

**Trigger:** step-3 checklist

Question: What should Close do with a connection that this pool did not create?

Current behaviour: Close lowers openingConns and calls the close callback for any non-nil value (channel.go:206-212). (observed-in-code)

Options: reject foreign values | accept | document NAT-02

Proposed: document NAT-02 (proposed)

**Status:** OPEN — human decision required

## Q-15: Should a connection handed to a waiter be validated (ping, idle age) like an idle one?

**Fault:** F-01

**Trigger:** step-4 matrix walk

Question: Should a connection handed to a waiter be validated (ping, idle age) like an idle one?

Current behaviour: The waiter path checks only the idle timeout (channel.go:141-147) against a timestamp that Put wrote at hand-over (channel.go:184), and never calls the ping function; the idle path checks both (channel.go:115-128). README.md:14 says invalid connections are discarded. (observed-in-code, explicit-requirement)

Options: ping on the waiter path too | leave as is | ping in Put

Proposed: ping on the waiter path (proposed)

**Status:** OPEN — human decision required

## Q-16: Is lazy idle expiry (only when Get meets the connection) intended, and should expired connections count in Len and in the capacity?

**Fault:** F-13

**Trigger:** step-5 lint

Question: Is lazy idle expiry (only when Get meets the connection) intended, and should expired connections count in Len and in the capacity?

Current behaviour: IdleTimeout is evaluated only inside Get (channel.go:115-121, 141-147); there is no timer or reaper; expired connections stay in the channel, count in Len (channel.go:247) and hold capacity (openingConns) until a Get discards them. (observed-in-code) README.md:13 says connections exceeding the idle time are closed and discarded.

Options: lazy expiry | background reaper | expiry also at Put/Len

Proposed: lazy expiry documented (proposed)

**Status:** OPEN — human decision required

## Q-17: Are the degenerate configurations MaxCap = 0 and MaxIdle = 0 valid?

**Fault:** F-01

**Trigger:** z3 invariant check

Question: Are the degenerate configurations MaxCap = 0 and MaxIdle = 0 valid?

Current behaviour: The validation channel.go:59 accepts MaxCap = 0 (with MaxIdle = 0, InitialCap = 0): every Get then waits forever (channel.go:133-137, no Put can arrive). MaxIdle = 0 makes an unbuffered idle channel, so every Put closes its connection (channel.go:189-196). Guard proof G-04 shows such a configuration satisfies the validation. (observed-in-code, z3)

Options: require MaxCap >= 1 | accept | document

Proposed: require MaxCap >= 1 (proposed)

**Status:** OPEN — human decision required

## Q-18: What does Len count?

**Fault:** F-19

**Trigger:** doctrine mapping

Question: What does Len count?

Current behaviour: Len returns len(conns): idle entries only, expired ones included (channel.go:247). README.md:58 says Len is the number of connections in the pool; README_ZH_CN.md:57 is equally unspecific. (observed-in-code, explicit-requirement)

Part-B fold: Len after Release (returns 0 for a nil channel, channel.go:247) is also unspecified.

Options: idle only | open connections (openingConns) | both

Proposed: idle only, documented (proposed)

**Status:** OPEN — human decision required

## Q-19: Is all-or-nothing the intended behaviour when the factory fails while the pool is pre-filled?

**Fault:** F-12

**Trigger:** step-5 lint

Question: Is all-or-nothing the intended behaviour when the factory fails while the pool is pre-filled?

Current behaviour: NewChannelPool presets openingConns = InitialCap (channel.go:75), calls Release on the first factory error and returns the error (channel.go:83-87); no retry. README.md is silent. (observed-in-code)

Options: all-or-nothing | partial pool | retry

Proposed: all-or-nothing, documented (proposed)

**Status:** OPEN — human decision required

## Q-20: Is the pool documented as safe for concurrent use, and which caller obligations (return each connection once, do not use after return, no calls after Release) apply?

**Fault:** F-19

**Trigger:** doctrine mapping

Question: Is the pool documented as safe for concurrent use, and which caller obligations (return each connection once, do not use after return, no calls after Release) apply?

Current behaviour: The code locks (channel.go:41, 97, 131, 172, 206, 226), tests use goroutines (channel_rpc_test.go:75-86), README.md and README_ZH_CN.md state nothing. NAT-02, NAT-03, NAT-08 are assumptions drawn from the code only. (observed-in-code, explicit-requirement absence)

Options: document goroutine-safety and the obligations | leave undocumented

Proposed: document (proposed)

**Status:** OPEN — human decision required

## Q-21: At MaxCap, must Get wait (code, README) or return ErrMaxActiveConnReached (test)?

**Fault:** F-19

**Trigger:** step-2 test replay

Question: At MaxCap, must Get wait (code, README) or return ErrMaxActiveConnReached (test)?

Current behaviour: TestPool_Get expects ErrMaxActiveConnReached from the Get after MaxCap connections are borrowed (channel_rpc_test.go:93-95); the code waits (channel.go:133-137) and the test hangs (as-is run: timeout after 60 s, blocked at channel.go:137). README.md:15 says waiting is supported. (observed-in-tests vs observed-in-code vs explicit-requirement)

Options: wait (README, code) | fail fast (test) | both, selected by configuration

Proposed: wait; update the test (proposed)

**Status:** OPEN — human decision required

## Q-22: Do N pools sharing one server reconnect in step, and is a factory failure retried or backed off?

**Fault:** F-10

**Trigger:** multi-instance probes

Question: Do N pools sharing one server reconnect in step, and is a factory failure retried or backed off?

Current behaviour: NewChannelPool opens InitialCap connections immediately (channel.go:82-89); idle connections created together expire together (channel.go:115-121) and are replaced one per Get with no jitter; Get returns a factory error at once and the pool never retries or backs off (channel.go:155-158). NAT-SYS-01. (observed-in-code, inferred for the aggregate)

Options: add jitter and backoff | document | leave as is

Proposed: document; callers own backoff (proposed)

**Status:** OPEN — human decision required

## Q-23: Is InitialCap a floor or only the initial fill?

**Fault:** F-19

**Trigger:** step-1 extraction

Question: Is InitialCap a floor or only the initial fill?

Current behaviour: The Config comment says InitialCap is the minimum number of connections in the pool (channel.go:19); the code fills once at construction and never replenishes (channel.go:82-89), so idle count can drop below InitialCap. README_ZH_CN.md:30 calls it the initial number. (observed-in-code, explicit-requirement)

Options: initial fill only (fix the comment) | maintain a floor

Proposed: fix the comment (proposed)

**Status:** OPEN — human decision required

## Q-24: Which observable orderings are part of the intended contract (reuse after Put, discard at Get time, waiter served by Put, Release closes idle connections, ErrClosed after Release)?

**Fault:** F-19

**Trigger:** adversarial trace

Question: Which observable orderings are part of the intended contract?

Current behaviour: the README states features and usage steps (README.md:13, 15, 46, 52, 55) but no ordering; the four orderings of traces T-01..T-04 were each checked with Jev (runs/jev-batch-control.json): all four `unclear` with ordering scope probability 0.04, 0.06, 0.05, 0.14, and the agent wrote "contemplates this ordering: no" for each from the quoted text, so none is a requirement-backed control verdict. Get after Release returning ErrClosed (channel.go:106) rests on a code comment only (pool.go:6). (observed-in-code, explicit-requirement absence)

Part-B folds: (1) nil rejection by Put/Close (UV-Conn-nil) rests on code only (channel.go:168-170, 204-206); (2) pair P-01a: Release closing a just-returned connection; (3) pair P-04b: an idle connection preferred over creating a new one; (4) a second Release being a no-op (channel.go:234) is documented only by the code guard.

Options: adopt each ordering as contract | leave undocumented | adopt some

Proposed: adopt all five as contract (proposed)

**Status:** OPEN — human decision required
