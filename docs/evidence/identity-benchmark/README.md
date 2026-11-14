# Finding benchmark and bounded identity prompt experiment

The regression benchmark now names eight observable behaviors, with ordered
conditions and executable references in `benchmark.json`. The additional case
B05 exposes a concrete shared omission in the two archived final reports. Their
existing four-control score remains historical evidence; the expanded score is
7/8 for both. No original report, question, probe or cost record was repaired.

`routed-review.json` and `matrix-review.json` contain attributed review judgments
with byte hashes and exact report anchors. `tools/finding_benchmark.py` validates
those annotations and totals them. It does **not** infer semantic coverage from
keywords, prove entailment, or automatically discover missing findings. The
reviewer must inspect conditions, order and consequence. General copying or
replacement prose is the explicit near miss for B05. Question counts are not
finding counts; grouping related behavior in one question remains valid.

The checker rejects incomplete rows, duplicates, changed files, fabricated
anchors and claimed tests without matching source/execution anchors. The first
empty-review red probe and subsequent green selftests are retained under results.
`--require-complete` exits 1 for each archived report with B05 missing; ordinary
audit exits 0 because a correctly documented incomplete report is valid evidence.
CI verifies both outcomes. A separate counterfactual test of routed Q-08's
unqualified original-breaker claim also fails in 3/3 race runs: the replacement
has zero admissions and one success. See `results/legacy-claim-red.txt` and its
raw JSONL. That expected-red assertion is a falsification probe, not an owner
requirement. No expected-red observation is repaired to force green.

Test depth is deliberately stricter than the previous four-control presence
screen. Routed has five complete test bindings and one partial binding; matrix
has three complete and two partial bindings. For example, routed's stale-return
probe asserts the original error but discards the returned value. The new reference
probe asserts both. Matrix's abandoned/stale probes do not cover both late outcomes.
These are test-coverage differences, not additional absent prose findings.

The eight reference cases and the unchanged archived suites were executed five
times with the race detector. Bounded nonreturn in the reentry probe is supported
by the actual mutex sites, not presented as an unbounded experimental time proof.
`results/proofs.txt` gives nonzero discovery totals. Reference and transfer-oracle
sources never enter model inputs. Copying policy and other intent questions remain
open; the benchmark observes behavior, it does not approve it.

The frozen English candidate, protocol, bounded task and verbatim baseline
excerpts are in `prompts/` and `protocol.md`. The standard pilot prompt and routing
remain unchanged after the mixed [comparison](comparison.md). Transfer cases are untuned checks
created by the same experiment author, not independently held-out evidence.

Four completed sessions retain all report/probe/provider outputs under `runs/`,
per-run byte hashes, and complete controller/provider cost accounting in
`measurements.json`. Independent final-suite replay passes with nonzero discovery.
The candidate is 15.7% costlier on gobreaker with one explicit case missing, and
13.7% cheaper on the six synthetic recipient classes with the same class coverage.
Both transfer suites have partial exact-sequence coverage for caller-variable
rebinding. The standard prompt is not promoted on this evidence.

## Reproduce the archive audit

From the repository root:

```sh
.venv/bin/python tools/selftest/test_finding_benchmark.py
.venv/bin/python tools/finding_benchmark.py docs/evidence/identity-benchmark/benchmark.json docs/evidence/identity-benchmark/routed-review.json
.venv/bin/python tools/finding_benchmark.py docs/evidence/identity-benchmark/benchmark.json docs/evidence/identity-benchmark/matrix-review.json --require-complete
```

The last command intentionally exits 1. Review annotations are not silently
recomputed when historical files drift. The proof script replays the original
probe sources, and `build_reviews.py` materializes the reviewed mappings with exact
anchors; refreshing replay logs requires explicit annotation refresh because the
logs include execution timestamps.

## Repeat a bounded comparison

Use a local gobreaker clone containing the pinned commit and the existing signed-in
Codex CLI. The normal Flash/Jev environment variables are required; OpenAI API-key
authentication is not used. Choose a new output directory for every experiment.

```sh
.venv/bin/python docs/evidence/identity-benchmark/scripts/run.py /tmp/identity-repeat --source-repo /path/to/gobreaker
.venv/bin/python docs/evidence/identity-benchmark/scripts/proofs.py --source-repo /path/to/gobreaker
bash docs/evidence/identity-benchmark/scripts/full_gates.sh
```

The runner keeps the old and candidate prompts identical except for the frozen
paragraph. It uses the original pilot transport's isolated filesystem/network
policy, selective output and incremental accounting. The transport's smoke-mode
status intentionally says no full artifact gates ran; this is not a full pilot.
The bounded report validator, nonzero probe discovery, source integrity, metering
and explicit behavioral review provide this experiment's narrower acceptance.
The collector refuses to overwrite retained runs and rejects changed input or
unexpected prompt deltas. Repeated measurements require a new evidence directory.

For this retained experiment, `scripts/collect.py OUTPUT_ROOT` captured the runs,
`scripts/verify_runs.py OUTPUT_ROOT` independently replayed the final overlays,
and `scripts/bounded_reviews.py` materialized the manually reviewed mappings.
Do not regenerate immutable evidence during ordinary CI. Audit it instead:

```sh
.venv/bin/python tools/finding_benchmark.py docs/evidence/identity-benchmark/benchmark.json docs/evidence/identity-benchmark/bounded-baseline-review.json --require-complete
.venv/bin/python tools/finding_benchmark.py docs/evidence/identity-benchmark/benchmark.json docs/evidence/identity-benchmark/bounded-candidate-review.json --require-complete
.venv/bin/python tools/finding_benchmark.py docs/evidence/identity-benchmark/transfer-benchmark.json docs/evidence/identity-benchmark/transfer-candidate-review.json --require-complete
```

The middle command intentionally exits 1 for B06. A complete class score does
not imply every sequence has a full test binding. The executed full repository
gate suite is retained in `results/full-gates.txt`; the additional subtest-binding
red probe and latest focused checker run are in `results/subtest-binding-red.txt`
and `results/checker-green.txt`.
