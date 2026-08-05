# Reconcile Prompt — Close the Loop (Stage 06)

**How to use:** run at the end of the implementation branch, after the deviation report reaches zero. Also run it later, whenever code under the component changed and the manifest reports the analysis as stale. Fill in CONFIG. Then paste this file into your coding agent at the repository root.

## CONFIG — fill in before running

```text
Analysis directory:   domain-analysis/<component>/
Component paths:      <paths the manifest watches, e.g. src/.../trigger/>
Branch:               <implementation branch, or current>
```

---

## PROMPT

You close the analysis loop. The approved model becomes the new as-is. The artifacts become fresh at HEAD. You change no behaviour in this run.

### Hard rules

1. Do not change component code or tests. Your outputs are analysis artifacts, the sidecar, and the manifest.
2. Promote only with proof. Every suite and every checker must be green at HEAD before Step 2.
3. Delete nothing. A superseded artifact moves to `archive/<date>/` inside the analysis directory.
4. A refreshed citation is a verified citation: `file:line ("fragment")`, with the fragment present near that line at HEAD.
5. Deferred questions stay OPEN. Reconciliation resolves staleness, not decisions.

### Step 0 — Preconditions

Run: the project baseline suite, the cell suite, the scenario suite, `check_matrix.py` (stage 2), `check_guards.py`, and the pack checker `tools/dsc_check.py`. All must pass. The deviation report must contain zero open items. If a precondition fails: stop and report. Do not promote.

There is no reconcile-lite. A promotion without `analysis.json` and a green `dsc_check` leaves the component below L4 (00-methods-reference, "Maturity levels"): the staleness anchor, the citation checks, and the CI gate all need the sidecar. An archive-plus-manifest bump without it does not reconcile anything — and it lets unverified "steady states" enter the record (dobby session, 2026-08-05).

### Step 1 — Archive

Create `archive/<date>/`. Move into it: the old `as-is.machine.mmd`, `to-be-diff.md`, and the resolved `deviation-report.md`. The `decisions/` directory never moves. It is the permanent memory.

### Step 2 — Promote

Rename `to-be.machine.mmd` to `as-is.machine.mmd`. Remove the to-be framing from the matrix header. The approved model is now the record of current behaviour.

### Step 3 — Citation refresh

Re-resolve every `observed-in-code` and `observed-in-tests` citation in the artifacts against HEAD. Fix drifted line numbers. Add a fragment to every citation that has none. Behaviour that the implementation added gets new citations: each behavioural DR now has an `observed-in-code` anchor.

### Step 4 — Sidecar and manifest

Emit `analysis.json` per the pack schema (`formats/analysis.schema.json`): states, events, cells with dispositions and links, pairs with traces, guard outcomes, the coverage table, questions, behavioural DRs. Write `manifest.json`: component, watch paths, `analyzedSha` = HEAD, pack version, date.

### Step 5 — Verify

Run `tools/dsc_check.py <analysis-dir> --repo . --model as-is.machine.mmd`. Citation checks and the staleness check must pass at HEAD. Include the output in `summary.md`.

### Step 6 — Summary addendum

Append to `summary.md`: the promotion note, the archive location, the citation-refresh count, and the list of questions that stay OPEN. End with the statement: **the component is in steady state; the standing instruction governs further changes; a stale manifest calls this prompt again.**
