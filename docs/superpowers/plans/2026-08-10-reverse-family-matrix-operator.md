# Reverse Matrix Operator Family Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `ignore-to-handle` mutation family to `tools/check_matrix_mutation.py`, then add one `ignore`-dispositioned UV column to golden-mini so the family is executed on the undesired-variant shape it exists for.

**Architecture:** Task A adds one mutator function plus wiring in `build_mutations`, gated by a kill-count assertion and three red cases in the selftest. Task B adds the `UV-M2-stale` event to the golden-mini fixture end to end (implementation, matrix column, catalogue annotations, cell suite, regenerated sidecar and variants), which puts three more eligible cells in front of the new family. Each task is separately committed and separately green.

**Tech stack:** Python 3 stdlib, existing golden-mini fixture, existing matrix-mutation checker, existing selftest framework, `uv` for dev dependencies.

## Global Constraints

- Do **not** change `formats/rules.toml`.
- Do **not** change `matrix-mutation.json` or its schema.
- Do **not** change `fault-mutants.json`, `tools/check_fault_mutants.py`, or `tools/gen_mutant_variants.py` as code. Task B *runs* the generator; it does not edit it.
- Do **not** mutate `ignore (accidental)`, `UNSPECIFIED`, or `defer (queued)` cells. See spec Decision 1.
- Exactly one new UV column. F-12, F-16, F-17, F-20 stay unclaimed.
- Do **not** edit `CHANGELOG.md` and do **not** bump the pack version. See "Spec deviations" below.
- Never resolve a `SURVIVED` mutant by weakening the suite or adjusting an expected count. A survivor stops the wave and is reported.
- No release, tag, or push.

## Amendments made during execution

Two defects were found after this plan was first written. Both are already
applied above; they are recorded here so a reader diffing plan against spec
does not see an unexplained divergence.

1. **The hole case needs its own `matrix-mutation.json`** (Task A, Step 1b).
   `sidecar()` copies the analysis dir to a temp path, but the copied config's
   `workingDirectory` is the relative `"../.."`, which does not survive the
   copy. The checker then cannot find the test command and stops at
   `BLOCKED: baseline exit=2` before running a single mutation. The fix writes
   a fresh config with an absolute `workingDirectory`. Verified not to mask the
   assertion: with the family absent the hole case still reports `killed=9`,
   so `killed=12` still goes red.

2. **The mutator keeps only the trailing citation** (Task A, Step 3). The first
   version sliced after the disposition token and preserved everything else, so
   `ignore (documented) DR-005; reason \`f:1\`` became
   `handle DR-005; reason \`f:1\`` — a mutant reading as if DR-005 authorised
   handling. Golden-mini has no annotated ignore cell, so no gate could catch
   it; the silenceper benchmark matrix does have that shape. A selftest case
   that builds an annotated cell was added, observed red, then fixed.

