# Invariants and lints — device-connection

## NAT invariants (environment assumptions; analysis may assume, tests may not)

- **NAT-1** `_simulate_connect` is probabilistic (~70% success) and may fail unpredictably. The connection result (success, refused, timeout) is determined by the simulated network environment. Observed-in-code: `device_connection.py:137-144`.
- **NAT-2** Single-input assumption (PA-8): events are processed one at a time under asyncio cooperative concurrency. The component does not use locks or threads. Observed-in-code: entire class uses `async`/`await` without threading primitives.
- **NAT-3** The caller serializes external events (connect, disconnect). There is no concurrent external dispatch from multiple callers within a single event-loop turn. Observed: standard asyncio contract.
- **NAT-4** `max_retries >= 1` (default 3). The constructor accepts any int; retry_count < max_retries comparison at line 108 assumes max_retries > 0 for meaningful behavior. With max_retries=0, the loop body never executes and the component stays in CONNECTING indefinitely. Proposed: document minimum.
- **NAT-SYS-1** When N > 1 DeviceConnection instances share one device, connection failures may synchronize across instances. The per-instance jitter (`random.uniform(0, backoff * 0.5)`, line 122) provides some decorrelation. Multi-instance traces model aggregate behavior.

## SYS invariants (obligations), checked state by state against the as-is model

| id | predicate | verdict |
|---|---|---|
| SYS-1 | `state == FAILED` ⇒ no `_connect_loop` is running | holds — `_connect_loop` returns at line 119 after setting FAILED; `connect()` raises in FAILED (line 86-87); no code path starts a new loop from FAILED |
| SYS-2 | `state == DISCONNECTED` ⇒ `_connect_task is None` | **VIOLATED** — `connect()` during RECONNECTING overwrites `_connect_task` (line 91) without cancelling the old task (lines 89-91). The old loop task continues running and can complete after `_connect_task` is set to a new task or to None. → Q-02 |
| SYS-3 | `state == CONNECTED` ⇒ `retry_count == 0` | holds — `retry_count = 0` set immediately at line 112 when connection succeeds; no path increments retry_count while CONNECTED |
| SYS-4 | `state == FAILED` is terminal under normal operation | **VIOLATED** — `disconnect()` has no FAILED guard (lines 96-103) and transitions FAILED → DISCONNECTED. Contradicts R-05 ("remains in FAILED state permanently"). → Q-03 |
| SYS-5 | `disconnect()` eventually reaches DISCONNECTED from any state | holds — disconnect() sets `self.state = State.DISCONNECTED` unconditionally at line 103 |
| SYS-6 | `_uptime_task is not None` ⇒ `state == CONNECTED` | holds — `_uptime_task` is created only in `_start_uptime_timer()` (line 154), called only from `_connect_loop` (line 113) immediately after setting CONNECTED (line 111); cleared on disconnect (line 102) |

## Doctrine mapping

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 DOC-5 DOC-6 DOC-7 DOC-8 DOC-9 -->

| id | mapping | target |
|---|---|---|
| DOC-1 | cell | (DISCONNECTED, connect), (CONNECTING, connect), (CONNECTED, connect) |
| DOC-2 | cell | (CONNECTING, disconnect), (RECONNECTING, disconnect) |
| DOC-3 | cell | (CONNECTING, connection_succeeds), (RECONNECTING, connection_succeeds) |
| DOC-3 | invariant | SYS-3 |
| DOC-4 | cell | (CONNECTING, connection_fails), (CONNECTING, connection_timeout), (RECONNECTING, connection_fails), (RECONNECTING, connection_timeout) |
| DOC-5 | cell | (CONNECTING, max_retries_exhausted), (RECONNECTING, max_retries_exhausted), (FAILED, connect) |
| DOC-5 | invariant | SYS-1, SYS-4 |
| DOC-6 | cell | (CONNECTING, disconnect), (RECONNECTING, disconnect) |
| DOC-7 | cell | (CONNECTING, connection_timeout), (RECONNECTING, connection_timeout) |
| DOC-8 | invariant | SYS-3 — retry_count=0 on connect; **gap**: reset happens before min_uptime elapses → Q-04 |
| DOC-9 | cell | backoff jitter at `device_connection.py:122-123` |

## Doctrine sweep prose detail (Step-5 closure of the DOC sweep; PA-22 cell check)

