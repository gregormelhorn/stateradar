# Resolved evaluation questions

All 13 owner decisions are retained with their original attribution. No deferred or OPEN question remains. This register applies only to the evaluation copy.

## Q-01 — RESOLVED

Should a zero-weight acquisition progress after cancellation removes the preceding queue head?

Decision: [DR-001](decisions/DR-001.yaml): `permit-zero-with-fifo-progress`.

## Q-02 — RESOLVED

Reject an impossible oversized acquisition promptly

Decision: [DR-004](decisions/DR-004.yaml): `immediate-error`.

## Q-03 — RESOLVED

Reject negative arguments before mutation

Decision: [DR-002](decisions/DR-002.yaml): `panic-on-negative`.

## Q-04 — RESOLVED

Keep state unchanged after over-release panic

Decision: [DR-003](decisions/DR-003.yaml): `validate-before-subtraction`.

## Q-05 — RESOLVED

Who cleans up abandoned pending acquisitions, held weight and old instances?

Decision: [DR-005](decisions/DR-005.yaml): `explicit-cancellation-and-release`.

## Q-06 — RESOLVED

Is each repeated acquisition by the same logical caller independent?

Decision: [DR-006](decisions/DR-006.yaml): `independent-invocations`.

## Q-07 — RESOLVED

May release responsibility transfer between callers without ownership tracking?

Decision: [DR-007](decisions/DR-007.yaml): `transferable-anonymous-weight`.

## Q-08 — RESOLVED

Who selects the correct semaphore instance and Context?

Decision: [DR-008](decisions/DR-008.yaml): `caller-responsibility`.

## Q-09 — RESOLVED

What Context implementations does Acquire support?

Decision: [DR-009](decisions/DR-009.yaml): `conforming-context-precondition`.

## Q-10 — RESOLVED

Which cancellation checkpoints and accounting guarantees apply?

Decision: [DR-010](decisions/DR-010.yaml): `defined-checkpoints-and-net-accounting`.

## Q-11 — RESOLVED

Does nonblocking acquisition promise bounded mutex or cancellation latency?

Decision: [DR-011](decisions/DR-011.yaml): `no-capacity-queue-wait`.

## Q-12 — RESOLVED

Which FIFO order and queue limits are guaranteed?

Decision: [DR-012](decisions/DR-012.yaml): `fifo-grants-with-uncapped-queue`.

## Q-13 — RESOLVED

Is Release(0) a wakeup operation or a logical no-op?

Decision: [DR-013](decisions/DR-013.yaml): `logical-no-op`.
