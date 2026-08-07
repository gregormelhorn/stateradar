# Adversarial Traces — device-connection

## Interaction Pairs

Interaction pairs examine cross-source event orderings on shared entities. Per-source UV checklists structurally miss races between sources. Each pair is presented in both orderings and evaluated against the component's code.

---

### P-01: connect / disconnect race

**Entities shared:** Single `DeviceConnection` instance, `_connect_task`, `_should_stop` flag.

**Ordering A: connect → disconnect (mid-attempt)**
- **Trace:** `connect()` sets state=CONNECTING, creates `_connect_task` → `_attempt_connection()` starts → `disconnect()` called → sets `_should_stop=True`, cancels `_connect_task`, sets state=DISCONNECTED → cancelled task raises `CancelledError` in `_connect_loop`.
- **Code path:** device_connection.py:84-90 → device_connection.py:91-100.
- **Expected outcome:** Component ends in DISCONNECTED. Connection attempt is cancelled.
- **Cited text contemplates this ordering:** yes (R-06 explicitly covers disconnect during connection).
- **Verdict:** COVERED — R-06.

**Ordering B: disconnect → connect (rapid reconnection)**
- **Trace:** `disconnect()` sets `_should_stop=True`, state=DISCONNECTED → `connect()` called → sets `_should_stop=False`, state=CONNECTING, creates new `_connect_task`.
- **Code path:** device_connection.py:91-100 → device_connection.py:84-90.
- **Expected outcome:** Component restarts connection from DISCONNECTED.
- **Cited text contemplates this ordering:** yes (R-01: "calling connect() initiates a connection attempt"). R-02 completes first, returning to DISCONNECTED; R-01 then applies normally.
- **Verdict:** COVERED — R-01, R-02.

---

### P-02: connection_succeeds / disconnect race

**Entities shared:** Single `DeviceConnection` instance, `_connect_task`.

**Ordering A: connection_succeeds → disconnect (just after connect)**
- **Trace:** Connection succeeds (`device_connection.py:106`) → state=CONNECTED, `retry_count=0`, `_connect_loop` returns → `disconnect()` called → `_should_stop=True`, state=DISCONNECTED.
- **Code path:** device_connection.py:106-108 → device_connection.py:91-100.
- **Expected outcome:** Component enters CONNECTED, then transitions to DISCONNECTED.
- **Cited text contemplates this ordering:** yes (R-03 then R-02).
- **Verdict:** COVERED.

**Ordering B: disconnect → connection_succeeds (success arrives after cancellation)**
- **Trace:** `disconnect()` called during CONNECTING → `_should_stop=True`, task cancelled → BUT `_attempt_connection()` already completed and the coroutine is about to process the success at line 106 → The cancellation may not take effect until the next `await` → `state=CONNECTED` is set AFTER `disconnect()` set it to DISCONNECTED.
- **Code path:** device_connection.py:91-100 → device_connection.py:106-108 (stale).
- **Expected outcome:** RACE: `disconnect()` sets state=DISCONNECTED, but the stale success from the cancelled task may overwrite state to CONNECTED. The component ends CONNECTED despite disconnect().
- **Cited text contemplates this ordering:** no — neither R-02 nor R-06 describes the case where a connection succeeds between the cancellation request and the cancellation taking effect.
- **Verdict:** GAP — raises Q-08. This is a TOCTOU race in the cancellation model.

---

### P-03: connection_fails / disconnect race

**Entities shared:** `_connect_task`, `retry_count`.

**Ordering A: connection_fails → disconnect (during retry loop)**
- **Trace:** Connection fails → `retry_count += 1` → if `retry_count < max_retries`, state=RECONNECTING, `asyncio.sleep(backoff)` starts → `disconnect()` called → `_should_stop=True`, task cancelled, state=DISCONNECTED.
- **Code path:** device_connection.py:111-120 → device_connection.py:91-100.
- **Expected outcome:** Component ends in DISCONNECTED. The backoff sleep is interrupted.
- **Cited text contemplates this ordering:** yes (R-06 covers disconnect during RECONNECTING).
- **Verdict:** COVERED — R-06.

**Ordering B: disconnect → connection_fails (failure arrives after cancellation)**
- **Trace:** Similar to P-02B: `disconnect()` cancels task, but failure already occurred → stale failure sets state=RECONNECTING (or FAILED) after disconnect() set DISCONNECTED.
- **Expected outcome:** RACE: stale failure overwrites DISCONNECTED.
- **Cited text contemplates this ordering:** no.
- **Verdict:** GAP — raises Q-08.

---

### P-04: connect during RECONNECTING (self-race)

**Entities shared:** `_connect_task`, `retry_count`, `state`.

**Trace:** Component is RECONNECTING with an active `_connect_loop` → second `connect()` called → guard at line 85 does NOT block RECONNECTING → `_should_stop=False`, `state=CONNECTING`, new `_connect_task` overwrites the old one → TWO `_connect_loop` coroutines now running.
- **Code path:** device_connection.py:84-90 (second connect) while first _connect_loop is executing (device_connection.py:102-120).
- **Expected outcome:** RACE: Two connection loops compete. The orphaned loop may still fire events (success/failure/timeout) that transition the component from under the new loop.
- **Cited text contemplates this ordering:** no — R-01 only says "if already connected or connecting, it is a no-op." RECONNECTING is not mentioned.
- **Verdict:** GAP — raises Q-04 (already captured in matrix).

