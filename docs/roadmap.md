# Roadmap (post-v1.33)

## 1. CONVERGENCE.md — calibration data

**Status:** ✅ Baselines recorded.

**silenceper-pool-32** (2026-08-07, pack v1.37, 02-pilot v1.15): two independent
runs, aligned base grid 47/49 convergent (4.1 % cell divergence, single root
cause: one state-granularity decision), finding-level convergence 9/11 (82 %),
zero contradictory findings.

**device-connection** (2026-08-07, pack v1.49, 02-pilot v1.15): two independent
runs, aligned 5-state × 21-event grid 105/105 convergent (100.0 % cell
convergence, 0 divergent cells). 5 questions each run with identical IDs.
Zero structural findings. Run1 sidecar lacks line citations
(gen_analysis_sidecar transfer; dispositions are identical). Finding-level
convergence: 5/5 questions (100 %, same IDs). Zero contradictory findings.

Variance concentrates in undesired-variant slicing — the input for roadmap
entry 5 (ensemble convergence). Repeat per release.

## 2. Synthetic example ("Device Connection")

**Status:** ✅ Done. `examples/device-connection/` contains a 130 LOC
Python component, a README with 9 requirements, and a full Part A
analysis with Mermaid statechart and critical finding Q-02 (FAILED
backdoor via disconnect).

## 3. XState / Semantic Analysis

**Status:** ✅ Minimal version shipped. `tools/check_reachability.py`
verifies all states are reachable from the initial state and that
terminal states are marked. Selftest red case, CI-wired on golden-mini.
Full reachability over hierarchy/parallel regions is deferred until
needed — the `formats/analysis.schema.json` carries enough data.

## 4. Rules registry (single source for method rules)

**Status:** ✅ Shipped in v1.35. `formats/rules.toml` (vocab + F-xx
fault catalogue + rules with class/enforcement/checker_ref/
selftest_ref) is rendered by `tools/gen_rules.py` into the PA list in
00, the Step-5 lints and vocabularies in 02, AGENTS §5, and the README
finds list; drift fails CI. The VOCAB-x2 sync check is gone by
construction. Open follow-ups surface as registry warnings: selftest
backlog (TODO refs), five checker candidates (PA-4/7/10/17/22), ODC
backfill over the eleven pilot manifests
(`docs/plan-rules-registry.md` has the details).

## 5. Ensemble convergence (from CONVERGENCE measurement to mechanism)

**Status:** ✅ Shipped in v1.38. `tools/ensemble_convergence.py` takes
N independent pilot sidecars, normalizes state names, aligns events by
ID, computes cell-level convergence, and mechanically marks divergent
cells `UNSPECIFIED → Q` (Q-EC-nn with a divergence summary). Green/
red selftests wired into `tools/selftest/run_selftest.py`; exit code
non-zero on divergence for CI gating. The CONVERGENCE.md protocol now
points to the tool instead of the hand-written diff step.

## 6. Benchmark dating protocol (contamination-honest evidence)

**Status:** ✅ Shipped in v1.38. `tools/benchmark_evidence.py` reads
dating metadata from each case's `expected.json` and classifies into
*primary evidence* (issue published after model release) vs *regression
anchor* (rest). Fields: `issue_published`, `model`, `model_release`,
`model_cutoff`. All four wired benchmarks carry dating metadata;
two are primary evidence (valkey-glide-5803, meilisearch-6508),
two are regression anchors (grpc-go-2669, python-websockets-1527).
Classification logic selftest wired into run_selftest.py.

## 7. Matrix mutation checker (is the matrix strong enough?)

**Status:** ✅ Shipped. `tools/check_matrix_mutation.py` runs a declared cell
suite against isolated temporary matrix copies. A component opts in with
`matrix-mutation.json`. The checker supports transition-to-ignore, transition
target-swap, handle-to-ignore, and the reverse ignore/reject-to-handle
mutations. It reports killed and surviving
mutants. The deterministic selftest proves a weak suite fails and the
golden-mini suite kills every supported mutant.

## 8. ACH-style fault-class mutants (testgen upgrade)

