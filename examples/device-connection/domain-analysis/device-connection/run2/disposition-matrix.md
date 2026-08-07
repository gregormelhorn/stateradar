# Disposition matrix — device-connection

<!-- states: DISCONNECTED CONNECTING CONNECTED RECONNECTING FAILED -->

Abstraction: flat leaf states, no hierarchy; completeness is relative to the
21-event catalogue (7 base + 14 UV). Single-input assumption (PA-8): one
event to completion at a time under asyncio cooperative concurrency.

## Base events

| state | connect | disconnect | connection_succeeds | connection_fails | connection_timeout | backoff_elapsed | max_retries_exhausted |
|---|---|---|---|---|---|---|---|
| **DISCONNECTED** | transition →CONNECTING `device_connection.py:89-91` ("self._should_stop = False; self.state = State.CONNECTING") | handle (idempotent) `device_connection.py:96-103` ("self._should_stop = True … self.state = State.DISCONNECTED") | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 |
| **CONNECTING** | ignore (documented) `device_connection.py:84` ("if self.state in (State.CONNECTED, State.CONNECTING): return") | transition →DISCONNECTED `device_connection.py:96-103` ("self._connect_task.cancel(); self.state = State.DISCONNECTED") | transition →CONNECTED `device_connection.py:111-112` ("self.state = State.CONNECTED; self.retry_count = 0") | transition →RECONNECTING `device_connection.py:115-123` [G-1] | transition →RECONNECTING `device_connection.py:115-123` [G-1] | UNSPECIFIED → Q-01 | transition →FAILED `device_connection.py:117-119` [G-1] |
| **CONNECTED** | ignore (documented) `device_connection.py:84` | transition →DISCONNECTED `device_connection.py:96-103` ("self._uptime_task.cancel(); self.state = State.DISCONNECTED") | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 |
| **RECONNECTING** | transition →CONNECTING `device_connection.py:89-91` (RECONNECTING not in idempotent guard at L84) → Q-02 | transition →DISCONNECTED `device_connection.py:96-103` ("self._connect_task.cancel(); self.state = State.DISCONNECTED") | transition →CONNECTED `device_connection.py:111-112` (_connect_loop calls _attempt_connection from RECONNECTING) | transition →RECONNECTING `device_connection.py:115-123` [G-1] | transition →RECONNECTING `device_connection.py:115-123` [G-1] | handle `device_connection.py:123` (sleep completes, loop continues; state stays RECONNECTING) | transition →FAILED `device_connection.py:117-119` [G-1] |
| **FAILED** | reject `device_connection.py:86-87` ("raise ConnectionError('device is in FAILED state')") | transition →DISCONNECTED `device_connection.py:96-103` (no FAILED guard in disconnect) → Q-03 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 | UNSPECIFIED → Q-01 |

## UV-connect variants

| state | UV-connect-loss | UV-connect-delay | UV-connect-duplication | UV-connect-out-of-order | UV-connect-contradiction | UV-connect-commission | UV-connect-value |
|---|---|---|---|---|---|---|---|
| **DISCONNECTED** | ignore (documented) — event never arrives at component; caller must timeout `device_connection.py:81` (connect() is the sole entry point for external connect events) | transition →CONNECTING `device_connection.py:89-91` (processed as connect) | transition →CONNECTING `device_connection.py:89-91` (first instance; second in CONNECTING ignored) | transition →CONNECTING `device_connection.py:89-91` (processed as connect) | transition →CONNECTING `device_connection.py:89-91` (connect wins if ordered first; see P-02a) | transition →CONNECTING `device_connection.py:89-91` (indistinguishable from legitimate connect) | ignore (documented) — connect() takes no arguments `device_connection.py:81` (signature: async def connect(self) -> None) |
| **CONNECTING** | ignore (documented) — event never arrives `device_connection.py:81` | ignore (documented) `device_connection.py:84` (processed as connect, idempotent guard) | ignore (documented) `device_connection.py:84` (second connect during CONNECTING) | ignore (documented) `device_connection.py:84` | ignore (documented) `device_connection.py:84` | ignore (documented) `device_connection.py:84` | ignore (documented) — connect() takes no arguments `device_connection.py:81` |
| **CONNECTED** | ignore (documented) — event never arrives `device_connection.py:81` | ignore (documented) `device_connection.py:84` | ignore (documented) `device_connection.py:84` | ignore (documented) `device_connection.py:84` | ignore (documented) `device_connection.py:84` | ignore (documented) `device_connection.py:84` | ignore (documented) — connect() takes no arguments `device_connection.py:81` |
| **RECONNECTING** | ignore (documented) — event never arrives `device_connection.py:81` | transition →CONNECTING `device_connection.py:89-91` (processed as connect; RECONNECTING not guarded at L84) → Q-02 | transition →CONNECTING `device_connection.py:89-91` → Q-02 | transition →CONNECTING `device_connection.py:89-91` → Q-02 | transition →CONNECTING `device_connection.py:89-91` → Q-02 | transition →CONNECTING `device_connection.py:89-91` → Q-02 | ignore (documented) — connect() takes no arguments `device_connection.py:81` |
| **FAILED** | ignore (documented) — event never arrives `device_connection.py:81` | reject `device_connection.py:86-87` (processed as connect, FAILED guard) | reject `device_connection.py:86-87` | reject `device_connection.py:86-87` | reject `device_connection.py:86-87` | reject `device_connection.py:86-87` | reject `device_connection.py:86-87` |