3. **Task B Step 6 scopes the generator with `--root tests/golden-mini`**
   (Task B, Step 6). The plan's `--root . --analysis-dir
   tests/golden-mini/domain-analysis mini` invocation makes
   `gen_analysis_sidecar._src_index` walk the whole repo — no SRC_ROOTS base
   exists at the repo root, so it falls back to root and an unsorted walk,
   where `tools/selftest/src/mini.py` shadows `tests/golden-mini/src/mini.py`
   (first hit wins). Every cell citation then reads `tools/selftest/src/mini.py`
   and `dsc_check --repo tests/golden-mini` fails with twelve
   `citation: tools/selftest/src/mini.py does not exist` errors. `--root
   tests/golden-mini` is the correct scope: it reproduces the committed golden
   sidecar byte-for-byte and yields `DSC CHECK: OK (3 states x 4 events,
   12 cells, 0 guard groups)`. The `--repo tests/golden-mini` dsc_check flag
   is untouched.

4. **The selftest's part-B fixtures follow the live catalogue** (Task B, Step
   11). `run_selftest.py` builds its inline blind tables and validates them
   against the golden-mini catalogue via `part_b_pack.py --check`, so adding
   the `UV-M2-stale` event to the catalogue necessarily broke the two green
   cases (`blind table complete`, `blind table finer than one row per id`)
   with `missing row: UV-M2-stale`. The two red cases were extended too, but
   only to keep each failing for its stated reason alone: `partial` now
   reports only `missing row: UV-M1-dup`, and `dup` only `duplicated
   checklist entry: M2` (verified by direct `part_b_pack --check` runs).

## Spec deviations (read before starting)

The spec `docs/superpowers/specs/2026-08-10-reverse-family-matrix-operator-design.md` lists `CHANGELOG.md` under "surfaces that move". **That is wrong and this plan overrides it.** Verified at HEAD:

- `CHANGELOG.md:12-14` reads "Supported v1 mutations: transition→ignore, transition-target-swap, handle→ignore. Golden-mini fixture proves weak-suite red and 9/9 kill green behavior." That entry sits under `## v1.50`, and v1.50 genuinely shipped three families and 9/9. It is a release record, not a live status line. Rewriting it would make the changelog lie about what v1.50 contained.
- `tools/check_pack_consistency.py:62-72` hard-errors unless `README.md`'s `**Version X.Y**` equals the newest `## vX.Y` CHANGELOG heading. Adding a `## v1.51` heading would therefore force a README version bump, i.e. a release — which this wave forbids.
- Precedent: the previous wave (`4861e95`) moved `docs/roadmap.md` and the prompts but left `CHANGELOG.md` and the version untouched, and `PACK CONSISTENCY` stayed green at 1.50.

So: `README.md` (living capability description) and `docs/roadmap.md` (living status) move. `CHANGELOG.md` and the version do not.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tools/check_matrix_mutation.py` | The `ignore-to-handle` mutator and its wiring. |
| `tools/selftest/run_selftest.py` | Kill-count assertions, the family's red cases, and the part-B blind-table fixtures (lines 611-651, keyed to the live catalogue: each new catalogue event needs a row + checklist tick there). |
| `README.md:174-175` | Living family list shown to readers. |
| `docs/roadmap.md` item 7 | Living family list for the mutation checker. |
| `docs/roadmap.md` item 8 | Fault-class claim accounting (F-15 claimed, four still not). |
| `tests/golden-mini/src/mini.py` | The `UV-M2-stale` branch. |
| `tests/golden-mini/domain-analysis/mini/disposition-matrix.md` | The new column and the abstraction count. |
| `tests/golden-mini/domain-analysis/mini/event-catalogue.md` | Event id list, catalogue row, M2 out-of-order coverage. |
| `tests/golden-mini/tests/test_cell_suite.py` | `EVENTS` must gain the new id, in column order. |
| `tests/golden-mini/domain-analysis/mini/analysis.json` | Regenerated sidecar. Never hand-edited. |
| `tests/golden-mini/expected/analysis.json` | Golden copy of the sidecar. Refreshed by `cp`. |
| `tests/golden-mini/src/mutants/mini.F-0{1,2,5}-*.py` | Regenerated by `tools/gen_mutant_variants.py`. |

---

## Task 0: Commit this plan

**Files:**
- Add: `docs/superpowers/plans/2026-08-10-reverse-family-matrix-operator.md`

- [ ] **Step 1: Confirm a clean starting tree**

This plan was committed by its author before handoff, so every later `git status --short` check is meaningful.

```bash
git status --short
git log --oneline -1
```

Expected: `git status --short` prints nothing, and the newest commit is `Plan the reverse matrix operator family wave`.

If the tree is dirty, stop and report `BLOCKED(task-0): working tree not clean at handoff` with the output. Do not start Task A on top of unrelated changes.

---

## Task A: The `ignore-to-handle` family

**Files:**
- Modify: `tools/check_matrix_mutation.py` (add function after `handle_to_ignore` at line 183-188; wire into `build_mutations` at line 191-201)
- Modify: `tools/selftest/run_selftest.py:293-304`
- Modify: `README.md:174-175`
- Modify: `docs/roadmap.md:72-77`

**Interfaces:**
- Produces: mutation `kind` string `"ignore-to-handle"`, consumed by Task B's selftest assertions.
- Produces: `MUTATION CHECK: OK (killed=13 ...)` on golden-mini, which Task B raises to 16.

- [ ] **Step 1a: Write the failing count assertion**

All four assertions go in **before** the mutator exists, so each one is observed red first (R-RED-PROBE). Apply Step 1a and Step 1b together, then run Step 2 once.

In `tools/selftest/run_selftest.py`, replace this exact block (currently lines 303-304):

```python
        expect("mutation checker golden-mini kills supported mutants", False,
               *mutation(gm), needle="MUTATION CHECK: OK")
