# Changelog

## v1.24 — fake-timer semantics, checker wrapper, typed suites, bulk-edit guidance (2026-08-05)

Learnings from the dobby refactoring round (check_matrix dedup, strict
typing of the domain suites, shared-fake consolidation):

- **Fake-timer semantics** (00-methods-reference): a fake timer needs
  both the scheduling delay and an absolute due offset per entry. With
  only stored delays, horizon-spanning scenarios starve long timers
  silently (15 rechecks in front of a TTL → hang, not failure).
- **tools/templates/check_matrix.py** (new): the per-component wrapper
  for the generic checker. 02-pilot now points at it instead of
  "write check_matrix.py" — component-specific checks only when the
  generic one does not cover them, never ~90% logic copies.
- **04-testgen**: the generated cell suite must pass the repo's static
  type gate (typed seams make assertions machine-checkable).
- **06-reconcile**: bulk mechanical edits call for
  refresh_citations.py + dsc_stamp.py, never manual blanket line
  shifts (a blanket +N over-shifts fragment-pinned citations).

## v1.23 — polish from the consumer loop (2026-08-05)

Six learnings from a full week of consumer work (19 governed
components, 4 blind passes, 47 DRs in dobby):

- **tools/check_matrix.py** (new): the generic per-component matrix
  checker. Every pilot had duplicated ~90% of it per component; this
  is the shared version (declarations, grid, citations, hole→Q,
  pair→trace).
- **tools/dsc_stamp.py** (new): validate first, then pin the manifest
  at HEAD — the two-commit manifest-bump pattern, mechanized.
- **part_b_pack learns the doctrine**: doctrine lines (DOC-n) are
  auto-extracted from extraction.md into the blind inputs (both
  Part-B artefacts traced to a missing doctrine line). New
  `--for-dispatch` mode prepends the anti-placeholder header.
- **02-pilot**: event-catalogue.md must be its own file (Part B reads
  it verbatim); dispatch notes — a blind pass refusing contaminated
  context is the control working.
- **04-testgen**: test-file naming convention (unique basenames,
  `test_<component>.py`) after three pytest collection collisions.

## v1.22 — scaffold, composition report, benchmarks (2026-08-05)

The mid-layer from the next-steps review:

- **tools/gen_matrix_scaffold.py** (new): emits the empty matrix grid
  (sub-table split for wide event sets) from the state list and the
  catalogue's id declaration. The LLM fills cells; it never holds the
  table structure.
- **tools/dsc_compose.py** (new): cross-model composition report —
  event names wired across models, and model links where a matrix
  hands behaviour to a neighbour (untestable-via-seam reasons naming
  another component). Report-only by design; a gate needs more models.
