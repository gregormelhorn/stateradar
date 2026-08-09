# Fault-Class Layer Separation and Observability Design

**Date:** 2026-08-09
**Scope:** Assign every fault class to exactly one mutation level, rate its
seam-observability, and define the pre-run BLOCKED precondition. This gates
all further operator work and the kill-rate report.

## Goal

Stop the fixture-per-class grind before it produces 22 selftest lines with
no consumer applicability. Each fault class gets one owner level — matrix or
implementation — chosen by whether an instance of the class is fully
expressible as a disposition change. Classes whose interesting faults live
below the matrix belong to the implementation level exclusively; everything
else at that level is double maintenance.

## The layer table

**Normative home:** `formats/rules.toml`. The pack built the registry and
`gen_rules` so that per-class assignments never live as parallel prose.
Each fault entry gains:

- `level` — closed vocabulary: `matrix | implementation | none`
- `observability` — closed vocabulary: `high | medium | low | n/a`;
  required on every entry; `n/a` exactly when `level` is `matrix` or
  `none`. Absence is never acceptable: a missing field is
  indistinguishable from a forgotten one.
- `precondition` — required for every implementation-level class. For
  HIGH classes it names the projection the suite must provide; for MEDIUM
  and LOW it also names the missing seam investment.
- `none_reason` — required iff `level = "none"`

`gen_rules` validates the vocabularies, the `n/a`-iff constraint, the
`precondition` requirement on implementation classes, and the `none_reason`
requirement, with red selftest cases proving each rule fails on its own
bad input.
The detector constraint (one `detects` reference per class, zero-warning
budget) is unaffected: all four `none` classes already have detectors
outside the mutation layer — F-06 by matrix totality (PA-14), F-10 by the
multi-instance lints, F-19 by doctrine mapping, F-21 by the test audit.
`none` means "no mutation operator", not "no detector".

The table below renders the registry view; the registry entries are the
normative form.

| Class | Level | Basis |
|---|---|---|
| F-01 missing transition | **matrix** | Fully expressible: `transition → ignore`. Family exists in `check_matrix_mutation`. |
| F-02 transfer fault | **matrix** | Fully expressible: target swap. Family exists. |
| F-03 output fault | **implementation** | Transition still fires; the effect is wrong. Cell unchanged. |
| F-04 sneak path | **matrix** | Fully expressible: `ignore/reject → handle`. Needs the reverse family in `check_matrix_mutation`. The existing implementation variant stays as the mirroring-vs-behavioral demonstration — evidence for why suite architecture matters. It is not an operator and counts toward no class rate. |
| F-05 corrupt state | **implementation** | Context variable corrupted below a correct `handle` cell. |
| F-06 trap door | **not a mutant** | Undocumented entry/exit paths are found by matrix totality (PA-14 round-tripping), not by code mutation. A trap-door mutant's path lies outside the cell suite's coverage universe by definition; implementation mutation would produce structural SURVIVED noise. |
| F-07 lifecycle coupling | **implementation** | Cross-lifecycle cleanup. Needs a multi-track suite; single-track behavioral suites cannot observe it. |
| F-08 double release | **implementation** | Second release must be a no-op; cell unchanged, realization wrong. |
| F-09 cancellation leak | **implementation** | Post-cancel resource survives without synchronization. |
| F-10 synchronized reset herd | **not a mutant** | Multi-instance aggregate. Needs an aggregate harness, not a per-component mutation. |
| F-11 callback deadlock | **implementation** | Re-entry under lock. Observable as a hang via suite timeout. |
| F-12 loss / omission | **matrix** | UV-loss disposition change is fully cell-expressible. |
| F-13 delay / late | **implementation** | Timeout removed or shortened. Clock doctrine exists (v1.24); clock injection in the seam is the missing piece. |
| F-14 duplication | **implementation** | Idempotency realization below a correct `handle` disposition (double increment, missing dedup). |
| F-15 out-of-order / stale | **matrix** | UV arrival disposition change is fully cell-expressible. |
| F-16 contradictory input | **matrix** | Same. |
| F-17 spontaneous commission | **matrix** | Same. |
| F-18 subtle value fault | **implementation** | Payload effects below a correct disposition. |
| F-19 unimplemented requirement | **not a mutant** | Doctrine-mapping finding, not a mutation operator. |
| F-20 blocked progress after terminal | **matrix** | Terminal cells: `ignore/reject → handle`. Same reverse family as F-04. |
| F-21 mirroring test | **not a mutant** | Suite property, not a component fault. |
| F-22 control stopped too soon / too long | **implementation** | Control timing. Same clock seam as F-13. |

Reverse-family note: F-04, F-12, F-15, F-16, F-17, F-20 all need one new
family in `check_matrix_mutation` — `ignore/reject → handle`. That addition
is part of the operator work, not of this spec.

## Seam-observability rating

A mutant is useful only if "the observable disposition of a decided cell
changed" is mechanically answerable. Rating per implementation-level class:

| Class | Rating | Precondition |
|---|---|---|
| F-05 | HIGH | Counter/variable projected by the suite (proven: `dup_count`). |
| F-08 | HIGH | Release count or released-state projected. |
| F-14 | HIGH | Idempotence observable via repeated delivery + counter. |
| F-03 | HIGH | Emitted effects projected by the seam. |
| F-09 | MEDIUM | Seam must support cancel plus a post-cancel resource probe. |
| F-11 | MEDIUM | Suite timeout must catch the hang deterministically. |
| F-18 | MEDIUM | Payload-effect projection required. |
| F-07 | LOW | Multi-track suite required. Deferred. |
| F-13 | MEDIUM | Clock doctrine exists (delay + absolute due-offset, v1.24); the missing piece is clock injection in the seam, not the method. Pulled forward: first seam investment after the F-08 wave. |
| F-22 | MEDIUM | Same clock seam as F-13; unblocked when it lands. |

