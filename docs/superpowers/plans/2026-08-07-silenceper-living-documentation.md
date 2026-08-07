# silenceper/pool Living Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the silenceper benchmark living documentation current, linked, and consistent with its completed Resolution-only artifact set.

**Architecture:** Add one benchmark-local living index at `domain-analysis/summary.md`. Update the root question register and the two benchmark-facing indexes to link to it. Keep the canonical root sidecar as as-is evidence, and keep the standard lifecycle in public documentation unchanged.

**Tech Stack:** Markdown, canonical JSON sidecar metadata, `ripgrep`, Python standard library path checks, and existing StateRadar pack gates.

## Global Constraints

- Change only silenceper living documentation, the benchmark index, and the implementation plan. Do not change `README.md`, `AGENTS.md`, generic prompts, the roadmap, historical specs, or `CHANGELOG.md`.
- Do not change `tests/benchmarks/silenceper-pool-32/analysis.json`, `expected.json`, decision records, upstream source, or upstream tests.
- The root sidecar is the canonical as-is record. The to-be artifacts remain under `domain-analysis/channelPool/`.
- Q-UV-01 is an OPEN canonical-sidecar question. Q-07 is an OPEN Resolution-local question and is not a root-sidecar question.
- Q-01 through Q-06 have accepted DRs only within their documented scopes.
- The benchmark stops after Resolution. Do not claim Testgen, upstream implementation, Reconcile, release, tag, or push results.
- Before committing to `main`, run the full pack gate set and paste actual outputs into the commit Evidence block.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tests/benchmarks/silenceper-pool-32/domain-analysis/summary.md` | New living index for as-is/to-be separation, DR status, open holes, validation, and scope boundary. |
| `tests/benchmarks/silenceper-pool-32/open-questions.md` | Root question register with corrected Q-01…Q-06 status text and explicit Q-UV-01/Q-07 entries. |
| `tests/benchmarks/silenceper-pool-32/MANIFEST.md` | Historical oracle finding plus a link to the current living index. |
| `tests/benchmarks/README.md` | Public benchmark-suite table with a link to the silenceper living index. |
| `docs/superpowers/plans/2026-08-07-silenceper-living-documentation.md` | Execution checklist for this documentation update. |

## Required Terminology

| Term | Required meaning |
|---|---|
| as-is | The canonical root `analysis.json` observation record. |
| to-be | The separate checker-green Resolution artifacts in `domain-analysis/channelPool/`. |
| Q-UV-01 | OPEN root-sidecar question about undesired Get variants. |
| Q-07 | OPEN Resolution-local question about undesired Release variants. |
| completed | The Resolution documentation artifact set and its pack validation are complete. It never means upstream implementation is complete. |

---

### Task 1: Create the living index and repair the root question register

**Files:**
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/summary.md`
- Modify: `tests/benchmarks/silenceper-pool-32/open-questions.md`

**Interfaces:**
- Consumes: `analysis.json`, `decisions/DR-001.yaml` through `DR-006.yaml`, and `domain-analysis/channelPool/` artifacts.
- Produces: a current documentation entry point that later benchmark indexes link to.

- [x] **Step 1: Show the stale status text before editing**

Run:

```bash
rg -n 'to-be model and test generation pending' \
  tests/benchmarks/silenceper-pool-32/open-questions.md
```

Expected: six matches, one for each of Q-01 through Q-06. This is the stale-text baseline. Do not change the root sidecar to remove it.

- [x] **Step 2: Create `domain-analysis/summary.md`**

Write the document with the following content. Use these relative links from the
new summary file.

