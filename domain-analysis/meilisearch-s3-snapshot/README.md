# meilisearch-s3-snapshot — sidecar kept as recorded

This sidecar (`analysis.json`) predates the schema rule that code citations
carry a `fragment` (CHANGELOG, "Unreleased — type checking and the fragment
rule in the schema"). It is kept as recorded, so `dsc_check` now fails it on
the missing fragments. Regenerate it from a fragment-cited matrix before
checking it again.
