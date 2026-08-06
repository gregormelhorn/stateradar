# Domain Statechart Method — Reference

This is the methodology behind the prompt pack. It uses Harel-style statecharts as explicit domain-behaviour specification and test oracle for software that AI coding agents write or modify. It condenses the full product handoff document (rev. 2) into a tooling-free form. Generated, executed checker scripts and normal test infrastructure (pytest + CI) do the work of the deterministic tooling described there.

Give this file to agents as context when running the pack prompts.

---

## Purpose and scope

The objective is not to control the coding agent. The objective is to bring **application-domain behaviour and test generation** under control:

1. domain logic must not remain hidden and silently decided inside AI-generated code;
2. tests must derive from explicit behaviour, not mirror the implementation.

Use the method for behaviour involving: lifecycles, connection management, protocol phases, asynchronous events, timeouts, retries, cancellation, recovery, sessions, mutually exclusive modes, concurrent coordination.

Do not use it for: pure calculations, stateless transformations, formatting, validation, ordinary CRUD without temporal behaviour. Statefulness alone does not qualify; *temporal* behaviour does. One machine per bounded context, never one global machine.

## The loop

```text
01 Scout        find and rank stateful components worth modelling
02 Pilot        as-is model, event catalogue, disposition matrix,
                invariants, adversarial traces → open domain questions
--              HUMAN answers the open questions
03 Resolution   answers → decision records → to-be model → updated matrix
04 Testgen      one test per matrix cell + invariant asserts + checker
                → deviation report → (optionally) code changes, DR-cited
05 Standing     repo-level instruction keeps future agent sessions
   instruction  inside the discipline; checker + cell tests enforce it in CI
06 Reconcile    after implementation: to-be becomes the new as-is,
                citations refresh at HEAD, manifest pins the analyzed SHA
07 Test audit   off-cycle: judge an existing suite against the decided
                matrix; weak tests (structure-bound) first, then
                redundancy, deviations, gaps; propose, never delete
```

## Core principle

The AI may propose and critique behaviour. It must not decide unclear domain semantics silently. Every extracted claim carries a provenance label:

```text
explicit-requirement | observed-in-code (file:line) |
observed-in-tests (file:line) | inferred | proposed
```

The human makes the genuine domain decisions. Each one becomes a decision record, never chat history. Deliver checks as **executed code**, never as claims. Agents write and run small verification scripts (matrix grid completeness, DR-link presence, z3 guard checks) instead of asserting correctness in prose.

## Artifact set

Per component, under `domain-analysis/<component>/`:

```text
extraction.md            provenance-labelled behaviour inventory
as-is.machine.mmd        Mermaid statechart of current behaviour
as-is-validation.md      existing tests replayed through the model
event-catalogue.md       all events incl. undesired variants
disposition-matrix.md    states × events, every cell dispositioned
invariants-and-lints.md  NAT/SYS invariants + checklist findings
adversarial-traces.md    concrete counterexample event sequences
open-questions.md        the human decision queue (Q-nn)
decisions/DR-NNN.yaml    resolved ambiguity, one record per decision
decisions/INDEX.md       Q-id → DR-id map
to-be.machine.mmd        approved model (= as-is + accepted DRs)
to-be-diff.md            semantic diff, every line DR-cited
remaining-holes.md       cells still open
check_matrix.py          the mechanical self-check, wired into pytest
check_guards.py          z3 guard proofs (disjointness, coverage, boundaries)
matrix-coverage.json     matrix cell → test id (or untestable reason)
seam.md                  observation points used by the tests
deviation-report.md      code-vs-model deviations from the test run
summary.md               counts and status
analysis.json            machine-readable sidecar (pack schema, dsc_check input)
manifest.json            component, watch paths, analyzedSha — staleness anchor
archive/<date>/          superseded artifacts after a reconcile
```

Mermaid (`stateDiagram-v2`) is the visual notation. The matrix, not the diagram, is the primary review and authority surface. The diagram cannot carry dispositions, guards, or DR links. The matrix can.

**Wide matrices.** When the event set outgrows one readable table (rule of thumb: more than ~10 columns), split the matrix into sub-tables, each with its own header row and its share of the event columns; the state rows repeat in full. A sub-table header is a normal markdown table header whose first cell names the state column. Checkers and the sidecar generator parse the declarations and headers per sub-table and treat the union as one grid (dobby trigger-service, 2026-08-05: 23 columns across four sub-tables).

## Maturity levels

Brownfield consumers adopt the discipline in levels. Each level names
its minimum artifact set; a level is complete only with everything
below it. Skipping levels silently is how matrices without DR links,
phantom question ids, and untested "steady states" happen (dobby
session, 2026-08-05).

