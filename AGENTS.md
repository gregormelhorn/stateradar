# How StateRadar works: instructions for an LLM

You are an agent in a repository that uses StateRadar. This document tells you what the system is. It shows how information flows through the system. It lists the rules that bind you. The language layer (STE/DTK) is a separate concern.

## 1. What this is

The pack treats a Harel-style statechart as the specification and the test oracle for one stateful component. The division of work does not change. You extract, classify, draft, and propose. Deterministic code verifies your outputs. The human owner decides domain semantics.

Never fill a specification gap with your own judgment, however plausible. Your value is completeness and honesty, not decisiveness.

## 2. The objects

* **Machine boundary**: the scope statement declares one bounded component. The machine boundary is this component, not the whole system.
* **State**: a state is a mode of the component. Implicit states count. Enumerate the reachable combinations of boolean flags and nullable references. These combinations are the real state space.
* **Event**: an event has one of three sources: external (boundary calls), internal (timers, delivered results), or an undesired variant (`UV-nn`). Derive the undesired variants per source from a fixed checklist (generated from `formats/rules.toml`):

<!-- generated:rules key=uv-categories -->
* loss or failure of the source (F-12, sidecar key: `loss`)
* delay beyond timeout (F-13, sidecar key: `delay`)
* duplication (F-14, sidecar key: `duplication`)
* out-of-order or stale arrival, especially after cancellation or shutdown (F-15, sidecar key: `out-of-order`)
* contradictory simultaneous inputs (F-16, sidecar key: `contradiction`)
* spontaneous commission — an event with no legitimate trigger (spurious wakeup, callback without a matching request, unsolicited push) (F-17, sidecar key: `commission`)
* subtle value fault — a plausible but wrong payload (foreign session or entity id, stale epoch or generation counter) (F-18, sidecar key: `value`)
<!-- /generated:rules -->

  The coverage table must show every category. Write a reason for each `n/a`.
* **Interaction pairs** (`P-nna/b`): an interaction pair is a cross-source event pair on one shared entity, in both orderings. Per-source checklists structurally miss races between sources. Interaction pairs close this gap.
* **Disposition**: each matrix cell has exactly one disposition: `transition → <target>`, `handle`, `ignore (documented)`, `ignore (accidental)`, `defer (queued)`, `reject`, or `UNSPECIFIED`. The values `ignore (accidental)` and `UNSPECIFIED` are holes.
* **Guards**: formalizable guard groups get z3 proofs: pairwise disjointness, coverage, and boundary probes. Each group ends as `proven`, `violation`, or `not-formalizable: <reason>`. Never skip a guard group silently.
* **Invariants**: `NAT` marks an assumption about the environment. Cite the assumption into the callee or upstream. `SYS` marks an obligation of the system. Check each SYS invariant state by state.
* **Doctrine lines** (`DOC-n`): extract every normative sentence from the requirements. Map each doctrine line to an invariant, a disposition constraint, or an explicit rejection. An unmapped doctrine line is an error.
* **Provenance**: every behavioural claim carries one label: `explicit-requirement`, `observed-in-code`, `observed-in-tests`, `inferred`, or `proposed`. Code and test citations carry a fragment: `file:line ("fragment")`. The checkers verify the fragment near that line.
* **Questions** (`Q-nn`): every hole, contradiction, and violated assumption becomes a question. Only the human can answer it. Drop nothing in consolidation. Every hole cell carries `→ Q-nn`.
* **Decision records** (`DR-nnn.yaml`): a decision record holds the human's answers with attributed rationale. The decision records are the permanent memory. A to-be deviation without a DR is an error.
* **Sidecar and manifest**: `analysis.json` holds your machine-readable claims. `manifest.json` holds `analyzedSha` and the watch paths. The pack checker consumes both files. Git diffs against the SHA turn staleness into a CI signal.

## 3. The loop

```text
01 Scout      rank stateful components; evidence-based, read-only
02 Pilot      Part A: extract → as-is model → catalogue → matrix → guards
              → invariants → adversarial traces → open questions
              Part B: a BLIND session predicts dispositions from the
              catalogue + requirements only; a diff classifies every row
   (human)    answers the questions — interview mode: one per round,
              recommended option first (Enter default), attributed
              rationale, write-through per answer, defer stays OPEN
03 Resolution DRs, to-be model, matrix update, re-run all checkers
04 Testgen    one test per matrix cell + scenario tests from decided
              traces; red tests against current code = deviation report
              = the implementation worklist, never a test defect
   (impl.)    fix code DR by DR; docs-only DRs first (no red test
              reminds you); tests are read-only
06 Reconcile  after green: promote to-be → as-is, refresh citations at
              HEAD, write sidecar + manifest, archive superseded files
07 Test audit off-cycle: weak tests first (structure over function),
              then redundancy, deviations, gaps; propose, never delete
```

Run 06 first when the manifest reports staleness. Run 01 or 02 for a new component. For a behaviour change request, follow the standing instruction: model and DR first, code second.

## 4. Rules that do not bend

