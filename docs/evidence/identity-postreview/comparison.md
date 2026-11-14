# Identity check as a final review: results

## Decision and scope

Keep the standard pilot prompt and routing unchanged. Exact finding preservation
works as a deterministic constraint on final review. The identity paragraph adds
useful ordered variants without losing B06, and both review variants close the
direct caller-variable test gap. The cost difference between them is small and
mixed. A full extra review substantially increases cost compared with stopping
after the original analysis.

Use identity review selectively for captured callbacks, mutable wrappers/keys or
identity/epoch ambiguity, with preservation, public-seam probes and separate
qualifications. This is a proposed use boundary, not an implemented automatic
router or a proven cost-saving default. Generic review still finds useful
non-identity boundaries that the focused run does not add.

Four fresh Sol medium sessions via ChatGPT login use the same pinned pack,
component sources, provider versions, selective output, timeouts and immutable
baseline within each pair. The order is gobreaker generic/identity, then transfer
identity/generic. The sole prompt difference is the frozen English identity
paragraph. Both transfer prompts require the direct F caller-variable test, with
no supplied expected counters or reference test. See [protocol](protocol.md).

## Retention and benchmark coverage

The starting reports are the previous **baseline** final reports: 29 gobreaker
findings and 74 transfer findings, including ordered steps and open questions.
Their existing probes and question documents are unchanged. New rows append;
corrections and test bindings are separate supplements. All four sessions pass
exact row preservation and input hashes. This preserves those starting reports,
not a newly consolidated union of every historical candidate report. The earlier
experiment and its additional candidate findings remain archived unchanged.

| Component / review | Retained rows | Added rows | Qualified rows | Benchmark cases | Full / partial test bindings |
|---|---:|---:|---:|---:|---:|
| Gobreaker generic | 29/29 | 5 | 10 | 8/8 | 7 / 0 |
| Gobreaker identity | 29/29 | 7 | 9 | 8/8 | 7 / 0 |
| Transfer generic | 74/74 | 4 | 42 | 6/6 | 6 / 0 |
| Transfer identity | 74/74 | 5 | 28 | 6/6 | 6 / 0 |

Gobreaker B04 reentry remains source-only. Transfer F improves from partial to
full exact-sequence test coverage. The primary finding scores were already 8/8
and 6/6 at input: these results demonstrate **no regression**, not blind discovery.
Unlike the earlier monolithic candidate's 7/8 result, this workflow cannot silently
remove the inherited B06 success ordering. Raw preservation is not endorsement of
a historical generalization; the reviewed scores incorporate narrower scopes in
the supplements. All four strict coverage audits exit 0. They check exact anchors
and reviewed annotations, not prose entailment. See `*-review.json` and
`results/coverage-audit.txt`. Transfer uses same-author synthetic controls, not
independently held-out validation or production coverage.

## Added behavior versus clarification

Gobreaker's identity review adds seven tested schedules:

- N01 distinguishes a separate wrapper copy and a caller-local pointer rebind
  from mutation of the originally captured wrapper.
- N02 replaces the wrapper from a state-change hook **during admission**: the
  origin receives admission, the replacement receives completion, and restoration
  lets the same callback complete on the origin too.
- N03 resolves expiry and notifies on a replacement before dropping a mismatch.
- N04 keeps a saved Execute method on its original receiver after caller rebinding,
  for both normal return and panic, including hook attribution and return values.
- N05 distinguishes replacement of the caller's Settings function from mutation
  of the original stored closure's captured environment.
- N06 zeroes/restores the wrapper: a nil-receiver panic does not consume the callback.
- N07 replaces the wrapper in a reporting hook and panics: the current call unlocks
  the origin, while a manual retry selects the replacement.

These are additional ordered variants relative to the supplied baseline, not seven
established defects. Some overlap earlier candidate topics. Admission-time and
reporting-hook replacement make distinct orderings explicit. Intent remains open.

Generic gobreaker review also finds identity effects: foreign closed failure trips
a replacement with zero admissions, and a foreign HalfOpen success invalidates
the target's own trial before restoration lets it complete the origin. Other
tested additions cover State-triggered notification panic, Goexit in ReadyToTrip,
and nil/typed-nil panic boundaries. The nil-interface observation is scoped to the
measured runtime mode; the alternate branch is unexercised. Generic also executes
a MaxRequests=2 below-threshold success probe. Identity qualifies that threshold
in prose but does not add the probe. Focused review does not subsume this work.

**Both transfer direct tests** create F's callback, reassign only the local pointer
to a distinct Port, and assert both account counters and the old Port alias before
and after delivery. The old Port.Target mutation probes remain. Together they
distinguish caller-variable rebinding from mutation of an object reachable by the
callee. The new negative control alone cannot distinguish every target-capture
implementation. Its execution was required in both prompts, so it is compliance
evidence, not a unique discovery caused by the identity paragraph.

