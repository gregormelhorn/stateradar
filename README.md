# Domain Statechart Pack

**Version 1.18.1.** Statecharts as domain specification and test oracle for AI-coding-agent workflows, as a pure prompt pack. No tooling to install; the prompts themselves bootstrap the deterministic layer (generated checker scripts, cell tests, CI wiring).

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
tools/          consistency checker and dsc_check (the pack-shipped sidecar
                checker: the agent emits analysis.json, the pack verifies)
tools/ste-pack/ the language layer, consumed as a pinned submodule (v1.0)
formats/        analysis.schema.json — the sidecar contract
.vale.ini       the pack's own prose gate; StylesPath into tools/ste-pack/
```

The pack is **stateless**: all analysis artifacts (`domain-analysis/<component>/`) and generated tests live in the consuming repository, never here.

## Running the checkers locally

System Python on macOS is PEP-668 externally managed. Run the checkers through uv, which supplies `jsonschema` (schema validation in `dsc_check`) without touching the system environment:

```bash
uv run --with jsonschema python3 tools/dsc_check.py <analysis-dir>
```

Without `jsonschema`, `dsc_check` degrades to structural checks only (it prints a note). CI installs the package with pip instead.

## Language policy (ste-pack dependency)

The language layer is a separate pack: **ste-pack v1.1.1**, consumed as a git submodule at `tools/ste-pack/`. It holds STYLE.md (strictness per text class) and the Vale styles (STE English, DTK German, STEDict dictionary check). It also holds the language agent passes and the language checkers. This pack's `.vale.ini` points its `StylesPath` into the submodule; `tools/check_pack_consistency.py` verifies that the checked-out submodule tag matches the version declared here.

After a fresh clone, recreate the dictionary symlinks if you use `STEDict` (the data is private and gitignored; see ste-pack STYLE.md, "Data placement"):

```bash
mkdir -p tools/ste-pack/styles/config/dictionaries
ln -sf ~/ste-private/ste.dic ~/ste-private/ste.aff tools/ste-pack/styles/config/dictionaries/
```

<!-- vale off -->
This pack's approved technical names (its project dictionary in the sense of ste-pack STYLE.md): statechart · state · event · transition · guard · disposition (the seven matrix values) · matrix · cell · hole · invariant · NAT (environment assumption) · SYS (system obligation) · doctrine line · episode · fold · seam · provenance · decision record / DR · blind pass · convergent · convergent-hole · divergence · artefact · pass-B-blind-spot · conformance · vector · trace · interaction pair · boundary · clamp · TTL · replay · digest · idempotent · disjoint · coverage · satisfiable · not-formalizable · write-through · remembrance semantics.
<!-- vale on -->

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
01 Scout ──► pick a component (use its generated CONFIG block)
02 Pilot ──► answer the questions (edit the file, or let 03 interview you)   ◄── you
03 Resolution ──► DRs + to-be model + updated matrix
04 Testgen ──► cell tests + check_matrix.py + check_guards.py + deviation report
05 Standing instruction ──► future agent sessions stay disciplined
06 Reconcile ──► the approved model becomes the new as-is; manifest pins HEAD
```

Once 04 has run, the discipline is CI-enforced in the consuming repo. Breaking a disposition, a DR link, a guard proof, or coverage breaks the build.

Calibration tip: run the pilot twice on the same component in fresh sessions and diff the two matrices. The divergence tells you how much to trust any single unverified run.

## Versioning

Pack versions are git tags (`v1.16`) mirrored in `CHANGELOG.md`. The pilot prompt also carries the method's feedback-loop changelog at its top. It folds divergence *classes* found by Part-B blind passes back into rules there. Consumers pin a tag; an analysis directory should note the pack version used to produce it. The submodule pins the ste-pack dependency by tag; the declaration lives in "Language policy" above.

## Scope

Use for lifecycles, connections, protocols, async workflows, retries, timeouts, cancellation, recovery, sessions, mutually exclusive modes. Do not use for pure calculations, stateless transforms, formatting, validation, or CRUD without temporal behaviour.

## License

MIT, including the prompt texts and skill files. Copying and adapting them is the intended use.
