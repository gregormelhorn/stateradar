# StateRadar Benchmark Suite — Oracle Evidence

The strongest evidence: bugs StateRadar found that were NOT in the
model's training data — 11 bugs across 6 projects, including 2 critical
upstream discoveries reported as new GitHub issues.

## New bugs found (strongest evidence)

| Project | Bugs | Notes |
|---|---|---|
| recws-org/recws | 7 (2 critical) | #64 Shutdown panic, log.Fatalf kills process |
| silenceper/pool | 1 | connReqs never closed on Release |
| gobreaker | 1 | stale done() silently dropped (#122) |
| meilisearch/meilisearch | 2 | D1 double release (#6578), D4 missing increment (#6577) |
| pladaria/reconnecting-websocket | 1 critical | Terminal lock leak |
| valkey-glide | 1 critical | Missing timeout→release transition |

## Oracle-confirmed benchmarks (3/3)

Caveat: The public issues may predate model training cutoff. New bugs
above are the strongest independent-discovery evidence; these serve as
regression anchors.

| # | Project | Issue | Defect class |
|---|---|---|---|
| 1 | valkey-glide | [#5803](https://github.com/valkey-io/valkey-glide/issues/5803) | Caller terminal, resource active |
| 2 | python-websockets | [#1527](https://github.com/python-websockets/websockets/issues/1527) | Deadline expires, caller blocked |
| 3 | meilisearch | [#6508](https://github.com/meilisearch/meilisearch/issues/6508) | Caller terminal, claim eligible |
| 4 | silenceper/pool | [#32](https://github.com/silenceper/pool/issues/32) | connReqs never closed |

## Totals

11 pilots, 4 Oracle-confirmed, 11 bugs found, 6 GitHub issues filed,
24 methodology rules (PA-1 through PA-24).
