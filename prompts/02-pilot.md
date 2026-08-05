# Domain Behaviour Analysis — Pilot Prompt (manual Pass 1, 2, 4)

**Version 1.10.** Changelog (feedback loop from real Part-B diffs: divergence *classes* go back into rules; divergence *content* is the mechanism at work):

<!-- vale off -->
* v1.10 — asserted absence: an empty `pairs`, `guardGroups`, or `coverage` section needs a reason in the sidecar's `completeness` block. Silence used to pass the checker, so a skipped step and a genuinely empty one looked the same.
* v1.9 — fragment citations for observed-in-* provenance (`file:line ("fragment")`, checker-verified); the analysis emits a machine-readable sidecar (`analysis.json`, pack schema) that the pack-shipped checker `tools/dsc_check.py` verifies — generic checks move to the pack, per-run scripts keep only the component-specific guard encodings.
* v1.7 — language: rewritten to STYLE.md strict mode; rules unchanged.
* v1.4 — feedback from the third run: remembrance semantics required in the catalogue vocabulary (what ended entities leave behind, in what bound, what late references resolve to — the one recurring Part-B artefact class); guard outcomes standardized into `guard-results.txt`; machine-readable id/state declaration markers so checkers parse declarations, never prose.
* v1.3 — feedback from the second real run: seam-contract sweep (call-site inference is not evidence of failure propagation); upstream-guard annotations and a checklist-coverage table in the catalogue, Stage-1-checked; the requirement-scope rule operationalized as a mandatory line on decision-citing control-trace verdicts, Stage-2-checked; Part-B packs include event-contract semantics; Part B gains a `convergent` class and mandatory row-coverage verification.
* v1.2 — guard disjointness/coverage/boundary proofs via z3 (`check_guards.py`) promoted from optional footnote to mandatory-where-formalizable; every guard group must end `proven`, `violation`, or `not-formalizable`.
* v1.1 — added: cross-source ordering pairs (missed class: window/bind race); requirement-scope rule (missed class: doc line applied to an ordering it never contemplated); doctrine-line sweep; ban on self-declared "benign"; mechanical hole→question mapping in the checker; catalogue gate-type annotation (Part-B artefact class); Part B formalized with divergence classification.
* v1.0 — initial.
<!-- vale on -->

**How to use:** fill in the CONFIG block. Then paste this file into your coding agent (for example Claude Code) at the repository root. The agent analyzes ONE stateful component. It produces analysis artifacts only. It must not change code. Any implementation language works.

## CONFIG — fill in before running

```text
Component under analysis:   <path/to/component or module name>
Entry points / public API:  <files, classes, handlers>
Related tests:              <path, or "none">
Requirements / docs:        <paths, or "none">
Output directory:           domain-analysis/<component>/
```

---

## PROMPT

You perform a domain-behaviour analysis of one stateful component. You analyze. You do not implement.

### Hard rules

1. Do not modify any source code, tests, or configuration. Your only outputs are the analysis files listed below, in the configured output directory.
2. Do not decide unclear domain behaviour yourself. If the behaviour is not clear, or two sources do not agree, or no source gives the behaviour: write an open question. Do not select an answer and continue. Label your recommendations `proposed`, never as fact. To call a gap "benign" is such a decision. Benignity may appear as a proposal inside a question. It is never a reason to omit the question.
3. Every claim about existing behaviour carries provenance: `explicit-requirement` (cite the document), `observed-in-code` (cite file:line), `observed-in-tests` (cite file:line), `inferred` (state the inference), or `proposed` (yours). A claim without provenance is at best `inferred`. An `observed-in-code` or `observed-in-tests` citation carries a short verbatim fragment: `file:line ("fragment")`. Checkers verify the fragment near that line.
4. **Requirement-scope rule.** A citation covers only the scenario that the cited text describes. If you apply a requirement, doc line, or recorded decision to an ordering, race, or variant it does not address: downgrade the provenance to `inferred` and treat the cell as a hole candidate. Written down is not the same as decided for this case.
5. Model what the code does, not what it should do. The desired design comes later, after a human resolves the open questions. Do not produce a to-be model in this run.
6. The component may have no real temporal behaviour: no lifecycle, no asynchronous events, no retries, no timeouts, no cancellation. In that case say so, explain briefly, and stop. A negative result is a valid result.

### Step 0 — Scope statement

Read the component, its tests, and its docs. Output a short scope statement: the machine boundary you will model (one bounded context, not the whole system), the actors, and what you exclude. Include **model links**: which already-modelled neighbouring component owns behaviour that surfaces in this matrix but lives elsewhere (a later untestable-via-seam cell cites the owning model, not a local defect). Continue without waiting for confirmation. Put scope doubts into the open questions.