```markdown
# silenceper/pool — Living Analysis Index

## Current status

The canonical root sidecar is the as-is observation record:
[`../analysis.json`](../analysis.json). The completed Resolution-only to-be
artifact set is in [`channelPool/`](channelPool/). The to-be matrix passed
`check_matrix.py`. The canonical sidecar passed `dsc_check.py` with 4 states,
20 events, and 80 cells.

This benchmark stops after Resolution. It has no Testgen result, upstream
implementation result, Reconcile result, release, tag, or push.

## As-is record

- [Canonical sidecar](../analysis.json)
- [Root question register](../open-questions.md)
- [Oracle manifest](../MANIFEST.md)
- [Convergence record](../CONVERGENCE.md)

## Resolution to-be record

- [As-is model](channelPool/as-is.machine.mmd)
- [To-be model](channelPool/to-be.machine.mmd)
- [Event catalogue](channelPool/event-catalogue.md)
- [Disposition matrix](channelPool/disposition-matrix.md)
- [Invariants and lints](channelPool/invariants-and-lints.md)
- [Semantic diff](channelPool/to-be-diff.md)
- [Local question register](channelPool/open-questions.md)
- [Remaining holes](channelPool/remaining-holes.md)

## Accepted decisions

| Decision | Scope |
|---|---|
| [DR-001](../decisions/DR-001.yaml) | `Active_IdleExhausted_AtCapacity × Release` resolves queued `Get()` waiters with `ErrMaxActiveConnReached`. |
| [DR-002](../decisions/DR-002.yaml) | Put integrity is a NAT caller contract. |
| [DR-003](../decisions/DR-003.yaml) | `Put()` after `Release()` is a safe terminal no-op. |
| [DR-004](../decisions/DR-004.yaml) | Queued `Get()` delivery uses configured Ping validation. |
| [DR-005](../decisions/DR-005.yaml) | Factory failure does not consume capacity. |
| [DR-006](../decisions/DR-006.yaml) | `openingConns >= 0` holds under the valid-caller contract. |

## Open questions

- **Q-UV-01 — OPEN:** canonical-sidecar undesired Get variants. See the
  [root question register](../open-questions.md) and the
  [local question register](channelPool/open-questions.md).
- **Q-07 — OPEN:** Resolution-local undesired Release variants. DR-001 does
  not decide these 16 cells. See the [remaining holes](channelPool/remaining-holes.md).
```

- [x] **Step 3: Correct all six answered status lines**

In `open-questions.md`, replace each exact status suffix:

```markdown
; to-be model and test generation pending.
```

with:

```markdown
; to-be artifacts complete. Testgen is intentionally out of scope for this benchmark task. See [the living analysis index](domain-analysis/summary.md).
```

Apply the replacement only to Q-01 through Q-06. Preserve their findings,
accepted decision text, DR links, and as-is citations.

- [x] **Step 4: Add the two current open-question entries**

Append these entries after Q-06:

```markdown
## Q-UV-01: undesired Get variants (F-17, F-18)

**Status:** OPEN — canonical as-is sidecar question.

A caller can invoke `Get()` with a pool reference when no legitimate trigger
exists. A caller can also ignore `ErrClosed` after `Get()` follows `Release()`.
The to-be matrix records these variants as `UNSPECIFIED → Q-UV-01`. See the
[local question register](domain-analysis/channelPool/open-questions.md).

## Q-07: undesired Release variants

**Status:** OPEN — Resolution-local question; not a root-sidecar question.

DR-001 decides only `Active_IdleExhausted_AtCapacity × Release`. It does not
decide duplicate, stale, contradictory, or unsolicited Release events in any
state. The to-be matrix records these 16 cells as `UNSPECIFIED → Q-07`. See
[the remaining holes](domain-analysis/channelPool/remaining-holes.md).
```

- [x] **Step 5: Prove the question register is current**

Run:

```bash
! rg -n 'to-be model and test generation pending' \
  tests/benchmarks/silenceper-pool-32/open-questions.md
rg -n 'to-be artifacts complete|Q-UV-01|Q-07|Resolution-local question' \
  tests/benchmarks/silenceper-pool-32/open-questions.md
```

Expected: the stale phrase has no matches. The output shows all six corrected
statuses and both OPEN questions.

### Task 2: Link the benchmark-facing documentation to the living index

**Files:**
- Modify: `tests/benchmarks/silenceper-pool-32/MANIFEST.md`
- Modify: `tests/benchmarks/README.md`

**Interfaces:**
- Consumes: the Task 1 summary at `silenceper-pool-32/domain-analysis/summary.md`.
- Produces: discoverable links from the historical manifest and the benchmark suite table.

- [x] **Step 1: Show that the current indexes have no living-index link**

Run:

```bash
! rg -n 'domain-analysis/summary\.md' \
  tests/benchmarks/silenceper-pool-32/MANIFEST.md tests/benchmarks/README.md
```

Expected: no match before the update.

- [x] **Step 2: Add a current-analysis section to `MANIFEST.md`**

Append this section after the three bullets in `## StateRadar output`, at the end of `MANIFEST.md`:

