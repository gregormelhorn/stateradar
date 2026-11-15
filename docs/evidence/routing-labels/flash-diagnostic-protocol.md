# Post-comparison Flash → Jev diagnostic

Declared after the original Jev/direct results were inspected. These four
components and labels are therefore already consumed; this is exploratory and
is not an untouched held-out result or full-pilot comparison. Run the existing
`draft_verify` implementation once per component with the same source and the
same prewritten source-fragment checks, but no reference labels or reviews.
Do not change prompts, sources, labels or thresholds during this diagnostic.

Task: for each check, if the exact cited fragment supports the exact statement,
return the unchanged id, kind, statement, line and fragment as a claim;
otherwise preserve it as an open question prefixed by its id. The tool's normal
citation check and Jev verification run. No output is automatically accepted.
Every changed, duplicated, missing, malformed, unverified, or ambiguous item is
retained and counted separately; a question is not equated to contradicted or
unclear. The supporting-case coverage and non-supported suggestions can be
compared descriptively to direct Codex's supported choices, with the different
output contracts explicit. Jev's verdict on a proposed claim remains advisory.

Use one new $2 ledger, four calls maximum to draft_verify, no semantic retries,
model jev-1.14.0. Preserve the returned parsed claims, questions, judgments,
usage, citations, provider ledger and failure status. On successful requests the
existing tool does not retain the original Flash response bytes or raw HTTP
response; do not claim that it does. Include both provider costs, elapsed time,
and all missing or unsettled usage. Controller/supervisor costs are not metered.
No automatic label or domain decision follows from this diagnostic.
