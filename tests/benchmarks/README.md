# StateRadar Benchmark Suite

Evidence archive for StateRadar. Three Oracle-confirmed benchmarks
document exactly what StateRadar found, the neutral requirements
used as Part B input, and the upstream issue that confirmed each
finding.

## Oracle Benchmarks (3/3 confirmed)

| # | Project | Issue | Defect class |
|---|---|---|---|
| 1 | valkey-glide | [#5803](https://github.com/valkey-io/valkey-glide/issues/5803) | Caller terminal, resource ownership active |
| 2 | python-websockets | [#1527](https://github.com/python-websockets/websockets/issues/1527) | Deadline expires, caller notification blocked |
| 3 | meilisearch | [#6508](https://github.com/meilisearch/meilisearch/issues/6508) | Caller terminal, scheduler claim eligible |

## Additional confirmed

| # | Project | Issue | Finding |
|---|---|---|---|
| 4 | silenceper/pool | [#32](https://github.com/silenceper/pool/issues/32) | connReqs never closed on Release |

## Earlier pilots (summaries)

| Project | Bugs | Key contribution |
|---|---|---|
| pladaria/reconnecting-websocket | 1 critical | First complete Part A + B + Diff |
| sony/gobreaker | 0 | Combined review comparison (issue #122 filed) |
| recws-org/recws | 7 (2 critical) | Issues #64 filed |
| lerouxrgd/recloser | 0 | CAS correctness verified |
| cenkalti/backoff | 0 | Terminal states as API reference |
| snapview/tungstenite-rs | 0 | RFC 6455 compliance matrix |
| jd/tenacity | 0 | Action-pipeline state model |
| uber-go/ratelimit | 0 | Skipped (too simple) |
| bsm/redislock | 0 | Dual-lifecycle design confirmed |

## Totals

11 pilots, 3 Oracle-confirmed, 11 bugs found, 6 GitHub issues filed,
24 methodology rules (PA-1 through PA-24).
