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

## Fault-class × detector coverage (ODC)

Dominant fault class per finding, from `formats/rules.toml`. Triggers per
the case artifacts (grpc-go-2669 tracked separately).

| Fault class | Trigger | Benchmark case(s) |
|---|---|---|
| F-07 lifecycle coupling | step-4 matrix walk; doctrine mapping (PA-21) | valkey-glide-5803 (Q-04), silenceper-pool-32 (primary) |
| F-08 double release | step-4 matrix walk | valkey-glide-5803 (Q-02, Q-03), meilisearch-6508 (Q-D1) |
| F-09 cancellation leak | step-4 matrix walk | meilisearch-6508 (Q-D2) |
| F-13 delay / late | step-4 matrix walk | meilisearch-6508 (Q-D3) |
| F-20 blocked progress after terminal event | step-4 matrix walk | python-websockets-1527 (Q-C1) |

Fault classes with zero benchmark findings so far: F-01, F-02, F-03, F-04, F-05, F-06, F-10, F-11, F-12, F-14, F-15, F-16, F-17, F-18, F-19, F-21.
