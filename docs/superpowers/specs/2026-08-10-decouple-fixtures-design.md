# Decouple the Fixtures: Generate What We Keep Repairing

**Date:** 2026-08-10
**Scope:** Remove two recurring fixture couplings by generating what is
derivable, instead of documenting the repair in each wave's "known trap"
section.
**Status:** measured; ready to plan.

## Why this spec starts with measurements

The three preceding specs in this series each shipped a criterion that turned
out to be wrong, and each was corrected only when someone tried to execute or
measure it: a changelog surface that must not move, an uncheckable category
match, a two-valued contract that had three forms, a kill-cause rule that
would have failed 3 of 4 legitimate mutants.

The common cause was writing criteria from an idea of the system rather than
from its measured state. So this spec inverts the order. Every claim below was
measured first, at commit `b6130c6`, and the commands are given so a reader can
re-measure rather than trust.

## Measured state

### Coupling 1 — the hand-authored F-04 variant

```bash
diff tests/golden-mini/src/mini.py tests/golden-mini/src/mutants/mini.F-04-sneak-path.py
```

```text
23c23
<             raise RejectedError("M1 rejected in Closed")
>             return "ignored"  # F-04 sneak path: Closed x M1 accepted
```

**One line.** `tools/gen_mutant_variants.py` supports `mode: "replace-block"`
with an exact single-match requirement, which is precisely this shape. No tool
change is needed to generate F-04.

The binder-generation spec excluded F-04 by scope decision, not for a
technical reason. The cost of that decision, measured:

- the previous wave appended an event to `src/mini.py`; F-04 was not carried
  along, and its kill proof went hollow (a pseudo-mutant without the F-04
  mutation scored `KILLED`)
- a region-counting gate was added to detect the drift
- the following wave had to carry an explicit F-04 synchronisation step
- `gen_mutant_variants --check` reports `checked=3` plus
  `UNBOUND F-04-sneak-path-Closed-M1 ... (hand-authored)`

Three of the four fault variants cannot drift, because they are generated. The
fourth has drifted twice.

### Coupling 2 — the inline part-B blind fixtures

`tools/part_b_pack.py:234-244` reports exactly three error kinds:

```text
missing row: <id> (no table row keyed by it)
missing checklist tick: <id>
duplicated checklist entry: <id> (<n>x)
```

`tools/selftest/run_selftest.py` builds four blind tables plus a shared
checklist inline, as literal strings enumerating every catalogue event. They
are validated against the **live** catalogue, so every added event breaks them.

Measured frequency: this has broken in **four consecutive waves**. Each time
it was repaired by hand and the wave's "known trap" section grew. The current
checklist literal enumerates seven ids.

Two of the four fixtures are complete tables — fully derivable from the
catalogue ids. The other two are deliberate single-defect violations of a
complete table:

| fixture | intent | today |
|---|---|---|
| `full` | complete, must pass | complete literal |
| `fine` | finer than one row per id, must pass | complete literal |
| `partial` | one missing row, must fail | literal minus one row |
| `dup` | one duplicated tick, must fail | literal plus one tick |

So the correct structure is: derive the complete table from the catalogue, then
apply a named violation. Nothing about the two red cases requires a literal.

## What this wave changes

### Task A — generate F-04

Add one binding to `tests/golden-mini/domain-analysis/mini/mutant-generation.json`
for `F-04-sneak-path-Closed-M1`, `mode: "replace-block"`, matching the single
`raise RejectedError(...)` line and replacing it with the sneak-path line.

**The proof is byte identity.** The hand-authored file exists today. If the
binding is correct, `gen_mutant_variants --check` reports `drift=0` against the
*unchanged tracked file* — meaning generation reproduces the hand authorship
exactly. That is the same class of evidence that identified the correct sidecar
command (`--root tests/golden-mini` reproducing the committed sidecar
byte-for-byte), and it is stronger than any assertion about intent.

After this, `--check` reports `checked=4` and emits no `UNBOUND` line.

