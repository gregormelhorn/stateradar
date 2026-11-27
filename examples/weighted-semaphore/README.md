# weighted-semaphore — accepted-decision evaluation copy

Part of [examples](../README.md).

## Overview

This is a copy of `golang.org/x/sync` v0.17.0, with its upstream `LICENSE`,
from upstream commit `04914c200cb38d4ea960ee6a4c314a028c632991`. It is an
evaluation fixture, not an upstream release, production deployment or
upstream-approved policy.

`semaphore/*.go` (except the evaluation tests `decision_*_test.go`),
`errgroup/errgroup.go`, `go.mod` and `LICENSE` were copied from that revision.
`semaphore/semaphore.go` was then modified:

- runtime changes implement DR-001..DR-004 (listed below);
- doc comments state the caller-facing clauses of DR-005..DR-013;
- its package comment says that the copy follows `CONTRACT.md`.

The other copied files, including the original upstream tests, are unchanged.
`errgroup` is present only because the upstream semaphore tests import it.

The four runtime decisions are:

- FIFO progress for zero weight (DR-001);
- negative-argument panic before mutation (DR-002);
- non-corrupting over-release panic (DR-003);
- an immediate explanatory error for an oversized `Acquire` (DR-004).

Only DR-001..DR-004 change behaviour relative to upstream. For example, a
pre-canceled Context with a nonnegative weight still returns `ctx.Err()` as
upstream does.

