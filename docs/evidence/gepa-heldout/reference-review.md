# Held-out reference review before optimization

No human reviewer participated. An isolated Codex session examined each source,
proposed case and reference test in `reference-review/`, `reference-review-v2/`
and `reference-review-v3/`; its original outputs and structural retries are
retained. Jev 1.14.0 separately evaluated cited claims (`*-jev*.json`); every
judgment was then checked against code and executed tests by the supervising AI.
These are AI judgments and executable observations, not normative decisions.

The first Codex review **refuted** two overly broad cases: S01 omitted the
possibility of a pre-existing non-EOF reader error, and A02 omitted the concrete
types checked before empty-state comparison. The original proposed descriptions
remain in `dataset-v1-reviewed.json`. Both descriptions were narrowed before
optimization, and `TestScannerFinalTokenPreservesPriorError` and
`TestValueCompareAndSwapMismatchedTypes` were added as opposite controls. The
independent session re-reviewed the updated cases; its second review noted the
Pipe descriptions also needed to identify open endpoints and lack of interfering
operations. Those scope conditions were made explicit in the final dataset, and
the third isolated session confirmed all seven final cases.

The initial reviewer also noted that the empty-write test did not check the
write count and the typed-nil test did not recheck the value after a panic.
Both assertions were added before the second and third reviews. In the final
empty-write test, the 50 ms check establishes only that no result was observed
in that interval; the writer may not yet have been scheduled. The handshake
mechanism is supported by source and the later completed read/write outcomes,
not a claim of unbounded liveness.

## Q-H01 — retained AI disagreement on A01

Jev's source-only judgment on A01 was `unclear` in both passes; the separate
Codex review and executed `TestValueTypedNilAndNil` support the exact stated
observable behavior. The disagreement remains recorded and is not converted
into certainty by model confidence. A01 is scored as a source-and-test-backed
case for this bounded experiment, with this grading uncertainty disclosed. The
question is why Jev could not confirm the typed-nil interpretation; it does not
authorize a change to the API contract.

The reference and upstream Go tests were run with Go 1.27.3 and the race
detector. `reference-v2.jsonl` includes the strengthened final source and the
two opposite controls; the earlier `reference.jsonl` remains historical. No
external issue, message, or domain decision was made.
