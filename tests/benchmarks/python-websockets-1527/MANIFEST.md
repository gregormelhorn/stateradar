# python-websockets — Keepalive Lifecycle

**Issue:** [#1527](https://github.com/python-websockets/websockets/issues/1527)
**Commit:** `4d229bf9f583d593aa103287aee0a77c9fbc3a79` (v13.1)
**Date:** 2026-08-06
**Oracle:** Confirmed — primary finding matched exactly.
**Defect class:** Local deadline expires, caller notification remains blocked (PA-21)

## Primary finding

**Missing transition:** `CloseDeadlineExpired → ClosureObservable`

The code at `send_context.go:863-872` called `close_transport()` after the
`close_timeout` expired, but then re-entered the wait for `connection_lost_waiter`.
The close_timeout forced transport closure but did not force caller-visible
termination. If `connection_lost()` was never delivered (stalled transport),
callers blocked indefinitely.

**Oracle match:** The issue describes "server never raises a
connectionclosederror... until client reconnects." The debug logs show
"connection is CLOSING" at 19:55 and "connection is CLOSED" only at 26:55 —
exactly the 7-minute gap between `close_transport()` and `connection_lost()`.

## Requirements (Part B input)

R-01 through R-12, including:
- R-07: `close_timeout` bounds the time spent completing the closing handshake.
- R-11: Caller-facing operations must eventually observe abnormal closure
  within the configured shutdown bound.

## StateRadar output

- **Matrix cell:** `(ClosurePending, EV-11 CloseDeadlineExpired) = UNSPECIFIED`
- **Invariant violations:** INV-02, INV-03, INV-04, INV-05, INV-08
- **Root lifecycle violation:** Close deadline expiry did not synchronize with caller notification.
- **Blind diff:** Part B derived the same invariant from requirements alone.
- **Proposed test:** Independently converged on metric-based deterministic test design.
