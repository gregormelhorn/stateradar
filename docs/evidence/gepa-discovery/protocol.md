# GEPA discovery evaluation protocol

Declared before new model calls. This is a small, supervised discovery
experiment, not a full StateRadar pilot or blind Part B. Use GEPA 0.1.4, an
isolated Codex gpt-6.1-sol medium task model, and the same model for proposing
prompt text. Inputs are whole source files; gold case descriptions, tests,
archived reports and prior analysis must never be shown to the task model.
Task prompts contain a general bounded finding-discovery instruction and one
review paragraph. They ask for up to six independently cited findings and
OPEN policy questions, with no case inventory. Both arms use the same task,
source and settings. There is no Flash/Jev pilot or change to standard routing.

Train: timer (known contradiction and controls). Validation: gobreaker (known
behavioral cases). Final: Cond and WaitGroup. Final component cases are new to
GEPA optimization, but are public Go sources in the same library family and
may appear in pretraining. The operator authored the gold cases and reviews
model outputs; upstream source and tests are independently authored, but no
independent human review of the gold or interpretations is claimed. These
limitations preclude claims of broad generalization or independent gold review.

Use source contracts and independently authored upstream tests as reference.
Actual runtime observations cannot decide unspecified domain intent. Scoring
maps a case only when an attributed review finds the complete situation and
consequence in a valid model finding. Review every returned finding as valid,
false or uncertain with reasons, including findings outside the case inventory.
Require exact source fragments and record whether required OPEN questions were
preserved. The program audits complete attributed reviews and fragments; it
does not judge semantic entailment. An uncertain finding is not counted as a
false positive or a confirmed correct finding. All generated findings and
review judgments are retained and the operator checks each against the source.
No model judge is treated as ground truth.

Use a generic fixed seed paragraph and actual GEPA search. GEPA receives only
operator-reviewed train feedback including missed training descriptions; it
receives validation scores but not validation gold descriptions. Selection is
fixed before final sources reach a task model. One final model call per arm per
component, alternating arm order; small samples cannot measure variance. Score
is case recall minus 0.1 per reviewed false finding, lower-bounded at zero;
report recall, false findings, uncertain findings, questions, and narrative
limitations separately. No length/cost bonus. Keep all outputs, costs, failures,
and structural repairs. Do not silently omit incomplete runs. Stop before a
call when previous cost is unknown. Maximum 20 Codex launches and $5 estimated
controller cost; cost is a credit-rate equivalent, not account charges, and
supervising work is unmetered. Final fixed and GEPA runs are independent calls,
not paired shared baseline outputs. Optimization costs are included separately.

The objective measures recall only against this small documented case set; a
finding outside the inventory is assessed for validity but does not count as a
new gold hit. Source citation checks are necessary but not semantic proof.
An unanticipated valid finding must be described separately, not retrofitted
into the frozen test score. Do not change project rules or promote a prompt on
these results alone.
