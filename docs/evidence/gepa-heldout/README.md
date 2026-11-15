# GEPA: distinct-component selection and test

This is an automated, bounded discovery experiment, **not** a StateRadar
pilot or blind Part B. No human reviewed the cases or findings. An isolated
Codex reviewer, Jev, code inspection and executable controls prepared the
reference; the supervising AI reviewed each model finding. Their judgments
are evidence with limitations, not human decisions on domain semantics.
The exact setup, preregistered split, score and budgets are in [protocol.md](protocol.md).

The training set contains 12 cases on five components. Selection uses three
new `io.Pipe` cases; final measurements use four cases on `bufio.Scanner` and
`sync/atomic.Value`, distinct from training. Public source may occur in model
pretraining. The initial source-only baseline results and reviews from an earlier
run are reused during training. Fresh proposal and validation outputs are
recorded in `runs/` with their costs and source-grounded AI assessments.

The single proposed modified paragraph obtained the same selection score as
the original: 2/3, with no false findings in either assessment. GEPA chose
candidate index 0, the **unchanged fixed prompt**. Consequently the final two
arms use identical prompt text: their repetitions characterize variability,
not the effect of an optimized prompt. The longer unselected candidate is not
promoted or installed as a project rule.

Selection grading has a material qualification: validation V02 was marked
partial for the seed because its partial-write example used five bytes rather
than six; the later candidate received full credit for the same behavior in
general form. Those sizes do not by themselves establish a behavioral
limitation. The candidate's V03 was marked partial because its successful
zero-length write did not explicitly spell out both return values. A more
generous interpretation of either statement can change the reported score;
the archived reviews and original selection are preserved. This experiment
therefore does not support a confident conclusion about a narrow selection tie.

Reference preparation initially exposed two overbroad cases. They were narrowed
before training began and strengthened with opposing controls; all seven final
cases received confirmation from a separate isolated AI review. Jev remained
uncertain on A01; [reference-review.md](reference-review.md) records this and
the limitations of the zero-write scheduling observation. These are not
converted into certainty by automated agreement.

The following exploratory comparison was declared after selecting the seed and
before inspecting final outputs: [exploratory-declaration.json](exploratory-declaration.json).
It compares the unselected candidate with already scheduled fixed-arm calls on
the same test components. It is post-selection exploration, not a fresh held-out
validation, evidence of a selected-prompt effect, or authorization to promote.

## Recorded primary observations

| Measurement | Full cases | False findings | Uncertain findings |
| --- | ---: | ---: | ---: |
| Historical fixed seed, five training outputs | 4/12 | 4 | 2 |
| Fresh proposed candidate, five training outputs | 7/12 | 4 | 0 |
| Fixed prompt, four final outputs | 4/8 | 0 | 1 |
| Selected prompt, four final outputs (same text) | 5/8 | 0 | 0 |

The historical seed and fresh candidate were not measured as simultaneous
paired repetitions. A full case requires all specified outcomes; partial cases
are retained in each review and do not receive full credit. A timer judgment
also interprets an unqualified expiration-first statement strictly in light of
possible intervening reset; a two-event interpretation may be narrower. These
small, attributed AI-graded samples do not establish model accuracy or a
population-level difference. All final atomic outputs covered the empty
CompareAndSwap case, but only partially covered the typed-nil Store case.
One scanner finding remains uncertain because it names ScanBytes but then
assigns that splitter a custom-error behavior ScanBytes cannot produce.

A clean offline replay rechecks frozen input hashes, prompt text, named Go test
runs, review completeness, source citation fragments, scores, trial coverage,
and metered call records. Red probes for missing and modified evidence precede
the corresponding passing checks. The replay checks evidence consistency;
it cannot prove the AI's semantic judgments correct.

## Post-selection exploration and cost

The unselected candidate's four fresh exploratory outputs covered 7/8 case
observations fully, with one false finding and no uncertain findings; the four
already scheduled fixed outputs covered 4/8, with no false finding and one
uncertain finding. The false candidate finding omitted the trailing-carriage-
return exception from a claimed Scanner token length. The full source-backed
assessments are in `exploratory/review-*.json`. These figures are descriptive:
there are only two repetitions per component, the reference cases and scoring
have the limitations above, and the candidate was examined after selection.
The result warrants a genuinely fresh prospective comparison if transfer is to
be evaluated; it does not change the selected prompt or any domain rule.

The newly metered calls total approximately **$0.9996 model-cost equivalent**:
13 isolated reference-review calls $0.3138, five settled Jev calls $0.000694,
16 primary calls $0.5696, and four exploratory calls $0.1156. Codex cost uses
$0.04 per reported credit and is an estimate rather than an invoice. The five
historical seed calls cost approximately $0.1795 in their earlier run and are
not new expenditure here. Supervising agent time, source preparation and any
future rework are not metered and must not be treated as free.

At the time of this experiment the branch started at `810d924`, while remote
main was at `9385573` with the pack-wide optional-GEPA CI dependency fix. The
experiment branch included that CI dependency line before the main commit
became its ancestor. This paragraph records the historical state at the end of
the experiment; check Git and CI for the current integration status.
