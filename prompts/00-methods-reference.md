# StateRadar Method — Reference

This is the methodology behind the prompt pack. It uses Harel-style statecharts as explicit domain-behaviour specification and test oracle for software that AI coding agents write or modify. It condenses the full product handoff document (rev. 2) into a tooling-free form. Generated, executed checker scripts and normal test infrastructure (pytest + CI) do the work of the deterministic tooling described there.

Give this file to agents as context when running the pack prompts.

---

## Purpose and scope

The objective is not to control the coding agent. The objective is to bring **application-domain behaviour and test generation** under control:

1. domain logic must not remain hidden and silently decided inside AI-generated code;
2. tests must derive from explicit behaviour, not mirror the implementation.

Use the method for behaviour involving: lifecycles, connection management,
protocol phases, asynchronous events, timeouts, retries, cancellation,
recovery, sessions, mutually exclusive modes, concurrent coordination.
This includes components whose state is explicit (enums, transition tables),
implicit (boolean flags, nullable references), or **loop-phase** — where the
lifecycle emerges from the phases of a retry/backoff/polling loop rather than
from a declared state variable (cenkalti/backoff, 2026-08-06).

Do not use it for: pure calculations, stateless transformations, formatting,
validation, ordinary CRUD without temporal behaviour. Statefulness alone does
not qualify; *temporal* behaviour does. One machine per bounded context, never
one global machine.

The method produces artifacts that serve three purposes:

1. **Specification and test oracle** — the matrix defines expected behaviour;
   tests assert against it.
2. **CI-enforceable discipline** — grid totality and DR links break the
   build on drift; doctrine-to-cell mapping is lint-enforced in Step 5
   (a checker candidate, tracked in `formats/rules.toml`).
3. **Public API documentation** — the statechart and terminal-state table
   are human-readable references for library consumers. A user migrating
   between major versions of a retry library needs the five-terminal-states
   table more than they need the source code (cenkalti/backoff #185,
   2026-08-06).

### Runtime boundary (PA-19)

The statechart models **discrete state transitions** triggered by **events**.
This leaves several behavioural layers outside its scope:

* **Language runtime state.** `sys.exc_info()`, traceback chaining, garbage
  collection, JIT behaviour, memory model details. These affect observable
  behaviour but are not statechart-modelable events (tenacity #534,
  2026-08-06: two Retrying blocks interacting via unittest's exception
  machinery).
* **OS-level behaviour.** Signal handling, OOM killer, scheduler preemption,
  page faults. Assume these are captured by NAT invariants or excluded.
* **Performance/deadline behaviour.** The statechart models *what* happens,
  not *how fast*. A timeout is an event; whether the timeout fires at 99ms
  or 101ms is a runtime concern.

If a finding depends on any of these, it is **not verifiable from the
statechart alone**. Flag it as `unverifiable-runtime` and require a
separate test or inspection.

### API contract vs. state machine (PA-20)

The statechart models **internal behavioural state** — what the component
does in response to events. The **public API contract** — what values
methods return, what exceptions they raise, what guarantees they make to
callers — is a separate layer.

* A method that returns stale data after a state transition is an API
  contract violation, not a state machine bug (tenacity #517,
  2026-08-06: `statistics` dict persisting after retry completes is a
  documented API contract, not a state leak).
* A method whose behaviour varies between decorator and context-manager
  usage is two different entry points into the same state machine — the
  machine is the same, the API surface differs (tenacity #511,
  2026-08-06: `fn=None` in context manager, non-None in decorator).

When a finding involves the API contract, ask: is this a state machine
issue (wrong transition), or an API design issue (wrong return value)?
Only the former belongs in the matrix.

### Lifecycle disagreement pattern (PA-21)

When two independent lifecycles share a resource, a terminal state in one
lifecycle must trigger a transition in the other:

| Pattern | Example | Bug |
|---|---|---|
| Caller vs. internal request | Timeout fires → caller done, but permit still held by internal request | valkey-glide #5803: stalled node exhausts shared capacity |
| Caller-local deadline vs. transport callback | Local `close_timeout` expires → transport closed, but `connection_lost()` callback never fires → caller still blocked | python-websockets #1527: server silent for 7 minutes with Wi-Fi off |
| Caller terminal vs. scheduler admission claim | Caller cancelled → receiver dropped, but `oneshot::Sender` still in scheduler queue → capacity, eviction, selection, metrics all polluted | Meilisearch SearchQueue #6508: dead waiters evict live requests |
| Public vs. background goroutine | Connection closed → user state terminal, but reconnect goroutine still holds lock | reconnecting-websocket Q-01: `_connectLock` leaked after maxRetries |
| User API vs. system cleanup | User calls `close()` but pending timer callback still mutates state | Common in async libraries |
| Explicit vs. implicit cleanup | `Permit::drop(self)` fires, then Rust `Drop` impl fires again → double release | Meilisearch SearchQueue #6578: two release signals per explicit drop |

**Detection rule:** When you extract a state variable (counter, lock, flag)
that is accessed from more than one lifecycle context, model each lifecycle
as a separate track. A terminal state in one track that does not have a
corresponding transition in the other track's cleanup state is a coupling
bug. The fix is always the same: the terminal transition must trigger the
cleanup transition in the shared resource track.

### Requirement-to-cell mapping (PA-22)

Every numbered requirement from the doctrine sweep (DOC-n) must map to at
least one matrix cell. Validate mechanically:

1. For each DOC-n, find the (state, event) cell that implements it.
2. If the cell is `UNSPECIFIED` or has a contradictory disposition, the
   requirement is **violated** — the code does not implement what the
   requirements demand.
3. If no cell maps to the requirement, the requirement is **unimplemented**.
   Raise a Q.