All thirteen [decision records](../../README.md#glossary) (DR-001..DR-013) are
accepted, and no original question remains open. The evidence is recorded in
three places:

- [Q-01 evidence](../../docs/evidence/semaphore-pilot/resolution-q01/deviation-report.md)
  (DR-001);
- [numeric evidence](../../docs/evidence/semaphore-pilot/resolution-q02-q04/deviation-report.md)
  (DR-002..DR-004);
- [final contract evidence](../../docs/evidence/semaphore-pilot/contracts-q05-q13/README.md)
  (DR-005..DR-013).

[CONTRACT.md](CONTRACT.md) is the normative evaluation contract. The
[current analysis](domain-analysis/weightedSemaphore/summary.md) records the
resolved matrix, cell coverage and reconciliation evidence. The original
upstream pilot in
[docs/evidence/semaphore-pilot](../../docs/evidence/semaphore-pilot/README.md)
is historical. Mutation statistics and the historical baseline are described
in [Evidence notes](#evidence-notes).

## Interface

- `verify_q01.py` — decision-acceptance driver for all thirteen decisions. It
  began as the driver for Q-01 alone, hence the name. Its members:
  - `--count N` — repeats of each decision and schedule test (default 50).
  - `--output-dir PATH` — keeps the Go JSON streams.
  - `--results PATH` — only validates a saved Go JSON stream. Pass the
    `--count` used for the recording (default 50), because every expected
    test must have passed exactly that many times.
  - `validate_results(output, count)` — checks one Go JSON stream.
  - `main()` — the entry point.
- `go.mod` — Go module `golang.org/x/sync` with the directive `go 1.24.0`.
- [CONTRACT.md](CONTRACT.md) — the normative evaluation contract. It
  summarizes DR-001..DR-004 in its preamble and gives the clauses for
  DR-005..DR-013.
- Subdirectories:
  - semaphore: [contract below](#semaphore) - the analyzed `Weighted`
    semaphore, plus the upstream tests and the evaluation decision tests.
  - errgroup: [`./errgroup/README.md`](./errgroup/README.md) - unchanged
    `errgroup.Group`, imported only by `semaphore/semaphore_test.go`.
  - cells: [contract below](#cells) - `run.py` runs the executable matrix
    cells and the interaction-pair orderings through `go test -overlay`.
  - schedule: [contract below](#schedule) - `run.py` runs six checkpointed
    scheduling tests and four fault overlays.
  - domain-analysis:
    [`./domain-analysis/README.md`](./domain-analysis/README.md) - the
    StateRadar model, [sidecar](../../README.md#glossary), DRs and checkers
    of the `weightedSemaphore` component.
  - faults: `faults/weak_test.go.txt` - the weak suite, a deliberately weak
    negative control that checks only the canceled `Acquire` result (no queue
    or capacity assertion) and therefore must miss the fault.
    `tools/semaphore_f09.py` overlays it as `semaphore/f09_weak_test.go` for
    the weak/full comparison on [F-09](../../README.md#glossary) (cancellation
    leak).
  - mutants: `mutants/*.go.txt` - five source mutants consumed by
    `tools/gen_mutant_variants.py` and `tools/check_fault_mutants.py`.

## Invariants

### verify_q01.py

- `--count` below 1 stops argument parsing with the error
  `--count must be positive`.
- Without `--results`, `verify_q01.py` first runs a
  [red probe](../../README.md#glossary): `validate_results('', count)` must
  fail, showing that empty test [discovery](../../README.md#glossary) is
  rejected (`RED-PROBE: empty discovery rejected`); otherwise it raises
  `RuntimeError('empty discovery unexpectedly accepted')`. With `--results`,
  it only validates the given stream and skips this red probe and every
  subprocess.
- Decision results are accepted only if all of these hold; otherwise
  `validate_results` raises `ValueError` starting `Decision discovery/results:`.
  - there are no failures;
  - every name in `EXPECTED` both started and passed exactly `count` times;
  - every record belongs to package `golang.org/x/sync/semaphore`;
  - a package-level pass exists.
- `EXPECTED` holds the DR-001..DR-004 test names and subtests plus
  `regularTests` from
  `docs/evidence/semaphore-pilot/contracts-q05-q13/contracts.json`: 32
  top-level groups and 66 test/subtest names.
- Any failing subprocess (guard, numeric or contract checker, Go test,
  schedule runner or fault probe) stops the run (`check=True`).
- Every subprocess has a timeout, and exceeding it also stops the run:
  - 30 s for each of the three evidence checkers;
  - 120 s for each Go test command and each schedule runner call.

## Side Effects

### verify_q01.py

- Runs three evidence checkers under `docs/evidence/semaphore-pilot/`:
  - `resolution-q01/check_guards.py`;
  - `resolution-q02-q04/check_numeric.py`;
  - `contracts-q05-q13/check_contracts.py`.
- Runs two Go test commands in `examples/weighted-semaphore`, in order:
  - `go test -race -count=N -timeout=60s -run '^TestDR[0-9]{3}' -json ./semaphore`
  - `go test -race -count=1 -timeout=60s ./...`
- Runs the schedule runner, first as `schedule/run.py --count N`, then as
  `schedule/run.py --mode M --count 1` for each of `omit-grant-rollback`,
  `omit-selected-rollback`, `try-bypass` and `zero-charges`.
- Writes `decisions.jsonl`, `schedule.jsonl` and `<mode>.jsonl` only when
  `--output-dir` is given.
- Makes no model or API calls.

## Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).

Prerequisites:

- Go ≥ 1.24.0 (CI installs the `go.mod` version).
- The current-model verifier
  `domain-analysis/weightedSemaphore/verify.py` checks the analysis against
  the code. The CI step that runs it also needs Git history back to the
  manifest's `analyzedSha`, because its staleness check runs `git diff`; CI
  checks out with `fetch-depth: 0`. `verify_q01.py` does not need Git
  history.

Recommended first command, one repeat of every decision test:

- Run: `python3 examples/weighted-semaphore/verify_q01.py --count 1`

CI steps in `.github/workflows/pack-ci.yml`:

- CI step "weighted semaphore accepted decisions" (job `consistency`):
  - Run: `python3 examples/weighted-semaphore/verify_q01.py`
- CI step "weighted semaphore current model and cells" (job `consistency`):
  - Run: `python3 examples/weighted-semaphore/domain-analysis/weightedSemaphore/verify.py`
- CI step "semaphore F-09 observability and weak/full comparison" (job
  `consistency`):
  - Run: `python3 tools/selftest/test_semaphore_f09.py`
  - Run: `python3 tools/semaphore_f09.py`
- CI step "weighted semaphore mutation binding" (job `consistency`):
  - see its three commands in
    [weightedSemaphore Verification](domain-analysis/weightedSemaphore/README.md#verification).
- CI step "mutation verdict and cell rationale selftests" (job `consistency`),
  one of its commands:
  - Run: `python3 docs/evidence/generic-canary/scripts/semaphore_weak_control.py`

## Evidence notes

### Decision acceptance (`verify_q01.py`)

`verify_q01.py` checks guard and coverage obligations. It runs the decision
tests and the scheduled-interleaving tests, each 50 times by default under
`-race`, and
rejects empty or incomplete discovery. It also runs the upstream plus decision
regression suite once and four faulty overlays.

The guard proof covers its stated integer assumptions; behaviour tests verify
the actual notification path. Neither proves all scheduler interleavings or a
production wall-clock latency bound.

### Current model (`verify.py`)

The current-model verifier checks every matrix
[cell](../../README.md#glossary): the executable guarded scenarios, the four
explicit contract limits and all
[interaction-pair](../../README.md#glossary) orderings. It repeats the
executable scenarios ten times under the race detector, demonstrates a
deliberately wrong matrix verdict, checks artifact mutations, and verifies the
retained historical artifact hashes.

The four contract-limit cells are the `UV-Delay` and `UV-ContextFault`
[UV events](../../README.md#glossary) in both states. They record what the
contract does not promise: no fixed latency bound (DR-011) and no guarantee for
a faulty custom Context (DR-009).
They are recorded as limits with an `untestable-via-seam` reason, not as
passing tests.

### Mutation binding

The [sidecar](../../README.md#glossary) `analysis.json` is the
[oracle](../../README.md#glossary) that the
temporary cell suite consumes. A kill requires completed cell discovery and
failure of the targeted cell. Compilation errors, panics before completion and
unrelated failures are reported as blocked.

`tools/check_matrix_mutation.py` prints six cells as not applicable:

- the four contract-limit cells, which have no test;
- the two queued cells `Acquire_WaitersPending × Acquire` (DR-012) and
  `Acquire_WaitersPending × UV-RepeatAcquire` (DR-006). Their disposition is
  `defer (queued)`, and the matrix-mutation operators never mutate that
  disposition.

The supported mutations exercise the remaining 32 cells with 41 matrix
changes. `tools/check_fault_mutants.py` adds five source faults from
`mutants/`. This is bounded evidence, not proof of every fault or
interleaving. Structured rationale for every cell is bound in
`domain-analysis/weightedSemaphore/cell-rationale.json`; see
[the format](../../docs/cell-rationale.md).

### Historical baseline

The original pilot's as-is probes intentionally describe the old behaviour and
remain archived. For that historical baseline, use the original reproduction
driver `docs/evidence/semaphore-pilot/reproduce.py` (see
[its README](../../docs/evidence/semaphore-pilot/README.md#reproduction-and-next-step)).
It must not be repurposed as conformance acceptance of the accepted-decision
evaluation copy.

## Child contracts

The manifest `domain-analysis/weightedSemaphore/manifest.json` watches
`semaphore/`, `cells/`, `schedule/`, `mutants/` and `faults/` (among other
paths in `watchPaths`). A committed file in any of these folders, including a
README, makes the manifest stale and fails `dsc_check --repo`. Re-pinning
`analyzedSha` only to admit a README would be
[reconcile-lite](../../README.md#glossary), which the
[root README](../../README.md#adopting-it-in-a-brownfield-repo) forbids. The
contracts for the three code folders therefore live here. `mutants/` and
`faults/` hold only `.go.txt` fixtures and have no contract of their own;
they are described under [Interface](#interface).

### semaphore

#### Overview

`semaphore/` is the evaluation copy of `golang.org/x/sync/semaphore` (import
path `golang.org/x/sync/semaphore`). It is the bounded stateful component that
the StateRadar pilot analyzes in
[domain-analysis/weightedSemaphore](domain-analysis/weightedSemaphore/README.md).
Runtime behaviour follows the accepted decisions DR-001..DR-013
([CONTRACT.md](CONTRACT.md)), not the pinned upstream contract.

#### Interface

- `NewWeighted(n int64) *Weighted` — creates a semaphore with maximum combined
  weight `n`.
- `type Weighted` — unexported fields `size`, `cur`, `mu sync.Mutex`,
  `waiters list.List`.
- `(*Weighted).Acquire(ctx context.Context, n int64) error` — blocks until
  weight `n` is granted or `ctx` is done.
  - Returns `nil` on success and `ctx.Err()` on cancellation.
  - When `n > size` it returns
    `"semaphore: requested weight %d exceeds capacity %d"` (`fmt.Errorf`).
- `(*Weighted).TryAcquire(n int64) bool` — acquires without joining the queue.
  It may still wait for the internal mutex (DR-011).
- `(*Weighted).Release(n int64)` — returns weight `n` and wakes eligible
  waiters.
- `waiter{n, ready}`, `(*Weighted).notifyWaiters()` — unexported helpers.

#### Invariants

- Argument checks (DR-002):
  - `NewWeighted` panics on a negative capacity
    (`"semaphore: negative capacity"`).
  - `Acquire`, `TryAcquire` and `Release` panic with
    `"semaphore: negative weight"` on a negative weight. That check runs
    first, before the mutex and before any mutation.
- Release accounting:
  - `Release(n)` with `n > cur` unlocks and panics with
    `"semaphore: released more than held"`, without changing `cur` (DR-003).
  - Accounting is aggregate only: caller identity and duplicate releases are
    not tracked (DR-007/008).
  - `Release(0)` still runs `notifyWaiters`, but in valid reachable states it
    changes no capacity, queue or grant (DR-013). Callers must not use it as
    a wakeup.
- Admission:
  - For a nonnegative weight, `Acquire` checks `ctx.Done()` under the mutex
    first. An already done Context returns `ctx.Err()` even if capacity is
    free, including for oversized requests (DR-004).
  - The fast path admits only when `size-cur >= n` and the waiter queue is
    empty. `TryAcquire` uses the same guard, so no request, including weight
    zero, bypasses queued waiters (DR-001, DR-012).
  - `n > size` returns an error immediately, without enqueuing or waiting for
    `Done` (DR-004).
  - `notifyWaiters` grants strictly in FIFO order and stops at the first head
    that does not fit, so a blocked head is never bypassed.
- Cancellation:
  - On cancellation after enqueue, a request that was already granted
    (`ready` closed) is rolled back (`cur -= n`, `notifyWaiters`).
  - Otherwise the element is unlinked. If it was the front, `notifyWaiters`
    runs even at capacity, so zero-weight heads can proceed.
  - If a grant is followed by a done Context, `Acquire` calls `Release(n)` and
    returns `ctx.Err()`. An error leaves no net holding for the request
    (DR-010).
  - A successful acquisition is never reclaimed by later cancellation; the
    caller must `Release` it (DR-005).
- The queue has no count cap (DR-012).
- Documented caller obligations (doc comments, not enforced):
  - Invocations are independent, and holding capacity while waiting for
    another acquisition can self-block (DR-006).
  - `ctx` must be a non-nil, conforming Context; a nil `Done` channel is valid
    (DR-009).
  - Mutex waits are allowed, and no fixed cancellation-latency bound is
    promised (DR-011).

#### Side Effects

- Mutates `cur` and the `waiters` list under `mu`.
- Closes per-waiter `ready` channels to signal grants.
- Panics on invalid arguments as listed above.
- No I/O, network or disk access.

#### Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).
They also need Go ≥ 1.24.0 (CI installs the `go.mod` version).

The `*_test.go` files in `semaphore/` are the upstream tests and the
evaluation tests `decision_contract_test.go`, `decision_numeric_test.go` and
`decision_q01_test.go`. `verify_q01.py` runs the decision tests with
`-run '^TestDR[0-9]{3}'` and then the whole module with `go test -race ./...`.

- Run: `cd examples/weighted-semaphore && go test -race ./...`
- CI step "weighted semaphore accepted decisions" (job `consistency`):
  - Run: `python3 examples/weighted-semaphore/verify_q01.py`

### cells

#### Overview

`cells/run.py` runs the state-cell suite through the
[public seam](../../README.md#glossary). It executes one Go subtest per
executable matrix cell of the
[weightedSemaphore](domain-analysis/weightedSemaphore/README.md) sidecar, plus
the 16 interaction-pair orderings. The states, events and cell count are
defined in that README. The test file derives a cell's state through the
public seam: `TryAcquire(0)` succeeds exactly when the waiter queue is empty.

The suite needs the scheduling checkpoints of [schedule](#schedule), where
`contractCheckpoint` is defined. Several pair orderings (for example `P-03a`,
`P-04a` and `P-07b`) run the `TestSchedule*` tests, which pause the semaphore
at those checkpoints to force one exact interleaving; the overlay also
supplies helpers such as `contractTimeout`. Queued states themselves are set
up by polling the waiter queue (`q01Enqueued`), not by checkpoints.
`cells/run.py` therefore inserts the same `ANCHORS` into a temporary
`semaphore.go`, and overlays two test files with `go test -overlay` so that
they are never placed in the package:

- `cells/state_cells_test.go.txt` becomes `semaphore/state_cells_test.go`.
- `schedule/checkpoints_test.go.txt` becomes
  `semaphore/schedule_contract_test.go` and provides `contractCheckpoint`.

#### Interface

- `run.py` CLI — `--analysis PATH` (default
  `domain-analysis/weightedSemaphore`), `--count N` (default 10),
  `--output PATH`, `--red-probe`, `--mutation-check`.
- `run(analysis, count, output, red_probe, mutation_check)` — the Python entry
  point behind the CLI.
- `state_cells_test.go.txt` — defines `TestStateCells` (it reads the sidecar
  path from `STATERADAR_CELL_ANALYSIS`) and `TestStatePairs`.

#### Invariants

- `--count` below 1 stops argument parsing with the error
  `positive count required`.
- The `go test` subprocess has a 150 s timeout (the Go test binary itself has
  `-timeout=90s`). Exceeding it raises `subprocess.TimeoutExpired`, which
  stops the run.
- Discovery must match exactly:
  - `analysis.json` must hold 38 cells;
  - 34 of them become tests named `TestStateCells/<state>/<event>`: every cell
    except those for the events `UV-Delay` and `UV-ContextFault`;
  - otherwise the run exits
    `BLOCKED: cell discovery requires 34 tests and four declared contract limits`.
- The pair orderings `TestStatePairs/P-01a`..`P-08b` must all run.
- A baseline run succeeds only if all of these hold:
  - exit 0;
  - every expected test started and passed `count` times;
  - the completion markers `CELL SUITE: 34 cells checked,` and
    `PAIR SUITE: 16 orderings completed` appear once per repeat.
- `--red-probe` rewrites the `Acquire_NoWaiters × TryAcquire` disposition to
  `reject` in a temporary sidecar. It then requires a non-zero exit, complete
  discovery and failure of exactly that cell (and its parent tests).
- A baseline or red-probe run that misses its expected verdict exits
  `BLOCKED: expected complete cell verdict missing`.
- `--mutation-check`:
  - requires `--count 1`, complete discovery and both completion markers;
    otherwise it exits `BLOCKED: incomplete Go behavior verdict`;
  - when those hold, it passes the Go exit code through.
- Reuses `ANCHORS`, `SOURCE` and `replace_once` from `schedule/run.py`. An
  absent or ambiguous anchor raises `ValueError`.

#### Side Effects

- Writes the patched `semaphore.go`, `overlay.json` and (for `--red-probe`) a
  modified `analysis.json` to a `tempfile.TemporaryDirectory`.
- Runs this command in `examples/weighted-semaphore`, with
  `STATERADAR_CELL_ANALYSIS` set in its environment:
  - `go test -race -count=N -timeout=90s -overlay ... -run '^TestState(Cells|Pairs)$' -json ./semaphore`
- Writes raw Go output to `--output` when given.
- Does not modify tracked files.

#### Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).
They also need Go ≥ 1.24.0 (CI installs the `go.mod` version).

- Run: `python3 examples/weighted-semaphore/cells/run.py`
- Run: `python3 examples/weighted-semaphore/cells/run.py --red-probe --count 1`
- CI step "weighted semaphore current model and cells" (job `consistency`)
  runs the baseline (10 repeats) and the red probe:
  - Run: `python3 examples/weighted-semaphore/domain-analysis/weightedSemaphore/verify.py`

The mutation tools run the cell suite through the `testCommand` in
`domain-analysis/weightedSemaphore/matrix-mutation.json` and
`fault-mutants.json`, with working directory `examples/weighted-semaphore`:

```text
python3 cells/run.py --analysis {analysis_dir} --count 1 --mutation-check
```

The tools substitute `{analysis_dir}` before each run.
`tools/check_matrix_mutation.py` passes a temporary copy of the analysis
directory with one matrix mutation applied. `tools/check_fault_mutants.py`
passes the analysis directory inside a temporary copy of the component with
one source mutant applied. The CI step "weighted semaphore mutation binding"
runs both; its commands are listed in
[weightedSemaphore Verification](domain-analysis/weightedSemaphore/README.md#verification).

### schedule

#### Overview

`schedule/run.py` runs scheduled-interleaving tests and fault overlays.

- It inserts `contractCheckpoint` calls into a temporary copy of
  `semaphore/semaphore.go`.
- It overlays `checkpoints_test.go.txt` as
  `semaphore/schedule_contract_test.go` to drive deterministic orderings for
  DR-010..DR-012.
- It can also apply one of four deliberate faults and require that the named
  test fails.

#### Interface

- `run.py` CLI — `--mode MODE` (default `baseline`), `--count N` (default
  50), `--output PATH`. `MODE` is one of:
  - `baseline`;
  - `omit-grant-rollback`, `omit-selected-rollback`, `try-bypass`,
    `zero-charges`.
- `SOURCE` — path of `semaphore/semaphore.go`, the source to patch.
- `SCHEDULE_TESTS` — the six `TestSchedule*` test names.
- `ANCHORS` — checkpoint insertions `before-mutex`, `initial-checked`,
  `cancel-selected`, `grant-received`, `queued-success`.
- `MUTATIONS` — mode → source replacement and target test.
- `replace_once(source, old, new)`, `run(mode, count, output)` — module
  functions. `cells/run.py` reuses `replace_once`, `ANCHORS` and `SOURCE`.
- `checkpoints_test.go.txt` — defines `contractCheckpoint`, `contractPause`
  and six tests:
  - `TestScheduleDR010FastLateCancel`, `TestScheduleDR010GrantedRollback`;
  - `TestScheduleDR010CancelSelectedRollback`,
    `TestScheduleDR010QueuedLateCancel`;
  - `TestScheduleDR011CancelBeforeMutex`, `TestScheduleDR012ReturnOrder`.

#### Invariants

- `--count` below 1 stops argument parsing with the error
  `count must be positive`.
- The `go test` subprocess has a 90 s timeout (the Go test binary itself has
  `-timeout=45s`). Exceeding it raises `subprocess.TimeoutExpired`, which
  stops the run.
- Every anchor and mutation pattern must occur exactly once in
  `semaphore.go`; otherwise `replace_once` raises `ValueError`. In a mutation
  mode the mutation is applied before the checkpoint anchors.
- Baseline passes only with exit 0 and each of the six schedule tests started
  and passed exactly `count` times, with no failures.
- Each mutation mode targets one test:
  - `omit-grant-rollback` → `TestScheduleDR010GrantedRollback`;
  - `omit-selected-rollback` → `TestScheduleDR010CancelSelectedRollback`;
  - `try-bypass` → `TestDR012HeadOfLineFIFO` (a decision test in
    `semaphore/decision_contract_test.go`);
  - `zero-charges` → `TestDR013ZeroRelease` (also a decision test).
- A mutation mode passes only if all of these hold:
  - the Go exit code is not 0;
  - the target test started and failed exactly `count` times;
  - a package-level fail record exists;
  - the output contains no `panic:` or `build failed`.
- Any other outcome exits
  `BLOCKED: expected named, completed behavior verdict missing`.

#### Side Effects

- Writes the altered source and `overlay.json` to a
  `tempfile.TemporaryDirectory`.
- Runs this command in `examples/weighted-semaphore`:
  - `go test -race -count=N -timeout=45s -overlay ... -run '^(<tests>)$' -json ./semaphore`
  - `<tests>` is the six schedule tests in baseline mode, or the single target
    test in a mutation mode.
- Writes raw Go output to `--output` when given.
- Does not modify tracked files.

#### Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../README.md#system-verification)).
They also need Go ≥ 1.24.0 (CI installs the `go.mod` version).

The second command is one fault probe; the other modes run the same way.

- Run: `python3 examples/weighted-semaphore/schedule/run.py`
- Run: `python3 examples/weighted-semaphore/schedule/run.py --mode try-bypass --count 1`
- CI step "weighted semaphore accepted decisions" (job `consistency`) runs the
  baseline and all four fault probes:
  - Run: `python3 examples/weighted-semaphore/verify_q01.py`
