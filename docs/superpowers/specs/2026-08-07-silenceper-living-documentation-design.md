# silenceper/pool Living Documentation Design

**Date:** 2026-08-07  
**Scope:** Update the living documentation for the `silenceper-pool-32` benchmark. Do not change public lifecycle documentation, historical release records, or upstream source.

## Goal

Make the current silenceper benchmark status easy to find and internally
consistent. The documentation must show that Resolution artifacts are complete,
while Testgen, upstream implementation, Reconcile, release, and push are out of
scope for this benchmark task.

## Current Evidence

The pack checker is green. It checks structural pack consistency. It does not
check that every narrative status statement is current.

The root `open-questions.md` still says that the to-be model and test generation
are pending for Q-01 through Q-06. The to-be model is complete. Testgen is not
part of this benchmark task.

The pack guidance requires a living `domain-analysis/summary.md` index. The
silenceper benchmark has no such index. Its Resolution artifacts are under
`domain-analysis/channelPool/` and need a stable entry point.

## Documentation Model

### Canonical as-is record

`tests/benchmarks/silenceper-pool-32/analysis.json` remains the canonical as-is
benchmark sidecar. It records observed upstream behavior. The documentation
must not present its state as the approved to-be behavior.

### Current Resolution record

Create `tests/benchmarks/silenceper-pool-32/domain-analysis/summary.md` as the
living index for the benchmark. It must link to:

- the root as-is sidecar and root question register;
- the six accepted decision records;
- the `channelPool` as-is model, to-be model, event catalogue, disposition
  matrix, invariants, semantic diff, and local question register;
- the two unresolved question sets: Q-UV-01 and Q-07.

The summary must state that the separate to-be artifact set is checker-green.
It must also state that this benchmark stops after Resolution. It must not claim
an upstream implementation, Testgen result, Reconcile result, release, or push.

### Root question register

Update `tests/benchmarks/silenceper-pool-32/open-questions.md` as follows:

1. Replace the six stale `to-be model and test generation pending` status tails.
2. State that each DR-backed decision has a complete to-be artifact link.
3. State that Testgen is intentionally out of scope for this benchmark task.
4. Add Q-UV-01 and Q-07 as OPEN entries. Link both to the local
   `domain-analysis/channelPool/` question and hole documents.
5. Preserve the original as-is findings and decision text. Do not rewrite them
   as implemented behavior.

### Benchmark-facing links

Update `tests/benchmarks/silenceper-pool-32/MANIFEST.md` with a short current
analysis-status section. It must link to `domain-analysis/summary.md` and say
that the primary finding is the frozen as-is/oracle record.

Update `tests/benchmarks/README.md` with a concise link from the silenceper
benchmark row or a nearby current-artifact note to the new summary. Do not add
the benchmark-specific stop condition to the public README or generic prompts.

## Non-goals

- Do not change `README.md`, `AGENTS.md`, the generic prompts, or the roadmap.
  They describe the normal StateRadar lifecycle.
- Do not rewrite historical `CHANGELOG.md` entries or past design documents.
- Do not change `analysis.json`, `expected.json`, the decision records, or any
  upstream code or tests.
- Do not add a new documentation checker in this update.

## Verification

Before the documentation commit:

1. Confirm each linked silenceper local path exists.
2. Confirm no stale `to-be model and test generation pending` text remains.
3. Confirm the summary distinguishes as-is from to-be and lists Q-UV-01 and
   Q-07 as OPEN.
4. Confirm generic lifecycle documents have no silenceper-specific changes.
5. Run `dsc_check`, `check_pack_consistency`, the tool selftests, tool tests,
   benchmark runner, benchmark-evidence report, and `git diff --check`.

## Completion Boundary

A local documentation commit completes this task. Do not start Testgen, upstream
implementation, Reconcile, a release, a tag, or a push as part of this work.
