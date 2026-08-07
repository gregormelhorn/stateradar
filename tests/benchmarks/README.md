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
| 5 | grpc-go | [PR #2669](https://github.com/grpc/grpc-go/pull/2669) (fixes #2663/#2636) | Stale backoff after established connection (F-18) |

## Totals

12 pilots, 5 Oracle-confirmed, 11 bugs found, 6 GitHub issues filed,
24 methodology rules (PA-1 through PA-24). The grpc-go-2669 case
(2026-08-07, pack v1.36) is the first pilot run with ODC fields,
SHARD categories, and blind-pass row-coverage checking end to end;
its 15 non-oracle findings describe the frozen v1.18.0 tree and are
unverified against current grpc-go.

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
| F-01 missing transition | step-4 matrix walk | grpc-go-2669 (Q-15) |
| F-02 transfer fault | doctrine mapping (PA-22); step-2 test replay | grpc-go-2669 (Q-04, Q-07) |
| F-03 output fault | step-2 test replay | grpc-go-2669 (Q-14) |
| F-04 sneak path | pairs table + z3 proof | grpc-go-2669 (Q-01) |
| F-05 corrupt state | adversarial trace | grpc-go-2669 (Q-16) |
| F-06 trap door | step-1 extraction | grpc-go-2669 (Q-10) |
| F-07 lifecycle coupling | seam-contract sweep; step-5 lint | grpc-go-2669 (Q-11, Q-12) |
| F-10 synchronized reset herd | step-5 lint + multi-instance probes | grpc-go-2669 (Q-13) |
| F-11 callback deadlock | step-3 lock-discipline annotation | grpc-go-2669 (Q-02) |
| F-13 delay / late | step-3 checklist + step-5 lint | grpc-go-2669 (Q-08) |
| F-15 out-of-order / stale | step-4 matrix walk | grpc-go-2669 (Q-09) |
| F-18 subtle value fault | step-1 extraction + traces; seam-contract sweep | grpc-go-2669 (Q-03 **oracle**, Q-05) |
| F-19 unimplemented requirement | doctrine mapping (PA-22) | grpc-go-2669 (Q-06) |

Fault classes with zero benchmark findings so far: F-12, F-14, F-16,
F-17, F-21 — for grpc-go-2669 the first four were probed by the
checklist and found correctly handled (a checked non-defect, not a
blind spot); F-21 needs a 07-test-audit case.

The grpc-go columns are the first data point for the portfolio
question the ODC fields exist to answer: the four pre-v1.11 benchmark
cases were found by a single trigger (matrix walk), the v1.15 pilot's
sixteen findings came through nine distinct detectors.

**silenceper-pool-32:** unwired — MANIFEST.md present but no
expected.json or run_benchmark case. This case was found by the
statechart method but was never wired into the deterministic runner.
