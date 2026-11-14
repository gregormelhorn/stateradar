# Review

The review covers the 34 lines of `component.go` and the eight lines of `README.md`. The README describes admission and completed-success accounting and limits the exercise to serialized public operations. It leaves outstanding-completion policy open. That requirement does not choose an outcome for replacement, epoch change, detach, repeat invocation, or abandonment. `explicit-requirement` — README.md:3–8.

## Draft claims

The retained draft has 16 claims with valid fragments, 15 Jev-supported results, and one unclear result. Each disposition below follows a direct reread. Claim IDs refer to `draft-verify.json`.

- **C1** — Kept as the admission increment and timing. `observed-in-code` — component.go:8 ("p.Target.Requests++").
- **C2** — Kept as the numeric epoch capture. `observed-in-code` — component.go:9 ("epoch := p.Target.Epoch").
- **C3** — Kept for non-nil live targets. The condition reads the live account's epoch, and success goes to the live account. A nil live account panics at the condition. `observed-in-code` — component.go:10 ("if p.Target.Epoch == epoch { p.Target.Successes++ }").
- **C4** — Split into pointer assignment and request increment. The original line establishes the assignment. C5 independently supplies the accounting part. `observed-in-code` — component.go:13 ("target := p.Target") and component.go:14 ("target.Requests++").
- **C5** — Kept as B's separate admission increment. `observed-in-code` — component.go:14 ("target.Requests++").
- **C6** — Kept for callbacks obtained from successful admission. B applies the increment to the admitted object even after a later rebinding, detachment, or epoch edit. `observed-in-code` — component.go:13 ("target := p.Target") and component.go:15 ("target.Successes++").
- **C7** — Kept for valid admission. The same source line also establishes the nil-target dereference that precedes the request increment. `observed-in-code` — component.go:18 ("target, epoch := p.Target, p.Target.Epoch").
- **C8** — Kept as C's admission increment after capture. `observed-in-code` — component.go:19 ("target.Requests++").
- **C9** — Kept. Pointer and epoch are independently necessary. The pointer comparison runs first, so after valid admission a nil live target short-circuits the epoch comparison. `observed-in-code` — component.go:18 ("target, epoch := p.Target, p.Target.Epoch") and component.go:20 ("p.Target == target && target.Epoch == epoch").
- **C10** — Kept for a non-nil key occupant. The request expression dereferences the lookup result during admission. `observed-in-code` — component.go:23 ("r.Entries[key].Requests++").
- **C11** — Kept. The callback lookup targets the admitted key in the current map, and the increment is guarded by the result's non-nil check. `observed-in-code` — component.go:24 ("if target := r.Entries[key]; target != nil { target.Successes++ }").
- **C12** — Split the unclear compound claim. Line 26 establishes the receiver kind and line 27 the admission increment. The final batch supported those independently. `observed-in-code` — component.go:26 ("func (p Port) E() func() {") and component.go:27 ("p.Target.Requests++").
- **C13** — Kept with receiver-signature evidence. The copy contains the pointer to the same Account. The public probe changes the external Port values and checks the account that receives the increment. `observed-in-code` — component.go:26 ("func (p Port) E() func() {") and component.go:28 ("p.Target.Successes++"). `observed-in-tests` — analysis/_probe/identity_test.go:320 ("counters(t, b.original, 1, 1)").
- **C14** — Split pointer assignment from accounting. Line 31 establishes capture. C15 independently supplies the increment. `observed-in-code` — component.go:31 ("target := p.Target") and component.go:32 ("target.Requests++").
- **C15** — Kept as F's separate admission increment. `observed-in-code` — component.go:32 ("target.Requests++").
- **C16** — Kept for callbacks obtained from successful admission. `observed-in-code` — component.go:31 ("target := p.Target") and component.go:33 ("target.Successes++").

## Draft questions

The numbers below follow the draft's array order. The linked IDs refer to [open-questions.md](open-questions.md).