- **.benchmarks/** (new): the falsifiable layer. Golden mini cases with
  expected outputs; the runner executes the pack tools against them
  (green cases prove the gates pass, red cases prove they catch
  violations). Includes the manual pilot-convergence protocol for the
  LLM-in-the-loop calibration claim.

## v1.21 — the low-friction tool layer (2026-08-05)

Four low-impact additions from the next-steps review:

- **tools/part_b_pack.py** (new): assembles the Part-B blind-pass input
  package (catalogue + requirements + contract texts) with a length
  guard against dropped payloads, and validates the blind table's
  coverage mechanically — every catalogue event id and pair ordering
  must appear exactly once in a table row. The instruction block is
  extracted live from `prompts/02-pilot.md`.
- **tools/refresh_citations.py** (new): the 06-reconcile citation
  refresh, mechanized. Content-anchor first (language-agnostic), Python
  def-map fallback, bare-basename resolution against src/. Unresolvable
  citations are reported for human review, never guessed (dobby
  trigger-service: 190 mechanical + 6 manual after the DR
  implementation).
- **not-formalizable needs a categorized reason.** `dsc_check` and the
  sidecar schema now require guardGroups with outcome
  `not-formalizable` to carry a `reason` starting with `external-call |
  dynamic-state | clock | unstructured-payload`. The outcome is a
  judgment call; the category makes it reviewable. The pilot prompt
  documents the vocabulary.
- **tools/templates/test_dsc_check.py** (new): the CI gate file that
  04-testgen describes — copy into the consuming repo and point
  PACK_CHECKER at your pack location.

## v1.20.4 — README explains why Part B exists (2026-08-05)

The README gained a "Why Part B exists" section: the mirroring trust
problem, the three blind inputs, the five diff classes, why blindness
is the mechanism, and the dobby trigger-service worked example (the
independently re-derived DR-035).

## v1.20.3 — GR-7/GR-8 Vale rules active (2026-08-05)

- ste-pack pinned v1.4.0 → v1.5.0: the Issue-9 general recommendations
  are now Vale rules. `STE.GenderNeutral` (warning, GR-7) finds
  gender-specific pronouns and man/woman; `STE.Possessive` (suggestion,
  GR-8) finds the Saxon genitive and defers the correctness judgment to
  the writer. On this pack's prose: zero GR-7 findings, 25 GR-8
  suggestions on correct possessives — informational, the gate stays
  0 errors.

## v1.20.2 — language layer on ASD-STE100 Issue 9 (2026-08-05)

- ste-pack pinned v1.3.1 → v1.4.0: Issue-9 alignment. Issue 9 renames
  "technical name" to **"technical noun"**; STYLE.md, the language
  prompts, and this pack's README and `technical-names.txt` header
  follow. The lintable limits are unchanged (20/25 words, six
  sentences), so the Vale gate is identical.
- Dictionary data rebuilt from the Issue-9 word lists
  (`ste-core-words-issue9.txt`: Issue-9 headwords + [TN] alternatives,
  union of the Issue-7 forms minus newly unapproved words). Notable for
  this pack's prose: `file`, `could`, `want`, `activate` are now
  approved; `required`, `switch`, `consult`, `separately` are newly
  unapproved and will flag.
- The rebuild command in the README and `technical-names.txt` points at
  the issue-9 list.

## v1.20.1 — Part-B inputs carry the disposition vocabulary (2026-08-05)

A blind pass without the seven-value vocabulary applies `reject` and
`handle` to identical semantics (four vocabulary-only "divergences" in
the dobby trigger-service Part B). The Part-B input block in
`02-pilot.md` now includes the disposition definitions verbatim.

## v1.20 — the deterministic layer stops passing silently (2026-08-05)

The prompts demanded discipline the checkers could not see. Five gaps let
a sidecar skip the pack's distinctive checks and still print `OK`. Each
fix ships with a selftest case that asserts the *red* result, because a
checker only ever run against passing input is a checker nobody tested.

- **Asserted absence.** An empty or missing `pairs`, `guardGroups`, or
  `coverage` section now fails unless the sidecar's new `completeness`
  block states a reason (`formats/analysis.schema.json`, min length
  enforced). Stripping all three used to return `DSC CHECK: OK` — the
  exact silent skip 00-methods-reference calls an error.
- **Model sync works on compound states.** The edge pattern was `\w+`,
  which can never match a compound label (`open idle`), so the check was
  dead for the most complex matrices. It now resolves Mermaid containers
  (`state open { idle --> busy }`) against compound rows and inherits
  container edges to leaves. The 04-testgen workaround ("pass no
  `--model` for compound-state matrices") is withdrawn.
- **The generator declares what it cannot derive.** `gen_analysis_sidecar.py`
  never emitted the three sections above, so "generate, never hand-write"
  plus silent-pass meant generated sidecars could not fail those checks.
  It now emits `completeness` reasons naming the source artifact, and
  preserves hand-merged sections on regeneration.
- **Any implementation language.** The generator indexed `src/**.py`
  only; every other layout silently dropped citations, which then failed
  the "needs a DR or a citation" check with a misleading message. Roots
  and extensions now cover the common layouts and are overridable
  (`sidecar-overlay.yaml`: `src_roots`, `src_exts`).
- **No silent schema degradation.** A missing `jsonschema` printed a note
  and exited 0. Contract validation is now required unless
  `--allow-no-schema` is passed explicitly.
- **CI exercises the real paths.** `tools/selftest/run_selftest.py` (11
  assertions, red and green) replaces the single green invocation, which
  ran without `--repo` or `--model` and so never touched citation checks,
  diagram sync, or staleness. New fixture `tools/selftest/compound/`:
  multi-table matrix, compound rows, hierarchical diagram, TypeScript
  source.

## v1.19 — brownfield adoption: maturity levels, sidecar generator, checker hardening (2026-08-05)

Learnings folded back from a full consumer session (dobby: scout → pilot
→ resolution on a 15-component brownfield repo, plus sidecar
backfill):

- **Maturity levels (L1–L5)** defined in 00-methods-reference and the
  README adoption section: descriptive → decided → enforced → verified
  → steady state. Brownfield "light loops" now have a name and a floor;
  skipping levels silently is called out as the drift source it is.
- **No reconcile-lite.** 06-reconcile step 0: a promotion without
  `analysis.json` and a green `dsc_check` is bookkeeping, not a
  reconcile.
- **tools/gen_analysis_sidecar.py** (new): the sidecar is generated
  from the matrices, never hand-written. Handles multi-table matrices
  (wide event sets, sub-tables with own headers), compound row labels,
  hole→Q extraction for both hole classes, DECIDED→RESOLVED status
  mapping. Per-project extras via `domain-analysis/sidecar-overlay.yaml`
  (skip list, question aliases, backfill citations).
- **dsc_check hardened**: friendly exit when the sidecar is missing
  (was a traceback); loud failure on snake_case `watch_paths` and on an
  empty `watchPaths` (both ran the staleness diff unfiltered and
  false-staled everything).
- **formats/manifest.schema.json** (new): the manifest contract
  (`component`, camelCase `watchPaths`, `analyzedSha`).
- **Wide matrices** documented (00-methods-reference, 02-pilot):
  sub-tables with per-table headers, state rows repeat.
- **Documenting edges** for event-unreachable states (02-pilot step 2):
  operator-set and guard-condition states need diagram presence.
- **Model links** (00-methods-reference, 02-pilot step 0, 04-testgen):
  cross-component behaviour ownership; a high untestable-via-seam share
  is a boundary signal, not a test gap.
- **Question status vocabulary** pinned: OPEN / ANSWERED / RESOLVED /
  CONFLICT (00-methods-reference); DECIDED maps to RESOLVED.
- **05-standing-instruction**: never enumerate the governed components
  (the directory is the authority); keep domain-analysis/summary.md as
  the living index; the CI gate is the cell suites plus dsc_check.

## v1.18.1 — 2026-07-29
- Test audit: two-suite reality modeled. The audit subjects are the
  hand-written unit tests; the pack-generated domain tests act as the
  sound reference suite, never re-judged. New CONFIG field `Reference
  suite`, new hard rule 9, `matrix-coverage.json` loaded as coverage
  evidence, `weak-redundant` proposes deletion (not rewrite) when the
  reference suite covers the cell, cell classes count reference coverage,
  checker verifies deletion proposals against the coverage map.

## v1.18 — 2026-07-29
- New stage prompt `prompts/07-test-audit.md`: test-suite audit against the
  decided matrix. Main goal: weak tests that bind to implementation instead
  of behaviour (rule 6 operationalized). Five weakness signals, seven test
  classes (`sound`, `weak-redundant`, `weak-seam-gap`, `weak-incidental`,
  `equivalent-duplicate`, `deviating`, `unmapped-behavioural`), four cell
  classes, mandatory executed checker (`check_test_coverage.py`), artifacts
  `test-coverage-map.md` + `coverage-diff-report.md`. Deletion and weakening
  stay human decisions via DR proposals. Wired in: consistency checker
  (18 artifacts), `commands/domain-test-audit.md`, skill routing rule 7,
  loop diagrams in methods reference and AGENTS.md.

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
