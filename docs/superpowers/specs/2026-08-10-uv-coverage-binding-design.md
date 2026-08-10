# UV Coverage Binding + the Remaining Matrix-Level UV Classes

**Date:** 2026-08-10
**Scope:** Add a checker rule that binds every UV column to its base event's
coverage entry (Task A), then add the three missing matrix-level UV columns
so `F-12`, `F-16`, and `F-17` are claimed with fixture proof (Task B).
**Status:** decisions settled; ready to plan.

## The defect that motivates Task A

Golden-mini's sidecar says, at `analysis.json` `coverage`:

```json
"M1": { "duplication": "n/a: sync", ... }
"M2": { "out-of-order": "UV-M2-stale", ... }
```

`M1.duplication` asserts that duplication cannot occur, *while the matrix
carries a `UV-M1-dup` column that exists for exactly that category*. Both
statements cannot be true. This survived because `tools/dsc_check.py` only
requires each coverage entry to be **non-empty** — `"n/a: sync"` satisfies it
as readily as a variant id.

Two failure directions are currently invisible:

1. **Unbound column** — a UV column exists, but no coverage entry names it.
   The catalogue claims a variant is handled; the coverage table claims the
   category is out of scope. This is golden-mini's live state for
   `UV-M1-dup`.
2. **Phantom binding** — a coverage entry names a variant id that has no
   matrix column. The analysis claims coverage it does not have.

The second is the more dangerous of the two: it is an unearned coverage
claim, which is the failure class this pack exists to prevent.

## Task A: reject phantom coverage bindings

> **Corrected after the first planning attempt.** The original version of
> this section specified a two-directional rule and a category match. A
> read-only survey by the planning agent, reproduced and measured, showed
> both were wrong. The measurements are recorded below because they are the
> reason for the narrower contract, and because the next wave needs them.

### What was wrong

1. **The category match is not mechanically checkable.** The section asked
   that a variant sit "in a category whose registry `fault` matches the class
   the variant stands for", while also forbidding name-derived inference.
   `formats/analysis.schema.json` gives an event only `id` and `undesired`;
   nothing records which UV category a variant belongs to. Those two
   requirements contradict each other. Dropped.
2. **The contract recognised two value forms; there are three.** Real
   coverage values include prose that asserts applicability without naming a
   variant, e.g. `examples/device-connection/.../run1`:
   `connect/loss = "applicable — async call may be dropped by the transport"`.
   Treating every non-`n/a:` value as a variant id would flag 12 such entries
   per run as phantom bindings. That is a defect in the rule, not the data.
3. **The blast radius was never measured.** The rule lands in
   `tools/dsc_check.py`, which is global, while the spec budgeted only
   golden-mini.

### Measured, at commit 42bbec5

| direction | violations | artifacts |
|---|---|---|
| phantom (coverage names a UV id that is not an event) | **0** | — |
| unbound (a UV event no coverage entry names) | **41** | 13 |

The newer analyses (`silenceper-pool-32`, `meilisearch-6510`,
`meilisearch-s3-snapshot`) bind cleanly; the older ones do not. The practice
improved and the old artifacts were never migrated.

### The rule this wave ships

Phantom direction only:

> Every `UV-`-prefixed token appearing in a coverage value must name an event
> that exists in `events`.

Three value forms stay legal: `n/a: <reason>`, one or more variant ids, and
prose that names no variant. Only a token that *looks like a variant
reference* is resolved.

Error string, following the style at `dsc_check.py:194-202`:

```
UV binding: coverage <base>/<cat> names <id>, which is not an event
```

This catches the more dangerous direction — an unearned coverage claim,
where the analysis asserts a variant it does not carry.

**Red probe must be constructed, not found.** There are 0 phantom violations
today, so the plan must build one in a temp copy (a coverage value naming an
invented id such as `UV-does-not-exist`), observe the exact error, and only
then trust the rule.

### The unbound direction is explicitly deferred

41 violations across 13 artifacts, including 14 per device-connection run,
plus the two selftest fixtures. That is a migration wave with its own
measured red probe — the same shape as the fault-registry migration and its
44-error probe. It is **not** folded in here.

**Honest consequence:** Task A therefore protects Task B only from the
coverage side. If Task B added a UV column and bound nothing, no checker
would object. The plan must make binding an explicit, separately verified
step for each new column rather than relying on a gate.

## Task B: the three remaining matrix-level UV columns

`formats/rules.toml` binds one UV category to one class. Of the four
matrix-level ones, `out-of-order` → F-15 landed in v1.51. Three remain:

