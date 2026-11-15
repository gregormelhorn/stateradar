# Late-completion workflow integration

The testgen workflow must classify every trace in its reviewed scope, not infer
applicability from event names or unstructured prose. Its inventory is a separate
scenario scope: cells, trace IDs, event ordering and source-grounded contract
facts. This may reference a bounded scenario slice rather than a total matrix;
the boundary must be explicit. The checker cannot discover omitted behavior in
code or prove a reviewer's semantic interpretation. Git-pinned scope review is
still required; structural completeness only covers the declared inventory.

The plan has exactly one row per scope trace: applicable, not-applicable or
blocked. A terminal lifecycle, one owned idle resource, no observed post-terminal
effects, and exactly-once release are explicit contract facts (true/false/unknown).
A false contract fact excludes this v1 oracle. Unknown semantics require an open
question; missing scheduling/observation seams block execution. Applicable rows
must cite an accepted DR and map to a unique case in the unchanged shared profile.
Both orderings remain required. Model cell, trace order, profile case and DR
identity must agree. Reasons and citations are mandatory, including exclusions.

Execution validation is separate from plan validation. A fresh receipt hashes
all relevant inputs and generated source variants. For applicable scenarios,
replay baseline and every mutant/weak observation through the shared oracle;
check exact repetitions and target failures in every repeat; verify independent
canary causes and dependency chains. Go adapter execution receipts bind raw
Go test events, traces, source/profile/adapter/oracle hashes and execution counts.
The first proof reader supports Go JSON events, explicitly not arbitrary-language
execution authentication. Other languages can still use the shared oracle and
add an evidence reader. No generic parser can authenticate a malicious producer.

Red probes must cover omitted scope decisions, wrong cells/traces/DRs, missing
positive controls, false exemption, blocked semantics without a question, absent
canaries, stale inputs, incomplete test discovery and incomplete observations.
The production checker must actually reject these, not merely list expected reds.
The addrConn runner emits and validates fresh receipts as part of normal execution.

Second candidate: gobreaker. Inspect pinned local source and execute a public-API
probe of stale completion across generation rollover. If its lifecycle/resource
contract differs, record not-applicable with evidence instead of redefining
termination or inventing a resource. Candidate readiness is not a second adapter
or a fresh pilot. No historical questions or semantics are silently resolved.
