# How the Domain-Statechart Part Works — Instructions for an LLM

You are an agent in a repository that uses the Domain Statechart Pack. This document tells you what the system is, how information flows through it, and which rules bind you. The language layer (STE/DTK) is a separate concern; see `STYLE.md`.

## 1. What this is

The pack treats a Harel-style statechart as the specification and the test oracle for one stateful component. The division of labor is fixed: **you** extract, classify, draft, and propose; **deterministic code** verifies your outputs; **the human owner** decides domain semantics. You never fill a specification gap with your own judgment, however plausible. Your value is completeness and honesty, not decisiveness.

## 2. The objects

* **Machine boundary**: one bounded component, declared in the scope statement. Not the whole system.
* **State**: a mode of the component. Implicit states count: enumerate reachable combinations of boolean flags and nullable references. They are the real state space.
* **Event**: external (boundary calls), internal (timers, delivered results), and **undesired variants** (`UV-nn`) derived per source from a fixed checklist: loss/failure, delay beyond timeout, duplication, out-of-order or stale arrival, contradictory input. A coverage table proves no category was silently skipped; `n/a` needs a reason.
* **Interaction pairs** (`P-nna/b`): cross-source event pairs on one shared entity, both orderings. They exist because per-source checklists structurally miss races between sources.
* **Disposition**: exactly one of `transition → <target>` · `handle` · `ignore (documented)` · `ignore (accidental)` · `defer (queued)` · `reject` · `UNSPECIFIED` per matrix cell. `ignore (accidental)` and `UNSPECIFIED` are **holes**.
* **Guards**: formalizable guard groups get z3 proofs — pairwise disjointness, coverage, boundary probes — and end as `proven`, `violation`, or `not-formalizable: <reason>`. Never silently skipped.
* **Invariants**: `NAT` (assumptions about the environment, cited into the callee or upstream) and `SYS` (obligations of the system, checked state by state).
* **Doctrine lines** (`DOC-n`): every normative sentence from the requirements, each mapped to an invariant, a disposition constraint, or an explicit rejection. An unmapped doctrine line is an error.
* **Provenance**: every behavioural claim carries one of `explicit-requirement` · `observed-in-code` · `observed-in-tests` · `inferred` · `proposed`. Code and test citations carry a fragment: `file:line ("fragment")` — checkers verify the fragment near that line.
* **Questions** (`Q-nn`): every hole, contradiction, and violated assumption becomes a question only the human can answer. Nothing is dropped in consolidation; every hole cell carries `→ Q-nn`.
* **Decision records** (`DR-nnn.yaml`): the human's answers, with attributed rationale. The permanent memory. To-be deviations without a DR are errors.
* **Sidecar + manifest**: `analysis.json` (your machine-readable claims) and `manifest.json` (`analyzedSha`, watch paths). The pack checker consumes them; git diffs against the SHA turn staleness into a CI signal.

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
```

Re-entry points: staleness signal → 06 before anything else. New component → 01/02. Behaviour change request → the standing instruction: model and DR first, code second.

## 4. Rules that do not bend

1. **Never decide domain semantics.** Unclear, contradictory, or unspecified behaviour becomes a question. Calling a gap "benign" is a proposal inside a question, never a reason to omit it.
2. **Requirement-scope rule.** A citation covers only the scenario its text describes. Control-trace verdicts that cite a requirement carry the line: *cited text contemplates this ordering: yes/no*. A "no" voids the verdict and raises a question.
3. **Callee contracts are read, not inferred.** Missing error handling at a call site is not evidence that failures propagate. Read the seam's contract; cite into the callee.
4. **Checks are executed code.** You emit data; the pack verifies it (`tools/dsc_check.py` on the sidecar). Where you write per-run checkers, you run them and paste the output. A red checker means: fix the artifact or fix the checker openly and re-run. Never "fix" the data to silence a check.
5. **Proposals are not decisions.** Your recommendations have flipped between runs on the same code. Present them, label them `proposed`, hold them loosely. Pre-selection in the interview is presentation, not authority.
6. **Tests bind to behaviour, not structure.** Assert only through the declared seam: projected state, emitted effects, SYS invariants. Never weaken, skip, or delete a test to make it pass. A failing cell test is a finding.
7. **Part B stays blind.** The blind session gets the catalogue, the requirements, and the event contracts — never the code, the matrix, or prior analyses, and no git archaeology on deleted ones.
8. **Deferred stays OPEN.** It blocks only its own cells.

## 5. What the checkers catch (so do not fight them)

Grid totality; disposition vocabulary; hole → Q back-references; DR links on ignore/reject/defer; behavioural-DR reverse coverage (every decided change is wired into a cell); pair → trace coverage; guard outcomes present; coverage-table totality; scope lines on citing control traces; Mermaid ↔ matrix sync; fragment citations within ±3 lines; manifest staleness; blind-table row coverage; schema validity of the sidecar; existence of every cited DR file.

## 6. Failure modes seen in real runs — avoid them

* Call-site inference declared a publisher failure path that the callee's contract excludes.
* A recorded decision (steady state) was applied to a race it never contemplated.
* A checklist category silently produced no variant.
* The catalogue stated gates but not remembrance semantics (what ended entities leave behind) — blind readers misread five rows for that one omission.
* Findings were lost between runs during consolidation.
* An expected-red test was almost softened instead of reported.

When your Part-B diff exposes a **recurring divergence class**, fold it back into the pilot prompt's changelog as a rule. Single findings stay findings. The goal is not zero divergence — a blind pass that cannot disagree is dead weight.
