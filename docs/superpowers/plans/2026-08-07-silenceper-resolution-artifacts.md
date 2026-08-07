# silenceper/pool Resolution Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create and validate a complete StateRadar to-be model and disposition matrix for the `silenceper/pool` benchmark from DR-001 through DR-006, without changing upstream code or generating implementation tests.

**Architecture:** The root `tests/benchmarks/silenceper-pool-32/analysis.json` remains the as-is benchmark oracle. A new `domain-analysis/channelPool/` directory is an approved, separate Resolution surface: it holds source-independent Mermaid models, a total 4×20 to-be matrix, the event catalogue used by `check_matrix.py`, invariant/lint results, a DR-cited semantic diff, and the remaining-hole declarations.

**Tech Stack:** Markdown, Mermaid `stateDiagram-v2`, YAML DR references, JSON sidecar as source data, `tools/gen_matrix_scaffold.py`, `tools/check_matrix.py`, and existing pack gates.

## Global Constraints

- This is a **StateRadar tool benchmark**. Do not clone, patch, test, tag, or push the upstream `silenceper/pool` repository.
- Do not create a test seam, red deviation tests, or an implementation worklist. Testgen is out of scope.
- Do not overwrite or promote the root `analysis.json`; it remains the current/as-is record until a later Reconcile phase.
- The to-be matrix must contain every canonical state × event pair exactly once: 4 states × 20 events = 80 cells.
- Every changed/decided cell must cite the applicable DR. `Q-UV-01` and `Q-07` are the remaining OPEN questions and must stay labelled on their cells.
- Preserve the caller-contract decisions: DR-002 and DR-006 are `NAT` assumptions, not runtime ownership tracking or rejection behavior.
- Before committing to `main`, run the full pack gate set and put its actual outputs in the commit Evidence block.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/event-catalogue.md` | Declares the exact 20 event IDs and their source/classification. |
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/as-is.machine.mmd` | Four-state current model, labelled as a representation of the root sidecar. |
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/to-be.machine.mmd` | Four-state approved model with DR-001 and DR-004 effects. |
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/disposition-matrix.md` | Four 20-event rows split into readable sub-tables; matrix authority for the to-be model. |
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/invariants-and-lints.md` | NAT/SYS statements and the Resolution lint result. |
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/to-be-diff.md` | Every as-is → to-be semantic difference, each cited by a DR. |
| `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/remaining-holes.md` | Explicitly retains Q-UV-01 (eight Get cells) and Q-07 (sixteen Release-UV cells). |

## Canonical Inputs

**States:** `Active_HasIdle`, `Active_IdleExhausted_UnderCap`, `Active_IdleExhausted_AtCapacity`, `Released`.

**Events, in matrix order:** `Get`, `Put`, `Close`, `Release`, `FactoryFail`, `IdleTimeout`, `PingFail`, `UV-Get-commission`, `UV-Get-value`, `UV-Put-loss`, `UV-Put-duplication`, `UV-Put-out-of-order`, `UV-Put-commission`, `UV-Close-duplication`, `UV-Close-out-of-order`, `UV-Close-contradiction`, `UV-Release-duplication`, `UV-Release-out-of-order`, `UV-Release-contradiction`, `UV-Release-commission`.

---

### Task 1: Create the Resolution directory, event catalogue, and red scaffold probe

**Files:**
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/event-catalogue.md`
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/open-questions.md`
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/disposition-matrix.md` (generated scaffold, then replaced in Task 3)

**Interfaces:**
- Consumes: root `analysis.json` states/events and `decisions/DR-001.yaml` through `DR-006.yaml`.
- Produces: the `<!-- event-ids: ... -->` declaration consumed by `gen_matrix_scaffold.py` and `check_matrix.py`.

- [x] **Step 1: Write the event catalogue with the exact event declaration**

Create `event-catalogue.md` with this declaration on one line:

```markdown
<!-- event-ids: Get Put Close Release FactoryFail IdleTimeout PingFail UV-Get-commission UV-Get-value UV-Put-loss UV-Put-duplication UV-Put-out-of-order UV-Put-commission UV-Close-duplication UV-Close-out-of-order UV-Close-contradiction UV-Release-duplication UV-Release-out-of-order UV-Release-contradiction UV-Release-commission -->
```

Add a catalogue table with all twenty IDs. Classify `Get`, `Put`, `Close`, and `Release` as external boundary calls; classify `FactoryFail`, `IdleTimeout`, and `PingFail` as internal; classify each `UV-*` row as undesired. State that the catalogue is inherited from the canonical root sidecar and that the to-be matrix uses the same abstraction.

- [x] **Step 2: Create the local remaining-question index**

Create `open-questions.md` containing only:

```markdown
# Remaining questions — silenceper/pool channelPool

