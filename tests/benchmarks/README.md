# StateRadar Benchmark Suite

Evidence archive for StateRadar. The strongest evidence is the bugs
StateRadar found that were NOT in the model's training data: 11 bugs
across 6 projects, including 2 critical upstream discoveries reported
as new GitHub issues.

## New bugs found (strongest evidence — cannot be in training data)

| Project | Bugs | Notes |
|---|---|---|
| recws-org/recws | 7 (2 critical) | #64 Shutdown panic, log.Fatalf kills process |
| silenceper/pool | 1 | connReqs never closed on Release |
| gobreaker | 1 | stale done() silently dropped (#122) |
| meilisearch/meilisearch | 2 | D1 double release (#6578), D4 missing increment (#6577) |
| pladaria/reconnecting-websocket | 1 critical | Terminal lock leak |
| valkey-glide | 1 critical | Missing timeout→release transition |

## Oracle-confirmed benchmarks (3/3 — verified against known issues)

These document what StateRadar found when run against pinned revisions
of known bugs. **Caveat:** The public issues may predate the model's
training cutoff. The strongest evidence for independent discovery are
the new bugs above; these serve as regression anchors.

| # | Project | Issue | Defect class |
|---|---|---|---|
| 1 | valkey-glide | [#5803](https://github.com/valkey-io/valkey-glide/issues/5803) | Caller terminal, resource ownership active |
| 2 | python-websockets | [#1527](https://github.com/python-websockets/websockets/issues/1527) | Deadline expires, caller notification blocked |
| 3 | meilisearch | [#6508](https://github.com/meilisearch/meilisearch/issues/6508) | Caller terminal, scheduler claim eligible |

## Totals

11 pilots, 3 Oracle-confirmed, 11 bugs found, 6 GitHub issues filed,
24 methodology rules (PA-1 through PA-24).
