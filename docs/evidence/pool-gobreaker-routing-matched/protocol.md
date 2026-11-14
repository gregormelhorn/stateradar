# Matched routing protocol

Compare `--routing-variant routed` with `--routing-variant hybrid` at pack `0a88714`. Run each on silenceper/pool `6084537` and sony/gobreaker `27b8e2c`. Only the routing variant changes within each component. Each session uses GPT-6.1 Sol medium and ChatGPT login, the selective output mode, Jev 1.14.0, a fresh Flash Part B, an independent default $2 routing ledger, no companion claims, Codex CLI `0.167.0-alpha.4.1`, Go `1.27.3` and a 2,700 second timeout.

Run Pool routed first and gobreaker hybrid first, followed by the other variants. Separate checkouts and model ledgers isolate the two components in each wave. The agents receive the same pilot prompt revision and the same brief except for the routing label. The control tests and reference artifacts stay outside their sandboxes. Log completion status and retries separately from completed-turn usage. Compare wall time with awareness of concurrent sessions and shared provider caches.

## Acceptance and behavior

Both variants must pass matrix, guard, sidecar, reachability and blind-row gates. Hybrid also checks matrix render identity and strict sidecar regeneration. Check the blind report for as-is rows even when coverage passes. Report upstream and pilot behavior-test failures separately. Record an unfinished Codex turn and any missing token fields as unavailable.

For Pool, match the historical P-04a by the sequence pinned in the [independent probe](../pool-p04a/README.md). The first Get misses an idle receive, Put buffers before the admission lock, that Get queues at capacity, another Get takes the idle value and a later Put wakes the original waiter. Record the below-capacity branch separately. Compare Release stranding blocked Gets, same-caller Get while waiting and while holding, caller abandonment, queue backing storage retention, idle expiry, the Ping/Release race and callback effects. For gobreaker, use four independent controls covering stale completion, repeated current-generation completion, abandoned HalfOpen admission and reentrant callback. Include any additional evidenced behaviors from the runs. For each result distinguish omitted, partially described, cited and behavior-tested. Catalogue IDs are local to a run.

To reproduce the gobreaker controls, copy [the control file](gobreaker-controls.go.txt) into a clean pinned checkout as `pilot_controls_test.go` and run `go test -race -count=3 -timeout=30s -run '^TestPilot' -v .`. [Executed control output](control-results.txt).

## Measurement

Read the completed-turn event and retain all reported Codex usage fields, including input, cache hits, cache writes, output and reasoning. Compute total as input plus output and uncached input as input minus cache hits. Preserve exact token counters, elapsed time and retained-log requests. Record settled and reserved ledger costs by provider, including the hybrid schedule call. Ledger amounts use the pack rates and omit Codex usage via ChatGPT login. A paired comparison per component does not estimate run variance.
