<!-- rule:R-WEAK-TEST-AUDIT -->
# Test Audit — Weak Tests and Coverage Prompt

**How to use:** fill in the CONFIG block. Then paste this file into your coding agent at the repository root. The agent audits an existing test suite against the decided disposition matrix of one analyzed component. Its main goal: improve test and software quality. It finds weak tests that bind to implementation instead of behaviour. It finds redundant tests, coverage gaps, and deviations. It never changes, deletes, or weakens a test.

## CONFIG — fill in before running

```text
Analysis directory:   <domain-analysis/<component>/>
Test paths:           <dirs or globs of the unit-test suite under audit>
Reference suite:      <path of the pack-generated domain tests, or "none">
Exclude:              <generated or vendored test dirs>
```

---

## PROMPT

You audit a test suite against the decided domain model of one stateful component. You judge what every test observes. You classify. You propose. You never modify.

### Hard rules

1. Do not modify, delete, or weaken any file. Your outputs are new artifacts in the analysis directory.
2. The decided matrix is the oracle. Never adjust the model to fit the tests. Every mismatch is a finding.
3. The seam is the only strength criterion. `seam.md` declares it: projected state, emitted effects, SYS invariants. A test is weak when none of its assertions read the seam.
4. Classify before you propose. Every test gets exactly one class. Every cell gets exactly one class. Nothing stays unclassified.
5. Every claim carries provenance. Tests: `file:line ("fragment")`. Cells: the decided disposition.
6. Deletion and weakening are human decisions. Every such proposal becomes a decision-record draft, marked `proposed`.
7. Checks are executed code. You emit `check_test_coverage.py`, run it, and paste the output.
8. Scenario tests overlap cell tests by design. Never mark a scenario test as a duplicate of a cell test.
9. The reference suite is sound by construction. The pack generated it from the matrix. Do not re-judge it. Use it as coverage evidence only.
10. Maximize test quality. Prefer rewrite to deletion. A reference test proves cell coverage. It does not prove boundary coverage. Never propose deletion when the audited test covers boundary cases that the reference test does not cover.

### Step 1 — Load the decided model

Read `disposition-matrix.md`, `event-catalogue.md`, `seam.md`, and `open-questions.md` from the analysis directory. Verify the analysis state: the matrix exists, and every hole cell carries a `→ Q-nn`. If the matrix does not exist, stop. The pilot must run first. When the reference suite exists, load `matrix-coverage.json`. Its entries name the cells that the reference suite covers with sound tests.

### Step 2 — Restate the seam

State the three observation channels from `seam.md`: projected state (what the component exposes), emitted effects (what crosses the boundary), and SYS invariants. If `seam.md` is missing, derive the seam from the analysis artifacts and record the gap as a finding.

### Step 3 — Judge every test

For each test, answer one question: what does this test observe? Use these weakness signals:

* asserts on private fields or internal state instead of the projection
* verifies calls on internal collaborators: mock verification, call counts, argument capture
* asserts internal strings, log lines, or error texts that the contract does not declare
* mirrors the implementation structure: one test per helper or per branch
* reads nothing that survives a behaviour-preserving refactoring

Assign exactly one class per test:

* `sound`: asserts through the seam only.
* `weak-redundant`: structure-bound, and the targeted behaviour is observable through the seam. Propose a rewrite to seam assertions when the test is the only coverage. When an equivalent seam test exists (in the reference suite or the audited suite), compare the boundary coverage: the weak test and the reference test. If the weak test asserts edge cases the reference test does not, the higher-quality outcome is a rewrite, not a deletion. Propose deletion only when the reference test already covers every boundary the weak test exercises. The standard is test quality, not test count.
* `weak-seam-gap`: structure-bound because the seam does not expose the behaviour. This is a seam-gap finding. It becomes a new `Q-nn`: extend the projection?
* `weak-incidental`: asserts detail with no behavioural relevance. Deletion candidate.
* `equivalent-duplicate`: sound, but it matches another test in cells, assertions, and expected values. Redundancy candidate. Propose which test to keep: the one with more SYS-invariant assertions.
* `deviating`: expects behaviour that the decided disposition contradicts. Record a deviation entry.
* `unmapped-behavioural`: drives behaviour that no cell covers. This is a matrix gap. It becomes a new `Q-nn`.

### Step 4 — Classify every cell

* `covered`: at least one `sound` test, in the audited suite or in the reference suite.
* `weakly-covered`: no `sound` test anywhere, only weak tests. The cell needs a seam-bound test. Note it in the report.
* `uncovered`: no test at all. A coverage gap.
* `contested`: a `deviating` test exists. The deviation decides the follow-up, never the auditor.

### Step 5 — Emit and run the checker

Write `check_test_coverage.py` into the analysis directory. It verifies totality: every test carries a class, every cell carries a class, no item is unclassified. When a reference suite is configured, it also verifies that every deletion proposal cites a covering cell from `matrix-coverage.json`. It prints the counts per class. Run it. Paste the output into the report.

### Step 6 — Report

Write `test-coverage-map.md`: one line per test with class, mapped cells, and citation. Write `coverage-diff-report.md` with six sections:

1. **Weak tests.** Grouped by class (`weak-redundant`, `weak-seam-gap`, `weak-incidental`), each with evidence and its proposal.
2. **Redundancy candidates.** Each `equivalent-duplicate` pair with the keep-proposal and the reason.
3. **Deviations.** Each `deviating` test with the contradicted disposition.
4. **Coverage.** `weakly-covered` and `uncovered` cells.
5. **DR proposals.** One draft per deletion or weakening: the question, numbered options with the quality-maximizing option first, the evidence. Prefer rewrite over deletion when boundary coverage is at stake.
6. **Questions.** New `Q-nn` entries for seam gaps and matrix gaps, appended to `open-questions.md` as proposals, marked `proposed`.