---

### P-05: max_retries_exhausted + disconnect race

**Entities shared:** `state`, `_should_stop`.

**Ordering A: final failure → FAILED → disconnect**
- **Trace:** Final connection fails, `retry_count >= max_retries` → `state = FAILED` (line 114) → `disconnect()` called → `state = DISCONNECTED` (line 100).
- **Code path:** device_connection.py:113-115 → device_connection.py:91-100.
- **Expected outcome:** Component exits FAILED via disconnect. Contradicts R-05 "remains in FAILED state permanently."
- **Cited text contemplates this ordering:** no — R-05 does not address explicit disconnect.
- **Verdict:** GAP — raises Q-06 (already captured in matrix).

**Ordering B: disconnect → final failure (disconnect during the last attempt)**
- **Trace:** Disconnect during the final connection attempt → `_should_stop=True`, task cancelled → but the failure exception already propagated to the except block → `state = FAILED` is set AFTER `disconnect()` set DISCONNECTED.
- **Expected outcome:** RACE: FAILED overwrites DISCONNECTED.
- **Cited text contemplates this ordering:** no.
- **Verdict:** GAP — raises Q-08.

---

## Adversarial Scenario Traces

### AS-01: Rapid connect/disconnect cycling

**Trace:** `connect()` → `disconnect()` → `connect()` → `disconnect()` → ... rapid cycling.
**Risk:** Task creation and cancellation churn. `_connect_task` repeatedly overwritten.
**Code observation:** `device_connection.py:90` always creates a new task. `device_connection.py:95` cancels and sets to None. No resource leak in the happy path, but rapid cycling during active connection could create orphaned tasks (see P-04).
**Severity:** MEDIUM.

### AS-02: Stale callback after reconnection

**Trace:** `connect()` → connection attempt starts → `disconnect()` → `connect()` (new attempt) → stale success from first attempt arrives.
**Risk:** The stale success callback sets state=CONNECTED even though a fresh connection attempt is running. The component now thinks it's CONNECTED but a connection loop is still active.
**Code path:** device_connection.py:106-108 fires for the old task. No task-identity check to validate which attempt succeeded.
**Severity:** HIGH — state corruption.
**Related:** Q-08.

### AS-03: Backoff sleep interruption and stale wakeup

**Trace:** Connection fails → RECONNECTING → `asyncio.sleep(backoff)` starts → `disconnect()` cancels task → BUT sleep already completed, task resumes at line 102 → `_should_stop` check catches it, loop exits.
**Risk:** The `_should_stop` check at line 102 is the defense. If the backoff elapsed between `disconnect()` starting and the task cancellation propagating, the loop iterates once more. In this iteration, `_should_stop` is True, so the while condition fails and the loop exits without another attempt.
**Severity:** LOW — the `_should_stop` flag catches this case.

### AS-04: max_retries = 0 or negative

**Trace:** Component constructed with `max_retries=0`. `connect()` → `_connect_loop` enters while `0 < 0` → loop body never executes → component remains in CONNECTING indefinitely.
**Risk:** The component hangs in CONNECTING. No timeout, no failure, no state change after the initial `connect()`.
**Code path:** device_connection.py:102: `while self.retry_count < self.max_retries` — `0 < 0` is False, loop skipped entirely.
**Severity:** MEDIUM — input validation gap.
**Related:** UV-maxretries-value (coverage table).

### AS-05: _uptime_task surviving disconnect

**Trace:** Connection succeeds → `_start_uptime_timer()` creates `_uptime_task` → `disconnect()` called rapidly → `_uptime_task` is cancelled at line 98-99.
**Expected:** `_uptime_task` cancelled. No leak.
**Severity:** NONE — properly handled.

---

## Q-08: TOCTOU race in task cancellation model

**Status:** OPEN

**Context:** The component uses `asyncio.Task.cancel()` for cancellation. Python's cancellation is cooperative: it raises `CancelledError` at the next `await`. If a connection attempt completes (success or failure) between the cancellation request and the next `await`, the result is processed AFTER `disconnect()` already set state=DISCONNECTED. This creates a TOCTOU window where stale results can overwrite the disconnected state.

**Affected pairs:** P-02B, P-03B, P-05B.

**Question:** Should the component:
1. **Add task-identity checks** — tag each attempt with a generation counter; discard results from stale generations.
2. **Add state guards before applying results** — check `self.state in (CONNECTING, RECONNECTING)` before applying connection_succeeds/connection_fails.
3. **Accept the race** — document that rapid disconnect/reconnect cycles may have undefined behavior.

**Recommendation:** Option 2. Adding a state guard at `device_connection.py:106` and `device_connection.py:111` is the minimal fix: check that the component is still in an appropriate state before applying the outcome.
