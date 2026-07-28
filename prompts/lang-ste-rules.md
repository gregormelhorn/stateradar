# STE Rules Check — Agent Prompt (language layer)

**How to use:** this prompt applies the Part-1 writing rules that no linter can do. It needs the private rules JSON (see STYLE.md, "Data placement"; build it with `tools/extract_ste_rules.py` from your licensed copy). Fill in CONFIG. Then paste this file into your agent at the repository root. The pack does not ship the rule texts.

## CONFIG — fill in before running

```text
Rules JSON:      <path, e.g. ~/ste-private/ste-rules-issue7.json>
Applicability map: <path, default ste-rules-map.json | none>
Target files:    <files to examine>
Scope:           <full | sample: list of rule ids>
Report output:   ste-rules-report.json
```

---

## PROMPT

You examine text against the STE writing rules. The rules JSON is your only source. You apply each rule as its text states it, not as you remember it.

### Hard rules

1. Ground every verdict in a rule: read the rule from the JSON and cite its id. Memory of STE does not count. If a rule is not clear for this text type: write `needs-human` with the open point.
2. Cover the declared scope. Under `full`, every rule id in the JSON gets exactly one verdict. Under `sample`, declare the subset in the report and cover it completely.
3. Verdicts come from this list only: `compliant | violation | not-applicable | machine-checked | needs-human`. Use `machine-checked` when a Vale rule already covers the rule; name that Vale rule. Use `not-applicable` with a reason (example: the safety-instruction rules apply to maintenance documents, not to prompts).
4. Each violation carries `file, line`, a quote of eight words maximum, and a rewrite when the rule gives a mechanical alternative.
5. When an applicability map is given: inherit its `not-applicable` and `machine-checked` verdicts verbatim, with the map's reason, and cite the map. Judge only the rules the map marks `judge`. Do not overrule the map; when you disagree, add a `note` and keep the map's verdict. The map is the owner's recorded decision.
6. Report format (`ste-rules-report.json`): `scope`, a `rules` list with `{ruleId, verdict, valeRule?, findings?: [{file, line, quote, rewrite?}], reason?}`, and a `summary` with counts. Run `tools/check_rules_report.py <report> <rules JSON> [map]` and include its output. Deliver checks as executed code, never as claims.

### Procedure

1. Read the rules JSON. Under `sample`, keep only the declared ids.
2. Classify each rule first: does a Vale rule already enforce it? Then `machine-checked` with the rule name. Is it out of scope for this text type? Then `not-applicable` with the reason.
3. Apply the remaining rules to the target files, sentence by sentence where the rule works at sentence level, paragraph by paragraph where it works at paragraph level.
4. Write the report. Run the checker.
