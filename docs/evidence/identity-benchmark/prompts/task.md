Run a bounded analysis, not a full pilot. Scope: deferred completion, accounting,
callbacks and lifecycle interactions in SOURCE. Read README.md and SOURCE in full.
Do not create a matrix, Part B or a to-be model. Do not modify existing files.
Write new artifacts under analysis/ and behavioral tests as analysis/_probe/*.go
using a Go overlay to inject them into the root package. Use only public API for
assertions. Do not read other repositories, old reports or benchmark answers.
Use only the pilot command tool. Full outputs are retained: use read-log LOGID
lines START END (at most 100 lines) or page continuations when needed.

First run one finding-neutral draft-verify on SOURCE using a general extraction
request, max-tokens 12000, model jev-1.14.0. Use python3
../pack/tools/local_models.py --ledger ../routing.sqlite for all routing calls.
Read and review every draft question and source-backed claim; drafts do not bound
your own pass. Then save analysis/initial.json BEFORE executing your probes.
Use exactly this report shape for initial.json and final.json:
{"findings":[{"id":"F01","initial":"starting condition","steps":["ordered step"],
"outcome":"actual observable effect", "citation":{"file":"SOURCE","line":1,
"fragment":"exact single source line"}, "test":"TestName or untested",
"question":"open intent question or source-backed contract explanation"}]}
Keep distinct consequences explicit even if questions are grouped. Include relevant
negative controls and source-backed limits. Do not invent intent or claim a probe
ran when it did not. Do not force a fixed number of findings.

Execute the probes with go test -race -count=3 -timeout=30s -json -overlay PATH
-run '^TestIdentity' . ; capture stdout/stderr under analysis/. Require nonzero
actual test discovery. Preserve every failed attempt and repair within this run.
Use exact test names starting TestIdentity in the report. Then perform one Jev
batch against SOURCE for the independently testable final claims (type claim,
statement, citation:{file,line,fragment}, id), model jev-1.14.0. Inspect actual CLI
schema via --help or source if needed. Jev proposes, you review; never rerun an
answered check to obtain a preferred answer. Preserve all responses and explain
each draft disposition and any changed claim in analysis/review.md.
Write final.json, run python3 validate_report.py analysis/initial.json
analysis/final.json, correct structural/fragment errors and re-run when necessary.
Write analysis/summary.md with actual checks and remaining limitations. Keep all
files and raw logs. Do not expand this into a full pilot. Finish within 900 seconds.
