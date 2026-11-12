# Plan: measurable model cascade for StateRadar

Status: evaluation tooling started; no automatic acceptance or escalation policy
is enabled. The purpose is to reduce expensive model work while measuring both
quality and the complete cost of a pilot. The human owner retains all domain
decisions; deterministic pack checks and the blind Part B remain mandatory.
The current commands and their accounting limits are documented in
[local model routing](local-model-routing.md); other project priorities are in
the [roadmap](roadmap.md).

## Next pilot

Identify existing source-grounded examples whose expected verdicts can be
reviewed independently of Jev. Record their evidence, attributed reviewer,
component or issue, and whether the case belongs to development or an untouched
held-out group. Keep unsupported or unresolved domain semantics as questions.
Run the current batch and offline evaluator on the development cases first,
then compare a chosen candidate against the existing workflow on the held-out
group. Record any missing inputs, API failures and excluded cases rather than
silently dropping them. Do not treat the evaluator's reviewer field alone as
proof of independence. Record the stronger-model cost separately from the
local ledger until an end-to-end accounting mechanism exists.

## Stages

1. **Evaluation foundation (started).** Collect independent, attributed labels
   for source-grounded checks. Compare Jev outputs with them using
   `tools/jev_eval.py`. Include supported, contradicted, insufficient evidence,
   races outside a requirement's scope, and seam-contract cases. Record a
   source hash and the full check identity, and keep a separate record of who
   reviewed each label. Do not label an unknown as a domain decision.
2. **Representative held-out pilots (planned).** Split by component or issue,
   not randomly by similar cells. Keep the held-out cases out of prompt and
   threshold development. Pin model versions and preserve requests, judgments,
   errors, token usage, elapsed time, and the cost of all model calls. Measure
   false support, missed defects, unnecessary escalations, and end-to-end
   coverage and time; include human review cost where feasible. The local ledger
   does not count the calling agent's or other providers' costs.
3. **Draft and verify (planned).** Have Flash propose bounded extraction or
   classification, validate required structure and citations in code, then
   batch narrow Jev questions over shared evidence. Preserve every claim and
   incomplete or failed check. Work spanning multiple sources needs all
   relevant evidence and provenance; a single source is not a callee contract.
4. **Calibrated escalation experiment (planned).** Only after the labelled
   evaluation supports it, select an explicit policy for source gaps, invalid
   output, contradictory and uncertain judgments, and provider failures. Send
   selected cases to stronger review, retain raw judgments, and compare the
   whole pipeline against the prior workflow. A model verdict is a proposal,
   never a domain decision or a reason to discard a question.
5. **Prompt research (planned).** Use targeted, independent questions and
   repeated requests to study stability. Feature discovery is conditional on a
   sufficient labelled dataset; evaluate changes on untouched components.
   Consistency is not accuracy, and vendor thresholds are not acceptance rules.

## Cookbook basis

The design draws on [SDE cascade](https://docs.typesafe.ai/cookbooks/sde_cascade),
[parallel questions](https://docs.typesafe.ai/cookbooks/parallel_questions),
[citation checks](https://docs.typesafe.ai/cookbooks/citation_check),
[Choice consistency](https://docs.typesafe.ai/cookbooks/consistency_choice_cookbook),
[Noul consistency](https://docs.typesafe.ai/cookbooks/consistency_noul_cookbook),
and [feature discovery](https://docs.typesafe.ai/cookbooks/autoresearch_feature_discovery).
Their demonstration results do not establish StateRadar performance or savings.
