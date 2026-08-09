# ACH Fault-Class Expansion Design — F-01, F-02, F-05

**Date:** 2026-08-09
**Scope:** Add three hand-authored implementation mutants to the golden-mini
fault-mutant fixture, expanding coverage from one fault class to four with
zero contract changes.

## Goal

Prove that the `fault-mutants.json` contract, `check_fault_mutants.py`, and
the behavioral cell suite generalize across multiple fault classes and
multiple mutants per component. Each new mutant is killed by a suite branch
that F-04 never exercised.

## Operator definitions

The F-04 operator was operationalized in v1 as "an `ignore (documented)` or
`reject` cell accepts the event". The three new classes get the same
treatment:

| Class | Operator (v1 definition) | Fixture cell |
|---|---|---|
| F-01 missing transition | A `transition →X` cell does not transition — the implementation ignores the event instead | `Open × M2` (→Closed) |
| F-02 transfer fault | A `transition →X` cell transitions to the wrong target | `Open × M2` (→Closed, goes to `Idle`) |
| F-05 corrupt state | A `handle` cell corrupts the counted state — the counter moves by the wrong amount | `Open × UV-M1-dup` (`handle (counted)`) |

F-02 exercises the transition-target assertion for the first time at the
implementation level. F-05 exercises the counter assertion added in the
final-review fix wave, which has never been red-probed by a real mutant.

## Changes

### New variant files

Three files under `tests/golden-mini/src/mutants/`, each an exact copy of
`src/mini.py` with exactly one changed region:

1. `mini.F-01-missing-transition.py` — `Open × M2` returns `"ignored"`
   instead of setting `state = "Closed"` and returning `"transition"`.
2. `mini.F-02-transfer-fault.py` — `Open × M2` sets `state = "Idle"` and
   returns `"transition"` instead of `"Closed"`.
3. `mini.F-05-corrupt-state.py` — the `UV-M1-dup` branch does
   `self.dup_count += 2` instead of `+= 1`.

### `fault-mutants.json`

Append three entries to the existing `mutants` array. Format, command,
`workingDirectory`, and `timeoutSeconds` are unchanged. The mutant entries
carry `fault`, `id`, `target`, `variant`, and `cell` as before.

### Selftest updates

The existing baseline case expects `FAULT MUTANTS: OK`; tighten it to also
assert `killed=4` so a silently dropped mutant cannot pass. Each new
variant gets a one-line diff verification inside the selftest: the variant
must differ from `src/mini.py` in exactly one contiguous region, proving
the kill is attributed to the declared mutation and not to fixture drift.

### Prompt and roadmap

`prompts/04-testgen.md`: the fault-class section gains one sentence listing
the operator pattern for F-01, F-02, and F-05 beside F-04. `docs/roadmap.md`
item 8 status updates to "4 of 22 fault classes operationalized".

## Non-goals

- No binder-driven generation. Variants stay hand-authored.
- No other fault classes. F-03, F-06, and F-07+ remain pending.
- No `rules.toml` change.
- No contract change: no new fields in `fault-mutants.json`, no checker
  changes. If a change becomes necessary, stop and report instead of
  extending the contract silently.
- No release, tag, or push without explicit instruction.

## Verification

1. Per-variant diff check: each variant differs from `src/mini.py` in
   exactly one region.
2. Direct checker run: `killed=4 survived=0 errors=0 blocked=0`, with one
   `KILLED` line per mutant carrying its fault id.
3. Item-7 regression: `check_matrix_mutation.py` still kills 9/9.
4. Full gate set: selftest, pack consistency (20 artifacts), tool tests,
   benchmarks, benchmark evidence, `git diff --check`.

## Completion boundary

A local commit completes this slice. Roadmap item 8 advances to 4 of 22
classes. Binder-driven generation remains deferred until more classes are
operationalized.
