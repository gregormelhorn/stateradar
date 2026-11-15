# Reusable late-completion oracle and addrConn reference

The shared `tools/late_completion.py` consumes a declared trace profile plus
actual adapter observations. It checks both completion/termination orderings,
terminal state/publication, absence of new effects after termination and
exactly-once resource release. The language-specific adapter does not choose
behavioral verdicts. See [contract and guide](../../late-completion.md).

The first real-component reference uses grpc-go v1.18.0 at
`a02b0774206b209466313a0b525d2c738fe407eb`. The historical source stays clean.
An exact-match patch in `examples/grpc-addrconn/late-completion/evaluation-patch.json`
implements accepted DR-001 in disposable evaluation copies: reject publication
under the addrConn lock, close the late transport outside that lock, and reject
connectivity changes after Shutdown. DR-001 is recorded as partially implemented
because this scoped acceptance does not establish complete component conformance.
Other addrConn decisions remain pending. Historical analyses are immutable.

## Executed comparison

| Evidence | Result |
|---|---|
| Historical source, 5 repetitions per scenario | Both late-publication and late-notification cases fail; normal ordering passes |
| Corrected evaluation source, 3 scenarios x 10 | All pass with race detector |
| State-only canary | Only terminal state obligation fails |
| Publication-only canary | Only post-terminal publication obligation fails |
| Output-only canary | Only post-terminal effect obligation fails |
| Resource-only canary | Only exactly-once release obligation fails |
| Remove publication guard | Fails Shutdown x CompleteTransport |
| Remove terminal connectivity guard | Fails Shutdown x NotifyReady |
| Independent full replay of each variant | Declared scenario fails in 5 repetitions |
| Weak replay of each variant | Survives 10 repetitions |
| Weak-canary generic control | First canary survives; five dependents BLOCKED without execution |
| Existing BackoffCancel and four state-transition tests | 5 named subtests x 5 on both historical and corrected source, isolated recording builder, race detector |
| Prior addrConn backoff cells on corrected source | All 6 cells x 10 repetitions pass |

The generic runner executes the four prerequisite canaries once per invocation
and then the two F-04 mutants, with exact suite cardinality and correct-cell
verdicts. The canaries form a dependency chain so both mutants require all four
observations. The separate replay verifies independence by requiring exactly
one failure cause for each canary. A whole-process timeout remains BLOCKED.

## Retained red and green evidence

- `design.md`: scope and model recorded before the evaluation fix.
- `oracle-red.txt`: an accept-without-validation stub failed 15 assertions;
  `oracle-green.txt` records the implemented oracle's seven passing test groups.
- `historical-red.txt`: actual historical behavior failures, before the fix.
- `evaluation-green.txt`: corrected source, 30 executed scenario traces.
- `mutants.txt`: final generic mutation run with four independent canaries.
- `recording-balancer-race.jsonl`: intermittent race in the unchanged historical
  recorder helper, observed on the corrected evaluation source.
- `pristine-regression-repeat.jsonl`: ten pristine-source repetitions passed;
  the race did not reproduce in that sample. This is not proof of race absence.
- `repeat-audit.txt`: each of the six variants fails its declared scenario in
  5/5 repetitions; the audit rejects a passing baseline substituted as a mutant
  (`repeat-audit-red.txt`).
- `runs/`: final repeated historical/baseline/mutant observations, raw Go test
  output, exact canary causes, weak controls and upstream/backoff regressions.
- `implementation-gates.txt`: complete final gate run before the implementation
  commit. `reconciled-checks.txt` records targeted anchor/replay checks after
  updating only the manifest anchors; executable sources are unchanged.
- `interrupted-driver.txt`: all child gates completed, but editing the parent
  shell script during execution invalidated its final read position (exit 127).
  That run is not counted as successful acceptance; the frozen final script is
  rerun in full.

The generic and adapter selftests additionally reject empty test discovery,
missing/duplicate records, wrong order/identity, premature parent teardown,
inconsistent resource types and disappearing effects. All prior pack gates
are included in the complete acceptance script:

```sh
LATE_EVIDENCE_DIR=/tmp/late-evidence bash docs/evidence/late-completion/scripts/full_gates.sh --checkout /path/to/pinned/grpc-go
```

## Historical regression fixture isolation

One repeated run failed under the race detector at the historical test helper:
`stateRecordingBalancer.Build` writes its embedded Balancer at line 490, while
`HandleSubConnStateChange` reads it without that lock at line 468. A shared
builder returns itself across connections, allowing old callbacks to race a
new Build. The production DR-001 patch does not change either line. Ten pristine
repetitions did not reproduce the intermittent race, which remains recorded.

The regression adapter registers a builder that snapshots the notifier under
its existing mutex and returns a fresh recorder per ClientConn. This uses the
published balancer registration/Build seam (`balancer/balancer.go:47,161`). No
historical test file, assertion, expectation, recorder method, or production
code is changed by this adapter. The same adapter runs on both historical and
corrected source; each must discover and pass all five tests in five repetitions.
This is explicitly an adapted regression fixture, not a claim that the original
historical test harness is race-free. The feature's own probe uses separate
per-scenario observers and does not depend on that historical recorder.

## Limits

This is one validated adapter and three scoped scenarios with a controlled idle
transport. It is not a second-component transfer proof for the new oracle, a
complete 182-cell addrConn replay, a fresh blind pilot, production grpc-go change,
real-transport leak measurement, or coverage of active-stream drain and health
monitoring. The prior F-09 feature has two independent real-component bindings;
that evidence does not imply this new late-completion feature does too.
No model API calls or new model-cost comparison are involved.

Both harness manifests are reconciled to implementation commit `7248be61`.
`anchor-red.txt` retains their observed stale-anchor rejections after that commit.
Only manifest anchors and reconciliation evidence change afterwards; the
executable implementation remains the one from the full successful gate run.
