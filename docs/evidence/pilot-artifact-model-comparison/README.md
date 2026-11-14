# Predictable artifacts and lower-cost controller screening

The runner now defaults to routed analysis with selective tool output and
GPT-6.1 Sol. The English pilot renders reviewed catalogue fields through a
shared helper, copies exact citation lines, and uses a consistent blind-row
contract. Matrix checks reject missing nonterminal state rows. Terra is
available explicitly with `--model gpt-6.1-terra`; these results do not
support making it the controller default.

Implementation: `8b8e854` (artifact workflow, checks and model selection),
`394ff35` (corrected controller write permission). The matched experiment
used **394ff35 for all four arms**, with identical settings within each
component except the controller model. See [frozen protocol](protocol.md)
and [execution notes](execution-notes.md).

## Matched outcome

| Component / controller | Codex credit equivalent | Flash/Jev ledger USD | Combined USD equivalent | Completion and gates |
| --- | ---: | ---: | ---: | --- |
| Pool / Sol | **Missing** | 0.018026 | **Unknown** | Service aborted after the report was saved; retained artifacts pass 6/6 local gates |
| Pool / Terra | 2.448755 | 0.008628 | 0.1065782 | Explicitly incomplete; 0/6 gates |
| gobreaker / Sol | 33.807440 | 0.039909 | 1.3922066 | Completed; 6/6 gates |
| gobreaker / Terra | 3.080195 | 0.015423 | 0.1386308 | Explicitly incomplete; 0/6 gates |

Both Terra sessions stopped after about 2.7 minutes, far below the 45-minute
limit and $2 provider budget. They wrote extraction and preliminary questions
but omitted catalogue/matrix completion, behavior probes, final verification
and blind Part B. A low price for those partial outputs is not a cheaper
accepted pilot. On gobreaker, Terra followed by the measured fresh Sol run
costs **$1.5308374**, about **10.0% more** than Sol alone. This is the observed
cost of a fresh-start fallback, not a measured continuation strategy.

Pool/Sol ran 1113.858 seconds before an OpenAI cybersecurity-risk service
flag. No final `turn.completed` usage event exists. It was not retried or
rephrased. The saved analysis passes all six local postflight gates, a
byte-identical strict sidecar regeneration and the blind-row audit. The
service failure still means the controller run did not complete normally.
**BLOCKED(Pool full-cost comparison): the Codex balance is missing.** Neither
zero nor the earlier diagnostic run's cost is substituted for it.

## Finding quality

Sol's retained Pool analysis covers historical P-04a with all three observable
outcomes: the original Get stays pending beside idle inventory, a later Get
takes that inventory, and a further Put completes the first. Its probe also
tests redundant creation below capacity. Release/Close waiter outcomes,
second Get while pending and holding, abandonment, queue retention, and
callback/handoff boundaries remain visible as distinct findings or open
questions. Terra identifies some broad lifecycle issues but does not develop
or test P-04a or the two second-Get cases.

Sol's gobreaker analysis covers all four independent controls: stale
completion accounting, duplicate done, abandoned HalfOpen allowance and
callback reentry. It also probes serialized wrapper reassignment as an open
contract question. Terra's preliminary questions overlap several controls,
but it does not verify them or produce the complete required analysis.
See the [behavior-by-behavior review](coverage.md), [independent control
results](control-results.txt), and the retained per-run reports.

All **101 Pool** and **115 gobreaker** blind situation rows have exactly one
classification in the Sol reports. A deliberately dropped classification
fails the audit. Code-derived catalogue observations limit blind independence;
the reports explicitly identify those dependencies. All domain decisions
remain open. Artifact gates are separate from reproduced component failures:
Pool's upstream timeout and Ping/Release race were retained as findings.

## Repair work and tool reads

| Matched arm | Retained-log reads | Actual blind requests | Catalogue rendering |
| --- | ---: | ---: | --- |
| Pool / Sol | 9 | 1 | First render passed; final identity passed |
| Pool / Terra | 0 | 0 | Not reached |
| gobreaker / Sol | 9 | 1 | One list-valued prose field rejected, then corrected; identity passed |
| gobreaker / Terra | 5 | 0 | Not reached |