```

with:

```python
        rc_gm, out_gm = mutation(gm)
        expect("mutation checker golden-mini kills supported mutants", False,
               rc_gm, out_gm, needle="MUTATION CHECK: OK")
        if "killed=13" not in out_gm:
            failures.append("matrix mutation count: expected killed=13\n" + out_gm)
        else:
            print("  ok  matrix mutation count killed=13 (passes)")
```

- [ ] **Step 1b: Write the other three failing assertions**

Still in `tools/selftest/run_selftest.py`, replace this exact block (currently lines 293-302):

```python
        weak = sidecar(tmp, gm)
        (weak / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "-c", "import sys; raise SystemExit(0)", "{analysis_dir}"],
            "workingDirectory": ".",
            "timeoutSeconds": 5,
        }))
        expect("mutation checker reports weak suite survivors", True,
               *mutation(weak), needle="SURVIVED")
```

with:

```python
        weak = sidecar(tmp, gm)
        (weak / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "-c", "import sys; raise SystemExit(0)", "{analysis_dir}"],
            "workingDirectory": ".",
            "timeoutSeconds": 5,
        }))
        rc_weak, out_weak = mutation(weak)
        expect("mutation checker reports weak suite survivors", True,
               rc_weak, out_weak, needle="SURVIVED")
        if "kind=ignore-to-handle" not in out_weak:
            failures.append("weak suite: expected an ignore-to-handle survivor\n" + out_weak)
        else:
            print("  ok  weak suite survives an ignore-to-handle mutant (fails as required)")

        hole = sidecar(tmp, gm)
        hole_mx = hole / "disposition-matrix.md"
        hole_mx.write_text(hole_mx.read_text().replace(
            "| **Open** | ignore (documented) `mini.py:22` |",
            "| **Open** | ignore (accidental) → Q-01 |"))
        (hole / "matrix-mutation.json").write_text(json.dumps({
            "formatVersion": 1,
            "testCommand": ["python3", "tests/test_cell_suite.py", "{analysis_dir}"],
            "workingDirectory": str(ROOT / "tests" / "golden-mini"),
            "timeoutSeconds": 5,
        }))
        rc_hole, out_hole = mutation(hole)
        expect("mutation checker leaves hole cells unmutated", False,
               rc_hole, out_hole, needle="MUTATION CHECK: OK")
        if "killed=12" not in out_hole:
            failures.append("hole cell: expected killed=12 (one fewer than 13)\n" + out_hole)
        else:
            print("  ok  hole cell produces no ignore-to-handle mutant (passes)")
```

Then, immediately after the `killed=13` block you added in Step 1a, append:

```python
        if "new='handle `mini.py:28`'" not in out_gm:
            failures.append("ignore-to-handle must drop the source annotation, "
                            "not carry it into the replacement\n" + out_gm)
        else:
            print("  ok  ignore-to-handle replacement drops the (documented) annotation (passes)")
```

Note on that last case: a naive implementation slicing after `"ignore"` instead of `"ignore (documented)"` produces `new='handle (documented) \`mini.py:28\`'` and fails this assertion. That is its red state.

- [ ] **Step 2: Run the selftest and watch all four assertions fail**

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
```

Expected: nonzero exit, with **all four** of these failure blocks present, because the mutator does not exist yet:

- `matrix mutation count: expected killed=13` (actual output shows `killed=9`)
- `weak suite: expected an ignore-to-handle survivor`
- `hole cell: expected killed=12 (one fewer than 13)` (actual shows `killed=9`)
- `ignore-to-handle must drop the source annotation`

If fewer than four fail, or any fails for a different reason, stop and report. **Paste this output into the task report** — this is the R-RED-PROBE evidence that all four assertions can fail.

- [ ] **Step 3: Implement the mutator**