```text
L1 descriptive   extraction.md + as-is.machine.mmd + disposition-matrix.md
L2 decided       + open-questions.md, DRs for decided cells, hole→Q links
L3 enforced      + tests/domain/<component>/ cell tests + matrix-coverage.json
L4 verified      + analysis.json sidecar, dsc_check OK, CI gate wired
L5 steady state  + reconciled manifest at HEAD, standing instruction active
```

A component below L3 is analysis, not governance: the standing
instruction's "green means conforming" does not apply to it yet. Say so
in its summary.md. Promotion to L5 requires the sidecar and a green
dsc_check — there is no "reconcile-lite" (06-reconcile step 0).

## Model links

One machine per bounded context means behaviour surfaces in one model
but lives in another (dobby: the mqtt-consumer's replaying state was
untestable because replay belongs to session-recovery). The scope
statement names these links: which neighbouring component owns the
behaviour this matrix can only reference. A matrix cell left
`untestable-via-seam` for that reason cites the owning model, not a
local defect. A high untestable ratio is a boundary signal, not a test
gap (04-testgen).

## The disposition matrix

Rows = leaf states of the model; columns = every catalogue event **including undesired variants**. Every cell has exactly one value:

```text
transition → <target>   | handle          | ignore (documented)
ignore (accidental)*    | defer (queued)  | reject | UNSPECIFIED*
```

Values marked * count as specification holes. Never accept "nothing happens" implicitly: it is either a documented, DR-linked ignore, or a hole. State dispositions at compound-state level; substates inherit them. Mark inherited cells with their source. Only unresolved leaf cells count as holes. In the to-be matrix, every `ignore` / `reject` / `defer` cell carries its DR link, and `ignore (accidental)` may no longer appear.

## Event catalogue and undesired variants

Every event lists: name, source, external/internal, payload gist, where produced and consumed. For every external source, derive undesired variants by checklist:

```text
loss/failure of the source · delay beyond timeout · duplication ·
out-of-order or stale arrival (esp. after cancellation/shutdown) ·
contradictory simultaneous inputs
```

Each variant receives a matrix column and a disposition (or an explicit `not applicable` with reason). This is the systematic counter to "completeness only holds relative to the catalogue".

## Invariants

Checkable predicates over (state, context), classified:

```text
NAT     assumption about the environment   e.g. 0 <= retryCount <= maxRetries
NAT-SYS assumption about N>1 instances     e.g. all instances observe the same
        sharing one external resource          server degradation simultaneously
SYS     obligation of the system           e.g. Streaming implies Authenticated
```

Analysis may assume NAT; tests must not. Adversarial traces deliberately violate NAT and require explicit robustness dispositions. Every generated test asserts **all SYS invariants after every delivered event**: the cheapest, strongest oracle in the method.

## Decision records

```yaml
id: DR-007
date: 2026-07-27
source_question: Q-07
question: May a delayed connection.opened reactivate a stopped device?
options: [reactivate, ignore, reject-with-diagnostic]
decision: ignore
rationale: Shutdown is operator-initiated and final.
links: ["matrix: stopped x connection.opened"]
status: accepted
```

**Question status vocabulary.** A question's status starts with exactly one of: `OPEN`, `ANSWERED`, `RESOLVED`, `CONFLICT`. The checker validates the first word against this set. Consumer vocabularies map onto it (`DECIDED` reads as `RESOLVED`; the sidecar generator maps it). Do not invent new first words.

Governance rules: every to-be deviation from as-is traces to a DR. No dispositioned cell, SYS invariant, or existing DR changes without a superseding DR. Agents raise `UNSPECIFIED` + question instead of deciding. Enforcement is the checker test (`test_matrix_discipline`) plus the cell suite in CI: breaking the discipline breaks the build.

## Semantics conventions

* Deliver one external event at a time, processed to completion, before the next arrives. Real implementations need a serializing dispatch seam per machine instance for tests to be meaningful.
* Observable output of a step = projected state + ordered emitted effects. Internals are invisible to tests (anti-mirroring rule).
* Control time: an injectable clock / fake timer; timers are the only permitted source of time dependence. Delay scenarios advance the fake clock. A correct fake timer carries TWO values per entry: the scheduling delay (what tests assert via pending lists and exact-delay fires) and an absolute due offset (what decides the next fire). With only stored delays, long-horizon scenarios break silently — fifteen 20 s rechecks in front of a 300 s TTL starve the TTL forever and the test hangs instead of failing (dobby trigger-service, 2026-08-05). When the horizon exceeds one fire, assert on the sequence of fires, not on a single delay.
* `defer` means an explicit, observable queue with re-delivery on the dequeuing state entry, never implicit buffering.
* Late, duplicate, and stale events are never undefined; they are catalogue variants with dispositions.

