# Resolution Prompt — Decisions → To-Be Model (Pass 3 + 5)

**How to use:** run after the pilot analysis (02), when you have answers for some or all questions in `open-questions.md`. Give your answers in one of three ways: edit `open-questions.md` (fill `Decision:` and `Rationale:` per question), paste them into the message, or select the interactive interview. Fill in CONFIG. Then paste this file into your coding agent at the repository root.

## CONFIG — fill in before running

```text
Analysis directory:     domain-analysis/<component>/
Answers provided via:   <edited open-questions.md | pasted below | interactive interview>
Chain into resolution:  <yes | no>   (interview mode only)
```

---

## PROMPT

You turn human decisions into an approved to-be behavioural model. You specify. You do not implement.

### Hard rules

1. Do not modify any source code, tests, or configuration. Your outputs are model, matrix, decision-record, and report files in the analysis directory only.
2. Only a question with an explicit human decision gets resolved. Unanswered questions stay OPEN. Never fill a gap with your own judgment. A plausible answer from you is still a specification hole.
3. An answer can be unclear, contradict another answer, or violate a SYS invariant or NAT assumption. In that case do not resolve the item. Record a follow-up question and spell out the conflict.
4. Every deviation of the to-be model from the as-is model must trace to a decision record or an explicit requirement. A to-be change without a DR is an error.
5. Provenance discipline continues: annotate to-be elements with the DR id or the requirement that justifies them.

### Step 0 — Interactive interview (only when CONFIG selects it)

Collect the owner's decisions one question at a time, with the recorded options as selectable choices and the proposal pre-selected. Never decide for the owner.

1. Read every OPEN question first. If the kickoff carries a **question-set amendments** block: apply it (add or adjust options and questions) before you interview.
2. Ask strictly one question per round, in id order. Announce progress ("Q-04: 4 of 17"). Before each choice, print a compact context card: the question, the current behaviour with its key citation, why it matters (the finding or doctrine at stake), and the Part-B status. No walls of text.
3. Present the choice with the harness's interactive question tool (Claude Code: `AskUserQuestion`). One question per call. Multi-select off. **List the recommended option first and label it "(recommended)". In Claude Code's picker the first option is the Enter-default. That implements the pre-selection.** Give every option a one-line consequence description. The built-in free-text field accepts an alternative decision, or `defer` to leave the question OPEN. Harness fallback without an interactive tool: numbered text menu, "1 = recommended, Enter = 1".
4. Capture the rationale with honest attribution. Recommended option accepted → `Rationale: proposal rationale adopted (owner-confirmed)`. Any other option or free text → ask one short follow-up for a rationale. If the owner skips it, record `Rationale: none given (owner decision)`. Never invent a rationale.
5. **Write through after every answer.** Update that question in `open-questions.md` at once: `Decision:`, `Rationale:`, `Status: ANSWERED — pending decision record`, `Decided-via: interactive interview <date>`. An aborted session must lose nothing.
6. Light live conflict check: an answer can directly contradict an earlier answer of this session or a SYS invariant. Say so and re-ask once. The full conflict analysis stays in Step 1.
7. End of interview: print a summary table (Q → decision; mark deviations from the recommendation) and the answered/deferred counts. If CONFIG says `Chain into resolution: yes`: continue with Step 1. Otherwise stop.

Rules that do not bend: the interviewer never answers a question itself. Pre-selection is presentation, not authority: the record must show that the owner acted. A deferred question stays OPEN and blocks only its own cells.

### Step 1 — Intake check

Read the analysis directory. List: questions with decisions, questions still open, and conflicts (answer vs. answer, answer vs. invariant, answer vs. NAT). A conflict becomes a follow-up question in `open-questions.md`, marked `Status: CONFLICT — needs re-decision`, and drops out of this run.

### Step 2 — Decision records

For every resolved question, write `decisions/DR-NNN.yaml`. Numbering starts at DR-001 and continues from existing DRs. Schema:

```yaml
id: DR-007
date: <today>
source_question: Q-07
question: May a delayed connection.opened reactivate a stopped device?
options: [reactivate, ignore, reject-with-diagnostic]
decision: ignore
rationale: <the human's rationale, verbatim gist>
links: ["matrix: stopped x connection.opened"]
status: accepted
```

Maintain `decisions/INDEX.md`: Q-ids mapped to DR-ids, with one-line summaries.

### Step 3 — To-be model

Start from `as-is.machine.mmd`. Apply the accepted DRs and nothing else. Produce:

* `to-be.machine.mmd`: Mermaid `stateDiagram-v2`; a changed or added element carries the DR id in the transition label or a comment
* `to-be-diff.md`: the semantic diff as-is → to-be, listing added, removed, and changed states, transitions, guards, actions. Every line cites its DR. A diff line without a DR citation is an error. Fix it before you finish.

### Step 4 — Matrix update

Regenerate `disposition-matrix.md` for the to-be model: rows = to-be leaf states, columns = the full catalogue incl. undesired variants. Rules:

* every `ignore` / `reject` / `defer (queued)` cell carries its DR link
* a cell governed by a still-open question stays `UNSPECIFIED` and appears in `remaining-holes.md`
* `ignore (accidental)` may no longer appear. Each such cell from the pilot is now either decided (DR) or listed as a remaining hole.

### Step 5 — Invariants and lints

A decision can add or strengthen SYS invariants. Extract those and add them to `invariants-and-lints.md` with their DR link. Then re-check every SYS invariant against the to-be model, state by state. Re-run the lint checklist from the pilot: timeouts on waiting states, retry limits, failure outcomes, cancellation, terminal-state meaning, startup and shutdown, capacity. A new finding becomes a new question in `open-questions.md`.

### Step 6 — Mechanical self-check

Update and execute `check_matrix.py` against the new matrix: grid completeness; a DR link on every ignore/reject/defer cell; no `ignore (accidental)` values left. Re-run `check_guards.py` against the to-be guards. Decisions often change thresholds or add branches. Every guard group must again end `proven`, `violation`, or `not-formalizable`. Include both outputs in `summary.md`. Deliver checks as executed code, never as claims.

### Step 7 — Summary

Update `summary.md`: DRs written, questions still open, conflicts raised, new questions from Step 5, diff statistics (transitions added, removed, changed). End with the explicit statement: **the implementation remains untouched. The test-generation step (04), not this step, establishes the deviation between to-be and current code.**