In `tools/check_matrix_mutation.py`, insert this function immediately after `handle_to_ignore` (which ends at line 188, just before `def build_mutations`):

```python
def ignore_or_reject_to_handle(cell: Cell) -> str | None:
    """Reverse family: a decided no-action cell claims it acts.

    Eligible: 'ignore (documented)' and 'reject'. Holes ('ignore (accidental)',
    'UNSPECIFIED') and 'defer (queued)' are never mutated - see the wave spec.
    The source annotation is dropped so the replacement reads 'handle', not
    'handle (documented)'; only the citation suffix survives.
    """
    for token in ("ignore (documented)", "reject"):
        if cell.raw == token:
            return "handle"
        if cell.raw.startswith(token + " "):
            citation = re.search(r"`[^`]+`\s*$", cell.raw)
            return f"handle {citation.group(0).strip()}" if citation else "handle"
    return None
```

This needs `import re` at the top of `tools/check_matrix_mutation.py`, after `import json`.

- [ ] **Step 4: Wire it into `build_mutations`**

In `build_mutations`, after the existing `handle_to_ignore` block (lines 199-201), add:

```python
        replacement = ignore_or_reject_to_handle(cell)
        if replacement is not None:
            pending.append((cell.state, cell.event, "ignore-to-handle", replacement, cell))
```

- [ ] **Step 5: Run the checker and confirm the four new mutants**

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
```

Expected: `MUTATION CHECK: OK (killed=13 survived=0 errors=0 blocked=0)`, with four lines carrying `kind=ignore-to-handle` for these cells:

| state | event | old | new |
|---|---|---|---|
| Idle | M2 | `ignore (documented) \`mini.py:28\`` | `handle \`mini.py:28\`` |
| Open | M1 | `ignore (documented) \`mini.py:22\`` | `handle \`mini.py:22\`` |
| Closed | M1 | `reject \`mini.py:23\`` | `handle \`mini.py:23\`` |
| Closed | M2 | `ignore (documented) \`mini.py:28\`` | `handle \`mini.py:28\`` |

**Paste the four `kind=ignore-to-handle` lines into the task report.** If any says `SURVIVED`, stop and report it as a finding.

- [ ] **Step 6: Run the full selftest**

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
```

Expected: `SELFTEST: OK`, including these four lines:

```
  ok  matrix mutation count killed=13 (passes)
  ok  weak suite survives an ignore-to-handle mutant (fails as required)
  ok  hole cell produces no ignore-to-handle mutant (passes)
  ok  ignore-to-handle replacement drops the (documented) annotation (passes)
```

**Paste those four lines into the task report.**

- [ ] **Step 7: Update the two living prose surfaces**

In `README.md`, replace lines 174-175 exactly:

```
**Spec mutants** (`tools/check_matrix_mutation.py`) mutate the *matrix* —
`transition → ignore`, target swap, `handle → ignore` — and run the declared
```

with:

```
**Spec mutants** (`tools/check_matrix_mutation.py`) mutate the *matrix* —
`transition → ignore`, target swap, `handle → ignore`, and the reverse
`ignore`/`reject → handle` — and run the declared
```

In `docs/roadmap.md`, replace this sentence in item 7 (lines 74-75):

```
`matrix-mutation.json`. The checker supports transition-to-ignore, transition
target-swap, and handle-to-ignore mutations. It reports killed and surviving
```

with:

```
`matrix-mutation.json`. The checker supports transition-to-ignore, transition
target-swap, handle-to-ignore, and the reverse ignore/reject-to-handle
mutations. It reports killed and surviving
```

- [ ] **Step 8: Run the full gate set**

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
git status --short
```

Expected:

- `MUTATION CHECK: OK (killed=13 survived=0 errors=0 blocked=0)`
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`
- `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)`
- `SELFTEST: OK`
- `PACK CONSISTENCY: OK (20 artifacts, registry, version 1.50)`
- `2/2 cases pass`
- `Results: 6 passed, 0 failed, 6 total`
- `Primary evidence: 3, Regression anchors: 3, Unknown: 0`
- `git diff --check` silent
- `git status --short` lists the four intended files. It may also list `?? docs/superpowers/plans/2026-08-10-reverse-family-matrix-operator.md` if the plan was not committed in Task 0; that one untracked file is expected and is not a finding.

- [ ] **Step 9: Commit Task A**

```bash
git add tools/check_matrix_mutation.py tools/selftest/run_selftest.py README.md docs/roadmap.md
git commit -m "Add reverse matrix mutation family: ignore/reject to handle" \
  -m "Evidence:
- red probe: killed=13 assertion added first, selftest failed with killed=9
- MUTATION CHECK: OK (killed=13 survived=0 errors=0 blocked=0)
- four new mutants, all KILLED, kind=ignore-to-handle:
    Idle x M2, Open x M1, Closed x M1 (reject), Closed x M2
- SELFTEST: OK incl. count, weak-suite family pin, hole-cell, annotation cases
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- PACK CONSISTENCY: OK (20 artifacts, registry, version 1.50)
- git diff --check: clean"
```

---

## Task B: The `UV-M2-stale` column

**Files:**
- Modify: `tests/golden-mini/src/mini.py` (insert after line 31)
- Modify: `tests/golden-mini/domain-analysis/mini/disposition-matrix.md`
- Modify: `tests/golden-mini/domain-analysis/mini/event-catalogue.md`
- Modify: `tests/golden-mini/tests/test_cell_suite.py:11`
- Regenerate: `tests/golden-mini/domain-analysis/mini/analysis.json`
- Regenerate: `tests/golden-mini/expected/analysis.json`
- Regenerate: `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py`, `mini.F-02-transfer-fault.py`, `mini.F-05-corrupt-state.py`
- Modify: `tools/selftest/run_selftest.py` (counts from Task A)
- Modify: `docs/roadmap.md` item 8

**Interfaces:**
- Consumes: `kind=ignore-to-handle` from Task A.
- Produces: `MUTATION CHECK: OK (killed=16 ...)`.

- [ ] **Step 0a: Move the counts and add the UV pin (red probe, before any fixture change)**

The assertions move first so each is observed red before the fixture makes it pass.

In `tools/selftest/run_selftest.py`:

Replace `"killed=13"` with `"killed=16"`, the message `"matrix mutation count: expected killed=13"` with `"matrix mutation count: expected killed=16"`, and the print `"  ok  matrix mutation count killed=13 (passes)"` with `"  ok  matrix mutation count killed=16 (passes)"`.

Replace `"killed=12"` with `"killed=15"` and the message `"hole cell: expected killed=12 (one fewer than 13)"` with `"hole cell: expected killed=15 (one fewer than 16)"`.

Then pin the UV shape. Replace:

```python
        if "kind=ignore-to-handle" not in out_weak:
            failures.append("weak suite: expected an ignore-to-handle survivor\n" + out_weak)
        else:
            print("  ok  weak suite survives an ignore-to-handle mutant (fails as required)")
```

with:

```python
        if "kind=ignore-to-handle" not in out_weak:
            failures.append("weak suite: expected an ignore-to-handle survivor\n" + out_weak)
        elif not any("kind=ignore-to-handle" in line and "event=UV-M2-stale" in line
                     for line in out_weak.splitlines()):
            failures.append("weak suite: the ignore-to-handle survivor must include a "
                            "UV cell - that is the shape the family exists for\n" + out_weak)
        else:
            print("  ok  weak suite survives an ignore-to-handle mutant on a UV cell "
                  "(fails as required)")
```

- [ ] **Step 0b: Run the selftest and watch the three assertions fail**

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
```

Expected: nonzero exit, with all three failing because `UV-M2-stale` does not exist yet:

- `matrix mutation count: expected killed=16` (actual output shows `killed=13`)
- `hole cell: expected killed=15 (one fewer than 16)` (actual shows `killed=12`)
- `weak suite: the ignore-to-handle survivor must include a UV cell`

**Paste this output.** It is the R-RED-PROBE evidence for Task B.

- [ ] **Step 1: Add the event to the implementation**

In `tests/golden-mini/src/mini.py`, insert **after** line 31 (`            return "handled"`) and **before** line 32 (`        raise ValueError(event)`):

```python
        if event == "UV-M2-stale":
            return "ignored"
```

