# run2 — kept as recorded

This sidecar (`analysis.json`) predates the schema rule that code citations
carry a `fragment` (CHANGELOG, "Unreleased — type checking and the fragment
rule in the schema"). It is kept as the run recorded it, so `dsc_check` now
fails it on the missing fragments. `run1` and the matrices are unaffected.
