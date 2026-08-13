# Structural Unreachability Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax. Tick each box in the same work session as the action it records; never reconstruct state from memory.

**Goal:** Give golden-mini a structurally unreachable cell expressed through the existing upstream-guard mechanism, then record the doctrine.

**Architecture:** Task A adds one internal event `svc-ack` with three different dispositions across its column — `reject` in `Idle` (unreachable by upstream guarantee), `handle` in `Open`, `ignore (documented)` in `Closed`. Task B writes the doctrine into `prompts/02-pilot.md` and adds the machine-readable-rationale roadmap item. The two tasks are independent after Task A commits and are meant for separate workers.

**Tech stack:** Python 3 stdlib, golden-mini fixture, existing checkers, `uv` for dev dependencies.

## Global constraints

- Do **not** add a disposition to `formats/rules.toml`. The wave's whole point is that unreachability is not a disposition.
- Do **not** add a rationale field to the sidecar schema. Named roadmap item, out of scope.
- Do **not** write a checker that greps prose for "unreachable" or similar. Heuristic of the kind forbidden for UV categories.
- Do **not** change `check_fault_mutants.py`, `check_matrix_mutation.py`, `part_b_pack.py`, `gen_mutant_variants.py`, or `dsc_check.py`.
- Do **not** touch the other four artifacts that used workarounds (`meilisearch-*`, `valkey-glide-*`, `grpc-go-*`).
- Sidecar only via `uv run --with jsonschema python3 tools/gen_analysis_sidecar.py --root tests/golden-mini`. Never `--root .`.
- `dsc_check` only with `--repo tests/golden-mini`. Never `--repo .`.
- `expected/analysis.json` only refreshed by `cp`. Never hand-edit either JSON.
- Use `rc=$?; test "$rc" -eq N` assertions, never bare `echo "exit=$?"`.
- No push, tag, release, CHANGELOG edit, or version bump.

## Derived values — measure, do not assume

`MUTATION CHECK` is `killed=25` today. Three new cells are added: one `reject`, one `handle`, one `ignore (documented)`. Expected new mutants: `ignore-to-handle` on the reject cell, `handle-to-ignore` on the handle cell, `ignore-to-handle` on the ignore cell — so **`killed=28` is the derived target, unverified at plan time**. `FAULT MUTANTS` should stay `killed=6`; `MUTANT GENERATION` stays `checked=6` but the variants change because `src/mini.py` grows.

Any mismatch is `BLOCKED(task-A): derived count mismatch`, reported with the real numbers. Never edit an assertion or expected value to force green.

## Start gate

```bash
cd /Users/gregormelhorn/workspace/domain-statechart
git status --short && echo "TREE CLEAN"
git merge-base --is-ancestor 71a995e HEAD && echo "SPEC PRESENT"
```

Expected: `TREE CLEAN` with no file lines above it, and `SPEC PRESENT`. If the tree is dirty, stop and report `BLOCKED(start-gate): working tree not clean`.

---

### Task A: Add the `svc-ack` internal event

**Files:**
- Modify: `tests/golden-mini/src/mini.py` (append before the final `raise ValueError(event)`)
- Modify: `tests/golden-mini/domain-analysis/mini/disposition-matrix.md`
- Modify: `tests/golden-mini/domain-analysis/mini/event-catalogue.md`
- Modify: `tests/golden-mini/tests/test_cell_suite.py` (`EVENTS` only)
- Regenerate: `analysis.json`, `expected/analysis.json`, the six mutant variants
- Modify: `tools/selftest/run_selftest.py` (counts only, after measuring)

- [x] **Step 1: Add the implementation**

In `tests/golden-mini/src/mini.py`, replace this exact block:

```python
        if event == "UV-M1-spurious":
            raise RejectedError("UV-M1-spurious rejected")
        raise ValueError(event)
```

with:

```python
        if event == "UV-M1-spurious":
            raise RejectedError("UV-M1-spurious rejected")
        if event == "svc-ack":
            if self.state == "Idle":
                # Structurally unreachable: the service only acknowledges a
                # delivered M1, so no ack can exist here. Rejecting makes a
                # breach of that upstream guarantee loud instead of silent.
                raise RejectedError("svc-ack without a delivered M1")
            if self.state == "Open":
                self.dup_count += 1
                return "handled"
            return "ignored"
        raise ValueError(event)
```

Appending keeps every existing citation line stable. Verify:

```bash
sed -n '38,50p' tests/golden-mini/src/mini.py
```

Expected: the new branch occupies lines 40-49 and `raise ValueError(event)` is line 50.
The implementing lines — the ones the matrix cites — are **45** (reject), **47**
(handle) and **49** (ignore). The three comment lines are part of the branch and
are counted; an earlier draft of this plan forgot them and cited 42/44/46, which
would have pointed the matrix at comment text.

- [x] **Step 2: Add the matrix column and fix the abstraction count**

