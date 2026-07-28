# STE Sense Check — Agent Prompt (language layer)

**How to use:** this prompt closes the layer that no linter can do: approved meaning and part of speech. It needs the private dictionary JSON (see STYLE.md, "Data placement"). Fill in CONFIG. Then paste this file into your agent at the repository root. The pack does not ship the dictionary data.

## CONFIG — fill in before running

```text
Dictionary JSON:      <path, e.g. ~/ste-private/ste-dictionary-issue7.json>
Target files:         <files to examine>
STEDict lint output:  <file with `vale --output=line` results, or "none">
Report output:        ste-sense-report.json
```

---

## PROMPT

You examine text against the STE dictionary at the sense level. The dictionary JSON is your only source. You judge usage, not presence.

### Hard rules

1. Ground every verdict in a dictionary entry. Read the entry from the JSON and cite its key. Do not use memory of STE. If no entry exists and the word is no declared technical name: write `needs-human`.
2. Cover everything. Every word in the lint output gets exactly one verdict. In addition, examine every verb in the target sentences: when the entry gives a restricted meaning, give a verdict.
3. Verdicts come from this list only: `ok | wrong-sense | wrong-pos | unapproved | technical-name-candidate | covered-by-project-dictionary | needs-human`.
4. Propose a rewrite for `wrong-sense`, `wrong-pos`, and `unapproved`, with the entry's listed alternative. Do not rewrite owner rationales or verbatim quotes (STYLE.md exemptions).
5. A domain word that the project dictionary declares gets `covered-by-project-dictionary`. A domain word that it does not declare, but that the domain needs, gets `technical-name-candidate` with a one-line note. The owner decides on admission.

### Procedure

1. Read the lint output. For each flagged word: look up `WORD (pos)` for each part of speech. Give the verdict and, where rule 4 applies, the rewrite.
2. Make a sentence pass over the target files. For each verb in use: look up its entry. When the approved meaning does not match the use in the sentence (example: FOLLOW is approved only as "to come after"): verdict `wrong-sense`, with the alternative from the entry.
3. Write `ste-sense-report.json`: a `findings` list with `word, file, line, usedAs, verdict, entryKey, entrySnippet` (8 words maximum), optional `rewrite` and `note`, plus a `summary` with counts per verdict.
4. Run `tools/check_sense_report.py <report> <lint output> <dictionary JSON>` and include its output. Deliver checks as executed code, never as claims.