The region-counting gate from the previous wave stays. It becomes redundant for
F-04 but still guards any future hand-authored variant, and removing a working
gate to celebrate a fix would be backwards.

### Task B — derive the part-B fixtures

Replace the four inline literals with one helper that builds a blind table from
the catalogue ids, plus explicit named violations:

```python
def blind_table(ids, *, omit_row=(), omit_tick=(), duplicate_tick=()):
    rows = "\n".join(f"| {i} | ignore (documented) |"
                     for i in ids if i not in omit_row)
    ticks = "\n".join(f"- [x] {i}" for i in ids if i not in omit_tick)
    extra = "".join(f"\n- [x] {i}" for i in duplicate_tick)
    return f"| id | disposition |\n|---|---|\n{rows}\n\n{ticks}{extra}\n"
```

with the ids read from the catalogue's `<!-- event-ids: ... -->` declaration —
the same source `part_b_pack` uses. The four fixtures become:

| fixture | call |
|---|---|
| `full` | `blind_table(ids)` |
| `fine` | finer variant, several situation rows per id |
| `partial` | `blind_table(ids, omit_row={"UV-M1-dup"})` |
| `dup` | `blind_table(ids, duplicate_tick={"M2"})` |

Note `partial` keeps the `UV-M1-dup` tick, so its sole failure is the missing
row — the precision fix the previous wave applied by hand is now structural
rather than remembered.

**The proof is that a new event no longer breaks anything.** The selftest gains
a case that builds a temporary catalogue with one extra event id and asserts
the derived tables grow with it. That test is red against the current literals
and green after the change, and it does not require adding a real event.

## What this wave does not do

- no change to `part_b_pack.py` itself — its three checks are correct
- no removal of the region-counting gate
- no change to `check_fault_mutants.py` or `check_matrix_mutation.py`
- no output contract for cell suites, and therefore no kill-cause gate. The
  measurement that killed the strict version stands and is recorded below;
  the corrected two-part criterion remains a named follow-up.
- no new fault classes, no new UV columns, no real-component work
- no CHANGELOG entry, no version bump, no release, tag, or push

## Recorded for the kill-cause follow-up

Measured at `b6130c6`, so the next attempt does not restart from intuition:

```text
Matrix mutants: 25/25 die at exactly the mutated cell, 0 crashes.

Fault mutants, declared cell -> cells actually reported:
  Closed x M1      -> [Closed×M1]                              single
  Open x M2 (F-01) -> [Closed×M1, Open×M2]                      more
  Open x M2 (F-02) -> [Closed×M1, Open×M2]                      more
  Open x UV-M1-dup -> [Closed×…, Idle×…, Open×UV-M1-dup]         more

Historical hollow case (F-04 before its resynchronisation):
  exit=1, MISMATCH=[Closed×M1], crash=True
```

So a "dies from exactly the declared cell" rule is **wrong**: F-01 breaks the
`Closed` navigation path, and F-05 corrupts a state-independent handler, so
both legitimately break more cells than they declare. The implementation has
about eight branches for 21 cells; a fault is not confined to one cell.

The defensible criterion has two parts: the declared cell must be **among**
those reported, and the suite must have **failed rather than crashed**. Only
the second would have caught the historical case. Neither is checkable without
a machine-readable failure line, because a crash and a failure are
indistinguishable by exit code in Python and in pytest.

## Verification

```bash
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
git diff --check
```

Expected after Task A: `MUTANT GENERATION: OK (checked=4 drift=0 blocked=0
errors=0)` with no `UNBOUND` line, `FAULT MUTANTS: OK (killed=4 ...)`
unchanged, and the tracked F-04 file **unmodified** by regeneration.

Expected after Task B: `SELFTEST: OK` including the new growth case, all four
part-B cases behaving as before, and `MUTATION CHECK: OK (killed=25 ...)`
unchanged.

## Completion boundary

Local commits complete the wave. No release. No tag. No push.
