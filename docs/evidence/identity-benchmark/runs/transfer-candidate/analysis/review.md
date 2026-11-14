# Finding verification

Scope is serialized public operations under README.md:3–6 (explicit-requirement). README.md:7–8 leaves outstanding completion policy undecided (explicit-requirement). The ordered sequences here set up public fields between calls. No ordering is excluded by a lock. The relevant completion bodies are component.go:10 ("return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }"), component.go:15 ("return func() { target.Successes++ }"), component.go:20 ("return func() { if p.Target == target && target.Epoch == epoch { target.Successes++ } }"), component.go:24 ("return func() { if target := r.Entries[key]; target != nil { target.Successes++ } }"), component.go:28 ("return func() { p.Target.Successes++ }"), component.go:33 ("return func() { target.Successes++ }") (observed-in-code). None uses a synchronization primitive. There is no claim of concurrent lost updates, a race, or a numerical sentinel. The captured epochs are integer field values compared for equality in component.go:9 ("epoch := p.Target.Epoch"), component.go:10 ("return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }"), component.go:18 ("target, epoch := p.Target, p.Target.Epoch") and component.go:20 ("return func() { if p.Target == target && target.Epoch == epoch { target.Successes++ } }") (observed-in-code).

## Neutral draft review

The draft ran before the initial report and probes. Its 13 claims and 22 questions are preserved in [draft-verify.json](draft-verify.json). The independent source pass and then the probes added orderings beyond the draft.

| Draft claim | Disposition |
| --- | --- |
| C1 | Retain A's immediate admission increment with component.go:8 ("p.Target.Requests++") in F31. |
| C2 | Split the copied epoch at component.go:9 ("epoch := p.Target.Epoch") from the completion comparison and recipient at component.go:10 ("return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }"). F01–F06 establish current-target behavior and F07–F08 distinguish pointer and value copies. |
| C3 | Retain separate capture and admission claims at component.go:13 ("target := p.Target") and component.go:14 ("target.Requests++") in F09 and F31. |
| C4 | Retain B's saved-pointer success increment at component.go:15 ("return func() { target.Successes++ }") in F09 and F12. |
| C5 | The draft verdict was unclear. Capture is at component.go:18 ("target, epoch := p.Target, p.Target.Epoch") and the request increment is at component.go:19 ("target.Requests++"). Retain both with separate final checks F16-capture and F31-C. |
| C6 | Retain the pointer check and captured epoch value comparison at component.go:20 ("return func() { if p.Target == target && target.Epoch == epoch { target.Successes++ } }") in F15–F20. The epoch comparison is conditional on the pointer check. |
| C7 | Retain D's admission lookup and increment at component.go:23 ("r.Entries[key].Requests++") in F31 and F34. |
| C8 | Retain the second lookup and nil guard at component.go:24 ("return func() { if target := r.Entries[key]; target != nil { target.Successes++ } }") in F21–F30. Different nil and replacement orders have separate rows. |
| C9 | Retain E's value receiver at component.go:26 ("func (p Port) E() func() {"). The closure reads the copy's pointer field at component.go:28 ("return func() { p.Target.Successes++ }"), so it refers to the same account as at admission. F10 and F13 distinguish this from copying the account value. |
| C10 | Retain E's admission increment at component.go:27 ("p.Target.Requests++") in F31. |
| C11 | Retain E's success write through the copied receiver at component.go:28 ("return func() { p.Target.Successes++ }") in F10 and F13. |
| C12 | Retain separate F capture and admission claims at component.go:31 ("target := p.Target") and component.go:32 ("target.Requests++") in F11 and F31. |
| C13 | Retain F's saved-pointer success increment at component.go:33 ("return func() { target.Successes++ }") in F11 and F14. |

All retained draft behaviors above are observed-in-code. Draft questions were reviewed individually in their original order.

| Draft question | Disposition |
| --- | --- |
| 1 | Observed current target at invocation in F02–F03. The desired policy stays in Q1. |
| 2 | Observed separate accounts for the request and success in F02. Intent stays in Q1. |
| 3 | Split nil admission F33 from nil completion F06 and recovery F36. Questions Q2 and Q4. |
| 4 | Retained as Q1 for B, with F09 and F12. |
| 5 | Retained as Q4 after observing the admission panic in F33. |
| 6 | Retained as Q1 and Q2, after observing pointer restoration in F19. |
| 7 | Split nil admission F33 and nil completion F18. Questions Q2 and Q4. |
| 8 | Resolved the factual read ordering from the short-circuit guard at component.go:20 ("return func() { if p.Target == target && target.Epoch == epoch { target.Successes++ } }"). The epoch expression runs only if pointer equality passes. The desired guard remains in Q1 and Q2. |
| 9 | Retained as Q4 after observing separate D admission panics in F34. |
| 10 | Split replacement credit F22 from deletion and other skips F23–F26. Questions Q1 and Q2. |
| 11 | Retained as Q1. F22 observes request and success on different accounts. |
| 12 | README.md:5–6 sets the serialized scope explicitly. Concurrent mutation is outside this run. |
| 13 | Retained as Q1 after observing E's copied receiver in F10 and F13. |
| 14 | Retained as Q4 after observing E's nil-account admission panic in F33. |
| 15 | Retained as Q1 after observing F's saved pointer in F11 and F14. |
| 16 | Split nil target F33 from nil port F35. Both are Q4. |
| 17 | README.md:5–6 sets the scope. F31 verifies admission and deferral per API. Q3 preserves the open accounting policy for subsequent calls. |
| 18 | README.md:5–6 answers the scope of this run. No concurrency-support guarantee is claimed for any API. |
| 19 | Retained as Q2. F02 and F16 are separate positive and negative controls with equal epoch values. |
| 20 | Retained as Q1. F09–F14 establish current behavior without assigning a design purpose to the APIs. |
| 21 | Retained as Q2 with no external epoch-management policy assumed. |
| 22 | Retained as Q3. F31, F32 and F37 separate the admission increment, late delivery, and no delivery. |

