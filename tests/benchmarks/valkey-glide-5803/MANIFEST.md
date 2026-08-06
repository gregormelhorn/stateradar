# valkey-glide — Inflight Permit Lifecycle

**Issue:** [#5803](https://github.com/valkey-io/valkey-glide/issues/5803)
**Commit:** v2.2.7
**Date:** 2026-08-06
**Oracle:** Confirmed — primary finding matched exactly.
**Defect class:** Caller terminal, resource ownership remains active (PA-21) — F-07 lifecycle coupling

## Primary finding

**Missing transition:** `CallerTimedOut → PermitReleased`

The `release_permit` event in `CallerTimedOut` state was `UNSPECIFIED`.
Requirement 3 states: "A request that times out releases its caller-facing
capacity immediately." The code released only after `send_command` returned,
which was after the internal Redis request completed — potentially long
after the timeout.

**Oracle match:** The issue describes "requests retain shared in-flight
capacity after the user-facing timeout has already fired." StateRadar
identified the exact missing transition from six neutral requirements.

## Requirements (Part B input)

1. A request acquires one unit of in-flight capacity before dispatch.
2. A completed request releases its capacity.
3. A request that times out from the caller's perspective releases its caller-facing capacity immediately.
4. Internal cleanup may continue after the caller receives a timeout.
5. A stalled request to one cluster node must not exhaust capacity for unrelated healthy nodes.
6. Releasing capacity more than once must have no additional effect.

## StateRadar output

- **Matrix cell:** `(CallerTimedOut, release_permit) = UNSPECIFIED`
- **Invariant violations:** INV-02 (bounded closing), INV-04 (closure observable without peer)
- **Root lifecycle violation:** Caller lifecycle terminal did not trigger capacity lifecycle release.
