# Invariants and Lints — device-connection

## Doctrine mapping

Doctrine lines extracted from `examples/device-connection/README.md`. Each normative sentence maps to an invariant, a disposition constraint, or an explicit rejection.

| DOC id | Mapping | Target |
|---|---|---|
| DOC-01 | invariant | SYS-01: `connect()` sets state to CONNECTING and starts a connection attempt |
| DOC-02 | disposition | connect in {CONNECTED, CONNECTING} → ignore (documented) |
| DOC-03 | invariant | SYS-02: `disconnect()` sets `_should_stop=True`, cancels pending tasks, sets state to DISCONNECTED |
| DOC-04 | invariant | SYS-03: On successful connection, state=CONNECTED and retry_count=0 |
| DOC-05 | invariant | SYS-04: On connection failure, retry_count increments, component retries up to max_retries with exponential backoff + jitter |
| DOC-06 | invariant | SYS-05: When retry_count >= max_retries, state=FAILED; no further connection attempts |
| DOC-07 | disposition | disconnect in {CONNECTING, RECONNECTING} → transition → DISCONNECTED |
| DOC-08 | invariant | SYS-06: Connection timeout is treated as a failure (caught in same except block, device_connection.py:111) |
| DOC-09 | invariant | SYS-07: retry_count=0 already set on successful connect; min_uptime timer started |
| DOC-10 | invariant | SYS-08: Backoff computed as `base_backoff * 2^(retry_count-1) + uniform(0, backoff*0.5)` |

## NAT — Assumptions about the environment

| ID | Statement | Cited callee / upstream |
|---|---|---|
| NAT-01 | `connect()` and `disconnect()` are called within a running asyncio event loop. | Caller contract — component uses `asyncio.create_task` and `asyncio.sleep`. |
| NAT-02 | The device address (`DeviceInfo.address`) is valid and reachable under normal network conditions. | `DeviceInfo` — value supplied by caller at construction. |
| NAT-03 | `asyncio.sleep()` does not wake spuriously. Python's asyncio implementation does not have spurious wakeups; this is an environmental assumption. | `asyncio` standard library. |
| NAT-04 | `asyncio.wait_for()` raises `TimeoutError` when the timeout is exceeded. This is Python's documented contract. | `asyncio` standard library. |
| NAT-05 | Task cancellation via `task.cancel()` propagates `CancelledError` into the task's coroutine at the next `await` point. | `asyncio.Task.cancel()` — Python standard library contract. |
| NAT-06 | Component is single-tenant: one `DeviceConnection` manages one device. No concurrent sharing of the same instance across threads. | Caller contract — no synchronization primitives in the component. |

## SYS — Obligations of the system

| ID | Statement | Verified states |
|---|---|---|
| SYS-01 | `state ∈ {DISCONNECTED, CONNECTING, CONNECTED, RECONNECTING, FAILED}` at all times. | All — enum guarantees this by construction. |
| SYS-02 | `retry_count ≤ max_retries` at all times. | All — checked in `_connect_loop` line 102; reset to 0 on success line 107; only incremented on failure line 112. |
| SYS-03 | After `connect()` returns from DISCONNECTED, `state == CONNECTING`. | DISCONNECTED — `device_connection.py:89`. |
| SYS-04 | After successful connection, `state == CONNECTED` and `retry_count == 0`. | CONNECTING, RECONNECTING — `device_connection.py:106-107`. |
| SYS-05 | `connect()` in FAILED raises `ConnectionError`. | FAILED — `device_connection.py:87-88`. |
| SYS-06 | After `disconnect()`, `state == DISCONNECTED` regardless of prior state (including FAILED per current code, but see Q-06). | All — `device_connection.py:100`. |
| SYS-07 | `_connect_task` is not None only during CONNECTING or RECONNECTING. | CONNECTING, RECONNECTING — set at `device_connection.py:90`, cleared on cancel/complete. |
| SYS-08 | Backoff includes random jitter: `backoff = base_backoff * (2 ** (retry_count - 1)) + uniform(0, backoff * 0.5)`. | RECONNECTING — `device_connection.py:119-120`. |
| SYS-09 | When `_should_stop == True`, the connection loop terminates at the next iteration boundary and no new attempts are made. | CONNECTING, RECONNECTING — `device_connection.py:102`. |

## SYS Invariant state-by-state check

| Invariant | DISCONNECTED | CONNECTING | CONNECTED | RECONNECTING | FAILED |
|---|---|---|---|---|---|
| SYS-01 (state in enum) | ✓ | ✓ | ✓ | ✓ | ✓ |
| SYS-02 (retry_count ≤ max_retries) | ✓ (retry_count=0) | ✓ | ✓ (retry_count=0) | ✓ | ✓ (retry_count=max_retries at time of entry) |
| SYS-06 (disconnect → DISCONNECTED) | ✓ (no-op) | ✓ | ✓ | ✓ | ⚠ code allows, Q-06 |
| SYS-07 (_connect_task) | ✓ (None) | ✓ (non-None) | ✓ (None after loop returns) | ✓ (non-None) | ✓ (None after loop exits) |

## Lints

| ID | Severity | Description | Location |
|---|---|---|---|
| L-01 | HIGH | `connect()` during RECONNECTING is not prevented — the guard at `device_connection.py:85` only checks CONNECTED/CONNECTING. A second `connect()` creates a new `_connect_task`, overwriting the reference to the running retry loop. The orphaned task may still fire events. | device_connection.py:85 |
| L-02 | HIGH | `disconnect()` during FAILED transitions to DISCONNECTED (`device_connection.py:100`). R-05 states the component "remains in FAILED state permanently." Code and requirement conflict. | device_connection.py:91-100, README.md R-05 |
| L-03 | MEDIUM | `_uptime_task` is created but its completion has no side effect — the comment at `device_connection.py:144-145` notes that `retry_count=0` is already handled in `_connect_loop`. The uptime timer is dead code that could be removed or repurposed to detect early disconnection. | device_connection.py:139-147 |
| L-04 | MEDIUM | `_should_stop` is set to `False` in `connect()` (`device_connection.py:88`) but only checked at the top of the while loop (`device_connection.py:102`). If `_should_stop` was set to `True` by a previous `disconnect()`, the new `connect()` correctly resets it. However, there is a TOCTOU window between the check and the `_attempt_connection()` call. | device_connection.py:88,102 |
| L-05 | INFO | `_connect_task` and `_uptime_task` are not awaited after cancellation. The tasks may still be in a cancelled state when the next `connect()` overwrites `_connect_task`. This is Python-idiomatic (cancelled tasks are GC'd) but could confuse static analysis. | device_connection.py:95-97 |