## UV-disconnect variants

| state | UV-disconnect-loss | UV-disconnect-delay | UV-disconnect-duplication | UV-disconnect-out-of-order | UV-disconnect-contradiction | UV-disconnect-commission | UV-disconnect-value |
|---|---|---|---|---|---|---|---|
| **DISCONNECTED** | ignore (documented) — event never arrives at component; caller must timeout `device_connection.py:93` (disconnect() is the sole entry point for external disconnect events) | handle `device_connection.py:96-103` (processed as disconnect, idempotent) | handle `device_connection.py:96-103` | handle `device_connection.py:96-103` | handle `device_connection.py:96-103` (disconnect wins if ordered first; see P-02b) | handle `device_connection.py:96-103` (indistinguishable from legitimate disconnect) | ignore (documented) — disconnect() takes no arguments `device_connection.py:93` (signature: async def disconnect(self) -> None) |
| **CONNECTING** | ignore (documented) — event never arrives `device_connection.py:93` | transition →DISCONNECTED `device_connection.py:96-103` (processed as disconnect) | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | ignore (documented) — disconnect() takes no arguments `device_connection.py:93` |
| **CONNECTED** | ignore (documented) — event never arrives `device_connection.py:93` | transition →DISCONNECTED `device_connection.py:96-103` (processed as disconnect) | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | ignore (documented) — disconnect() takes no arguments `device_connection.py:93` |
| **RECONNECTING** | ignore (documented) — event never arrives `device_connection.py:93` | transition →DISCONNECTED `device_connection.py:96-103` (processed as disconnect) | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | transition →DISCONNECTED `device_connection.py:96-103` | ignore (documented) — disconnect() takes no arguments `device_connection.py:93` |
| **FAILED** | ignore (documented) — event never arrives `device_connection.py:93` | transition →DISCONNECTED `device_connection.py:96-103` (processed as disconnect, no FAILED guard) → Q-03 | transition →DISCONNECTED `device_connection.py:96-103` → Q-03 | transition →DISCONNECTED `device_connection.py:96-103` → Q-03 | transition →DISCONNECTED `device_connection.py:96-103` → Q-03 | transition →DISCONNECTED `device_connection.py:96-103` → Q-03 | ignore (documented) — disconnect() takes no arguments `device_connection.py:93` |

## Guard notes

### G-1: retry_count guard on connection_fails / connection_timeout / max_retries_exhausted

Applies to: (CONNECTING, connection_fails), (CONNECTING, connection_timeout), (RECONNECTING, connection_fails), (RECONNECTING, connection_timeout), (CONNECTING, max_retries_exhausted), (RECONNECTING, max_retries_exhausted).

Code: `device_connection.py:115-123`. Single except block handles both ConnectionError and ConnectionTimeout. After `self.retry_count += 1` (line 116):
- `retry_count < max_retries` → `self.state = State.RECONNECTING` (line 120)
- `retry_count >= max_retries` → `self.state = State.FAILED` (lines 117-119)

Disjointness: proven pairwise (mutually exclusive integer comparison).
Coverage: jointly exhaustive (every retry_count value satisfies exactly one branch).
Not formalizable: dynamic-state (retry_count is mutable instance state, not a formal parameter).
