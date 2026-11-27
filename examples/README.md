# examples — reference components

Part of [StateRadar](../README.md).

## Overview

Reference runs of the pack. Each one shows what a complete StateRadar
analysis looks like: statechart, [disposition matrix](../README.md#glossary),
open questions, decision records and the checks that gate them.

### Device connection (synthetic)

`device-connection/` is a 147-line Python component built for this purpose:
the lifecycle of a single device, with a terminal FAILED state that its code
does not keep terminal (see
[device-connection Invariants](#invariants)).

The example runs the full [Part A + Part B](../README.md#glossary) workflow
on a component small enough to read in two minutes. Its two independent
pilot runs are in `device-connection/domain-analysis/device-connection/run1/`
and `run2/`. Their convergence report is
[CONVERGENCE.md](./device-connection/CONVERGENCE.md).

### Disclosure before adding a component

Analysis artifacts describe the analyzed system's internals in detail:
architecture, event flows and failure behaviour. grpc-addrconn and
weighted-semaphore analyze public, pinned open-source code. Before you commit
an analysis of non-public code, review the disclosure implications: IP,
security and confidentiality. The synthetic device-connection example is the
safe default for public demonstrations.

## Subdirectories & Boundaries

- device-connection: [`./device-connection/README.md`](./device-connection/README.md) -
  the requirements (R-01..R-09) and two analysis runs; its code contract is
  [below](#device-connection).
- grpc-addrconn: [`./grpc-addrconn/README.md`](./grpc-addrconn/README.md) -
  grpc-go `addrConn` pinned at v1.18.0.
  - It holds a benchmark for the cancellation-leak fault class (F-09).
  - It also holds a fixture for the [late-completion](../README.md#glossary)
    check.
- weighted-semaphore: [`./weighted-semaphore/README.md`](./weighted-semaphore/README.md) -
  an evaluation copy of `golang.org/x/sync/semaphore`.
  - Its source implements its own decision records DR-001..DR-004 as runtime
    changes; `CONTRACT.md` documents DR-005..DR-013.
  - It holds the reconciled
    [weightedSemaphore](./weighted-semaphore/domain-analysis/weightedSemaphore/README.md)
    model and its runners.
- gobreaker: (no contract) - `gobreaker/late-completion-readiness/` holds
  only JSON and a Go probe template: the fixture for
  `tools/gobreaker_late_readiness.py`.
  - That tool is a [readiness probe](../README.md#glossary) for the
    late-completion contract. The probe's result: gobreaker does not fit,
    because it starts a new "generation" whenever its state changes or its
    counting interval expires, and it has no terminal state. Late results are
    dropped by generation, which is outside the terminal and idle-resource
    contract.
  - The probe uses the archived source in
    `docs/evidence/identity-postreview/runs/gobreaker-identity/input/`, so it
    clones nothing; Go may still fetch modules on a cold cache. Only its
    `gobreaker.go` is pinned by SHA-256.
  - Run it with `python3 tools/gobreaker_late_readiness.py` (needs Go). CI
    runs it in the step "reusable late-completion oracle and addrConn
    reference" (job `consistency`).

## Child contracts

`examples/device-connection/README.md` is the component's requirements
document. The run manifests in
`device-connection/domain-analysis/device-connection/run1/` and `run2/` list
it in their `watchPaths`, and a blind Part B session reads it. The code
contract lives here for two reasons:

- the main one: code-observed facts in that README would leak code
  knowledge into the blind pass;
- a secondary one: they would make both manifests stale, although no CI
  step checks these two manifests.

### device-connection

#### Overview

Every statement below is observed in code
(`device-connection/device_connection.py`), not taken from the requirements.
This contract does not settle any divergence from R-01..R-09; the analysis
questions do that.

#### Interface

- `State` — an `Enum`: `DISCONNECTED`, `CONNECTING`, `CONNECTED`,
  `RECONNECTING`, `FAILED`.
- `DeviceInfo` — a `dataclass` with `device_id: str` and `address: str`.
- `ConnectionError`, `ConnectionTimeout` — `Exception` subclasses. The local
  `ConnectionError` shadows the Python built-in.
- `DeviceConnection` — constructed as
  `DeviceConnection(device, max_retries=3, connect_timeout=5.0, min_uptime=2.0, base_backoff=1.0)`.
  - Methods: `async connect()` and `async disconnect()`.
  - Public attributes: `device`, `max_retries`, `connect_timeout`,
    `min_uptime`, `base_backoff`, `state` and `retry_count`.
- `_connect_loop`, `_attempt_connection`, `_simulate_connect`,
  `_start_uptime_timer` — internal helpers.

#### Invariants

- `connect()`:
  - It returns without effect in `CONNECTED` or `CONNECTING`.
  - It raises `ConnectionError("device is in FAILED state")` in `FAILED`.
  - Otherwise it resets `_should_stop = False`, sets `CONNECTING` and starts
    a new `_connect_loop` task, which replaces `_connect_task`.
  - In `RECONNECTING` it starts a second loop without canceling the running
    one. Two loops can then run concurrently, and `disconnect()` cancels only
    the newest.
- `disconnect()` sets `_should_stop`, cancels and clears `_connect_task` and
  `_uptime_task`, then sets `DISCONNECTED` in every state, including `FAILED`.
- `_connect_loop` runs while `retry_count < max_retries and not _should_stop`:
  - Success sets `CONNECTED`, resets `retry_count` to 0 and starts the uptime
    timer.
  - Failure increments `retry_count`. At `retry_count >= max_retries` the
    loop sets `FAILED` and returns.
  - Otherwise it sets `RECONNECTING` and sleeps
    `base_backoff * 2**(retry_count-1)` plus `uniform(0, backoff*0.5)` jitter.
- Observed defect (not a guarantee), the reconnect hang: after `FAILED` → `disconnect()` → `connect()`,
  `retry_count` still equals `max_retries`. The loop condition is false at
  once, so the state stays `CONNECTING` forever.
- `_attempt_connection` turns `asyncio.TimeoutError` from
  `asyncio.wait_for(..., timeout=connect_timeout)` into `ConnectionTimeout`.
- The uptime timer only sleeps for `min_uptime` and has no observable effect.

#### Side Effects

- Creates the `asyncio` tasks `_connect_task` and `_uptime_task`.
- Calls `asyncio.sleep` for backoff and simulated latency.
- Uses `random` for jitter, latency and simulated failure: about 30 % of
  attempts fail (`random.random() > 0.7` raises).
- Opens no real network connection.

#### Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../README.md#system-verification)).

No automated check covers this folder. `device_connection.py` and the runs in
`device-connection/domain-analysis/` are not run by any test or CI step.

`tests/device-connection/` holds a separate, frozen pair of run sidecars. It
is not a copy of this folder's runs. `tools/selftest/run_selftest.py` uses it
as the ensemble-convergence baseline and expects 93.8 % convergence over 32
aligned cells. To compare this folder's two runs yourself:

- Run: `python3 tools/ensemble_convergence.py examples/device-connection/domain-analysis/device-connection/run1/analysis.json examples/device-connection/domain-analysis/device-connection/run2/analysis.json`

Expected result: 100 % behavioural convergence over 5 × 21 = 105 aligned
cells, exit 0, matching [CONVERGENCE.md](./device-connection/CONVERGENCE.md)
and the root README.
