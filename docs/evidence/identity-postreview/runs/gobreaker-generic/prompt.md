Run a bounded final review of an existing analysis, not a new full pilot.
Read gobreaker.go and README.md in full, analysis/initial.json, the preserved probes,
and baseline/open-questions.md. The baseline is evidence, not authority. Review
its conditions, ordered consequences, citations, test scope and unresolved intent.
Identify material omissions or unsupported claims. Do not decide domain policy.

Use only the pilot command tool. Read retained output with read-log LOGID lines
START END (at most 100 lines) or page continuations when needed. Never read other
repositories, benchmark answers, or previous experiment results.

Preservation is mandatory: copy every finding in analysis/initial.json exactly
into analysis/final.json, with the same IDs, fields, steps and open questions.
Append genuinely additional findings using N01, N02, etc. Do not replace existing
findings with new grouping or wording. If an old claim is wrong or too broad,
retain its historical row and explicitly qualify or contradict it in the separate
analysis/supplement.json; preservation is not an endorsement. Never silently fix
or drop a finding. Do not edit source, existing tests, baseline/, initial.json,
analysis/_probe/, analysis/overlay.json, validator scripts or immutable.json.

New finding rows use the same shape as the baseline:
{"id":"N01","initial":"starting condition","steps":["ordered step"],
"outcome":"observable effect","citation":{"file":"gobreaker.go","line":1,
"fragment":"exact source line"},"test":"TestIdentityName or untested",
"question":"open intent question or cited contract explanation"}.
Supplement shape:
{"qualifications":[{"id":"F01","status":"qualified or contradicted",
"rationale":"precise limitation or correction","citation":{"file":"gobreaker.go",
"line":1,"fragment":"exact source line"}}],
"test_bindings":[{"id":"F01 or N01","test":"TestIdentityName",
"scope":"exact ordered claim this additional probe establishes"}]}.
Either list may be empty. All original questions remain open unless requirements
actually resolve them; document newly raised questions in the added findings.

Perform one bounded Flash draft-verify review of gobreaker.go, using a task file that
asks for source-grounded gaps or qualifications relevant to this final review.
Use python3 ../pack/tools/local_models.py --ledger ../routing.sqlite draft-verify
gobreaker.go TASKFILE --output analysis/draft-verify.json --max-tokens 12000 --model
jev-1.14.0. Review every returned claim/question against source. Drafts never bound
the review. Retain raw provider results. Do not repeat an answered judgment to
obtain a preferred answer. Make one final Jev batch for material added/qualified
claims and the new probe's identity premise, with the actual CLI schema:
[{"id":"C1","kind":"claim","statement":"one testable assertion",
"line":1,"fragment":"exact single source line of at least four characters"}].
Command: python3 ../pack/tools/local_models.py --ledger ../routing.sqlite
jev-batch gobreaker.go CHECKSFILE --model jev-1.14.0 --output analysis/final-jev.json.
Jev results are proposals: explain disagreements rather than changing observed
behavior to match a verdict. Keep existing source-backed negatives and limits.

Add new public-seam probes under analysis/_postprobe/. Extend the provided
analysis/overlay.json into analysis/overlay-final.json without removing or
replacing any existing overlay entry. Inject only new root *_test.go files.
Execute all old and new probes with go test -race -count=3 -timeout=30s -json
-overlay analysis/overlay-final.json -run '^TestIdentity' . ; retain stdout/stderr
for every attempt. No skipped tests or zero discovery. Never weaken a failing
test. Preserve failures, investigate them, and report observed limitations.

Probe material additional findings through the public API; preserve all existing probes.

Save analysis/final.json and analysis/supplement.json. Run python3
validate_postreview.py and resolve structural/preservation failures without
altering the immutable baseline. Write analysis/review.md explaining draft
dispositions, new or qualified findings, actual probe results, remaining work and
limits. Write analysis/summary.md. This is a final review, not a matrix, Part B,
runtime change or policy decision. Finish within 900 seconds.
