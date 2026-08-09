# Reverse Matrix Operator Family: `ignore/reject → handle`

**Date:** 2026-08-10
**Scope:** Add one mutation family to `tools/check_matrix_mutation.py`
(Task A), then add one `ignore`-dispositioned UV column to golden-mini so the
family is executed on the shape it exists for (Task B). Keep
`matrix-mutation.json`, `fault-mutants.json`, `check_fault_mutants.py`, and
`tools/gen_mutant_variants.py` unchanged as code.
**Status:** decisions settled 2026-08-10 (see Decisions); ready to plan.

## Goal

The layer-separation spec states the gap:

> Reverse-family note: F-04, F-12, F-15, F-16, F-17, F-20 all need one new
> family in `check_matrix_mutation` — `ignore/reject → handle`. That addition
> is part of the operator work, not of this spec.

Three waves have declared this out of scope. This spec closes the operator
half of it and states, without softening, which fault classes the wave earns
and which it does not.

## The asymmetry today

`build_mutations` (`tools/check_matrix_mutation.py:191`) emits three families:

| Family | Source disposition | Result |
|---|---|---|
| `transition-to-ignore` | `transition →X` | `ignore (documented)` |
| `transition-target-swap` | `transition →X` | `transition →Y` |
| `handle-to-ignore` | `handle` | `ignore (documented)` |

Every family moves *away* from action. Nothing moves *toward* it. A suite that
never drives an ignored or rejected event is invisible to all three: the cell
says "nothing happens", the suite does nothing, and the mutant that also does
nothing passes. That is the F-04 sneak-path shape at matrix level, and it is
exactly the blind spot the reverse family probes.

## The new family

Name: `ignore-to-handle`.

| Source disposition | Replacement |
|---|---|
| `ignore (documented)` | `handle` |
| `reject` | `handle` |

Eligibility is by *decided* disposition only. These are **not** mutated:

- `ignore (accidental)` — a hole. It carries `→ Q-nn`. Mutating an
  undecided cell would assert a semantics nobody approved.
- `UNSPECIFIED` — a hole, same reason.
- `defer (queued)` — excluded. See Decision 1.

### Replacement text

The existing mutators preserve the cell suffix by slicing after the
disposition token. `handle_to_ignore` (`tools/check_matrix_mutation.py:183`)
does this crudely: it turns
`handle (counted) \`mini.py:30\`` into
`ignore (documented) (counted) \`mini.py:30\``. The annotation survives into a
disposition where it means nothing. The suite tolerates it, because it reads
`raw.split("\`")[0].strip()` and then `expected.split()[0]`.

The new family must not copy that wart. It strips the source annotation and
keeps only the citation:

- `ignore (documented) \`mini.py:28\`` → `handle \`mini.py:28\``
- `reject \`mini.py:23\`` → `handle \`mini.py:23\``

The citation is preserved so `apply_mutation`'s drift guard and the matrix
checkers see a well-formed cell.

## What golden-mini yields

The fixture matrix (`disposition-matrix.md:11-13`):

| state | M1 | M2 | UV-M1-dup |
|---|---|---|---|
| Idle | transition →Open | ignore (documented) | handle (counted) |
| Open | ignore (documented) | transition →Closed | handle (counted) |
| Closed | reject | ignore (documented) | handle (counted) |

Four cells are eligible: three `ignore (documented)` plus one `reject`. The
mutant count moves from 9 to 13. Predicted verdicts, with the mechanism that
kills each:

| Cell | Mutant | Suite behaviour | Verdict |
|---|---|---|---|
| Idle × M2 | `handle` | `deliver("M2")` returns `ignored`, not `handled` | KILLED |
| Open × M1 | `handle` | returns `ignored` | KILLED |
| Closed × M2 | `handle` | returns `ignored` | KILLED |
| Closed × M1 | `handle` | raises `RejectedError`; the `handle` branch rejects that | KILLED |

These four verdicts are measured, not predicted. Each cell was mutated by hand
in a temporary copy and the suite was run against it before this spec was
written:

```text
Idle x M2      ignore (documented)  -> handle : KILLED (exit=1)
  MISMATCH Idle × M2: expected handle (counter 0→0), got ignored state=Idle
Open x M1      ignore (documented)  -> handle : KILLED (exit=1)
  MISMATCH Open × M1: expected handle (counter 0→0), got ignored state=Open
Closed x M1    reject               -> handle : KILLED (exit=1)
  MISMATCH Closed × M1: expected handle, got reject
Closed x M2    ignore (documented)  -> handle : KILLED (exit=1)
  MISMATCH Closed × M2: expected handle (counter 0→0), got ignored state=Closed
```

`MUTATION CHECK: OK (killed=13 survived=0 errors=0 blocked=0)` is the expected
line. A survivor is a finding, not a target to adjust.

## The class-credit problem

