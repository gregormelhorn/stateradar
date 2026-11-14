# Weighted semaphore: accepted-decision evaluation copy

This is a small, licensed copy of `golang.org/x/sync` v0.17.0, upstream commit
`04914c200cb38d4ea960ee6a4c314a028c632991`. It is an evaluation fixture, not an
upstream release, production deployment or upstream-approved policy.

`semaphore/*.go`, `go.mod` and `LICENSE` were copied from that revision.
`errgroup/errgroup.go` is the unchanged dependency of the upstream semaphore
tests. The original upstream tests are retained unchanged. The runtime changes
implement four accepted decisions: FIFO progress for zero weight (DR-001),
negative-argument panic before mutation (DR-002), non-corrupting over-release
panic (DR-003), and an immediate explanatory error for oversized Acquire
(DR-004). Pre-canceled Context handling remains unchanged for nonnegative
weights. These evaluation-specific contracts differ from the pinned upstream.

The [Q-01 evidence](../../docs/evidence/semaphore-pilot/resolution-q01/deviation-report.md),
[numeric evidence](../../docs/evidence/semaphore-pilot/resolution-q02-q04/deviation-report.md)
and [final contract evidence](../../docs/evidence/semaphore-pilot/contracts-q05-q13/README.md)
record all thirteen accepted decisions and completed focused conformance work.
[CONTRACT.md](CONTRACT.md) is the normative evaluation contract. No original
question remains open. The [current analysis](domain-analysis/weightedSemaphore/summary.md) records the resolved matrix, cell coverage and reconciliation evidence. The original upstream pilot remains historical.

From the pack root, with Go 1.24+ and the pack Python dependencies:

```sh
.venv/bin/python examples/weighted-semaphore/verify_q01.py
.venv/bin/python examples/weighted-semaphore/domain-analysis/weightedSemaphore/verify.py
```

The original entry-point name is retained; it now checks all thirteen decisions.
It checks guard/coverage obligations, runs 32 ordinary groups (66 exact test/subtest
names) and 6 scheduled groups 50 times with the race detector, and rejects
empty/incomplete discovery. It also runs the upstream plus decision regression
suite and four faulty overlays. CI runs the same command with `python`. No model/API calls are made. The guard proof covers its stated integer
assumptions; behavior tests verify the actual notification path. Neither proves
all scheduler interleavings or a production wall-clock latency bound.

The original pilot's as-is probes intentionally describe the old behavior and
remain archived. Use the original reproduction driver for that historical
baseline; it must not be repurposed as conformance acceptance of this fix.

The current-model verifier checks 38 matrix cells: 34 executable guarded scenarios and four explicit contract limits, plus all 16 interaction-pair orderings. It repeats executable scenarios ten times under the race detector, demonstrates a deliberately wrong matrix verdict, checks artifact mutations, and verifies all 52 retained historical artifact hashes. Faulty Context guarantees and absent fixed latency bounds are not counted as green tests.

The generic mutation binding runs separately in CI:

```sh
.venv/bin/python tools/gen_mutant_variants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore --check
.venv/bin/python tools/check_matrix_mutation.py examples/weighted-semaphore/domain-analysis/weightedSemaphore
.venv/bin/python tools/check_fault_mutants.py examples/weighted-semaphore/domain-analysis/weightedSemaphore
```

The JSON sidecar is the actual oracle consumed by the temporary cell suite.
A kill requires completed cell discovery and failure of the targeted cell.
Compilation errors, panics before completion and unrelated failures are blocked.
The four contract-limit cells and two queued cells without a supported matrix
operator are printed as not applicable. Supported mutations exercise 32 cells,
with 41 matrix changes and four source faults. This is bounded evidence, not
proof of every fault or interleaving. Structured rationale for all 38 cells is
bound in `cell-rationale.json`; see [format](../../docs/cell-rationale.md).
