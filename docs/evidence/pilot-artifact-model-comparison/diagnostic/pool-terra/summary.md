# Partial analysis — not complete

model routing: on (unevaluated, cascade plan stage 3)

The command `go test -timeout 20s ./...` failed: TestPool_Get timed out at channel_rpc_test.go:93 while Get waited at channel.go:137 (pilot log 008). The test expects ErrMaxActiveConnReached after exhausting capacity; README.md:15 describes waiting. Neither settles shutdown or timeout policy.

Draft extraction and Jev review ran on README.md, channel.go, pool.go and channel_rpc_test.go. All draft citation checks passed; test-file verification returned two unclear judgments. Drafts and questions have not been fully reviewed or consolidated. Preliminary observations are in extraction.md and open-questions.md.

The statechart, catalogue, matrix, guard proofs, probes, invariants, complete traces, sidecar, verification and blind Part B are incomplete. No blind table was authored or dispatched. DSC and reachability checks failed because analysis.json is absent (pilot logs 023 and 025). Matrix and guard gates were not run because inputs do not exist. No finding has completed Step 8.

Skipped calls: seam-contract Jev batches, ordering checks, finding verification and blind pass await reviewed inputs. No provider call failed. Source and existing tests were not edited.

Ledger: routing.sqlite. Last status: limit 2,000,000 microdollars, committed or reserved 9,160 microdollars, eight settled calls (four DeepSeek Flash and four Jev); full status in pilot log 024.
