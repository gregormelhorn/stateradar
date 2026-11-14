# addrConn F-09 transfer and delegated evaluation decisions

The second real-component cancellation-leak binding uses grpc-go v1.18.0 at
`a02b0774206b209466313a0b525d2c738fe407eb`. It drives the real addrConn into
backoff after a failed dial, locally tears it down and checks its worker and
timer while the actual parent ClientConn is still alive. Disposable overlays
add a controllable backoff timer, a scheduling barrier and an observer at
return from resetTransport; they do not set addrConn state or fake completion.

## Executed result

`comparison.txt` and `runs/` retain the first full measurement:

| Run | Result |
|---|---|
| Pristine baseline, six scoped cells, race detector | 10 repetitions, 60 cell executions, all pass |
| Timer canary: omit timer.Stop on canceled wait | KILLED at BackoffWaiting x TearDown |
| Worker canary: wait for parent after local cancellation | KILLED at BackoffWaiting x TearDown |
| F-09: omit local ac.cancel in tearDown | KILLED at BackoffWaiting x TearDown |
| State-only weak controls, each of the three variants | SURVIVED, 10 complete repetitions each |

The generic runner verifies completed discovery and declared-cell failures,
executes each canary once and blocks dependents unless its prerequisite is
KILLED. Both resource coordinates have an independent sensitivity probe. The
canaries and main fault are three variants of F-09, not three new fault classes.
The registered cancellation-leak binder now has semaphore and addrConn bindings.
This is a bounded six-cell projection, not full coverage of the 182-cell pilot.

## Observed failures and limits

- `initial-build-blocked.jsonl`: the first harness used WithContextDialer, which
  does not exist in this historical version. Discovery correctly blocked the
  compile failure; this was not counted as a kill. The fixture now uses the
  pinned WithDialer API already used by upstream's own test.
- `resource-red.txt`: before adding the post-teardown resource assertions, the
  timer canary failed only a later cell. The declared cell had not detected it,
  so the general runner reported 0 killed, 3 blocked and skipped dependents.
  Adding the resource follow-up to the declared cell produces the three valid
  kills recorded in `comparison.txt`.
- `model-checks.txt`: the scoped shutdown guard partition has executed overlap/
  coverage red probes and a green proof; asynchronous scheduling is explicitly
  not a formal liveness theorem. The actual decision validator rejects an
  omitted Q-16 in a disposable copy.
- `fixture-selftest.txt`: empty Go discovery and omitted decision coverage are
  rejected; exact decision attribution/status survives indexing.
- `reachability-red.txt`: the separate final graph check caught a missing
  terminal declaration in the matrix. The matrix now carries the supported
  terminal annotation, and the fixture runner invokes reachability in CI.

The scheduling barrier makes Pending observable before allowing the real
select to proceed. Watchdogs bound the experiment only. A negative result is a
completed test failure; all failed runs clean up after verdict collection, so
parent cancellation during cleanup cannot turn into a passing local-cancel
observation. The timer is a controlled dependency, not a wall-clock leak proof.
No arbitrary scheduler ordering or production latency guarantee is claimed.

## Decisions

The user instructed: “die offenen fragen analysieren und dann nach deinen
empfehlungen beantworten”. This explicitly delegates adoption of the reviewed
recommendations for this evaluation. It is recorded as owner authorization,
with Codex as recommendation author; no per-question verbatim owner response
or upstream maintainer decision is fabricated.

All Q-01..Q-16 are ANSWERED in the separate current evaluation records:
[resolution and rationale](../../../examples/grpc-addrconn/domain-analysis/addrConnBackoff/resolution.md).
The broad implementation status remains pending. Notable refinements from the
historical proposals are generation-safe resets (Q-03), first-status versus
stable health-watch silence (Q-08), terminal no-op wrapper semantics (Q-09),
explicit drain/abrupt cleanup and correction of the parent-context assumption
(Q-11), attempt-scoped cleanup (Q-12), and saturating keepalive growth (Q-16).
No historical question or blind result was rewritten.

## Full acceptance

```sh
bash docs/evidence/addrconn-f09/scripts/full_gates.sh --checkout /path/to/pinned/grpc-go
```

This adds the pinned fixture, source/decision checks, scoped model guard proof
and fixture selftests to all previous generic-canary, semaphore, mutation,
model, pack, model-routing, finding and accounting gates. The complete logs
are retained with the implementation and harness-anchor reconciliation commits.
No new model API calls or cost comparison are involved.

The harness anchor is reconciled to implementation commit `ff2263aa`.
`harness-staleness-red.txt` retains the real stale-anchor rejection after the
implementation commit. `reconciled-gates.txt` records the complete successful
rerun after updating the anchor; no behavior or cell expectations changed.
