# Test Generation Prompt — One Test per Matrix Cell

**How to use:** run after resolution (03), when a to-be model and an updated matrix exist. Fill in CONFIG. Then paste this file into your coding agent at the repository root. The model is the oracle; the code is under test, not the other way around. The examples use Python and pytest. Adapt them mechanically to the project's language and test framework.

## CONFIG — fill in before running

```text
Analysis directory:            domain-analysis/<component>/
Component under test:          <path>
Test framework:                <pytest | vitest | ...>
Test output directory:         tests/domain/<component>/
May introduce a test seam:     <no (propose only) | yes, behaviour-preserving>
May modify the component to
match the to-be model:         <no (report deviations only) | yes, smallest change, cite DRs>
```

---

## PROMPT

You generate a conformance test suite from an approved behavioural model.

### Hard rules

1. Tests assert only through the declared observation points: the projected state, the emitted effects (through fakes and spies), and the SYS invariants. Never assert on implementation internals or code structure. Tests specify behaviour, not code. This is the anti-mirroring rule.
2. Never weaken, skip, or delete a test to make it pass. A failing test against current code is a **finding**: the code deviates from the approved model. It is not a defect of the test.
3. If the seam cannot observe a cell's expected outcome: mark the cell `untestable-via-seam` in the coverage map and give the reason. Do not fake a passing test. A reasoned untestable cell is a valid outcome. A high untestable share (rule of thumb: a third or more of the grid) is a boundary signal — the behaviour may belong to a neighbouring model. Record that as a model link and, when the link is new, as a question; do not grind out shallow tests to make the ratio look better (dobby mqtt-consumer: 6 of 12 cells untestable because replay belongs to session-recovery).
4. Respect the CONFIG switches. Under "propose only", write down the minimal seam or code change and stop. Do not perform it.
5. Every test cites its matrix cell. If a DR fixed the disposition, the test cites the DR too.

### Step 1 — Seam

Identify how to initialize a known state and context. Identify how to deliver exactly one event at a time. Observe the resulting state through a state-projection function. Observe emitted effects in order (fake transport, fake bus, spies). Control time through an injectable clock or fake timer.

Document the seam in `seam.md`: the projection, the fakes, the clock mechanism. If no adequate seam exists: under "propose only", write the minimal behaviour-preserving change and stop after Step 2. Under "yes", implement it behaviour-preserving and note it in `seam.md`.

### Step 2 — Cell tests

Write one test per matrix cell (state × catalogue event, incl. undesired variants). Conventions:

* naming: `test_cell__<state>__<event>`; undesired variants add a suffix, for example `__duplicate`
* docstring: disposition, DR link, provenance
* arrange: reach the state. Prefer an event sequence from the initial state (a generated path). Use direct construction only where the seam supports it and the path is impractical.
* act: deliver the event. Deliver undesired variants concretely: duplication = deliver twice; stale = deliver after the state moved on; delay = advance the fake clock past the timeout first.
* assert by disposition: `transition` → the projected state equals the target, and the expected effects appear in order; `handle` → state unchanged, expected effect emitted; `ignore` → state unchanged, no effect; `reject` → the declared rejection signal (error, diagnostic, nack); `defer (queued)` → state unchanged, the event visible in the queue, processed on the entry that dequeues it
* after **every** delivered event, assert all SYS invariants from `invariants-and-lints.md`

For each (state, event) with guarded transitions, add boundary tests: below the limit, exactly at the limit (`==`), and above the limit.

→ `tests/domain/<component>/test_cells_*.py`

Name test files `test_<component>.py` (one per component) — pytest
collection requires unique basenames across the domain suite, and
`test_cells.py` / `test_router.py` collide the moment a second
component adopts the same name (dobby, 2026-08-05: three collisions in
one week).

### Step 3 — Scenario tests

Convert each adversarial trace from `adversarial-traces.md` whose question has a DR into a multi-event scenario test. Assert the decided outcome and the SYS invariants at every step. Skip undecided traces and list them.

→ `test_scenarios_*.py`

### Step 4 — Coverage map and checker

Write `matrix-coverage.json`: every matrix cell → test id, or `untestable-via-seam: <reason>`. Keep the generated suite type-clean: the cell suite must pass the repo's static type gate — typed seams make assertions machine-checkable, and untyped fixture helpers are where construction bugs hide (dobby found ~8 real construction bugs the first time the domain suite was type-gated, 2026-08-05). Extend `domain-analysis/<component>/check_matrix.py` with two checks. Every non-UNSPECIFIED cell has a mapped test or a reasoned untestable entry. Every ignore/reject/defer cell has a DR link. Then wire both checkers into the suite:

