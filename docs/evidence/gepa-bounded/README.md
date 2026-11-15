# Bounded GEPA review experiment

This experiment connects the actual `gepa==0.1.4` optimizer to the existing Codex
ChatGPT-login transport and metered Flash/Jev drafting. It compares stopping after
the baseline with a fixed final-review paragraph and a GEPA-selected paragraph.
The complete protocol was written before paid model calls; inputs are frozen in
`runs/input-freeze.json`. The standard pilot prompt and routing are unchanged.

## Result and decision

**Targeted final review improves correction and scope precision in this bounded
task. A quality advantage specific to GEPA is not demonstrated.** The owner asked
that benefits beyond cost reduction receive more weight. We retained the frozen
primary comparison, added a separately declared post-selection correction
diagnostic, and examined rationale precision against executed controls. The
additional evidence was never fed back to optimization.

| Quality measure | No final review | Fixed review | GEPA review |
|---|---:|---:|---:|
| Primary correct verdict observations | 42/42 | 42/42 | 42/42 |
| Explicit intervening-rearm qualification in timer-03 reasons | 0/3 | 3/3 | 3/3 |
| Seeded errors corrected in supplementary diagnostic | 0/6 (unchanged input) | 6/6 | 6/6 |
| Correct controls retained in supplementary diagnostic | 8/8 (input) | 8/8 | 8/8 |
| New wrong verdicts in supplementary diagnostic | — | 0 | 0 |
| Structural repair calls in final evaluation / diagnostic | 0 / — | 0 / 0 | 0 / 0 |

The primary unit is **14 distinct held-out claims on two components, each repeated
three times**, not 42 independent problems. All primary arms preserve unknown
application-policy questions. The supplementary diagnostic has one review per
component and arm; its seeded errors are known inputs, not newly discovered bugs.
The no-review diagnostic entries describe retaining those inputs, not additional
model calls. See [audited totals](runs/audited-summary.json),
[diagnostic protocol](quality-extension.md) and [raw diagnostic results](runs/quality-extension.json).

The scope review finds a useful distinction hidden by the 7/7 verdict score:
after a timer callback begins, a first Reset of its expired firing returns false;
after that Reset rearms the timer, a second Reset can return true while the earlier
callback still runs. Every fixed and GEPA review explicitly adds this qualifier.
Two public-API controls run five times with the race detector verify the rearm
case and repeated Stop. [Attributed annotations](scope-review.json) preserve the
exact original reasons; their integrity checker does not claim to prove prose
entailment. The frozen timer-03 inventory itself omits an explicit intervening-
Reset exclusion. Its primary label assumes that exclusion. This evaluation-scope
limitation remains visible instead of silently rewriting the historical score.

A further [OPEN question, Q-GEPA-01](open-questions.md), concerns the scope of
Go's func-timer Stop documentation. Repeated Stop can return false even when the
first Stop prevented the callback. Three advisory Flash drafts repeat the broader
documentation sentence, and Jev accepts its citation. The supervising review
found this mismatch; neither experimental review arm receives discovery credit.
It lies outside the seven frozen timer claims and illustrates what the score
does not measure. No upstream requirement or runtime behavior was changed.

## Measured costs and search behavior