In `disposition-matrix.md`, replace `to the seven-event catalogue.` with `to the eight-event catalogue.`

Then replace the header and separator rows:

```
| state | M1 | M2 | UV-M1-dup | UV-M2-stale | UV-M1-lost | UV-M2-conflict | UV-M1-spurious |
|---|---|---|---|---|---|---|---|
```

with:

```
| state | M1 | M2 | UV-M1-dup | UV-M2-stale | UV-M1-lost | UV-M2-conflict | UV-M1-spurious | svc-ack |
|---|---|---|---|---|---|---|---|---|
```

Then append one cell to each of the three state rows, before the trailing `|`:

- `**Idle**` row: ` reject \`mini.py:45\` |`
- `**Open**` row: ` handle (counted) \`mini.py:47\` |`
- `**Closed**` row: ` ignore (documented) \`mini.py:49\` |`

- [x] **Step 3: Declare the event in the catalogue**

Replace the `event-ids` comment:

```
<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious -->
```

with:

```
<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious svc-ack -->
```

Add this row to the events table, after the `UV-M1-spurious` row:

```
| svc-ack | service acknowledges the open | svc | internal | id | svc | op |
```

Add this annotation block after the `### M2` block. **`svc-ack` is not a UV event, so it needs `gate`, `upstream_guards`, and all seven coverage categories** — `dsc_check` enforces this:

```
### svc-ack
- gate: correlation id matches a delivered M1
- upstream_guards: the service emits an ack only in response to a delivered M1; an ack without one cannot reach this boundary
- coverage:
  - loss: n/a: local
  - delay: n/a: sync
  - duplication: n/a: sync
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: n/a: sync
  - value: n/a: correlation id checked
```

- [x] **Step 4: Add the event to the cell suite**

In `tests/golden-mini/tests/test_cell_suite.py`, replace:

```python
EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale", "UV-M1-lost", "UV-M2-conflict", "UV-M1-spurious"]
```

with:

```python
EVENTS = ["M1", "M2", "UV-M1-dup", "UV-M2-stale", "UV-M1-lost", "UV-M2-conflict",
          "UV-M1-spurious", "svc-ack"]
```

`EVENTS` order must match the matrix column order — `zip(..., strict=True)` couples them. Leave `NAVIGATE` unchanged.

- [x] **Step 5: Run the cell suite directly**

```bash
( cd tests/golden-mini && python3 tests/test_cell_suite.py domain-analysis/mini ); rc=$?
echo "exit=$rc"; test "$rc" -eq 0 && echo "ASSERT OK" || echo "ASSERT FAILED"
```

Expected: `CELL SUITE: 24 cells checked, 0 failed`, then `CELL SUITE: OK`, `exit=0`, `ASSERT OK`.

A failure here means a disposition and the implementation disagree — report it, do not adjust either to match.

- [x] **Step 6: Regenerate the sidecar and refresh the golden copy**

```bash
uv run --with jsonschema python3 tools/gen_analysis_sidecar.py --root tests/golden-mini
cp tests/golden-mini/domain-analysis/mini/analysis.json tests/golden-mini/expected/analysis.json
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini; rc=$?
echo "exit=$rc"; test "$rc" -eq 0 && echo "ASSERT OK" || echo "ASSERT FAILED"
```

Expected: `DSC CHECK: OK (3 states x 8 events, 24 cells, 0 guard groups)`.

If it reds on `R-GATE-TYPE`, `R-UPSTREAM-GUARD`, or UV coverage, Step 3 is incomplete — fix Step 3, never the JSON.

- [x] **Step 7: Prove the variants are stale, then regenerate**

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini; rc=$?
echo "exit=$rc"; test "$rc" -eq 1 && echo "ASSERT RED AS REQUIRED" || echo "ASSERT FAILED: expected drift"
```

Expected: six `DRIFT` lines and `exit=1`. **Paste this.** Then:

```bash
python3 tools/gen_mutant_variants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
```

Expected: `MUTANT GENERATION: OK (checked=6 drift=0 blocked=0 errors=0)`.

- [x] **Step 8: Measure the new mutation count**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini | tail -1
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini | grep 'event=svc-ack'
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini | tail -1
```

Expected: `FAULT MUTANTS: OK (killed=6 ...)` unchanged, three lines with `event=svc-ack` all `KILLED`, and a `MUTATION CHECK` summary. The derived target is `killed=28`; **if the real number differs, stop and report `BLOCKED(task-A): derived count mismatch` with the actual output.** Do not adjust anything to reach 28.

- [x] **Step 9: Confirm the part-B fixtures grew by themselves**

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1 | grep -E 'blind table|grows with catalogue'
```

Expected: all part-B cases still behave as before, with no manual fixture edit. They were derived from the catalogue in v1.52; this is the first added event since, so it is the first wave that should need **no** part-B repair step. If a part-B case fails, that is a finding about the derivation — report it.

- [x] **Step 10: Update the selftest counts to the measured values**

Update the matrix-mutation count assertion in `tools/selftest/run_selftest.py` from `killed=25` to the number measured in Step 8, including its failure message and its `ok` print. Change nothing else.

Then:

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1 | tail -1
```

