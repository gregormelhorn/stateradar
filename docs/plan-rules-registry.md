# Plan: rules registry — single source for method rules

**Status:** shipped in v1.35 (2026-08-07) — stages 1–4 implemented.
Registry: `formats/rules.toml` (TOML, not YAML as originally drafted:
stdlib `tomllib` keeps the pack's zero-dependency principle — PyYAML
is not part of "stdlib-Python plus jsonschema"). Generator/checker:
`tools/gen_rules.py` (`--write`, `--check` via
`tools/check_pack_consistency.py`, `--selftest` in CI).

Remaining follow-ups, tracked as registry warnings (not silent):

* Selftest backlog: PA-1/PA-2 only (the z3 guard proofs are per-run
  artifacts; a pack-side red case needs a z3 dev-dependency). The other
  twelve TODO refs were discharged on 2026-08-07 with red cases in
  `tools/selftest/run_selftest.py`.
* Six `checker_candidate` rules: PA-4, PA-7, PA-10, PA-17, PA-22, and
  R-REQUIREMENT-SCOPE — the last one downgraded from a false
  enforcement claim: AGENTS §5 advertised a scope-line checker that no
  tool implements. The registry constraints surfaced it.
* ODC backfill over the eleven existing pilot manifests (fault class ×
  trigger per recorded finding).

## Problem

The pack's rules live as prose in five places with no shared identity:
PA-1–24 in `prompts/00-methods-reference.md` (flat list + six prose
sections), the inline lints in `prompts/02-pilot.md` Steps 3/5/6, the
divergence classes in the 02 changelog, the failure modes and checker
catalogue in `AGENTS.md` §5/§6, and the "what StateRadar finds" bullets
in `README.md`. Three concerns are mixed that the literature separates:

* **wellformedness** — deterministically checkable shape rules (guards
  disjoint, grid total);
* **fault model** — what can be wrong (drives variant derivation and
  test generation);
* **process** — who decides what (prompt/human territory).

Symptoms: the `VOCAB x2` check in `tools/check_pack_consistency.py`
keeps a *duplicated* vocabulary in sync instead of eliminating the
duplication; AGENTS §5 drifted from the prompts and was chased manually
three times (2026-08-05); no mapping exists from fault class to
detector, so the detection portfolio cannot be evaluated against a
fault catalogue (the ODC question: which detector has never found
anything, which fault class has no detector).

## Design

One machine-readable registry at formats/rules.toml (new file) with
three top-level sections:

### 1. `vocab` — the closed vocabularies

```yaml
vocab:
  dispositions: ["transition", "handle", "ignore (documented)",
                 "ignore (accidental)", "defer (queued)", "reject", "UNSPECIFIED"]
  holes: ["ignore (accidental)", "UNSPECIFIED"]
  question_status: [OPEN, ANSWERED, RESOLVED, CONFLICT]
  not_formalizable: [external-call, dynamic-state, clock, unstructured-payload]
  provenance: [explicit-requirement, observed-in-code, observed-in-tests,
               inferred, proposed]
```

Today these are duplicated across 00, 02, `tools/dsc_check.py`, and
`tools/check_pack_consistency.py`. After stage 2 every occurrence is
generated or imported from the registry.

### 2. `faults` — the fault-class catalogue (F-xx)

Binder's state-machine fault taxonomy (missing transition, transfer
fault, output fault, sneak path, corrupt state, trap door) plus the
pack's own empirically found classes:

```yaml
faults:
  - {id: F-01, name: missing transition,      binder: missing-transition}
  - {id: F-02, name: transfer fault,          binder: transfer-fault}
  - {id: F-03, name: output fault,            binder: output-fault}
  - {id: F-04, name: sneak path,              binder: sneak-path}
  - {id: F-05, name: lifecycle coupling,      source: PA-21}
  - {id: F-06, name: double release,          source: PA-23}
  - {id: F-07, name: cancellation leak,       source: PA-24}
  - {id: F-08, name: synchronized reset herd, source: v1.11}
  - {id: F-09, name: callback deadlock,       source: v1.12}
  # undesired-variant categories (SHARD-aligned, stage 4):
  - {id: F-10, name: loss/omission}
  - {id: F-11, name: delay/late}
  - {id: F-12, name: duplication}
  - {id: F-13, name: out-of-order/stale}
  - {id: F-14, name: contradictory input}
  - {id: F-15, name: spontaneous commission}   # SHARD: commission
  - {id: F-16, name: subtle value fault}       # SHARD: value (subtle)
```

