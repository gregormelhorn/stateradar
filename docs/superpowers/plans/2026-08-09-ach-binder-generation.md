# ACH Binder-Driven Mutant Generation (golden-mini) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Keep checkbox state accurate. Review before final summary.

**Goal:** Replace the hand-authored golden-mini `F-01`, `F-02`, and `F-05` variant files with deterministic generator outputs from a component-local binding file, while preserving the existing `fault-mutants.json` and checker contracts.

**Architecture:** Add `mutant-generation.json` plus `tools/gen_mutant_variants.py`; regenerate the three existing variant files; add minimal selftest coverage for generator green/red cases; update the prompt and roadmap to document the new maintenance path. `F-04` stays hand-authored.

**Tech stack:** Python 3 stdlib only, existing golden-mini fixture, existing fault-mutant checker, existing selftest framework.

## Global Constraints

- Do **not** change `formats/rules.toml`.
- Do **not** change the `fault-mutants.json` schema.
- Do **not** change `tools/check_fault_mutants.py` or `tools/check_matrix_mutation.py`.
- `F-04` stays hand-authored and out of generator scope.
- v1 generator scope is golden-mini only.
- v1 class scope is `F-01`, `F-02`, `F-05` only.
- `F-01` and `F-02` remain matrix-level by doctrine. Their generated variant files are a fixture-maintenance bridge only.
- `F-05` must carry the `dup_count` projection dependency.
- No release, tag, or push without explicit user instruction.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tests/golden-mini/domain-analysis/mini/mutant-generation.json` | Component-local binding file for `F-01`, `F-02`, `F-05`. |
| `tools/gen_mutant_variants.py` | Deterministic generator and drift checker. |
| `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py` | Generated output; must remain byte-identical to the intended fixture. |
| `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py` | Generated output; must remain byte-identical to the intended fixture. |
| `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py` | Generated output; must remain byte-identical to the intended fixture. |
| `tools/selftest/run_selftest.py` | Generator green/red selftest coverage. |
| `prompts/04-testgen.md` | Note the optional `mutant-generation.json` maintenance flow. |
| `docs/roadmap.md` | Item 8 status wording no longer says golden-mini binder generation is deferred. |
| `docs/superpowers/specs/2026-08-09-ach-binder-generation-design.md` | Spec for this wave. |
| `docs/superpowers/plans/2026-08-09-ach-binder-generation.md` | This execution checklist. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/progress.md` | SDD ledger. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/task-1-brief.md` | Task 1 brief. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/task-1-report.md` | Task 1 report. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/task-2-brief.md` | Task 2 brief. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/task-2-report.md` | Task 2 report. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/task-3-brief.md` | Task 3 brief. |
| `.superpowers/sdd/2026-08-09-ach-binder-generation/task-3-report.md` | Task 3 report. |

---

## Task 1: Binding file and generator tool

**Files:**
- Create: `tests/golden-mini/domain-analysis/mini/mutant-generation.json`
- Create: `tools/gen_mutant_variants.py`
- Regenerate: `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py`
- Regenerate: `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py`
- Regenerate: `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py`

**Interfaces:**
- Consumes: `tests/golden-mini/src/mini.py`
- Consumes: `tests/golden-mini/domain-analysis/mini/fault-mutants.json`
- Produces: three deterministic variant files, with the same paths already referenced by `fault-mutants.json`

- [ ] **Step 1: Write `mutant-generation.json`**

Create a v1 config with:

- `formatVersion = 1`
- `workingDirectory = "../.."`
- `source = "src/mini.py"`
- `projections.dup_count.kind = "counter"`
- `projections.dup_count.provenBy = "F-05-corrupt-state-Open-UV-M1-dup"`

Add exactly three `bindings[]` entries:

- `F-01` / `missing-transition` / `Open x M2`
- `F-02` / `transfer-fault` / `Open x M2`
- `F-05` / `corrupt-state` / `Open x UV-M1-dup`

Each binding must carry:

- `fault`
- `binder`
- `id`
- `cell`
- `variant`
- `mode = "replace-block"`
- `match`
- `replace`

`F-05` additionally carries:

- `requiresProjection = "dup_count"`

- [ ] **Step 2: Implement `tools/gen_mutant_variants.py`**

Support:

```bash
python3 tools/gen_mutant_variants.py <analysis-dir>
python3 tools/gen_mutant_variants.py --check <analysis-dir>
```

Hard requirements:

- load `mutant-generation.json`
- resolve the component root from `workingDirectory`
- load `fault-mutants.json`
- require 1:1 ID/path agreement between bindings and `fault-mutants.json`
- support exact `replace-block` only
- require exactly one source match per binding
- in generate mode, write the three variant files
- in check mode, compare generated content to tracked files and fail on drift
- report `BLOCKED` if a binding requires an undeclared projection
- do **not** edit `fault-mutants.json`
- do **not** touch `F-04`

- [ ] **Step 3: Regenerate the tracked variant files**

Run:

```bash
python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini
```

Expected:

- three `GENERATED` lines
- `MUTANT GENERATION: OK (generated=3 drift=0 blocked=0 errors=0)`

- [ ] **Step 4: Verify drift-free check mode**

Run:

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
```