### Step 1 — Extraction (with provenance)

Extract and list, each item with provenance and location: states, external events, internal events, transitions, guards and conditions, actions and side effects. Also: timeouts and timers, retry behaviour and limits, cancellation paths, failure modes, apparent invariants. Also: contradictions between code, tests and docs, and behaviour you cannot determine. Include implicit states in boolean flags, nullable references, and enum-plus-flag mixtures. Enumerate the reachable combinations; they are the real state space.

**Doctrine-line sweep.** Extract every normative sentence from the requirements and docs. Principle lines such as "identity stays sacred", "no lost X", "failures must be loud" go into a numbered list `DOC-1..n` with their source. Step 5 must classify each doctrine line: adopted as an invariant, adopted as a disposition constraint, or explicitly rejected as non-binding. A silently unused doctrine line is an error.

**Seam-contract sweep.** For every external seam the component invokes (publisher or bus, classifier or model client, scheduler, executor, storage): read the callee's contract. Record its failure semantics (raises what, never raises, timeout behaviour) as NAT candidates with citations into the callee. Missing error handling at a call site is **not** evidence that failures propagate. To declare an invoked-operation failure path a hole without reading the callee's contract is an unproven inference. Label it as such.

→ `extraction.md`

### Step 2 — As-is statechart

Produce a Mermaid `stateDiagram-v2` of the current behaviour. Rules: do not idealize. Where the code contradicts itself: model the dominant path and record the contradiction as a finding. Use hierarchy where the code's structure supports it.

Every matrix state must exist in the diagram (PA-14 round-trippability; the pack checker verifies it). A state that no event transition reaches still needs presence: add a **documenting edge** labelled with its entry semantics — `active --> retired: operator (manual status)` for operator-set states, `partial --> invalid: deque length mismatch (guard)` for guard-condition states. The edge documents; it does not claim an event.

Then validate the model against the existing tests. Walk each relevant test scenario through the model. A test the model cannot accept means a modelling error or undocumented behaviour. Report which one, with provenance.

→ `as-is.machine.mmd`, `as-is-validation.md`

### Step 3 — Event catalogue incl. undesired variants and interaction pairs

List every event with name, source, external/internal, payload gist, and where the code produces and consumes it.

**Gate-type annotation.** For each event whose handling branches, state the gate: payload content, or service-side state. A reader of the catalogue alone, including the Part-B pass, must not have to guess.

**Remembrance semantics.** For every event family whose entities can end (episodes, sessions, connections): state what an ended entity leaves behind. What the component remembers, in what bound (size or duration), and what a late reference to it resolves to. Transition behaviour without end-of-life memory semantics is exactly where blind readers and late-arrival dispositions go wrong.

For every external event source, derive undesired variants with this checklist: loss or failure of the source; delay beyond a timeout; duplication. Also: out-of-order or stale arrival, above all after cancellation or shutdown. Also: contradictory simultaneous inputs. Add the variants to the catalogue. They receive matrix columns like any other event.

**Upstream-guard annotation.** For every external event, state which validations happen upstream of this boundary (with citations into the upstream code) and which are absent here. Do this per deployment topology when more than one exists. A guard the catalogue does not mention will be re-invented or falsely assumed by every blind reader.

**Checklist coverage table (machine-readable).** Emit a table `undesired-coverage`: rows = external sources, columns = the five checklist categories. Each cell holds the derived variant id(s), or an explicit `n/a: <reason>`. An empty cell is an error. This table prevents a checklist category from silently producing no variant.

**Cross-source interaction pairs.** Enumerate every pair of *external* events from *different* sources that reference the same entity (room, session, stream, id) and can plausibly arrive near-simultaneously. Both orderings of each pair get an id (`P-01a`, `P-01b`, …) in a pairs table. The per-source checklist covers single-source orderings. This table exists because a per-source checklist structurally misses the races *between* sources.

→ `event-catalogue.md` — always its own file, never a section inside
`extraction.md`: the Part-B blind pass consumes it verbatim, and a
catalogue buried in another artifact has to be re-extracted first
(dobby appliance-client, 2026-08-05).

### Step 4 — Disposition matrix

Build a Markdown table: rows = leaf states of the as-is model; columns = all catalogue events including undesired variants. When the event set outgrows one readable table (~10 columns), split into sub-tables with one header each (00-methods-reference, "Wide matrices"); state rows repeat in full. Every cell gets exactly one value:

* `transition → <target>`: with provenance
* `handle`: stays in the state, does something; with provenance
* `ignore (documented)`: intent has evidence; cite it (the requirement-scope rule applies). Citations are cheapest at matrix-writing time — a `file:line ("fragment")` per cell now beats a backfill pass later.
* `ignore (accidental)`: nothing happens only by omission or fall-through; **counts as a hole**, however harmless it looks. It carries a hole reference like any hole: `ignore (accidental) → Q-03`.
* `defer (queued)`: the code buffers the event; cite where
* `reject`: with provenance
* `UNSPECIFIED`: you cannot determine the behaviour; **counts as a hole**

For each (state, event) with guarded transitions, add a guard note that lists the guards and the boundary values.

**Guard proofs (mandatory where formalizable).** Formalize every such guard group as predicates over typed context variables. Use Int / Real / Bool / enum sorts, with domains from the NAT invariants (for example `0 <= retryCount <= maxRetries`, `confidence in [0,1]`). Write `check_guards.py` with z3 (`pip install z3-solver`) and execute it.

For each group establish, under the declared NAT assumptions: (a) **pairwise disjointness**: `g_i AND g_j` unsatisfiable for every pair. (b) **coverage**: `NOT (g_1 OR ... OR g_n)` unsatisfiable, or an explicit else-branch exists. (c) **boundary probes**: for every comparison, evaluate below, exactly at, and above the limit, and record which branch takes each. Every result cites the assumptions it used.

A guard you cannot formalize gets the mark `not-formalizable: <category>: <reason>` and keeps its inspection reasoning, labelled unproven. The category comes from a closed vocabulary — `external-call` (the guard calls out of the machine), `dynamic-state` (the guard reads mutable runtime content), `clock` (floating-point or wall time), `unstructured-payload` (free-form content) — because the not-formalizable outcome is a judgment call, and the category makes it reviewable (the pack checker enforces the vocabulary). Every guard group must end as `proven`, `violation` (a finding), or `not-formalizable`. To skip a group silently is an error. Write the outcomes to `guard-results.txt` and back into the matrix's guard notes.

**Mechanical self-check (mandatory).** Write `check_matrix.py` in the output directory and execute it. The catalogue must carry a machine-readable id declaration (`<!-- event-ids: ... -->`) and the matrix a state declaration (`<!-- states: ... -->`). Checkers parse these declarations, never prose.

Stage 1 (after this step): every state row contains exactly one disposition per catalogue event column. No catalogue column is missing. Every `ignore (documented)` and `reject` cell carries a citation. The `undesired-coverage` table is total (no empty cells).

Stage 2 (after Step 7, re-run): every hole cell (`UNSPECIFIED` or `ignore (accidental)`) carries a `→ Q-nn` back-reference that exists in `open-questions.md`. Every interaction pair `P-nn` appears in at least one trace in `adversarial-traces.md`. Every guard group has an outcome from `check_guards.py`. Every control-trace verdict that cites a requirement or decision carries the scope line ("cited text contemplates this ordering: yes/no").

Also emit the machine-readable sidecar `analysis.json` (schema: pack `formats/analysis.schema.json`). Contents: states, events, cells with dispositions and links, pairs with traces, guard outcomes, the coverage table, questions, behavioural DRs. Run the pack checker `tools/dsc_check.py <output-dir> --repo . --model as-is.machine.mmd` in addition to the two per-run scripts. Include all outputs in `summary.md`. Deliver checks as executed code, never as claims.

**Assert every absence.** An empty `pairs`, `guardGroups`, or `coverage` section is a claim, not a silence: it says this component has no interaction pairs, no formalizable guard groups, or no external sources. State it in the `completeness` block with a reason, or the checker fails the sidecar:

```json
"completeness": { "guardGroups": { "count": 0,
  "reason": "no branch in this component compares context values" } }
```

Omitting a section you simply did not produce is the failure this block exists to prevent. It used to read as a pass.

→ `disposition-matrix.md`, `check_matrix.py`, `check_guards.py`

### Step 5 — Invariants and lint findings

Propose invariants as checkable predicates over state and context, classified `NAT` (assumption about the environment) or `SYS` (obligation of the system). Check every SYS invariant against the as-is model, state by state. Violations are findings. **Close the doctrine sweep:** map every `DOC-n` line from Step 1 to an invariant, a disposition constraint, or an explicit rejection with reason. An unmapped doctrine line is an error.

Then run this checklist against the model and report violations with provenance:

* waiting, connecting, or stopping states without timeout behaviour
* retries without a maximum
* invoked external operations without an explicit failure outcome
* externally initiated operations without cancellation handling
* terminal or error states without documented meaning or diagnostic
* undefined startup or shutdown behaviour
* unbounded queues or buffers, unhandled overload

→ `invariants-and-lints.md`

### Step 6 — Adversarial traces

Produce concrete, numbered event sequences of two kinds:

1. **Systematic:** one trace per interaction-pair ordering from the Step-3 pairs table (`P-01a`, `P-01b`, …). Each trace ends in an explicit disposition or a raised question. No pair stays untraced.
2. **Free probes (at least 10):** unexpected ordering; delayed responses that arrive after cancellation or shutdown; duplicates; cancellation races; restart mid-operation; simultaneous external events; deliberate NAT violations.

For each trace give (a) the sequence, (b) what the code appears to do, with provenance, and (c) the domain question it raises. For a control trace, write `none — control trace` instead of a question. A control-trace verdict that rests on a cited requirement or recorded decision must add one line with a short quote. The line: **"cited text contemplates this ordering: yes/no"**. A "no" voids the control verdict and raises a question. This is the requirement-scope rule made mechanical.

→ `adversarial-traces.md`

### Step 7 — Open domain questions (primary deliverable)

Consolidate every hole, contradiction, accidental ignore, invariant violation, unmapped-doctrine finding, lint finding, and adversarial question into a numbered list. These are decisions that only a human can make. **Nothing gets dropped in consolidation.** Every hole cell maps to exactly one Q. To group related cells into one Q is fine. To omit one is not.

Write the mapping back into the matrix (`→ Q-nn` per hole cell), so that the Stage-2 checker can verify it. Format each question as a proposed decision record:

```text
Q-07
Question: May a delayed connection.opened reactivate a stopped device?
Current behaviour: reactivates (observed-in-code, connection.py:214)
Options: reactivate | ignore | reject with diagnostic
Proposed: ignore — shutdown is operator-initiated and final
Status: OPEN — human decision required
```

Do not resolve these questions. End with a summary count: states / events incl. undesired variants / interaction pairs / matrix cells / UNSPECIFIED / accidental ignores / guard groups proven / guard violations / not-formalizable / findings / open questions.

→ `open-questions.md`, `summary.md`

---

## PART B — Blind adversarial pass (separate, fresh session)

Run this in a **new** agent session with no access to the as-is model, the matrix, the traces, or the code. Provide only these inputs. First: `event-catalogue.md`, with gate-type annotations, upstream-guard annotations, and the pairs table. Second: the prose requirements. Third: the **normative contract text of every event the component emits or consumes**. Contract text means contract docstrings and schema descriptions: requirements-level material, never component code.

> Here is the event catalogue of a component, and its requirements. For every event — including undesired variants and both orderings of every interaction pair — state in which situations the component should handle, ignore, or reject it, and what should happen. Describe situations in requirement terms. If you must assume a lifecycle state the requirements do not name, label it `assumed-state:`. You have no access to the implementation. Be concrete. Produce a table keyed by the catalogue's event ids. End with a coverage checklist: every catalogue event id, listed once, ticked. A missing row must be impossible to miss.
>
> The disposition vocabulary you must use (from the methods reference): `transition → <target>` | `handle` (stays in the state, does something) | `ignore (documented)` | `ignore (accidental)` | `defer (queued)` | `reject` (a declared refusal signal: error, diagnostic, nack) | `UNSPECIFIED`. Without these definitions a blind pass applies `reject` and `handle` to identical semantics interchangeably (dobby trigger-service, 2026-08-05: four vocabulary-only "divergences").

Then diff its table against `disposition-matrix.md` (an agent that sees both may do this diff).

Dispatch notes (learned the hard way, dobby 2026-08-05): inline the
inputs VERBATIM in the dispatch — a placeholder payload is the known
failure, and `tools/part_b_pack.py --for-dispatch` exists so it cannot
happen silently. If the blind agent refuses to run because its context
is contaminated, that refusal IS the control working: fix the inputs
or the context, never the agent. Before you classify: verify blind-table coverage mechanically. Every catalogue event id has exactly one row. Report any miscount. Then classify **every** row of the blind table into exactly one class:

* `convergent`: the blind pass reproduces the documented disposition: agreement, no gap, no action
* `convergent-hole`: the blind pass independently flags a gap that pass A found: this strengthens the finding; note it on the existing Q
* `divergence`: different expected behaviour: a blind spot of pass A, or a genuine open question. **Every divergence must end as a new Q or as a reasoned fold into an existing Q. The Stage-2 checker treats an unclosed divergence as a failure.**
* `artefact`: catalogue phrasing caused it, not behaviour: repair the catalogue entry (usually a missing gate-type, remembrance, or upstream annotation), so the artefact class cannot recur
* `pass-B-blind-spot`: pass A saw something pass B did not: note it, no action

→ `part-b-diff.md`

---

## Feedback loop

After each Part-B diff, fold recurring divergence *classes* (not single findings) back into this prompt as new rules. Record them in the changelog at the top. The goal is not zero divergence. A blind pass that can no longer disagree is dead weight. The goal: no divergence *class* survives two components.