The new lines become 32-33. **Append only** — this is deliberate. Every existing citation (`mini.py:19`, `:22`, `:23`, `:26`, `:28`, `:30`) keeps its line number, so no existing matrix cell, fault-mutant, or generator `match` block needs editing. Verify with:

```bash
sed -n '29,35p' tests/golden-mini/src/mini.py
```

Expected:

```
        if event == "UV-M1-dup":
            self.dup_count += 1
            return "handled"
        if event == "UV-M2-stale":
            return "ignored"
        raise ValueError(event)
```

- [ ] **Step 2: Add the matrix column and fix the abstraction count**

In `tests/golden-mini/domain-analysis/mini/disposition-matrix.md`, replace lines 5-6:

```
Abstraction: flat leaf states, no hierarchy; completeness is relative
to the three-event catalogue.
```

with:

```
Abstraction: flat leaf states, no hierarchy; completeness is relative
to the four-event catalogue.
```

and replace lines 9-13 (the whole table):

```
| state | M1 | M2 | UV-M1-dup |
|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` |
```

with:

```
| state | M1 | M2 | UV-M1-dup | UV-M2-stale |
|---|---|---|---|---|
| **Idle** | transition →Open `mini.py:19` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
| **Open** | ignore (documented) `mini.py:22` | transition →Closed `mini.py:26` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
| **Closed** | reject `mini.py:23` | ignore (documented) `mini.py:28` | handle (counted) `mini.py:30` | ignore (documented) `mini.py:33` |
```

- [ ] **Step 3: Add the catalogue entry and bind the coverage category**

In `tests/golden-mini/domain-analysis/mini/event-catalogue.md`:

Replace line 3:

```
<!-- event-ids: M1 M2 UV-M1-dup -->
```

with:

```
<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale -->
```

Add this row to the events table, immediately after the `UV-M1-dup` row:

```
| UV-M2-stale | stale close after shutdown | operator | external | id | op | svc |
```

In the `### M2` annotation block, replace:

```
  - out-of-order: n/a: sync
```

with:

```
  - out-of-order: UV-M2-stale
```

Leave `### M1`'s coverage untouched, and give `UV-M2-stale` **no** annotation section — undesired variants inherit gate and upstream guards from their base event (`tools/dsc_check.py:178-185`), exactly as `UV-M1-dup` does today.

- [ ] **Step 4: Add the event to the cell suite**

In `tests/golden-mini/tests/test_cell_suite.py`, replace line 11:

```python
EVENTS = ["M1", "M2", "UV-M1-dup"]
```

with:

```python
EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale"]
```

Leave `NAVIGATE` (line 10) unchanged — the new event is never used to navigate. Order matters: `parse_matrix` uses `zip(EVENTS, cells[1:], strict=True)` at line 32, so `EVENTS` must match the matrix column order exactly or the suite raises `ValueError`.

- [ ] **Step 5: Run the cell suite directly and confirm it is green**

```bash
( cd tests/golden-mini && python3 tests/test_cell_suite.py domain-analysis/mini ); rc=$?; echo "exit=$rc"; test "$rc" -eq 0 && echo "ASSERT OK" || echo "ASSERT FAILED"
```

Expected: `CELL SUITE: OK`, then `exit=0`, then `ASSERT OK`. Twelve cells now parse (3 states × 4 events).

The explicit `test` is deliberate: `cmd; echo "exit=$?"` prints the right number but leaves the *shell's* exit status at 0, so a harness that gates on exit code would read a failure as success.

If you see `ValueError`, `EVENTS` and the matrix columns are out of sync — fix that before continuing.

- [ ] **Step 6: Regenerate the sidecar and refresh the golden copy**

```bash
uv run --with jsonschema python3 tools/gen_analysis_sidecar.py --root tests/golden-mini
cp tests/golden-mini/domain-analysis/mini/analysis.json tests/golden-mini/expected/analysis.json
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
```

Expected: the generator reports `3 states x 4 events = 12 cells`, and `DSC CHECK: OK (3 states x 4 events, 12 cells, 0 guard groups)`.

`--repo tests/golden-mini` is required and verified. The fixture's citations are `src/mini.py` **relative to the component root**, so `--repo .` produces nine `citation: src/mini.py does not exist` errors and `DSC CHECK: FAIL`.

