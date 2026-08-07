# silenceper/pool Resolution Design

**Date:** 2026-08-07  
**Status:** approved design; implementation plan pending  
**Scope:** StateRadar Resolution artifacts only. No upstream `silenceper/pool` source, test, tag, or push changes.

## Goal

Turn accepted decisions DR-001 through DR-006 into an explicit, reviewable to-be model for the `silenceper/pool` `channelPool` benchmark. Completion is successful StateRadar artifact and pack-check validation; it does not require an upstream implementation.

## Context

The root benchmark sidecar, `tests/benchmarks/silenceper-pool-32/analysis.json`, remains the as-is observation record. It records current upstream behavior and is used by the benchmark runner. The six questions are answered and linked to decision records, but the desired behavior has not been represented in a separate to-be model.

## Architecture

Create a dedicated Resolution directory:

```text
tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/
```

The directory is an approved specification surface. It does not replace the root sidecar until a later Reconcile phase after implementation is green.

### Artifacts

| File | Responsibility |
|---|---|
| `as-is.machine.mmd` | Four-state current model: `Active_HasIdle`, `Active_IdleExhausted_UnderCap`, `Active_IdleExhausted_AtCapacity`, and `Released`. |
| `to-be.machine.mmd` | Same state topology with DR-labelled effects for terminal release and waiter-path Ping validation. |
| `disposition-matrix.md` | Total 4×20 to-be matrix. Every answered row cites its governing DR; no answered cell remains an unlabelled hole. |
| `invariants-and-lints.md` | Documents INV-01 and its DR-002/DR-006 valid-caller assumption. |
| `to-be-diff.md` | Exact as-is → to-be semantic differences, one DR citation per line. |
| `remaining-holes.md` | Declares Q-01 through Q-06 answered and lists any cell that remains unresolved after matrix construction. |

## Approved decisions represented

| DR | To-be effect |
|---|---|
| DR-001 | `Release()` transitions to `Released` and resolves queued `Get()` waiters with `ErrMaxActiveConnReached`. |
| DR-002 | Lost, duplicate, and foreign `Put()` are valid-caller (`NAT`) assumptions, not lease-tracking requirements. |
| DR-003 | `Put()` after `Release()` is a safe terminal no-op; callers clean up outstanding borrows before release. |
| DR-004 | A configured Ping validates every connection before `Get()` returns it, including waiter delivery; failure discards and retries. |
| DR-005 | Factory errors return without consuming capacity; initialization failure aborts construction; no at-capacity waiter notification is added. |
| DR-006 | `openingConns >= 0` is a SYS invariant under the valid-caller ownership assumption. No duplicate-close guard or counter clamp is added. |

## Matrix rules

1. The matrix has the canonical four states and twenty events from the root sidecar.
2. DR-001 and DR-004 produce behavioral deviations from the as-is model.
3. DR-002, DR-003, DR-005, and DR-006 state contract or existing-behavior decisions. Their cells cite the relevant DR without inventing an unimplemented runtime guard.
4. A caller-misuse variant is described as a `NAT` assumption in the invariant/lint artifact. It is not presented as a runtime rejection if the pool cannot identify it.
5. Every `ignore (documented)`, `reject`, or `defer (queued)` disposition carries a DR reference when it differs from as-is or is governed by a decision.

## Validation

Resolution-only validation must prove:

- both Mermaid models use the canonical four state names;
- the to-be matrix covers every state × event pair exactly once;
- every claimed semantic change cites DR-001 through DR-006;
- INV-01 names the DR-002/DR-006 environment assumption;
- the root sidecar and benchmark expectations remain unchanged by this phase;
- no source code, upstream test, release tag, or push is created.

The existing pack gates (`dsc_check`, selftest, consistency, tool tests, benchmark, and evidence) remain required before the Resolution artifact commit.

## Out of scope

- Implementing upstream `silenceper/pool` changes.
- Generating or executing upstream red tests, test seams, or deviation reports.
- Treating an upstream implementation change as necessary evidence that StateRadar works.
- Updating the root sidecar from as-is to to-be.
- Releasing a new StateRadar version.
- Pushing the resulting commits.