## Q-UV-01: undesired Get variants

**Status:** OPEN.

`UV-Get-commission` and `UV-Get-value` remain unspecified in every state.
They are labelled `→ Q-UV-01` in the to-be matrix. DR-001 through DR-006 do
not decide caller authorization for Get() or ignored ErrClosed values.

## Q-07: undesired Release variants

**Status:** OPEN.

DR-001 decides only `Active_IdleExhausted_AtCapacity × Release`: terminal
Release resolves queued Get() calls with `ErrMaxActiveConnReached`. It does not
decide `UV-Release-duplication`, `UV-Release-out-of-order`,
`UV-Release-contradiction`, or `UV-Release-commission` in any state. Those
sixteen cells remain `UNSPECIFIED → Q-07`.
```

- [x] **Step 3: Generate the matrix scaffold**

Run:

```bash
python3 tools/gen_matrix_scaffold.py \
  tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool \
  --states "Active_HasIdle Active_IdleExhausted_UnderCap Active_IdleExhausted_AtCapacity Released" \
  --columns 7 --write
```

Expected: a new `disposition-matrix.md` with the canonical state declaration and three event sub-tables.

- [x] **Step 4: Run the red probe before filling cells**

Run:

```bash
python3 tools/check_matrix.py \
  tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool
```

Expected: non-zero exit with `coverage: empty cell` diagnostics. Save the command output for the eventual commit Evidence block. Do not bypass this failure by weakening `check_matrix.py`.

- [x] **Step 5: Commit the catalogue/scaffold red-probe stage**

Do not commit until Task 3 turns the probe green. Keep the scaffold and red output as the first half of the observed checker mechanism.

### Task 2: Write as-is/to-be models and decision documentation

**Files:**
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/as-is.machine.mmd`
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/to-be.machine.mmd`
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/to-be-diff.md`
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/invariants-and-lints.md`
- Create: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/remaining-holes.md`

**Interfaces:**
- Consumes: DR-001…DR-006 and canonical state names.
- Produces: DR-cited model changes and invariant language used by the matrix review.

- [x] **Step 1: Write `as-is.machine.mmd`**

Use Mermaid `stateDiagram-v2`. Declare the four canonical state names exactly. Include active-to-`Released` edges for `Release`, an at-capacity `Get` waiting/self edge, and a comment that the root `analysis.json` is the as-is authority. Do not encode desired waiter wake-up or Ping behavior in this file.

- [x] **Step 2: Write `to-be.machine.mmd`**

Copy the same four states and core topology. Add only these DR-labelled effects:

```mermaid
Active_IdleExhausted_AtCapacity --> Released: Release / resolve queued Get() with ErrMaxActiveConnReached (DR-001)
Active_IdleExhausted_AtCapacity --> Active_IdleExhausted_AtCapacity: queued Get / Ping before return; discard and retry on failure (DR-004)
```

Retain the as-is `Released --> Released` Release self-loop only as an observed-model edge with its existing citation. Do not attach DR-001 to that edge: DR-001 decides only the active at-capacity Release cell. Do not add a lease-tracking state or a duplicate-close state.

- [x] **Step 3: Write `to-be-diff.md`**

Write exactly these semantic diff categories, with each changed line carrying its DR:

1. At-capacity `Release` changes from an unanswered waiter-lifecycle hole to terminal transition plus waiter resolution — DR-001.
2. At-capacity queued `Get` gains configured Ping validation before delivery — DR-004.
3. Put misuse is a NAT caller contract, not a runtime ownership feature — DR-002.
4. Post-release Put is a terminal no-op — DR-003.
5. Factory failure returns without consuming capacity; at-capacity FactoryFail is not reachable through the Factory gate — DR-005.
6. `openingConns >= 0` is checked under the DR-002/DR-006 valid-caller assumption — DR-006.

