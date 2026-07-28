# Changelog

## v1.17 — 2026-07-28
- Prompts 00–05 rewritten through the ste-pack rewrite pass (mechanical round: Vale gate at zero errors, strict class). Rewrite-integrity proofs green per file (code, identifiers, paths, numbers, URLs verified verbatim). No method changes: rules, format tokens, and controlled vocabulary unchanged. Literal tokens adjusted where they tripped the gate: the trace marker "none — control trace" is now "none - control trace", the summary statement in 03 is reworded active, and the disposition/divergence lists use `: ` instead of ` — `. ste_lint deltas:

| file | before | after | delta |
| --- | --- | --- | --- |
| 00-methods-reference.md | 4.11 | 1.35 | −67% |
| 01-scout.md | 2.05 | 1.75 | −15% |
| 02-pilot.md | 4.38 | 2.37 | −46% |
| 03-resolution.md | 2.11 | 1.06 | −50% |
| 04-testgen.md | 3.52 | 2.25 | −36% |
| 05-standing-instruction.md | 1.58 | 0.96 | −39% |

## v1.16 — 2026-07-28
- Split: the language layer is extracted into its own repository, the **ste-pack v1.0** (STYLE.md, Vale styles STE/DTK/STEDict, the three lang-ste prompts, the language checkers incl. the new license-free German catalog `dtk-rules.json`, ste-rules-map.json, selftests). This pack consumes it as a pinned git submodule at `tools/ste-pack/`; the consistency checker verifies the pin against the version declared in the README. The pack's `.vale.ini` now resolves its StylesPath through the submodule. The statechart project dictionary moves from STYLE.md into the README ("Language policy"). Vale gate enabled on this pack's own prompts (strict at error; baseline: 131 errors queued for the ste-pack rewrite pass).

## v1.15 — 2026-07-27
- German adaptation (DTK layer): opt-in Vale style `styles/DTK/` with the machinable subset for German technical writing — Passiv (both word orders, distance-tolerant, single alternated pattern: Vale concatenates `raw` items), Konjunktiv/Modalverben, Füllwörter substitutions, Satzlänge, Nominalstil density, Schachtelsatz; verified on a violation-packed sample (9 flags across all six rules). STYLE.md documents the adaptation path: checkers and prompts are data-agnostic; rules come from a privately licensed tekom Leitlinie via an adapted extractor; the dictionary layer becomes a project termbase (Vorzugsbenennungen + deprecated-synonym substitutions, lemma level, agent handles inflection).

## v1.14 — 2026-07-27
- STE rewrite agent: `prompts/lang-ste-rewrite.md` transforms text into STE using all three layers (Vale mechanics, dictionary-grounded substitutions with cited entry keys, rules pass under the applicability map), meaning-protected by the new `tools/check_rewrite_integrity.py` (code blocks/spans, identifiers, paths, numbers, URLs, protected tokens must survive verbatim; positive and negative selftest in CI). Applied live to the pack: the skill description's gerund chain (Rule 3.5) and the commands' obey-sense "follow" (dictionary: FOLLOW = "to come after"; rewritten to OBEY) — integrity checker green on both.

## v1.13 — 2026-07-27
- Applicability map for the rules layer: `ste-rules-map.json` records the owner's verdict per rule (proposed draft shipped: 8 machine-checked, 3 not-applicable — the safety-instruction section, 42 judge) in own wording; the rules prompt inherits map verdicts verbatim and the checker verifies the inheritance, so applicability is decided once instead of re-litigated per run. Two decisions marked OPEN: Rule 1.14 (British vs American spelling across the corpus) and Rule 8.1 (semicolon ban vs our suggestion level).

## v1.12 — 2026-07-27
- STE writing-rules layer: `tools/extract_ste_rules.py` pulls all 53 Part-1 rules from the owner's licensed copy into a private JSON; `prompts/lang-ste-rules.md` applies them as a grounded agent pass (one verdict per rule, enum incl. `machine-checked` mapping to Vale rules, sample scope must be declared); `tools/check_rules_report.py` verifies coverage, grounding, and quote bounds (fake-data selftest in CI). First migration of a machinable rule into Vale: Rule 6.6 as `STE.ParagraphLength`. First sample on the pack's own texts: the pack title violates Rule 2.1 (four-word noun cluster) and the skill description violates Rule 3.5 (gerund chain).

