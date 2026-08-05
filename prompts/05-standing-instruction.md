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

Keep `domain-analysis/summary.md` current as the living index (component table with DRs/tests/manifest, totals, known gaps): update it on every stage completion, every pilot, and every reconcile. The hard enforcement in CI is the cell suites plus the pack checker gate (`dsc_check` per sidecar-carrying component, 04-testgen).
