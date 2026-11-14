# Codex-led hybrid pilot on Pool and gobreaker

Codex steered both pilots via ChatGPT login. DeepSeek Flash proposed competing schedules, existing Jev and Flash checks remained available for bounded analysis, and a separate Flash session ran blind Part B. The runner checked the generated matrix against the structured cell fields and rebuilt the sidecar in strict mode.

Pool used `silenceper/pool` at `6084537` and pack `e2ab4ee`. Gobreaker used `sony/gobreaker` at `27b8e2c` and pack `bd8a61f`. The second pack SHA includes the shorter schedule prompt and increased response budget applied after the initial Pool Flash call was truncated. We retested both source files with the shorter prompt. The complete Pool analysis below comes from the initial hybrid session and its independent postflight.

| Measure | Pool | gobreaker |
| --- | ---: | ---: |
| States / events / generated cells | 4 / 26 / 104 | 3 / 30 / 90 |
| Pair orderings / open questions | 36 / 20 | 26 / 16 |
| Artifact gates | 7/7 after service cutoff | 7/7 in runner |
| Completed MCP calls / retained-log read attempts | 110 / 5 | 143 / 15 |
| Elapsed | 15:29 to cutoff | 18:22 |
| Codex input + output tokens | unavailable | 6,406,574 |
| Codex input excluding cache hits | unavailable | 160,785 |
| Flash schedule call, included below | $0.010626 | $0.005091 |
| All Flash calls | $0.025951 | $0.027007 |
| All Jev calls | $0.002382 | $0.002187 |
| Settled provider ledger | **$0.028333** | **$0.029194** |

Flash schedule amounts use the ledger's undiscounted rates. Both pilots ended with zero reserved balance. The ledger excludes Codex under ChatGPT login. The Pool service stopped the Codex session before its final summary and usage event, so its Codex token total and any overall savings are unknown. Gobreaker's earlier compact and standard runs recorded 7,448,642 and 8,638,386 Codex tokens respectively. They used different routing and output modes, so the observed 14% and 26% reductions cannot be attributed to the matrix renderer. The earlier Pool Codex-reference ledger was $0.018308 and Flash-writes was $0.040228. The hybrid provider ledger sits between them.

## Pool

The historical P-04a became `P-01a/Q-01` in this catalogue. Get A observes an empty inventory before taking the admission lock. Put buffers a connection between those two steps. At full capacity A queues despite idle inventory. Get B takes the idle connection first, and a later Put wakes A. Below capacity A creates a new connection while the idle value remains. The existing independent probe passed 25 times with the race detector. Both cases in the new pilot probe passed five race-detector repeats in postflight. The reachable state `GetWaitingWithIdle` is linked to the cited trace and test in the regenerated sidecar.

Flash W-06 gave the exact at-capacity schedule in its retained response. Truncation and invalid citation shape forced Codex to reconstruct the input and cite the implementation itself. The bounded retry cost $0.005209, produced eight mechanically valid candidates and omitted the exact P-04a schedule. This retry is outside the pilot ledger.

The pilot covered Release stranding queued and about-to-queue Gets, a second Get while the first is waiting or holding a lease, caller abandonment, queue backing storage retention, lazy idle expiry, and callback lifecycle effects around Release. The overlay verified missed receive, Release at the admission gap, distinct queued requests and FIFO dispatch, failed disposal reopening capacity, skipped overflow cleanup, Ping/Release panic and callback outcomes, and cleanup reentry. Caller abandonment, storage retention, the held-lease case and idle expiry were traced in source. The upstream suite timed out in `TestPool_Get`. The remaining suite passed when that one test was skipped. The all-probe race run found a race in the pilot scheduling hook. Pool Part B covered all 62 required rows and flagged two rows that carry as-is information (`Expiry`, `UV-15`). See [Pool postflight](pool-postflight.md).

## Gobreaker

All four independent controls passed three repetitions. The hybrid pilot recovered all four in its own probes: a stale completion can refresh an expired breaker before its accounting is discarded, a duplicate current completion can change counters, an abandoned HalfOpen completion can retain its admission slot, and a callback reentering the same breaker waits on its mutex. The final overlay passed all ten probes under the race detector, including panic effects, expiry equality, and wrapper reassignment redirecting an outstanding completion. The regular upstream Go suite passed. Its race run separately failed on a direct fixture read in `TestCustomCircuitBreaker`.

Flash supplied eight mechanically valid schedule candidates. Codex retained three and corrected five. Three corrections moved claimed interleavings outside the admission mutex. Two accounted for lazy expiry before the stale-generation check. The separate bounded retest cost $0.004266 and produced eight mechanically valid candidates. Part B covered all 56 required rows.

## Checks and proposed rollout

Both stored matrices matched fresh rendering byte for byte. Both sidecars regenerated byte for byte after deletion in fresh copies. The seven gates covered matrix identity, strict sidecar regeneration, matrix totality, guard checks, sidecar validation, reachability and blind row coverage. The pack's type check, consistency check, rule and deterministic selftests, routing selftests and golden/red tool tests also passed.

Keep `--routing-variant hybrid` opt-in while collecting matched runs on the same pack and component SHAs. The schedule proposals give Codex useful leads. The source sweep, lock-scope review and executable probes are still needed to cover missed and impossible interleavings. Keep the generated matrix as the deterministic output of reviewed structured fields.

[Protocol](protocol.md) and [measured counters](measurements.json). Raw local artifacts and logs are under `/private/tmp/stateradar-hybrid-routing.KBX5gr`.