All amounts below are USD **cost equivalents**, including Codex, not account
debits. Ranges apply the observed Sunday Flash rates with unknown input-cache
split. The original conservative peak/no-cache provider ledger is retained and
audited separately. [Pricing sensitivity](runs/cost-sensitivity.json) records both
the bounds and the controller-cache counterfactual, using
[Flash pricing](https://api-docs.deepseek.com/quick_start/pricing/) and
[Jev pricing](https://help.typesafe.ai/articles/5187202169-how-much-does-jev-cost)
verified on 2026-11-15.

| Strategy or work | Cost equivalent |
|---|---:|
| No review, six primary trials | $0.16448–0.16628 |
| Fixed review, same baselines and trials | $0.38623–0.38804 |
| GEPA review, same baselines and trials | $0.32717–0.32897 |
| One-time optimization, including repair | $0.52786–0.52955 |
| Additional seeded-error reviews, fixed / GEPA | $0.04327 / $0.03160 |
| Actual experiment, all 34 Codex calls and provider calls, baseline charged once | $1.15166–1.15515 |

The strategy rows are alternatives sharing identical baseline outputs. They must
not be summed as the actual experiment bill. There were two optimization baseline
runs, seven metric evaluations, two reflection proposals, six final baselines,
twelve primary reviews, four supplementary reviews, and **one structural repair**
of an optimization baseline: 34 Codex calls in total. No semantic errors were
repaired using hidden labels. Supervising implementation, qualitative review and
human effort remain unmetered; these figures are not complete project costs.

GEPA selected candidate 2 of three, including the fixed seed. Every candidate
already achieved 7/7 validation verdicts. The preregistered length tie-break chose
the shorter paragraph; the optimizer did not demonstrate a quality improvement
or optimize measured expenditure. The paragraph explicitly distinguishes return
values and their causes from deferred work starting/finishing and includes actions
created after cancellation. [Selection and full English prompts](runs/selected-prompt.json)
retain all candidates and scores.

The primary review-only difference is $0.05907, but with all Codex input valued
without its cache discount it shrinks to $0.00654 (about 2.3% of fixed review
cost). Thus the observed saving is strongly cache-sensitive. The conservative
ledger's nominal break-even of about 54 future reviews assumes the small observed
cost difference persists; this experiment does not establish that assumption.

**Recommendation:** retain selective final review and the experimental GEPA
adapter; do not promote GEPA as the standard reviewer yet. The next experiment
should seek valid findings missing from the input, detect contradictory source
wording and scope errors, preserve correct controls and OPEN questions, and test
transfer on new components. Obtain separate oracle review and freeze new held-out
cases before optimization. Prioritize those quality outcomes, then compare total
measured cost and required rework. The present held-out set is now consumed.

## Independent source and scope

The new dataset has 28 explicit behavioral-claim obligations on four components.
The authors of the source contracts and original tests are the upstream Go authors,
not the prompt optimizer. Snapshots, BSD licenses and source hashes are retained in
`upstream/` and `upstream-pins.json`. Public source locations:

- [Go context](https://github.com/golang/go/blob/go1.27.3/src/context/context.go)
- [x/sync singleflight v0.11.0](https://github.com/golang/sync/blob/v0.11.0/singleflight/singleflight.go)
- [Go time](https://github.com/golang/go/blob/go1.27.3/src/time/sleep.go)
- [Go sync](https://github.com/golang/go/blob/go1.27.3/src/sync/oncefunc.go)

Train uses context.AfterFunc; validation uses singleflight; locked final evaluation
uses time.AfterFunc/Timer and sync.OnceFunc/OnceValue. Components are disjoint.
Train and timer deliberately share temporal themes; this measures component
transfer, not independence of every concept. The public inventory includes normal
controls, false generalizations and unknown application policy. The hidden oracle
is assembled locally from upstream contracts/source and executable probes. There
is no independent human second review or claim that public source is absent from
model pretraining. Original upstream test snapshots supply provenance; the executed
reference suite is our public-API probe, not an execution of every upstream test.

The task model judges the provided claims. Therefore scores measure bounded
behavioral judgment and correction, not spontaneous discovery of unknown bugs,
full matrix coverage, test generation, or a fresh blind Part B. Exact citation
matching does not prove that every sentence in a rationale follows from the source.
Unknown application policy is scored as unspecified with an OPEN question; no
application semantics are silently decided.

## Mechanisms and negative controls

- `tools/gepa_eval.py`: exact inventories, source fragments, explicit corrections,
  open policy questions and split separation. A permissive scaffold fails eleven
  rejection assertions (`evaluator-red.txt`); the implementation passes 13 tests.
- `tools/gepa_search.py`: real GEPA with a custom provider adapter, fixed seed and
  bounded metric budget. The inert scaffold fails (`search-red.txt`); the real
  algorithm proposes and selects a better mock candidate (`search-green.txt`).
  Mock scores prove integration behavior only, not model quality.
- `tools/run_gepa_comparison.py`: isolated model calls, immutable inputs and final
  selection, exact child usage, settled provider ledger, timeout/repair accounting.
  Launch and cost caps reject uncertain costs and are tested red/green.
- `tools/gepa_report.py`: re-reads raw output and usage, rejects omitted costs or
  repairs, checks shared baselines and replays all scores. The actual experiment
  counts each paid baseline once; counterfactual strategy totals include the
  baseline in each alternative without claiming three actual baseline charges.
  Two additional mutations of copied archived runs initially escaped detection:
  removing a whole trial from every arm and removing provider costs from every
  strategy. Both rejection tests were observed red, then the audit was strengthened
  to bind the full declared trial inventory and settled provider totals. All seven
  accounting tests now pass (`archive-audit-red.txt`, `archive-audit-green.txt`).
- `label-red-probes.txt`: each of 28 single-verdict corruptions lowers the score.
- `reference-output.jsonl`: four public-API reference groups x five race-detector
  repetitions; exact test and package completion required. The source/runtime
  version is pinned. Application policy questions have contract-scope review,
  not a fabricated executable policy oracle.

Reproduce deterministic checks without overwriting the archived reference:

```sh
uv pip install --python .venv/bin/python -r docs/evidence/gepa-bounded/requirements.txt
.venv/bin/python tools/verify_gepa_reference.py
.venv/bin/python tools/selftest/test_gepa_eval.py
.venv/bin/python tools/selftest/test_gepa_budget.py
.venv/bin/python tools/selftest/test_gepa_search.py
.venv/bin/python tools/selftest/test_gepa_report.py
.venv/bin/python tools/selftest/test_gepa_rates.py
.venv/bin/python tools/verify_gepa_quality.py
.venv/bin/python tools/gepa_report.py docs/evidence/gepa-bounded/runs
.venv/bin/python tools/gepa_cost_sensitivity.py docs/evidence/gepa-bounded/runs
```

Run the complete gate chain from the repository root, including previous
late-completion, mutation, semaphore, pack and tool checks:

```sh
bash docs/evidence/gepa-bounded/scripts/full_gates.sh --checkout /path/to/grpc-go-v1.18.0
```

[Executed output](full-gates.txt) and [command/exit status](full-gates-status.json)
retain the local acceptance run. Expected-red historical and mutant controls in
that log are successful negative checks, not unresolved gate failures.

A **new paid experiment** requires an unused output path:

```sh
.venv/bin/python tools/run_gepa_comparison.py /tmp/new-gepa-comparison
```

The runtime reference requires Go 1.27.3; the optional experiment dependency is
isolated from consumer requirements. CI replays the deterministic tests and
archived outputs; it does not launch paid model optimization.

## Cost boundaries

Codex uses the existing ChatGPT login, not an OpenAI API key. Standard Sol rates
were verified on 2026-11-15 at [official pricing](https://learn.chatgpt.com/docs/pricing):
50 input, 2.5 cached input, 250 output credits per million tokens. The report values
credits at $0.04/credit, the explicitly retained comparison assumption. These are
cost equivalents, not invoice debits or an assertion about marginal subscription
charges. Flash/Jev costs use the existing rate-based settled ledger.

Every experiment Codex call, optimization proposal, validation evaluation and
structural repair is charged. No hidden-label semantic repairs are allowed.
Residual incorrect judgments remain unresolved work. Supervising implementation,
this report and any human labor are not fully metered and are not priced as zero.
The results cannot establish a complete all-in project expenditure.
