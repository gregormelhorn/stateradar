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
source fragments. All broad implementation obligations remain pending. The
local no-transport backoff path already implements the resource contract being
probed; none of the other decisions is silently implemented or marked verified.
The historical archive and its original OPEN statuses remain a frozen record.
