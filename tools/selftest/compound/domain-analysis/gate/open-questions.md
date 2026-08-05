# Open Questions — gate (selftest fixture)

Q-01
Question: A finish arriving in closed does nothing by fall-through. Intended?
Current behaviour: no branch handles it (observed-in-code, gate.ts:28)
Options: ignore with diagnostic | reject | handle as late completion
Proposed: reject — a closed gate has no in-flight work
**Status:** OPEN — human decision required

Q-02
Question: What does a duplicated arrive resolve to while open?
Current behaviour: undetermined (no dedup key observed)
Options: idempotent no-op | reject as duplicate | treat as a second arrival
Proposed: idempotent no-op
**Status:** OPEN — human decision required
