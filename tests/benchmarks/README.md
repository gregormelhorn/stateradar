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
| meilisearch/meilisearch | 3 | D1 double release (#6578), D4 missing increment (#6577), S3 multipart cancel detach (#6510) |
| pladaria/reconnecting-websocket | 1 critical | Terminal lock leak |
| valkey-glide | 1 critical | Missing timeout→release transition |

## Wired benchmark standard

A wired benchmark case (with `expected.json`) must carry a canonical
`analysis.json` that passes `dsc_check` — including gate-type and
upstream-guard annotations on every base event, ODC `fault`/`trigger`
fields on every question, and asserted-absence `completeness` block.
Convergence `convergence/run*.json` recordings are raw pilot output
and exempt from dsc_check; only the canonical merged sidecar is
gate-checked.

## Oracle-confirmed benchmarks (6/6)

Caveat: The public issues may predate model training cutoff. New bugs
above are the strongest independent-discovery evidence; these serve as
regression anchors.

| # | Project | Issue | Defect class |
|---|---|---|---|
| 1 | valkey-glide | [#5803](https://github.com/valkey-io/valkey-glide/issues/5803) | Caller terminal, resource active |
| 2 | python-websockets | [#1527](https://github.com/python-websockets/websockets/issues/1527) | Deadline expires, caller blocked |
| 3 | meilisearch | [#6508](https://github.com/meilisearch/meilisearch/issues/6508) | Caller terminal, claim eligible |
| 4 | silenceper/pool | [#32](https://github.com/silenceper/pool/issues/32) | connReqs never closed ([current analysis](silenceper-pool-32/domain-analysis/summary.md)) |
| 5 | grpc-go | [PR #2669](https://github.com/grpc/grpc-go/pull/2669) (fixes #2663/#2636) | Stale backoff after established connection (F-18) |
| 6 | meilisearch/s3 | [#6510](https://github.com/meilisearch/meilisearch/issues/6510) | Structured-cancellation: cancel detaches multipart uploads |

## Totals

12 pilots, 6 Oracle-confirmed, 12 bugs found, 6 GitHub issues filed,
72 methodology rules. The grpc-go-2669 case
(2026-08-07, pack v1.50) is the first pilot run with ODC fields,
SHARD categories, and blind-pass row-coverage checking end to end;
its 15 non-oracle findings describe the frozen v1.18.0 tree and are
unverified against current grpc-go.

<!-- generated:odc start -->

## Fault-class × detector coverage (ODC)

Dominant fault class per finding, from `formats/rules.toml`. Generated from benchmark sidecar `fault`/`trigger` fields.

| Fault class | Trigger | Benchmark case(s) |
|---|---|---|
| F-01 | step-4 matrix walk | grpc-go-2669 (Q-15), silenceper-pool-32 (Q-05) |
| F-02 | doctrine mapping (PA-22); step-2 test replay | grpc-go-2669 (Q-04), grpc-go-2669 (Q-07) |
| F-03 | step-2 test replay | grpc-go-2669 (Q-14) |
| F-03 | step-4 matrix walk | silenceper-pool-32 (Q-04) |
| F-04 | pairs table + z3 proof | grpc-go-2669 (Q-01) |
| F-04 | step-4 matrix walk | silenceper-pool-32 (Q-03) |
| F-05 | adversarial trace | grpc-go-2669 (Q-16) |
| F-05 | step-4 matrix walk | silenceper-pool-32 (Q-06) |
| F-06 | step-1 extraction | grpc-go-2669 (Q-10) |
| F-07 | seam-contract sweep; step-5 lint | grpc-go-2669 (Q-11), grpc-go-2669 (Q-12) |
| F-07 | step-4 matrix walk | silenceper-pool-32 (Q-01) |
| F-07 | step-4 matrix walk; doctrine mapping | valkey-glide-5803 (Q-04) |
| F-08 | step-4 matrix walk | meilisearch-6508 (Q-D1), valkey-glide-5803 (Q-02), valkey-glide-5803 (Q-03) |
| F-09 | step-4 matrix walk | meilisearch-6508 (Q-D2) |
| F-10 | step-5 lint + multi-instance probes | grpc-go-2669 (Q-13) |
| F-11 | step-3 lock-discipline annotation | grpc-go-2669 (Q-02) |
| F-12 | step-3 checklist | silenceper-pool-32 (Q-02) |
| F-12 | step-4 matrix walk | silenceper-pool-32 (Q-05) |
| F-13 | step-3 checklist + step-5 lint | grpc-go-2669 (Q-08) |
| F-13 | step-4 matrix walk | meilisearch-6508 (Q-D3) |
| F-14 | step-3 checklist | silenceper-pool-32 (Q-02) |
| F-14 | step-4 matrix walk | silenceper-pool-32 (Q-06) |
| F-15 | step-4 matrix walk | grpc-go-2669 (Q-09), silenceper-pool-32 (Q-03) |
| F-17 | step-3 checklist | silenceper-pool-32 (Q-02), silenceper-pool-32 (Q-UV-01) |
| F-18 | seam-contract sweep; step-1 extraction + traces | grpc-go-2669 (Q-03), grpc-go-2669 (Q-05) |
| F-18 | step-3 checklist | silenceper-pool-32 (Q-UV-01) |
| F-19 | doctrine mapping (PA-22) | grpc-go-2669 (Q-06) |
| F-20 | step-4 matrix walk | python-websockets-1527 (Q-C1), silenceper-pool-32 (Q-01) |

<!-- generated:odc end -->