**Status:** 🔶 Partially shipped — 5 of 22 fault classes operationalized
(F-01, F-02, F-04, F-05, F-14). The `fault-mutants.json` contract and
`tools/check_fault_mutants.py` prove a behavioral cell suite kills one
implementation mutant per class while a mirroring suite
survives. Remaining classes pending. Golden-mini now derives the F-01,
F-02, and F-05 fixture variants from component-local bindings
(`mutant-generation.json` plus `tools/gen_mutant_variants.py`). This
removes hand-authored drift in the fixture. It does not broaden operator
ownership: F-01 and F-02 remain matrix-level families and F-05 remains
implementation-level. **F-04 is now generated too**, so no golden-mini fault
variant is hand-authored and none can drift; the region-counting selftest gate
remains as a guard for any future hand-authored variant. Broader binder-driven
generation and real-component coverage remain pending.

The reverse matrix family (ignore/reject → handle) now runs on all four
matrix-level undesired-variant shapes in golden-mini: `UV-M1-lost` (F-12
loss), `UV-M2-stale` (F-15 out-of-order/stale), `UV-M2-conflict` (F-16
contradiction), and `UV-M1-spurious` (F-17 spontaneous commission). Each
column has three KILLED reverse-family mutants. This claims **F-12**,
**F-15**, **F-16**, and **F-17** with fixture proof.

It does **not** claim F-13 or F-18: delay needs clock injection and value needs
payload-effect projection. F-20 needs a terminal-progress shape, which is not a
UV column at all.

**F-14 (duplication) is now claimed** — 5 of 22 classes operationalised. It cost
more than F-05 despite the same `dup_count` projection, because its registry
precondition is "idempotence observable via repeated delivery plus counter": a
projection alone is not enough, the suite needs a *delivery rule*. The suite now
reads which events are duplication variants from the sidecar's coverage
bindings — never from the event name — and delivers those twice, as
`prompts/04-testgen.md` has required all along. The measured finding that forced
this: an idempotence break whose second delivery escalated state passed all 21
cells unnoticed (`MUT-005 SURVIVED fault=F-14`), because a single delivery
cannot observe idempotence by definition. Without the delivery rule an "F-14
mutant" would only have been a second F-05 under another name.

Kill proofs are now cause-checked rather than exit-code-correlated. A cell
suite must print `CELL FAIL <state> x <event>` per failing cell and
`CELL SUITE: <n> cells checked, <m> failed` on completion; without both,
`check_fault_mutants.py` reports `BLOCKED` instead of `KILLED`, and a kill whose
declared cell is absent from the reported ones is reported as
`KILLED (wrong cell)`. This closed a real hollow proof: F-04 once reported its
cell correctly and then crashed on a later one, so a pseudo-mutant carrying no
fault at all also scored `KILLED`. The contract is documented for future
components in `prompts/04-testgen.md`. `check_matrix_mutation.py` was left
unchanged, because its 25 mutants were measured to die at exactly the mutated
cell with zero crashes.

**Prior status:** Planned — after 7, together with the F-catalogue. Meta's
ACH (FSE 2025) generates few, fault-class-targeted mutants and then
tests that kill exactly those, instead of broad mutation scatter; the
Assured-LLMSE frame (Alshahwan/Harman) names per-artifact assurances
(buildable, non-flaky green). Coupling to our registry is natural:
the F-xx classes ARE the mutation operators ("violate cell X via
sneak path"), and 04-testgen hardens the cell test against that
mutant. Replaces the after-the-fact mutmut honesty probe with
targeted, per-class hardening.

## 9. GEPA experiment (the feedback loop as an algorithm)

**Status:** Planned — once the benchmark suite has a few more cases.
GEPA (arXiv:2507.19457, ICLR 2026 oral, in DSPy) optimizes prompts by
natural-language reflection over execution trajectories and needs a
textual feedback function — which the pack already has: checker
outputs and Part-B diff classes. Our manual cycle (divergence classes
folded into the pilot changelog) *is* GEPA by hand. First step: not
the whole 380-line pilot — evolve one bounded sub-prompt (e.g. the
Step-3 UV-checklist section) against the benchmark suite and see
whether the machine finds rules eleven human-run pilots did not.
Order of operations is already right: measurement harness first,
optimizer second.

## Positioning note (for the README, task-8 sweep)

Spec-Driven Development became the mainstream answer to vibe-coding
drift in 2025/26 (Spec Kit, Kiro, OpenSpec, BMAD; EARS notation in
the 2026 practice guides). StateRadar's category line: **"SDD for
temporal behaviour, with a checkable completeness criterion"** — the
level-2/3 niche ("From Code to Contract", 2026) that generic markdown
specs structurally cannot cover.
