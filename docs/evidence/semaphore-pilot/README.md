# Third-component pilot: weighted semaphore

The original runner completed a routed, selective pilot of one `semaphore.Weighted`
instance in golang.org/x/sync v0.17.0. Review then repaired two artifact/input
omissions. At that checkpoint the reviewed result passed **7/7 gates**, covered
the five independent public-boundary controls, and left **13 domain questions OPEN**. No domain
implementation change, accepted DR, to-be promotion or Step-04 conformance
suite was claimed at that pilot checkpoint.

Follow-up: the owner has now accepted **Q-01 as DR-001**. The
[focused resolution](resolution-q01/deviation-report.md) records the expected-red
tests and the minimal fix in the [evaluation copy](../../../examples/weighted-semaphore/README.md).
Its five scenarios pass 50 times each with the race detector; upstream tests
also pass. **Twelve questions remain OPEN** in the
[active question register](resolution-q01/open-questions.md). The historical
analysis below remains the original baseline, not a reconciled fixed model.

## Frozen inputs and scope

- Component source: `04914c200cb38d4ea960ee6a4c314a028c632991`
  ([upstream tag](https://github.com/golang/sync/tree/v0.17.0)).
- Original pilot pack/runner: `a00ea120189136e6e96c8142d9ea0620d2f878dd`.
- Post-review tooling: `9458923`, including the additional completion audit.
- Codex `gpt-6.1-sol`, medium effort, ChatGPT login, standard speed, routed
  analysis, selective output, Jev 1.14.0. No OpenAI API key.
- Codex CLI 0.167.0-alpha.4.1; Go 1.27.3. Pilot elapsed 798.293 seconds,
  127 command/readback calls. No paid controller restart.
- Candidate selection and exclusions: [candidates.md](candidates.md).
  This is unused in the local tuning sequence, not a claim of training-data
  novelty or a customer deployment. Owner choices concern this evaluation,
  not Go upstream maintainer approval.

## Quality and evidence

The model has 3 grid states, 19 events including 13 undesired variants,
8 pairs / 16 orderings, 57 cells, and 13 questions. Eight guard groups are
proven under their stated NAT assumptions; one dynamic select is explicitly
not formalizable. Zero guard violations do not prove liveness or settle intent.

| Independent control | Pilot coverage | Assessment |
| --- | --- | --- |
| Pre-canceled call preserves available capacity | Entry/cancellation traces, upstream TestWeightedAcquireCanceled replay | Covered |
| Second acquisition while first weight is held | Q-06, repeated-acquisition probe, P-05/P-06 | Covered; pending and held cases stay distinct |
| Oversized request can cancel without occupying the ordinary queue | Q-02, T-01, source contract replay | Covered; the separate control does not force the oversized call's scheduling point |
| Negative TryAcquire can increase apparent capacity | UV-Weight, Q-03, signed-input trace | Covered in the shared invalid-weight group |
| Recovery after over-release can admit above capacity | Q-04 and dedicated public-outcome probe | Covered |

[Five independent controls](controls/README.md) passed with the race detector.
The pilot independently wrote five further observations, including a
zero-weight request stranded after a positive queue head cancels at full
capacity. `Release(0)` wakes it. This supplies a real F-20 progress case for a
later approved conformance test; it is not yet a new mutation-coverage claim.

Upstream semaphore tests, the pilot's full repository test run, and its race
probes passed. The reproducibility run repeats the upstream race suite and all
10 distinct observations five times. Probes assert current behavior; they do
not substitute for tests against an approved to-be model.

The initial independent overlay used /tmp instead of the canonical /private/tmp
path and discovered zero tests. That exit-0 result is retained as a failure of
test discovery, not reported as a pass. The corrected run and reproduction
require the expected named probes to execute. A deliberately empty Go test
result is rejected by the reproduction driver in [reproduction-red.txt](reproduction-red.txt).

## Review corrections and blind pass

The original six gates passed even though `manifest.json` was absent and the
sidecar used WORKTREE with empty watch paths. The new completion audit rejects
that original artifact set. Review added the source-pinned manifest, regenerated
the sidecar and ran all seven gates. This is a correction to an observed
completion hole, not a relaxed gate. See [abort-accounting evidence](../abort-accounting/README.md).

The first blind request omitted the full Go Context/CancelFunc contract and
contained 109 classified situations. Its exact response, package and comparison
remain under `analysis/archive/original-pilot`. Review copied the public
contract comments verbatim, inspected the resulting package, and made one fresh
Flash request. The generic Stream sample is public Done documentation, not
component implementation. The request contained no matrix, traces, tests,
questions or previous response. It also included the now-complete public
normative-line list and the pilot's two catalogue clarifications; this was an
input repair, not a matched one-variable experiment.

The [reviewed comparison](analysis/part-b-diff.md) classifies all **125** new
situations: 43 convergent, 19 convergent-hole, 62 divergence and one blind spot.
All divergences link to retained questions. These counts are not accuracy scores:
many matches depend on code-derived catalogue observations. The new pass also
invented unsupported ownership/refusal guarantees and switched its zero-weight
expectation from immediate admission to rejection. Its answers are proposals,
not requirements. All 13 questions and their separate consequences remain open.

## Costs and their limits

| Measured work | USD equivalent |
| --- | ---: |
| Codex pilot controller, complete final counters | 0.944124 |
| Original Flash/Jev calls | 0.016218 |
| One additional blind request for repaired input | 0.008799 |
| Pilot plus measured repair | **0.969141** |
| Initial live usage-format probe | 0.018900 |
| Known measured subtotal | **0.988041** |

These are rate-based equivalents using the recorded standard-speed Codex rates
and **$0.04/credit assumption**, plus settled provider ledger amounts. They are
not billing receipts. The supervising Codex chat, manual classification and
human decision work have no complete measured cost here, so the end-to-end
total remains **unknown**, explicitly null in [reviewed-cost-estimate.json](reviewed-cost-estimate.json).
No cost-saving claim against Pool, gobreaker or another controller follows.

The child usage history and final counters are retained under `run/`. Replaying
those records through the hardened parser reproduced the final counters with no
paid call. The source ledger has no unsettled reservations. The original run's
cost/acceptance files are preserved separately from post-review totals.

## Reproduction and next step

With the pack's Python dependencies and a suitable Go installation:

```sh
.venv/bin/python docs/evidence/semaphore-pilot/reproduce.py --output /tmp/semaphore-recheck
```

This fetches the pinned source, reconstructs the checked artifacts and tool
revision, and runs the seven gates plus race/observation tests. It makes no model
calls. `--source-repo /path/to/existing/sync` avoids the network fetch. The executed
result is [reproduction.txt](reproduction.txt). [retained-hashes.json](retained-hashes.json)
records the archived analysis bytes. Narrow local Git whitespace attributes
preserve canonical renderer output, existing Markdown hard breaks, and the
verbatim indentation of the public Go contract example unchanged;
the semantic and catalogue checks remain enabled.

Q-01 was accepted as [DR-001](resolution-q01/decisions/DR-001.yaml): keep zero
weight and FIFO, and notify an eligible zero prefix after the blocking head
cancels even at full capacity. The focused to-be refinement, red/green tests and
evaluation fix are complete. The next domain step is the next unanswered
question in the [active register](resolution-q01/open-questions.md), one per
round. Other questions stay OPEN and block only their own branches. Full
conformance and reconciliation remain pending; this partial DR implementation
does not promote the historical as-is analysis or establish generic F-20
mutation coverage.
