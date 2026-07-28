# STE Rewrite — Agent Prompt (language layer)

**How to use:** this prompt turns a text into STE-conform text. It uses the three layers together: the Vale rules, the private dictionary JSON, and the rules JSON with the applicability map. The checkers verify the result. The pack does not ship the data. Fill in CONFIG. Then paste this file into your agent at the repository root.

## CONFIG — fill in before running

```text
Target files:            <files to rewrite>
Text class:              <strict | flavored>   (STYLE.md matrix)
Dictionary JSON:         <path | none>
Rules JSON:              <path>
Applicability map:       <path, default ste-rules-map.json>
Output:                  <in-place | sibling file *.ste.md>
Extra protected tokens:  <path | none>
Max rounds:              <default 3>
```

---

## PROMPT

You rewrite text into STE. You keep the meaning. You prove the result with the checkers.

### Hard rules

1. Do not change meaning. When a rewrite would change meaning: keep the sentence and record `needs-human` with the problem.
2. Protected content stays verbatim: code spans and code blocks, identifiers (`DR-*`, `Q-*`, `GG-*`, `UV-*`, `P-*`, `SYS-*`, `NAT-*`), file paths, numbers, URLs, literal format tokens, `<!-- vale off -->` blocks, owner rationales, and quoted material (the STYLE.md exemptions). `tools/check_rewrite_integrity.py` verifies this. A failed integrity check voids the round.
3. Ground each word substitution in the dictionary: an unapproved word gets the entry's listed alternative; a wrong sense gets the entry's alternative for that sense. Cite the entry key in the report. When no listed alternative fits: restructure the sentence (Rule 9.1) and record the sentence pair.
4. Do not paraphrase domain terms away. A domain word that the project dictionary declares stays. A domain word that it does not declare gets a `technical-name-candidate` note, not a forced paraphrase. Precision beats simplicity.
5. Deliver measurements, not claims: baseline and final linter numbers go into the report. For the strict class, the end state is zero Vale errors.

### Procedure

1. **Baseline.** Run Vale (with `STEDict` when the dictionary exists) and `python3 tools/ste_lint.py` on the targets. Record the numbers.
2. **Mechanical round.** Apply the Vale substitutions. Split long sentences. Remove em dashes and semicolons per the rules. One instruction per sentence.
3. **Dictionary round.** Resolve every `STEDict` flag per hard rules 3 and 4. Make the sense corrections: part of speech, approved meaning.
4. **Rules round.** Apply the `judge` rules from the map: noun clusters, `-ing` forms, phrasal verbs, paragraph splits, tense structure.
5. **Verify.** Re-run the linters and `tools/check_rewrite_integrity.py <original> <rewritten>`. Not clean: do the next round, up to the CONFIG maximum. Then write `ste-rewrite-report.json`: metrics before and after, substitutions with entry keys, restructured sentence pairs, technical-name candidates, `needs-human` items, and every checker output.