Expected: `SELFTEST: OK`.

- [x] **Step 11: Run the full gate**

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini | tail -1
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini | tail -1
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini | tail -1
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini | tail -1
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py 2>&1 | tail -1
python3 tools/check_pack_consistency.py 2>&1 | tail -1
python3 tools/run_tool_tests.py 2>&1 | tail -1
python3 tools/run_benchmark.py 2>&1 | tail -1
uv run --with jsonschema python3 tools/check_reachability.py tests/golden-mini/domain-analysis/mini | tail -1
git diff --check && echo "diff-check clean"
git status --short
```

Expected: all green, `2/2 cases pass`, `6 passed, 0 failed`, `REACHABILITY CHECK: OK`, `diff-check clean`, and `git status --short` listing only the intended files.

- [x] **Step 12: Tick Task-A checkboxes and commit**

Tick with line-anchored matching — a substring replacer fails because these titles also appear inside this block:

```python
from pathlib import Path
path = Path("docs/superpowers/plans/2026-08-12-structural-unreachability.md")
lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
start = next(i for i, l in enumerate(lines) if l.startswith("### Task A"))
end = next(i for i, l in enumerate(lines) if l.startswith("### Task B"))
ticked = 0
for i in range(start, end):
    if lines[i].startswith("- [ ] **Step"):
        lines[i] = lines[i].replace("- [ ] **Step", "- [x] **Step", 1)
        ticked += 1
if ticked != 12:
    raise SystemExit(f"expected 12 Task-A checkboxes, ticked {ticked}")
path.write_text("".join(lines), encoding="utf-8")
print(f"TASK A CHECKBOXES: OK ({ticked}/12)")
```

```bash
git add tests/golden-mini/src/mini.py \
  tests/golden-mini/domain-analysis/mini/disposition-matrix.md \
  tests/golden-mini/domain-analysis/mini/event-catalogue.md \
  tests/golden-mini/domain-analysis/mini/analysis.json \
  tests/golden-mini/expected/analysis.json \
  tests/golden-mini/tests/test_cell_suite.py \
  tests/golden-mini/src/mutants/ \
  tools/selftest/run_selftest.py \
  docs/superpowers/plans/2026-08-12-structural-unreachability.md
git commit -m "Add svc-ack: a structurally unreachable cell held by an upstream guarantee" \
  -m "Paste the measured evidence here: the cell-suite line, DSC CHECK, the drift
proof, the three event=svc-ack mutant lines, and every gate summary."
```

---

### Task B: Record the doctrine

**Files:**
- Modify: `prompts/02-pilot.md` (next to the upstream-guard instruction)
- Modify: `docs/roadmap.md`

Independent of Task A's fixture work; run it in a separate worker after Task A commits.

- [ ] **Step 1: Write the rule into the pilot prompt**

In `prompts/02-pilot.md`, find the paragraph beginning `**Upstream-guard annotation.**` and append this to it:

```
When an upstream guarantee makes a (state, event) cell structurally
unreachable, do not invent a "cannot happen" disposition and do not leave the
cell on `ignore`. Keep a defensive disposition — prefer `reject` — and name the
guarantee in the upstream-guard annotation. The disposition covers the breach;
the annotation explains why it should never occur. An ignored breach is a
silent breach, and unreachability is a property of the environment, not a
behaviour of the component.
```

- [ ] **Step 2: Add the roadmap item**

In `docs/roadmap.md`, add a new item after the last numbered one:

```markdown
## 10. Machine-readable cell rationale

**Status:** Planned. Measured at v1.52: 339 `ignore (documented)` cells across
all sidecars, **0** carrying a machine-readable rationale. Every justification
lives in matrix cell prose, where no checker reaches it — so "ignored because
harmless" and "ignored because it cannot occur" are indistinguishable to any
tool. Structural unreachability is expressed today through a defensive
disposition plus the upstream-guard annotation (see `prompts/02-pilot.md`);
a rationale field would let a checker verify that such a claim cites its
guarantee. Building that checker first would mean matching prose for words like
"unreachable" — the kind of heuristic this pack forbids for UV categories, so
the field comes first.
```

- [ ] **Step 3: Verify and commit**

```bash
python3 tools/check_pack_consistency.py 2>&1 | tail -1
git diff --check && echo "diff-check clean"
git status --short
```

Expected: `PACK CONSISTENCY: OK`, clean diff-check, only the two files listed.

Tick the Task-B checkboxes with the same line-anchored script, scoped from `### Task B` to the end of the file, expecting 3. Then commit both files with an evidence block.

---

## Completion boundary

Local commits complete the wave. No release. No tag. No push.