The reverse family is a precondition for F-12, F-15, F-16, F-17, and F-20. It
is not sufficient, and the roadmap must not claim it is.

Those are undesired-variant classes. Their matrix shape is a UV column whose
cell says the variant is ignored or rejected. Golden-mini has one UV event,
`UV-M1-dup` (`event-catalogue.md:3`), and all three of its cells are
`handle (counted)`. **No eligible cell in golden-mini sits in a UV column.**

So the four Task A mutants exercise the F-04 shape on ordinary events. The
operator's machinery is identical for a UV cell — it never inspects the column
— but the *shape the family exists for* would never have been run. Shipping it
that way would be the hollow-check failure the pack already recorded once.
Task B closes that. See Decision 2.

One further correction to an easy misreading: the registry maps one UV
category to one class (`uv_categories` in `formats/rules.toml` — `loss`→F-12,
`out-of-order`→F-15, `contradiction`→F-16, `commission`→F-17). **One UV column
earns one class, not five.** F-20 is not a UV category at all; its shape is
blocked progress after a terminal event. Any wording that implies one column
settles the group is false.

## Decisions

The owner delegated both open questions on 2026-08-10 with the instruction to
weigh long-term quality over speed. Both are recorded here with the evidence
that settled them, not with a preference.

### Decision 1: `defer (queued)` is excluded from the family

The deciding fact is mechanical, not aesthetic: **no fixture can execute the
branch.**

- `tests/golden-mini/domain-analysis/mini/matrix-mutation.json` is the only
  mutation config in the repository, so golden-mini is the only place
  `check_matrix_mutation.py` ever runs.
- Golden-mini has zero `defer` cells.
- The one fixture that *does* carry a `defer (queued)` cell
  (`tools/selftest/compound/.../disposition-matrix.md:17`) has no cell suite
  and no mutation config. The checker never runs there.
- Worse, the golden-mini suite cannot represent a defer cell at all.
  `check()` in `tests/test_cell_suite.py` derives `kind` from the first token
  and has no `defer` branch, so it returns `unknown disposition`. A defer cell
  added today would fail the **baseline**, and the checker would stop at
  `BLOCKED: baseline exit=1` before reaching any mutant.

So adding `defer` eligibility now would ship an operator branch that nothing
exercises and nothing could exercise. That is the vacuous-green shape in §6 of
`AGENTS.md`, written into a new mechanism on purpose. The semantic argument
points the same way: a deferred event is queued and re-delivered, so its
adversaries are "the queue drops it" and "it fires now instead of later".
Neither is `handle`. `defer → handle` would smuggle a timing claim in under a
disposition family's name.

**Trigger to revisit, so this does not rot into silence:** the first time a
component with a `defer` cell declares a `matrix-mutation.json`, deferral gets
its own family with its own semantics (`defer → handle` *and* `defer →
ignore`, as a pair), and the suite contract grows a defer branch first. That
precondition — suite before operator — is the same order this wave uses.

### Decision 2: one wave, two ordered tasks, two commits

Neither pure option was right, and the deciding evidence is on both sides.

Against splitting into two waves: the reverse family has been deferred three
times. `AGENTS.md` §6 records the pattern directly — *"every tool change
shipped without a simultaneous gate arrived defective but green; every change
built together with its red case held on first contact."* A family whose
intended shape is never run is exactly a change without its gate.

Against merging into one undifferentiated task: adding a UV column moves the
mutant count for a second, independent reason in the same commit. A red gate
would then be ambiguous about which change caused it.

So: **one wave, two tasks, each independently gated and separately committed.**

- **Task A — the operator.** Family plus red probes. Count moves 9 → 13. No
  fixture change.
- **Task B — one UV column.** Adds `UV-M2-stale` (out-of-order/stale arrival)
  to golden-mini, dispositioned `ignore (documented)` in all three states.
  Count moves 13 → 16. The family is now executed on the shape it exists for,
  and **F-15 alone** is claimed with fixture proof.

Task B is not optional and not deferrable out of this wave. If it is dropped,
Task A must be dropped with it, because Task A alone ships an unexercised
purpose.

**What is still not earned after Task B, and why.** F-12 (loss), F-16
(contradiction), and F-17 (commission) each need their own UV column, because
the registry maps one category to one class. F-20 needs a terminal-event
progress shape, which is not a UV column at all. These stay unclaimed, named,
with the reason recorded in roadmap item 8. Claiming them from one column
would be the shortcut this decision exists to refuse.

### Bonus proof Task B produces for free

Adding an event to `src/mini.py` shifts every line the three generated variant
files copy. Task B therefore re-runs `tools/gen_mutant_variants.py` and the
regenerated variants must differ. That is the first real exercise of last
wave's binder generation: without it, the same edit would have meant three
hand-edited variant files and a likely drift. `--check` proving `drift=0`
afterwards is the evidence that the regeneration was complete.

