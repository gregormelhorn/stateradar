# Weighted semaphore: DR-001 evaluation copy

This is a small, licensed copy of `golang.org/x/sync` v0.17.0, upstream commit
`04914c200cb38d4ea960ee6a4c314a028c632991`. It is an evaluation fixture, not an
upstream release, production deployment or upstream-approved policy.

`semaphore/*.go`, `go.mod` and `LICENSE` were copied from that revision.
`errgroup/errgroup.go` is the unchanged dependency of the upstream semaphore
tests. The original upstream tests are retained unchanged. The only runtime
change is the two-line cancellation guard/comment patch in `semaphore.go`:
head removal scans the next waiter even when no positive capacity is free.
The existing notifier still admits only an eligible FIFO prefix.

[DR-001](../../docs/evidence/semaphore-pilot/resolution-q01/decisions/DR-001.yaml)
records the owner's Q-01 decision. Five additional behavior scenarios exercise
that decision; they are a partial conformance suite. The other twelve pilot
questions remain OPEN. Tests use a read-only enqueue barrier for scheduling and
assert public API outcomes; see the [seam](../../docs/evidence/semaphore-pilot/resolution-q01/seam.md).

From the pack root, with Go 1.24+ and the pack Python dependencies:

```sh
.venv/bin/python examples/weighted-semaphore/verify_q01.py
```

This checks the source-bound symbolic guard, runs five named decision scenarios
50 times with the race detector, rejects empty/incomplete test discovery, and
runs the upstream plus decision regression suite. CI runs the same command with
`python`. No model/API calls are made. The guard proof covers its stated integer
assumptions; behavior tests verify the actual notification path. Neither proves
all scheduler interleavings or a production wall-clock latency bound.

The original pilot's as-is probes intentionally describe the old behavior and
remain archived. Use the original reproduction driver for that historical
baseline; it must not be repurposed as conformance acceptance of this fix.
