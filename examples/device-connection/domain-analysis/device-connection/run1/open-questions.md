# Open questions — device-connection

Q-01 Internal events arriving when no _connect_loop is active

**Question:** What is the defined behavior when `connection_succeeds`, `connection_fails`, `connection_timeout`, `backoff_elapsed`, or `max_retries_exhausted` arrive in DISCONNECTED, CONNECTED, or FAILED states (where no `_connect_loop` is running)? Also: `backoff_elapsed` arriving in CONNECTING (loop is running but no backoff is active).

**Current:** Under normal single-threaded asyncio execution, these events cannot arrive — the `_connect_loop` is the sole producer and consumer of internal events, and it only runs in CONNECTING and RECONNECTING states. However, orphaned tasks (see Q-02) could deliver stale events. The code has no handling for internal events arriving in unexpected states.

**Affected cells:** (DISCONNECTED, connection_succeeds), (DISCONNECTED, connection_fails), (DISCONNECTED, connection_timeout), (DISCONNECTED, backoff_elapsed), (DISCONNECTED, max_retries_exhausted), (CONNECTING, backoff_elapsed), (CONNECTED, connection_succeeds), (CONNECTED, connection_fails), (CONNECTED, connection_timeout), (CONNECTED, backoff_elapsed), (CONNECTED, max_retries_exhausted), (FAILED, connection_succeeds), (FAILED, connection_fails), (FAILED, connection_timeout), (FAILED, backoff_elapsed), (FAILED, max_retries_exhausted). Total: 16 cells UNSPECIFIED.

**ODC:** F-01 (missing transition), F-15 (out-of-order/stale event from orphaned task). Trigger: step-4 matrix walk.

**Proposed:** For DISCONNECTED/CONNECTED/FAILED, all internal events are `ignore (accidental)` — they represent stale or spurious deliveries from tasks that should no longer exist. The real fix is to prevent orphaned tasks (Q-02). For CONNECTING, `backoff_elapsed` is `ignore (accidental)` since backoff only fires in RECONNECTING.

**Status:** OPEN

---

Q-02 connect() during RECONNECTING orphans existing _connect_loop task

**Question:** When `connect()` is called while the component is in RECONNECTING state, the idempotent guard at line 84 does not block (only checks CONNECTED and CONNECTING). The code proceeds to create a new `_connect_loop` task (line 89), overwriting `self._connect_task` without cancelling the old task. The old task continues executing and can produce state transitions (connection_succeeds, connection_fails) that race with the new task. Is this behavior intentional, or should `connect()` cancel the existing task before creating a new one?

**Current:** `device_connection.py:84-89`:
```python
if self.state in (State.CONNECTED, State.CONNECTING):
    return  # RECONNECTING is NOT in this set
...
self._connect_task = asyncio.create_task(self._connect_loop())
```
The old task is neither awaited nor cancelled. It becomes an orphan that can independently modify `self.state` and `self.retry_count`.

**ODC:** F-09 (cancellation leak — old task not cancelled), F-07 (lifecycle coupling — two tasks sharing `retry_count` and `state`). Trigger: step-4 matrix walk.

**Proposed:** Either (a) add RECONNECTING to the idempotent guard at line 84, making `connect()` during RECONNECTING a no-op, or (b) cancel the existing `_connect_task` before creating a new one. Option (a) is simpler and matches the stated idempotent semantics of `connect()`.

**Status:** OPEN

---

Q-03 disconnect() from FAILED state transitions to DISCONNECTED, contradicting R-05

**Question:** R-05 states "The component remains in FAILED state permanently." However, `disconnect()` has no FAILED guard (lines 92-99) and unconditionally sets `self.state = State.DISCONNECTED` at line 99. Calling `disconnect()` from FAILED recovers the component to DISCONNECTED. Is this intentional (disconnect as a recovery mechanism) or should `disconnect()` reject in FAILED state?

**Current:** `device_connection.py:92-99`:
```python
async def disconnect(self) -> None:
    self._should_stop = True
    if self._connect_task is not None:
        self._connect_task.cancel()
        self._connect_task = None
    if self._uptime_task is not None:
        self._uptime_task.cancel()
        self._uptime_task = None
    self.state = State.DISCONNECTED
```
No early return or guard for FAILED state.

**ODC:** F-06 (trap door — undocumented recovery path from terminal state), F-19 (unimplemented requirement — R-05 permanence not enforced). Trigger: step-4 matrix walk.

**Proposed:** Add a FAILED guard to `disconnect()` that raises an error or is a no-op, matching R-05. Alternatively, if recovery via disconnect is intentional, update R-05 to document FAILED as "terminal unless explicitly disconnected."

**Status:** OPEN

---

Q-04 retry_count reset before min_uptime validation (R-08 gap)

**Question:** R-08 says "A connection that survives for at least `min_uptime` is considered stable." The code resets `retry_count = 0` immediately on successful connect (line 106), before `min_uptime` has elapsed. The `_uptime_task` (lines 127-132) is a no-op — it sleeps for `min_uptime` and then does nothing. If the connection drops within `min_uptime`, the component does not detect the drop, and `retry_count` has already been reset. Should the retry_count reset be deferred until after `min_uptime` elapses?

**Current:** `device_connection.py:105-107`:
```python
self.state = State.CONNECTED
self.retry_count = 0
self._start_uptime_timer()
```
And `device_connection.py:127-132`:
```python
async def _uptime():
    await asyncio.sleep(self.min_uptime)
    # Connection survived min_uptime — already handled by
    # retry_count=0 set in _connect_loop.
```
The timer is a no-op. Additionally, there is no mechanism to detect a dropped connection (see Q-05).

**ODC:** F-19 (unimplemented requirement — R-08 not enforced). Trigger: step-5 lint (waiting/connecting states without timeout — CONNECTED has no timeout or heartbeat).

**Proposed:** If early-drop detection is desired, the uptime timer should monitor the connection and, on early drop, restore the pre-reset retry_count (or increment it). If R-08 is aspirational (retry_count=0 is acceptable even for short connections), the timer should be removed and R-08 revised.

**Status:** OPEN

---

Q-05 No connection-drop detection after CONNECTED

**Question:** Once the component reaches CONNECTED state, there is no mechanism to detect a dropped connection. The component stays CONNECTED until `disconnect()` is called. There is no heartbeat, no connection monitoring, and no automatic reconnection. Is this intentional (the component relies on the caller to detect drops and call `disconnect()`), or should `_uptime_task` be extended to monitor connection health?

**Current:** No connection monitoring code exists. `_uptime_task` (lines 127-132) only sleeps and exits. The `_simulate_connect` function (lines 121-125) only models connection establishment, not ongoing connection health.

**ODC:** F-01 (missing transition — no CONNECTED → RECONNECTING path on connection loss). Trigger: step-5 lint (waiting/connecting/stopping states without timeout — CONNECTED has no timeout or monitoring).

**Proposed:** Either (a) document that connection health monitoring is outside the component's scope (NAT assumption: caller detects drops), or (b) add a heartbeat/keepalive mechanism that transitions CONNECTED → RECONNECTING on failure.

**Status:** OPEN
