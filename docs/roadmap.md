# Roadmap (post-v1.33)

## 1. CONVERGENCE.md — calibration data

**Status:** ✅ Baseline recorded (2026-08-07, pack v1.37, 02-pilot
v1.15): two independent runs, aligned base grid 47/49 convergent
(4.1 % cell divergence, single root cause: one state-granularity
decision), finding-level convergence 9/11 (82 %), zero contradictory
findings. Variance concentrates in undesired-variant slicing — the
input for roadmap entry 5 (ensemble convergence). Repeat per release.

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

**Status:** Planned — priority 1 (cheap, turns an existing weakness
into a feature). The 2024–26 LLM-FSM-inference literature (ProtocolGPT
arXiv:2405.00393, FlowFSM arXiv:2507.11222, SpecGPT arXiv:2510.14348)
runs multiple independent extractions and votes: transition
intersection = high confidence, symmetric difference = automatic
question candidates. Our CONVERGENCE protocol only *measures*
divergence; the upgrade is to *use* it — run the pilot 2–3×, diff at
cell level with tooling, and mechanically mark divergent cells
`UNSPECIFIED → Q` instead of comparing by hand. Turns the calibration
advice into a pack feature.

## 6. Benchmark dating protocol (contamination-honest evidence)

**Status:** Planned — priority 1 (cheap; makes the evidence section
self-writing). Knowledge cutoff only bounds pretraining; post-training
on newer data is common, so "issue predates cutoff" is not the right
caveat. Adopt the LiveCodeBench / CWE-Trace pattern: every case
manifest gains `issue_published`, `model`, `model_release`,
`model_cutoff`; the benchmark runner classifies cases automatically
into *primary evidence* (issue published after model release) and
*regression anchor* (rest). The 2026-08 pilots are already de-facto
rolling collection — only the protocol formalization is missing.

## 7. Matrix mutation checker (is the matrix strong enough?)

**Status:** Planned — priority 2 (biggest insight per effort).
MutDafny (ICSE 2026) mutates *specifications*, not code. Transfer:
mutate matrix cells (`transition→ignore`, target swap, guard
negation) and check whether the generated cell suite notices.
Surviving matrix mutants = under-tested cells. Answers the question
the pack leaves open today: not "is the matrix total" but "do its
tests defend it". A new checker beside dsc_check/reachability, with a
red selftest, per house rule.

## 8. ACH-style fault-class mutants (testgen upgrade)

**Status:** Planned — after 7, together with the F-catalogue. Meta's
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
