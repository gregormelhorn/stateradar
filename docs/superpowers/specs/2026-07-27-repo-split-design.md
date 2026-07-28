# Repo split: domain-statechart + ste-pack

Date: 2026-07-27. Status: approved design, pending implementation.

## Goal

Split `~/workspace/domain-statechart` into two repositories with one
direction of dependency: the domain-statechart pack consumes the ste-pack.
Replace the personal `ste-writing` pi skill with the pack-shipped version.

## Decision (option C)

Two repositories plus thin harness wrappers in each:

1. **`~/workspace/ste-pack`** (new) — controlled-language layer: ASD-STE100
   (English) and DTK (German). Harness-neutral prompts + Vale styles +
   checkers, plus `skills/` and `commands/` wrappers.
2. **`~/workspace/domain-statechart`** (existing, keeps history and tag
   v1.15) — statechart methodology pack. Consumes ste-pack as a pinned git
   submodule under `tools/ste-pack/`.

## What moves to ste-pack

- `STYLE.md`, `styles/` (STE, DTK, STEDict, vocabularies), `consumer.vale.ini`
- `prompts/lang-ste-sense.md`, `lang-ste-rules.md`, `lang-ste-rewrite.md`
- `tools/build_ste_dictionary.py`, `extract_ste_rules.py`,
  `check_sense_report.py`, `check_rules_report.py`,
  `check_rewrite_integrity.py`, `ste_lint.py`
- `ste-rules-map.json`, `dtk-rules.json` (incl. the uncommitted v1.16 work)
- Selftests `rewrite/`, `sense/`, `rules/`, `rules-de/`
- New: own README, CHANGELOG (STE history ported from the v1.9–v1.16
  entries), LICENSE copy, own CI

## ste-writing skill replacement

- Linting in the pack works through **Vale** (declarative YAML rules in
  `styles/STE/` + project vocabulary + optional STEDict layer). This is
  the primary mechanical layer and the more modern approach. The
  standalone `ste-lint.py` bundled with the old skill reimplements
  mechanics ad hoc and is **dropped, not merged**.
- `tools/ste_lint.py` (the pack version, newer than the skill's) stays
  as-is: a quick delta-signal approximation, not a certified checker.
- The skill's extra linter categories (marketing adjectives, phrasal
  verbs, modal hedges, contractions, nominalizations) are not in the
  Vale styles. They stay as agent-side judgment in the SKILL.md
  self-lint checklist. Migrating them into Vale rules is possible later
  — out of scope for the split (YAGNI).
- The skill's SKILL.md (rules digest, strict vs STE-flavored modes,
  self-lint checklist) becomes `ste-pack/skills/ste-writing/SKILL.md`,
  pointed at Vale and the pack tools instead of a bundled script. Modes
  map onto the pack's strictness-per-text-class policy in STYLE.md —
  cross-reference, do not duplicate.
- `~/.pi/agent/skills/ste-writing/` (SKILL.md + ste-lint.py) is deleted
  and replaced by a symlink to the pack-shipped skill, so the personal
  skill tracks the pack version.

## What stays in domain-statechart

- `prompts/00–06`, `commands/`, `skills/claude-code/domain-statechart/`,
  `formats/`
- `tools/dsc_check.py`, `tools/check_pack_consistency.py` (STE artifact
  entries removed; new check: pinned submodule tag == declared version)
- `tools/selftest/analysis/`, `selftest/src/`
- The statechart vocabulary from STYLE.md line 34 stays here as consumer
  termbase config; ste-pack keeps a generic example instead.
- `.vale.ini` at repo root, StylesPath into `tools/ste-pack/styles/`
  (replaces the consumer.vale.ini copy workflow for this repo).
- README/CHANGELOG trimmed of STE sections; both replaced by a dependency
  declaration. SKILL.md gets a routing line: language work → ste-pack skill.

## Versioning

- ste-pack starts at **v1.0**. Its CHANGELOG marks the ported entries as
  "ported from domain-statechart pack".
- domain-statechart then bumps to **v1.16**: "STE layer extracted to
  ste-pack, consumed as pinned submodule v1.0". The uncommitted v1.16
  German-rules work moves with the STE files into ste-pack (it is entirely
  STE-side).

## CI

- ste-pack CI: consistency checker + all selftests (sense, rules,
  rules-de, rewrite integrity). This makes the v1.16 CHANGELOG claim
  "selftest wired into CI" true — it currently is not (workflow runs only
  the consistency checker).
- domain-statechart CI: pack consistency + dsc_check selftest, submodule
  pinned and checked out.

## Implementation order

1. Create `~/workspace/ste-pack`, move files (uncommitted v1.16 changes
   travel with them), write README/CHANGELOG/CI, port the skill SKILL.md
   to point at Vale + pack tools, commit, tag v1.0.
2. In domain-statechart: remove moved files, add submodule, rewire
   .vale.ini, patch check_pack_consistency.py, trim README/CHANGELOG,
   add routing line to SKILL.md, commit, tag v1.16.
3. Replace `~/.pi/agent/skills/ste-writing/` with a symlink to the pack
   skill.
4. Verify: both CIs green locally (run checkers by hand), vale runs in
   domain-statechart against the submodule styles, pi loads the symlinked
   skill.

## Risks

- Submodule pinning adds a manual update step to domain-statechart —
  accepted, it matches the pack's own consumer doctrine.
- The symlinked personal skill breaks if ste-pack moves — documented in
  the ste-pack README.