<!-- rule:R-NO-SILENT-DECISIONS -->
1. **Never decide domain semantics.** If behaviour is unclear, contradictory, or unspecified, write a question. Treat a "benign" gap as a proposal inside the question. It is never a reason to omit the question.
<!-- rule:R-REQUIREMENT-SCOPE-a -->
2. **Requirement-scope rule.** A citation covers only the scenario that its text describes. A control-trace verdict that cites a requirement must carry the line: *cited text contemplates this ordering: yes/no*. A "no" voids the verdict. Then raise a question.
<!-- rule:R-SEAM-CONTRACT -->
3. **Read callee contracts. Do not infer them.** Missing error handling at a call site is not evidence that failures propagate. Read the contract of the seam. Cite into the callee.
<!-- rule:R-EXECUTED-CHECKS -->
4. **Run checks as executed code.** You emit data. The pack verifies it with `tools/dsc_check.py` on the sidecar. When you write per-run checkers, run them and paste the output. A red checker means: fix the artefact, or fix the checker openly and re-run. Never "fix" the data to silence a check.
<!-- rule:R-PROPOSALS -->
5. **Proposals are not decisions.** Recommendations have flipped between runs on the same code. Present them, label them `proposed`, and hold them loosely. Pre-selection in the interview is presentation, not authority.
<!-- rule:R-ANTI-MIRRORING -->
6. **Tests bind to behaviour, not structure.** Assert only through the declared seam: projected state, emitted effects, and SYS invariants. Never weaken, skip, or delete a test to make it pass. A failing cell test is a finding.
<!-- rule:R-PART-B -->
7. **Part B stays blind.** The blind session gets the catalogue, the requirements, and the event contracts. It never gets the code, the matrix, or prior analyses. Do no git archaeology on deleted analyses.
<!-- rule:R-DEFERRED-OPEN -->
8. **Deferred stays OPEN.** A deferred question blocks only its own cells.
<!-- rule:R-READ-PROMPTS -->
9. **Read prompts in full.** When a task says "run prompt X" or references a prompt file (e.g. `prompts/02-pilot.md`), read the complete file before producing output. Do not guess its content from the filename, derive it from memory, or skip steps that the prompt requires. A subagent that produces the wrong number of events because it did not read the undesired-variant checklist has not executed the prompt.

## 5. What the checkers catch

The checkers catch the following defects. Do not fight them. (Generated from `formats/rules.toml` — the registry maps each line to its rule, checker, and selftest.)

<!-- generated:rules key=checker-catalogue -->
* grid totality
* disposition vocabulary
* hole → Q back-references
* DR links on ignore, reject, and defer
* behavioural-DR reverse coverage: every decided change connects to a cell
* pair → trace coverage
* guard outcomes present
* coverage-table totality
* Mermaid ↔ matrix sync
* fragment citations within ±3 lines
* manifest staleness
* blind-table row coverage
* schema validity of the sidecar
* existence of every cited DR file
* reachable states and terminal-state marking
* state names follow PA-17 (PascalCase segments or ALL-CAPS API enums)
* doctrine-line mapping totality (DOC-n → cell / invariant / rejected)
* event classification present per catalogue event (PA-4)
* abstraction statement in the matrix (PA-10)
* scope lines on citing control traces
* gate-type annotation presence on events
* upstream-guard annotation presence on events
<!-- /generated:rules -->

## 6. Failure modes seen in real runs

Avoid these failure modes from real runs.

* Call-site inference declared a publisher failure path. The callee's contract excludes this path.
* An agent applied a recorded decision for steady state to a race. The decision never contemplated this race.
* A checklist category silently produced no variant.
* A catalogue stated gates but not remembrance semantics. Remembrance semantics say what ended entities leave behind. Blind readers misread five rows for that one omission.
* Consolidation lost findings between runs.
* An agent almost softened an expected-red test instead of reporting it.

When your Part-B diff exposes a recurring divergence class, fold it back into the pilot prompt's changelog as a rule. Single findings stay findings. The goal is not zero divergence. A blind pass that cannot disagree is dead weight.

- **Completion-report drift.** Session reports have described work
  absent from the repository: tasks marked done that were never
  committed, tags reported "pushed" that never left the workspace.
  Countermeasures that worked: acceptance criteria as executable
  commands, remote verification, paste obligations.
- **Hollow checks.** A verification mechanism was built so it could
  not fail (file-existence instead of anchor verification; anchors
  resolving into generated blocks). The countermeasure is R-RED-PROBE:
  a mechanism's failure path is demonstrated at build time.
- **Vacuous green.** A relocated test runner reported "0/0 cases
  pass" with exit 0. Discovery that finds nothing now hard-fails.
- **First-contact failures.** Across one extended session, every tool
  change shipped without a simultaneous gate arrived defective but
  green; every change built together with its red case held on first
  contact. The gate is not overhead — it is the difference.

## 7. Working on this pack

The rules above govern the analysis. These govern changes to the pack
itself — every one of them exists because its violation was observed
in real pack-development sessions.

<!-- rule:R-VERIFIED-COMPLETION -->
1. **Completion = diff + executed acceptance.** Describe only work
   that is in the committed diff, and only acceptance commands you
   ran. Paste their output under `Evidence:` in the commit body.
<!-- rule:R-RED-PROBE -->
2. **No mechanism without an observed failure.** Build the red probe
   first, watch it fail for the intended reason, then build the
   mechanism, then watch the probe pass. Paste both runs. A check
   that has never been red proves nothing (see §5's CI note).
<!-- rule:R-REMOTE-TRUTH -->
3. **"Pushed" means the remote says so.** Verify tags and pushes with
   `git ls-remote` and paste it. Your working copy is not the release.
<!-- rule:R-GREEN-MAIN -->
4. **Green before push.** Run the full gate set (§5) before every
   commit to main. Red gate → no push. Red CI after a push → fixing
   it comes before everything else.
<!-- rule:R-REMEASURE -->
5. **Reality wins.** When a check disagrees with a recorded number,
   the number is re-measured, never massaged — and every surface that
   states it (tool output, selftest asserts, CHANGELOG, README,
   CONVERGENCE) moves in the same commit.
<!-- rule:R-BLOCKED-HONESTY -->
6. **BLOCKED is a valid result.** A premise that fails stops the task.
   Record `BLOCKED(<task>): <reason>` and move on. Substituting
   something plausible and reporting success is the failure mode this
   whole section exists to prevent.
