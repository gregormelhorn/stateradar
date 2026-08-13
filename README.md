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
no build step, no service, nothing leaves your repo.

---

## A bug, in one table row

`examples/device-connection/` ships a 130-line async component with nine
written requirements. R-05 says:

> The component remains in FAILED state permanently.

The pilot walks every state against every event and fills one cell per
combination. Here is the row for `FAILED`:

| state | connect | disconnect |
|---|---|---|
| **FAILED** | reject `device_connection.py:85-86` ("raise ConnectionError('device is in FAILED state')") | transition →DISCONNECTED `device_connection.py:92-99` (no FAILED guard in disconnect) → **Q-03** |

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
difference is classified: *convergent*, *convergent-hole*, *divergence*
(must end as a question), *artefact* (repair the catalogue), or
*pass-B blind spot*.

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
git -C tools/prompt-pack checkout v1.50
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

Run the deterministic layer locally at any point:

```bash
uv run --with-requirements tools/requirements-dev.txt \
  python3 tools/dsc_check.py domain-analysis/<component>
```

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
registered as F-01…F-22 in `formats/rules.toml`. Wired today: F-01 missing
transition, F-02 transfer fault, F-04 sneak path, F-05 corrupt state.
Results report `KILLED / SURVIVED / ERROR / BLOCKED` — never a bare rate.

This is mutation-guided test assessment in the spirit of Meta's ACH work,
with one structural difference: because each mutant *is* an instance of a
named class by construction, "is this mutant relevant?" is a label rather
than a judgment call — and equivalence is decided against the matrix instead
of by an LLM judge.

Honest status: the implementation mutants are hand-authored per class today.
Generating them from the fault classes is the next step, not a shipped one.

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
Typical target: one bounded component, roughly 200–1,500 LOC of lifecycle
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
examples/    device-connection reference run
tests/       benchmark suite, Oracle evidence, golden/red fixtures
docs/        roadmap and design documents
```

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

Pack versions are git tags (`v1.50`), mirrored in
[`CHANGELOG.md`](CHANGELOG.md). Consumers pin a tag; an analysis directory
records the pack version that produced it. The pilot prompt carries the
method's own feedback-loop changelog — divergence *classes* found by blind
passes get folded back into the rules there.

Issues and pull requests are welcome, and pilot reports on your own
components are the most useful contribution of all: the method improves from
real divergences, not from hypotheticals.

## License

Copyright 2026 Gregor Melhorn.

Licensed under the Apache License, Version 2.0. See [`LICENSE`](LICENSE).
This covers the prompt texts and the skill files as well — copying and
adapting them is the intended use. Apache-2.0 adds an express patent grant,
which the MIT License did not carry.

Releases up to and including v1.50 were published under the MIT License.
Those versions remain available under the MIT terms; the relicensing applies
going forward and is not retroactive.