1. **A's epoch and reassignment** — Kept as Q1 and Q2. Separate same-epoch and different-epoch replacements from an epoch edit on the original account.
2. **A versus C on reassignment** — Kept under Q1 and Q3. The observed distinction warrants a policy question for each operation.
3. **D's absent or nil admission** — Kept under Q8. Included missing key, nil entry, and nil map separately in the probe and atomic checks.
4. **D's replacement accounting** — Kept under Q5 and Q9. Included key reuse, whole-map replacement, and an unrelated-key control.
5. **E's value receiver and caller rebind** — Kept under Q4. Reviewed the receiver signature separately from the callback effect.
6. **B and F after target or epoch changes** — Kept under Q4. Added E as a separately evidenced variant with the same accounting effect in those orders.
7. **Admission with no completion and one-to-one accounting** — Kept under Q6 and Q7. Tested no invocation and independently tested repeat invocation; the two effects get separate checks.
8. **Ordering and invocation-time attribution** — Kept across Q1–Q5 and Q9. Replaced the general wording with serialized orderings and concrete counter attribution.
9. **Concurrent or repeat invocation** — Split by scope. Q6 retains serialized repeat invocation. Concurrent unsynchronized writes are outside the explicit fixture scope (README.md:5–6).
10. **Nil Port.Target** — Kept under Q8. Distinguished admission from detachment after valid admission, and distinguished panic from a normal return with no credit.
11. **Whether A and C deliberately differ** — Kept under Q1–Q3. The observed guards leave the desired policy open.
12. **Receiver form and capture policy** — Kept under Q1, Q3 and Q4. F's explicit pointer argument and E's value receiver are separate source-supported mechanisms.

## Changes after the initial report

- **F61 corrected.** The initial report placed C's nil-target admission panic at the request increment. The epoch field read occurs first, so the final report cites that read and identifies the unreachable increment. The probe verifies a panic, while the source establishes its exact expression. `observed-in-code` — component.go:18 ("target, epoch := p.Target, p.Target.Epoch") and component.go:19 ("target.Requests++"). `observed-in-tests` — analysis/_probe/identity_test.go:303 ("mustPanic(t, func() { op.admit(b) })").
- **F01–F06** now explicitly limit the README's role to the public accounting description. **F07–F12** state the replacement's unchanged Requests separately from the success attribution. **F25–F30** spell out the intermediate detach or removal before the replacement is installed. **F31 and F33** separate the first callback, binding restoration without invocation, and the later callback. **F62** names the three invalid lookup variants separately. The final report attaches the exact passing tests and source citations to each finding.
- **F67–F72 added.** The new comparison starts from the same admission and same-epoch replacement, and branches into no delivery versus invoking the very same returned callback after the initiating side has departed. The probe models that separation by retaining the callback on the delivery side in a serialized sequence. `observed-in-tests` — analysis/_probe/lifecycle_test.go:21 ("b.replace(op, incoming)"), analysis/_probe/lifecycle_test.go:25 ("deliverySide()") and analysis/_probe/lifecycle_test.go:34 ("counters(t, b.original, 1, wantOriginal[op.name])").
- **F73–F74 added.** One test turns A's replacement epoch from mismatching to matching. The other independently varies C's pointer and epoch before finally restoring both. The checks after restoration and before invocation isolate restoration from the credit effect. `observed-in-tests` — analysis/_probe/lifecycle_test.go:51 ("counters(t, incoming, 0, 0)"), analysis/_probe/lifecycle_test.go:54 ("counters(t, incoming, 0, 1)"), analysis/_probe/lifecycle_test.go:67 ("counters(t, b.original, 1, 0)") and analysis/_probe/lifecycle_test.go:71 ("counters(t, b.original, 1, 1)").

## Final Jev batch and source review

The command accepted `kind`, `line`, and `fragment` at the top level. The input retains the requested `type` and nested `citation` fields as well. One call submitted 68 independent checks to Jev 1.14.0. The retained responses contain 61 supported, six unclear, and one contradicted choice. The supported choices were checked against the cited line with its surrounding source and the corresponding probes where applicable. Reusable checks such as the admission increment and the per-invocation success increment retain separate IDs.

