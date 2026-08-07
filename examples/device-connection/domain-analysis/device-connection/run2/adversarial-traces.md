# Adversarial traces — device-connection

Format per trace: (a) sequence, (b) what the code does (provenance),
(c) question raised, or `none — control trace` (with the
requirement-scope line where a verdict cites text).

## Systematic — interaction-pair orderings

**P-01a** connect then disconnect during CONNECTING.
(a) DISCONNECTED → connect → CONNECTING → disconnect → DISCONNECTED.
(b) `connect()` sets state=CONNECTING and creates `_connect_task` (lines 89-91).
`disconnect()` cancels `_connect_task` (line 98), sets `_connect_task=None`
(line 99), sets state=DISCONNECTED (line 103). The cancelled task raises
`CancelledError` which propagates unhandled out of `_connect_loop` (the
except at line 115 only catches ConnectionError/ConnectionTimeout).
(c) none — control trace. Cites R-06 ("Calling disconnect() during
CONNECTING … cancels the connection attempt and returns to DISCONNECTED").
Cited text contemplates this ordering: yes.

**P-01b** disconnect then connect.
(a) CONNECTED → disconnect → DISCONNECTED → connect → CONNECTING.
(b) `disconnect()` cancels `_uptime_task` (line 101-102), sets state=DISCONNECTED
(line 103). `connect()` sets state=CONNECTING (line 90). Normal lifecycle.
(c) none — control trace.

**P-02a** connect then disconnect (contradiction race).
(a) Two events arrive near-simultaneously. If connect processes first:
DISCONNECTED → connect → CONNECTING → disconnect → DISCONNECTED.
If disconnect processes first:
DISCONNECTED → disconnect → DISCONNECTED (handle, idempotent) → connect → CONNECTING.
(b) Under single-input assumption (PA-8), one event completes before the next.
Both orderings are deterministic for the given interleaving.
(c) none — control trace. Both orderings are already covered by matrix cells.

**P-02b** connect during CONNECTING (duplicate connect).
(a) DISCONNECTED → connect → CONNECTING → connect (duplicate) → stays CONNECTING.
(b) Second `connect()` hits idempotent guard at line 84, returns immediately.
State unchanged. `_connect_task` unchanged.
(c) none — control trace. Cites R-01 ("If already connected or connecting,
it is a no-op"). Cited text contemplates this ordering: yes.

**P-03a** disconnect during DISCONNECTED (duplicate disconnect).
(a) DISCONNECTED → disconnect → DISCONNECTED → disconnect → DISCONNECTED.
(b) `disconnect()` always executes (lines 96-103). Sets `_should_stop=True`,
cancels None tasks (no-op), sets state=DISCONNECTED (already DISCONNECTED).
Second call is identical. Idempotent in effect.
(c) none — control trace.

**P-03b** connect during RECONNECTING (orphaned task).
(a) DISCONNECTED → connect → CONNECTING → connection_fails → RECONNECTING →
connect (new call) → CONNECTING. Old `_connect_loop` task continues running
as orphan, new `_connect_loop` created at line 91.
(b) Old task: still in backoff sleep or about to call `_attempt_connection`.
New task: starts fresh `_connect_loop` with `retry_count` possibly modified
by the old task. Both tasks share `self.state`, `self.retry_count`,
`self._should_stop`. Race on state transitions.
(c) **Q-02** — orphaned task races with new task. F-09 (cancellation leak),
F-07 (lifecycle coupling). Cited R-01 text ("If already connected or
connecting, it is a no-op"). RECONNECTING is not "connected or connecting."
Cited text contemplates this ordering: no.

## Systematic — adversarial scenario traces

**T-01** Happy path: connect, succeed, disconnect.
(a) DISCONNECTED → connect → CONNECTING → connection_succeeds → CONNECTED →
disconnect → DISCONNECTED.
(b) Lines 89-91 (connect → CONNECTING), 111-112 (succeed → CONNECTED,
retry_count=0), 96-103 (disconnect → DISCONNECTED).
(c) none — control trace.

**T-02** Retry then succeed.
(a) DISCONNECTED → connect → CONNECTING → connection_fails → RECONNECTING →
backoff_elapsed → connection_succeeds → CONNECTED.
(b) Lines 115-120 (fail → RECONNECTING, retry_count=1), 121-123 (backoff sleep),
111-112 (succeed → CONNECTED, retry_count=0).
(c) none — control trace. Cites R-04 ("retries up to max_retries attempts
with exponential backoff"). Cited text contemplates this ordering: yes.

**T-03** Retry exhaustion after max_retries failures.
(a) DISCONNECTED → connect → CONNECTING → connection_fails (count=1) →
RECONNECTING → backoff_elapsed → connection_fails (count=2) → RECONNECTING →
backoff_elapsed → connection_fails (count=3 >= max=3) → max_retries_exhausted →
FAILED.
(b) Lines 115-119: after third failure, retry_count=3 >= max_retries=3,
state=FAILED, `return`. Loop exits.
(c) none — control trace. Cites R-05 ("When max_retries is exhausted, the
component enters FAILED state"). Cited text contemplates this ordering: yes.

**T-04** Disconnect during RECONNECTING.
(a) DISCONNECTED → connect → CONNECTING → connection_fails → RECONNECTING →
disconnect → DISCONNECTED.
(b) Lines 96-100: `disconnect()` cancels `_connect_task` (which is sleeping
or about to retry), sets state=DISCONNECTED. CancelledError propagates
out of `_connect_loop` (unhandled — except at line 115 only catches
ConnectionError/ConnectionTimeout).
(c) none — control trace. Cites R-06 ("Calling disconnect() during …
RECONNECTING cancels the connection attempt and returns to DISCONNECTED").
Cited text contemplates this ordering: yes.

**T-05** Connection timeout.
(a) DISCONNECTED → connect → CONNECTING → connection_timeout → RECONNECTING.
(b) Lines 129-134: `asyncio.wait_for` raises TimeoutError → `_attempt_connection`
raises ConnectionTimeout → caught at line 115 → retry_count=1, state=RECONNECTING
(line 120).
(c) none — control trace. Cites R-07 ("If a connection attempt does not
complete within connect_timeout, it is treated as a failure and retried").
Cited text contemplates this ordering: yes.

**T-06** disconnect from FAILED (contradicts R-05).
(a) … → max_retries_exhausted → FAILED → disconnect → DISCONNECTED.
(b) Lines 96-103: `disconnect()` has no FAILED guard. Sets `_should_stop=True`,
cancels None tasks, sets state=DISCONNECTED (line 103). Component recovers
from FAILED.
(c) **Q-03** — FAILED is not terminal. R-05 says "remains in FAILED state
permanently." Cites R-05 ("The component remains in FAILED state permanently.
No further connection attempts are made."). Cited text contemplates this
ordering: no.

**T-07** connect rejected in FAILED.
(a) … → FAILED → connect → reject (ConnectionError).
(b) Lines 86-87: `raise ConnectionError("device is in FAILED state")`.
State stays FAILED.
(c) none — control trace. Cites R-05 ("No further connection attempts are
made"). Cited text contemplates this ordering: yes.

**T-08** backoff_elapsed → handle (internal loop).
(a) … → RECONNECTING → backoff_elapsed → (stays RECONNECTING, loop calls
_attempt_connection).
(b) Line 123: `await asyncio.sleep(backoff + jitter)` completes.
The `while` loop (line 108) iterates. State is still RECONNECTING.
`_attempt_connection` is called. If it succeeds → CONNECTED (line 111).
If it fails → RECONNECTING again (line 120) or FAILED (lines 117-119).
(c) none — control trace. Backoff_elapsed itself is `handle` — no state
change. The subsequent connection_succeeds or connection_fails changes state.

**T-09** Connection drops before min_uptime (R-08 gap).
(a) CONNECTING → connection_succeeds → CONNECTED (retry_count=0 immediately,
line 112). Connection drops at t < min_uptime. Component stays CONNECTED
(no drop detection). `_uptime_task` is sleeping (line 150), will wake and
do nothing.
(b) retry_count already 0. No transition on drop. No recovery mechanism.
(c) **Q-04** — retry_count reset before min_uptime validation.
**Q-05** — no connection-drop detection. Cites R-08 ("A connection that
survives for at least min_uptime is considered stable"). R-08's intent
is not enforced. Cited text contemplates this ordering: no.

**T-10** Orphaned task delivers connection_succeeds after disconnect.
(a) DISCONNECTED → connect → CONNECTING → disconnect (cancels task) →
DISCONNECTED. But old `_connect_loop` was in `_attempt_connection` when
cancelled. The `CancelledError` propagates unhandled.
(b) No state change from the cancelled task — CancelledError is not
caught by except at line 115, so the task terminates. However, if
`_attempt_connection` completed just before cancel took effect, the
result could be delivered. Under asyncio, cancel() schedules
CancelledError at the next await point.
(c) none — CancelledError propagation is standard asyncio behavior.
The task terminates without producing further internal events.
