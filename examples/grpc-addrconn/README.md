# grpc-addrconn — grpc-go addrConn local backoff cleanup

Part of [examples](../README.md).

## Overview

An `addrConn` is one subchannel to one address inside a
[grpc-go](https://github.com/grpc/grpc-go) `ClientConn`. "Local" cleanup is
cleanup triggered by the addrConn itself, not by tearing down the parent
ClientConn.

This example is a source-pinned mutation benchmark for the
[F-09 fault class](../../README.md#glossary) (cancellation leak, defined in
[`formats/rules.toml`](../../formats/rules.toml)). It runs the real grpc-go
v1.18.0 code at commit `a02b0774206b209466313a0b525d2c738fe407eb`.

The benchmark measures suite strength, not an upstream bug. The local
no-transport backoff path already meets its resource contract: the pristine
baseline passes all six cells. The question is whether the six-cell suite
detects two F-09 [canaries](../../README.md#glossary) and the F-09 fault
[mutant](../../README.md#glossary) `omit-local-cancel`, and whether a deliberately weak,
state-only suite lets all three survive.

The [`late-completion/`](#late-completion) fixture is a second, separate use of
the same pinned checkout. It reproduces a real completion/shutdown race and
evaluates this component's DR-001 against it.

- No upstream code is changed in this repository.
- The runners work on disposable copies of the checkout. Go overlays add
  scheduling hooks, controllable timers and observation points to those
  copies only.
- The fake dial fails without opening a network connection.
- The real parent ClientConn stays alive throughout the assertions, so local
  cleanup cannot be credited to parent teardown. The `wait-for-parent` canary
  detects exactly that mistake.

### The six-cell projection

The benchmark checks a [projection](../../README.md#glossary) of the full
model, that is, a reduced slice of it: three states × two events
(`TearDown`, `ObserveWorker`), six cells in total. See
[`scope.md`](domain-analysis/addrConnBackoff/scope.md).

- The three states are an already-waiting backoff worker (`BackoffWaiting`),
  local shutdown pending (`ShutdownPending`), and shutdown completed
  (`ShutdownStopped`).
- The projection excludes established transports, health monitoring, reset
  races, resolver updates and dial-publication races.
- `scope.md` states the preconditions, source observations, resource
  obligations and coverage limits.

### Canaries and the F-09 fault

A canary is a deliberate mutant that proves the suite can observe one kind of
failure. Resource release has two parts here, the timer and the worker, and
each part has its own canary:

- `omit-backoff-stop` leaves the timer active, although the worker returns.
- `wait-for-parent` stops the timer, but keeps the worker alive until the
  parent tears down.

The F-09 fault `omit-local-cancel` drops the local cleanup trigger.

- The mutants run in a `requiresProjection` chain (see
  [Executed projection dependencies](../../docs/fault-mutants.md#executed-projection-dependencies)):
  `omit-backoff-stop` → `wait-for-parent` → `omit-local-cancel`.
- `omit-backoff-stop` is self-proving: its `requiresProjection` names the
  projection it proves itself (`timer_release`), so its own KILL bootstraps
  that projection.
- All three must fail the cell `BackoffWaiting x TearDown` in a fully
  completed suite.
- The state-only weak suite deliberately survives all three.

<a id="two-manifests"></a>

### Analysis and harness manifests

The folder has three [manifests](../../README.md#glossary):

- `domain-analysis/addrConnBackoff/manifest.json` (the analysis manifest)
  pins the upstream grpc-go source.
- `harness-manifest.json` independently watches the committed pack harness,
  model and decision files.
- `late-completion-manifest.json` watches the late-completion fixture; see
  the [late-completion contract](#late-completion).

`tools/addrconn_f09.py` checks the first two, plus the
[sidecar](../../README.md#glossary) via `tools/dsc_check.py`, before any Go
run.

## Interface

The two runners live in [`tools/`](../../tools/README.md), but this folder is
their only input. This README owns the runners' behaviour; `tools/README.md`
only lists them.

- `tools/addrconn_f09.py` — the backoff benchmark runner. Without options it
  clones grpc-go into a temporary directory.
  - `--checkout PATH` — use this clean, pinned checkout instead of cloning.
  - `--output-dir PATH` — write evidence here instead of a temporary
    directory.
  - `--prepare-only DIR` — prepare the component in `DIR`, generate and check
    the mutant variants, then stop without running Go.
- `tools/addrconn_late.py` — the late-completion runner. It takes
  `--checkout PATH` and `--output-dir PATH` with the same meaning. Its
  fixture is documented under [late-completion](#late-completion).
- `check_model.py` — a scoped z3 check of one dispatch guard and of the
  decision records.
  - Its single positional argument is the pinned grpc-go checkout.
  - `tools/addrconn_f09.py` runs it with the same Python interpreter.
  - It reuses `verify_records` and `ANALYSIS` from that runner.
- `tests/backoff_test.go.txt` — the Go probe, which defines `TestRadarCells`
  and the weak, state-only `TestRadarWeak`.
- `tests/run.py` — runs the probe. Both runners copy `tests/` into the
  disposable checkout as `stateradar/`.
  - Arguments: `--analysis DIR` (required), `--weak` (run `TestRadarWeak`
    instead of `TestRadarCells`), `--count N` (default `1`) and
    `--output FILE`.
  - Overlay: `stateradar/backoff_test.go.txt` is overlaid as
    `radar_backoff_test.go`, and `clientconn.go` is replaced by a patched
    copy that inserts scheduling hooks at three source anchors.
  - Output: one `CELL FAIL <state> x <event>` line per failed cell (for
    example `CELL FAIL BackoffWaiting x TearDown`) and one
    `CELL SUITE: 6 cells checked, <n> failed` line per repeat. The weak
    suite prints `CELL SUITE: 1 cells checked, 0 failed` only when it passes.
  - Exit code: the `go test` exit code once
    [discovery](../../README.md#glossary) is complete; 1 with a message for
    the conditions under [Invariants](#testsrunpy).
- `harness-manifest.json` — holds `analyzedSha` and the
  [`watchPaths`](../../README.md#glossary) of the committed pack harness:
  `tools/addrconn_f09.py`, `tests/`, `check_model.py` and, from
  `domain-analysis/addrConnBackoff/`, `analysis.json`, `decisions/`,
  `resolution.json`, `scope.md`, `fault-mutants.json`,
  `mutant-generation.json`, `disposition-matrix.md` and `as-is.machine.mmd`.
- `domain-analysis/addrConnBackoff/manifest.json` — pins the upstream source:
  `analyzedSha` is the grpc-go commit and `watchPaths` is `clientconn.go`.
  `tools/dsc_check.py` uses it to check source citations and staleness.
- `late-completion-manifest.json` — holds `upstreamSha`, `analyzedSha` and
  the `watchPaths` of the late-completion fixture (listed under
  [late-completion Invariants](#late-completion-invariants)).
- Subdirectories:
  - late-completion: [late-completion contract](#late-completion) - the
    DR-001 completion/shutdown fixture
  - tests: (test-only) - six-cell backoff suite
  - domain-analysis: (no contract) - analysis artifacts (scope, matrix,
    decisions, resolution, mutant configuration); no source code

## Invariants

### check_model.py

A dispatch guard is the condition that selects a branch. For each guard,
z3 answers two questions: can both branches apply (overlap), and can neither
apply (gap)? z3 `sat` means a counterexample (overlap or gap) exists, `unsat`
means none does. The first row is a [red probe](../../README.md#glossary):
it must fail before the real check counts.

| Condition | Error text | Enforced by |
|---|---|---|
| A red probe (a duplicate guard) gives `(sat, sat)`: an overlap and a gap | `guard red probe did not expose overlap and gap` | `check_model.py` |
| The shutdown guard (`perform = s==0`, `already_shutdown = s∈{1,2}`) gives `(unsat, unsat)`: disjoint and exhaustive | `guard partition failed` | `check_model.py` |
| `verify_records` rejects a copy of `resolution.json` without its last record, and its error message names the expected range Q-01..Q-16 | `question omission accepted` | `check_model.py` |

On success the script prints its own scope:

```text
SCOPED MODEL PASS: 16 attributed answers; 3 projected states; no broad conformance claim
```

"No broad conformance claim" means it says nothing about the full addrConn
model.

### tests/run.py

Violating any condition exits with status 1 and the message shown.

| Condition | Error text | Enforced by |
|---|---|---|
| `--count` is at least 1 | `positive count required` | `tests/run.py` |
| Each of the three scheduling anchors occurs exactly once in `clientconn.go` | `BLOCKED: scheduling anchor absent/ambiguous: <anchor>` | `tests/run.py` |
| Every expected test (and, for the full suite, every cell subtest from `analysis.json`) runs and finishes exactly `--count` times, no `panic:` occurs, and a package-level verdict is present | `BLOCKED: incomplete Go discovery/verdict` | `tests/run.py` |
| The full suite prints `CELL SUITE: 6 cells checked,` exactly `--count` times | `BLOCKED: missing complete cell loop` | `tests/run.py` |

### tools/addrconn_f09.py

Violating any condition stops the runner with the message shown.

| Condition | Error text | Enforced by |
|---|---|---|
| The harness manifest has watch paths and `analyzedSha` is not `WORKTREE` | `unanchored harness manifest` | `verify_harness` |
| No watched path changed since `analyzedSha` | `stale harness manifest: <paths>` | `verify_harness` |
| Records are exactly `Q-01..Q-16`, in order | `decision coverage is not exactly Q-01..Q-16` | `verify_records` |
| Each record is `accepted` and `ANSWERED`, with an authorization and a rationale; `implementation_status` is `partial` for DR-001 and `pending` otherwise | `decision attribution/status missing` | `verify_records` |
| Each record equals its `decisions/DR-*.yaml` | `decision record/index drift` | `verify_records` |
| Each evidence fragment occurs within ±3 lines of its cited line | `decision citation drift: <citation>` | `verify_records` |
| The checkout is at the pinned commit | `wrong grpc-go revision` | `prepare` |
| The checkout tree is clean | `upstream checkout must be clean` | `prepare` |
| `tools/check_fault_mutants.py` exits 0 | `generic canary/fault comparison failed` | `main` |
| Every weak control is `SURVIVED` | `weak control did not survive with complete discovery` | `main` |

- Order: harness, records, `check_model.py`, `tools/dsc_check.py`,
  `tools/check_reachability.py`, `prepare`, then
  `tools/gen_mutant_variants.py` (generate, then `--check`), all before any
  Go run.
- `--prepare-only DIR` copies the checkout with `copytree`, so `DIR` must not
  exist yet.

### tools/addrconn_late.py

The first six rows of the `tools/addrconn_f09.py` table (`verify_harness` and
`verify_records`) also apply here. Fixture-specific checks are under
[late-completion Invariants](#late-completion-invariants).

| Condition | Error text | Enforced by |
|---|---|---|
| The checkout is clean and at the pinned commit | `reference checkout must be clean and exactly pinned` | `main` |
| `upstreamSha` equals the pin, `watchPaths` is not empty, `analyzedSha` is not `WORKTREE` | `unanchored late-completion fixture` | `verify_anchor` |
| The historical source fails exactly `Shutdown x CompleteTransport` and `Shutdown x NotifyReady` | `historical defect was not reproduced at both declared scenarios` | `main` |
| The weak-canary control reports `killed=0 survived=1 errors=0 blocked=5` and exits 1 | `weak canary did not block all dependents` | `main` |
| Each canary fails only its own cell, for its declared cause | `canary did not independently isolate its projection: <causes>` | `main` |

- The weak-canary control runs the mutant chain against the weak suite. The
  first canary must survive there, so all five dependents are BLOCKED
  without running.
- Order: clean/pinned checkout, `verify_harness`, `verify_anchor`,
  `verify_records`, then `check_plan` on `workflow.json`, all before any Go
  run.

## Side Effects

This section is the single description of what the two runners do to the
machine; `tools/README.md` links here.

- Network: without `--checkout`, both runners clone grpc-go:
  `git clone --depth 1 --branch v1.18.0 https://github.com/grpc/grpc-go.git`
  into their temporary directory. CI runs both this way.
- Other git calls (read-only):
  - `git rev-parse HEAD` and `git status --porcelain` in the checkout, to
    check the pin and a clean tree.
  - `git diff --name-only <analyzedSha>..HEAD -- <watchPaths>` in this
    repository, once per watching manifest (`verify_harness`, and for the
    late-completion runner also `verify_anchor`).
- Subprocesses of `tools/addrconn_f09.py`:
  - `command(...)` runs `git`, `check_model.py`, `tools/dsc_check.py`,
    `tools/check_reachability.py`, `tools/gen_mutant_variants.py` and
    `stateradar/run.py` with a 180 s timeout. A non-zero exit raises
    `RuntimeError` with the captured output.
  - `tools/check_fault_mutants.py` also has a 180 s timeout but runs outside
    `command(...)`. On failure only its message from the
    [Invariants table](#toolsaddrconn_f09py) is raised. The output is in
    `generic.txt`.
  - The weak replays run through `run_command` from
    `tools/check_fault_mutants.py`, with the `timeoutSeconds` (120) of
    `fault-mutants.json`. A timeout yields a non-SURVIVED verdict, not an
    exception.
- Subprocesses of `tools/addrconn_late.py`:
  - It calls `command(...)` from `tools/addrconn_f09.py` for `git`, the
    backoff regression and `tools/gen_mutant_variants.py` (generate, then
    `--check`), so these raise with the captured output.
  - The adapter runs (`late/run.py`), the upstream regression `go test` and
    `tools/check_fault_mutants.py` go through `execute(...)`: 180 s timeout,
    no exception on a non-zero exit (only on timeout). Each caller checks
    the exit code.
  - The weak replays run through `run_command`, as in the backoff runner.
- `check_model.py` copies the analysis folder into a
  `tempfile.TemporaryDirectory` and rewrites `resolution.json` in that copy
  only. Committed files stay unchanged.
- `tests/run.py` writes a patched `clientconn.go` and `overlay.json` into a
  `tempfile.TemporaryDirectory(prefix='addrconn-overlay-')`, then runs
  `go test -race -json` with `-overlay` in the copied checkout (120 s
  subprocess timeout). It sets `STATERADAR_ANALYSIS` to the `--analysis`
  folder, from which the probe reads `analysis.json`. With `--output FILE` it
  writes the raw `go test` output there.
- Both runners run `go test` only in disposable copies of the checkout.
- `tools/addrconn_f09.py` writes to `--output-dir`, or a temporary directory
  by default:
  - `baseline.txt` and `baseline.go.jsonl` (6 cells × 10 repeats);
  - `generic.txt` (the generic canary and fault run);
  - `<mutant-id>.weak.go.jsonl` per mutant (weak suite, 10 repeats);
  - `results.json`, only when every check passes.
- With `--prepare-only DIR`, `tools/addrconn_f09.py` leaves the prepared
  component in `DIR`: the checkout copy, `stateradar/` with the generated
  variants in `stateradar/mutants/`, and `domain-analysis/addrConnBackoff/`.
- `tools/addrconn_late.py` writes its evidence as listed under
  [late-completion Side Effects](#late-completion-side-effects).

## Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).

Start with the cheap selftest. It needs only Python: it replaces `go` with a
fake script, reads committed files and uses no network.

- Run: `python3 tools/selftest/test_addrconn_f09.py`

Prerequisites for the runners:

- `check_model.py` needs `z3` (from the dev requirements).
- A Go toolchain with `go test -race` support. This example has no `go.mod`
  of its own: `go test` runs inside the grpc-go checkout and uses its
  `go.mod`/`go.sum` with `-mod=readonly`. CI installs the Go version in
  `examples/weighted-semaphore/go.mod` (1.24.0).
- `git`, for the clone and the read-only checks under
  [Side Effects](#side-effects).
- For the `--checkout` pair, clone once; the checkout must stay clean and at
  the pinned commit:

  ```sh
  git clone --depth 1 --branch v1.18.0 https://github.com/grpc/grpc-go.git <dir>
  ```

Run one of the two pairs:

- `--checkout` pair (offline after one clone; a cold Go module cache still
  needs network):
  - Run: `python3 tools/addrconn_f09.py --checkout <dir> --output-dir <out>/f09`
  - Run: `python3 tools/addrconn_late.py --checkout <dir> --output-dir <out>/late`
- No-argument pair (clones each time):
  - Run: `python3 tools/addrconn_f09.py`
  - Run: `python3 tools/addrconn_late.py`

CI runs the backoff benchmark in
[`.github/workflows/pack-ci.yml`](../../.github/workflows/pack-ci.yml):

- CI step "pinned addrConn backoff slice and decisions" (job
  `consistency`):
  - Run: `python3 tools/selftest/test_addrconn_f09.py`
  - Run: `python3 tools/addrconn_f09.py`

The late-completion CI step is listed under
[late-completion Verification](#late-completion-verification).

## Evidence notes

### Decisions

All 16 historical open questions ([Q-nn](../../README.md#glossary)) have
accepted answers, recorded as DR-001..DR-016 in
[`resolution.md`](domain-analysis/addrConnBackoff/resolution.md) and
[`resolution.json`](domain-analysis/addrConnBackoff/resolution.json). DR and
Q numbers are per component analysis (see the
[glossary](../../README.md#glossary)); DR-001 here is this component's
decision.

- The owner authorized adopting the reviewed recommendations. Each record
  carries this authorization, a rationale and checked source fragments.
- DR-001 is `partial`: its evaluation patch is applied to disposable copies
  by [`late-completion/`](#late-completion) and covers three scenarios, not
  the whole component.
- DR-002..DR-016 are decided but `pending` (not implemented).
- The original OPEN questions stay unchanged in
  [`tests/benchmarks/grpc-go-2669/open-questions.md`](../../tests/benchmarks/grpc-go-2669/open-questions.md),
  which `resolution.json` names as `historical_questions`.

## Child contracts

Two [manifests](../../README.md#glossary) watch folders of this example:
`late-completion-manifest.json` watches `late-completion/`, and
`harness-manifest.json` watches `tests/`, `check_model.py` and the committed
analysis files. A file committed under a watch path makes its manifest stale,
which fails `tools/addrconn_late.py` or `tools/addrconn_f09.py` respectively.
Re-stamping a manifest only to admit a README would be
[reconcile-lite](../../README.md#glossary), which the root README forbids
([Adopting it in a brownfield repo](../../README.md#adopting-it-in-a-brownfield-repo)).
The `late-completion/` contract therefore lives here. `tests/` is test-only
and is documented under [Interface](#interface).

### late-completion

<a id="late-completion-overview"></a>

#### Overview

`late-completion/` is a reference binding of the shared, language-neutral
[late-completion](../../README.md#glossary) [oracle](../../README.md#glossary)
([`tools/late_completion.py`](../../tools/late_completion.py), described in
[`docs/late-completion.md`](../../docs/late-completion.md)) to the real
grpc-go `addrConn` at the pinned SHA. It is a fixture, not a standalone
program. It covers this component's DR-001
([`DR-001.yaml`](domain-analysis/addrConnBackoff/decisions/DR-001.yaml)).
Its scope is "three named scenarios, not the 182-cell historical matrix"
(`scenario-scope.json`, field `boundary`). That matrix is the full addrConn
analysis (7 states × 26 events) of the
[`grpc-go-2669` benchmark](../../tests/benchmarks/grpc-go-2669/summary.md).

`tools/addrconn_late.py` runs it as follows:

1. It copies the pinned checkout to a disposable folder, copies this folder
   in as `late/`, and copies the oracle in as `late/late_completion.py`.
2. On the historical source, it reproduces both completion/shutdown races and
   runs five named upstream subtests of grpc-go's `Test`:
   `Test/BackoffCancel`, `Test/StateTransitions_SingleAddress`,
   `Test/StateTransitions_ReadyToTransientFailure`,
   `Test/StateTransitions_TriesAllAddrsBeforeTransientFailure` and
   `Test/StateTransitions_MultipleAddrsEntersReady`.
3. It applies DR-001 (`evaluation-patch.json`) to the disposable copy and
   checks that all three scenarios pass. It runs the same upstream subtests
   again, and runs the six-cell backoff regression on the corrected source.
4. It checks the publication and notification guards with mutants.

The mutants are two guard-removal fault mutants of the
[F-04 fault class](../../README.md#glossary) (sneak path) plus four canaries
(two F-04, one F-03 output fault, one F-09); each canary isolates one failure
cause.

The mutants run in a `requiresProjection` chain (see
[Executed projection dependencies](../../docs/fault-mutants.md#executed-projection-dependencies)).
A mutant runs only after the canary that proves its required projection has
been KILLED; a SURVIVED or BLOCKED canary BLOCKS all its dependents. Here the
chain is `state-canary` → `publication-canary` → `effect-canary` →
`resource-canary` → both guard-removal mutants. `state-canary` is
self-proving: it requires `terminal`, the projection it proves itself.

As in the backoff benchmark, the parent ClientConn stays alive. An idle fake
transport and controlled barriers expose real addrConn behaviour; this is not
a full transport implementation test.

<a id="late-completion-interface"></a>

#### Interface

- `run.py` — the adapter CLI. Its arguments are `--analysis <dir>`
  (required), `--weak`, `--count <n>` (default `1`) and `--output-dir <dir>`.
  - It imports `EvidenceError`, `report` and `validate_profile` from the
    copied `late_completion` module.
  - `--weak` is not passed to Go. It only switches the oracle call
    `report(profile, traces, count, weak)` to the weak, state-only suite.
  - The exit code comes from `report(...)`: 0 for pass, 1 for an oracle
    failure. On the historical source and on mutants, 1 is the expected
    result. Evidence errors give 2.
- `profile.json` — the oracle profile.
  - It sets `terminalState` `SHUTDOWN`, `acceptedState` `READY` and
    `acceptanceEffect` `READY`. Its `decision` field points to DR-001.
  - It declares three cases, each with a `checkpoint` and an `order`:
    - `late-publication` (`Shutdown x CompleteTransport`, `after-create`);
    - `late-notification` (`Shutdown x NotifyReady`, `before-ready`);
    - `normal-completion` (`Connecting x CompleteTransport`,
      `after-create`).
- `probe_test.go.txt` — the Go probe, overlaid in place of
  `late_completion_test.go`.
  - It defines `TestLateCompletionEvidence`, the hooks `lateFactory`,
    `lateCheckpoint`, `lateSettled`, `lateReturned` and `lateEffect`, and the
    idle fake transport `lateTransport`.
  - It prints one `LATE TRACE <json>` line per case and repeat. The JSON
    has `case`, `repeat` and `steps`; each step has `action`, `state`,
    `published`, `releaseCount`, `effects`, `resource` and `parentAlive`.
- `regression_fixture_test.go.txt` — overlaid as
  `zz_late_regression_test.go` for the upstream regression run.
  - It registers the isolated `lateRegressionBuilder` recorder.
  - `tools/addrconn_late.py` runs it in the disposable copy, with
    `regression-overlay.json` as the overlay:

    ```sh
    go test -mod=readonly -race -count=5 -timeout=90s -overlay ... -run '^Test/(BackoffCancel|StateTransitions_)' -json .
    ```

- `evaluation-patch.json` — the DR-001 evaluation edits, applied by
  `apply_evaluation_patch` in `tools/addrconn_late.py`.
  - One edit adds a Shutdown guard to `updateConnectivityState`.
  - The other closes a late `newTr` before publication.
- `fault-mutants.json`, `mutant-generation.json` — the configuration that
  `tools/check_fault_mutants.py` and `tools/gen_mutant_variants.py` consume.
  - Six mutants: the guard-removal mutants `omit-publication-guard` and
    `omit-terminal-guard` (F-04), plus four canaries: `state-canary` and
    `publication-canary` (F-04), `effect-canary` (F-03) and
    `resource-canary` (F-09).
  - `mutant-generation.json` declares the four projections (`terminal`,
    `publication`, `effect`, `resource`) and a `requiresProjection` for all
    six mutants; both guard-removal mutants require `resource`.
  - The variants `late/mutants/*.go.txt` are not in the repository.
    `tools/gen_mutant_variants.py` creates them in the disposable copy and
    then checks them with `--check`.
  - The `testCommand` is `python3 late/run.py --analysis {analysis_dir}`,
    and `expectedCells` is 3.
- `scenario-scope.json` — the trace scope with citations.
- `workflow.json` — the execution plan, which `check_plan` in
  `tools/check_late_workflow.py` checks.

<a id="late-completion-invariants"></a>

#### Invariants

`late-completion-manifest.json` watches these paths; a committed change to
any of them after `analyzedSha` stales the fixture and fails
`tools/addrconn_late.py`, and with it CI:

- `tools/late_completion.py`, `tools/addrconn_late.py` and
  `tools/check_late_workflow.py`;
- `examples/grpc-addrconn/late-completion`;
- `docs/evidence/late-completion/design.md`;
- `tools/selftest/test_late_completion.py`,
  `tools/selftest/test_late_adapter.py` and
  `tools/selftest/test_late_workflow.py`;
- `prompts/04-testgen.md`, whose Step 3 defines `scenario-scope.json` and
  `workflow.json`; an edit to the Testgen prompt therefore stales the fixture.

| Condition | Error text | Enforced by |
|---|---|---|
| Each adapter anchor occurs exactly once in `clientconn.go` | `missing/ambiguous adapter anchor: <anchor>` | `run.py` |
| `--count` is at least 1 | `positive repetitions required` | `run.py` |
| `go test` exits 0; each `TestLateCompletionEvidence/<id>/<r>` runs and passes exactly once; a package-level pass is present | `incomplete/failed adapter execution` | `run.py` |
| `evaluation-patch.json` has `upstreamSha` equal to the pin and `decision` `DR-001` | `patch source/decision mismatch` | `apply_evaluation_patch` |
| Each patch `match` occurs exactly once | `missing/ambiguous evaluation patch anchor` | `apply_evaluation_patch` |
| No watched path changed since `analyzedSha` | `stale late-completion manifest: <paths>` | `verify_anchor` |
| `tools/check_fault_mutants.py` passes on the full suite | `generic late-completion mutations failed` | `main` |
| Each mutant's direct replay fails its declared cell | `wrong-cell replay` | `main` |
| Each mutant's weak replay survives | `weak suite failed/incomplete: <output>` | `main` |
| `go test` exits 0; the parent `Test` and the five named subtests each start and pass exactly 5 times | `upstream regression discovery/failure; see <label>-upstream.go.jsonl` | `upstream_regressions` |

- `run.py` turns evidence errors (`EvidenceError`, `ValueError`, `OSError`,
  `subprocess.TimeoutExpired`) into `BLOCKED: ...` and exit code `2`.
- `tools/addrconn_late.py` raises with the adapter output when `run.py`
  exits with an unexpected code (`require_adapter`).

<a id="late-completion-side-effects"></a>

#### Side Effects

- `run.py` writes a patched `clientconn.go` and `overlay.json` into a
  `tempfile.TemporaryDirectory(prefix='late-overlay-')`. Upstream files stay
  unchanged, because `go test -overlay` replaces them only for the test run.
- `run.py` runs `go test` in the copied checkout with a 120 s subprocess
  timeout and the environment variables `LATE_PROFILE` and `LATE_REPEATS`:

  ```sh
  go test -mod=readonly -race -count=1 -timeout=90s -overlay ... -run ^TestLateCompletionEvidence$ -json .
  ```

- With `--output-dir`, `run.py` writes three files:
  - `go.jsonl`;
  - `observations.json`, the parsed `LATE TRACE` lines;
  - `execution.json`, which holds `formatVersion`, `count`, `weak`, `goExit`
    and SHA-256 digests of the source, profile, adapter, probe, oracle,
    `go.jsonl` and `observations.json`.
- `tools/addrconn_late.py` writes `regression-overlay.json` into the
  disposable `late/` folder.
- `tools/addrconn_late.py` writes to `--output-dir`, or a temporary directory
  by default:
  - `upstream-source.go.txt`, the unpatched `clientconn.go`;
  - `historical/` and `evaluation/`, each with the `run.py` output files plus
    `verdict.txt`;
  - `historical-upstream.go.jsonl` and `evaluation-upstream.go.jsonl`;
  - `backoff.txt` and `backoff.go.jsonl` (backoff regression on the
    corrected source);
  - `generation.txt`, `generic.txt` and `weak-canary-control.txt`;
  - one folder per mutant, with the `run.py` output files, `verdict.txt`, a
    `weak/` folder and `weak.txt`;
  - `results.json` and `workflow-receipt.json`.

<a id="late-completion-verification"></a>

#### Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).
The prerequisites are those of the parent [Verification](#verification).

- Run: `python3 tools/addrconn_late.py --checkout <dir> --output-dir <out>/late`
- CI step "reusable late-completion oracle and addrConn reference" (job
  `consistency`):
  - Run: `python3 tools/selftest/test_late_adapter.py`
  - Run: `python3 tools/addrconn_late.py`

The same CI step also runs the gobreaker readiness probe and the
late-completion oracle and workflow selftests; those do not touch addrConn.