End the document with: `No upstream source, test, tag, or push was changed by this Resolution artifact set.`

- [x] **Step 4: Write `invariants-and-lints.md`**

Create a `## NAT invariants` section containing the DR-002/DR-006 caller contract verbatim: a caller returns or closes one genuine borrowed connection exactly once and does not both Put and Close a borrow.

Create a `## SYS invariants` section containing:

```markdown
- INV-01 — `openingConns >= 0` while the DR-002/DR-006 valid-caller contract holds. [DR-006]
```

Create a four-row state check table. Mark INV-01 `holds under NAT` in each active state and `not mutable; terminal no-op` in `Released`. Add lint findings for terminal waiter resolution (DR-001), waiter-path Ping parity (DR-004), Factory capacity accounting (DR-005), and no ownership tracking (DR-002/DR-006).

- [x] **Step 5: Write `remaining-holes.md`**

List these eight remaining cells with `→ Q-UV-01`:

```text
Active_HasIdle × UV-Get-commission
Active_HasIdle × UV-Get-value
Active_IdleExhausted_UnderCap × UV-Get-commission
Active_IdleExhausted_UnderCap × UV-Get-value
Active_IdleExhausted_AtCapacity × UV-Get-commission
Active_IdleExhausted_AtCapacity × UV-Get-value
Released × UV-Get-commission
Released × UV-Get-value
```

Then list all sixteen state × `UV-Release-*` cells with `→ Q-07`: every canonical state crossed with `UV-Release-duplication`, `UV-Release-out-of-order`, `UV-Release-contradiction`, and `UV-Release-commission`. State that DR-001 decides only the base at-capacity Release cell; Q-07 preserves its remaining undesired-variant scope. State that no Testgen or implementation phase is included in this benchmark task.

### Task 3: Fill the total to-be disposition matrix and turn the probe green

**Files:**
- Modify: `tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/disposition-matrix.md`

**Interfaces:**
- Consumes: the Task 1 scaffold, Task 2 DR semantics, canonical base grid, and remaining Q-UV-01 holes.
- Produces: exactly 80 non-empty cells accepted by `tools/check_matrix.py`.

- [x] **Step 1: Add the matrix abstraction and terminal declaration**

Place immediately below the state declaration:

```markdown
Abstraction: four flat leaf states derived from idle availability, capacity,
and terminal release; completeness is relative to the twenty-event catalogue.
<!-- terminal: Released -->
```

- [x] **Step 2: Fill the seven base-event columns with these exact dispositions**

Use the root sidecar’s existing code citations for unchanged documented/reject/defer rows. Cite DRs for the rows below that are decided by Resolution.

| State | Get | Put | Close | Release | FactoryFail | IdleTimeout | PingFail |
|---|---|---|---|---|---|---|---|
| `Active_HasIdle` | `handle` | `handle` | `handle` | `transition →Released` | `handle` | `handle` | `handle` |
| `Active_IdleExhausted_UnderCap` | `handle` | `transition →Active_HasIdle` | `handle DR-006` | `transition →Released` | `handle DR-005` | `ignore (documented)` with existing citation | `ignore (documented)` with existing citation |
| `Active_IdleExhausted_AtCapacity` | `defer (queued) DR-004; Ping before return` | `handle` | `handle DR-006` | `transition →Released DR-001; resolve waiters` | `ignore (documented) DR-005; Factory gate cannot fire at capacity` | `ignore (documented)` with existing citation | `ignore (documented)` with existing citation |
| `Released` | `reject` with existing citation | `ignore (documented) DR-003` | `ignore (documented)` with existing citation | `ignore (documented) DR-001` | `ignore (documented)` with existing citation | `ignore (documented)` with existing citation | `ignore (documented)` with existing citation |

- [x] **Step 3: Fill the thirteen undesired-event columns with these exact policies**

