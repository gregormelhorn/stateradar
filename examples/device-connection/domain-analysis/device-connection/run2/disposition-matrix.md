# Disposition Matrix — device-connection

<!-- states: DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED -->

Abstraction: This matrix models `DeviceConnection` as a single-threaded asyncio component. Events are delivered sequentially within one event loop iteration. Concurrent access (multiple coroutines calling `connect()`/`disconnect()`) is treated as a UV interaction pair.

Guard Group G1 (`connection_fails`, `connection_timeout` in states {CONNECTING, RECONNECTING}):
- G1a: `retry_count + 1 < max_retries` → target RECONNECTING
- G1b: `retry_count + 1 >= max_retries` → target FAILED
- Provenance: observed-in-code (device_connection.py:111-118)
- z3 proof: not-formalizable: requires modelling mutable `retry_count` and `max_retries` across sequential failures; the guard outcome depends on execution history, not just current state and event.

| state | connect | disconnect | connection_succeeds | connection_fails | connection_timeout | backoff_elapsed | max_retries_exhausted |
|---|---|---|---|---|---|---|---|
| **DISCONNECTED** | transition → CONNECTING device_connection.py:88-90 | ignore (documented) device_connection.py:100 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 |
| **CONNECTING** | ignore (documented) device_connection.py:85-86 | transition → DISCONNECTED device_connection.py:92-100 | transition → CONNECTED device_connection.py:106-108 | transition → RECONNECTING [G1a] device_connection.py:111-118 | transition → RECONNECTING [G1a] device_connection.py:111-118 | UNSPECIFIED → Q-02 | UNSPECIFIED → Q-03 |
| **RECONNECTING** | UNSPECIFIED → Q-04 | transition → DISCONNECTED device_connection.py:92-100 | transition → CONNECTED device_connection.py:106-108 | transition → RECONNECTING [G1a] device_connection.py:111-118 | transition → RECONNECTING [G1a] device_connection.py:111-118 | handle device_connection.py:120 | UNSPECIFIED → Q-03 |
| **CONNECTED** | ignore (documented) device_connection.py:85-86 | transition → DISCONNECTED device_connection.py:92-100 | UNSPECIFIED → Q-05 | UNSPECIFIED → Q-05 | UNSPECIFIED → Q-05 | UNSPECIFIED → Q-05 | UNSPECIFIED → Q-05 |
| **FAILED** | reject device_connection.py:87-88 | UNSPECIFIED → Q-06 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 | UNSPECIFIED → Q-07 |

Note: Connection fails/timeout from CONNECTING and RECONNECTING under guard G1b transitions to FAILED (device_connection.py:113-115). The matrix parser extracts only the first target per cell; the G1b → FAILED path is documented in the Guard Group above.
