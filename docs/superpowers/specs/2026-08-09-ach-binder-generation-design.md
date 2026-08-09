# ACH Binder-Driven Mutant Generation v1 (golden-mini)

**Date:** 2026-08-09  
**Scope:** Replace three hand-authored golden-mini implementation-variant files with deterministic generator outputs derived from component-local bindings. Keep `fault-mutants.json`, `check_fault_mutants.py`, and `check_matrix_mutation.py` unchanged.

## Goal

Generate the golden-mini variant files for:

- `F-01` missing transition
- `F-02` transfer fault
- `F-05` corrupt state

from a small binding file, so the fixture stops depending on manual copy-editing.

The generator is a **fixture-maintenance mechanism**, not a new checker contract.

## Layer rule and the explicit exception

The layer-separation spec stays authoritative:

- `F-01` is **matrix-level**
- `F-02` is **matrix-level**
- `F-05` is **implementation-level**

This spec makes one narrow exception:

- golden-mini may generate `F-01` and `F-02` implementation-variant files as a **demonstration bridge**
- this bridge exists only to remove hand-authored drift in the fixture
- it does **not** reclassify `F-01` or `F-02`
- it does **not** create implementation-level kill-rate credit for `F-01` or `F-02`
- the authoritative operator families for `F-01` and `F-02` remain the matrix-mutation families

`F-05` is the only class in this v1 that is both generated here and belongs to the implementation layer by doctrine.

## Architecture

### New component-local binding file

Create:

- `tests/golden-mini/domain-analysis/mini/mutant-generation.json`

This file is **not** a replacement for `fault-mutants.json`.

Responsibilities:

- bind a fault-class mutant ID to:
  - one source file
  - one exact source block
  - one replacement block
  - one variant output path
- keep the current `fault-mutants.json` contract untouched
- record the projection dependency for `F-05`

### New generator tool

Create:

- `tools/gen_mutant_variants.py`

CLI:

```bash
python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
```

Modes:

- **generate mode**: write the derived variant files
- **check mode**: generate in memory and compare against tracked files; fail on drift

The tool is deterministic and local. No AST engine. No code synthesis.

### Existing checker contract stays unchanged

Keep unchanged:

- `tests/golden-mini/domain-analysis/mini/fault-mutants.json`
- `tools/check_fault_mutants.py`
- `tools/check_matrix_mutation.py`

The fault-mutant checker still consumes explicit variant paths.  
The generator only ensures those files are derived reproducibly.

## Binding format v1

Use a narrow JSON format. No general AST mapping. No schema change elsewhere.

```json
{
  "formatVersion": 1,
  "workingDirectory": "../..",
  "source": "src/mini.py",
  "projections": {
    "dup_count": {
      "kind": "counter",
      "provenBy": "F-05-corrupt-state-Open-UV-M1-dup"
    }
  },
  "bindings": [
    {
      "fault": "F-01",
      "binder": "missing-transition",
      "id": "F-01-missing-transition-Open-M2",
      "cell": "Open x M2",
      "variant": "src/mutants/mini.F-01-missing-transition.py",
      "mode": "replace-block",
      "match": [
        "        if event == \"M2\":",
        "            if self.state == \"Open\":",
        "                self.state = \"Closed\"",
        "                return \"transition\"",
        "            return \"ignored\""
      ],
      "replace": [
        "        if event == \"M2\":",
        "            if self.state == \"Open\":",
        "                return \"ignored\"  # F-01 missing transition: Open x M2 never fires",
        "            return \"ignored\""
      ]
    },
    {
      "fault": "F-02",
      "binder": "transfer-fault",
      "id": "F-02-transfer-fault-Open-M2",
      "cell": "Open x M2",
      "variant": "src/mutants/mini.F-02-transfer-fault.py",
      "mode": "replace-block",
      "match": [
        "        if event == \"M2\":",
        "            if self.state == \"Open\":",
        "                self.state = \"Closed\"",
        "                return \"transition\"",
        "            return \"ignored\""
      ],
      "replace": [
        "        if event == \"M2\":",
        "            if self.state == \"Open\":",
        "                self.state = \"Idle\"  # F-02 transfer fault: Open x M2 lands in Idle",
        "                return \"transition\"",
        "            return \"ignored\""
      ]
    },
    {
      "fault": "F-05",
      "binder": "corrupt-state",
      "id": "F-05-corrupt-state-Open-UV-M1-dup",
      "cell": "Open x UV-M1-dup",
      "variant": "src/mutants/mini.F-05-corrupt-state.py",
      "mode": "replace-block",
      "requiresProjection": "dup_count",
      "match": [
        "        if event == \"UV-M1-dup\":",
        "            self.dup_count += 1",
        "            return \"handled\""
      ],
      "replace": [
        "        if event == \"UV-M1-dup\":",
        "            self.dup_count += 2  # F-05 corrupt state: counter moves by the wrong amount",
        "            return \"handled\""
      ]
    }
  ]
}
```

## Generator behavior

### Resolution and validation

The tool must:

1. load `mutant-generation.json`
2. resolve the component root from `workingDirectory`
3. read the declared `source`
4. read `fault-mutants.json`
5. require, for every binding, an injective mapping to exactly one entry in `fault-mutants.json` with matching `id` and `variant`:
   - `bindings[].id` ↦ `fault-mutants.json mutants[].id`
   - `bindings[].variant` ↦ `fault-mutants.json mutants[].variant`
   Unbound mutants in `fault-mutants.json` (e.g., `F-04` hand-authored) are permitted and reported as `UNBOUND <id> <variant>`.

