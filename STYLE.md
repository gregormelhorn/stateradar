# STYLE.md — Language Policy (ASD-STE100-based)

The pack's texts follow Simplified Technical English (ASD-STE100), with strictness set per text class. The goal is not style. The goal is fewer misreadings: a blind Part-B reader gets only the catalogue's prose, and in the third TriggerService run, all six artefact rows came from one prose-ambiguity class. Controlled language is the countermeasure, and it is lintable.

Enforcement is mechanical where possible: a deterministic STE linter (the machine-checkable subset; score = violations per 100 words) runs as the third checker next to `check_matrix.py` and `check_guards.py`. The linter's score delta is the signal, not the absolute number. The judgment rules of full STE need a human. Waivers follow the existing lint-waiver pattern: with a reason and a DR link.

## Strictness by text class

| text class | mode | reason |
| --- | --- | --- |
| prompts 01–05 (instructions to agents) | **strict** | procedural text is STE's home ground; one instruction per sentence improves agent compliance |
| event catalogue, vocabulary, contract extracts | **strict** | consumed blind by Part B; this is where the artefact class lives |
| matrix cell notes, trace text, findings | strict | short, factual, cited |
| question texts and options | STE-flavored | option nuance is load-bearing; do not flatten it |
| methods reference, README | STE-flavored | descriptive text; full strict makes it stilted |
| DR `decision` fields written by the agent | strict | |
| DR `rationale` from the owner | **exempt** | the owner's words are the record; the validator may suggest, never rewrite |
| verbatim quotes (incl. scope-line quotes), code, identifiers, citations | **exempt** | quoted material must stay verbatim by definition |

## Core writing rules (the lintable subset)

1. One instruction per sentence. Keep procedural sentences short (target ≤ 20 words).
2. Use the active voice. Use the imperative for instructions.
3. **One name for one thing.** Do not use two names for one item. The dictionary below is the source of names.
4. Use the short common word: use, help, start, before, after, make sure.
5. Do not stack subordinate clauses. Split the sentence.
6. Lists carry parallel structure.
7. Do not use decoration that carries no meaning (filler adverbs, hedges, chained em-dashes).

## Project dictionary (approved technical names)

STE allows approved technical names beyond its core dictionary. These names are approved for this pack, with one meaning each. Do not paraphrase them — precision beats simplicity when they conflict.

statechart · state · event · transition · guard · disposition (the seven matrix values) · matrix · cell · hole · invariant · NAT (environment assumption) · SYS (system obligation) · doctrine line · episode · fold · seam · provenance · decision record / DR · blind pass · convergent · convergent-hole · divergence · artefact · pass-B-blind-spot · conformance · vector · trace · interaction pair · boundary · clamp · TTL · replay · digest · idempotent · disjoint · coverage · satisfiable · not-formalizable · write-through · remembrance semantics

Add new technical names here before you use them in strict-mode text. Removal or change of a name needs a DR.

## Example (before → after, strict mode)

Before: "Never silently decide ambiguous domain semantics. When behaviour is unclear, contradictory, or unspecified, record it as an open question — do not pick an answer and move on."

After: "Do not decide unclear domain behaviour yourself. If the behaviour is not clear, or two sources do not agree, or no source gives the behaviour: write an open question. Do not select an answer and continue."

## The dictionary check (full STE)

The heart of full ASD-STE100 is a closed core dictionary: about 900 approved general words, each with one approved meaning and part of speech, plus rules for technical names and technical verbs. The checks above are the machine-checkable *rule* subset. They do not contain the dictionary, for two reasons. First, the data: ASD holds the copyright; the specification is issued free of charge on request (asd-ste100.org), but that does not make the word list redistributable inside an MIT repository. Second, the precision limit: a word-presence check cannot verify the approved *sense* or part of speech ("follow" only as "come after"). That judgment stays with the validator agent.

The pack ships the mechanism: obtain the core list yourself, then run `tools/build_ste_dictionary.py --wordlist <file>`. The script merges your list with the project dictionary above and the Pack vocabulary, and writes hunspell files. Enable the check by adding `STEDict` to `BasedOnStyles` for the paths you want gated — it is off by default so the pack works without the data. Every flag means: not in the core list and not a declared technical name. Commercial full-STE checkers (HyperSTE class) exist for certified-grade compliance; this pack does not compete with them.

**Data placement and rebuild.** The data has three roles. (1) The source of truth — the specification PDF and the extracted word lists — lives outside every repository, for example in `~/ste-private/`. It never enters git history, also not in private repos: history is permanent, and a later public switch or contractor access would ship the ASD data with it. (2) The built `ste.dic`/`ste.aff` go into the gitignored dictionaries path of each repo that checks (`styles/config/dictionaries/` in this pack; `tools/prompt-pack/styles/config/dictionaries/` in a consumer repo), or stay central in `~/ste-private/` with per-repo symlinks — Vale reads through symlinks, and ignored files do not make a submodule dirty. (3) The curation file (`technical-name-candidates.txt`) is temporary; its accepted terms become public in the project dictionary above and in `styles/config/vocabularies/Pack/accept.txt` — that is your own vocabulary, not ASD material. After every curation, rebuild: `python3 tools/build_ste_dictionary.py --wordlist ~/ste-private/ste-core-words-issue7.txt` — changes to the vocabulary files do not flow into the dictionary by themselves.