This turns the doctrine sweep from documentation into a verifiable
compliance check. The valkey-glide pilot (2026-08-06) demonstrated this:
Requirement 3 ("release immediately on timeout") maps to the cell
(CallerTimedOut, release_permit). That cell was `UNSPECIFIED` in the
as-is matrix — a direct match to the production bug (#5803).

### Dual ownership cleanup paths (PA-23)

When a resource object has **both** an explicit release method
(`close()`, `drop(self)`, `dispose()`) **and** an implicit
cleanup hook (destructor, `Drop` impl, `__del__`, `defer`), model
both as independent events in the Held state. The disposition matrix
must have cells for `ExplicitReleaseRequested` and for
`ImplicitCleanupTriggered`. If both can fire for the same resource
instance (because the explicit method's return triggers the implicit
hook), the invariant "exactly one logical release per permit" must
be proven — either the second path is no-oppable, or one path
suppresses the other. Meilisearch SearchQueue D1 (2026-08-06):
`Permit::drop(self)` sends one signal, then Rust's `Drop for Permit`
sends a second. Every explicit release produced two capacity returns.

### Async cancellation isolation (PA-24)

In async/await languages, cancelling a task or dropping a future
does **not** automatically propagate to resources that were
transferred to other tasks before cancellation. The sender-side
and receiver-side lifecycles are separate orthogonal regions in
the statechart. A terminal event in the receiver region (caller
cancelled, future dropped) must have an **explicit** synchronization
transition to the sender region (entry becomes ineligible). Implicit
sync does not exist across channel boundaries. Meilisearch SearchQueue
D2/#6508 (2026-08-06): `oneshot::Sender<Permit>` survived receiver
cancellation and continued to affect capacity, eviction, selection,
and metrics — because no explicit cancellation event reached the
scheduler region.

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

<!-- generated:rules key=disposition-vocab -->
```text
transition → <target> | handle | ignore (documented) | ignore (accidental)*
| defer (queued) | reject | UNSPECIFIED*
```
<!-- /generated:rules -->

Values marked * count as specification holes. Never accept "nothing happens" implicitly: it is either a documented, DR-linked ignore, or a hole. State dispositions at compound-state level; substates inherit them. Mark inherited cells with their source. Only unresolved leaf cells count as holes. In the to-be matrix, every `ignore` / `reject` / `defer` cell carries its DR link, and `ignore (accidental)` may no longer appear.

## Event catalogue and undesired variants

Every event lists: name, source, external/internal, payload gist, where produced and consumed. For every external source, derive undesired variants by checklist (each category carries its fault-class id from `formats/rules.toml`):

<!-- generated:rules key=uv-categories -->
* loss or failure of the source (F-12, sidecar key: `loss`)
* delay beyond timeout (F-13, sidecar key: `delay`)
* duplication (F-14, sidecar key: `duplication`)
* out-of-order or stale arrival, especially after cancellation or shutdown (F-15, sidecar key: `out-of-order`)
* contradictory simultaneous inputs (F-16, sidecar key: `contradiction`)
* spontaneous commission — an event with no legitimate trigger (spurious wakeup, callback without a matching request, unsolicited push) (F-17, sidecar key: `commission`)
* subtle value fault — a plausible but wrong payload (foreign session or entity id, stale epoch or generation counter) (F-18, sidecar key: `value`)
<!-- /generated:rules -->

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

### State naming convention (PA-17)

Part A (code-aware) and Part B (blind) must name states consistently so the
diff is mechanical, not interpretive. Both passes follow the same rules:

1. **Prefer the public API name.** If the component exposes a state enum
   (`CONNECTING`, `OPEN`, `CLOSED`, `CLOSED`), use that name.

2. **Name sub-states by their CONDITION, not by the implementation flag.**
   "AwaitingStability" not "`_uptimeTimeout_active`"; "RetriesExhausted" not
   "`_retryCount>=maxRetries`"; "UserRequested" not "`_closeCalled`". A blind
   reader who has only the requirements can derive these names.

3. **Format: PascalCase, `_` as sub-state separator.** `Open_AwaitingStability`,
   `Open_Stable`, `Closed_UserRequested`, `Closed_RetriesExhausted`.
   The first segment is the parent state; the rest are qualifying conditions.

4. **One state per behaviorally distinct combination.** If changing one flag
   changes the disposition of at least one event, it is a separate state.
   If two flag combinations produce identical dispositions across all events,
   they are the same state.

### Terminal states (PA-18)

A **terminal state** is a state from which no event can cause a transition.
The component has left the active lifecycle and will not process further
events (Retry returned, connection permanently closed, process exited).

1. **Mark terminal states in the matrix.** Instead of a full row of
   `ignore (documented)`, add a single declaration after the matrix:
   `<!-- terminal: Succeeded, PermanentFailure, Exhausted, TimedOut, Cancelled -->`.
   The checker treats all events in terminal states as `ignore (documented)`
   with an implicit citation to the state's entry condition.

2. **Name terminal states by their exit condition.** "Exhausted" not
   "State_MaxTriesReached"; "Cancelled" not "State_ContextCancelled".
   Terminal states are the API contract — they tell the caller why the
   component stopped. The names should be meaningful in isolation.

This eliminates repetitive cells (cenkalti/backoff, 2026-08-06:
5 terminal states × 14 events = 70 cells of identical `ignore (documented)`).

5. **Document the condition.** Every state name carries a one-line description
   in the catalogue or extraction: "`Open_AwaitingStability`: connection
   established but min-uptime not yet reached (DOC-9)."

This convention removes the mapping problem discovered in the
reconnecting-websocket Part-B diff (2026-08-06): the blind pass used
human-readable names ("CLOSED", "OPEN_unstable") while the matrix used
machine-readable names ("Closed_Idle", "Open_Unstable"). Both were valid;
neither could match the other. With PA-17, Part A extracts states from the
code and names them per the convention; Part B derives states from the
requirements and names them per the SAME convention. The diff matches by
name because both passes speak the same language.

## Testing conventions

* **One test per matrix cell**, named `test_cell__<state>__<event>[__variant]`, docstring citing disposition and DR.
* Assert by disposition (target state + effects / unchanged + effect / unchanged + nothing / rejection signal / queued).
* **Boundary tests** for every guarded pair: below, exactly at (`==`), above the limit.
* **Scenario tests** from decided adversarial traces, SYS invariants asserted at every step.
* `matrix-coverage.json` maps every cell to its test or a reasoned `untestable-via-seam` entry; the checker verifies the map.
* A failing test is a **finding** (code deviates from the approved model), never a defect of the test. Never weaken, skip, or delete tests to pass. Fix deviations in code or, with human approval, in the model plus a superseding DR.
* Optional honesty probe: run a mutation tool (`mutmut`, `cosmic-ray`, Stryker) over the lifecycle code; surviving mutants are weak spots of the suite.
* Calibration probe for the method itself: run the pilot twice on the same component in fresh sessions and diff the matrices. Divergence measures how much you can trust a single unverified run.

## Method rules (PA-1 … PA-24, condensed)

Settled by prior art; agents must not relitigate them without a DR. In pack mode, generated checker scripts, explicit reasoning marked unproven, and the CI-wired test suite discharge the "Analyzer/tooling" duties.

The registry `formats/rules.toml` is the single source for these rules — their class (wellformedness | completeness | fault-model | process), their enforcement (checker | test | lint | prompt | human | data), and the fault-class catalogue (F-xx) they detect. The list below is generated from it (`tools/gen_rules.py`); a split id (PA-3a/PA-3b) marks a rule whose original prose mixed two classes.

<!-- generated:rules key=pa-condensed -->
```text
PA-1   guards per (state,event) pairwise disjoint — order must never decide
PA-2   guards jointly exhaustive, or an explicit else exists; gap = hole
PA-3a  guard checks state their assumptions; z3 proofs via a generated
       check_guards.py where formalizable
PA-3b  unformalizable guards keep inspection-only reasoning, labelled
       `not-formalizable: <category>` from the closed vocabulary
PA-4   events classified: monitored input | controlled output | internal
PA-5   derived events may be defined as @T(predicate) WHEN condition
PA-6a  invariants split NAT vs SYS
PA-6b  analysis may assume NAT, tests may not
PA-7   bindings (abstract action → concrete symbol) are part of the spec
PA-8   single-input assumption: one event to completion at a time
PA-9a  tests require a serializing dispatch seam
PA-9b  probe reentrancy from callbacks and event handlers
PA-10  completeness is relative to a declared abstraction (hierarchy
       inheritance, guard predicates) — state it in the matrix header
PA-11  aim for a witness trace per matrix cell, not just happy paths
PA-12  every reachable cell gets ≥1 test; untestable cells carry reasons
PA-13a undesired-event checklist applied to every external source; the
       coverage table is total
PA-13b the checklist categories are registry data (SHARD-aligned); extending
       them is a data edit, not a prose edit
PA-14a the matrix round-trips with the diagram; sync is checker-verified
PA-14b the matrix is the primary review surface
PA-15  lint checklist follows the Jaffe–Leveson completeness criteria: every
       input in every state, timing on waiting states, startup/shutdown
       defined, capacity bounded, robustness to undesired events
PA-16  render complex guards as AND/OR tables for human review
PA-17  state naming: public API names, condition-named sub-states, PascalCase
       with `_` separator — blind-derivable from requirements
PA-18a terminal states declared after the matrix; the checker treats their
       events as ignore (documented)
PA-18b terminal states named by their exit condition — they are the API
       contract
PA-19  language-runtime, OS, and performance behaviour are outside the
       statechart; findings there are `unverifiable-runtime`
PA-20  wrong return values are API-contract issues, wrong transitions are
       matrix issues; only the latter belong in the matrix
PA-21  shared state across independent lifecycles: a terminal state in one
       track must trigger cleanup in the other
PA-22  every DOC-n requirement maps to ≥1 matrix cell; UNSPECIFIED there =
       violated, no cell = unimplemented
PA-23  explicit release and implicit destructor are independent events; prove
       exactly-one logical release
PA-24  receiver-side terminal events need explicit sync transitions to the
       sender region — implicit sync does not cross channel boundaries
```
<!-- /generated:rules -->

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
* Binder. *Testing Object-Oriented Systems: Models, Patterns, and Tools.* Addison-Wesley, 1999. (State-machine fault taxonomy: the F-xx catalogue names.)
* Pumfrey, McDermid. *Software Safety Analysis — SHARD.* (HAZOP guide words for software: omission, commission, early, late, value — the undesired-variant categories.)
* Chillarege et al. *Orthogonal Defect Classification.* IEEE TSE 18(11), 1992. (Defect type × trigger — the fault-class/detector fields on findings.)
<!-- vale on -->

Tool pointers (optional, not dependencies): Mermaid for diagrams; `z3-solver` (pip) for ad-hoc guard proofs; mutation tools (`mutmut`, `cosmic-ray`, Stryker). Use Quint (quint.sh) if a composed multi-machine design ever warrants formal simulation/checking.
