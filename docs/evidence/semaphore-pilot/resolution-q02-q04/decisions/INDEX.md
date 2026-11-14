# Accepted decisions

DR-001 / Q-01 remains in ../.. / resolution-q01/decisions.

- DR-002: Q-03 — Reject negative arguments before mutation.
- DR-003: Q-04 — Keep state unchanged after over-release panic.
- DR-004: Q-02 — Reject an impossible oversized acquisition promptly.

- DR-005: Q-05 — Explicit cancellation and release; no automatic reclamation.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-006: Q-06 — Independent repeated acquisitions; self-blocking is possible.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-007: Q-07 — Transferable release responsibility; aggregate accounting only.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-008: Q-08 — Caller selects the instance and Context; no semantic-mismatch detection.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-009: Q-09 — Require a conforming non-nil Context; no automatic repair/recovery.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-010: Q-10 — Defined cancellation checkpoints and rollback of own holdings; transient reservations permitted.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-011: Q-11 — No capacity-queue wait for TryAcquire; mutex waits allowed, no fixed latency bound.
  Accepted during the continuing interview; contract/conformance follow-up pending.

- DR-012: Q-12 — FIFO grants without bypass; return order unspecified, no internal queue cap.
  Accepted during the continuing interview; contract/conformance follow-up pending.

Q-13 remains OPEN. This implements the explicitly selected next
numeric-contract changes; prior recommendations for the other questions are
not silently promoted to decisions. Q-13 has a post-fix investigation and revised proposal in q13-investigation;
its owner decision and conformance acceptance remain pending.
