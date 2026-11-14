# Bounded reference and identity comparison

## What the expanded benchmark catches

The two immutable full-pilot archives each describe seven of the eight reviewed
behaviors. Both miss B05's specific serialized wrapper reassignment and recipient
accounting. Routed additionally overstates that a callback remains bound to the
original breaker. A counterfactual test of that assertion fails in all three race
runs; the replacement actually has zero requests and one success.

| Archived report | Correctly described | Complete executable case | Partial executable case | Refuted related claims |
|---|---:|---:|---:|---:|
| Routed | 7/8 | 5/8 | 1/8 | 1 |
| Matrix | 7/8 | 3/8 | 2/8 | 0 |

These counts use the expanded, explicitly ordered cases. They do not revise the
historical four-control presence score. Examples of partial test evidence are
matrix's one-outcome stale/abandonment probes and routed's original-error assertion
without an assertion about the returned value. The new separate reference
suite covers all eight; both archived suites and the reference suite were replayed
five times with the race detector. Reference probes are never credited to a pilot.

The machine validates reviewer annotations, hashes, exact evidence and named test
passes. It does not understand arbitrary prose or infer that a generic copying
mention entails a particular consequence. See the retained reviews and red/green
outputs for the boundary between review judgment and executed verification.

## Comparison scope

The frozen candidate asks the controller to distinguish captured values and
objects from mutable wrapper/key lookups, trace replacement between creation and
use, follow accounting to its actual recipient, check identity separately from a
generation number, and preserve documented exclusions or open intent questions.
It contains no gobreaker names, expected counters, transfer answers or fixed
number of findings. The baseline consists of unchanged excerpts from pilot 1.29.
The candidate paragraph is the sole prompt difference within each matched pair.

Four fresh sessions use the existing isolated pilot transport, selective output,
gpt-6.1-sol at medium reasoning with ChatGPT login, a Flash draft and Jev verification
pinned to jev-1.14.0. The order is gobreaker baseline/candidate, then transfer
candidate/baseline. This reverses order across inputs, not within a repeated input.
All probes, retries, rereads and reviews inside each session count toward its cost.

This is a bounded extraction/trace/finding-review experiment. There is no matrix,
blind Part B, full pilot gate score or production implementation change. The
transport's smoke status correctly records that full artifact gates did not run.
Bounded validation checks report shape and fragments, actual probe discovery,
unchanged source and complete accounting. Behavioral review is separate.

Gobreaker is known regression evidence. The six synthetic transfer cases include
two mutable-indirection positives and four no-redirection controls: fixed target
capture, explicit identity+epoch guard, value receiver copy and caller-variable
rebinding. They were created after freezing the candidate and not used to retune
it. The same author created and reviewed them; they are not independent held-out
validation. Each expected sequence was executed five times without model access
to the oracle or answers.

## Gobreaker result

| Bounded session | Explicit benchmark coverage | Full / partial test bindings | Codex equivalent | Flash/Jev ledger | Combined equivalent | Seconds | Log rereads | Failed commands |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 8/8 | 7 / 0 | $0.498386 | $0.005859 | $0.504245 | 658.201 | 4 | 1 |
| Candidate | 7/8 | 5 / 1 | $0.5785212 | $0.004904 | $0.5834252 | 686.094 | 3 | 0 |

The candidate costs 15.7% more despite fewer tool calls (38 versus 56) and fewer
log rereads. The increased cost is in Codex; the provider ledger is slightly
smaller. Neither count alone predicts total cost. This single pair does not
isolate a general causal effect of the paragraph from stochastic model behavior.

Both sessions find and test wrapper reassignment. The baseline already found it
without the added paragraph, so recovery relative to the older full-pilot reports
cannot be attributed to the candidate. The candidate adds concrete copying,
variable-rebinding, replacement-generation and foreign HalfOpen completion cases.
However, it does not work through B06's ordinary success sequence: two outstanding
Allow callbacks, first success, unchanged Requests=2, third refusal, second success
closing. Its F12 uses a first **failure**, changes generation and makes the other
callback stale. Cumulative-count prose is relevant but does not preserve the
required explicit sequence. These are different consequences, not just Q grouping.

B01 is retained in the candidate's summary and F04/F21, rather than marked as a
missing finding. The executed variants use replacement of the target, or a
panicking same-instance notification, so the ordinary same-instance control is
only partially represented by its tests. Both bounded sessions leave B04 reentry
as a source-only finding. The eight-case scores are a review of these cases, not
a certification of every sentence or every possible finding in either report.

Both controllers repaired their own drafts. Baseline expands 23 initial rows to
29 final rows and executes two passing probe suites; candidate keeps 24 rows and
executes one passing suite. Row changes include provenance/test upgrades and
scope refinements, so they are not counted mechanically as errors. Baseline's
review corrects misleading Flash premises about Counts refreshing expiry,
rejected admissions' internal generation return, and HalfOpen failure. Candidate
narrows a contradicted Jev claim that placed all mutex acquisition inside
`afterRequest`: admission and reads also acquire it. Final Jev batches contain
93 parts (15 unclear) and 100 parts (19 unclear, one contradicted), respectively.
These are review workloads; an unclear verdict is not itself a false finding.

