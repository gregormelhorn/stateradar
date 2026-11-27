# weightedSemaphore — StateRadar analysis

Part of [domain-analysis](../README.md).

## Overview

StateRadar analysis of the weighted semaphore in
`examples/weighted-semaphore/semaphore` (contract in
[the weighted-semaphore README](../../README.md#semaphore)). The normative
evaluation contract is [CONTRACT.md](../../CONTRACT.md), and
[summary.md](summary.md) is the human-readable status.

### State model

- States: two [projected](../../../../README.md#glossary) queue states, a
  reduced view of the semaphore that keeps only whether requests wait:
  - `Acquire_NoWaiters` — the waiter queue is empty;
  - `Acquire_WaitersPending` — at least one request is queued.
- Events: 19, namely four external calls (`NewWeighted`, `Acquire`,
  `TryAcquire`, `Release`), two internal events (`ContextDone`, `Grant`) and
  13 [UV events](../../../../README.md#glossary) such as `UV-Delay` and
  `UV-RepeatAcquire`.
- Cells: 2 × 19 = 38 [cells](../../../../README.md#glossary).
  - 34 are executable and run as `TestStateCells/<state>/<event>`.
  - 4 are contract limits: `UV-Delay` and `UV-ContextFault` in both states,
    recorded as `untestable-via-seam` rather than tested.

### Sidecar is the source

In the generic flow, `tools/gen_analysis_sidecar.py` parses
`disposition-matrix.md` into `analysis.json`. Here the direction is reversed:
`analysis.json` is the source, and `check_matrix.py` requires
`disposition-matrix.md` to equal `render(analysis.json)` byte for byte.

The sidecar is the source because it holds more than the matrix. Besides the
grid, it carries data that the rendered matrix does not show: per-cell
structured `rationale`, `decisionEvidence`, `guardGroups`, `pairs`,
`docLines` and the question register. Parsing the matrix could not recover
that data, so the matrix is a rendered view of the sidecar, and the
byte-equality check keeps the two from drifting.

Two sidecar fields recur below:

- `behaviouralDrs` — the decisions the matrix cells cite (all 13,
  DR-001..DR-013). The set of DRs cited by the cells must equal it.
- `decisionEvidence` — one entry per DR, with a code citation and a test
  citation (`file`, `line`, `fragment`) and provenance labels. A provenance
  label says where a claim comes from; the allowed labels are
  `explicit-requirement`, `observed-in-code`, `observed-in-tests`, `inferred`
  and `proposed` ([AGENTS.md §2](../../../../AGENTS.md#2-the-objects)).

## Interface

- `verify.py` — current-model acceptance driver. `main()` runs every step
  listed under Invariants in sequence. No CLI options.
- `check_matrix.py` — component-specific validator (not
  `tools/check_matrix.py` or the `tools/templates` wrapper). Its members:
  - `render(model)` — renders the matrix text from the sidecar.
  - `citations(obj)` — walks the sidecar and yields every citation object.
  - `validate(model, coverage, scenarios, matrix, root)` — the validator.
  - `run(adir, selftest)` — the entry point.
  - `--selftest` — CLI flag that adds the artifact
    [red probes](../../../../README.md#glossary) (deliberately broken inputs
    that must fail).
- `check_guards.py` — z3 guard prover for this component, built on
  `check_group`, `boundary_probe` and `render` from `tools/guard_proofs.py`.
  Its members:
  - `run(source=None)` — the entry point.
  - `--source PATH` — CLI flag that checks another source file; `verify.py`
    uses it for a red probe, which the digest pin rejects.
- `analysis.json` (the [sidecar](../../../../README.md#glossary)),
  `manifest.json`, `matrix-coverage.json`, `scenario-coverage.json`,
  `disposition-matrix.md`, `source-pins.json`, `decisions/DR-*.yaml` (the 13
  [decision records (DRs)](../../../../README.md#glossary)) — data artifacts
  read by the checkers.
- `summary.md` (human-readable status), `as-is.machine.mmd`,
  `event-catalogue.md`, `extraction.md`, `adversarial-traces.md`,
  `invariants-and-lints.md`, `open-questions.md`, `cell-rationale.json`,
  `fault-mutants.json`, `matrix-mutation.json`, `mutant-generation.json` —
  other analysis artifacts.
- Subdirectories:
  - archive/2026-11-14:
    [`./archive/2026-11-14/README.md`](./archive/2026-11-14/README.md) -
    superseded reconciliation inputs.
  - evidence: [`./evidence/README.md`](./evidence/README.md) - executed
    evidence logs.

## Invariants

These checks pin the analysis, so drift between matrix, sidecar, DRs and
source fails CI. In `check_matrix.py`, each requirement below raises
`ValueError` with its own message, for example `state/event discovery drift`,
`matrix text differs from sidecar` or `broken fragment: …`.

- `check_matrix.py`, grid and registers:
  - exactly 2 states and 19 events;
  - 38 cells in both `analysis.json` and `matrix-coverage.json`, covering the
    full state × event grid;
  - `disposition-matrix.md` equals `render(analysis.json)` byte for byte;
  - the set of cell DRs equals `behaviouralDrs` (13 entries);
  - `decisionEvidence` has exactly 13 entries matching `behaviouralDrs`;
  - all 13 questions are `RESOLVED`.
- `check_matrix.py`, cell coverage:
  - each cell's `dr` and `disposition` in `matrix-coverage.json` equal the
    sidecar's;
  - cells for `UV-Delay` and `UV-ContextFault` carry an
    `untestable-via-seam` reason longer than 40 characters and no test;
  - every other cell names the test `TestStateCells/<state>/<event>`.
- `check_matrix.py`, scenario traces:
  - `scenario-coverage.json` holds exactly 30 traces: the interaction-pair
    orderings `P-01a`..`P-08b` and the adversarial traces `T-01`..`T-14`
    ([T-nn traces](../../../../README.md#glossary), defined in
    `adversarial-traces.md`);
  - `T-08` and `T-09` must be `untestable-via-seam` with a reason starting
    with `DR-009`;
  - every other trace names a test whose top-level name (the part before the
    first `/`) appears in its `testCitation.fragment`.
- `check_matrix.py`, decision copies:
  - each `decisions/DR-*.yaml` ends with a `canonical_record:` line. Its value
    is the repo-relative path of the owner's accepted record under
    `docs/evidence/semaphore-pilot/` (for DR-001, in `resolution-q01/`; for
    the others, in `resolution-q02-q04/`);
  - the local copy must equal that accepted record verbatim, followed by the
    `canonical_record:` line. The only permitted change is that the record's
    `implementation_evidence:` path, relative to the record, is rewritten as
    a repo-relative path;
  - otherwise the message is
    `decision attribution or scope differs from accepted record: <DR>`.
- `check_matrix.py`, citations: every `file:line ("fragment")` citation,
  including those in the coverage-table n/a prose, matches within 3 lines
  either side of the cited line.

`check_guards.py` works on [guard groups](../../../../README.md#glossary)
(G-nn), the entries of `analysis.json["guardGroups"]`. G-01..G-09 are sets of
mutually exclusive branch conditions extracted from `semaphore.go`. G-10
collects the inductive obligations: z3 formulas, each describing a forbidden
situation at a mutex-release boundary. G-11 is the queued `select`, recorded
as `not-formalizable`. A boundary probe evaluates a group at concrete values
below, at and above each comparison limit.

- `check_guards.py` checks the following, in order. Each failure exits with
  a message starting `GUARD FAIL:`:
  - the SHA-256 of `semaphore/semaphore.go` must equal
    `source-pins.json["semaphore.go"]`; otherwise
    `GUARD FAIL: reviewed source digest changed; re-extract guard expressions`;
  - each boundary probe of G-01..G-09 must select exactly one guard;
    otherwise `GUARD FAIL: boundary not uniquely covered`;
  - the seven G-10 inductive obligations must be `unsat`:
    - examples are an admit, release or grant that moves `cur` outside
      `0..size`, or a retained blocked head that would fit;
    - `unsat` means the situation cannot occur under the stated integer
      assumptions;
    - otherwise `GUARD FAIL: <obligation> <model>`, with the obligation name
      and the z3 counterexample;
  - guard groups G-01..G-09 must be pairwise disjoint and covering (outcome
    `proven`); otherwise `GUARD FAIL: partition`;
  - the recorded outcomes in `analysis.json["guardGroups"]`; otherwise
    `GUARD FAIL: recorded outcomes differ`:
    - the first ten entries must equal, in order,
      `{"id": "G-nn", "outcome": "proven"}` for G-01..G-10;
    - the comparison is exact, so any extra key in one of them fails;
    - the eleventh entry (G-11) must have outcome `not-formalizable`.
- `verify.py`, green steps (each must exit 0):
  - `check_matrix.py --selftest`, `tools/check_matrix.py`, `check_guards.py`;
  - `cells/run.py --red-probe --count 1` (the runner itself requires the
    expected cell to fail) and the `cells/run.py` baseline;
  - `tools/dsc_check.py` and `tools/check_reachability.py`.

`verify.py` runs two guard red probes on a temporary copy of `semaphore.go` in
which `if isFront {` is rewritten to `if isFront && s.size > s.cur {`. When a
canceled waiter at the front of the queue is removed, the copy then calls
`notifyWaiters` only if spare capacity remains. That is the DR-001
regression: the added condition is the pinned upstream head guard that DR-001
removed. At full capacity the copy skips `notifyWaiters`, so a zero-weight
waiter that becomes the new head stays queued although it needs no capacity,
which DR-001 forbids.

- `verify.py`, guard red probes:
  - `docs/evidence/semaphore-pilot/resolution-q01/check_guards.py --source`
    must exit non-zero and print `Counterexample:`;
  - `check_guards.py --source` must exit non-zero and print
    `GUARD FAIL: reviewed source digest changed`.
- `verify.py`, other gates:
  - a step with the wrong exit code or missing text exits
    `BLOCKED: acceptance command did not produce the required verdict`;
  - `if isFront {` must occur exactly once in `semaphore.go`; otherwise it
    exits `head guard anchor drift`;
  - every file listed in `docs/evidence/semaphore-pilot/retained-hashes.json`
    (52 files) must match both its SHA-256 and its byte length; otherwise it
    exits `BLOCKED: historical artifact changed: <name>`.

## Side Effects

- `verify.py` runs these subprocesses from the repository root, in order:
  - `check_matrix.py --selftest`, `tools/check_matrix.py`, `check_guards.py`;
  - the two guard red probes on a temporary source copy;
  - `cells/run.py --red-probe --count 1` and the baseline (contract in
    [the weighted-semaphore README](../../README.md#cells)), which run
    `go test -race`;
  - `tools/dsc_check.py <dir> --repo . --model as-is.machine.mmd` (or
    `to-be.machine.mmd` if present), which runs `git diff` against
    `analyzedSha` for the staleness check;
  - `tools/check_reachability.py`.
- `verify.py` writes only to a `tempfile.TemporaryDirectory`. It makes no
  artifact writes and no model calls.
- `check_matrix.py --selftest` mutates in-memory copies only:
  - six artifact red probes, each of which must fail: missing DR evidence,
    missing cell, missing coverage, broken fragment, false exclusion, lost
    trace;
  - one matrix-text drift probe, which must also fail.

## Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../../../README.md#system-verification)).

Prerequisites:

- Go ≥ 1.24.0 (CI installs the `go.mod` version).
- A Git checkout with history back to the manifest's `analyzedSha`, because
  `tools/dsc_check.py --repo` runs `git diff`. CI checks out with
  `fetch-depth: 0`.

Start with `check_matrix.py --selftest`; it needs neither Go nor Git history.

- Run: `python3 examples/weighted-semaphore/domain-analysis/weightedSemaphore/check_matrix.py --selftest`
- Run: `python3 examples/weighted-semaphore/domain-analysis/weightedSemaphore/check_guards.py`
- CI step "weighted semaphore current model and cells" (job `consistency`):
  - Run: `python3 examples/weighted-semaphore/domain-analysis/weightedSemaphore/verify.py`
- CI step "weighted semaphore mutation binding" (job `consistency`):
  - Run: `python3 tools/gen_mutant_variants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore --check`
  - Run: `python3 tools/check_matrix_mutation.py examples/weighted-semaphore/domain-analysis/weightedSemaphore`
  - Run: `python3 tools/check_fault_mutants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore`
