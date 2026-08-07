# Ensemble Convergence Report

## Runs

- **run1**
  States: 5, Events: 21
- **run2**
  States: 5, Events: 7

## Structural divergence (not in cell rate)

- Event presence divergence: 'UV-connect-commission' — run-1: UV-connect-commission; run-2: absent
- Event presence divergence: 'UV-connect-contradiction' — run-1: UV-connect-contradiction; run-2: absent
- Event presence divergence: 'UV-connect-delay' — run-1: UV-connect-delay; run-2: absent
- Event presence divergence: 'UV-connect-duplication' — run-1: UV-connect-duplication; run-2: absent
- Event presence divergence: 'UV-connect-loss' — run-1: UV-connect-loss; run-2: absent
- Event presence divergence: 'UV-connect-out-of-order' — run-1: UV-connect-out-of-order; run-2: absent
- Event presence divergence: 'UV-connect-value' — run-1: UV-connect-value; run-2: absent
- Event presence divergence: 'UV-disconnect-commission' — run-1: UV-disconnect-commission; run-2: absent
- Event presence divergence: 'UV-disconnect-contradiction' — run-1: UV-disconnect-contradiction; run-2: absent
- Event presence divergence: 'UV-disconnect-delay' — run-1: UV-disconnect-delay; run-2: absent
- Event presence divergence: 'UV-disconnect-duplication' — run-1: UV-disconnect-duplication; run-2: absent
- Event presence divergence: 'UV-disconnect-loss' — run-1: UV-disconnect-loss; run-2: absent
- Event presence divergence: 'UV-disconnect-out-of-order' — run-1: UV-disconnect-out-of-order; run-2: absent
- Event presence divergence: 'UV-disconnect-value' — run-1: UV-disconnect-value; run-2: absent

## State alignment (case-insensitive exact match)

Aligned states: 5

- `connected` ← CONNECTED, CONNECTED
- `connecting` ← CONNECTING, CONNECTING
- `disconnected` ← DISCONNECTED, DISCONNECTED
- `failed` ← FAILED, FAILED
- `reconnecting` ← RECONNECTING, RECONNECTING

## Cell convergence (aligned grid only)

Aligned grid: 5 states × 7 events

| Metric | Value |
|---|---|
| Total aligned cells | 35 |
| Convergent | 30 |
| Disposition-divergent | 5 |
| Target-divergent | 0 |
| Hole noise (non-behavioural) | 0 |
| **Behavioural convergence rate** | **85.7%** |
| New questions raised | 5 |
| Structural findings | 14 |

## Divergent cells → Questions

### Q-EC-01
**Status:** OPEN

Ensemble divergence at (CONNECTING, max_retries_exhausted): run1: transition→failed; run2: UNSPECIFIED. Multiple independent pilot runs disagree on the disposition. Human decision required.

### Q-EC-02
**Status:** OPEN

Ensemble divergence at (DISCONNECTED, disconnect): run1: handle; run2: ignore (documented). Multiple independent pilot runs disagree on the disposition. Human decision required.

### Q-EC-03
**Status:** OPEN

Ensemble divergence at (FAILED, disconnect): run1: transition→disconnected; run2: UNSPECIFIED. Multiple independent pilot runs disagree on the disposition. Human decision required.

### Q-EC-04
**Status:** OPEN

Ensemble divergence at (RECONNECTING, connect): run1: transition→connecting; run2: UNSPECIFIED. Multiple independent pilot runs disagree on the disposition. Human decision required.

### Q-EC-05
**Status:** OPEN

Ensemble divergence at (RECONNECTING, max_retries_exhausted): run1: transition→failed; run2: UNSPECIFIED. Multiple independent pilot runs disagree on the disposition. Human decision required.