```markdown
## Current analysis status

This manifest preserves the frozen as-is oracle finding. The separate
Resolution-only to-be artifact set is complete and checker-green. See the
[living analysis index](domain-analysis/summary.md).

This benchmark task does not include Testgen, upstream implementation,
Reconcile, a release, a tag, or a push.
```

Do not alter the Issue, PR, Commit, Date, Oracle, primary finding, defect
class, or StateRadar-output text.

- [x] **Step 3: Add the summary link to the benchmark suite table**

In the `silenceper/pool` row of the `## Oracle-confirmed benchmarks (3/3)`
table in `tests/benchmarks/README.md`, replace the defect-class cell:

```markdown
connReqs never closed
```

with:

```markdown
connReqs never closed ([current analysis](silenceper-pool-32/domain-analysis/summary.md))
```

Do not alter the row count, issue URL, bug count, or generated ODC block.

- [x] **Step 4: Verify local links and intended scope**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
checks = {
    Path('tests/benchmarks/silenceper-pool-32/MANIFEST.md'):
        'domain-analysis/summary.md',
    Path('tests/benchmarks/README.md'):
        'silenceper-pool-32/domain-analysis/summary.md',
    Path('tests/benchmarks/silenceper-pool-32/open-questions.md'):
        'domain-analysis/summary.md',
}
for document, reference in checks.items():
    target = document.parent / reference
    assert target.is_file(), f'{document}: missing {reference}'
    print(f'OK {document}: {reference}')
PY
git diff --quiet -- README.md AGENTS.md docs/roadmap.md prompts CHANGELOG.md
```

Expected: each local link target exists. The generic public lifecycle and
historical documentation files have no diff.

### Task 3: Run the documentation and pack gates, then commit

**Files:**
- Verify: all Task 1 and Task 2 files.
- Commit: the summary, question register, manifest, benchmark index, and this plan.

**Interfaces:**
- Consumes: completed documentation links and corrected status text.
- Produces: a committed local documentation update with the pack gates green.

- [x] **Step 1: Run the direct documentation assertions**

Run:

```bash
rg -n 'canonical root sidecar|Resolution-only|Q-UV-01|Q-07|Testgen' \
  tests/benchmarks/silenceper-pool-32/domain-analysis/summary.md
! rg -n 'to-be model and test generation pending' \
  tests/benchmarks/silenceper-pool-32/open-questions.md
rg -n 'current analysis' tests/benchmarks/README.md
rg -n 'living analysis index' tests/benchmarks/silenceper-pool-32/MANIFEST.md
```

Expected: the summary distinguishes as-is from to-be, both OPEN questions are
visible, no stale phrase remains, and both benchmark-facing links are visible.

- [x] **Step 2: Run the complete gate set**

Run:

```bash
uv run --with-requirements tools/requirements-dev.txt python3 tools/dsc_check.py tests/benchmarks/silenceper-pool-32
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
git status --short
```

Expected: `dsc_check` reports 4 states, 20 events, and 80 cells. The pack
checker reports `PACK CONSISTENCY: OK`. Tool tests report `2/2 cases pass`.
The benchmark runner reports `5 passed, 0 failed, 5 total`. Evidence reports
`2 primary`, `3 regression`, and `0 unknown`.

- [x] **Step 3: Commit the documentation update**

```bash
git add \
  docs/superpowers/plans/2026-08-07-silenceper-living-documentation.md \
  tests/benchmarks/README.md \
  tests/benchmarks/silenceper-pool-32/MANIFEST.md \
  tests/benchmarks/silenceper-pool-32/open-questions.md \
  tests/benchmarks/silenceper-pool-32/domain-analysis/summary.md
git commit -m "Refresh silenceper living documentation" \
  -m "Links the as-is benchmark record to the completed Resolution-only to-be artifacts. Records Q-UV-01 and Q-07 as open. Does not claim Testgen, upstream implementation, Reconcile, release, tag, or push work.

Evidence:
- Paste direct documentation assertion output.
- Paste the actual complete gate output."
```

- [x] **Step 4: Stop at the documented boundary**

Do not start Testgen, upstream implementation, Reconcile, a release, a tag, or
a push. Report the committed documentation paths, the remaining Q-UV-01/Q-07
questions, and the gate outputs.

## Execution Handoff

Execute only Tasks 1 through 3. Completion is a local documentation commit with
all direct assertions and pack gates green. The next StateRadar tool-development
item remains the separate roadmap matrix-mutation-checker design, not a
silenceper implementation task.
