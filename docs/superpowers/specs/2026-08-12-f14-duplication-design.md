# F-14 Duplication: Deliver Duplicates Twice, Then Claim the Class

**Date:** 2026-08-12
**Scope:** Make the golden-mini cell suite deliver duplication variants twice,
as the pack's own doctrine already requires, then operationalise `F-14`.
**Status:** measured; ready to plan.

## Measured state, at commit `7148e05`

### A real F-14 fault survives the suite today

This is the finding the wave rests on. A duplication mutant whose *second*
delivery escalates state — invisible on a single delivery — was run against the
current suite:

```text
CELL SUITE: 21 cells checked, 0 failed
exit=0                                    -> SURVIVED
```

All 21 cells pass. The same implementation, with the event delivered twice:

```text
Basis        Idle -> Idle,   dup_count=2, idempotent=True
F-14-Mutant  Idle -> Closed, dup_count=2, idempotent=False
```

The mutant is:

```python
        if event == "UV-M1-dup":
            self.dup_count += 1
            if self.dup_count >= 2:  # F-14 duplication: repeat is not idempotent
                self.state = "Closed"
            return "handled"
```

Per `AGENTS.md`, a surviving mutant is a suite finding. This one is not
hypothetical and not a doctrine argument — it is a measured blind spot.

### The suite contradicts the pack's own instruction

```text
prompts/04-testgen.md:44   "Deliver undesired variants concretely:
                            duplication = deliver twice; ..."

test_cell_suite.py         m.deliver(event)     - exactly one occurrence
```

Golden-mini is the reference every future component copies, and it does not
follow the rule the same repository publishes.

### Why F-14 differs from F-05, which was cheap

```text
F-05  binder "corrupt-state"   precondition "counter or context variable
                                             projected by the suite"
F-14  binder MISSING           precondition "idempotence observable via
      shard "commission (repeat)"            repeated delivery plus counter"
```

F-05 needed only a projection, which existed. F-14 additionally needs a
**delivery rule**. Without repeated delivery, idempotence is unobservable by
definition, and an "F-14 mutant" would just be a second F-05 under another
name — an overclaim.

`formats/rules.toml` has no `binder` for F-14, so this wave must add one.
Earlier waves forbade touching that file; here it is the point.

### How the suite learns which event is a duplicate

Not from the name — name-derived inference is explicitly forbidden by the
UV-binding spec. From the coverage binding:

```json
"M1": { "duplication": "UV-M1-dup", ... }
```

That binding was repaired two waves ago for an unrelated reason: it read
`"n/a: sync"` while a `UV-M1-dup` column existed. It now becomes the data
source for the delivery rule.

## Task A: deliver duplication variants twice

The suite reads the sidecar's `coverage` map, collects every variant id bound
to the `duplication` category, and delivers those events twice in the act step.
Everything else keeps single delivery.

The `handle` assertion must follow: for a duplication variant the counter moves
by **two**, not one, and the state must be unchanged after *both* deliveries.
That second half is the part that catches F-14.

**Derived, unverified at spec time:** whether any existing count moves. The
`handle` cells for `UV-M1-dup` change their expected counter, so
`MUTATION CHECK` and `FAULT MUTANTS` must be re-measured by the executor rather
than assumed. F-05 should stay killable — it corrupts the counter by the wrong
amount, which a doubled expectation does not mask — but that is a prediction,
not a measurement.

## Task B: operationalise F-14

- add `binder = "duplication"` to the F-14 entry in `formats/rules.toml`
- add the variant above, generated through `mutant-generation.json` — it is a
  plain `replace-block`, so no generator change is needed
- declare it in `fault-mutants.json` as cell `Idle x UV-M1-dup`, which keeps it
  distinct from F-05's `Open x UV-M1-dup`
- expected: `FAULT MUTANTS` moves from `killed=4` to `killed=5`

The cell-failure contract from v1.52 applies: the kill must report the declared
cell among its `CELL FAIL` lines, so this class is cause-checked from birth
rather than exit-code-correlated.

### The red probe is already measured

Task B's mutant **must** survive before Task A and be killed after. That single
observation proves both tasks at once: it shows the blind spot is real, and it
shows the delivery rule closes it. The executor must observe both states.

## What this wave does not claim

- **F-13 (delay) and F-18 (value)** stay unclaimed. They are implementation
  level too, but delay needs clock injection and value needs payload-effect
  projection. Neither is a delivery rule.
- **F-20** still needs a terminal-progress shape.
- No other undesired-variant category gains a delivery rule. `stale` and
  `commission` have their own doctrine lines in `prompts/04-testgen.md:44`
  (`stale = deliver after the state moved on`), and golden-mini's stale column
  may or may not satisfy them. That is a separate measurement, deliberately not
  bundled here.

## Non-goals

- no change to `check_fault_mutants.py`, `check_matrix_mutation.py`,
  `part_b_pack.py`, or `gen_mutant_variants.py`
- no new UV columns
- no name-derived category inference
- no CHANGELOG entry or version bump inside the wave
- no release, tag, or push

## Verification

```bash
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
git diff --check
```

Expected after Task B: `FAULT MUTANTS: OK (killed=5 survived=0 errors=0
blocked=0)`, with the F-14 kill naming `Idle x UV-M1-dup`. All other measured
values re-reported rather than assumed; a mismatch is
`BLOCKED(<task>): derived count mismatch`.

## Completion boundary

Local commits complete the wave. No release. No tag. No push.
