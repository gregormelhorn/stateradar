# GEPA discovery: bounded supervised experiment

## Result

**No GEPA-specific quality improvement was demonstrated.** Actual GEPA 0.1.4
ran seven metric evaluations and proposed two prompt changes. All three
candidates scored 2/3 on the known gobreaker selection cases; GEPA selected its
original fixed prompt (candidate 0). The three train cases scored 3/3 in each
of four timer evaluations. The feedback therefore had no missed reference case
on this training component to guide a correction. The held-out arms used **identical prompt
text**, in four independent task-model calls. Differences between these outputs
cannot be attributed to prompt optimization.

| Held-out component | Fixed call | GEPA-selected call | Incorrect findings, fixed / GEPA |
|---|---:|---:|---:|
| Cond | 1/3 | 2/3 | 0 / 0 |
| WaitGroup | 2/3 | 2/3 | 1 / 1 |
| Total | 3/6 | 4/6 | 1 / 1 |

The Cond difference is an output difference between two calls with the same
prompt, not evidence of a GEPA effect. There is one call per arm per component,
so variability or transfer cannot be estimated reliably. Cases have multiple
required elements; a partial mention is not full credit. All outputs and
case-by-case reviews are retained under `runs/`. The fixed and GEPA WaitGroup
calls each contained a different incorrect finding; these were caught through
source review and executed controls, not counted as successful discoveries:

* The GEPA-labelled call said an escaping task panic is always re-panicked
  before `Done`. With `GODEBUG=panicnil=1`, `panic(nil)` instead lets the
  wrapper run `Done`; `panicnil-acceptance.jsonl` records three passes.
  Panics are outside the `WaitGroup.Go` contract; this is a false universal
  claim about implementation behavior, not a decision on intended semantics.
* The fixed-labelled call said an outside `Wait` can return at zero without
  clearing a retained synctest association. Under the exact tested sequence
  it instead panics with a nil pointer: `synctest-acceptance.jsonl`
  records three passes of the explicit panic assertion. The runtime callee
  is archived at `runtime-reference/synctest-runtime.go:450`. Whether this
  behavior is intended is [Q-GEPA-D01](open-questions.md).

The unexpected synctest behavior was investigated **after** the model output;
its targeted tests and runtime snapshots are supplementary evidence and were
not used to train or select a prompt. The archived initial compile failure for
the panicnil control arose from a Go 1.23 module declaration with an API that
requires 1.25; it was retained, the module version corrected, and the test
rerun. The two reference controls with timed waits observe only bounded
nonreturn, not an unbounded liveness guarantee.

## Scope and evaluation

[Protocol](protocol.md), [benchmark](benchmark.json), all source snapshots,
[selection](runs/selected-prompt.json), raw outputs, [attributed reviews](runs/)
and [replayed audit](runs/audit.json) are retained. The task model received
source and generic instructions, not the gold cases or tests. Its shell and
web tools were disabled; all recorded events were checked for forbidden tool
calls. Selection and input hashes were frozen before final task calls.

The source contracts and Go upstream tests were authored independently; the
experiment operator created the gold cases and reviewed every model finding.
There is **no independent human second review** of those interpretations.
The two final components are distinct, but both belong to Go's sync package and
are public; pretraining exposure is unknown. This is not a full pilot, a blind
Part B, a representative sample, or evidence of spontaneous discovery beyond
the limited reference set. Several interesting reported behaviors were outside
the inventory; they were reviewed but did not become post-hoc scored hits.
Source-line validation establishes citation integrity, not entailment.

Six relevant Go upstream tests passed three times each with the race detector.
Our two supplementary public-seam controls passed five times, and both
model-claim counterexamples passed three times. Their source is
`reference/reference_test.go`; raw Go JSONL includes exact discovery and
package completion. The auxiliary control source was created after the first
optimization call, and counterexample probes after their respective model
outputs. The gold descriptions and task inputs remained frozen.

The experiment made 13 Codex calls, all with recorded usage and no structural
repairs: seven metric calls, two reflections and four final calls. Total estimated
cost equivalent is **$0.59114**, of which $0.43040 is optimization/reflection
and $0.16075 is final calls, at the archived $0.04/credit assumption. This is
not an account debit; supervision and human/reviewer time are unmetered. With
both final arms using the same prompt, their measured cost difference is not a
prompt-efficiency result.

## Mechanisms and rules

`tools/gepa_discovery_eval.py` audits complete distinct case and finding reviews,
source fragments, OPEN-question requirements and component split/selection
gates. It leaves semantic classification to the attributed reviewer. The
permissive evaluator scaffold failed eight rejection tests before implementation
(`evaluator-red.txt`); the permissive split gate failed three rejection tests
(`phase-red.txt`); the final 13 selftests pass (`phase-green.txt`). These
negative tests prove the named structural failure paths, not semantic truth.
The archive replay was likewise tested against a permissive stub and a missing-
freeze-entry defect: `archive-red.txt`, `archive-omission-red.txt` and
`archive-green.txt` retain both failures and the seven passing final tests.

No StateRadar domain decision, normal routing, blind inputs or domain-analysis
rule was changed. Mypy now tolerates the absence of optional GEPA imports while
checking the rest of the project: the missing-dependency red and green probes
are retained in `optional-import-red.txt` and `optional-import-green.txt`. No rule was shown to be unnecessarily restrictive. GEPA's mutable
paragraph and explicitly bounded evaluation allowed experimentation under the
existing constraints. Retain GEPA as experimental: stronger independently
reviewed, varied cases and repeated fixed-versus-different-prompt comparisons
would be needed before promoting any optimized prompt.

To replay deterministic checks without model calls:

```sh
.venv/bin/python tools/selftest/test_gepa_discovery.py
.venv/bin/python tools/selftest/test_gepa_discovery_archive.py
.venv/bin/python tools/verify_gepa_discovery.py
.venv/bin/mypy
.venv/bin/python tools/check_pack_consistency.py
.venv/bin/python tools/gen_rules.py --selftest
.venv/bin/python tools/selftest/run_selftest.py
cd docs/evidence/gepa-discovery/reference
go test -race -count=5 -timeout=20s -run '^(TestCondSignalBeforeWait|TestWaitGroupPositiveAddWhileActive)$' ./...
GODEBUG=panicnil=1 go test -race -count=3 -timeout=20s -run '^TestWaitGroupGoPanicNilLegacy$' ./...
go test -race -count=3 -timeout=20s -run '^TestWaitGroupSynctestOutsideWait$' ./...
```