The README "what StateRadar finds" list is generated from this section.

### 3. `rules` — one entry per rule

```yaml
rules:
  - id: PA-1
    title: guards pairwise disjoint
    class: wellformedness    # wellformedness | completeness | fault-model
                             # | process | empirical-pattern
    statement: "guards per (state,event) pairwise disjoint — order must never decide"
    enforcement: checker     # checker | test | lint | prompt | human | data
    checker_ref: "check_guards.py (per-run) + dsc_check: guard outcomes present"
    selftest_ref: "tests/red-mini"
    emits_to: ["00#method-rules", "AGENTS#5"]
    lineage: [heitmeyer-tosem-1996]
    added_by: v1.0           # or {version: v1.11, pilot: reconnecting-websocket}
    detects: []              # F-xx refs; required for class: fault-model
```

`enforcement: data` marks rules whose content is itself registry data
(the undesired-variant category list): extending them is a data edit
that propagates to every generated block, not a prose edit in three
files.

## Generation

A new generator script (tools/gen_rules.py, new file) renders marked
blocks — `<!-- generated:rules key=... -->` … `<!-- /generated -->` —
into four targets:

| Target | Generated content |
|---|---|
| `prompts/00-methods-reference.md` | condensed PA list ("Method rules" section), disposition vocabulary |
| `prompts/02-pilot.md` | Step-5 lint list, disposition vocabulary (incl. the Part-B dispatch copy), undesired-variant checklist in Step 3 |
| `AGENTS.md` | §5 checker catalogue (from rules with `enforcement: checker`) |
| `README.md` | "what StateRadar finds" list (from `faults`) |

`tools/check_pack_consistency.py` switches to regenerate-and-diff:
render to a temp dir, diff against the working tree, drift fails the
build. The `VOCAB x2` check is deleted — both occurrences are rendered
from `vocab.dispositions`, so divergence is impossible by construction.

Prose context around the generated blocks (the PA-19/20/21 case-study
sections, semantics conventions, lineage) stays hand-written. The
registry owns rule identity, classification, and every *list* that must
agree across files — not the explanatory prose.

## Registry constraints (checked in check_pack_consistency)

1. `enforcement: checker` ⇒ `checker_ref` **and** `selftest_ref`
   present; referenced paths exist. (The 2026-08-05 lesson — every
   checker needs a red selftest — becomes a constraint instead of a
   discipline appeal.)
2. `enforcement: lint` ⇒ the rule appears in the generated Step-5
   block.
3. `class: fault-model` ⇒ at least one `detects` entry.
4. Every F-class with no rule that `detects` it ⇒ warning. This is the
   standing ODC gap signal: a fault class without a detector is a real
   hole; a detector with no finds over N pilots is dead prompt freight.
5. Ids unique; `emits_to` targets resolve to existing marker blocks.

## Classification of PA-1–24 (seed data for stage 1)

