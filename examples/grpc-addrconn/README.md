# grpc-go addrConn local backoff cleanup

A source-pinned F-09 mutation benchmark using the real grpc-go v1.18.0 code
(`a02b0774206b209466313a0b525d2c738fe407eb`). No upstream code is changed in this
repository. Disposable copies plus Go overlays add scheduling/time controls
and observations. The fake dial fails without opening a network connection;
the actual parent ClientConn stays alive throughout the assertions.

Run from the StateRadar repository root:

```sh
.venv/bin/python tools/addrconn_f09.py
# Or reuse a clean exact-pinned checkout:
.venv/bin/python tools/addrconn_f09.py --checkout /path/to/grpc-go --output-dir /tmp/addrconn-proof
```

Without `--checkout`, the runner clones v1.18.0 into a temporary directory and
verifies the exact SHA before executing anything. The upstream manifest checks
source citations/staleness; `harness-manifest.json` independently watches the
committed pack harness/model/decision files. CI executes this benchmark and
its exact-discovery/decision selftests. Go dependencies follow the pinned
upstream go.mod/go.sum with `-mod=readonly`.

The six-cell state projection covers an already-waiting backoff worker, local
shutdown pending, and shutdown completed. It explicitly excludes established
transports, health monitoring, reset races, resolver updates and dial-publication
races. See `domain-analysis/addrConnBackoff/scope.md` for the preconditions,
source observations, resource obligations and coverage limits.

Two independent canaries establish both coordinates of resource observation:
`omit-backoff-stop` leaves the timer active although the worker returns;
`wait-for-parent` stops the timer but retains the worker until parent teardown.
The F-09 fault `omit-local-cancel` drops the local cleanup trigger. The generic
runner executes the timer canary first, then the worker canary, then the fault.
All three must fail `BackoffWaiting x TearDown` in a fully completed suite.
The state-only weak suite deliberately survives all three.

The owner additionally delegated adoption of reviewed recommendations for all
16 historical questions. `resolution.md`, `resolution.json` and DR-001..016
record ANSWERED evaluation decisions with author/owner attribution and checked
source fragments. DR-001 now has a separate partial implementation in `late-completion/`. Other
implementation obligations remain pending. The
local no-transport backoff path already implements the resource contract being
probed; no broad decision is silently marked fully verified.
The historical archive and its original OPEN statuses remain a frozen record.

## Late-completion reference

`late-completion/` is a separate reference binding of the shared language-neutral
late-completion oracle. It reproduces both historical completion/shutdown races,
applies DR-001 to disposable evaluation copies, and checks the publication and
notification guards with two F-04 mutants and four independent canaries. The
parent remains live. An idle fake transport and controlled barriers expose real
addrConn behavior; this is not a full transport implementation test.

```sh
.venv/bin/python tools/addrconn_late.py --checkout /path/to/pinned/grpc-go --output-dir /tmp/late-proof
```

The same run executes the prior six-cell backoff regression on corrected source
and five named upstream cancellation/state-transition subtests. The historical
source pin and the evaluation patch are separate; `late-completion-manifest.json`
tracks committed oracle, adapter, profile and patch revisions. DR-001 remains
partial for broad conformance; all other implementation statuses stay pending.