## Testing conventions

* **One test per matrix cell**, named `test_cell__<state>__<event>[__variant]`, docstring citing disposition and DR.
* Assert by disposition (target state + effects / unchanged + effect / unchanged + nothing / rejection signal / queued).
* **Boundary tests** for every guarded pair: below, exactly at (`==`), above the limit.
* **Scenario tests** from decided adversarial traces, SYS invariants asserted at every step.
* `matrix-coverage.json` maps every cell to its test or a reasoned `untestable-via-seam` entry; the checker verifies the map.
* A failing test is a **finding** (code deviates from the approved model), never a defect of the test. Never weaken, skip, or delete tests to pass. Fix deviations in code or, with human approval, in the model plus a superseding DR.
* Optional honesty probe: run a mutation tool (`mutmut`, `cosmic-ray`, Stryker) over the lifecycle code; surviving mutants are weak spots of the suite.
* Calibration probe for the method itself: run the pilot twice on the same component in fresh sessions and diff the matrices. Divergence measures how much you can trust a single unverified run.

## Method rules (PA-1 … PA-16, condensed)

Settled by prior art; agents must not relitigate them without a DR. In pack mode, generated checker scripts, explicit reasoning marked unproven, and the CI-wired test suite discharge the "Analyzer/tooling" duties.

```text
PA-1  guards per (state,event) pairwise disjoint — order must never decide
PA-2  guards jointly exhaustive, or an explicit else exists; gap = hole
PA-3  guard checks state their assumptions (in pack mode: z3 proofs via
      a generated check_guards.py where formalizable; otherwise labelled
      inspection-only)
PA-4  events classified: monitored input | controlled output | internal
PA-5  derived events may be defined as @T(predicate) WHEN condition
PA-6  invariants split NAT vs SYS; analysis may assume NAT, tests may not
PA-7  bindings (abstract action → concrete symbol) are part of the spec
PA-8  single-input assumption: one event to completion at a time
PA-9  tests require a serializing dispatch seam; probe reentrancy
PA-10 completeness is relative to a declared abstraction (hierarchy
      inheritance, guard predicates) — state it in the matrix header
PA-11 aim for a witness trace per matrix cell, not just happy paths
PA-12 every reachable cell gets ≥1 test; untestable cells carry reasons
PA-13 undesired-event checklist applied to every external source
PA-14 the matrix is the primary review surface; keep it round-trippable
PA-15 lint checklist follows the Jaffe–Leveson completeness criteria:
      every input in every state, timing on waiting states, startup/
      shutdown defined, capacity bounded, robustness to undesired events
PA-16 render complex guards as AND/OR tables for human review
```

## Lineage (why this works)

The mechanisms are not novel. They descend from tabular requirements methods for safety-critical software. The A-7E requirements document and Heninger's method paper made completeness checkable while staying reviewable; pilots found errors by inspection.

The SCR formalization added automated disjointness and coverage checking, the one-input assumption, and mode classes. Gargantini–Heitmeyer generated tests from table cells. The Jaffe–Leveson criteria define completeness. RSML/TCAS II (hierarchical state machines + AND/OR guard tables) is the closest architectural relative.

The lineage is methodological, not a certification claim.

### References

<!-- vale off — bibliography: proper names and citation titles are not prose -->
* Heninger, Kallander, Parnas, Shore. *Software Requirements for the A-7E Aircraft.* NRL 3876, 1978.
* Heninger. *Specifying Software Requirements for Complex Systems.* IEEE TSE SE-6(1), 1980.
* Parnas, Madey. *Functional Documents for Computer Systems.* SCP 25(1), 1995.
* Heitmeyer, Jeffords, Labaw. *Automated Consistency Checking of Requirements Specifications.* ACM TOSEM 5(3), 1996.
* Gargantini, Heitmeyer. *Using Model Checking to Generate Tests from Requirements Specifications.* ESEC/FSE 1999.
* Jaffe, Leveson, Heimdahl, Melhart. *Software Requirements Analysis for Real-Time Process-Control Systems.* IEEE TSE 17(3), 1991.
* Leveson, Heimdahl, Hildreth, Reese. *Requirements Specification for Process-Control Systems.* IEEE TSE 20(9), 1994.
* Heimdahl, Leveson. *Completeness and Consistency in Hierarchical State-Based Requirements.* IEEE TSE 22(6), 1996.
<!-- vale on -->

Tool pointers (optional, not dependencies): Mermaid for diagrams; `z3-solver` (pip) for ad-hoc guard proofs; mutation tools (`mutmut`, `cosmic-ray`, Stryker). Use Quint (quint.sh) if a composed multi-machine design ever warrants formal simulation/checking.
