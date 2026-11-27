# StateRadar

**Find the missing transition.**

Most defects in asynchronous, stateful code are not wrong lines. They are
*absent* ones — the state/event combination nobody specified, the timeout
with no guaranteed exit, the terminal state that quietly is not terminal.
Code review reads control flows one at a time and cannot see what is not
there. Line coverage cannot either: you can hold 100 % coverage over a
component whose contract has a hole in it.

StateRadar reconstructs, independently, (1) what behaviour the requirements
demand, (2) what state model the implementation actually realizes, and (3)
where the two disagree — and turns the answers into tests and CI gates.

> Model-based testing checks code against a model.
> StateRadar first checks whether the model deserves to be the oracle.

**Version 1.53.** Apache-2.0, prompts included. Runs inside your AI coding agent;
no build step or StateRadar service. The optional local model workflow sends the
supplied text to hosted model providers (see
[Global Side Effects](#global-side-effects)). Project terms are defined in
the [Glossary](#glossary) under System Overview, near the end.

---

## A bug, in one table row

`examples/device-connection/` ships a 147-line async component with nine
written requirements. R-05 says:

> The component remains in FAILED state permanently.

The pilot walks every state against every event and fills one cell per
combination. Here is the row for `FAILED`, with citations re-anchored to the
current source:

| state | connect | disconnect |
|---|---|---|
| **FAILED** | reject `device_connection.py:81-82` ("device is in FAILED state") | transition →DISCONNECTED `device_connection.py:88-97` (no FAILED guard in disconnect) → **Q-03** |

`connect()` guards FAILED. `disconnect()` does not — it unconditionally
assigns `state = DISCONNECTED`. So the terminal state has a back door, the
requirement is contradicted, and nothing in the test suite fails, because no
test ever drove that pair.

The finding lands as a question with a citation, a fault class, and a
proposed resolution — not as a vague review comment:

```
Q-03  disconnect() from FAILED transitions to DISCONNECTED, contradicting R-05
      ODC: F-06 (trap door), F-19 (unimplemented requirement)
      Trigger: step-4 matrix walk
      Status: OPEN
```

The same shape shows up in production code. In `valkey-glide` #5803 the
`(CallerTimedOut, release_permit)` cell was UNSPECIFIED — and that was
exactly the reported bug. In `python-websockets` #1527 it was
`(ClosurePending, CloseDeadlineExpired)`. The hole in the table *is* the
defect.

---

## The completeness criterion

The reason a hole is visible at all: every cell of the state × event grid
must carry a disposition from a closed vocabulary — `transition`, `handle`,
`ignore`, `reject`, `defer`, and friends. An empty cell is not an omission
you can shrug at. It is `UNSPECIFIED`, it maps mechanically to an open
question, and the checker fails the build until a human decides it.

That is the whole trick. "Did we think of everything?" is normally
unanswerable. Against a total grid it becomes a diff.

Every filled cell carries a fragment citation (`file:line ("code")`) or a
decision record. Claims without evidence do not pass the checker.

---

## How it works

**Part A — code-informed analysis.** An agent reads the requirements, the
code, and the tests of ONE bounded component and reconstructs the
implemented model: states, events, guards, the disposition matrix,
invariants, adversarial traces, open questions.

**Part B — the blind run.** A second, independent session gets three inputs
and nothing else: the event catalogue, the prose requirements, and the
contract text of each event type. No code. No matrix. No traces. From those
alone it must say, for every event, whether the component should handle,
ignore, or reject it.

**The blind diff.** The two models are compared cell by cell, and every
difference is classified: `convergent`, `convergent-hole`, `divergence`
(must end as a question), `artefact` (repair the catalogue), or
`pass-B blind spot`.

Part B exists because Part A has a trust problem with a name: **mirroring**.
An agent that read the code produces a model that matches the code by
construction, and you cannot tell whether a cell records a requirement or
rationalizes an accident. Blindness is the mechanism, not a ritual — an
agent that has seen the matrix cannot un-see it.

Worked example: on a real component, the pilot found the code contradicting
its own docstring, and the owner decided *for the code*. The blind pass knew
none of that and derived the same behaviour from the requirements alone.
Three independent sources agreeing — code, owner, requirements. Cost: one
subagent run.

---

## What you actually run

Vendor the pack, then drive it from your agent:

```bash
git submodule add https://github.com/gregormelhorn/stateradar tools/prompt-pack
git -C tools/prompt-pack checkout v1.53
```

For Claude Code, drop in the skill and the slash commands:

```bash
ln -s ../../tools/prompt-pack/skills/claude-code/stateradar .claude/skills/stateradar
cp tools/prompt-pack/commands/*.md .claude/commands/
```

Then the loop:

```
DISCOVER   01 Scout ......... rank the stateful components, pick one
MODEL      02 Pilot ......... as-is model, matrix, traces -> open questions
           (you) ............ answer them                              <-- human
           03 Resolution .... decision records + to-be model
           Part B ........... blind adversarial pass, fresh session
ENFORCE    04 Testgen ....... one test per cell + checkers + CI gate
           05 Standing ...... future agent sessions stay disciplined
MAINTAIN   06 Reconcile ..... to-be becomes as-is; manifest pins the SHA
           07 Test audit .... judge an existing suite against the matrix
```

Run the deterministic layer locally at any point (paths as vendored above):

```bash
uv run --with-requirements tools/prompt-pack/tools/requirements-dev.txt \
  python3 tools/prompt-pack/tools/dsc_check.py domain-analysis/<component> --repo .
```

### Cost-aware model workflow

The optional [local model workflow](docs/local-model-routing.md) uses DeepSeek
Flash for bounded drafts and extraction, and Jev for narrow source-grounded
checks. Independent checks against the same source can be batched, and
`draft-verify` chains both: Flash drafts cited claims, code checks the
citations, Jev judges them. The pilot prompt routes extraction, scope checks,
citation verification and the blind Part B through these commands. Code checks
citations and structure; a reviewing agent inspects every model judgment, and
the human owner decides domain semantics. The blind Part B keeps its restricted
inputs. A per-pilot ledger estimates the cost of calls made through the tools;
it does not cover the calling agent or other providers. Keys, metering
and billing are listed under [Global Side Effects](#global-side-effects).

The [model cascade plan](docs/plan-model-cascade.md) sets out the next steps:
independently reviewed cases, a held-out quality and cost comparison, and only
then a calibrated experiment that escalates selected cases to stronger review.
A first [fragment-label routing evaluation](docs/evidence/routing-labels/README.md)
compares Jev and direct Codex on 20 AI-reviewed checks, followed by a separate
post-comparison Flash→Jev diagnostic. Both direct judges match 19/20 references
with different discrepancies; the examples are previously exposed and not a
full pilot. Automatic acceptance or escalation is not enabled, and end-to-end
savings are not established. See the [project roadmap](docs/roadmap.md).

After stage 04 the discipline is CI-enforced in *your* repo. Breaking a
disposition, a decision link, a guard proof, or cell coverage breaks the
build.

---

## What lands in your repository

The pack itself is stateless — every artifact lives in the consuming repo:

- `domain-analysis/<component>/disposition-matrix.md` — the total grid, cited
- `event-catalogue.md` — events, undesired variants, interaction pairs
- `open-questions.md` — findings a human must decide
- `decisions/DR-*.yaml` — the decisions, linked from the cells they justify
- a Mermaid statechart, checked against the matrix for drift
- one generated test per cell, plus `check_matrix.py` and `check_guards.py`
- `analysis.json` — the machine-readable sidecar the checkers verify
- `manifest.json` — pins the analyzed SHA, so staleness is a CI signal
  rather than a guess

---

## How the tests get judged

Generated tests are only worth their CI time if they actually bind to
behaviour. Two mutation layers answer that, and they measure different
things:

**Spec mutants** (`tools/check_matrix_mutation.py`) mutate the *matrix* —
`transition → ignore`, target swap, `handle → ignore`, and the reverse
`ignore`/`reject → handle` — and run the declared
cell suite against unchanged code. A suite that stays green is reading its
own hardcoded expectations, not the spec. Vacuous green has nowhere to hide.

**Fault mutants** (`tools/check_fault_mutants.py`) mutate the *code*, one
named fault class at a time, and ask whether the suite notices. The classes
come from Binder's state-machine fault taxonomy plus empirical additions,
registered as F-01..F-22 in `formats/rules.toml`. Fixture coverage includes
F-01 missing transition, F-02 transfer fault, F-04 sneak path, F-05 corrupt
state and F-14 duplication. F-09 cancellation-leak bindings are executed on
both weighted semaphore and grpc-go addrConn.
Results report `KILLED / SURVIVED / BLOCKED` — never a bare rate. Declared
projection canaries execute before dependent mutants; incomplete or wrong-cell
results cannot count as kills. The required `expectedCells` pins the suite's
nonempty size. [Execution contract and migration](docs/fault-mutants.md).

This is mutation-guided test assessment in the spirit of Meta's ACH work,
with one structural difference: because each mutant *is* an instance of a
named class by construction, "is this mutant relevant?" is a label rather
than a judgment call — and equivalence is decided against the matrix instead
of by an LLM judge.

Component-local bindings generate the six golden-mini and five semaphore
variants, plus three addrConn backoff variants (two canaries and one F-09 fault).
[Second-component F-09 proof](docs/evidence/addrconn-f09/README.md).

**Late-completion scenario checks** (`tools/late_completion.py`) consume a
language-neutral profile and recorded observations for operation → termination
→ completion, with completion → termination as a required positive control.
They verify terminal state/publication, emitted effects and exactly-once resource
release; malformed or incomplete traces are BLOCKED. Component adapters own
scheduling and actual discovery. The first reference, pinned grpc-go addrConn,
uses the accepted DR-001 evaluation patch, two F-04 mutants and four independent
state/publication/output/resource canaries. It is validated on this
reference, not yet on a second component. These three scenario checks are not
a complete state/event matrix, and the idle fake transport does not validate
transport internals.
[Contract and adapter guide](docs/late-completion.md) ·
[Executed evidence](docs/evidence/late-completion/README.md).
The Testgen workflow additionally checks a reviewed applicability inventory,
trace/cell/DR bindings and fresh execution receipts with
`tools/check_late_workflow.py`. Plan-only passes are separate from replayed
execution evidence. Gobreaker was assessed with an executed public-API probe:
its generation rollover is outside the terminal/idle-resource contract, so this
is not a second adapter validation.
[Workflow evidence and limits](docs/evidence/late-workflow/README.md).

**Bounded prompt optimization (experimental)** connects GEPA to isolated Codex
ChatGPT-login calls, Flash/Jev drafts, component-separated evaluation and complete
child-call accounting. The first experiment evaluates 28 supplied claims across
four components. Both fixed and GEPA final reviews correct all six seeded errors
and add the same timer-scope qualification; neither demonstrates a quality
advantage over the other. This is claim review, not open-ended bug discovery or
full-pilot optimization. The standard routing is unchanged.
[Results, costs and limitations](docs/evidence/gepa-bounded/README.md).
A follow-up [supervised discovery experiment](docs/evidence/gepa-discovery/README.md)
uses source-backed open findings and held-out components. GEPA retained the fixed
seed, so the final arms used identical prompts; no GEPA advantage is established.
The subsequent [reviewed training catalogue and fixed baseline](docs/evidence/gepa-training-catalog/README.md)
records recurrent source-scope gaps and controls; it is not a new GEPA optimization.
A [new component-split GEPA experiment](docs/evidence/gepa-heldout/README.md)
trained on that catalogue and again selected the unchanged prompt. Separate
exploratory results and AI-review uncertainty are retained; no human review or
GEPA improvement is claimed. A subsequent [prospective comparison and tie audit](docs/evidence/gepa-prospective/README.md)
reproduces GEPA's index-based exact-tie behaviour, reports ties without a winner,
and compares both prompts on two further components.

---

## Evidence

12 pilots across real upstream projects, 12 bugs found, 6 issues filed:

| Project | Bugs | Notes |
|---|---|---|
| recws-org/recws | 7 (2 critical) | #64 shutdown panic; `log.Fatalf` kills the process |
| meilisearch/meilisearch | 3 | double release (#6578), missing increment (#6577), multipart cancel detach (#6510) |
| silenceper/pool | 1 | `connReqs` never closed on Release |
| sony/gobreaker | 1 | stale `done()` silently dropped (#122) |
| pladaria/reconnecting-websocket | 1 critical | terminal lock leak |
| valkey-io/valkey-glide | 1 critical | missing timeout → release transition |

Six benchmark cases are Oracle-confirmed and wired as reproducible
regression anchors, with the contamination caveat stated rather than hidden:
issues published before the model's training cutoff are classified as
*regression anchors*, not as discovery evidence. The classifier is a tool
(`tools/benchmark_evidence.py`), not a claim in prose. Full per-case
analysis: [`tests/benchmarks/README.md`](tests/benchmarks/README.md).

---

## How reliable is a single run?

An LLM-in-the-loop method owes you a variance number. Two independent
fresh-session pilots on the same component, diffed mechanically by
`tools/ensemble_convergence.py`:

| Component | Aligned grid | Cell convergence | Findings |
|---|---|---|---|
| `silenceper/pool` | 47/49 base cells | 95.9 % (one state-granularity root cause) | 9/11 found by both, zero contradictory |
| `examples/device-connection` | 5 × 21 = 105 cells | 100 % | 5/5 questions, identical IDs |

Read the second row with the caveat it deserves: device-connection is the
pack's own synthetic example. The pool number is the one measured on
foreign code.

Divergent cells are not averaged away — the tool marks them
`UNSPECIFIED → Q` and exits non-zero, so disagreement becomes a finding
instead of noise. Calibration tip: run the pilot twice on your own component
and diff. The divergence tells you how far to trust any single run.

---

## Scope

**Use it for** lifecycles, connections, protocols, async workflows, retries,
timeouts, cancellation, recovery, sessions, mutually exclusive modes.
Typical target: one bounded component, roughly between 200 and 1,500 LOC of lifecycle
code, with requirements somewhere — README, docstrings, API contracts, or
tests.

**Do not use it for** pure calculations, stateless transforms, formatting,
validation, or CRUD without temporal behaviour.

StateRadar is not a general AI code-review bot, a linter, a security
scanner, a UML tool, a model checker, a formal proof, or a replacement for
tests and human review. It is a verification workflow for lifecycle
contracts.

---

## What StateRadar finds

The fault-class catalogue behind this list lives in `formats/rules.toml`
(F-xx ids; the italic names are Binder's state-machine fault taxonomy,
which the matrix's completeness makes testable):

<!-- generated:rules key=readme-finds -->
* missing State/Event transitions and `UNSPECIFIED` matrix cells (*missing transitions*);
* timeout events without guaranteed progress;
* caller operations blocked after a terminal event;
* internal requests holding resources after a caller timeout;
* unbounded waits;
* invalid recovery or reconnect paths (*transfer faults*);
* wrongly coupled lifecycle regions (caller vs. internal);
* lost or overwritten failure causes (*output faults*);
* missing idempotency in cleanup and release;
* events accepted where the specification says ignore or reject (*sneak paths*);
* requirements without a complete execution path;
* implementation paths without a documented contract (*trap doors*);
* tests that assert internal states but not caller-visible behaviour.
<!-- /generated:rules -->

---

## Adopting it in a brownfield repo

Per component, in levels — each needs everything below it:

```
L1 descriptive   extraction + as-is statechart + disposition matrix
L2 decided       + open questions, DRs for decided cells, hole -> Q links
L3 enforced      + one cell test per matrix cell + matrix-coverage.json
L4 verified      + analysis.json sidecar, dsc_check OK, CI gate wired
L5 steady state  + reconciled manifest at HEAD, standing instruction active
```

Rules of thumb from consumer experience:

- **The directory is the authority.** Any component with
  `domain-analysis/<component>/` is governed at its level. Never hardcode a
  component list — it goes stale at the next pilot.
- **No reconcile-lite.** A manifest bump without a sidecar and a green
  `dsc_check` is bookkeeping, not a reconcile.
- **Generate sidecars, never hand-write them.** Fix the matrix, regenerate.

Start with one component. The Scout stage exists to tell you which one.

---

## Repository layout

```
prompts/     the canonical method, harness-neutral Markdown
             00 methods reference · 01 scout · 02 pilot · 03 resolution
             04 testgen · 05 standing instruction · 06 reconcile · 07 test audit
formats/     rules.toml (rules + F-xx fault catalogue + closed vocabularies),
             analysis.schema.json, manifest.schema.json
tools/       the deterministic layer — see below
skills/      Claude Code skill packaging
commands/    optional slash commands
examples/    reference components: device-connection, grpc-addrconn,
             weighted-semaphore, gobreaker readiness fixture
tests/       benchmark suite, Oracle evidence, golden/red fixtures
docs/        roadmap and design documents
```

The contract READMEs for these directories are indexed in
[Subdirectories & System Boundaries](#subdirectories--system-boundaries).

The deterministic layer, grouped by what it is for:

- **Check an analysis:** `dsc_check`, `check_matrix`, `check_reachability`,
  `guard_proofs` (z3 disjointness / coverage / boundary)
- **Generate, never hand-write:** `gen_analysis_sidecar`,
  `gen_matrix_scaffold`, `gen_rules`, `gen_odc_table`
- **Blind pass:** `part_b_pack`, `dsc_blind`, `dsc_cross_check`
- **Judge the suite:** `check_matrix_mutation`, `check_fault_mutants`
- **Measure the method:** `ensemble_convergence`, `run_benchmark`,
  `benchmark_evidence`
- **Maintain:** `refresh_citations`, `dsc_stamp`, `dsc_compose`,
  `check_pack_consistency`

---

## Running the checkers

System Python on macOS is PEP-668 externally managed. `uv` supplies the
pinned dev dependencies (`tools/requirements-dev.txt`: jsonschema for the
sidecar contract, z3-solver for guard proofs) without touching it:

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/dsc_check.py <analysis-dir>
```

Missing optional dependencies degrade **loudly**. Without `jsonschema`,
`dsc_check` refuses to validate the contract and says so; `--allow-no-schema`
accepts structural checks only — a deliberate reduction in coverage, never a
silent one.

The full first-run gate list is in [System Verification](#system-verification).

---

## Why the checkers are trustworthy

A gate that has only ever run against passing input is a gate nobody tested.
The pack's own selftest therefore runs every checker **red as well as
green** — silent omission, drifted citations, a diagram out of sync with the
matrix, a snake_case manifest key, overlapping or gapping guard groups. Each
must fail:

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/selftest/run_selftest.py
```

The same standard applies to the project's own history. When v1.47 shipped a
"fix" that injected identical synthetic data into both sides of a
comparison, the v1.48 entry says so in the changelog and names it a hollow
fix. Corrections stay in the record. If you are evaluating whether to trust
the numbers above, that history is the more useful artifact.

---

## Claims

StateRadar currently claims, credibly:

- detects missing lifecycle transitions in real asynchronous components;
- separates requirement-level defects from implementation mechanisms;
- identifies incorrect coupling between caller-visible and internal
  lifecycles;
- detects unspecified, untested, or unimplemented state/event combinations;
- produces traceable findings before known upstream bug information is
  revealed;
- turns approved lifecycle decisions into executable tests and CI checks;
- detects weak cell suites by deterministic matrix mutation, and per-class
  suite strength by fault-class mutation.

It does **not** claim to find all defects, to guarantee correctness, to
replace code review, to provide formal proofs, to have no false positives,
or to work without usable requirements.

---

## Versioning and contributing

Pack versions are git tags (`v1.53`), mirrored in
[`CHANGELOG.md`](CHANGELOG.md). Consumers pin a tag; an analysis directory
records the pack version that produced it. The pilot prompt carries the
method's own feedback-loop changelog — divergence *classes* found by blind
passes get folded back into the rules there.

Issues and pull requests are welcome, and pilot reports on your own
components are the most useful contribution of all: the method improves from
real divergences, not from hypotheticals.

---

## License

Copyright 2026 Gregor Melhorn.

Licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).
This covers the prompt texts and the skill files as well — copying and
adapting them is the intended use. Apache-2.0 adds an express patent grant,
which the MIT License did not carry.

Releases up to and including v1.50 were published under the MIT License.
Those versions remain available under the MIT terms; the relicensing applies
going forward and is not retroactive.

---

## System Overview

The sections above describe the method. The sections below are the
repository's contract index for agents and developers.

`tools/` and `examples/` have [contract](#glossary) READMEs. The other entries
in [Subdirectories & System Boundaries](#subdirectories--system-boundaries) say
where their documentation lives instead; `tests/README.md` and the skill's
`SKILL.md` are documentation, not contracts. An agent can learn what a directory
promises without reading its code.

Some code has its contract in the parent README under "Child contracts":

- `examples/device-connection/` (code): its own README is the requirements
  document that a blind Part B session reads, so code-observed facts must not
  go there. Contract:
  [examples/README.md](examples/README.md#device-connection)
- `examples/grpc-addrconn/late-completion/` →
  [examples/grpc-addrconn/README.md](examples/grpc-addrconn/README.md#late-completion)
- `examples/weighted-semaphore/semaphore/`, `cells/` and `schedule/` →
  [examples/weighted-semaphore/README.md](examples/weighted-semaphore/README.md#semaphore),
  [#cells](examples/weighted-semaphore/README.md#cells) and
  [#schedule](examples/weighted-semaphore/README.md#schedule)

The addrConn and semaphore folders above are watched by a manifest (see
`watchPaths` in the [glossary](#glossary)). Adding a README there would make
the analysis stale.

The repository has two layers:

- the method: harness-neutral prompts in `prompts/`, with the registry in
  `formats/rules.toml`;
- the deterministic layer in `tools/`: checkers, generators and runners that
  verify the data an agent emits.

`examples/` shows complete analyses of reference components.

### Glossary

- **pack**: this repository, vendored into a consumer repository (for example
  as `tools/prompt-pack`).
- **contract**: a README that states what a directory promises. Component
  directories use Overview, Interface, Invariants, Side Effects and
  Verification; grouping directories use Overview and Subdirectories &
  Boundaries.
- **harness**: in "harness-neutral prompts", the agent tool that runs the
  prompts, such as Claude Code or Codex. A *test harness* (as in
  `harness-manifest.json`) is the pack code that drives a component's tests.
- **pilot**: one run of the `02 Pilot` prompt on one component. It produces
  the as-is model, the matrix and open questions.
- **Scout**: the `01 Scout` prompt, which ranks candidate stateful components.
- **Part A / Part B**: Part A is the code-informed analysis. Part B is the
  blind pass from the event catalogue and requirements only; see
  [How it works](#how-it-works).
- **R-nn**: a numbered written requirement of a component.
- **as-is / to-be**: the model the code implements today, and the model after
  the decided changes.
- **reconcile / reconcile-lite**: reconcile (`06 Reconcile`) promotes to-be to
  as-is, refreshes citations and re-pins the manifest. Reconcile-lite means
  bumping a manifest without that work, which is forbidden; see
  [Adopting it in a brownfield repo](#adopting-it-in-a-brownfield-repo).
- **disposition matrix / cell**: the state × event grid in
  `disposition-matrix.md`. Each cell carries one disposition from the closed
  vocabulary in `formats/rules.toml`.
- **sidecar**: `analysis.json`, the machine-readable analysis that the
  checkers consume. It is normally generated from the matrix.
- **oracle**: whatever supplies the expected behaviour that tests compare
  against, such as a sidecar or `tools/late_completion.py`. This is distinct
  from *Oracle-confirmed* below.
- **manifest / `analyzedSha` / `watchPaths`**: `manifest.json` (or a named
  `*-manifest.json`) pins the commit an analysis was made at (`analyzedSha`).
  It also lists the paths it depends on (`watchPaths`). A committed change
  under a watched path after `analyzedSha` makes the manifest stale.
- **`WORKTREE`**: the placeholder `analyzedSha` of a manifest that is not yet
  pinned. `dsc_check` skips the staleness check for it. The addrConn runners
  refuse it as "unanchored".
- **DR-nnn / Q-nn**: a decision record holding the human owner's answer, and
  an open or answered question. Numbers are per component analysis, so the
  DR-001 records of two examples are unrelated.
- **NAT / SYS invariant**: NAT is an assumption about the environment. SYS is
  an obligation of the system, checked state by state.
- **F-xx**: a fault class in `formats/rules.toml`, for example F-04 sneak path
  or F-09 cancellation leak.
- **UV event**: an undesired-variant event, such as loss, delay or
  duplication. Each is derived from the seven-category undesired-event
  checklist in `formats/rules.toml`.
- **hole cell**: a matrix cell whose disposition is `UNSPECIFIED` or
  `ignore (accidental)`. Every hole must link a question (`→ Q-nn`).
- **guard group (`G-nn`)**: usually the branch conditions at one decision
  point, which z3 checks for disjointness and coverage. A group can instead
  hold other z3 proof obligations, or be recorded as `not-formalizable` with
  a reason.
- **DOC-n**: a doctrine line, one normative sentence extracted from the
  requirements; each must map to a cell, an invariant or an explicit
  rejection.
- **T-nn trace**: an adversarial trace, a scripted event ordering in
  `adversarial-traces.md` with its expected outcome.
- **interaction pair (`P-nna/b`)**: two events from different sources on one
  entity, tested in both orders.
- **public seam**: the interface that tests may assert through. It covers
  projected state, emitted effects and SYS invariants, never internals.
- **projection**: one observable aspect of behaviour at the seam, for example
  state, publication, emitted effect or resource release. The word also names
  a reduced slice of a model, such as the six-cell addrConn projection or the
  semaphore's projected queue states.
- **test discovery**: confirmation that every expected test or subtest started
  and finished the expected number of times. Incomplete test discovery yields
  BLOCKED, never a pass or a kill. Elsewhere in this README, "discovery"
  means finding bugs.
- **red probe**: a deliberately broken input that a checker must reject. It
  proves the check can fail.
- **canary / mutant / mutation binding**:
  - A spec mutant changes the matrix; a fault mutant changes the code.
  - A canary is a deliberately broken variant that proves a projection is
    observable. Dependents declare it with `requiresProjection` and count
    only after it is killed; see [docs/fault-mutants.md](docs/fault-mutants.md).
  - A binding connects a component's suite to the mutation tools.
- **KILLED / SURVIVED / BLOCKED**: mutation verdicts. KILLED means the suite
  detected the mutant. SURVIVED means it did not. BLOCKED means no verdict
  could be reached, for example because test discovery was incomplete or a
  required canary was not killed.
- **weak suite**: a deliberately reduced test suite used as a control, for
  example one that asserts only state or only an API result. It must miss the
  faults that the full suite kills.
- **late-completion**: an operation that completes after its component has
  terminated. `tools/late_completion.py` checks it; see
  [docs/late-completion.md](docs/late-completion.md).
- **readiness probe**: a bounded check of whether a component fits the
  late-completion contract before an adapter is written.
- **Oracle-confirmed**: a benchmark finding that matches a published upstream
  issue, which serves as ground truth; see
  [tests/benchmarks/README.md](tests/benchmarks/README.md).
- **Flash / Jev**: hosted models used by the
  [cost-aware local model workflow](#cost-aware-model-workflow), also called
  local model routing.
  - DeepSeek Flash drafts.
  - Jev is [Typesafe](https://docs.typesafe.ai/)'s hosted judgment API. It
    answers narrow source-grounded checks.
  - "Local" refers to the pack-local CLI, not on-device inference; see
    [docs/local-model-routing.md](docs/local-model-routing.md).
- **GEPA**: an external prompt optimizer (the `gepa` Python package),
  evaluated in
  [docs/evidence/gepa-bounded/README.md](docs/evidence/gepa-bounded/README.md).
- **Codex runner / Sol**: a tool that starts
  [Codex CLI](https://github.com/openai/codex) sessions on the signed-in
  account, which uses its quota or billing. Sol is the default Codex model
  `gpt-6.1-sol`.
- **golden-mini / red-mini**: `tests/golden-mini` is a 3-state fixture
  component and the tools' golden regression case; `tests/red-mini` is a
  deliberately drifted case that proves the gates catch drift.
- **MCP**: Model Context Protocol, the protocol some pilot runners use to
  expose commands to a Codex session.
- **ODC**: Orthogonal Defect Classification (Chillarege et al., 1992). In
  this pack, ODC fields on findings are rule `R-ODC-FIELDS` in
  `formats/rules.toml`.
- **`AGENTS.md`**: the standing instruction file for AI agents working in
  this repository.

## Subdirectories & System Boundaries

- tools: [`./tools/README.md`](./tools/README.md) - the deterministic layer
  (about 85 Python scripts), with contracts for `templates/` and `selftest/`.
- examples: [`./examples/README.md`](./examples/README.md) - reference
  components and their analyses: device-connection, grpc-addrconn,
  weighted-semaphore and the gobreaker readiness fixture.
- skills: [`./skills/claude-code/stateradar/SKILL.md`](./skills/claude-code/stateradar/SKILL.md) -
  the Claude Code skill packaging.
- tests: [`./tests/README.md`](./tests/README.md) - the golden-mini and
  red-mini tool fixtures, the Oracle benchmark evidence and the
  device-connection convergence baseline.
- prompts, formats, commands, docs: (no contract) - Markdown, TOML and
  JSON-schema method files, not code packages; see
  [Repository layout](#repository-layout).
- .github: (no contract) - the CI workflow `pack-ci.yml`; mapped under
  [System Verification](#system-verification).
- docs/evidence: (no contract) - frozen evidence archives, each documented by
  its own README. A few of their scripts are called by current gates, such as
  `docs/evidence/semaphore-pilot/resolution-q01/check_guards.py` and
  `docs/evidence/generic-canary/scripts/semaphore_weak_control.py`. They are
  not edited as live packages.

## Global Invariants

- The sidecar is generated from the matrix (`tools/gen_analysis_sidecar.py`)
  and is never hand-edited. One component inverts this:
  [weightedSemaphore](examples/weighted-semaphore/domain-analysis/weightedSemaphore/README.md).
- `formats/rules.toml` is the registry for rules, F-xx fault classes and
  closed vocabularies. `tools/gen_rules.py --check` requires the generated
  blocks to match it. Those blocks are in `README.md`, `AGENTS.md`,
  `prompts/00-methods-reference.md` and `prompts/02-pilot.md`.
- Staleness:
  - A committed change under a manifest's `watchPaths` makes that manifest
    stale until the analysis is reconciled and `analyzedSha` is re-pinned.
  - Watched paths include
    `examples/weighted-semaphore/{semaphore,cells,schedule,mutants,faults}`
    and `examples/grpc-addrconn/{tests,late-completion}`. They also include
    `prompts/04-testgen.md`, `formats/analysis.schema.json`,
    `examples/device-connection/README.md` and several `tools/` scripts; see
    [tools/README.md](tools/README.md#tool-files-watched-by-manifests).
  - `dsc_check` checks staleness only with `--repo`. `tools/addrconn_f09.py`
    and `tools/addrconn_late.py` always check it.
- Tool-level invariants (schema handling, selftest references, version
  checks) are owned by [tools/README.md](tools/README.md#invariants).

## Global Side Effects

Per-tool detail is in [tools/README.md](tools/README.md#side-effects).

- Cost: Flash and Jev calls send the supplied text to DeepSeek and Typesafe.
  They read `DEEPSEEK_API_KEY` and `TYPESAFE_API_KEY` and are metered in a
  SQLite ledger, capped at $2 per ledger by default. Codex runners use the
  signed-in account, found through `CODEX_APP_RUNTIME_CLI_PATH` or `codex` on
  `PATH`.
- Network:
  - `tools/addrconn_f09.py` and `tools/addrconn_late.py` clone grpc-go from
    GitHub unless `--checkout` is given.
  - `tools/run_benchmark.py` clones the benchmark repositories.
  - Go commands may download modules on a cold module cache.
  - When `uv` is on `PATH`, `tools/run_tool_tests.py` runs through
    `uv run --with jsonschema`, which can download `jsonschema`.
- Go: the addrConn, semaphore and gobreaker runners run `go test -race` in
  disposable copies or overlays. `examples/weighted-semaphore/verify_q01.py`
  runs it in place.
- Git: the staleness checks run `git diff`, and the reference runners check
  `git rev-parse` and `git status` of their checkouts. Some pilot runners
  create git checkouts.
- Repository writes:
  - The generators and maintenance tools write `analysis.json`,
    `manifest.json`, variant files and generated README and prompt blocks,
    each only when invoked to.
  - Two "Run these first" gates rewrite tracked files on every run; the
    files are byte-identical when the run is green.
    `tools/selftest/run_selftest.py` rewrites
    `tools/selftest/compound/domain-analysis/gate/analysis.json`, and
    `tools/run_tool_tests.py` regenerates
    `tests/<case>/domain-analysis/mini/analysis.json`.
  - Some pilot and routing runners write tracked files under
    `docs/evidence/`.

## System Verification

Commands run from the repository root. Python `Run:` commands in this
repository's READMEs are written as `python3 ...`. Go commands are written as
`cd <module> && go test ...`.

Python commands assume Python 3.12, as in CI, and `tools/requirements-dev.txt`.
The GEPA selftests and runners also need
`docs/evidence/gepa-bounded/requirements.txt`. On a PEP-668 host such as
macOS, install [uv](https://docs.astral.sh/uv/) and prefix each command with
`uv run --with-requirements tools/requirements-dev.txt`; the first run
downloads the dependencies. Alternatively, install the files into a
virtualenv.

Run these first. They need no Go or API keys, and each exits 0 when green.
The first `uv run` needs network to download the dependencies, and
`tools/run_tool_tests.py` may fetch `jsonschema` through `uv`.

- Run: `python3 tools/selftest/run_selftest.py`
- Run: `python3 tools/run_tool_tests.py`
- Run: `python3 tools/gen_rules.py --selftest`
- Run: `python3 tools/check_pack_consistency.py`
- Run: `python3 -m mypy`
  - Install both requirements files to match CI's type resolution, for
    example
    `uv run --with-requirements tools/requirements-dev.txt --with-requirements docs/evidence/gepa-bounded/requirements.txt python3 -m mypy`.

CI (`.github/workflows/pack-ci.yml`) installs both requirements files with
`pip`. Step-level commands live in the component contracts; this is the map:

- CI job `consistency`:
  - the gates above and the per-tool selftests; see
    [tools/selftest/README.md](tools/selftest/README.md#verification) for
    counts;
  - the golden-mini sidecar, `dsc_check` and reachability step;
  - the Go reference steps for addrConn, late-completion, gobreaker readiness
    and the weighted semaphore. These include `tools/semaphore_f09.py` and
    `docs/evidence/generic-canary/scripts/semaphore_weak_control.py`, and the
    addrConn steps clone grpc-go;
  - the weighted-semaphore mutation binding.
- CI job `gepa-evaluation`:
  - the GEPA and routing-label selftests, offline replays and reference
    controls.
