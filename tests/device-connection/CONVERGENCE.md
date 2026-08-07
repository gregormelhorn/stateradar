# CONVERGENCE — Device Connection

**Component:** `examples/device-connection/device_connection.py`
**Method:** Two independent Part-A pilot runs on the same component.
**Status:** Baseline recorded 2026-08-07, updated 2026-08-07 (v1.38 fixup).
Both runs fresh sessions, independence enforced; both matrices
checker-green.

## Protocol (automated via tools/ensemble_convergence.py)

1. Run `02-pilot.md` on `examples/device-connection/` in a fresh session.
2. Run `02-pilot.md` on the same component in a second, independent
   fresh session.
3. Generate `analysis.json` from each run.
4. Run `python3 tools/ensemble_convergence.py run1/analysis.json run2/analysis.json -o merged.json --report convergence-report.md`.
5. The tool aligns states and events, diffs cells, marks divergent
   cells `UNSPECIFIED → Q`, and writes a convergence report.
6. Exit code non-zero = divergent cells found = human review needed.

## Expected state space

- DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED
- FAILED may or may not be modeled as terminal (R-05 says permanent,
  implementation has backdoor via disconnect)

## Run 1

**Date:** 2026-08-07
**Session:** fresh subagent
**States:** 6 — Disconnected, Disconnected_RetriesExhausted,
Connecting, Connected, Reconnecting, Failed
**Events:** 10 (4 base, 3 timer/internal, 3 UV)
**Cells:** 60

## Run 2

**Date:** 2026-08-07
**Session:** fresh subagent
**States:** 6 — DISCONNECTED, CONNECTING, CONNECTED,
RECONNECTING_Backoff, RECONNECTING_AttemptInFlight, FAILED
**Events:** 9 (4 base, 3 timer/internal, 2 UV)
**Cells:** 54

## Divergence

**Aligned grid (4 × 8 = 32 cells), mechanical diff via tools/ensemble_convergence.py:**

| Metric | Value |
|---|---|
| Aligned states | 4 (Disconnected↔DISCONNECTED, Connecting↔CONNECTING, Connected↔CONNECTED, Failed↔FAILED) |
| Aligned events | 8 |
| Aligned cells | 32 |
| Convergent | 30 |
| Cell-divergent | 2 (6.3 %) |
| Structural findings | 7 (4 granularity + 3 UV-slicing) |
| **Behavioural convergence rate** | **93.8 %** |
| New questions raised | 2 |

**Cell divergence (2/32 = 6.3 %):**

1. `Disconnected × UV-connect-dup`: Run 1 UNSPECIFIED, Run 2 handle
2. `Failed × disconnect`: Run 1 transition→disconnected (backdoor), Run 2 UNSPECIFIED

Both divergent cells are the FAILED backdoor — the protocol's predicted
divergence source. Run 1 found the backdoor and rendered it as an
explicit transition; Run 2 left the cell unspecified.

**Structural divergence (7 findings):**

- State granularity: Run 1 splits RECONNECTING into a single flat
  state; Run 2 splits it into Backoff and AttemptInFlight sub-states.
  Run 1 adds Disconnected_RetriesExhausted (retry budget survives
  disconnect — the finding both runs observed).
- UV slicing: Run 1 has UV-connection-loss and UV-disconnect-dup;
  Run 2 has UV-disconnect-spurious. Different UV derivation axes.

## Notes

- The predicted FAILED-terminality divergence manifests consistently:
  both runs recognize the disconnect backdoor but handle it differently
  in the matrix.
- Run-to-run variance concentrates in state granularity and
  undesired-variant slicing — the method's softest joints.
  `tools/ensemble_convergence.py` (roadmap §5) addresses this:
  intersection = confidence, symmetric difference = automatic Q
  candidates.
- Tool-verified: 2026-08-07, pack v1.38 — ensemble_convergence
  reproduces the mechanical diff.