```python
def test_matrix_discipline():
    assert run_check_matrix() == OK   # grid complete, DR links present, cells covered
    assert run_check_guards() == OK   # every guard group proven / violation-free / labelled
```

This puts the model discipline itself into CI. Whoever breaks a disposition, a DR link, a guard proof, or coverage breaks the build.

For components with an `analysis.json` sidecar, also wire the pack checker as a parametrized test over every sidecar-carrying component (`dsc_check.py <dir> --repo . --model as-is.machine.mmd` per component). Always pass `--model`: the checker resolves Mermaid container states (`state open { idle --> busy }`) against compound matrix labels (`open idle`), so a hierarchical diagram no longer needs the check switched off. One test function per component keeps failures attributable.

When a component has an executable cell suite, write an optional
`matrix-mutation.json` beside `disposition-matrix.md`:

```json
{
  "formatVersion": 1,
  "testCommand": ["python3", "tests/test_cell_suite.py", "{analysis_dir}"],
  "workingDirectory": "../..",
  "timeoutSeconds": 30
}
```

`testCommand` is an argv array. It contains `{analysis_dir}` exactly once. The
mutation checker replaces that token with an isolated mutated analysis copy:

```bash
python3 tools/check_matrix_mutation.py domain-analysis/<component>
```

A surviving mutant is a coverage finding. Do not weaken or skip a cell test to
make a mutant survive or pass.

#### Fault-class hardening (`fault-mutants.json`)

Optionally, harden the suite against hand-authored implementation mutants
per fault class. An **F-04 sneak-path** mutant changes one `ignore (documented)`
or `reject` cell to accept the event instead. The suite must detect and kill it:
the behavioral check for that cell must fail.

The same pattern defines F-01 (a `transition →X` cell does not
transition), F-02 (a `transition →X` cell lands in the wrong target), and
F-05 (a `handle` cell corrupts the counted state). Golden-mini ships one
killed mutant per class as the fixture proof.

Write `fault-mutants.json` beside `disposition-matrix.md`:

```json
{
  "formatVersion": 1,
  "testCommand": ["python3", "tests/test_cell_suite.py", "{analysis_dir}"],
  "workingDirectory": "../..",
  "timeoutSeconds": 5,
  "mutants": [
    {
      "fault": "F-04",
      "id": "F-04-sneak-path-Closed-M1",
      "target": "src/mini.py",
      "variant": "src/mutants/mini.F-04-sneak-path.py",
      "cell": "Closed x M1"
    }
  ]
}
```

`testCommand` is an argv array. It contains `{analysis_dir}` exactly once.
The checker replaces that token with an isolated analysis copy:

```bash
python3 tools/check_fault_mutants.py domain-analysis/<component>
```

The `testCommand` must invoke the suite by relative path so the checker
runs the copied script inside the temporary component copy; an absolute
path would exercise the pristine implementation and every mutant would survive.

A surviving mutant is a suite finding. Never weaken or skip a cell test
to make a mutant survive or pass.

##### Optional: derived variant files (`mutant-generation.json`)

`fault-mutants.json` stays the execution contract. A component may also
ship `mutant-generation.json` beside it. That file binds a mutant ID to
one exact source block and one replacement block, so the variant file is
derived instead of hand-edited. Check it for drift:

```bash
python3 tools/gen_mutant_variants.py --check domain-analysis/<component>
python3 tools/gen_mutant_variants.py domain-analysis/<component>
```

Check mode compares the derived content against the tracked variant file
and reports `DRIFT`. Write mode regenerates the variant files. A binding
that needs a projection the config does not declare reports `BLOCKED`.
Mutants with no binding stay hand-authored and report `UNBOUND`.

Golden-mini derives its `F-01`, `F-02`, and `F-05` variants this way. That
is a fixture bridge against hand-authored drift. It does not change layer
ownership: `F-01` and `F-02` stay matrix-level families, `F-05` stays
implementation-level, and `F-04` stays hand-authored.

### Step 5 — Run and report

Run the full suite. Write `deviation-report.md`: every failing test is a deviation of the current code from the approved model, listed as `cell / expected (DR) / observed (file:line)`. Under "report only", this list is the implementation worklist. Stop here. Under "yes, smallest change": implement the smallest change per deviation, cite the DR, and rerun until green. Never resolve a deviation by touching the test.

### Step 6 — Summary

Update `summary.md`: cells total / tested / untestable / UNSPECIFIED-skipped; scenarios converted / skipped; the suite result; the deviations found (and fixed, if permitted); the checker status. Optional honesty probe, if a mutation tool is available (`mutmut`, `cosmic-ray`, Stryker). Run it on the component's lifecycle code. Report surviving mutants as weak spots of the suite.