Expected:

- three `OK` lines
- `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)`

- [ ] **Step 5: Confirm the fault-mutant contract still kills the generated files**

Run:

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
```

Expected:

- `BASELINE: OK`
- four `KILLED` lines
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`

If any mutant survives: stop. Report the survivor. Do not change the contract silently.

- [ ] **Step 6: Commit Task 1**

```bash
git add tests/golden-mini/domain-analysis/mini/mutant-generation.json \
  tools/gen_mutant_variants.py \
  tests/golden-mini/src/mutants/mini.F-01-missing-transition.py \
  tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py \
  tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py
git commit -m "Generate golden-mini ACH mutants from binder constraints" \
  -m "Evidence:
- gen_mutant_variants write mode: generated=3 drift=0 blocked=0 errors=0
- gen_mutant_variants check mode: checked=3 drift=0 blocked=0 errors=0
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)"
```

---

## Task 2: Minimal selftest wiring for the generator

**Files:**
- Modify: `tools/selftest/run_selftest.py`

**Interfaces:**
- Consumes: the golden-mini binding file and generated variants from Task 1

- [ ] **Step 1: Add the green check-mode case**

Add a selftest case that runs:

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
```

Expected:

- success
- summary line contains `checked=3`
- no `DRIFT`
- no `BLOCKED`

- [ ] **Step 2: Add a red drift case**

In a temp copy of golden-mini:

- change one generated variant line by hand
- rerun `--check`

Expected:

- nonzero exit
- a `DRIFT` line naming that variant
- summary contains `drift=1`

- [ ] **Step 3: Add a red BLOCKED case for `F-05`**

In a temp copy of golden-mini:

- remove `projections.dup_count` from `mutant-generation.json`
- rerun `--check`

Expected:

- nonzero exit
- `BLOCKED F-05-corrupt-state-Open-UV-M1-dup projection dup_count undeclared`
- summary contains `blocked=1`

This is the v1 precondition integration. Do not widen it into checker-level BLOCKED automation.

- [ ] **Step 4: Add a red config case for an unmatched source block**

In a temp copy of golden-mini:

- alter one `match` line so the source no longer matches exactly once
- rerun the generator

Expected:

- nonzero exit
- `CONFIG ERROR` naming the binding ID and the zero-match problem

- [ ] **Step 5: Run the full selftest**

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

Expected:

- `SELFTEST: OK`
- explicit green line for generator check mode
- explicit red coverage for drift, blocked, and bad-match cases
- existing fault-mutant and matrix-mutation cases still green

- [ ] **Step 6: Commit Task 2**

```bash
git add tools/selftest/run_selftest.py
git commit -m "Selftest binder-driven mutant generation" \
  -m "Evidence:
- SELFTEST: OK
- generator green case passes
- drift red case fails as required
- blocked red case fails as required
- bad-match red case fails as required"
```

---

## Task 3: Prompt, roadmap, spec, plan, and SDD ledger

**Files:**
- Modify: `prompts/04-testgen.md`
- Modify: `docs/roadmap.md`
- Create: `docs/superpowers/specs/2026-08-09-ach-binder-generation-design.md`
- Create: `docs/superpowers/plans/2026-08-09-ach-binder-generation.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/progress.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/task-1-brief.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/task-1-report.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/task-2-brief.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/task-2-report.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/task-3-brief.md`
- Create: `.superpowers/sdd/2026-08-09-ach-binder-generation/task-3-report.md`

- [ ] **Step 1: Update `prompts/04-testgen.md`**

Add a short maintenance note in the fault-mutant subsection:

- a component may ship `mutant-generation.json`
- run `python3 tools/gen_mutant_variants.py --check domain-analysis/<component>`
- golden-mini’s `F-01` / `F-02` generated variants are a fixture bridge only
- layer ownership does not change

Keep `fault-mutants.json` as the execution contract.

- [ ] **Step 2: Update roadmap item 8**

Replace “binder-driven generation deferred” wording with a narrower statement:

- golden-mini now derives `F-01`, `F-02`, `F-05` fixture variants from bindings
- this removes hand-authored drift
- broader operator generation remains deferred
- real-component coverage remains deferred

- [ ] **Step 3: Write the spec and plan files**

Persist the final versions of:

- `docs/superpowers/specs/2026-08-09-ach-binder-generation-design.md`
- `docs/superpowers/plans/2026-08-09-ach-binder-generation.md`

- [ ] **Step 4: Initialize the SDD ledger**

Create `.superpowers/sdd/2026-08-09-ach-binder-generation/` with:

- `progress.md`
- `task-1-brief.md`
- `task-1-report.md`
- `task-2-brief.md`
- `task-2-report.md`
- `task-3-brief.md`
- `task-3-report.md`

`progress.md` should record:

- Task 1 status
- Task 2 status
- Task 3 status
- any deferred cosmetic findings
- review status per task

- [ ] **Step 5: Run the full gate set**

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
git status --short
```

Expected:

- `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)`
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`
- `MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)`
- `SELFTEST: OK`
- `PACK CONSISTENCY: OK`
- tool tests green
- benchmark commands green
- `git diff --check` clean
- `git status --short` shows only intended tracked changes before commit, then clean after commit

- [ ] **Step 6: Commit Task 3**

```bash
git add prompts/04-testgen.md \
  docs/roadmap.md \
  docs/superpowers/specs/2026-08-09-ach-binder-generation-design.md \
  docs/superpowers/plans/2026-08-09-ach-binder-generation.md \
  .superpowers/sdd/2026-08-09-ach-binder-generation
git commit -m "Document and gate binder-driven golden-mini mutant generation" \
  -m "Evidence:
- gen_mutant_variants --check: OK
- FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)
- MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)
- SELFTEST: OK
- PACK CONSISTENCY: OK
- git diff --check: OK"
```

- [ ] **Step 7: STOP**

Stop after the local commits.

Report:

- commit SHAs
- generator summary line
- four `KILLED` lines by fault class
- roadmap item 8 wording
- any deferred findings

Do **not**:

- release
- tag
- push
- widen scope to other classes
- widen scope to `F-04`
- widen scope to real components
- widen scope to reverse-family matrix operators

## Execution Handoff

Execute only Tasks 1–3.

Out of scope for this wave:

- reverse-family matrix operator work
- automated checker-level BLOCKED preflight beyond the generator’s local declaration check
- any class beyond `F-01`, `F-02`, `F-05`
- any component beyond golden-mini
- grpc-go `addrConn`
- `F-08` end-to-end work