| DOC | classification | mapping | verdict |
|---|---|---|---|
| DOC-1 | adopted: disposition constraint | (DISCONNECTED, connect) → CONNECTING; (CONNECTING/CONNECTED, connect) → ignore | conforms at `device_connection.py:84,89-91` |
| DOC-2 | adopted: disposition constraint | (CONNECTING/RECONNECTING, disconnect) → DISCONNECTED | conforms at `device_connection.py:96-103` |
| DOC-3 | adopted: disposition constraint + invariant | connection_succeeds → CONNECTED, retry_count=0 | conforms at `device_connection.py:111-112` |
| DOC-4 | adopted: disposition constraint | connection fails → retry with exponential backoff + jitter | conforms at `device_connection.py:115-123`; jitter at line 122 |
| DOC-5 | adopted then found **violated** | max_retries_exhausted → FAILED, permanent; (FAILED, connect) → reject | SYS-1 holds (no loop in FAILED). SYS-4 **violated**: disconnect() from FAILED → DISCONNECTED at line 96-103. FAILED is not permanent. → Q-03 |
| DOC-6 | adopted: disposition constraint | disconnect during CONNECTING/RECONNECTING → DISCONNECTED | conforms at `device_connection.py:96-100` |
| DOC-7 | adopted: disposition constraint | timeout treated as failure, retried | conforms — same except block at `device_connection.py:115` |
| DOC-8 | adopted: invariant | retry_count=0 after stable connection | **gap**: retry_count reset at line 112 happens before min_uptime elapses. `_uptime_task` is a no-op (lines 149-154). Connection drops within min_uptime are not detected. → Q-04 |
| DOC-9 | adopted: code observation | backoff includes random jitter | conforms at `device_connection.py:122-123` |

## Lint checklist (rules.toml step-5 list)

| lint | finding |
|---|---|
| waiting/connecting/stopping states without timeout | CONNECTING and RECONNECTING have timeout via `connect_timeout` in `_attempt_connection` (lines 129-134). **However**, CONNECTED has no connection monitoring — once connected, the component stays CONNECTED until disconnect(). No heartbeat, no drop detection. → Q-05 |
| retries without a maximum | bounded by `max_retries` (default 3, line 60). Conforms. **Note**: `max_retries=0` is accepted by constructor and results in infinite CONNECTING (loop body never executes, line 108). Proposed: validate max_retries >= 1. |
| invoked external operations without explicit failure outcome | `_attempt_connection` explicitly models success/failure/timeout (lines 125-135). All outcomes handled. Conforms. |
| externally initiated operations without cancellation handling | `connect()` creates cancellable `_connect_task` (line 91). `disconnect()` cancels it (line 98). **Gap**: `connect()` during RECONNECTING does not cancel the old task before creating a new one. → Q-02 (F-09 cancellation leak) |
| terminal/error states without documented meaning | FAILED is documented in R-05 ("no further connection attempts"). **Contradiction**: FAILED can be exited via disconnect(). → Q-03 |
| undefined startup/shutdown behaviour | Startup: `__init__` at lines 57-79 sets state=DISCONNECTED, retry_count=0. Shutdown: `disconnect()` cancels tasks and sets DISCONNECTED. **No dedicated shutdown/cleanup method** — disconnect() doubles as cleanup. Acceptable for single-device component. |
| unbounded queues/buffers, unhandled overload | No queues or buffers. Conforms. |
| synchronized reset points | `retry_count=0` on successful connect (line 112) is a synchronized reset: all instances that connect simultaneously reset their retry count. With NAT-SYS-1, a device flap can synchronize reset across instances. The jitter applies only to backoff, not to the retry_count reset. Proposed: note in multi-instance analysis. |
| lifecycle disagreement (PA-21) | `retry_count` is accessed from both `connect()` (indirectly via `_connect_loop`) and `_connect_loop` internal. The orphaned-task scenario (Q-02) creates two concurrent `_connect_loop` instances accessing the same `retry_count` — a lifecycle coupling fault (F-07). |
| dual ownership cleanup (PA-23) | `_connect_task` is created by `connect()` and cancelled by `disconnect()`. Single ownership in normal flow. **Gap**: connect() during RECONNECTING creates a second task without releasing the first. → Q-02 |
| async cancellation isolation (PA-24) | `_connect_loop` task is fire-and-forget after `connect()` returns. No synchronization from task completion back to the caller. Acceptable for state-only component (no result channel). **Gap**: orphaned task can deliver state changes after disconnect() — no suppression mechanism. → Q-02 |
| user-model gap | (RECONNECTING, connect) → CONNECTING via lines 89-91: correct disposition but the orphaned task scenario (racing old and new `_connect_loop`) is visible only under concurrent execution (two loop tasks). The adversarial trace P-03b documents this. Also (FAILED, disconnect) → DISCONNECTED: correct per code but contradicts documented contract R-05. |
