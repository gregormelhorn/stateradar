# CONVERGENCE — Device Connection

**Component:** `examples/device-connection/device_connection.py`
**Method:** Two independent Part-A pilot runs on the same component.
**Status:** Pending — needs two fresh sessions.

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

**Date:** (pending)
**Session:** (pending)
**Matrix cells:** (pending)
**UNSPECIFIED cells:** (pending)
**Ignore (accidental) cells:** (pending)

## Run 2

**Date:** (pending)
**Session:** (pending)
**Matrix cells:** (pending)
**UNSPECIFIED cells:** (pending)
**Ignore (accidental) cells:** (pending)

## Divergence

| Metric | Run 1 | Run 2 | Match |
|---|---|---|---|
| States | | | |
| Events | | | |
| Cells total | | | |
| Convergent | — | — | |
| Convergent-hole | — | — | |
| Divergent | — | — | |
| Pass-B-blind-spot | — | — | |

**Divergence rate:** (pending)

## Notes

- The FAILED state backdoor (disconnect exits FAILED) may be
  classified differently by the two runs — one may model FAILED as
  terminal (per R-05), the other may model it as non-terminal (per
  implementation). This is the expected primary divergence source.