Prioritization follows observability, not catalogue order: F-05 (done),
F-08, F-14, F-03, F-09, F-11, F-18, then F-13 once the clock seam exists
(F-22 unblocks with it). F-07 alone remains deferred — one named domain
gap, not three.

## The BLOCKED precondition

`SURVIVED` must never be ambiguous between "suite weak" and "mutant not
observable". The checker fills `BLOCKED` **before** the run, from three
pre-flight facts:

1. **Cell existence (matrix level):** a cell for this class exists to
   mutate. A component with an asserted-absence instead of a UV column has
   nothing to mutate for F-12/F-15/F-16/F-17 — `BLOCKED`, never skipped.
2. **Reachability (implementation level):** the mutated region is on a
   path the suite can drive through the declared seam.
3. **Projection, proven by canary (implementation level):** the suite
   declares what it projects (state, counters, effects, release counts),
   and each projection type carries a **canary mutant** that must be
   KILLED at pre-flight. A canary that survives refutes the projection
   claim, and every mutant requiring that projection is `BLOCKED:
   <mutant-id> projection <name> unproven (canary survived)` — never run,
   never SURVIVED. The F-05 variant is the counter-projection canary in
   golden-mini today; the mechanism generalizes it to one designated
   canary per projection type per component.

   **Residual uncertainty, stated openly:** a canary proves the suite
   projects a variable *in the exercised path*. A component with multiple
   seams could project a counter on one seam and not another, and the
   canary would not see it. v1 accepts this granularity and records it;
   per-seam canaries become required the first time a component declares
   more than one seam.

Self-declared projections are not accepted as proof: an unverified
`requires` list would recreate the hollow-backfill failure shape
(synthetic claim on one side, green gate, empty statement). The canary is
the projection's red probe.

## Two measures, two names

The matrix level and the implementation level measure different things,
and they are never averaged into one number:

- **Bindungstreue (matrix level):** a **boolean conformance finding**, not
  a rate. *Suite is spec-reading: yes/no*, with surviving matrix mutants
  as the evidence. It answers whether the cell tests track their cells'
  dispositions or run vacuously green. Because the value has exactly two
  states, it is an acceptance gate: run once at testgen completion, and
  re-run when the suite itself changes — not a per-build CI number that
  consumers pay for while nothing can change it.
- **Fehlererkennung (implementation level):** `killed / (killed +
  survived)` per class per component from `check_fault_mutants`. **The
  rate is never reported without its blocked share.** A kill-rate over a
  hidden denominator reads well and means nothing: `F-05: 1/1 killed, 0
  blocked` and `F-13: — (4/4 blocked, no rate)` are the only permitted
  forms. This follows the same principle as the zero-denominator
  handling in `ensemble_convergence`, which reports n/a instead of a
  rate.

## Kill-rate definition of done

Per fault class, the definition of done is **operator + two components +
Fehlererkennung in the report** — never "class checked off":

- **Operator:** a named transformation over model + binding, registered per
  class, formulated so it is citable verbatim as a generator-prompt
  constraint. The binding layer builds on matrix citations
  (`file:line` per cell), which already bind cells to code regions.
- **Two components, at least one real:** golden-mini stays the contract
  fixture only. At least one component must be a wired benchmark with a
  real behavioral suite — otherwise the differentiating number is
  collected on toys and repeats the 105/105 convergence pattern. The
  primary candidate is grpc-go `addrConn` (richest existing analysis,
  real lifecycle code). silenceper/pool is available only if its standing
  Resolution-only exclusion is lifted explicitly; building a suite for it
  without that decision is out of scope.

  **On the expected objection:** grpc-go-2669 is a regression anchor under
  the dating protocol, and a reviewer may call it contaminated. That
  objection misfires here: contamination guards *discovery* claims (did
  the agent know the bug before analysis?). Suite-strength measurement
  makes no discovery claim — the suite is either strong enough to kill a
  class or it is not, regardless of when the issue was published.
- **Fehlererkennung:** reported per class per component, always paired
  with the blocked share. Bindungstreue is reported beside it as a
  boolean, never folded in.

## Non-goals

- No mutant generation. Operators are defined, not yet generated.
- No changes to existing golden-mini variants; they stay as fixture proofs.
- No reverse-family addition to `check_matrix_mutation` in this spec.
- No F-10, F-19, or F-21 operators.
- No device-connection suite and no new benchmark suite in this spec;
  the addrConn suite is the named next artifact.

## Verification

This spec ships with the registry migration: `rules.toml` gains the four
fields on all 22 fault entries in one atomic change, `gen_rules` validates
the closed vocabularies and the `none_reason` requirement, and a red
selftest proves a `none` class without a reason and a bad `level` value
each fail. The migration is mechanical but has blast radius — `gen_rules`
renders into `00-methods-reference`, `02-pilot`, AGENTS §5, and the README
finds list — so the acceptance bar is: `gen_rules --check` and
`--selftest` green, all 22 entries migrated atomically, and the
zero-warning budget unchanged.

## Completion boundary

A committed spec **plus the registry migration** as its mechanical first
step. After that: behavioral suite on grpc-go `addrConn`, then F-08
(double release) end-to-end on it, and the operator format written *from*
that application. The format spec follows contact, not the reverse.