1. For `UV-Get-commission` and `UV-Get-value`, write `UNSPECIFIED → Q-UV-01` in every state.
2. For `UV-Put-loss`, `UV-Put-duplication`, and `UV-Put-commission`, write `ignore (documented) DR-002; NAT caller contract` in every state.
3. For `UV-Put-out-of-order`, write `ignore (documented) DR-003; terminal/no-ownership contract` in every state.
4. For `UV-Close-duplication`, `UV-Close-out-of-order`, and `UV-Close-contradiction`, write `ignore (documented) DR-006; NAT caller contract` in every state.
5. For all four `UV-Release-*` columns, write `UNSPECIFIED → Q-07` in every state. DR-001 is not a citation for these cells because its accepted scope is only `Active_IdleExhausted_AtCapacity × Release`.

- [x] **Step 4: Run the green checker**

Run:

```bash
python3 tools/check_matrix.py \
  tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool
```

Expected: `CHECK MATRIX: OK`. If it reports an empty cell, fill that exact state/event cell; do not change event declarations, checker code, or the root as-is sidecar to hide the error.

- [x] **Step 5: Verify model/matrix name agreement**

Run:

```bash
rg -n 'Active_HasIdle|Active_IdleExhausted_UnderCap|Active_IdleExhausted_AtCapacity|Released' \
  tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/{as-is,to-be}.machine.mmd \
  tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool/disposition-matrix.md
```

Expected: all four canonical names appear in both Mermaid models and the matrix.

### Task 4: Verify the Resolution-only boundary and commit

**Files:**
- Verify only: root `tests/benchmarks/silenceper-pool-32/analysis.json`, `expected.json`, upstream source paths, and Git release state.
- Commit: only the new `domain-analysis/channelPool/` artifact directory and any status-wording correction needed to say Testgen is out of scope.

**Interfaces:**
- Consumes: Tasks 1–3.
- Produces: a committed, green Resolution artifact set without implementation or release side effects.

- [x] **Step 1: Prove the root benchmark oracle was not promoted**

Run:

```bash
git diff -- tests/benchmarks/silenceper-pool-32/analysis.json \
  tests/benchmarks/silenceper-pool-32/expected.json
```

Expected: no root-sidecar or expected-fixture changes from this Resolution artifact task. If previously committed decision metadata appears, do not rewrite it.

- [x] **Step 2: Run the complete verification set**

Run:

```bash
python3 tools/check_matrix.py tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool
uv run --with-requirements tools/requirements-dev.txt python3 tools/dsc_check.py tests/benchmarks/silenceper-pool-32
uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
python3 tools/check_pack_consistency.py
python3 tools/run_tool_tests.py
python3 tools/run_benchmark.py
python3 tools/benchmark_evidence.py
git diff --check
git status --short
```

Expected: matrix checker green; canonical sidecar and pack gates green; `run_tool_tests` reports `2/2 cases pass`; benchmark reports `5 passed, 0 failed, 5 total`; evidence reports `2 primary`, `3 regression`, `0 unknown`; no upstream source/test, tag, or push action appears.

- [x] **Step 3: Commit the Resolution artifact set with red/green evidence**

```bash
git add tests/benchmarks/silenceper-pool-32/domain-analysis/channelPool
git commit -m "Add silenceper Resolution to-be artifacts" \
  -m "Records DR-001 through DR-006 in a separate to-be model and total 4×20 matrix. Q-UV-01 and Q-07 remain explicit. No upstream implementation or Testgen work is included.

Evidence:
- Matrix red probe: CHECK MATRIX failed on empty scaffold cells.
- Matrix green probe: CHECK MATRIX: OK.
- Paste the actual full-gate outputs from Step 2."
```

- [x] **Step 4: Stop**

Do not tag, push, generate tests, create an upstream patch, or reconcile the to-be model into the root as-is sidecar. Report the artifact path, the checker red/green evidence, and the remaining Q-UV-01 and Q-07 holes.

## Execution Handoff

Execute only Tasks 1 through 4. The completion boundary is a committed, checker-green Resolution artifact set under `domain-analysis/channelPool/`. Do not continue to Testgen, upstream implementation, release, or push work without a new user instruction.
