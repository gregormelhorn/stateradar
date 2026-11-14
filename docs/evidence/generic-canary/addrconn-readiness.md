# grpc-go addrConn: second-component F-09 readiness

**Result: technically promising, not yet ready as a validated second binding.**
The historical source builds and its cancellation test runs, but that test
survives the targeted omission. The retained analysis cannot be used unchanged
as the current test oracle. No domain decision or upstream implementation was
changed during this assessment.

## Scope and executed evidence

Read the retained `tests/benchmarks/grpc-go-2669` artifacts, then cloned the
upstream v1.18.0 tag and verified SHA
`a02b0774206b209466313a0b525d2c738fe407eb`. All code observations below concern
that historical pin, not today's grpc-go. Source checkout remained clean.

Reproduce with a clean checkout at that SHA:

```sh
.venv/bin/python docs/evidence/generic-canary/scripts/addrconn_probe.py /path/to/grpc-go --output-dir /tmp/addrconn-results
```

The probe executes `go test -mod=readonly -race -count=10 -timeout=90s
-run '^Test/BackoffCancel$' -json .`, first unchanged, then with a temporary Go
overlay omitting only `ac.cancel()` in `tearDown`. It verifies exactly ten
completed `Test/BackoffCancel` subtests and ten parent tests per run.

**observed-in-tests:** both runs pass 10/10. This is a readiness negative
control, not a full F-09 binding, a generic-runner kill result or a proof that
arbitrary leaks are absent. See `addrconn-probe.txt`, `addrconn/summary.json`
and the two raw Go JSON streams. The locally executed toolchain was Go 1.27.3
on darwin/arm64; cross-platform readiness was not measured.

## Contracts and observation points checked

| Evidence at pinned source | Consequence |
|---|---|
| `clientconn.go:603 ("ac.ctx, ac.cancel = context.WithCancel(cc.ctx)")` | **observed-in-code:** the addrConn context is a child of ClientConn's context. |
| `clientconn.go:853 ("defer cc.cancel()")` and `clientconn_test.go:971 ("cc.Close()")` | **observed-in-code / inferred:** the existing test tears down the parent too; parent cancellation can mask omitted local cancellation. The overlay's survival is observed, this causal explanation follows the context wiring. |
| `clientconn.go:1337 ("ac.cancel()")` and `clientconn.go:1140 ("case <-acctx.Done():")` | **observed-in-code:** local teardown cancels the context; the backoff wait observes cancellation, stops its timer and returns. This is a candidate resource lifecycle independent of a live transport. |
| `grpc_test.go:46 ("leakcheck.Check(errorer{t: t})")` | **observed-in-code:** existing test teardown performs a package goroutine scan. Its passing result is not an executed canary for a scoped addrConn resource projection. |
| `clientconn.go:1187 ("transport.NewClientTransport(connectCtx, ac.cc.ctx")` and `internal/transport/http2_client.go:150 ("ctx, cancel := context.WithCancel(ctx)")` | **observed-in-code:** connect deadlines derive from ac.ctx, but transport lifetime is passed cc.ctx. Do not infer that ac.cancel alone closes an established transport. |
| `internal/transport/http2_client.go:791 ("GracefulClose sets the state to draining")` | **observed-in-code:** graceful close permits active streams to drain. Immediate physical transport disappearance is not a valid universal post-cancel oracle. |

Historical Q-11 describes indirect transport cleanup and remains OPEN. Its
old citation to `http2_client.go:326-338` is not a sufficient proof that local
addrConn cancellation closes that transport: at the pinned source those lines
run the writer and close its connection on termination, while the supplied
lifetime context is the parent's. This is a limitation to correct in a new
evaluation copy; the historical question and its proposed answer remain intact.

## Artifact readiness

**observed:** historical summary lists 16 OPEN questions, no decision records,
no executable cell suite and no coverage map. Running today's `dsc_check.py`
against this source pin fails (retained in `addrconn-historical-check.txt`),
including missing citation fragments and newer schema/coverage requirements.
This is a known historical artifact compatibility limit, separate from the
green active-pack gates. No historical analysis was rewritten to hide it.

## Recommended next scope (proposed)

Start with `TransientFailure_Backoff` plus local addrConn teardown while the
parent ClientConn remains alive. Establish entry into the backoff wait through
a deterministic scheduling seam and observe the worker's exit/resource cleanup
through a declared completion signal. The omission of local cancellation must
leave that resource pending; a weak state-only assertion can still see Shutdown.
Use an independent resource canary and keep test watchdogs distinct from domain
latency guarantees. A timer/worker seam still needs implementation and proof;
this assessment does not claim it already exists.

Before that second-component slice, create a separate current evaluation copy:
refresh source-fragment citations, explicit event/coverage annotations and the
scoped model/test mapping. Resolve only owner questions that actually govern
the selected cells. The existing Shutdown/dial-publication race (Q-01) and
live-transport/drain semantics (Q-11) must not be silently answered or folded
into this narrower backoff test. Historical artifacts remain frozen.
