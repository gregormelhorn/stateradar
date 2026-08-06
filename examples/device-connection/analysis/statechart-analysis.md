# StateRadar Analysis — Synthetic Device Connection

**Component:** `DeviceConnection` (Python, 130 LOC)
**Pack:** v1.33
**Date:** 2026-08-06

---

## Part A — Code-Informed Analysis

### State model (PA-17)

| State | Condition | Terminal? |
|---|---|---|
| DISCONNECTED | No connection, no pending attempt | No |
| CONNECTING | `_connect_task` running, `_connect_loop` active | No |
| CONNECTED | Connection established, `_uptime_task` running | No |
| RECONNECTING | Between attempts, backoff+sleep active | No |
| FAILED | `retry_count >= max_retries`, R-05 says "permanently" | Claimed but not enforced |

### Events

| ID | Source | Description |
|---|---|---|
| connect | Caller | `connect()` called |
| disconnect | Caller | `disconnect()` called |
| connection_succeeds | Internal | `_attempt_connection()` returns without error |
| connection_fails | Internal | `_attempt_connection()` raises ConnectionError |
| connection_timeout | Internal | `_attempt_connection()` times out |
| backoff_elapsed | Internal | `asyncio.sleep(backoff+jitter)` completes |
| max_retries_exhausted | Internal | `retry_count >= max_retries` in `_connect_loop` |

### Disposition matrix (critical cells)

<!-- states: DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED -->

| state | connect | disconnect | connection_succeeds | connection_fails | connection_timeout | backoff_elapsed | max_retries_exhausted |
|---|---|---|---|---|---|---|---|
| **DISCONNECTED** | transition → CONNECTING device_connection.py:62 | ignore (documented) — already disconnected | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |
| **CONNECTING** | ignore (documented) — already connecting device_connection.py:60 | transition → DISCONNECTED — cancels task device_connection.py:72 | transition → CONNECTED device_connection.py:84 | transition → RECONNECTING — increments retry_count device_connection.py:88 | transition → RECONNECTING device_connection.py:88 | ignore (accidental) → Q-01 — not in backoff phase | transition → FAILED device_connection.py:91 |
| **CONNECTED** | ignore (documented) — already connected device_connection.py:60 | transition → DISCONNECTED — cancels uptime task device_connection.py:72 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |
| **RECONNECTING** | ignore (documented) — already connecting | transition → DISCONNECTED — _should_stop=True device_connection.py:72 | transition → CONNECTED — on next loop iteration after sleep | transition → RECONNECTING — stays, increments retry_count | transition → RECONNECTING — stays | transition → CONNECTING — retry attempt device_connection.py:82 | transition → FAILED |
| **FAILED** | transition → CONNECTING — _connect_loop starts device_connection.py:63 | **UNSPECIFIED → Q-02** — sets state to DISCONNECTED, retry_count NOT reset. _connect_loop exits immediately on reconnect, leaving state stuck in CONNECTING | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (documented) — already failed |

### Findings

**Q-01:** Internal events in non-active states. Structurally impossible —
these events only fire from within `_connect_loop`. Document as such.

**Q-02 (Critical):** `disconnect()` in FAILED state. R-05 states FAILED is
permanent, but `disconnect()` at `device_connection.py:72-79` does not check
for FAILED. It sets `self.state = State.DISCONNECTED`, allowing a subsequent
`connect()` to re-enter CONNECTING. However, `retry_count` is not reset by
`disconnect()`, so `_connect_loop` exits immediately (`retry_count >= max_retries`
still true), leaving the component stuck in CONNECTING with no running task.
This is a lifecycle disagreement: `disconnect()` exits FAILED (contradicting
R-05) and produces a stuck state because `retry_count` is not cleared.

### Part B — Blind Requirements Analysis

From requirements alone, Part B would derive:
- FAILED is terminal (R-05: "permanently")
- `disconnect()` should be `ignore (documented)` or `reject` in FAILED
- `retry_count` should be reset on disconnect or not affect a fresh connection

The cell `(FAILED, disconnect) = UNSPECIFIED` is the primary finding.
Part B would flag it identically to Part A.

### Blind diff

| Cell | Part A | Part B | Classification |
|---|---|---|---|
| (FAILED, disconnect) | transition → DISCONNECTED (then stuck) | IGNORE or REJECT (terminal) | **E — implementation defect** |

### CONVERGENCE note

This is a single-run analysis. For calibration data, run the pilot
twice in independent sessions and record the divergence rate.
