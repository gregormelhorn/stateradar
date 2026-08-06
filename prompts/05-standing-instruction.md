# Standing Instruction — paste into CLAUDE.md / AGENTS.md

**How to use:** copy the block below into the repository's standing agent instructions (`CLAUDE.md`, `AGENTS.md`, or your harness's equivalent). It keeps every future agent session inside the model discipline. The hard enforcement is not this text. The hard enforcement is the checkers and the cell tests in the test suite (04). This text makes agents work with that enforcement instead of tripping over it.

---

## Domain-behaviour discipline (statechart-analyzed components)

An approved behavioural model governs a component with a directory under `domain-analysis/<component>/`: to-be statechart, disposition matrix, invariants, decision records. The directory, never an enumerated list, is the authority — a hardcoded component list in this file goes stale the day the next pilot lands (dobby: 4 listed, 15 governed). If you keep a dated list for orientation, regenerate it on every stage completion. For these components:

1. **Read before you touch.** Before you modify such a component, read its `to-be.machine.mmd`, `disposition-matrix.md`, `invariants-and-lints.md`, and `decisions/`.
2. **Model first, code second.** A behaviour change goes through the model. Update the matrix or model and add a new decision record (`decisions/DR-NNN.yaml`, next free number, citing the human request that authorizes it) **before** you change code. Never change a dispositioned matrix cell, a SYS invariant, or an existing DR without a superseding DR.
3. **Never decide silently.** If you meet behaviour the model does not specify (a new event, a new state, an unclear cell): record it as `UNSPECIFIED` in the matrix and raise the question in `open-questions.md`. Do not select an answer and continue, however plausible it seems.
4. **Green means conforming.** After each change, run the component's cell-test suite and the checkers (`check_matrix.py`, `check_guards.py`). All must pass. A failing cell test means the code deviates from the approved model. Fix the code, or change the model plus a new DR, and only with explicit human approval. Never fix the test in isolation. Never weaken or skip it.
5. **Follow the test conventions.** New behaviour tests use the cell-test conventions: one cell per test, SYS invariants asserted after every delivered event, `matrix-coverage.json` kept current.
6. **On conflict, ask.** If these rules conflict with other instructions in the session: stop and ask the human before you continue.
7. **Verify your own claims (v1.13).** After producing findings, re-read each bug claim against the code. Concurrency claims must cite memory ordering or synchronization primitives. Sentinel values must distinguish literal constants from computed results. Severity must be recalibrated: bug vs. design observation vs. documentation gap. A lock-free CAS that silently drops a transition is correct design, not a bug.
8. **Name states per PA-17.** Use PascalCase with `_` as sub-state separator. Prefer public API names. Name sub-states by their condition, not by the implementation flag: `Open_AwaitingStability` not `_uptimeTimeout_active`. Both Part A (code-aware) and Part B (blind) use the same convention.
9. **Mark terminal states (PA-18).** States from which no event can cause a transition are terminal. Declare them with `<!-- terminal: Succeeded, Exhausted -->` instead of a full row of `ignore (documented)` cells. The checker auto-generates the cells.
10. **Model loop-phase states.** For retry loops, backoff loops, and polling loops where states are the phases of iteration (Attempting, Evaluating, Waiting) rather than explicit enums, extract the phases from the `for`/`while` loop structure. Terminal states are the exit conditions.
11. **Model multi-instance behaviour (v1.11).** For components connecting to shared external resources, ask: do N instances reset internal state on the same external signal? Does this create a synchronization cascade? A state reset triggered by an external event that removes backpressure (retryCount→0) can produce a thundering herd.
12. **Record lock discipline (v1.12).** For every mutex-held section, state whether callbacks may re-enter public methods. A callback invoked under the mutex that calls back into the component is a deadlock.

Keep `domain-analysis/summary.md` current as the living index (component table with DRs/tests/manifest, totals, known gaps): update it on every stage completion, every pilot, and every reconcile. The hard enforcement in CI is the cell suites plus the pack checker gate (`dsc_check` per sidecar-carrying component, 04-testgen).
