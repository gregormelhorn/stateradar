# GEPA discovery experiment: preflight

Historical preflight, superseded by [the executed experiment](README.md). At
this point the benchmark and feedback path did not yet exist. No model calls
had occurred at the time of this preflight. The later experiment is small and
has no independent human second review; see its result and limitations.

## Starting point

The previous experiment is committed at `719a684`. Its independent-component
test evaluates 14 supplied claims three times. Its timer and once components
have already been opened as final-test inputs; they are not a fresh holdout.
Its scorer requires a fixed, exhaustive input claim inventory and validates
citation fragments, not semantic entailment (`tools/gepa_eval.py`). The
repeated-Stop documentation discrepancy is known and may be a training or
regression example, not a newly discovered held-out finding.

The existing identity benchmark includes source-anchored, attributed manual
reviews and executed observations. Both archived runs found 7/8 cases; their
missed B05 and their outputs are already published and inspected. The checker
validates annotations and anchors but explicitly does not judge entailment or
discover missing findings (`tools/finding_benchmark.py`). These historical
cases are useful for evaluator development and negative controls, not as a
fresh independent final test.

The old GEPA experiment's adapter also cannot simply be pointed at the identity
benchmark: its optimization feedback counts verdicts on a supplied inventory.
Providing the target findings as that inventory would leak the answers to a
discovery task. Keyword matching would not distinguish a valid ordered finding
from a superficial mention, and citation matching would not establish that the
finding follows from the source.

## Evidence checked

Commands executed on the checked-out `main` commit before this preflight:

```text
$ .venv/bin/python tools/verify_gepa_reference.py
REFERENCE PASS: 4 components x 5 repetitions; exact discovery; race detector; pinned source

$ .venv/bin/python tools/verify_gepa_quality.py
SCOPE CONTROL PASS: intervening rearm and repeated Stop, 2 controls x 5 repetitions with race detector
SCOPE ANNOTATIONS PASS: exact original reasons; semantic judgments remain attributed review

$ .venv/bin/python tools/selftest/test_gepa_eval.py
Ran 13 tests in 0.000s
OK

$ .venv/bin/python tools/selftest/test_gepa_search.py
Ran 1 test in 0.055s
OK
```

The last test uses a mock adapter; the simulated improvement is not evidence of
an improvement on a real model or discovery task. The archived finding reviews
were also replayed: both report 7/8 findings and B05 missing. The GEPA report
replays 42/42 verdict observations per arm, 6/6 seeded corrections and 8/8
retained controls in both review arms. These are historical results, not the
requested new comparison.

## Work required before paid optimization

1. Assemble source-pinned cases on separate components, including findings
   absent from the input report, source-scope contradictions, correct controls
   and open policy questions. Record executable observations and independently
   attributed semantic reviews; distinguish behavioral observations from
   desired domain semantics. Establish which case families were previously
   exposed to each model and disclose any uncertainty.
2. Freeze component-disjoint train, selection and final sets, the seed prompt,
   fixed comparison prompt, evaluation protocol and budgets before calls. Keep
   final cases and expected findings outside all task and reflection inputs.
3. Build and red-probe an evaluation path that reviews *every* emitted finding,
   verifies source/output anchors, counts missed and incorrect findings and
   preserved OPEN questions separately, and records the reviewer and rationale.
   A fragment or a model confidence score is not semantic proof. Arrange for
   train feedback to be reviewed before GEPA can use it, and retain incomplete,
   failed and unreviewed outputs as such.
4. Compare the frozen fixed prompt with GEPA on identical inputs, repeat on
   held-out components, and record all model calls, review effort and unknown
   costs. Freeze the selected candidate before opening the final set. A
   candidate is not promoted merely because it improves an aggregate score.

Existing project rules do not prevent this experimental workflow. No specific
rule has been shown to be unnecessarily restrictive, so none is changed by this
preflight. A future proposed change to a rule requires its own evidence and
must preserve the separation between model proposals, deterministic checks and
human decisions on domain semantics.
