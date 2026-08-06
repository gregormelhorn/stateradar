# StateRadar Benchmark Suite

Evidence archive and regression test suite for StateRadar.
Each benchmark records what StateRadar found, what the oracle confirmed,
and the neutral requirements used as Part B input.

## Oracle Benchmarks (3 confirmed)

| # | Project | Issue | Defect class | Status |
|---|---|---|---|---|
| 1 | valkey-glide | #5803 | Caller terminal, resource ownership remains active | ✅ Confirmed |
| 2 | python-websockets | #1527 | Local deadline expires, caller notification blocked | ✅ Confirmed |
| 3 | meilisearch | #6508 | Caller terminal, scheduler admission claim eligible | ✅ Confirmed |

## Additional pilots (8)

| # | Project | Bugs found | Key finding |
|---|---|---|---|
| 4 | silenceper/pool | 1 | connReqs never closed on Release (confirmed by issue #32) |
| 5 | pladaria/reconnecting-websocket | 1 | Terminal lock leak after maxRetries |
| 6 | sony/gobreaker | 0 | stale done() callback silently dropped (issue #122 filed) |
| 7 | recws-org/recws | 7 | log.Fatalf kills process, keepalive CPU spin (2 issues filed) |
| 8 | lerouxrgd/recloser | 0 | lock-free CAS verified correct, State accessor proposed |
| 9 | cenkalti/backoff | 0 | 5 terminal states documented as API reference |
| 10 | snapview/tungstenite-rs | 0 | RFC 6455 compliance matrix |
| 11 | jd/tenacity | 0 | action-pipeline state model |

## Metrics

| Metric | Count |
|---|---|
| Total pilots | 11 |
| Oracle-confirmed critical bugs | 3/3 detected |
| Total bugs found | 11 |
| New issues filed | 6 |
| Methodology rules (PA-1 through PA-24) | 24 |
| Prompt versions | 13 (02-pilot v1.0 → v1.13) |
| Tool versions | 32 (v1.0 → v1.32) |
| Defect classes identified | 6 (PA-21 taxonomy) |
| Tracker-bug coverage (earlier pilots) | 93% |

## Regression test design

Each Oracle benchmark records:
- The pinned commit hash
- The neutral requirements (Part B input)
- The expected primary finding (matrix cell, missing transition)
- The oracle issue/PR for confirmation

A regression test verifies that StateRadar still finds the expected
primary finding on the same commit, to guard against prompt degradation.
