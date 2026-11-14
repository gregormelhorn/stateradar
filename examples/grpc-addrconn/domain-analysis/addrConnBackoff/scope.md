# Local backoff cleanup evaluation scope

This is a bounded regression/mutation slice of the pinned real addrConn, not a
new complete pilot of its 182 historical cells. The historical archive is never
rewritten. `resolution.json` answers its 16 questions for this evaluation under
the owner's explicit delegation; all broad implementation work stays pending.
No broad to-be model is promoted by this slice.

Precondition: one addrConn has exhausted its address list after a controlled
failed dial, is waiting on its backoff timer, and has no live transport. Its
actual parent ClientConn remains alive. Timer delivery, ResetConnectBackoff,
resolver updates, live transports, health checks and publication races are
excluded from this slice, not claimed covered by it.

States enumerate the reachable projected combinations at the controlled seam:
BackoffWaiting = TransientFailure + active worker + live timer;
ShutdownPending = Shutdown + active worker, cancellation initiated;
ShutdownStopped = Shutdown + completed worker + stopped timer. The stopped
state is terminal within this slice. A mutated retained timer/worker violates
the projection/invariant; it is not a new accepted state. A scheduling barrier
holds the worker immediately before its real select, so Pending is observable.

TearDown invokes the real local method, observes its immediate state, then runs
its mandatory resource-release follow-up trace. ObserveWorker inspects Waiting
without delivering a wake, or resumes and joins a pending worker. Repeating
both operations in Shutdown rows tests their projected idempotence. The suite
consumes the matrix targets from analysis.json; resource obligations are
independent assertions, not copied implementation expressions.

SYS-1: local shutdown eventually releases its backoff worker and timer, while
parent context remains live (DR-011; observed-in-code clientconn.go:1337
("ac.cancel()"), clientconn.go:1140 ("case <-acctx.Done():")).
SYS-2: repeated local shutdown cannot restart the worker (DR-009/011).
NAT-1: no timer/reset/parent-cancel input races this ordering. The backoff
Strategy seam permits a selected waiting duration (internal/backoff/backoff.go:
Backoff(retries)); the timer replacement controls time without changing the
branch's operations. Watchdogs bound tests, not the domain's completion latency.

P-01a: Observe Waiting; TearDown; join worker and observe stopped timer.
P-01b: TearDown; Observe Pending to completion; repeat observation.
Cited text contemplates this ordering: yes — local cancellation followed by
backoff select cancellation, with no live transport or parent cancellation.
These traces use observed code plus the evaluation decision, not the broad
channel connectivity requirement or the disputed historical NAT-5.

The upstream source manifest pins grpc-go, not the pack harness. Harness and
model revisions are retained in this repository's tested commits/evidence.
This fixture's model and decisions do not claim that grpc-go upstream adopted
them or that all 16 implementation obligations have been completed.
