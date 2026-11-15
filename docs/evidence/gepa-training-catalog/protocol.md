# Training catalog and fixed-prompt baseline protocol

Written before new baseline calls. Objective: collect previously observed
source-grounded missed or overgeneralized behavior and controls, independently
review the references, and measure whether the existing fixed discovery prompt
misses them in fresh isolated runs. This is preparation for a possible GEPA
experiment, **not** GEPA optimization, a held-out evaluation, a full StateRadar
pilot, or a blind Part B. Standard routing and domain rules do not change.

The catalog contains twelve cases on five components. It includes historical
misses/incorrect assertions and correct positive or negative controls. Previously
used cases are training/regression cases, never an unexposed final test. The
separate AI reviewer must approve every exact case with reason, sources and
executed references; it is not a human domain decision or an independent human
review. A rejected or absent review blocks its case until corrected.

After review, freeze catalog, independent review, protocol, source snapshots,
fixed prompt, task and caller scripts, and cited evidence by SHA-256. The task
model receives the same general task and fixed paragraph used in the prior GEPA
discovery experiment and complete source text only; no case list, prior output,
reference test, review or score is sent. Pool input concatenates the pinned
channel.go and pool.go snapshots with section markers; input-map.json identifies
original line numbers. Disable shell, network and other model tools. Use Codex
ChatGPT-login gpt-6.1-sol medium. Two fresh calls per component; order is
G,C,W,T,P, then P,T,W,C,G. Do not change settings or repair semantics with
hidden labels. One counted structural repair is allowed per call; failures and
unsettled usage are retained, not silently replaced. Maximum 20 Codex launches,
$3 soft controller cap at recorded credit assumptions; supervision is unmetered.

Evaluate every output after the calls: source-check every finding as valid,
false or uncertain; for each catalog case make an explicit attributed mapping
or absence with source-backed reasoning. Counterfactual/negative controls must
not be marked found unless the model states the correct distinct outcome.
Required owner or contract wording questions stay OPEN. Evaluate behavior,
not keywords; full case credit requires the specified conditions and result.
Archive exact fragments, anchors and review reasons. Cases can be grouped in a
single finding or use multiple findings where all elements are explicit.
Report per-case found/missing and valid/false/uncertain findings, and distinguish
stable observed misses from one-call omissions. Two repetitions are a small
signal, not a frequency estimate. Retain all unanticipated findings and errors.

The same fixed paragraph and task were also used in some previous runs; their
results are historical evidence, not additional fresh repetitions. The
historical pool Flash miss used a different workflow, so do not present it as
a previous GPT-6.1 Sol fixed-prompt result. Previously observed WaitGroup
false assertions are distinct from omissions, and invalid outputs must not count
as successful discovery. No recommendation to change the standard prompt or
launch GEPA follows automatically from a single miss.
