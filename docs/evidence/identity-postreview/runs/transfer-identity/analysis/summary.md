# Deferred accounting review summary

The final review preserves all 74 initial findings and their questions. It adds five findings and 28 qualifications covering caller-variable reassignment, wrapper and key lookup, Account copying and overwrite, and the scope of the preserved probes. [Final findings](final.json) · [Qualifications and probe bindings](supplement.json) · [Detailed review](review.md)

F's saved callback continued to credit the original Account after the caller reassigned only its local *Port. Both Port targets stayed intact. A and C continued to read the original Port after caller reassignment. After a subsequent Target change on that retained Port, A credited the matching-epoch replacement and C skipped it. D kept the original Registry pointer and key value through caller reassignment, while updating the original Registry entry redirected its next delivery. C skipped an equal-valued Account copy, then credited the original object after its pointer was restored and its contents were overwritten in place at the saved epoch. [Source](../component.go) · [New probes](./_postprobe/binding_test.go)

All 111 test and subtest names passed each of three race-enabled runs. Pilot log 026 retains stdout and empty stderr. The preservation validator passed. One final Jev verdict disputed A's redirection and three were unclear. The review records the source and probe evidence for the retained claims. [Execution and model dispositions](review.md)

The README limits analysis to serialized operations and leaves lifecycle policy open. The nine baseline questions and the additional questions in the new findings remain open. [README](../README.md#L5) · [Baseline questions](../baseline/open-questions.md)
