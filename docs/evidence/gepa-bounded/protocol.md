# Bounded GEPA experiment — declared before model calls

Objective: compare no final review, a fixed English final review, and a GEPA-selected
review under identical controller settings. This is a structured behavioral-claim
benchmark, not free-form bug discovery, full-pilot acceptance or a Part-B session.
No runtime or domain semantics are changed. Fixed requirements/checkers are not
optimized. Only the review paragraph is mutable.

Independence: use new components and externally authored Go contracts/source/tests.
Train: context.AfterFunc. Selection validation: x/sync singleflight. Locked final
test: time.AfterFunc/Timer and sync.OnceFunc/OnceValue. Whole components stay in
one split. Cases and reference probes are assembled here against upstream evidence;
there is no claim of independent human second review, private benchmark novelty,
or absence from model pretraining. Original upstream source/tests and content hashes
are retained. Labels/oracles/tests never enter task-model inputs. Reflective feedback
may expose train errors; validation contributes scores; final test never drives search.

Task: assess a fixed inventory of source-grounded behavioral claims, including
ordinary positive cases, identity/lifecycle edge cases, false generalizations and
explicitly unspecified application policy. Return complete structured verdicts,
source fragments and reasons. The deterministic scorer checks inventory, source
fragments and expected verdicts; it does not prove prose entailment. Reference
probes execute real APIs with controlled ordering and race detection. Citation
checks alone are not counted as semantic proof. Unknown policy stays OPEN.

Baseline: one bounded Flash draft and Jev citation batch, followed by a fresh
Codex gpt-6.1-sol medium analysis via ChatGPT login. Jev is advisory, never an oracle.
Fixed and GEPA review each receive the exact same immutable baseline within a
pair. No-review reuses that baseline; it is not a second charged execution.
All task inputs contain only the public case inventory/source and provider draft.
No task tools, web, repository history or reference outputs are available.

Three final paired repetitions per held-out component. Review order alternates
fixed/GEPA, GEPA/fixed, fixed/GEPA on the first component, reversed on the second.
Fresh baselines per repetition. Model, effort, source, providers, timeout and output
contract stay fixed. Repetitions expose variability; two held-out components do
not establish a broad population result. No retuning after final-test access.

GEPA 0.1.4, fixed seed 17, at most 8 metric calls (evaluated component reports),
engine stop threshold six (a completed iteration may add evaluations),
reflection batches of one component; at most three reflection proposals. No
cache reuse for stochastic final repeats. Selection score is correct-case fraction
plus at most 0.001 for shorter review text; a single case regression dominates this
secondary objective. This is a bounded length tie-break, not measured cost savings.
Use the installed real GEPA search loop and a custom Codex proposer. Baseline data
for train/validation is generated once and immutable. Final test is opened only
after selection is frozen. If GEPA keeps its seed, report that honestly.

Each Codex call: 240s timeout, one structural repair at most, counted separately.
No semantic repair from hidden labels. Invalid outputs/timeouts remain failed or
BLOCKED and are never silently discarded. Each experiment call is metered;
optimization, validation, final review and repair are separate cost categories.
Controller rates: 50 / 2.5 / 250 credits per million input/cached/output tokens,
verified 2026-11-15 at https://learn.chatgpt.com/docs/pricing ; $0.04/credit is an
explicit valuation assumption, not an account debit. Provider usage uses the
existing settled ledger. Per-call observations remain in reports alongside cost
aggregates. Total missing usage => unknown total, never zero.

Bound: 40 Codex launches maximum including reflection/repairs, $2 total provider
ledger cap, estimated experiment-controller spend ceiling $10 checked before each
new call. An in-flight call can exceed this soft ceiling; this is not a provider
hard cap. Unsettled usage stops subsequent calls. Human/supervising implementation
and review costs are not fully metered; report this gap and do not claim complete
all-in project cost. Measured rework includes every repair/retry; residual wrong
claims count as unresolved work, not free correction.

Promote neither routing nor prompt by default. Require no known-case regressions,
retention of all undecided policy questions, and repeated cost/quality benefit.
Report incremental cost, baseline-plus-review cost and optimization cost separately;
calculate amortization only if per-use savings are positive on eligible results.
