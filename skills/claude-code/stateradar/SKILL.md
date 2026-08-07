---
name: stateradar
description: "Use when you analyze, modify, test, or review stateful components (lifecycles, connections, sessions, protocols, state machines, retries, timeouts, cancellation, recovery, queues, concurrent coordination), or when the user mentions a disposition matrix, decision records, domain-analysis/, open questions, or the statechart method. Enforces StateRadar lifecycle contract verification: model first, no silent domain decisions, checker-verified matrices, one test per matrix cell."
---

# StateRadar Discipline

The pack's canonical prompts live in this repository (default vendored path:
`tools/prompt-pack/prompts/`; if absent, search for `prompts/00-methods-reference.md`).
Always load `00-methods-reference.md` as context first.

## Stage routing

Determine the state of the component in question and follow the matching prompt:

1. **No component chosen yet** (the user asks which component to analyze, or
   no candidate exists) → run `01-scout.md`. The scout ranks stateful components
   and generates the CONFIG block that the pilot consumes.
2. **No `domain-analysis/<component>/` exists** and the user wants analysis or
   is about to make behavioural changes to a stateful component →
   run `02-pilot.md`.
3. **Pilot exists, `open-questions.md` has answered questions** → run `03-resolution.md`.
   If questions stay unanswered, present them to the human. Never answer them yourself.
4. **To-be model and updated matrix exist, no cell tests yet** → run `04-testgen.md`.
5. **The component is already analyzed and the task is a code change** → follow
   `05-standing-instruction.md` strictly: read the model first, model + new DR before
   code, run the cell suite and both checkers (`check_matrix.py`, `check_guards.py`)
   after the change.

6. **Implementation merged, or the manifest reports staleness** (watched paths
   changed since `analyzedSha`) → run `06-reconcile.md` before any new analysis
   or model-first change.

7. **The user asks about weak, redundant, or superfluous tests** on an analyzed
   component → run `07-test-audit.md`. The audit classifies every test and cell.
   Deletion and weakening stay human decisions.

## Non-negotiable rules (all stages)

- Never silently decide ambiguous domain semantics; raise `UNSPECIFIED` + a question.
- Never change a dispositioned matrix cell, SYS invariant, or DR without a superseding DR.
- Never weaken, skip, or delete a cell test to make it pass.
- Deliver checks as executed code (checker scripts), never as claims.
