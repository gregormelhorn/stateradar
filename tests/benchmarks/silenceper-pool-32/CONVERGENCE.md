# CONVERGENCE — silenceper/pool

**Component:** `silenceper/pool` channelPool (Go connection pool)
**Method:** Two independent Part-A pilot runs on the same component.
**Status:** Baseline recorded 2026-08-07, pack v1.44.
Run 1: code-informed (this session). Run 2: independent fresh subagent.

## Protocol (automated via tools/ensemble_convergence.py)

1. Run 1: extract states, events, cells from channel.go/pool.go with code access.
2. Run 2: fresh subagent, no access to Run 1's analysis, independent extraction.
3. Normalize event/state names to a shared canonical vocabulary.
4. Run `python3 tools/ensemble_convergence.py run1.json run2.json -o merged.json --report report.md`.

## Run 1 (code-informed)

**States:** 5 — Initializing, Active_HasIdle, Active_IdleExhausted_UnderCap,
Active_IdleExhausted_AtCapacity, Released
**Events:** 10 (7 boundary + 3 internal)
**Cells:** 50 (5 × 10)
**UNSPECIFIED:** 8 → 7 questions

## Run 2 (independent, fresh subagent)

**States:** 4 — Active_HasIdle, Active_IdleExhausted_UnderCap,
Active_IdleExhausted_AtCapacity, Released
**Events:** 8 base + 28 UV variants
**Cells:** 32 (4 × 8, base events only)
**UNSPECIFIED:** 51 (including UV columns) → 12 questions

## Divergence

**Aligned grid (4 × 7 = 28 cells), mechanical diff via tools/ensemble_convergence.py:**

| Metric | Value |
|---|---|
| Aligned states | 4 |
| Aligned events | 7 (Get, Put, Close, Release, IdleTimeout, PingFail, FactoryFail) |
| Aligned cells | 28 |
| Convergent | 28 |
| Cell-divergent | 0 |
| **Behavioural convergence rate** | **100.0 %** |
| Structural findings | 5 (1 state granularity + 4 event granularity) |

**Zero cell divergence.** Both runs independently agree on every
semantically aligned cell — including the critical finding: Release()
does not close connReqs waiter channels (F-07 lifecycle coupling).

**Structural divergence (5 findings):**

- Run 1 models `Initializing` as a separate constructor-only state;
  Run 2 folds initialization into the active states.
- Event granularity: Run 1 distinguishes PutNil, CloseNil, Len;
  Run 2 separates FactoryCreate from FactoryFail. These are naming
  choices, not behavioural disagreements.

**Finding-level convergence (manually recorded):**

Both runs independently found the Release/connReqs goroutine leak (F-07).
Run 1: Q-02. Run 2: Q-01. Both found: Put-after-Release semantics gap,
concurrent Release/Get race, factory failure handling. Run 2
additionally found 28 UV-derived holes (the full checklist per event).
No contradictory findings — divergence is purely additive (Run 2 has
more UV coverage).

## Notes

- This is the first CONVERGENCE baseline on a real (non-synthetic)
  component and the first ODC data point through the automated
  gen_odc_table pipeline.
- The 100% aligned-cell convergence reflects that both runs used
  aggressive state normalization. In practice, the structural
  divergence in state granularity (Initializing vs not) and event
  naming (PutNil, Len) is the real signal.
- Tool-verified: 2026-08-07, pack v1.44.

## Canonical merge reconciliation (verified)

The canonical `analysis.json` (4 states, 7 events, 3 questions) is a
reduction of 7+12 run questions. Verified line-by-line against
`convergence/run1.json`, `convergence/run2.json`, and `analysis.json`.

### Run 1 questions (7) → canonical

| Run1 Q | Disposition | Details |
|---|---|---|
| Q-01 (Initializing modeling) | dropped | Initializing is constructor-only; pool ref not returned to caller until NewChannelPool completes. Canonical folds into Active states. |
| Q-02 (Release/connReqs goroutine leak) | carried-as Q-01 | |
| Q-03 (internal Release on factory failure) | merged-into Q-05 | FactoryFail in init calls Release() internally; same fault: connReqs not closed. |
| Q-04 (waiter-path Get skips ping) | LOST | AtCapacity×Get = defer (queued), does not capture internal ping-skip. channel.go:142-147. |
| Q-05 (Put after Release leaks) | carried-as Q-03 | |
| Q-06 (openingConns negative) | LOST | Close = handle does not capture counter-underflow. |
| Q-07 (Len semantics) | dropped | Len removed: informational, no lifecycle transitions. |

### Run 2 questions (12) → canonical

| Run2 Q | Disposition | Details |
|---|---|---|
| Q-01 (Release/connReqs leak) | carried-as Q-01 | |
| Q-02 (caller crash without Put/Close) | LOST | No openingConns-leak model. |
| Q-03 (Put duplication) | LOST | No duplicate-detection. |
| Q-04 (Put after Release, out-of-order) | merged-into Q-03 | Released×Put = UNSPECIFIED → Q-03. |
| Q-05 (Put + Release race) | LOST | Concurrency race not explicitly modeled. |
| Q-06 (spurious/foreign Put) | LOST | No connection identity validation. |
| Q-07 (Double Close) | LOST | No double-close model. |
| Q-08 (Close after Release) | resolved-by-cell | Released×Close = ignore (documented). channel.go:202: c.close==nil → return nil. |
| Q-09 (Close + Get race) | LOST | |
| Q-10 (spurious/foreign Close) | LOST | |
| Q-11 (Release + Get/Put race) | LOST | |
| Q-12 (spontaneous Release) | LOST | |

**Summary:** 3 carried/merged, 1 resolved-by-cell (citation confirmed),
2 dropped with rationale, 13 LOST in merge.

### Removed events

| Event | Disposition | Justification |
|---|---|---|
| CloseNil | removed | Folded into Close upstream_guard annotation. channel.go:198 nil check is a fast-reject, not a lifecycle event. |
| Len | removed | Informational only (channel len), no lifecycle transitions. |
| PutNil | removed | Folded into Put upstream_guard annotation. channel.go:183 nil check is a fast-reject, not a lifecycle event. |