Baseline's sole nonzero command is an attempted `local_models.py batch --help`;
the actual command is `jev-batch`. Its correction is included in Codex usage.
The shared task's Jev parenthesis uses report-style nested citation notation,
whereas the existing CLI requires flat `kind`, `line`, and `fragment` fields.
Both controllers inspected the CLI and sent the actual schema successfully. Keep
this common setup limitation visible; correct that hint before a new experiment,
without rewriting the measured prompt or attributing discovery reads solely to
the candidate. No model output was repaired outside its metered session.

## Transfer result

| Bounded session | Correct recipient classes | Full / partial test bindings | Codex equivalent | Flash/Jev ledger | Combined equivalent | Seconds | Log rereads | Failed commands |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Baseline | 6/6 | 5 / 1 | $0.5020296 | $0.002671 | $0.5047006 | 635.315 | 1 | 0 |
| Candidate | 6/6 | 5 / 1 | $0.4328068 | $0.002592 | $0.4353988 | 537.521 | 0 | 0 |

The candidate costs 13.7% less in this pair. Both make 45 tool calls and run two
passing suites; the candidate uses no retained-log reread versus one. Both retain
the two redirection cases A/D and correctly exclude redirection in B/C/E/F. This
is six reviewed recipient/effect classes, not six identical fully executed
canonical schedules or a universal false-positive rate. Both generated suites
test F after mutation of the original Port.Target but do not separately execute
the canonical caller-variable rebinding. That test binding remains **partial**.
Candidate C uses a copied replacement with Requests already one; the canonical
oracle uses a fresh zero-counter replacement. Both demonstrate the identity guard
and no added success. The starting request count does not participate in the guard.

Baseline expands 66 rows to 74, candidate 35 to 40. These totals reflect different
grouping and added sequences; they are not a count of unique correct findings.
Baseline corrects the expression that panics during C admission and adds explicit
caller-departure and restored-eligibility traces. Candidate adds departure,
panic/recovery and repeated-delivery orderings. Baseline's final Jev batch has 68
parts, six unclear and one contradicted; candidate's has 79 parts and 25 unclear.
The baseline's contradicted `A_later_eligible` claim is actually supported by the
source and independent replay: an earlier epoch mismatch does not consume the
callback, so a later matching target can receive success. The controller retains
it after review. Jev disagreement is review input, not an automatic veto or a
reason to change the observed outcome.

## Acceptance and recommendation

All four bounded sessions complete with unchanged input sources, valid report
fragments, complete cost accounting, and nonempty passing probes. Independent
replay selects the final additive overlay, preserves source and existing tests,
and runs each generated suite three times with the race detector:

| Session | Top-level tests | Pass events including subtests across three repetitions |
|---|---:|---:|
| Gobreaker baseline | 22 | 213 |
| Gobreaker candidate | 23 | 171 |
| Transfer baseline | 19 | 315 |
| Transfer candidate | 9 | 189 |

The replay also demonstrates rejection of an empty discovery run even when Go
returns exit 0. The strict semantic-review audit accepts the bounded baseline
8/8, rejects gobreaker candidate 7/8 at B06, and accepts both transfer class scores
6/6 while retaining their partial test coverage. Passing execution is therefore
not conflated with complete finding coverage. See `results/independent-replay.txt`,
`results/*-audit.json`, and the attributed `*-review.json` files.

**Keep the standard pilot prompt and routed execution unchanged.** The candidate
finds useful additional identity variants but does not consistently improve
cost and retained findings. Summing these two inputs gives $1.0089456 for baseline
and $1.0188240 for candidate (+1.0%), with a missing gobreaker case in the latter.
That sum is descriptive, not a workload-weighted forecast. No failed run, missing
usage or outside repair has been priced as zero to manufacture a saving.

The next proposed experiment is an identity review appended to an existing
findings list, with an explicit obligation to retain prior conditions/orderings
and a direct caller-variable-rebinding probe. Use independently reviewed transfer
cases and repeated matched runs before promotion. Fix the shared task's schema
hint in a new protocol, leaving this measured input immutable. Neither domain
copying policy nor any outstanding intent question is decided by this experiment.

## Cost interpretation

Costs include complete Codex session usage plus all settled Flash/Jev calls,
including unsuccessful commands and corrective work within the session. Missing
usage would leave totals unknown. Common implementation, this supervising review
chat and human review are excluded; outstanding semantic work is reported as work,
not assigned an invented dollar amount.

The [official OpenAI Standard rates](https://learn.chatgpt.com/docs/pricing#token-rates)
were checked on 2026-11-14: Sol 50/2.5/250 credits per million uncached/cached/output.
Conversion uses the same explicit $0.04/credit assumption as the previous comparison.
The provider ledger retains the same conservative Flash peak/uncached estimate;
see the [existing pricing verification](../mutation-rationale-cost/pricing-note.md).
These are comparable model-cost equivalents, not subscription marginal charges or
verified account debits. No inference about the missing historical Pool usage is
made from this experiment.