## Final claim checks

The one final Jev batch returned 54 supported and 25 unclear verdicts. [The submitted checks](final-claims.json) and [all returned verdicts](final-jev.json) are preserved. The CLI takes `kind`, `line` and `fragment` as flat fields. The submitted records also carry the requested `type` and nested `citation`. Each finding ID prefixes its additional checks. The ordered steps in the final report specify the conditions where the check text is terse.

- F02's main batch entry combined the replacement increment and original-account non-increment. F02-original checked the latter separately. I verified the replacement increment independently against component.go:10 ("return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }") and analysis/_probe/identity_test.go:41 ("counters(t, b, 0, 1)"). The original-account result is independently asserted at analysis/_probe/identity_test.go:40 ("counters(t, a, 1, 0)"). I retained the original batch and used the two assertions to review the effects separately.
- F05 and F08 retain the probe-backed outcomes. The condition at component.go:10 ("return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }") reads the target at invocation time. The tests produce the matching epoch by restoration and by copying the account before overwriting the original port, respectively. F06 uses the same read with nil. The probe observes a panic, and the exact field expression explains where the panic occurs. F36 checks recovery and a later matching call separately.
- F16, F18, F19 and F20 retain the probe-backed outcomes under component.go:18 ("target, epoch := p.Target, p.Target.Epoch") and component.go:20 ("return func() { if p.Target == target && target.Epoch == epoch { target.Successes++ } }"). The account value copy has a different pointer. A current nil pointer differs from the nonnil captured pointer and stops evaluation of the second operand. Restoring the pointer or restoring the epoch value satisfies both comparisons on the later invocation. The skip and later credit have separate counter assertions.
- F21 and F40-before retain the unchanged-key credit under component.go:23 ("r.Entries[key].Requests++") and component.go:24 ("return func() { if target := r.Entries[key]; target != nil { target.Successes++ } }"). F26 through F29 retain the distinct outcomes of deletion then reinsertion, map replacement, caller-pointer rebinding, and shared map mutation. The lookup site is identical across these orders. F28-capture verifies the receiver type separately from the invocation behavior. The probes supply each mutation and assert both recipient counters.
- F34-missing, F34-nil-map and F35 retain their independently probed input failures. Evaluating the D admission increment at component.go:23 ("r.Entries[key].Requests++") dereferences the nil account yielded by either lookup. F reads through the nil port argument at component.go:31 ("target := p.Target"). These probes assert a panic and do not depend on a particular panic message.
- F37 and F37-B through F37-F retain the no-delivery result from the six public probes and the distinct admission/deferred-body checks F31 through F31-F-deferred. Admission lines establish the increment only. The test supplies teardown and the absence of delivery, then checks both counters. F38 tests both accounts before and after replacement and retains its later credit under component.go:10 ("return func() { if p.Target.Epoch == epoch { p.Target.Successes++ } }").
- For supported verdicts, the source reread keeps the exact guard operands, field accesses, and saved values. F03–F04 and F17 each exercise one failing guard condition. F07, F09–F15, F22–F25 and F30 distinguish wrapper identity, account identity and lookup semantics. F31–F33 preserve individually checked admission, success deferral, repeated invocation and nil-account behavior for each applicable API. F34's general nil-lookup result is supplemented by the tested variants above. F39 and F40 use independent first and second invocation checks. The capture checks establish binding and value selection only. The counter assertions establish the concrete effect under the ordered inputs.

## Changes after probing and severity

- F07 makes the original receiver explicit. F08 names the copied account as a distinct object created after admission and records the inherited Requests count. F16 and F19 align the initial condition with the concrete field-identical copy used by the probe.
- F21 adds the D capture and admission sites. F32 clarifies that the fixture simulates caller departure. F34 names three separate fixtures for the nil lookup cases.
- F36 adds the successful invocation after nil panic recovery and target restoration. F37 adds a separate no-delivery teardown control. F38–F40 record delivery on both sides of replacement, including the skipped second effect for C.
- All final rows add test provenance from the completed probes. The initial report stays unchanged as the pre-probe record.
- The findings are observed behaviors with open intent questions. Redirected or repeated accounting and skipped increments are design or documentation questions under README.md:7–8. Nil admission and nil completion panics are API contract questions. No behavior is classified as a confirmed bug, and no bug claim was removed as disproven. No GC timing or race conclusion is drawn from the probes.
