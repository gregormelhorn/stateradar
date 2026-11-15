# Prospective fixed versus unselected candidate

Declared before any comparison model call or inspection of model outputs. This
is a source-grounded discovery experiment, not a StateRadar pilot or blind Part
B. No human review. Two components not used as components in the earlier GEPA
experiments: sync.Once and bytes.Buffer from the Go 1.27.3 distribution. Public
code might be present in model pretraining. Freeze the source, tests, dataset,
reference AI review, fixed prompt and previously proposed candidate before the
first comparison call. Execute the reference tests three times with race
detection; have an isolated Codex review every case against source and test and
retain any disagreement rather than declaring it resolved. The bounded waiting
test alone cannot establish that the second goroutine was scheduled; source and
completion controls are needed.

Run two independent fixed and two candidate calls per component, alternating
order by component and repeat. Use the prior source-only task and output schema,
no case descriptions or reference tests in model prompts, same model and
isolation as before. Review every finding and case against source, giving full
credit when its explicitly stated behavioral conditions logically cover the
reference case even if incidental values differ. An analogous example alone
that does not assert the general behavior is partial; numeric equality alone
is not a requirement. False and uncertain findings remain separate, and a
partially correct claim does not receive full credit. Preserve raw evidence and
pre-existing prior scores without retroactive edits. Report all output, review,
cost, supervision limitations and unresolved cases. This tiny set is a
prospective check, not proof of broad performance or automatic promotion.

Cap new comparison calls at 12, reference review at 4, model-cost equivalent at
$3 per group (soft, one in-flight call can exceed); stop on unknown usage. Do
not tune prompts, references or thresholds after seeing comparison output. The
selected seed and tied proposal are fixed to the archived candidate texts. No
semantic decision may be made by the evaluator or by GEPA.