| PA | Class | Enforcement today | Note |
|---|---|---|---|
| 1, 2 | wellformedness | checker (z3 + dsc_check) | clean |
| 3 | **splits** | checker + prompt | 3a proof obligation (wellformedness/checker); 3b `not-formalizable` labelling discipline (process; category list moves to `vocab.not_formalizable`) |
| 4 | wellformedness | prompt | checker candidate: catalogue annotation is parseable |
| 5 | wellformedness | prompt | notation permission (SCR `@T`) |
| 6 | **splits** | prompt | 6a NAT/SYS classification (wellformedness, sidecar-checkable); 6b "analysis may assume NAT, tests may not" (process rule binding 04-testgen) |
| 7 | wellformedness | prompt | bindings section is checkable → checker candidate |
| 8 | wellformedness | prompt | semantics convention, not checkable |
| 9 | **splits** | test + prompt | 9a dispatch-seam requirement (process/test infra); 9b reentrancy probe (fault-model, detects F-09) |
| 10 | completeness | prompt | matrix-header statement → checker candidate |
| 11 | completeness | prompt | "aim for" is deliberately soft; stays prompt |
| 12 | completeness | checker (coverage map) | clean |
| 13 | **splits** | checker + data | 13a checklist *obligation* per external source (completeness; checker: coverage-table totality); 13b the category *list* itself (fault-model, `enforcement: data`, detects F-10…F-14; SHARD extension F-15/F-16 lands here as a data edit) |
| 14 | **splits** | checker + prompt | 14a Mermaid↔matrix sync (wellformedness, checker exists); 14b "matrix is the primary review surface" (process) |
| 15 | completeness | lint | Jaffe–Leveson checklist; the Step-5 list is generated |
| 16 | process | prompt | human-review aid (AND/OR tables) |
| 17 | wellformedness | prompt | cheap checker: PascalCase regex on the `<!-- states: ... -->` declaration |
| 18 | **splits** | checker + prompt | 18a terminal declaration + checker semantics (wellformedness; `tools/check_reachability.py` covers it); 18b exit-condition naming (process, pairs with PA-17) |
| 19, 20 | process | prompt/human | to be restated on the Parnas/Madey four-variable model (PA-20 = OUT relation; PA-19 = outside monitored variables) |
| 21 | fault-model | lint | fault class F-05 + its lint detector |
| 22 | completeness | lint | **enforcement gap:** 00 claims "doctrine mapping breaks the build" but AGENTS §5 lists no DOC-n→cell check — registry will show `checker_ref: null`; checker candidate |
| 23 | fault-model | lint | fault class F-06 + detector |
| 24 | fault-model | lint | fault class F-07 + detector |

PA-21/23/24 split along a different axis: fault class (a `faults`
entry) vs. detector (a `rules` entry with `detects`). Detector = ODC
trigger axis, F-class = ODC defect-type axis.

Also enters the registry (beyond PA-1–24): the AGENTS §4 hard rules
(process), Step-8 finding verification (process, v1.13), lock
discipline (fault-model, v1.12, detects F-09), multi-instance probes +
synchronized-reset lint (fault-model, v1.11, detects F-08), user-model
gap lint (process, v1.12), remembrance semantics (wellformedness of
the catalogue, v1.4), asserted absence (wellformedness/checker, v1.10),
requirement-scope rule (process; scope-line check exists).

## Stages

**Stage 1 — seed.** Write formats/rules.toml from the existing texts.
Purely mechanical; no semantic change, no generated output yet. Split
PAs get suffixed ids (PA-3a/PA-3b …); original numbering stays stable.
Acceptance: registry parses; every current PA, lint item, checker-
catalogue line, and vocabulary value is represented exactly once.

**Stage 2 — generate.** Add the generator, insert marker blocks into
the four targets, switch check_pack_consistency to regenerate-and-diff,
delete the VOCAB x2 check. Acceptance: generated blocks byte-identical
to the previous hand-written content (modulo agreed formatting); CI
green; a deliberate registry edit shows up in all targets via one
regeneration.

**Stage 3 — constraints.** Enable registry constraints 1–5.
Acceptance: constraint violations list exactly the known gaps (the
`checker_ref: null` candidates PA-4/7/10/17/22) as a visible backlog,
nothing else. The PA-22 DOC→cell checker gap is either implemented or
explicitly downgraded in 00's purpose section.

**Stage 4 — new content as data.** SHARD categories F-15/F-16 into the
undesired-variant checklist (two data rows, propagates to 00, 02
Step 3, and the Part-B dispatch); F-catalogue names into the README
list; ODC fields (defect type × trigger) added to the finding format
from the next pilot on, backfill over the existing pilot manifests
separately. Acceptance: 02's changelog gains one entry describing the
mechanism change; no hand-edited duplicate of the category list remains.

## Out of scope

EARS normalization of DOC lines (Step-1 addition) and the Parnas/Madey
rewrite of PA-19/20 are worthwhile but independent; they follow after
stage 4 as ordinary prompt/prose changes. Test-criterion field in
`matrix-coverage.json` (`all-transitions | round-trip | W`) is a
04-testgen concern, tracked separately.