Never hand-edit either JSON file. If `dsc_check` reds on `UV coverage` or `R-GATE-TYPE`, the catalogue edit in Step 3 is incomplete — fix Step 3, do not patch the JSON.

- [ ] **Step 7: Regenerate the mutant variants**

The three generated variants are full copies of `src/mini.py`, so they are now stale. Prove it, then fix it:

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini; rc=$?; echo "exit=$rc"; test "$rc" -eq 1 && echo "ASSERT RED AS REQUIRED" || echo "ASSERT FAILED: expected exit 1"
```

Expected: three `DRIFT` lines, `MUTANT GENERATION: FAIL (checked=3 drift=3 blocked=0 errors=0)`, `exit=1`, then `ASSERT RED AS REQUIRED`. **Paste this** — it is the evidence that the binder generation from the previous wave is doing real work.

If you see `ASSERT FAILED`, the variants were already regenerated or the edit in Step 3 did not land. Stop and report.

Then:

```bash
python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
```

Expected: three `GENERATED` lines, then `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)`.

- [ ] **Step 8: Confirm the fault-mutant contract still holds**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
```

Expected: `BASELINE: OK`, four `KILLED` lines, `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`.

A survivor here means the regenerated variants no longer express their fault. Stop and report.

- [ ] **Step 9: Confirm the new column produces three more kills**

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
```

Expected: `MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)`, including three lines with `kind=ignore-to-handle` and `event=UV-M2-stale` (states Idle, Open, Closed), each `KILLED`.

**Paste those three lines.** They are the whole point of the wave: the reverse family executing on an undesired-variant cell.

- [ ] **Step 10: Confirm the counts moved in Step 0a are intact**

No edit is needed here: the three assertions were already moved in Step 0a. Confirm they are still present and unmodified:

```bash
grep -c 'killed=16\|killed=15\|event=UV-M2-stale' tools/selftest/run_selftest.py
```

Expected: `5` or more. If it reports `0`, Step 0a was skipped — go back and do it, then re-run Step 0b before continuing.

- [ ] **Step 11: Run the full selftest**

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
```

Expected: `SELFTEST: OK`, including:

```
  ok  matrix mutation count killed=16 (passes)
  ok  weak suite survives an ignore-to-handle mutant on a UV cell (fails as required)
  ok  hole cell produces no ignore-to-handle mutant (passes)
  ok  ignore-to-handle replacement drops the (documented) annotation (passes)
```

- [ ] **Step 12: Update roadmap item 8 with honest class accounting**

In `docs/roadmap.md` item 8, replace this sentence:

```
implementation-level, and F-04 stays hand-authored. Broader binder-driven
generation and real-component coverage remain pending.
```

with:

```
implementation-level, and F-04 stays hand-authored. Broader binder-driven
generation and real-component coverage remain pending.

The reverse matrix family (ignore/reject → handle) now ships, and golden-mini
carries a `UV-M2-stale` column so the family runs on an undesired-variant
cell. That claims **F-15** (out-of-order/stale) with fixture proof. It does
**not** claim F-12, F-16, or F-17: the registry binds one UV category to one
class, so each needs its own column. F-20 needs a terminal-progress shape,
which is not a UV column at all. Those four remain unclaimed.
```

- [ ] **Step 13: Run the full gate set**

```bash
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
uv run --with jsonschema python3 tools/check_reachability.py tests/golden-mini/domain-analysis/mini
git diff --check
git status --short
```

Expected:

- `MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)`
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`
- `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)`
- `SELFTEST: OK`
- `PACK CONSISTENCY: OK (20 artifacts, registry, version 1.50)`
- `2/2 cases pass` — this proves `expected/analysis.json` was refreshed correctly
- `Results: 6 passed, 0 failed, 6 total`
- `Primary evidence: 3, Regression anchors: 3, Unknown: 0`
- `REACHABILITY CHECK: OK`
- `git diff --check` silent

- [ ] **Step 14: Commit Task B**

```bash
git add tests/golden-mini/src/mini.py \
  tests/golden-mini/domain-analysis/mini/disposition-matrix.md \
  tests/golden-mini/domain-analysis/mini/event-catalogue.md \
  tests/golden-mini/domain-analysis/mini/analysis.json \
  tests/golden-mini/expected/analysis.json \
  tests/golden-mini/tests/test_cell_suite.py \
  tests/golden-mini/src/mutants/ \
  tools/selftest/run_selftest.py \
  docs/roadmap.md