- **A_later_eligible (contradicted)** — Kept after source and test review. The first mismatch exits that invocation with no accounting change. The closure compares the live epoch with the saved value on each call and writes no state on a miss. Both original-epoch restoration and a replacement with a newly matching epoch passed. `observed-in-code` — component.go:9 ("epoch := p.Target.Epoch") and component.go:10 ("if p.Target.Epoch == epoch { p.Target.Successes++ }"). `observed-in-tests` — analysis/_probe/identity_test.go:231 ("counters(t, b.original, 1, 1)") and analysis/_probe/lifecycle_test.go:54 ("counters(t, incoming, 0, 1)").
- **A_after_panic (unclear)** — Kept for the specific sequence with recovery outside the callback and a later explicit invocation. The panic and later credit have separate test assertions. `observed-in-code` — component.go:10 ("if p.Target.Epoch == epoch { p.Target.Successes++ }"). `observed-in-tests` — analysis/_probe/identity_test.go:149 ("mustPanic(t, complete)") and analysis/_probe/identity_test.go:157 ("counters(t, b.original, 1, expected[op.name]+1)").
- **C_skip_nil_target (unclear)** — Kept with the valid-admission premise. Admission dereferences the original pointer, so it is non-nil in this scenario. The live nil pointer fails equality and Go evaluates the right conjunct only when equality succeeds. The probe establishes normal return with zero credit. `observed-in-code` — component.go:18 ("target, epoch := p.Target, p.Target.Epoch") and component.go:20 ("p.Target == target && target.Epoch == epoch"). `observed-in-tests` — analysis/_probe/identity_test.go:151 ("complete()") and analysis/_probe/identity_test.go:153 ("counters(t, b.original, 1, expected[op.name])").
- **D_nil_map (unclear)** — Kept for a non-nil Registry. Lookup in a nil map returns the zero value, a nil account pointer, which fails the callback guard. `observed-in-code` — component.go:5 ("Entries map[string]*Account") and component.go:24 ("if target := r.Entries[key]; target != nil { target.Successes++ }"). `observed-in-tests` — analysis/_probe/identity_test.go:197 ("b.registry.Entries = nil") and analysis/_probe/identity_test.go:170 ("counters(t, b.original, 1, 0)").
- **D_later_eligible (unclear)** — Kept. The lookup is inside the callback and repeats on every explicit invocation. The missing-key, nil-entry and nil-map probes separately exercise reinstallation and later credit. `observed-in-code` — component.go:24 ("if target := r.Entries[key]; target != nil { target.Successes++ }"). `observed-in-tests` — analysis/_probe/identity_test.go:178 ("b.registry.Entries[key] = incoming") and analysis/_probe/identity_test.go:183 ("counters(t, incoming, 0, 1)").
- **D_admission_nil_map (unclear)** — Kept. The admission expression dereferences the nil pointer from the lookup before the callback can be returned, distinct from the guarded callback lookup. `observed-in-code` — component.go:5 ("Entries map[string]*Account") and component.go:23 ("r.Entries[key].Requests++"). `observed-in-tests` — analysis/_probe/identity_test.go:294 ("nil_map") and analysis/_probe/identity_test.go:298 ("mustPanic(t, func() { op.admit(b) })").
- **E_rebinding (unclear)** — Kept after checking the receiver declaration together with the callback body and the rebind and detach probes. The callback-only fragment omits how the receiver reached the closure. `observed-in-code` — component.go:26 ("func (p Port) E() func() {") and component.go:28 ("p.Target.Successes++"). `observed-in-tests` — analysis/_probe/identity_test.go:314 ("b.port.Target = incoming") and analysis/_probe/identity_test.go:320 ("counters(t, b.original, 1, 1)").

Each applicable IDs list below links a final finding to the independent batch results in [jev-results.json](jev-results.json). Full scheduled effects are checked by the passing public API probes. The source request and callback checks establish separate parts of those effects.

