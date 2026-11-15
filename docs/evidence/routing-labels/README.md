# Bounded source-fragment evaluation for model routing

This benchmark measures one narrow routing operation: whether a **cited
fragment** supports a supplied claim or event ordering. It is not a statechart
pilot or a measure of full discovery coverage. The supervising AI prepared 20
checks and proposed labels before any evaluated model output. Separate fresh,
isolated Codex sessions reviewed all cases without seeing proposed labels or
Jev results. Both AI reviews agreed on all 20; no human review occurred.
Agreement is evidence, not proof of independence or correctness.

The [protocol](protocol.md) fixes the inputs, labels, component split and
comparison before the measured calls. Once and Pipe form the development set;
Buffer and Value form the held-out set for this comparison. All four are public
Go 1.27.3 components used in prior project experiments, so this is neither an
unseen-source test nor evidence against model pretraining contamination. The
same supervising AI prepared the development and held-out cases. No tuning or
threshold selection was performed between the development and held-out calls.
The dev results were frozen before the held-out calls.

The cases include supported, contradicted and insufficient fragments,
requirement-scope orderings and a missing callee-error-contract check. Their
source hashes, single-line fragments, proposed labels and independent review
are under `inputs/`, `reference-review/`, and `frozen/`. All costs and raw
recorded comparison outputs are under `runs/`; `reviewed-results.json` records
all 20 reviewed judgments and three open questions. No model verdict removes a
question, establishes domain behavior or authorizes automatic acceptance.

## Direct fragment checks

| Dataset | Jev 1.14.0 exact labels | Direct Codex exact labels | False support |
| --- | ---: | ---: | ---: |
| Development: 2 components, 10 checks | 10/10 | 10/10 | 0 for each |
| Held out from development: 2 components, 10 checks | 9/10 | 9/10 | 0 for each |
| Total | 19/20 | 19/20 | 0 for each |

The models missed different cases. Jev called A03 `contradicted` even though
the cited zero-value sentence does not itself contemplate the prior Swap; this
is an overstatement of **fragment scope**, not a conclusion about runtime
behavior. Direct Codex called B05 `unclear`, demanding an executable return
where the quoted API comment explicitly states EOF. The check's unqualified
wording permits a stricter reading that requires runtime evidence; Q-R03
preserves this grading uncertainty. A separately declared
[runtime control](runtime-controls/control_test.go) observes EOF for B05.

A04 asks what the **comment** says and is labelled supported in that narrow
sense. The separate runtime control observes that `Swap(7)` followed by `Load`
without `Store` returns 7, exposing a mismatch with that comment. Q-R01 asks
how the contract should describe this; Q-R02 retains the A03 scope discrepancy
and Q-R03 the B05 evidence-interpretation discrepancy. All remain OPEN. The
control tests were added after the comparison as diagnostics, with intended red
and three race-detector green repetitions; they did not change frozen labels.
The complete ordering-scope probabilities are preserved without selecting a
threshold or making an automatic decision.

## Post-comparison Flash → Jev diagnostic

The [diagnostic protocol](flash-diagnostic-protocol.md) was declared **after**
the direct comparisons were inspected. It uses the already-consumed sources,
so it is exploratory and cannot validate a new held-out claim. The existing
`draft_verify` chain was asked to reproduce exactly the supplied checks whose
fragments support them and to turn the others into named questions. It received
no labels or reference reviews.

All 20 IDs were preserved: eight unchanged, citable claims, all eight judged
`supported` by Jev, and twelve named questions (four contradicted and eight
unclear reference cases). No altered, missing, duplicate or extra claim was
recorded. This is a **binary proposal-versus-question task**, whereas the direct
Jev/Codex comparison has three verdicts: the figures cannot be read as the same
accuracy metric. The pipeline's A04 proposal reports the comment, not a domain
or runtime decision; Q-R01 remains OPEN. No claim was automatically accepted.

Successful `draft_verify` results retain parsed claims, questions, model
judgments, usage and ledger entries, but the existing tool does not archive the
original Flash response bytes or raw HTTP response. The diagnostic records this
limit rather than presenting reconstructed data as an original response.

## Costs, timing and limits

| Newly executed group | Metered amount | Measured call time |
| --- | ---: | ---: |
| Independent AI reference: 4 isolated Codex calls | $0.0562772 equivalent | recorded per call |
| Direct Codex: 4 isolated calls | $0.1319404 equivalent | 41.247 s |
| Jev: 4 batches | $0.000591 | 1.198 s |
| Post-comparison Flash → Jev: 4 chains | $0.005358 | 7.156 s |

Codex amounts use the prior $0.04-per-credit estimate, not an invoice. Total
newly metered cost is approximately $0.19417 including reference preparation
and the post-comparison diagnostic. The Jev/Flash ledger costs are separately
settled. Timings are sums of individual calls in this run; they do not include
case preparation, supervision, tool setup, follow-up, or other pilot phases.
The supervising AI's work is unmetered, not zero. These small, single-run,
non-randomized, previously exposed components cannot establish cost savings,
variance, or whole-pilot quality.

The initial runner preflight failed before any model call due to initialization
order. `preflight-blocked/` retains the traceback and zero-call ledgers;
`start-red.txt` and `start-green.txt` show the targeted fix. A later exploratory
check does not retroactively make the original component holdout fresh.

## Reproduction

Offline `tools/verify_routing_label_eval.py` validates frozen inputs, component
split and dev-before-holdout evidence, label/reference identities, complete
review and open questions, source citations, score replay, prompt inputs,
settled costs and both intentionally red runtime controls. Offline
`tools/verify_routing_flash_diagnostic.py` checks the separate post-comparison
protocol, source and task hashes, proposals/questions and settled ledger.
Red/green tests also exercise split overlap, premature held-out access, source
hash/fragment drift, missing reviews, altered scores/prompts, and preservation
of open questions. These checks detect structural inconsistency; they do not
prove the semantic correctness or independence of AI labels.

Next: build a fresh, independently checked dataset on components not previously
seen in these experiments, then preregister a matched end-to-end Flash/Jev vs
agent-only workflow with repeated runs and complete controller/continuation
accounting. Preserve questions, negative controls, and all omitted, failed or
unsettled cases. Until that comparison is complete, keep the existing routing
and acceptance policy unchanged.
