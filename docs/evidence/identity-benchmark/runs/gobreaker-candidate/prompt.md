### Hard rules

1. Do not modify any source code, tests, or configuration. Your only outputs are the analysis files listed below, in the configured output directory.
<!-- rule:R-NO-SILENT-DECISIONS -->
2. Do not decide unclear domain behaviour yourself. If the behaviour is not clear, or two sources do not agree, or no source gives the behaviour: write an open question. Do not select an answer and continue. Label your recommendations `proposed`, never as fact. To call a gap "benign" is such a decision. Benignity may appear as a proposal inside a question. It is never a reason to omit the question.
3. Every claim about existing behaviour carries provenance: `explicit-requirement` (cite the document), `observed-in-code` (cite file:line), `observed-in-tests` (cite file:line), `inferred` (state the inference), or `proposed` (yours). A claim without provenance is at best `inferred`. An `observed-in-code` or `observed-in-tests` citation carries a short verbatim fragment: `file:line ("fragment")`. Checkers verify the fragment near that line.
<!-- rule:R-REQUIREMENT-SCOPE-a -->
4. **Requirement-scope rule.** A citation covers only the scenario that the cited text describes. If you apply a requirement, doc line, or recorded decision to an ordering, race, or variant it does not address: downgrade the provenance to `inferred` and treat the cell as a hole candidate. Written down is not the same as decided for this case.
5. Model what the code does, not what it should do. The desired design comes later, after a human resolves the open questions. Do not produce a to-be model in this run.
6. The component may have no real temporal behaviour: no lifecycle, no asynchronous events, no retries, no timeouts, no cancellation. In that case say so, explain briefly, and stop. A negative result is a valid result.


For cancellation and teardown, follow the operation past the caller's
departure. Compare no later input with a later matching input. Track
where a delivered value goes when its caller has stopped waiting.
For each callback that can meet a lifecycle boundary, examine success
and failure on both sides of the boundary. Cite the lock or other
guarantee for impossible orderings. For reachable orders, follow the
result through retries, captured references, cleanup and any skipped
effect. Keep the distinct orders even when one event column groups
the callback outcomes. An applicable probe can also satisfy the
systematic or free-probe requirement above.


### Step 8 — Finding verification (mandatory, after open questions)

Re-read every bug claim, invariant violation, and lint finding against
the code with heightened scrutiny. The pilot writes claims quickly; this
step verifies them carefully before the matrix is finalized.

1. **Concurrency claims.** Every finding that asserts a race condition,
   lost update, or silent failure must cite the actual memory ordering
   or synchronization primitive — `Acquire`/`Release`, `SeqCst`, mutex
   lock site. If the ordering guarantees correctness, the finding is NOT
   a bug. Downgrade to a documentation question or drop it.

2. **Sentinel values.** A sentinel that is a literal constant (`-1.0`)
   is safe. A sentinel that is the result of a computation is fragile.
   Check which one applies. Reclassify accordingly.

3. **Line-number accuracy.** Re-read every cited `file:line`. Does the
   code at that line actually do what the finding claims? Off-by-one
   citations or misread logic must be corrected before the matrix is
   finalized. Split a compound finding into independently testable claims
   while keeping the conditions and event order each claim depends on. For
   example, “Cancel clears the timer and emits a diagnostic” requires a
   separate check for each effect. With model routing on, batch one
   `claim` per part against its cited source file and keep the separate
   verdicts linked to the original finding. A supported part cannot supply
   evidence for another part. Review each part and preserve unresolved
   questions before deciding what the combined finding supports.

4. **Severity recalibration.** For each finding: is this a bug
   (incorrect behavior), a design observation (correct but surprising),
   a documentation gap (correct but undocumented), a runtime concern
   (`unverifiable-runtime`: depends on `sys.exc_info()`, traceback chaining,
   GC, or memory model — outside statechart scope, requires separate test),
   or an API contract issue (wrong return value, not wrong transition)?
   Reclassify. A lock-free CAS that silently drops a transition is correct
   design, not a bug — the ring buffer already recorded the contribution.

Update the open questions, matrix dispositions, and summary to reflect
any reclassifications. A finding downgraded from bug to documentation
gap stays in `open-questions.md`; a finding that was simply wrong is
removed with a note in the summary.

→ (no new file — updates existing artifacts)

---

<!-- rule:R-PART-B -->

For each deferred callback, handle or stored reference, trace identity from
creation to use. Distinguish a copied value, a captured object and a lookup
through a mutable wrapper or key. Identify which reference is read at invocation.
Where the public boundary permits it, compare copying, replacement or reassignment
between creation and invocation with the unchanged case. Follow the result to
the actual recipient, including admission, counters, generation checks and cleanup.
Do not treat a generation number alone as proof of object identity. State the
starting objects, ordered operations and observable outcome; cite capture and
use sites. Probe material claims through the public seam. A general mention of
copying or replacement does not cover an untraced effect. If a documented contract
excludes an ordering, cite that contract; if intent is silent, retain an open
question. Do not infer that copying is supported, or invent a defect when the
captured value or an identity check prevents redirection.

Run a bounded analysis, not a full pilot. Scope: deferred completion, accounting,
callbacks and lifecycle interactions in gobreaker.go. Read README.md and gobreaker.go in full.
Do not create a matrix, Part B or a to-be model. Do not modify existing files.
Write new artifacts under analysis/ and behavioral tests as analysis/_probe/*.go
using a Go overlay to inject them into the root package. Use only public API for
assertions. Do not read other repositories, old reports or benchmark answers.
Use only the pilot command tool. Full outputs are retained: use read-log LOGID
lines START END (at most 100 lines) or page continuations when needed.

First run one finding-neutral draft-verify on gobreaker.go using a general extraction
request, max-tokens 12000, model jev-1.14.0. Use python3
../pack/tools/local_models.py --ledger ../routing.sqlite for all routing calls.
Read and review every draft question and source-backed claim; drafts do not bound
your own pass. Then save analysis/initial.json BEFORE executing your probes.
Use exactly this report shape for initial.json and final.json:
{"findings":[{"id":"F01","initial":"starting condition","steps":["ordered step"],
"outcome":"actual observable effect", "citation":{"file":"gobreaker.go","line":1,
"fragment":"exact single source line"}, "test":"TestName or untested",
"question":"open intent question or source-backed contract explanation"}]}
Keep distinct consequences explicit even if questions are grouped. Include relevant
negative controls and source-backed limits. Do not invent intent or claim a probe
ran when it did not. Do not force a fixed number of findings.

Execute the probes with go test -race -count=3 -timeout=30s -json -overlay PATH
-run '^TestIdentity' . ; capture stdout/stderr under analysis/. Require nonzero
actual test discovery. Preserve every failed attempt and repair within this run.
Use exact test names starting TestIdentity in the report. Then perform one Jev
batch against gobreaker.go for the independently testable final claims (type claim,
statement, citation:{file,line,fragment}, id), model jev-1.14.0. Inspect actual CLI
schema via --help or source if needed. Jev proposes, you review; never rerun an
answered check to obtain a preferred answer. Preserve all responses and explain
each draft disposition and any changed claim in analysis/review.md.
Write final.json, run python3 validate_report.py analysis/initial.json
analysis/final.json, correct structural/fragment errors and re-run when necessary.
Write analysis/summary.md with actual checks and remaining limitations. Keep all
files and raw logs. Do not expand this into a full pilot. Finish within 900 seconds.