- F01 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`.
- F02 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`.
- F03 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`.
- F04 — `D_admission`, `D_success`, `D_only_success_field`.
- F05 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`.
- F06 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`.
- F07 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_same_epoch_other_target`.
- F08 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_rebinding`.
- F09 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_other_target`.
- F10 — `D_admission`, `D_success`, `D_only_success_field`, `D_new_key_occupant`.
- F11 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_rebinding`.
- F12 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_rebinding`.
- F13 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_skip_mismatched_epoch`.
- F14 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_rebinding`.
- F15 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_other_target`.
- F16 — `D_admission`, `D_success`, `D_only_success_field`, `D_new_key_occupant`.
- F17 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_rebinding`.
- F18 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_rebinding`.
- F19 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_skip_mismatched_epoch`.
- F20 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_epoch`.
- F21 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_changed_epoch`.
- F22 — `D_admission`, `D_success`, `D_only_success_field`, `D_epoch`.
- F23 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_epoch`.
- F24 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_epoch`.
- F25 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_no_dispatch`.
- F26 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_no_dispatch`.
- F27 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_no_dispatch`.
- F28 — `D_admission`, `D_success`, `D_only_success_field`, `D_no_dispatch`.
- F29 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_no_dispatch`.
- F30 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_no_dispatch`.
- F31 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_nil_target_panic`, `A_after_panic`.
- F32 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_repeat`, `B_rebinding`.
- F33 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_nil_target`, `C_later_eligible`.
- F34 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_repeat`, `E_rebinding`.
- F35 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_repeat`, `F_rebinding`.
- F36 — `D_admission`, `D_success`, `D_only_success_field`, `D_absent`.
- F37 — `D_admission`, `D_success`, `D_only_success_field`, `D_absent`, `D_later_eligible`.
- F38 — `D_admission`, `D_success`, `D_only_success_field`, `D_nil_entry`.
- F39 — `D_admission`, `D_success`, `D_only_success_field`, `D_nil_entry`, `D_later_eligible`.
- F40 — `D_admission`, `D_success`, `D_only_success_field`, `D_nil_map`.
- F41 — `D_admission`, `D_success`, `D_only_success_field`, `D_nil_map`, `D_later_eligible`.
- F42 — `D_admission`, `D_success`, `D_only_success_field`, `D_whole_map`, `D_other_key`.
- F43 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_skip_mismatched_epoch`, `A_later_eligible`.
- F44 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_changed_epoch`, `C_later_eligible`.
- F45 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_same_epoch_other_target`, `A_repeat`.
- F46 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_other_target`, `C_later_eligible`.
- F47 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_no_dispatch`, `A_repeat`.
- F48 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_no_dispatch`, `B_repeat`.
- F49 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_no_dispatch`, `C_repeat`.
- F50 — `D_admission`, `D_success`, `D_only_success_field`, `D_no_dispatch`, `D_repeat`.
- F51 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_no_dispatch`, `E_repeat`.
- F52 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_no_dispatch`, `F_repeat`.
- F53 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_same_epoch_other_target`.
- F54 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_rebinding`.
- F55 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_other_target`.
- F56 — `D_admission`, `D_success`, `D_only_success_field`, `D_new_key_occupant`.
- F57 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_rebinding`.
- F58 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_rebinding`.
- F59 — `A_invalid_admission`.
- F60 — `B_invalid_admission`.
- F61 — `C_invalid_admission`.
- F62 — `D_invalid_admission`, `D_admission_missing`, `D_admission_nil_entry`, `D_admission_nil_map`.
- F63 — `E_invalid_admission`.
- F64 — `F_invalid_admission`.
- F65 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_rebinding`.
- F66 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_live_counter`.
- F67 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_same_epoch_other_target`, `A_no_dispatch`.
- F68 — `B_admission`, `B_success`, `B_only_success_field`, `B_capture`, `B_rebinding`, `B_no_dispatch`.
- F69 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_other_target`, `C_no_dispatch`.
- F70 — `D_admission`, `D_success`, `D_only_success_field`, `D_new_key_occupant`, `D_no_dispatch`.
- F71 — `E_admission`, `E_success`, `E_only_success_field`, `E_value_receiver`, `E_rebinding`, `E_no_dispatch`.
- F72 — `F_admission`, `F_success`, `F_only_success_field`, `F_capture`, `F_rebinding`, `F_no_dispatch`.
- F73 — `A_admission`, `A_success`, `A_only_success_field`, `A_saved_epoch`, `A_skip_mismatched_epoch`, `A_later_eligible`, `A_same_epoch_other_target`.
- F74 — `C_admission`, `C_success`, `C_only_success_field`, `C_capture`, `C_skip_other_target`, `C_skip_changed_epoch`, `C_later_eligible`.