Transfer identity adds five tested schedules: direct F rebinding; caller rebinding
followed by original-Port mutation for A and C; caller key/Registry rebinding
followed by original-key mutation; and an equal-valued Account copy versus an
in-place overwrite at the original address. Generic adds the F test and a D
two-key alias control. Its two further nil-wrapper admission findings are explicitly
**untested**. Identity mentions nil-wrapper limits in prose without executing them.

Qualification counts are not independent bug counts. Of identity transfer's 28
annotations, 24 specialize repeated Port/Registry wording; four refine citation,
copy, counter-reset or guard scope. Generic's 42 also specialize shared wording
and identify citation/schedule limits, including discarded versus retained
callbacks. Both correct the counter-reset description. Domain questions remain open.

## Costs and observed work

All four reviews have complete Codex usage and settled Flash/Jev accounting. The
strategy total adds the measured baseline ($0.504245 gobreaker, $0.5047006 transfer)
to the final review. That baseline was reused as input, not rerun or charged again.

| Review | Codex review equivalent | Flash/Jev | Incremental review | Baseline + review | Seconds |
|---|---:|---:|---:|---:|---:|
| Gobreaker generic | $0.5347152 | $0.007276 | $0.5419912 | $1.0462362 | 443.346 |
| Gobreaker identity | $0.5213672 | $0.003992 | $0.5253592 | $1.0296042 | 466.285 |
| Transfer generic | $0.3555504 | $0.002150 | $0.3577004 | $0.8624010 | 293.383 |
| Transfer identity | $0.3611344 | $0.002414 | $0.3635484 | $0.8682490 | 344.612 |

Identity is 3.1% cheaper incrementally on gobreaker and 1.6% more expensive on
transfer. Including the baseline, the differences are **−1.6% and +0.7%**. The sum
across these two inputs is $1.9086372 generic versus $1.8978532 identity, just 0.6%
lower; this is not a workload-weighted forecast or an established saving. The four
new review sessions sum to $1.7885992. Relative to no extra review, identity adds
about 104% to gobreaker's original cost and 72% to transfer's. This is a quality
expense, not evidence that an unconditional extra phase lowers total cost.

| Review | MCP calls incl. rejections | read-log requests | Go-suite attempts | Rejected tools | Nonzero command exits |
|---|---:|---:|---:|---:|---:|
| Gobreaker generic | 84 | 55 | 1 | 0 | 1 |
| Gobreaker identity | 132 | 98 | 2 | 1 | 0 |
| Transfer generic | 65 | 33 | 1 | 0 | 0 |
| Transfer identity | 63 | 32 | 1 | 0 | 0 |

All Go attempts pass. The second gobreaker identity suite adds N07 after a passing
first suite, rather than repairing a failed test. Its rejected request asks for
105 log lines despite the documented maximum of 100, then is corrected. The cost
includes it. Completed MCP events count 132 calls; child `result.json` counts 131
retained command logs because the rejection produced no command log. Generic's
nonzero `rg` exit means no AGENTS.md matched, not a test or runner defect. No
controller retry, fallback, missing usage or source change occurred. Read-log
counts include initial pagination of large supplied reports and claim responses,
so they cannot be labeled 55 or 98 error corrections. All this reading is costed.

Final Jev batches have 14/12/3/3 unclear judgments for gobreaker generic/identity
and transfer generic/identity. The first, second and fourth also each contradict
one claim supported by source and execution. Controllers retain those observations
with explicit review. Generic transfer has no contradicted verdict. These are
workload counts on different claims, not a calibrated error rate; source and
public behavior determine the finding judgment.

Cost equivalents use the previous [verified standard rates and $0.04/credit assumption](../identity-benchmark/comparison.md#cost-interpretation).
They include all metered child Codex/provider work. Common implementation, this
supervising comparison and human review are unmetered and excluded, not free.
The collector was extended outside the sessions to read actual Go command logs
when analysis-folder copies were absent; its red/green tests are retained. No
model output was repaired outside its metered session. Timing includes tool waits;
one pair per input does not isolate prompt effects from variability, cache or host load.

## Acceptance and next step

Independent replay preserves old overlay entries and injects only new tests. Each
suite runs three times with the race detector: 28/29/21/23 top-level tests and
249/240/321/333 pass events including subtests, in table order. Every reported
probe name executes. Empty discovery is rejected despite Go exiting 0. The separate
caller-variable reference passes five repetitions and is not credited to a model.
All 741 archived file hashes and frozen protocol/prompt/validator hashes match.

The full repository suite, preservation selftests, tool-log red/green tests,
reviewed-coverage audits and independent replays pass. Full-pilot matrix and blind
Part-B gates were not run and are not implied by bounded acceptance.

Keep preservation whenever a final review is requested. Next proposed experiment:
a smaller identity pass on an independently reviewed component, comparing useful
additional test coverage and all continuation cost against **no extra review**.
Retain ordinary success/failure cases and direct caller-variable controls. Repeated
matched runs are needed before using these small deltas as a default-routing claim.
