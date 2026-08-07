# CONVERGENCE — Device Connection

**Component:** `examples/device-connection/device_connection.py`
**Method:** Two independent Part-A pilot runs on the same component.
**Status:** Baseline recorded 2026-08-07, pack v1.37 (02-pilot v1.15).
Both runs fresh sessions, independence enforced (no access to the
reference analysis, the other run, tests/, or the web); both matrices
checker-green (check_matrix, guard proofs via `tools/guard_proofs.py`,
dsc_check incl. doctrine mapping).

## Protocol

1. Run `02-pilot.md` on `examples/device-connection/` in a fresh session.
2. Run `02-pilot.md` on the same component in a second, independent
   fresh session.
3. Diff the two disposition matrices cell by cell.
4. Record the divergence count and rate below.

## Expected state space

- DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED
- FAILED may or may not be modeled as terminal (R-05 says permanent,
  implementation has backdoor via disconnect)

## Run 1

**Date:** 2026-08-07
**Session:** fresh subagent, resumed once after a transient API drop
**States:** 8 — Disconnected_Idle, Disconnected_RetriesExhausted,
Connecting_Attempting, Connecting_RetriesExhausted, Connected,
Reconnecting_BackingOff, Reconnecting_Attempting, Failed
**Matrix cells:** 96 (8 × 12; 7 base + 5 UV events)
**UNSPECIFIED cells:** 0
**Ignore (accidental) cells:** 3 (external task cancellation, → Q-05)
**Questions:** 11 · **Guard groups:** 4 proven

## Run 2

**Date:** 2026-08-07
**Session:** fresh subagent, resumed once after a transient API drop
**States:** 7 — DISCONNECTED, Connecting_AttemptInFlight,
Connecting_NoAttempt, CONNECTED, Reconnecting_Backoff,
Reconnecting_AttemptInFlight, FAILED
**Matrix cells:** 70 (7 × 10; 7 base + 3 UV events)
**UNSPECIFIED cells:** 7 (double-loop/orphan regime, → Q-02)
**Ignore (accidental) cells:** 0
**Questions:** 8 · **Guard groups:** 2 proven

## Divergence

Semantic state alignment: 7 of Run 1's 8 states map 1:1 onto Run 2's 7
(PA-17 made the mapping mechanical apart from ALLCAPS-vs-PascalCase
spelling of the enum states); Run 1's extra state is
`Disconnected_RetriesExhausted`. Base events align 1:1 (naming only:
`attempt.refused`/`attempt.failed`, `uptime.expired`/`uptime.elapsed`).

**Aligned base grid (7 × 7 = 49 cells), mechanical diff:**

| Metric | Run 1 | Run 2 | Match |
|---|---|---|---|
| States | 8 | 7 | 7 aligned |
| Base events | 7 | 7 | 7 aligned |
| UV events | 5 | 3 | not alignable (different slicing) |
| Aligned base cells | 49 | 49 | 47 convergent, 2 divergent |
| Holes | 3 accidental | 7 UNSPECIFIED | different axes (see notes) |

**Cell divergence rate (aligned base grid): 2/49 = 4.1 %** — and both
divergent cells share one root: Run 1's extra state (teardown targets
`Disconnected_RetriesExhausted` where Run 2 targets `DISCONNECTED`).
One granularity decision, not two behavioural disagreements — and it
encodes the very finding both runs made independently (retry budget
survives disconnect).

**Finding-level convergence: 9 of 11 distinct findings found by both
runs (82 %).** Both found: double-loop spawn, stale-delivery
corruption, exhausted-budget CONNECTING trap, FAILED backdoor
(the protocol's predicted divergence source — it converged), dead
min_uptime code, budget-survives-disconnect, max_retries off-by-one,
synchronized reset + capped jitter, missing connection-loss
detection. Unique to Run 1: external task cancellation (Q-05),
disconnect-idempotence scope gap (Q-11). Unique to Run 2: none. No
contradictory findings — divergence was purely additive.

## Notes

- The predicted FAILED-terminality divergence did **not** occur: both
  runs modeled the disconnect backdoor identically and raised it as a
  question (R1 Q-04 / R2 Q-03).
- Run-to-run variance concentrates in **undesired-variant slicing**
  (5 vs 3 UV columns, different axes) and hence in where the holes
  sit: Run 1 holes on external cancellation, Run 2 holes on the
  double-loop regime — each run *found* the other's hole topic but
  carried it as a question rather than a hole. UV derivation is the
  method's softest joint; the roadmap's ensemble-convergence entry
  (#5) targets exactly this: intersection = confidence, symmetric
  difference = automatic Q candidates.
- The alignment + diff performed here by hand-written script is the
  natural seed for that ensemble tooling.