git commit -m "Run the reverse family on a UV cell: golden-mini UV-M2-stale" \
  -m "Evidence:
- generator drift proven before regeneration: drift=3, exit=1
- MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0) after regen
- MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)
- three new KILLED mutants kind=ignore-to-handle event=UV-M2-stale (Idle/Open/Closed)
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0) against regenerated variants
- DSC CHECK: OK (3 states x 4 events, 12 cells)
- SELFTEST: OK incl. UV-shape pin on the weak-suite case
- run_tool_tests: 2/2 cases pass (golden sidecar refreshed)
- PACK CONSISTENCY: OK (20 artifacts, registry, version 1.50)
- roadmap item 8: F-15 claimed; F-12/F-16/F-17/F-20 named unclaimed with reasons"
```

- [ ] **Step 15: STOP**

Report:

- both commit SHAs
- the `killed=9 → 13 → 16` progression
- the four Task A mutant lines and the three Task B UV mutant lines
- the drift=3 evidence from Step 7
- any deferred findings

Do **not**: release, tag, push, add a second UV column, touch `CHANGELOG.md`, bump the version, add a `defer` family, or widen to real components.

---

## Execution Handoff

Execute Tasks A and B in order. Task B depends on Task A's `kind=ignore-to-handle` string and on its selftest counts.

Out of scope for this wave:

- any second, third, or fourth UV column (F-12, F-16, F-17 stay unclaimed)
- the terminal-progress shape for F-20
- a `defer (queued)` family
- `CHANGELOG.md` and any version bump
- `grpc-go addrConn`, `F-08`, the clock seam
- real-component coverage

---

## Execution evidence (durable record)

Both waves' red probes were run and observed. Neither commit body carried the
transcript, and two independent reviews raised the same gap: an R-RED-PROBE
claim whose only referent is a gitignored subagent artefact is not
self-evidencing. The transcripts are recorded here, in a tracked file, so the
claim has a durable home. This is the countermeasure — the ledger under
`.superpowers/` cannot serve, because it is gitignored.

### Task A, Step 2 — four assertions red before the mutator existed

Run against `617a628`, with all four assertions added and `ignore_or_reject_to_handle`
not yet written:

```text
 - matrix mutation count: expected killed=13
   ... MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)
 - hole cell: expected killed=12 (one fewer than 13)
   ... (actual killed=9)
 - weak suite: expected an ignore-to-handle survivor
 - ignore-to-handle must drop the source annotation, not carry it into the replacement
SELFTEST_EXIT=1
```

Exactly four failure blocks. The `mutation checker leaves hole cells unmutated`
`expect()` passed, which is why the count assertion two lines below it is the
load-bearing one.

### Task B, Step 0b — three assertions red before the UV column existed

Run against `e88cc13`, with the counts moved to 16/15 and the UV pin added,
before `UV-M2-stale` was introduced:

```text
SELFTEST: FAIL
 - weak suite: the ignore-to-handle survivor must include a UV cell
   - that is the shape the family exists for
   ... MUTATION CHECK: FAIL (killed=0 survived=13 errors=0 blocked=0)
 - hole cell: expected killed=15 (one fewer than 16)
   ... MUTATION CHECK: OK (killed=12 survived=0 errors=0 blocked=0)
 - matrix mutation count: expected killed=16
   ... MUTATION CHECK: OK (killed=13 survived=0 errors=0 blocked=0)
exit=1
```

Exactly three, each for the intended reason.

### Standing rule for future waves

R-RED-PROBE in `AGENTS.md` §7 already says "Paste both runs". It is satisfied
by pasting into the **commit body**, not into a subagent report. When a worker
reports a red probe, the reviewer of that commit must be able to find the
transcript in `git show`. If it is missing, the commit is incomplete even
though every gate is green.
