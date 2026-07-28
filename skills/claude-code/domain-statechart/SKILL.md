---
name: domain-statechart
description: "Use when you analyze, modify, test, or review stateful components — lifecycles, connections, sessions, protocols, state machines, retries, timeouts, cancellation, recovery, queues, concurrent coordination — or when the user mentions a disposition matrix, decision records, domain-analysis/, open questions, or the statechart method. Enforces the domain-statechart discipline: model first, no silent domain decisions, checker-verified matrices, one test per matrix cell."
---

# Domain Statechart Discipline

The pack's canonical prompts live in this repository (default vendored path:
`tools/prompt-pack/prompts/`; if absent, search for `prompts/00-methods-reference.md`).
Always load `00-methods-reference.md` as context first.

## Stage routing

Determine the state of the component in question and follow the matching prompt:

1. **No `domain-analysis/<component>/` exists** and the user wants analysis or
   is about to make behavioural changes to a stateful component →
   run `02-pilot.md` (suggest `01-scout.md` first if the component is not yet chosen).
2. **Pilot exists, `open-questions.md` has answered questions** → run `03-resolution.md`.
   If questions are unanswered, present them to the human — never answer them yourself.
3. **To-be model and updated matrix exist, no cell tests yet** → run `04-testgen.md`.
4. **The component is already analyzed and the task is a code change** → follow
   `05-standing-instruction.md` strictly: read the model first, model + new DR before
   code, run the cell suite and both checkers (`check_matrix.py`, `check_guards.py`)
   after the change.

5. **Implementation merged, or the manifest reports staleness** (watched paths
   changed since `analyzedSha`) → run `06-reconcile.md` before any new analysis
   or model-first change.

## Non-negotiable rules (all stages)

- Never silently decide ambiguous domain semantics; raise `UNSPECIFIED` + a question.
- Never change a dispositioned matrix cell, SYS invariant, or DR without a superseding DR.
- Never weaken, skip, or delete a cell test to make it pass.
- Checks are delivered as executed code (checker scripts), never as claims.