## v1.11 — 2026-07-27
- STE sense layer as a grounded agent pass: `prompts/lang-ste-sense.md` judges approved meaning and part of speech against the private per-entry dictionary JSON (built from the owner's licensed copy; not shipped). Every verdict cites an entry key; `tools/check_sense_report.py` verifies coverage of all lint flags, the verdict enum, and the grounding (selftest with fake data in CI). First real sample on the pack's own texts: FOLLOW used in the obey-sense twice (STE approves only "to come after"; rewrite OBEY), RUN and CHECK as verbs flagged as technical-verb candidates for the project dictionary, STATE covered as a declared technical name.

## v1.10 — 2026-07-27
- Full-STE dictionary check as an off-by-default mechanism: `tools/build_ste_dictionary.py` merges a user-supplied ASD core word list with the project dictionary and the Pack vocabulary into hunspell files; the separate Vale style `STEDict` flags words outside that union. The data is not shipped (ASD copyright — spec free on request, not redistributable); sense/part-of-speech compliance stays with the validator agent. Mechanism verified with a toy list and then with the owner's licensed Issue-7 extraction (738 keywords, 1,116 incl. listed verb forms, 1,331 with rule-permitted noun plurals); generated dictionaries are gitignored — the data never enters the repository. Data-placement discipline documented (source outside git history, built files gitignored or symlinked, curated terms public, rebuild after curation).

## v1.9 — 2026-07-27
- Stage 06 (reconcile): after implementation the to-be model is promoted to the new as-is, citations refresh at HEAD, superseded artifacts move to `archive/<date>/`, and `manifest.json` pins the analyzed SHA so staleness becomes a CI signal instead of a guess.
- Pack-shipped checker `tools/dsc_check.py` + sidecar contract `formats/analysis.schema.json`: the agent emits `analysis.json`, the pack verifies grid totality, holes→Q, DR links, pair traces, guard outcomes, coverage-table totality, behavioural-DR reverse coverage, Mermaid↔matrix sync, fragment citations, and manifest staleness. Per-run scripts keep only component-specific guard encodings. Selftest fixture wired into CI. The schema is executed, not just shipped: `dsc_check` validates the sidecar against `analysis.schema.json` (jsonschema in CI, graceful note locally), requires the manifest keys, and verifies that every cited DR exists as a `decisions/DR-*.yaml` file. Benchmarked at 75x real scale (10,800 cells): profiling found repeated citation file reads dominant; an lru_cache cut the check from ~1.3 s to ~0.5 s — no compilation needed.
- Fragment citations (`file:line ("fragment")`) required for observed-in-* provenance (02).

## v1.8 — 2026-07-27
- STE enforcement ported to Vale: `.vale.ini` encodes the STYLE.md strictness matrix as path-scoped sections (errors gate `prompts/**`, warnings elsewhere, records exempt via `<!-- vale off -->`); rules as `styles/STE/*.yml` (banned words, em dash, sentence length, passive, semicolon) + `Pack` vocabulary; CI gates on errors only. Verified against Vale 3.15.2 (project now under the vale-cli org): 0 errors, warnings informational. `tools/ste_lint.py` stays as the zero-dependency cross-check. `consumer.vale.ini` ships as the template for consumer repositories (root placement, StylesPath into the vendored pack, catalogue at error level, decisions/*.yaml untouched).

## v1.7 — 2026-07-27
- Language: prompts 01–05 rewritten to STYLE.md strict mode; 00 got the STE-flavored pass on its prose sections. Rules, literal format tokens, controlled vocabulary, and the historical changelog entries are unchanged. `tools/ste_lint.py` added (deterministic approximation of the machine-checkable STE subset; score = violations per 100 words; the delta is the signal, the owner's validator has the final word). Lint deltas:

| file | before | after | delta |
| --- | --- | --- | --- |
| 00-methods-reference.md | 4.93 | 4.11 | −17% |
| 01-scout.md | 5.05 | 2.05 | −59% |
| 02-pilot.md | 7.18 | 4.40 | −39% |
| 03-resolution.md | 4.97 | 2.11 | −58% |
| 04-testgen.md | 6.14 | 3.52 | −43% |
| 05-standing-instruction.md | 4.17 | 1.58 | −62% |


## v1.6 — 2026-07-27
- STYLE.md: ASD-STE100-based language policy — strict mode for prompts and blind-consumed artifacts (catalogue, vocabulary, contract extracts), STE-flavored for descriptive text, exemptions for owner rationales and verbatim quotes; project dictionary of approved technical names; STE lint as third checker (score delta as signal); measurable experiment against the Part-B artefact-row baseline.

## v1.5 — 2026-07-27
- Interactive interview intake mode in 03: one question per round with selectable options, recommended option first (= Enter-default in Claude Code's picker), attributed rationale capture, per-answer write-through, defer via free text, optional chaining into resolution (03; README, resolve command updated).

## v1.4 — 2026-07-27
- Third-run feedback: remembrance semantics required per event family in the Step-3 catalogue vocabulary (the recurring Part-B artefact class: end-of-life/memory semantics missing); guard outcomes standardized into `guard-results.txt`; machine-readable `<!-- event-ids -->` / `<!-- states -->` declaration markers, checker-parsed (02).

## v1.3 — 2026-07-27
- Second-run feedback (same component, v1.2 protocol): seam-contract sweep in Step 1 (failure contracts of invoked seams recorded as NAT — call-site inference is not evidence); upstream-guard annotations and a machine-checked `undesired-coverage` table in Step 3; requirement-scope rule operationalized as a mandatory, Stage-2-checked line on decision-citing control-trace verdicts in Step 6; Part-B blind packs now include event-contract semantics; Part B gains the `convergent` class and mandatory row-coverage verification (02).

## v1.2 — 2026-07-27
- Guard disjointness/coverage/boundary proofs via z3 (`check_guards.py`) promoted from optional footnote to mandatory-where-formalizable; every guard group must end `proven`, `violation`, or `not-formalizable` (02, 03, 04, 05, 00 aligned).
- Repository structure: canonical `prompts/`, Claude Code skill + slash commands, pack consistency checker + CI.

## v1.1 — 2026-07-27
- Feedback round from the first real Part-B diff: cross-source interaction pairs; requirement-scope rule; doctrine-line sweep; ban on self-declared "benign"; mechanical hole→question mapping (checker Stage 2); catalogue gate-type annotation; Part B formalized with divergence classification (02).

## v1.0 — 2026-07-27
- Initial pack: methods reference, scout, pilot, resolution, testgen, standing instruction.
