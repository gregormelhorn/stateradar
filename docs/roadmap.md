# Roadmap (post-v1.33)

## Current priorities

This is the project's existing roadmap. The entries below preserve historical
status reports and measurements from their stated versions; they are not a
fresh audit of every feature. The following outstanding work links to those
entries and separates the new model-routing plan from shipped capabilities.

1. **Measure cost-aware model routing.** Flash drafting, Jev batches, the
   `draft-verify` chain, a local ledger, and an offline batch evaluator exist,
   and `prompts/02-pilot.md` (v1.18) routes Steps 1, 6, 8 and Part B through
   them; two full routed pilots ran on silenceper/pool, the second blind to
   the benchmark and with executed as-is tests (entry 11). Next run a timed
   agent-only pilot of the same component, build independently reviewed
   examples, split held-out components or issues, and measure errors,
   coverage, time, and total cost of the routed pilot against the agent-only
   pilot. Only then evaluate selective escalation.
   Automatic acceptance and escalation are not implemented. Details: [model
   cascade plan](plan-model-cascade.md) and [entry
   11](#11-cost-aware-model-routing-deepseek-flash--jev).
2. **Broaden mutation coverage and validate on real components.** Continue
   [fault-class mutants](#8-ach-style-fault-class-mutants-testgen-upgrade):
   add supported classes and component bindings with observed red probes and
   behavioral kill evidence. Some fault shapes need additional observability;
   fixture results alone do not prove coverage on a consuming component.
3. **Make disposition rationale machine-readable.** Design and validate a
   representation for cell rationale before building checks that depend on it.
   See [machine-readable cell rationale](#10-machine-readable-cell-rationale).
4. **Evaluate bounded prompt optimization.** After sufficient independent
   benchmark cases exist, test a small sub-prompt against held-out cases; see
   [GEPA experiment](#9-gepa-experiment-the-feedback-loop-as-an-algorithm).
   Keep this separate from assuming that a more stable model answer is correct.
5. **Expand semantic reachability when needed.** The existing checker covers
   the minimal model; hierarchy and parallel regions remain a possible
   follow-up, described under [semantic analysis](#3-xstate--semantic-analysis).

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

## 10. Machine-readable cell rationale

**Status:** Planned. Measured at v1.52: 339 `ignore (documented)` cells across
all sidecars, **0** carrying a machine-readable rationale. Every justification
lives in matrix cell prose, where no checker reaches it — so "ignored because
harmless" and "ignored because it cannot occur" are indistinguishable to any
tool. Structural unreachability is expressed today through a defensive
disposition plus the upstream-guard annotation (see `prompts/02-pilot.md`);
a rationale field would let a checker verify that such a claim cites its
guarantee. Building that checker first would mean matching prose for words like
"unreachable" — the kind of heuristic this pack forbids for UV categories, so
the field comes first.

## 11. Cost-aware model routing (DeepSeek Flash + Jev)

**Status:** 🔶 Partially shipped (unreleased). `tools/local_models.py` sends
bounded drafts and the blind Part B to DeepSeek Flash and source-grounded
claim and ordering checks to Jev (`flash`, `jev`, `jev-batch`, `blind`,
`draft-verify`). A per-pilot SQLite ledger reserves estimated costs;
`tools/jev_eval.py` scores a saved batch against independently reviewed
labels. The pilot prompt's "Model routing" section maps Steps 1, 6, 8 and
Part B to these commands; a Jev judgment may add a question and never
removes one. 429/503/529 responses are retried with `Retry-After`.

Open, in order:

1. **Full routed pilot.** A first live smoke run (2026-11-13,
   device-connection example, 8,245 microdollars in total; outputs in
   `docs/evidence/routing-smoke-2026-11-13/`) exercised `draft-verify`,
   `jev-batch` and `blind` without provider errors. Its findings: Jev's
   ordering `choice` and scope probability disagree (`supported` with scope
   0.11), now handled by the pilot's routing rule 4; the same claim scored
   0.71 or 1.0 depending on the cited fragment; the blind coverage check saw 0
   pair orderings because the example catalogue carries no `P-` ids, so it
   cannot fail on missing pairs; and Flash's blind table used disposition
   wording outside the closed vocabulary, which the coverage check does not
   test.

   **First full routed pilot** (2026-11-13, silenceper/pool `channelPool`,
   pack da655aa, prompt v1.16, `jev-1.14.0`; outputs and comparison in
   `docs/evidence/routed-pilot-2026-11-13/`): 25,038 microdollars over 15
   calls (6 Flash, 9 Jev). It found the benchmark's primary finding (Release
   never unblocks waiters in `connReqs`), but not blind to it: the operator
   brief named the finding, and the Part-A agent's draft task for
   `channel.go` named the race as its example, so Flash raising it is not
   independent evidence either. 133 drafted claims had 0 citation failures.
   None of the 6 Step-6 orderings was backed by Jev (all `unclear`, scope
   0.02-0.05), so the provisional 0.5 veto fired on every `yes`; the agent's
   statements added detail the fragments do not mention, which seems to drive
   the score. Jev also judged equivalent claims about the same line
   differently (C59 and K5 `contradicted`, C78 `supported`). Against the
   agent-only baseline (whose two runs agree 28/28), with a state alignment
   and divergence judgments made by the pilot agent: 21 of 28 aligned base
   cells agree; of the 7 divergent cells, 1 differs only in its label, 3
   FactoryFail cells and 2 Close cells rest on baseline claims the code
   refutes in whole or part, and Released x Close turns on a doc comment. The
   comparison lists 13 questions new against the baseline plus 4 voided
   control verdicts (Q-20..Q-23; Q-22 and Q-23 the base scope rule raises
   anyway). Tool and prompt fixes from it: draft budget and truncated-draft
   handling, two hollow checks (sidecar fragments, `###` trace headers),
   doctrine lines written as a table never reached Part B, the Part-B
   catalogue copy without code fragments, line numbers and analysis ids,
   heading-style question ids, finding-neutral draft tasks, and the ODC
   trigger vocabulary (including `draft-verify` and `jev check`). Still open
   from it: prose in the catalogue that states as-is conclusions (mandatory
   remembrance, gate, upstream-guard and lock-discipline annotations) still
   reaches Part B, so Part-B agreement on those rows is not independent; the
   sidecar generator does not merge pairs, guard outcomes or ODC fields;
   `status` has no tokens, timestamps or step labels; the 0/6 orderings and
   the inconsistent claim judgments belong in the labelled set.

   **Second routed pilot** (2026-11-13, same component, pack a331dae, prompt
   v1.17, `jev-1.14.0`; outputs, as-is tests and comparison in
   `docs/evidence/routed-pilot-2-2026-11-13/`): blind to the benchmark
   (neutral brief; the checkout excluded `docs/`, `tests/benchmarks/`,
   `README.md` and `CHANGELOG.md`; finding-neutral draft tasks). 22,826
   microdollars over 20 calls (7 Flash, 13 Jev), about 37 minutes wall
   clock, of which the model calls took about 70 seconds; no provider
   errors. Flash's `channel.go` draft raised the primary finding as its
   first question, and the agent's Q-01 matches it; all six expected
   baseline questions have a counterpart (Q-05 only partly, its
   counter-drift premise is refuted by the code). Executed as-is Go tests:
   22 of 23 observe their claim, T5 reports the as-is data race on the ping
   function, and the repository's own `TestPool_Get` hangs until the
   timeout. Jev backed 1 of 6 orderings (scope 0.58); two `yes` verdicts
   were voided at scope 0.30 and 0.31 and became questions; 51 Step-8 claim
   checks gave 44 supported, 5 unclear and 2 contradicted, all kept after a
   re-read. 19 of 28 aligned base cells agree with the agent-only baseline
   (first pilot 20 under the same counting rule, 21 as published): the same
   FactoryFail, Close and Released x Close divergences, plus lazy idle expiry
   marked accidental; the one-cell gap is not a measured regression. Part B:
   21 convergent rows (16 of the agreeing rows, 13 convergent and 3
   convergent-hole, depend on as-is prose in the catalogue) and 8 artefacts, mostly remembrance and upstream statements
   read as documented intent. Fixes from it: line numbers following a
   citation, `blind` stdout, the blockquote line in the Part-B task, the
   matrix wrapper template's pack path, and 02-pilot v1.18. Still open from
   it: the sidecar generator's missing pairs, guard and ODC fields (the
   pilot merged them with a per-run script); as-is prose in the catalogue
   reaching Part B (the pilot's candidate rule: remembrance and upstream
   statements carry the provenance "observed in code"). Next: a timed
   agent-only run of the same component in a fresh session, so time and cost
   compare like for like. Its `timing.md` shows where the 37 minutes went:
   about 70 s of Flash and Jev calls, about 3 minutes of `go test` (mostly
   three waits on the hanging `TestPool_Get`'s 60 s timeout) and about 32
   minutes of the steering agent's own work; the pack's Python tools are not
   a measurable share, so speeding them up would not shorten a run.
2. **Flash writes, the steering agent decides.** After the timed agent-only
   run: a pilot of the same component in which Flash drafts the bulk text
   (matrix cells, as-is tests) from the steering agent's decisions, and the
   steering agent only decides, checks citations and runs the gates. Measure
   wall clock, cost and finding quality against the same benchmark. The
   risk to watch: Step 8 of the second pilot found 2 contradicted and 5
   unclear among 51 checked Flash claims, so the judgment step stays with the
   steering agent in this pilot.
3. **Flash as the steering agent.** Only if pilot 2 holds the finding
   quality: the same component with Flash steering the whole run. Jev stays a
   verifier, since it checks claims and orderings and does not plan, read
   code or write files.
4. **Labelled evaluation set.** Collect attributed, independently reviewed
   labels for claim and requirement-scope checks across components (stage 1
   of the cascade plan), including races outside a requirement's scope and
   seam-contract cases. Keep a held-out group per component or issue.
5. **Calibrated thresholds, then escalation.** TypeSafe's cookbooks use
   vendor-calibrated cut-offs (0.7 per-field gate, 0.8 citation auto-accept,
   0.3/0.7 Noul bands). StateRadar adopts none of them until the labelled set
   supports a value. The pilot's provisional 0.5 scope cut-off is
   question-only (it can void a verdict, never accept one) and is the first
   value to calibrate; any escalation policy is compared end to end against
   the prior workflow.
6. **Known limits to design around.** Jev accepts 64k tokens per request and
   32k per question, so long sources need excerpting with provenance; English
   is its primary language, so non-English requirements need a measured
   accuracy check; aliases move with releases, so measurements pin
   `jev-1.14.0`. The ledger counts only calls through the tool, not the
   calling agent.
7. **Prompt research.** Repetition and nonce-based consistency studies, and
   feature discovery only after the labelled set exists (see entry 9).

## Positioning note (for the README, task-8 sweep)

Spec-Driven Development became the mainstream answer to vibe-coding
drift in 2025/26 (Spec Kit, Kiro, OpenSpec, BMAD; EARS notation in
the 2026 practice guides). StateRadar's category line: **"SDD for
temporal behaviour, with a checkable completeness criterion"** — the
level-2/3 niche ("From Code to Contract", 2026) that generic markdown
specs structurally cannot cover.
