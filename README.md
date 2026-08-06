# Domain Statechart Pack

**Version 1.26.** Statecharts as domain specification and test oracle for AI-coding-agent workflows, as a pure prompt pack. No tooling to install; the prompts themselves bootstrap the deterministic layer (generated checker scripts, cell tests, CI wiring).

> The agent may propose and challenge behaviour, but must not silently decide it — and the tests come from the specification, not from the code.

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
                dsc_stamp (validate + pin the manifest), templates/
                (the CI gate file + the per-component checker wrapper)
.benchmarks/    golden cases + runner — the falsifiable layer for the tools
tools/ste-pack/ the language layer, consumed as a pinned submodule (v1.5.0)
formats/        analysis.schema.json + manifest.schema.json — the sidecar
                and manifest contracts
.vale.ini       the pack's own prose gate; StylesPath into tools/ste-pack/
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

## Language policy (ste-pack dependency)

The language layer is a separate pack: **ste-pack v1.5.0**, consumed as a git submodule at `tools/ste-pack/`. It holds STYLE.md (strictness per text class) and the Vale styles (STE English, DTK German, STEDict dictionary check). It also holds the language agent passes and the language checkers. This pack's `.vale.ini` points its `StylesPath` into the submodule; `tools/check_pack_consistency.py` verifies that the checked-out submodule tag matches the version declared here. The word data follows ASD-STE100 **Issue 9** (2025-01-15).

This pack's approved technical nouns and verbs (Issue 9 term; Issue 7 called them technical names) — its project dictionary in the sense of ste-pack STYLE.md — live in `technical-names.txt`, one name per line. Add a name there before you use it in strict-mode text, then rebuild the dictionary.

After a fresh clone, recreate the dictionary symlinks if you use `STEDict` (the data is private and gitignored; see ste-pack STYLE.md, "Data placement"), then rebuild so the technical names flow in:

```bash
mkdir -p tools/ste-pack/styles/config/dictionaries
ln -sf ~/ste-private/ste.dic ~/ste-private/ste.aff tools/ste-pack/styles/config/dictionaries/
python3 tools/ste-pack/tools/build_ste_dictionary.py \
  --wordlist ~/ste-private/ste-core-words-issue9.txt \
  --names technical-names.txt
```

## Using the pack in a repository

**Option A: git submodule (recommended for your own repos).**

```bash
git submodule add <this-repo-url> tools/prompt-pack
git -C tools/prompt-pack checkout v1.16
```

Updating later: `git -C tools/prompt-pack fetch --tags && git -C tools/prompt-pack checkout v1.17`. One place, no drift. The submodule brings its own `tools/ste-pack/` submodule; init recursively (`git submodule update --init --recursive`).

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

Pack versions are git tags (`v1.16`) mirrored in `CHANGELOG.md`. The pilot prompt also carries the method's feedback-loop changelog at its top. It folds divergence *classes* found by Part-B blind passes back into rules there. Consumers pin a tag; an analysis directory should note the pack version used to produce it. The submodule pins the ste-pack dependency by tag; the declaration lives in "Language policy" above.

## Scope

Use for lifecycles, connections, protocols, async workflows, retries, timeouts, cancellation, recovery, sessions, mutually exclusive modes. Do not use for pure calculations, stateless transforms, formatting, validation, or CRUD without temporal behaviour.

## License

MIT, including the prompt texts and skill files. Copying and adapting them is the intended use.
