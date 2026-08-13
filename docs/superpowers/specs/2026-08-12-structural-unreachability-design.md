# Structural Unreachability: No New Disposition, a Guarded Cell

**Date:** 2026-08-12
**Scope:** Give golden-mini a structurally unreachable cell, and record how the
pack expresses one — using the upstream-guard mechanism that already exists
rather than an eighth disposition.
**Status:** measured; ready to plan.

## Measured state, at commit `32d7f90`

### The vocabulary has no "can't happen", and the practice has four workarounds

```text
dispositions = [transition → <target>, handle, ignore (documented),
                ignore (accidental), defer (queued), reject, UNSPECIFIED]
holes        = [ignore (accidental), UNSPECIFIED]
```

Researched best practice keeps three categories distinct: *event ignored*,
*can't happen*, *error/reject* — and states the distinction "must be defined
explicitly during modeling". The pack carries only two of them.

Real analyses have hit this already, and each solved it differently:

| artifact | workaround |
|---|---|
| `meilisearch-s3-snapshot/open-questions.md:11` | open question: "structurally unreachable outside the active…" |
| `valkey-glide-5803/open-questions.md:75` | `Q-01 … Structurally impossible`, F-04 "ruled out as structurally impossible" |
| `grpc-go-2669/open-questions.md:182` | prose NAT reference: "unreachable today per NAT-4" |
| `grpc-go-2669/event-catalogue.md:89` | upstream-guard table: `| event | guarded upstream | absent here |` |

Four routes for one situation means no checker can see it and the next analyst
invents a fifth.

### But the mechanism already exists

`prompts/02-pilot.md:152` requires, for **every** external event, "which
validations happen upstream of this boundary (with citations into the upstream
code) and which are absent here". Golden-mini already carries it as
`upstream_guards` in the sidecar, and `dsc_check` enforces its presence
(`R-UPSTREAM-GUARD`).

That is the missing link. **Unreachability is not a disposition — it is a
consequence of an upstream guarantee.** A disposition says what the component
does when the event arrives; "cannot arrive" says what the environment will not
send. Those are different layers, and this pack spent a whole wave separating
layers for fault classes.

### Nothing is machine-readable today

```text
ignore (documented) across all sidecars: 339, with a rationale field: 0
```

Every justification lives in matrix cell prose. No checker can reach it. This
is the broader problem behind the narrow one, and it is deliberately **not**
solved here.

## Decision: no eighth disposition

Rejected, with reasons:

- **Layer confusion.** A disposition describes component behaviour. Structural
  unreachability describes the environment. Adding `impossible (structural)`
  would mix the two in the one place the pack keeps them apart.
- **Cost.** Schema, `vocab`, `dsc_check`, `check_matrix`, every prompt, and
  every existing matrix would move for a case that four artifacts already
  express with existing mechanics.
- **It would weaken the cell.** Marking a cell "impossible" invites an empty
  code path. Ned Batchelder's rule applies: *"Code should only do nothing if
  nothing is the correct thing to do."* If the impossible happens anyway, it
  must be loud.

**Instead:** an unreachable cell carries a **defensive disposition** —
normally `reject` — and the event's `upstream_guards` annotation states the
guarantee that makes it unreachable. The disposition covers the breach; the
annotation explains the expectation. Both already exist and are already gated.

## The golden-mini case

Golden-mini has no unreachable cell today, and no internal events at all —
every catalogue entry is `operator / external`. So the fixture cannot exercise
the rule, and a rule no fixture exercises is the hollow-check shape from
`AGENTS.md` §6.

Add one internal event:

| field | value |
|---|---|
| id | `svc-ack` |
| name | service acknowledges the open |
| source | `svc` |
| ext/int | **internal** |
| upstream_guards | the service emits an ack only in response to a delivered `M1` |

Dispositions, one per state, deliberately all different:

| state | disposition | why |
|---|---|---|
| `Idle` | `reject` | **structurally unreachable**: no `M1` was ever delivered, so the guarantee above means no ack can exist. Rejecting makes a breach of that guarantee loud instead of silent. |
| `Open` | `handle` | the normal case: the ack for the open that got us here |
| `Closed` | `ignore (documented)` | a late ack after close is possible and harmless |

This is a fixture design decision, not a derivation. It is defensible because
it exercises three different dispositions on one column, introduces the first
internal event, and makes the unreachable cell the *reject* one — so the
defensive choice is the one under test.

### What it earns

- the first internal event in the fixture, so `ext/int` classification is
  exercised rather than merely declared
- a cell whose disposition is justified by an upstream guarantee, which is the
  pattern this spec is defining
- no new fault class; F-17 (spontaneous commission) already covers "an event
  with no legitimate trigger" as a *matrix* shape, and this is not that: a
  spurious event **can** arrive, an unreachable one is excluded by a guarantee

## Doctrine to record

In `prompts/02-pilot.md`, next to the upstream-guard instruction: when an
upstream guarantee makes a cell structurally unreachable, keep a defensive
disposition (prefer `reject`) and name the guarantee in `upstream_guards`.
Do not invent a "cannot happen" disposition, and do not leave the cell on
`ignore` — an ignored breach is a silent breach.

Roadmap item to add, **not** built here: machine-readable cell rationale.
`339 ignore (documented), 0 with a rationale field` is the measured case for
it, and it would let a checker verify that an unreachability claim cites its
guarantee. Building the checker before the field exists would mean matching
prose for words like "unreachable" — heuristics of exactly the kind this pack
forbade for UV categories.

## Non-goals

- no eighth disposition, no `vocab` change
- no rationale field in the sidecar schema (named roadmap item)
- no checker that greps prose for unreachability claims
- no new fault class, no new UV column
- no changes to the other four artifacts that used workarounds
- no CHANGELOG entry, no version bump, no release, tag, or push

## Verification

```bash
uv run --with jsonschema python3 tools/dsc_check.py tests/golden-mini/domain-analysis/mini --repo tests/golden-mini
python3 tools/check_fault_mutants.py tests/golden-mini/domain-analysis/mini
python3 tools/check_matrix_mutation.py tests/golden-mini/domain-analysis/mini
python3 tools/gen_mutant_variants.py --check tests/golden-mini/domain-analysis/mini
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
git diff --check
```

**Derived and unverified at spec time.** A fourth column changes the matrix to
3 × 8 = 24 cells, and adds `reject`, `handle`, and `ignore` cells, so
`MUTATION CHECK` (today `killed=25`) moves by an amount the executor must
measure, not assume. `FAULT MUTANTS` should stay at `killed=6`. A mismatch is
`BLOCKED(<task>): derived count mismatch`.

The part-B blind fixtures grow automatically — they were derived from the
catalogue in v1.52, so this is the first wave since that no longer needs a
manual fixture repair step. That is worth confirming explicitly.

## Completion boundary

Local commits complete the wave. No release. No tag. No push.