## Selftest additions

`tools/selftest/run_selftest.py`, section "matrix checker (markdown side)".
Each mechanism gets an observed failure before it is trusted (R-RED-PROBE).

**Task A:**

1. **Green, counted:** `mutation(gm)` passes and the summary carries
   `killed=13`. The existing case asserts only `MUTATION CHECK: OK`, so the
   family could be dropped entirely and that case would stay green. The count
   assertion is what makes the family's absence red.
2. **Red, weak suite:** the existing always-exit-0 mirroring config must
   report a `SURVIVED` line whose `kind=ignore-to-handle`. The current weak
   case proves survival for some family; this pins it to the new one.
3. **Red, hole not mutated:** a temp copy whose `Open × M1` cell reads
   `ignore (accidental) → Q-01` must produce no `ignore-to-handle` mutant for
   that cell. Asserted as a count drop, not as absence of a substring.
4. **Red, annotation not carried:** no generated mutant text may contain
   `handle (documented)`. This pins the wart fix from the replacement-text
   section.

**Task B:**

5. **Green, recounted:** `killed=16`, and the Task A assertion moves with it.
   Two surfaces state this number and both change in Task B's commit.
6. **Red, UV cell specifically:** the weak-suite case must report a
   `SURVIVED` line for a `UV-M2-stale` cell. This is the assertion that the
   family runs on the shape it was built for. Task A cannot make it pass.
7. **Generator drift:** `gen_mutant_variants.py --check` reports `drift=0`
   after the variants are regenerated against the new `src/mini.py`.

## Surfaces that move, per task

R-REMEASURE: every surface that states a number or the family list moves in
the commit that changes it.

**Task A:**

- `tools/check_matrix_mutation.py` — the family.
- `tools/selftest/run_selftest.py` — cases 1–4, including `killed=13`.
- `docs/roadmap.md` item 7 — the family list currently reads
  "transition-to-ignore, transition target-swap, and handle-to-ignore".
- `CHANGELOG.md` — the family list appears there too.

**Task B:**

- `tests/golden-mini/src/mini.py` — the `UV-M2-stale` branch.
- `tests/golden-mini/domain-analysis/mini/disposition-matrix.md` — the column.
- `tests/golden-mini/domain-analysis/mini/event-catalogue.md` — the
  `event-ids` comment, the event row, and M2's `out-of-order` coverage entry,
  which stops being `n/a: sync` and names the new event.
- `tests/golden-mini/tests/test_cell_suite.py` — `EVENTS`, and `NAVIGATE` if
  the new cells need driving.
- `tests/golden-mini/domain-analysis/mini/analysis.json`,
  `manifest.json`, and `tests/golden-mini/expected/analysis.json` —
  regenerated, not hand-edited.
- the three generated variant files — regenerated by
  `tools/gen_mutant_variants.py`.
- `tools/selftest/run_selftest.py` — cases 5–7, and `killed=13` → `killed=16`.
- `docs/roadmap.md` item 8 — F-15 claimed with fixture proof; F-12, F-16,
  F-17, F-20 named as still unclaimed, each with its reason.
- `CHANGELOG.md`.

`prompts/04-testgen.md` enumerates dispositions but not families, so it moves
only if Task B changes disposition guidance. It should not.

Dated plan files under `docs/superpowers/plans/` record what was true at the
time. They are not rewritten.

## Non-goals

- no change to `matrix-mutation.json` or its schema
- no change to `fault-mutants.json`, `check_fault_mutants.py`, or
  `gen_mutant_variants.py` (Task B re-runs the generator; it does not edit it)
- no new fault-class mutants
- no second, third, or fourth UV column (F-12, F-16, F-17 stay unclaimed)
- no terminal-progress shape for F-20
- no `defer` family (Decision 1, with a recorded trigger)
- no real-component work
- no release, tag, or push

## Verification

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
```

Expected after Task A:

- `MUTATION CHECK: OK (killed=13 survived=0 errors=0 blocked=0)`
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)` — unchanged
- `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)` — unchanged
- `SELFTEST: OK` with cases 1–4

Expected after Task B:

- `MUTATION CHECK: OK (killed=16 survived=0 errors=0 blocked=0)`
- `FAULT MUTANTS: OK (killed=4 survived=0 errors=0 blocked=0)` — still four
  classes, against regenerated variants
- `MUTANT GENERATION: OK (checked=3 drift=0 blocked=0 errors=0)` — after
  regeneration
- `SELFTEST: OK` with cases 1–7
- pack consistency, tool tests, and benchmarks green; the golden sidecar
  (`tests/golden-mini/expected/analysis.json`) and `manifest.json` regenerated

A survivor at either step stops the wave and is reported. It is never resolved
by adjusting the suite or the count.

## Completion boundary

A local commit completes the wave. No release. No tag. No push.
