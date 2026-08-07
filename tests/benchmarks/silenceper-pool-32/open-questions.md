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

Put() after Release: conns is nil so Put calls c.Close(conn) at
channel.go:190. Close() then checks c.close==nil and is a silent no-op —
the connection is leaked, openingConns is not decremented (already stale).

## Q-05: FactoryFail handling (F-01)

Factory failure during Get() at channel.go:155 returns error to caller
without decrementing openingConns or notifying waiters.
