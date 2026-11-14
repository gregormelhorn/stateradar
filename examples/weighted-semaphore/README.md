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
question remains open. Historical as-is reconciliation remains separate.

From the pack root, with Go 1.24+ and the pack Python dependencies:

```sh
.venv/bin/python examples/weighted-semaphore/verify_q01.py
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