| category | class | new event | base | disposition |
|---|---|---|---|---|
| `loss` | F-12 | `UV-M1-lost` | M1 | `ignore (documented)` |
| `contradiction` | F-16 | `UV-M2-conflict` | M2 | `ignore (documented)` |
| `commission` | F-17 | `UV-M1-spurious` | M1 | `reject` |

### Why `UV-M1-spurious` is `reject` and not `ignore`

Two reasons, and the second is the operative one.

Semantically, a spontaneous commission is an event with no legitimate
trigger; refusing it is the more faithful disposition, and silently ignoring
it would model a component that cannot tell a spurious call from a real one.

Mechanically, it is the coverage that matters: the reverse family accepts
both `ignore (documented)` and `reject`, but golden-mini's only `reject` cell
is `Closed × M1`, an ordinary event. After this wave the family will be
exercised on a `reject` cell **in a UV column** as well. Making all three new
columns `ignore` would add nine mutants of a shape already proven three times
over and would leave `reject`-on-a-UV-cell untested.

### Counts

Nine new cells, all eligible for `ignore-to-handle`. No other family applies
to `ignore` or `reject` cells. So:

- `MUTATION CHECK: OK (killed=25 ...)`, up from 16
- `ignore-to-handle` mutants: 16, up from 7
- matrix becomes 3 states × 7 events = 21 cells
- the abstraction statement moves from `four-event` to `seven-event`

These are derived, not measured — the columns do not exist yet. The plan must
mark them as such and the executor must report the real numbers.

### What this earns, and what it does not

After Task B, roadmap item 8 may claim **F-12, F-16, F-17** in addition to
F-15, all with fixture proof. That is every matrix-level UV class.

It does **not** earn:

- **F-20** — blocked progress after a terminal event. Not a UV category at
  all; it needs a progress shape, not a column.
- **F-13, F-14, F-18** — `delay`, `duplication`, `value` are
  implementation-level per the registry. A UV column does not operationalise
  them; they need implementation mutants. Note that `UV-M1-dup` already
  exists as a column and F-14 is still *not* claimed — the column is the
  matrix-side shape, the class needs the implementation side. Task A's
  binding rule makes that distinction visible rather than blurring it.

## Ordering

Task A ships first, but the original justification for that no longer holds
and is withdrawn: with only the phantom direction enforced, the checker does
**not** turn a forgotten binding red. Task A still goes first because Task B
writes three new coverage bindings, and the phantom rule verifies that each
one resolves to an event that actually exists — which catches a typo'd or
misspelled variant id at the moment it is introduced.

Golden-mini's `M1.duplication` defect (`"n/a: sync"` while a `UV-M1-dup`
column exists) moves to **Task B**, where the coverage bindings are edited
anyway. It is a data correction, not a red probe for the shipped rule.

## Known trap, inherited from the last wave

Adding catalogue events breaks four inline part-B blind fixtures in
`tools/selftest/run_selftest.py` (the four blind tables plus the shared
checklist), because they are validated against the live catalogue. Three new
events means three new rows and three new ticks in each. This cost the last
wave a mid-flight stop; the plan must carry it as an explicit step.

Likewise: the sidecar is regenerated with `--root tests/golden-mini`, never
`--root .`, and `dsc_check` runs with `--repo tests/golden-mini`.

## Non-goals

- no name-derived category inference in the binding rule
- no unbound-direction rule, and no migration of the 41 unbound variants
  across 13 artifacts — named as the next wave, with the count measured here
- no UV-category metadata in the schema (the prerequisite for ever checking
  a category match)
- no F-20 progress shape
- no implementation-level classes (F-13, F-14, F-18)
- no `defer` family — its recorded trigger has not occurred
- no `handle_to_ignore` annotation-wart fix (separate, named follow-up)
- no CHANGELOG entry or version bump inside the wave
- no release, tag, or push

## Verification

```bash
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
git diff --check
```

Expected after Task A: `DSC CHECK: OK`, with the new rule proven red first
against `UV-M1-dup`, and `MUTATION CHECK` unchanged at `killed=16`.

Expected after Task B: `DSC CHECK: OK (3 states x 7 events, 21 cells, ...)`,
`MUTATION CHECK: OK (killed=25 ...)`, `FAULT MUTANTS: OK (killed=4 ...)`
against regenerated variants, `MUTANT GENERATION: OK (checked=3 drift=0 ...)`.

A survivor at either step stops the wave and is reported.

## Completion boundary

Local commits complete the wave. No release. No tag. No push.