## German adaptation (DTK layer)

The architecture transfers to German without code changes: the checkers are data-agnostic (`check_rules_report.py`, `check_sense_report.py`, `check_rewrite_integrity.py` accept any rules or dictionary JSON), the three language prompts are parametric over their CONFIG paths, and the applicability-map mechanism is language-free. What changes is the data, and one structural point.

Data sources to license privately (same copyright discipline as ASD): the tekom Leitlinie "Regelbasiertes Schreiben — Deutsch für die Technische Kommunikation" is the German rule catalog (stable rule numbers across editions; extract with an adapted `extract_ste_rules.py` into a private rules JSON); DIN 8579 (übersetzungsgerechtes Schreiben) is a second source. The structural difference: German has no closed core dictionary. The dictionary layer becomes a **termbase** in the German tech-writing tradition: preferred terms (Vorzugsbenennungen) as the accept vocabulary, deprecated synonyms as a substitution map, seeded from the project's own glossary or ontology. Lemma level only; the agent handles inflection.

The machinable subset ships as the opt-in Vale style `DTK` (enable per path): Passiv (both German word orders, distance-tolerant), Konjunktiv and Modalverben, Füllwörter substitutions, Satzlänge (20), Nominalstil density, Schachtelsatz (comma count). German-specific rule classes for the agent pass: Satzklammer distance (separable verbs), Funktionsverbgefüge, Komposita over three constituents.

## The experiment (measure, do not assert)

The language policy is a testable claim, not a preference:

1. Baseline exists: run 3 produced 6 Part-B artefact rows, all from catalogue phrasing.
2. Rewrite the catalogue-producing prompt text and the catalogue template to strict mode. Record the lint-score delta.
3. On the next component run, count the Part-B artefact rows again.
4. If the count drops, the policy earned its place — and the numbers go into the case study. If it does not drop, record that too.

## Tooling

Primary enforcement: **Vale** (Go prose linter; the project moved from the errata-ai org to vale-cli). The strictness matrix above is encoded literally in `.vale.ini` as path-scoped sections: strict rules gate `prompts/**` at level `error`, descriptive files get the same rules at `warning`, and `CHANGELOG.md`/`LICENSE` are exempt. The rules live in `styles/STE/` (banned-word substitutions, em dash, sentence length, passive voice, semicolon); the project dictionary feeds `styles/config/vocabularies/Pack/`. Vale ignores code fences and inline code by itself; `<!-- vale off -->` marks record blocks (the pilot changelog). CI gates on errors only (`--minAlertLevel=error`); warnings inform.

Fallback and cross-check: `tools/ste_lint.py`, a zero-dependency Python approximation of the same subset (score = violations per 100 words; the delta is the signal).

Judgment layer: an agent, but grounded and checked, not free-floating. The sense prompt (`prompts/lang-ste-sense.md`) gives the agent the private per-entry dictionary JSON; every verdict must cite an entry key, memory of STE does not count, and `tools/check_sense_report.py` verifies coverage (every lint flag gets a verdict), the verdict enum, and the grounding. That closes one layer no linter can do: approved meaning and part of speech. The second judgment layer is the Part-1 writing-rules pass (`prompts/lang-ste-rules.md`): the agent applies all 53 rules from the private rules JSON (build: `tools/extract_ste_rules.py`), one verdict per rule, coverage-checked by `tools/check_rules_report.py`. Triage principle: a rule that a linter can enforce migrates into a Vale rule and gets the verdict `machine-checked` with the Vale rule name — the first migration is Rule 6.6 (paragraph length) as `STE.ParagraphLength`. Judgment rules (one topic per sentence, correct tense choice, noun-cluster meaning) stay with the agent. The third language prompt closes the loop: `prompts/lang-ste-rewrite.md` rewrites a text into STE with all three layers, grounded substitutions only (entry-listed alternatives, cited), and `tools/check_rewrite_integrity.py` proves that protected content survived: code, identifiers, paths, numbers, URLs, exempt blocks. Strict-class rewrites end at zero Vale errors, measured, not claimed. The applicability decision itself is recorded once, not re-litigated per run: `ste-rules-map.json` holds the owner's verdict per rule (judge / machine-checked / not-applicable, own wording only), the rules prompt inherits it, and the checker verifies the inheritance. Two decisions are marked OPEN in the map: Rule 1.14 (American spelling vs the current British corpus) and Rule 8.1 (STE bans the semicolon; our Vale level is suggestion). Neither layer certifies STE compliance; together they cover presence at machine speed and sense at agent speed, both with executed checks.