A missing or mismatched mapping for a binding is a `CONFIG ERROR` (exit 2).

### Replacement model

Supported operator in v1:

- `mode = "replace-block"`

Semantics:

- find the exact `match` block in pristine `src/mini.py`
- require exactly one match
- replace that block with `replace`
- write the full result to `variant`

Hard failures:

- zero matches
- more than one match
- duplicate binding IDs
- duplicate output paths
- unknown fault ID / binder pairing
- `fault-mutants.json` mismatch
- missing source or variant parent path

This is deliberate. Silent fallback is forbidden.

### Output contract

Generate exactly these files:

- `tests/golden-mini/src/mutants/mini.F-01-missing-transition.py`
- `tests/golden-mini/src/mutants/mini.F-02-transfer-fault.py`
- `tests/golden-mini/src/mutants/mini.F-05-corrupt-state.py`

Do not touch:

- `tests/golden-mini/src/mutants/mini.F-04-sneak-path.py`

`F-04` stays hand-authored in this wave.

### BLOCKED preconditions

This wave does **not** add checker-level BLOCKED automation to `check_fault_mutants.py`.

It does integrate preconditions in the generator’s own contract:

- `F-05` binding carries `requiresProjection = "dup_count"`
- `mutant-generation.json` must declare that projection in `projections`
- the declaration names the existing canary mutant ID:
  - `F-05-corrupt-state-Open-UV-M1-dup`

If the binding requires a projection that is undeclared, the generator reports:

- `BLOCKED <mutant-id> projection <name> undeclared`

and exits nonzero.

Why this is enough in v1:

- golden-mini already proves the `dup_count` projection through the existing behavioral suite and fault-mutant kill proof
- this wave reuses that proof
- broader automated canary enforcement across components remains future work

This respects the layer-separation spec without widening checker scope.

## Expected tool output

### Generate mode

Example shape:

```text
GENERATED F-01 F-01-missing-transition-Open-M2 -> src/mutants/mini.F-01-missing-transition.py
GENERATED F-02 F-02-transfer-fault-Open-M2 -> src/mutants/mini.F-02-transfer-fault.py
GENERATED F-05 F-05-corrupt-state-Open-UV-M1-dup -> src/mutants/mini.F-05-corrupt-state.py
MUTANT GENERATION: OK (generated=3 drift=0 blocked=0 errors=0)
```

### Check mode

Example shape:

```text
OK F-01 F-01-missing-transition-Open-M2
OK F-02 F-02-transfer-fault-Open-M2
OK F-05 F-05-corrupt-state-Open-UV-M1-dup
MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)
```

### Drift

Example shape:

```text
DRIFT F-02 F-02-transfer-fault-Open-M2 -> src/mutants/mini.F-02-transfer-fault.py
MUTANT GENERATION: FAIL (checked=3 drift=1 blocked=0 errors=0)
```

### Blocked

Example shape:

```text
BLOCKED F-05-corrupt-state-Open-UV-M1-dup projection dup_count undeclared
MUTANT GENERATION: FAIL (checked=3 drift=0 blocked=1 errors=0)
```

## Selftest additions

Add minimal selftest wiring in `tools/selftest/run_selftest.py`:

1. **Green**: `gen_mutant_variants.py --check` passes on golden-mini
2. **Red drift**: tamper one generated variant in a temp copy; `--check` fails with `DRIFT`
3. **Red blocked**: remove the `dup_count` projection declaration in a temp copy; `--check` fails with `BLOCKED`
4. **Red config**: break one `match` block so the generator sees zero exact matches; fail with `CONFIG ERROR`

No new checker is introduced. The selftest only proves the generator can fail red and pass green.

## Integration

### Prompt

Update `prompts/04-testgen.md`:

- keep `fault-mutants.json` as the execution contract
- add a short note that a component may also ship `mutant-generation.json`
- direct maintainers to run:

```bash
python3 tools/gen_mutant_variants.py --check domain-analysis/<component>
```

- state clearly:
  - golden-mini’s `F-01` / `F-02` generation is a fixture bridge
  - this does not change layer ownership

### Roadmap

Update `docs/roadmap.md` item 8 so it no longer says binder-driven generation is deferred in golden-mini.

Recommended status sentence:

> Golden-mini now derives the F-01, F-02, and F-05 fixture variants from component-local bindings. This removes hand-authored drift in the fixture. It does not broaden operator ownership: F-01 and F-02 remain matrix-level families, F-05 remains implementation-level. Broader binder-driven generation and real-component coverage remain pending.

## Non-goals

- no changes to `formats/rules.toml`
- no changes to the `fault-mutants.json` schema
- no changes to `tools/check_fault_mutants.py`
- no changes to `tools/check_matrix_mutation.py`
- no reverse-family work for `ignore/reject → handle`
- no generation for `F-04`
- no generation for classes beyond `F-01`, `F-02`, `F-05`
- no real-component work (`grpc-go addrConn`, `F-08`, clock seam, etc.)
- no general AST mapping
- no release, tag, or push

## Verification

Run, in this order:

```bash
python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
```

Expected:

- generation tool green in write mode and check mode
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)`
- `MUTATION CHECK: OK (killed=9 survived=0 errors=0 blocked=0)`
- `SELFTEST: OK` with generator green/red coverage
- pack consistency green
- tool tests green
- benchmark commands unchanged and green
- no whitespace diff errors

## Completion boundary

A local commit completes this wave.

Success means:

- golden-mini’s three derived variants are generator-owned
- `fault-mutants.json` stays unchanged
- existing mutation checkers stay unchanged
- selftest proves generator red/green behavior

No release. No tag. No push.
