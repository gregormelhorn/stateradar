# silenceper/pool — Open Questions

## Q-01: Release/connReqs goroutine leak (F-07, F-20)

**Status:** ANSWERED — [DR-001](decisions/DR-001.yaml); to-be model and test generation pending.

CRITICAL: Release() at channel.go:215 sets conns=nil, closes idle conns
channel, iterates idle conns — but NEVER closes connReqs waiter channels.
Goroutines blocked in Get() on <-req at channel.go:139 hang forever after
pool termination. Pool terminal does not synchronize with Waiter lifecycle
(PA-21).

Fix: close each connReqs channel so waiters receive zero value and return
ErrMaxActiveConnReached.

**Accepted decision:** `Release()` resolves all queued `Get()` waiters with
`ErrMaxActiveConnReached`; it must not leave them blocked. This decision applies
to terminal shutdown only and does not decide a capacity-exhaustion timeout
policy.

## Q-02: Put integrity (F-12, F-14, F-17)

**Status:** ANSWERED — [DR-002](decisions/DR-002.yaml); to-be model and test generation pending.

Lost, duplicate, and foreign `Put()` inputs are caller-contract assumptions.
A caller must return or close exactly one genuine borrowed connection exactly
once. The pool does not add lease identity or ownership tracking to recover a
lost connection or detect a duplicate/foreign return.

## Q-03: Put after Release (F-04)

**Status:** ANSWERED — [DR-003](decisions/DR-003.yaml); to-be model and test generation pending.

Put() after Release: conns is nil so Put calls c.Close(conn) at
channel.go:190. Close() then checks c.close==nil and is a silent no-op —
the connection is leaked, openingConns is not decremented (already stale).

**Accepted decision:** this is a safe terminal no-op. `Put()` after `Release()`
returns successfully without a second physical close; callers return or close all
borrowed connections before releasing the pool.

## Q-04: Waiter-path Ping validation (F-03)

**Status:** ANSWERED — [DR-004](decisions/DR-004.yaml); to-be model and test generation pending.

When `Ping` is configured, every connection must pass it before `Get()` returns
that connection, including one delivered to a queued waiter. On Ping failure,
the pool discards/closes the connection and retries acquisition; it does not
return the failed connection or merely pass the Ping error through.

## Q-05: FactoryFail handling (F-01)

**Status:** ANSWERED — [DR-005](decisions/DR-005.yaml); to-be model and test generation pending.

The ordinary `Get()` path increments `openingConns` only after `Factory()`
succeeds. A Factory error returns to the caller without consuming capacity.
Initial construction failure releases partial state and aborts pool creation;
Factory is not invoked from the at-capacity waiter branch, so no special waiter
notification is required.

## Q-06: Close ownership and `openingConns` (F-05, F-14)

**Status:** ANSWERED — [DR-006](decisions/DR-006.yaml); to-be model and test generation pending.

`openingConns >= 0` is a system invariant under the DR-002/DR-006 valid-caller
contract. A caller closes only a genuine borrowed connection once and does not
both `Put()` and `Close()` the same borrow. The pool does not add duplicate-close
tracking, foreign-connection detection, or counter clamping.
