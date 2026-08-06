# StateRadar

**Find the missing transition.**

**Open-source lifecycle contract verification for stateful software.**

StateRadar reconstructs independently (1) what behaviour the
requirements and documented contracts demand, (2) what state model the
implementation actually realizes, and (3) where the two disagree. It
finds missing transitions, incomplete timeout paths, blocked terminal
states, wrongly coupled lifecycles, unhandled State/Event
combinations, and missing tests.

> Model-based testing checks code against a model.
> StateRadar first checks whether the model deserves to be the oracle.

The pack is a pure prompt pack for AI-coding-agent workflows. No
tooling to install; the prompts themselves bootstrap the deterministic
layer (generated checker scripts, cell tests, CI wiring). The agent
may propose and challenge behaviour, but must not silently decide it —
and the tests come from the specification, not from the code.

**Version 1.32.**

## The problem

Defects in asynchronous, stateful components rarely live in a single
function. The real behaviour is distributed across timers, callbacks,
futures and tasks, locks, reference counting, resource ownership,
retry loops, transport states, and caller-vs-internal lifecycles.
Ordinary code review inspects individual control flows. StateRadar
analyzes the complete lifecycle contract instead.

## How it works

### Part A — code-informed analysis

An agent reads the requirements, the code, and the tests of ONE
bounded component and reconstructs the implemented state model:
states, events, guards, a disposition matrix, invariants, adversarial
traces, and open questions.

### Part B — blind run

A second, independent session receives only the requirements and the
event catalogue — never the code, the matrix, or the traces. From
these alone it must state, for every event, when the component should
handle, ignore, or reject it. Because Part B never saw the
implementation, it cannot rationalize implementation accidents as
desired behaviour.

### Blind diff

The two models are compared cell by cell. Every difference is
classified: convergent, convergent-hole, divergence (must end as a
question), artefact (repair the catalogue input), or
pass-B-blind-spot. The blindness is the mechanism, not a ritual — an
agent that knows the matrix cannot un-know it.

## What StateRadar finds

* missing State/Event transitions and `UNSPECIFIED` matrix cells;
* timeout events without guaranteed progress;
* caller operations blocked after a terminal event;
* internal requests holding resources after a caller timeout;
* unbounded waits;
* invalid recovery or reconnect paths;
* wrongly coupled lifecycle regions (caller vs. internal);
* lost or overwritten failure causes;
* missing idempotency in cleanup and release;
* requirements without a complete execution path;
* implementation paths without a documented contract;
* tests that assert internal states but not caller-visible behaviour.

## Proven pilot cases

Both findings were frozen before the known upstream issues were
revealed, then confirmed by the real bug reports.

### valkey-glide — missing transition `CallerTimedOut → PermitReleased`

