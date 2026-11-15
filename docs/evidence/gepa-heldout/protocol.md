# GEPA held-out comparison protocol

Declared before optimization. This is a bounded discovery comparison, not a
full StateRadar pilot or blind Part B. The user requested no human review.
An isolated Codex session and Jev review each source-grounded held-out case;
the supervising agent inspects every judgment against source and executed
controls. Their disagreement is retained; no model judgment is a domain
policy decision. Missing contracts/intent stay OPEN.

Train: all twelve cases on gobreaker, cond, waitgroup, timer and pool from
`gepa-training-catalog`. Their previously recorded first fixed-prompt outputs
and attributed reviews are immutable, reused as each seed training evaluation.
One actual GEPA 0.1.4 reflection minibatch covers all five train components,
with feedback including their reviewed missed/incorrect cases; proposal and
new evaluations are fresh Codex gpt-6.1-sol medium calls. Source behavior and
policy questions are not replaced by an optimizer's preferred interpretation.

Selection validation: new io.Pipe cases. Locked final: new bufio.Scanner and
sync/atomic.Value cases. They are distinct components and packages from the
train and prior GEPA runs, but all public Go source may have appeared in model
pretraining. Cases, source, tests and independent model reviews are frozen
before optimization. Only train feedback enters reflection. Validation gold
contributes a reviewed score, never case descriptions or labels to reflection.
Final source and gold do not enter model calls until selected prompt is frozen.

The source-only task, fixed paragraph, model and output schema are the same as
the prior training baseline. A fresh result is reviewed case-by-case and
finding-by-finding against source, runtime dependencies and the executed probes;
full case credit needs the ordered conditions and outcomes. Preserve correct
controls, report false and uncertain statements separately, and record partial
coverage. An AI source review is not independent human gold. Jev uncertainties
and initial refuted overbroad cases are retained, not treated as resolved by
confidence. The two corrected cases add explicit reader/type preconditions and
separate opposite controls.

Use GEPA seed 17, current_best, no merge, reflection batch size 5 (all training
components), 11 metric-call stopping budget and up to 14 to accommodate the
last complete iteration. Candidate score is full-case fraction minus 0.1 for
each false finding, lower-bounded at zero; uncertain findings are reported
separately. Never select on final observations. Preserve all evaluated
candidates and identical-source prompts. A candidate needs no known regression
on the measured training cases and correct controls before promotion; this
small experiment never automatically changes the project prompt.

For final comparison, run fixed and selected prompt twice each on both held-out
components; order fixed/gepa then gepa/fixed for the first, reversed for the
second. Calls are independent, not a shared precomputed baseline. If GEPA
selects the original seed, report that honestly and treat final results as
repeats of the same prompt, not an optimized-prompt comparison. Include all
failed calls, structural repairs, model output, AI review, cost and residual
work. Limit optimization/final to 25 Codex launches and a $6 soft controller
credit-equivalent cap, stop on unknown usage. Initial independent reference
review and Jev calls are separate, also counted; supervision is unmetered.
No retries for semantic outcomes or fixed score thresholds. Two final repeats
per arm do not establish population reliability.
