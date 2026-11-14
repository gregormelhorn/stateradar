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
