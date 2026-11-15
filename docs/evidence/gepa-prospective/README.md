# Prospective GEPA candidate comparison

The earlier run's GEPA 0.1.4 result assigned both candidates 2/3 on one
selection component. `GEPAResult.best_idx` calls Python `max` over candidate
indices keyed by score, so an exact tie returns the first index: the fixed
seed. The prior experiment did not select the longer candidate; it only looked
better in the separately declared, four-output exploratory follow-up. The
upstream behavior is reproduced by `tools/selftest/test_gepa_selection_upstream.py`.

This is an index-order tie break, not evidence of superior quality. New
`tools/gepa_selection.py` reports all exact tied indices and gives no best
index for a tie. It rejects empty/nonfinite inputs. `tools/report_gepa_selection.py`
compares the recorded GEPA index with this tie-aware report. The new comparison
uses that audit before launching. It does not alter GEPA, assign domain intent,
change historical observations, or promote a candidate. A unique numeric score
is not a confidence interval; near ties and sampling uncertainty remain.

The prior V02 finding gave a concrete five-byte example, not the exact six-byte
reference case; another report described the general partial-write behavior.
Whether the analogous concrete example implies full coverage was treated
inconsistently with a later generalization, and V03's implicit success return
was also open to interpretation. Those reviews and the actual historical tie
are not retroactively changed. The prospective protocol says to give full
credit to a stated general rule covering a case regardless of incidental
values, and to mark an analogous concrete example partial if the model does not
assert the general rule. Every case and every finding is still source-reviewed;
this rubric is an attributed evaluation judgment, not formal proof of semantic
entailment.

The [protocol](protocol.md) was written before model comparison: two distinct
Go 1.27.3 components, race-detected reference controls, independent isolated
AI checks, two repetitions per prompt and component, alternating order, and
frozen input hashes. There is no human review. In the Once wait test a 50 ms
nonreturn does not prove the waiting goroutine was scheduled; the source-based
reference review makes that limitation explicit. Go public source may have
appeared in model pretraining.

The supervisor also read the callee contracts instead of inferring them:
`contracts/mutex.go:44` ("blocks until the mutex is available"),
`contracts/atomic-type.go:18` ("Load atomically loads"), and
`contracts/runtime-panic.go:673` ("Goexit runs all deferred calls"). These
are local Go 1.27.3 snapshots; the comparison model receives only the component
source, not these contracts, the reference tests or case labels. The contracts
were examined while assessing returned findings and are not asserted to have
been part of the pre-comparison input freeze.
Buffer findings also require seam contracts: `contracts/io.go:58` ("0 <= n <= len(p)"),
`contracts/io.go:95` ("must return a non-nil error" for a short write), and
`contracts/utf8.go:150` ("its width in bytes"). A
short writer with nil error is an undesired implementation variant, not a
conforming Writer; the observed error path remains useful as an adversarial
case. The supervisor inspected these snapshots when grading, after the
comparison was frozen.

The [sensitivity table](selection-sensitivity.json) illustrates why one
validation result is fragile: hypothetically crediting only seed V02 changes
the numeric winner to the seed, while crediting only candidate V03 changes it
to the candidate. Crediting both leaves a tie. These are counterfactual scoring
scenarios, not a revised historical verdict or an executed optimization.

## Results

| Component and two independent outputs per arm | Fixed full cases | Candidate full cases |
| --- | ---: | ---: |
| `sync.Once` | 4/4 | 3/4 |
| `bytes.Buffer` | 0/4 | 0/4 |
| Total | 4/8 | 3/8 |

All 48 model findings were reviewed against source; zero were assessed false or
uncertain in this small set. Partial reference coverage is retained separately
in `runs/review-*.json`: notably one candidate Once output stated waiting but
not explicitly that the competing function is skipped on normal completion.
For Buffer both arms found other source-backed behavior but did not fully state
either prepared reference case in either run. These are case observations,
not eight independent components. Different case selection or semantic grading
could change the comparison; the results do not establish a population-level
winner or justify changing a production prompt. No policy questions were
answered automatically.

The new reference review used four metered Codex calls (two structural
citation repairs) costing approximately $0.0600 in credit-equivalent terms;
eight comparison calls cost approximately $0.2165. Total approximately
$0.2765 uses the same $0.04-per-credit estimate, not an invoice. Supervising
agent work and any future rework are unmetered. The pre-existing experiment and
its costs are separate. `provenance.json` maps reference cases and each reviewed
finding to the observed-in-code fragment, and the named Go reference tests.

`tools/verify_gepa_prospective.py` replays the frozen hashes, 12 named Go test
passes, prompt construction, citation fragments, scoring and trial coverage.
The model source prompts contain neither case labels nor reference tests.
Archive, budget and selection checks have retained red/green probes. The
verification validates recorded evidence and cannot establish AI semantic
judgments by itself.