A concrete defect (issue #5803): requests retained shared in-flight
capacity after the user-facing timeout had fired. One unresponsive
cluster node exhausted the permit limit for all healthy nodes.
StateRadar identified the missing timeout-release transition, the
wrong coupling between caller and internal request lifecycles, and
the need for an immediate, idempotent release — from six neutral
requirements alone.

### python-websockets — missing transition `CloseDeadlineExpired → ClosureObservable`

After `close_timeout` expired, the implementation closed the transport
but then waited again for the `connection_lost()` event-loop callback.
With Wi-Fi off, no TCP reset arrives, `connection_lost()` never
fires, and the server stayed silent for minutes instead of raising
`ConnectionClosedError` (issue #1527). StateRadar found the missing
progress after deadline expiry, the faulty dependence on the
event-loop callback, and the gap between protocol, transport, and
caller lifecycles.

Earlier pilots on eight real-world components (reconnecting-websocket,
gobreaker, recws, recloser, cenkalti/backoff, tungstenite-rs,
tenacity) reached 93% tracker-bug coverage and surfaced eight new
bugs, two of them critical and reported upstream.

## Scope

Use for lifecycles, connections, protocols, async workflows, retries,
timeouts, cancellation, recovery, sessions, mutually exclusive modes.
Typical scope: one bounded component, roughly 200–1,500 LOC of
relevant lifecycle code, with requirements in README, docstrings, API
contracts, or tests. Do not use for pure calculations, stateless
transforms, formatting, validation, or CRUD without temporal
behaviour.

StateRadar is not a general AI code-review bot, a static linter, a
security scanner, a UML diagram tool, a classical model checker, a
formal proof, or a replacement for tests and human review. It is a
verification workflow for lifecycle contracts.

## Repository layout

```text
prompts/        canonical source of truth (harness-neutral Markdown)
  00-methods-reference.md   methodology; give to agents as context
  01-scout.md               find & rank stateful components
  02-pilot.md               as-is model, matrix, traces -> open questions
  03-resolution.md          your answers -> decision records -> to-be model
  04-testgen.md             one test per matrix cell + checkers in CI
  05-standing-instruction.md  block for the consumer repo's CLAUDE.md/AGENTS.md
  06-reconcile.md           close the loop: promote, refresh citations, pin the SHA
  07-test-audit.md          audit a suite against the matrix: weak tests first
skills/         thin harness packagings (Claude Code skill)
commands/       optional Claude Code slash commands
examples/       reference runs (see examples/README.md before publishing any)
tools/          consistency checker, dsc_check (the pack-shipped sidecar
                checker), gen_analysis_sidecar (emits the sidecar from
                the matrices), part_b_pack (assembles and coverage-checks
                the Part-B blind inputs), refresh_citations (the
                06-reconcile citation refresh), gen_matrix_scaffold
                (empty matrix grids), dsc_compose (cross-model report),
                check_matrix (the generic per-component checker),
                dsc_stamp (validate + pin the manifest),
                dsc_blind (blind-pass assembly + diff),
                dsc_cross_check (reviewer cross-check), templates/
                (the CI gate file + the per-component checker wrapper)
.benchmarks/    golden cases + runner — the falsifiable layer for the tools
formats/        analysis.schema.json + manifest.schema.json — the sidecar
                and manifest contracts
```

The pack is **stateless**: all analysis artifacts (`domain-analysis/<component>/`) and generated tests live in the consuming repository, never here.

## Running the checkers locally

System Python on macOS is PEP-668 externally managed. Run the checkers through uv, which supplies `jsonschema` (schema validation in `dsc_check`) without touching the system environment:

```bash
uv run --with jsonschema python3 tools/dsc_check.py <analysis-dir>
```

Without `jsonschema`, `dsc_check` cannot validate the sidecar contract and fails with that reason. Pass `--allow-no-schema` to accept structural checks only — a deliberate reduction in coverage, never a silent one. CI installs the package with pip instead.

The pack's own deterministic layer has a selftest that runs the checker red as well as green (silent omission, drifted citations, a diagram out of sync with the matrix, a snake_case manifest key — each must fail):

```bash
uv run --with jsonschema python3 tools/selftest/run_selftest.py
```

## Using the pack in a repository

**Option A: git submodule (recommended for your own repos).**

```bash
git submodule add <this-repo-url> tools/prompt-pack
git -C tools/prompt-pack checkout v1.32
```

Updating later: `git -C tools/prompt-pack fetch --tags && git -C tools/prompt-pack checkout <newer-tag>`. One place, no drift. The submodule brings its own `tools/ste-pack/` submodule; init recursively (`git submodule update --init --recursive`).

**Option B: vendored copy (for repos that avoid submodules).** copy `prompts/` to `tools/prompt-pack/prompts/` and record the tag in `tools/prompt-pack/VERSION`. You are responsible for updating it; the version you copied is the version your analyses claim. If you want the prose lint, vendor the ste-pack the same way and copy its `consumer.vale.ini` to your repo root as `.vale.ini`.

**Standing instruction without drift:** do not paste the whole of `05-standing-instruction.md` into `CLAUDE.md`. Use an import so the rules update with the pack:

```markdown
@tools/prompt-pack/prompts/05-standing-instruction.md
```

## Claude Code integration

* **Skill (auto-triggering):** copy or symlink `skills/claude-code/domain-statechart/` into `.claude/skills/` (per repo) or `~/.claude/skills/` (personal). The skill routes stateful work into the right stage of the workflow; language work routes to the ste-pack's `ste-writing` skill.
* **Slash commands (explicit):** copy `commands/*.md` into `.claude/commands/`. They assume you vendored the pack at `tools/prompt-pack/`. Adjust the path at the top of each command if yours differs.

Other harnesses: paste the prompts directly, or wire them into your harness's skill mechanism. The canonical files in `prompts/` are plain Markdown on purpose.

## Workflow

```text
DISCOVER   01 Scout ──► pick a component (use its generated CONFIG block)
MODEL      02 Pilot ──► answer the questions (edit the file, or let 03 interview you)   ◄── you
           03 Resolution ──► DRs + to-be model + updated matrix
           Part B ──► blind adversarial pass in a fresh session (02-pilot, PART B)
ENFORCE    04 Testgen ──► cell tests + check_matrix.py + check_guards.py + deviation report
           05 Standing instruction ──► future agent sessions stay disciplined
MAINTAIN   06 Reconcile ──► the approved model becomes the new as-is; manifest pins HEAD
           07 Test audit ──► off-cycle: judge the suite against the decided matrix
```

Once 04 has run, the discipline is CI-enforced in the consuming repo. Breaking a disposition, a DR link, a guard proof, or coverage breaks the build.

Calibration tip: run the pilot twice on the same component in fresh sessions and diff the two matrices. The divergence tells you how much to trust any single unverified run.

## Why Part B exists (the blind pass)

Pass A (the pilot) builds the matrix from the code. That creates a
trust problem. Where the matrix agrees with the code, you cannot tell
whether it records a requirement or rationalizes an implementation
accident. The analysis agent read the code, so its model matches by
construction. This failure mode has the name mirroring, and the matrix
alone cannot reveal it.

Part B attacks it by independent re-derivation. A FRESH agent session
receives exactly three inputs and nothing else. No access to the code,
the matrix, or the traces:

1. the event catalogue (events, undesired variants, interaction pairs,
   gate annotations),
2. the prose requirements,
3. the normative contract text of every event type.

From these alone it must state, for every event: when should the
component handle, ignore, or reject it, and what should happen. An
agent that sees both sides then diffs the blind table against the
matrix, row by row:

- **convergent** — both independently agree. The behaviour is
  derivable from the requirements, not a code accident. The strongest
  cheap trust signal.
- **convergent-hole** — the blind pass flags the same gap pass A
  found. The finding gains weight.
- **divergence** — different expectation. A real finding: a blind spot
  in pass A, an ambiguous catalogue, or a genuine open question. Every
  divergence must end as a question or a reasoned fold, never closed
  silently.
- **artefact** — the catalogue phrasing caused it. Repair the
  catalogue input, not the model.
- **pass-B-blind-spot** — pass A saw something the blind pass missed.
  Noted, no action.

The blindness is the mechanism, not a ritual. An agent that knows the
matrix cannot un-know it. Fresh session, exactly three inputs, nothing
else.

Worked example (dobby trigger-service, 2026-08-05). The pilot found
the code contradicting its own docstring ("highlight ALWAYS" vs an
early return for uncalibrated sources). The owner decided for the code
(DR-035). The blind pass knew none of this and still derived from
"highlight on VALIDATED receipt" that uncalibrated sources get no
highlight. Three independent sources agreed: code, owner decision,
requirements derivation. All 23 events and all 12 pair orderings
converged, zero divergences.

Cost: one subagent run. Benefit: the matrix stops being a claim by the
analysis agent alone.

## Adopting the pack in an existing project

Brownfield adoption runs in maturity levels per component
(00-methods-reference has the full definitions). Each level needs
everything below it:

```text
L1 descriptive   extraction + as-is statechart + disposition matrix
L2 decided       + open questions, DRs for decided cells, hole→Q links
L3 enforced      + one cell test per matrix cell + matrix-coverage.json
L4 verified      + analysis.json sidecar, dsc_check OK, CI gate wired
L5 steady state  + reconciled manifest at HEAD, standing instruction active
```

Rules of thumb from consumer experience:

- **The directory is the authority.** Any component with
  `domain-analysis/<component>/` is governed at its level. Never
  hardcode the component list in the standing instruction — it goes
  stale at the next pilot.
- **No reconcile-lite.** A manifest bump without the sidecar and a
  green `dsc_check` is bookkeeping, not a reconcile (06-reconcile
  step 0). Unverified "steady states" corrupt the record.
- **Keep the living index current.** `domain-analysis/summary.md`
  (component table, totals, known gaps) updates on every stage
  completion.
- **Generate sidecars; never hand-write them.**
  `tools/gen_analysis_sidecar.py` parses the matrices (single- and
  multi-table, compound states) and emits `analysis.json`. Per-project
  extras (question aliases, backfill citations, a skip list) live in
  `domain-analysis/sidecar-overlay.yaml`. Fix the matrix, regenerate
  the sidecar.
- **Manifests use the pack keys.** `formats/manifest.schema.json`:
  `component`, `watchPaths` (camelCase, narrow per component),
  `analyzedSha`. A snake_case `watch_paths` silently empties the
  staleness filter; `dsc_check` fails loudly on it.

## Versioning

Pack versions are git tags (`v1.32`) mirrored in `CHANGELOG.md`. The pilot prompt also carries the method's feedback-loop changelog at its top. It folds divergence *classes* found by Part-B blind passes back into rules there. Consumers pin a tag; an analysis directory should note the pack version used to produce it. The submodule pins the ste-pack dependency by tag; the declaration lives in "Language policy" above.

## Claims

StateRadar currently claims credibly:

* Detects missing lifecycle transitions in real-world asynchronous components.
* Separates requirement-level defects from implementation mechanisms.
* Identifies incorrect coupling between caller-visible and internal lifecycles.
* Detects unspecified, untested, or unimplemented State/Event combinations.
* Produces traceable findings before known upstream bug information is revealed.
* Turns approved lifecycle decisions into executable tests and CI checks.

It does not claim to find all software defects, to guarantee
correctness, to replace code review, to provide formal proofs, to have
no false positives, or to work without usable requirements.

## License

MIT, including the prompt texts and skill files. Copying and adapting them is the intended use.