Help and package-only commands are excluded from actual blind requests.
Distinct situations sharing an ID were accepted and all classified; neither
Sol run commissioned an unnecessary second blind answer for that reason.

The missing-state-row check caught a real intermediate gobreaker matrix with
unmarked rows. The controller corrected it before completion. Other repair
work remained: a malformed Flash draft on Pool, a truncated Flash draft and
allowed larger-budget rerun on gobreaker, citation corrections, a null-valued
Jev-result reader, and a Mermaid inheritance mismatch. All paid attempts and
controller work before completion are included where usage is available.
Nonzero commands also include expected component failures and an empty search;
they are not all runner failures. See [command work details](matched-work.json).

The earlier three-way experiment used a different pack. These runs do not
isolate the artifact helper's net cost effect. No causal percentage saving
is claimed for the helper. It improves format validation and removes a
contradictory review rule; model completion remains a separate requirement.

## Accounting and limits

Codex calculations use the published standard rates per million input,
cached input and output tokens: Sol 50 / 2.5 / 250 credits; Terra
25 / 1.25 / 125 credits, checked on 2026-11-14 at the
[official pricing page](https://learn.chatgpt.com/docs/pricing#token-rates).
Total input includes cache hits, which are subtracted before pricing uncached
input. Reasoning is already part of output and is not added again. All
recorded cache-write counters are zero. Credits convert at an explicitly
assumed **$0.04/credit**. These are comparable cost equivalents, not observed
account debits or incremental subscription charges. Provider ledger amounts
are runner estimates; cache/off-peak billing may reduce actual provider debit.

The four diagnostic pilots cost **$2.901866** in total; the Terra availability
smoke adds **$0.0226304**. The diagnostic Pool/Sol pilot completed at
$1.418397, but its different controller permission configuration makes it
context, not the missing matched value. Those attempts are retained in
[diagnostic measurements](diagnostic-measurements.json). Temporary-directory
preparation refusals occurred before model calls and incurred no provider cost.

The matched attempts have **$1.6554416 of known model cost**, including the
$0.018026 Pool/Sol provider ledger, **plus unknown Pool/Sol Codex cost**.
Across matched, diagnostic and smoke work, the known subtotal is
**$4.579938 plus that unknown Codex cost**. No provider reservation remains
open. The supervising implementation/audit chat is not metered by this
runner and is excluded; these figures are not a complete bill for this chat.

One matched run per model/component is screening evidence, not a general
reliability rate. The service cutoff cannot be attributed to routing or
model reasoning quality. It does limit end-to-end reliability and prevents
a complete two-component cost ranking.

## Standard and next measure

Keep **Sol controlling routed Flash/Jev work with selective output** as the
runner default. Keep matrix/hybrid variants explicit. Do not promote Terra
to the complete-pilot controller on the strength of its lower unit rates.
Before broader cost claims, capture controller usage incrementally across
service failures. A subsequent cheaper-model experiment should use bounded,
checkable phases with completion feedback and count every continuation or
fallback; it must meet the same behavior controls before promotion.

## Evidence

- [Matched measurements and complete available counters](matched-measurements.json)
- [Fresh sidecar regeneration and postflight checks](fresh-regeneration.json)
- [Blind row audit including its red probe](blind-row-audit.json)
- [Original regression failures](red.txt), [passing regressions](green.txt)
- [Permission regression failure](sandbox-red.txt), [passing test](sandbox-green.txt)
- [Full local gates](sandbox-gates.txt)
- [Pool service failure](matched/pool-sol/service-failure.json)
- [Pool Sol report](matched/pool-sol/summary.md), [Pool Terra report](matched/pool-terra/summary.md)
- [gobreaker Sol report](matched/gobreaker-sol/summary.md), [gobreaker Terra report](matched/gobreaker-terra/summary.md)

Raw commands, events, outputs and pinned checkouts remain under
`/tmp/stateradar-controller-matched-czn61wf4` and
`/tmp/stateradar-controller-4us5gpyo`. Curated artifacts are stored here;
trailing whitespace and empty end lines in archived Markdown are normalized;
citation-bearing line numbers are preserved. Hashes in the measurements refer to raw run files. Probe Go
files use `.go.txt` to avoid recursive test discovery; their original overlay
maps use raw-run paths. The collector scripts are retained in `scripts/`.
