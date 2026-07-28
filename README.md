# Domain Statechart Pack

**Version 1.15.** Statecharts as domain specification and test oracle for AI-coding-agent workflows — as a pure prompt pack. No tooling to install; the deterministic layer is bootstrapped by the prompts themselves (generated checker scripts, cell tests, CI wiring).

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
skills/         thin harness packagings (Claude Code skill)
commands/       optional Claude Code slash commands
examples/       reference runs (see examples/README.md before publishing any)
tools/          consistency checker, ste_lint, and dsc_check (the pack-shipped
                sidecar checker: the agent emits analysis.json, the pack verifies)
formats/        analysis.schema.json — the sidecar contract
STYLE.md        language policy: ASD-STE100-based, strictness per text class
.vale.ini +     the policy as an executable Vale configuration
styles/STE/     path-scoped: errors gate prompts/, warnings inform elsewhere
```

The pack is **stateless**: all analysis artifacts (`domain-analysis/<component>/`) and generated tests live in the consuming repository, never here.

## Using the pack in a repository

**Option A — git submodule (recommended for your own repos):**

```bash
git submodule add <this-repo-url> tools/prompt-pack
git -C tools/prompt-pack checkout v1.2
```

Updating later: `git -C tools/prompt-pack fetch --tags && git -C tools/prompt-pack checkout v1.3` — one place, no drift.

**Option B — vendored copy (for repos that avoid submodules):** copy `prompts/` to `tools/prompt-pack/prompts/` and record the tag in `tools/prompt-pack/VERSION`. You are responsible for updating it; the version you copied is the version your analyses claim.

**Prose lint in the consumer repo:** copy `consumer.vale.ini` to the consumer repo root as `.vale.ini` (adjust `StylesPath` to your vendored path). Vale then gates the blind-consumed catalogue at `error` and informs on the rest — the language policy travels with the pack.

**Full-STE dictionary check (optional):** the word check (`STEDict`) is off by default because the ASD-STE100 word list is copyrighted — obtain it yourself, build with `tools/build_ste_dictionary.py`, and enable per path. Generated dictionaries are gitignored by design. Placement, symlink option, and the rebuild rule: see STYLE.md, "The dictionary check". The sense layer (approved meaning, part of speech) runs as a grounded agent pass: `prompts/lang-ste-sense.md`, coverage-checked by `tools/check_sense_report.py`. The writing-rules layer (all 53 Part-1 rules) runs the same way: `prompts/lang-ste-rules.md` + `tools/check_rules_report.py`; machinable rules migrate into Vale over time. The owner's per-rule applicability decisions live in `ste-rules-map.json`; the rules run inherits them, checker-verified. `prompts/lang-ste-rewrite.md` rewrites text into STE with all three layers; `tools/check_rewrite_integrity.py` proves meaning-critical tokens survived. German: the opt-in `DTK` Vale style covers the machinable subset; rules and termbase data come from a licensed tekom Leitlinie copy (see STYLE.md, "German adaptation").

**Standing instruction without drift:** do not paste the whole of `05-standing-instruction.md` into `CLAUDE.md`. Use an import so the rules update with the pack:

```markdown
@tools/prompt-pack/prompts/05-standing-instruction.md
```

## Claude Code integration

* **Skill (auto-triggering):** copy or symlink `skills/claude-code/domain-statechart/` into `.claude/skills/` (per repo) or `~/.claude/skills/` (personal). The skill routes stateful work into the right stage of the workflow.
* **Slash commands (explicit):** copy `commands/*.md` into `.claude/commands/`. They assume the pack is vendored at `tools/prompt-pack/` — adjust the path at the top of each command if yours differs.

Other harnesses: paste the prompts directly, or wire them into your harness's skill mechanism — the canonical files in `prompts/` are plain Markdown on purpose.

## Workflow

```text
01 Scout ──► pick a component (use its generated CONFIG block)
02 Pilot ──► answer the questions (edit the file, or let 03 interview you)   ◄── you
03 Resolution ──► DRs + to-be model + updated matrix
04 Testgen ──► cell tests + check_matrix.py + check_guards.py + deviation report
05 Standing instruction ──► future agent sessions stay disciplined
06 Reconcile ──► the approved model becomes the new as-is; manifest pins HEAD
```

Once 04 has run, the discipline is CI-enforced in the consuming repo: breaking a disposition, a DR link, a guard proof, or coverage breaks the build.

Calibration tip: run the pilot twice on the same component in fresh sessions and diff the two matrices — the divergence tells you how much to trust any single unverified run.

## Versioning

Pack versions are git tags (`v1.2`) mirrored in `CHANGELOG.md`. The pilot prompt additionally carries the method's feedback-loop changelog at its top: divergence *classes* found by Part-B blind passes are folded back into rules there. Consumers pin a tag; an analysis directory should note the pack version it was produced with.

## Scope

Use for lifecycles, connections, protocols, async workflows, retries, timeouts, cancellation, recovery, sessions, mutually exclusive modes. Do not use for pure calculations, stateless transforms, formatting, validation, or CRUD without temporal behaviour.

## License

MIT — including the prompt texts and skill files. Copying and adapting them is the intended use.
