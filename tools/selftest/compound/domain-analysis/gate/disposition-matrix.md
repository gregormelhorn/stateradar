# Disposition Matrix — gate (selftest fixture)

Exercises the generator paths that had no test: a **multi-table** matrix
(wide event set split across sub-tables with their own headers), **compound
row labels** (`**fam** leaf`), transition targets that resolve only against
the full state list, and `→ Q-nn` back-references on both hole classes.

<!-- states: open idle, open busy, closed -->
<!-- event-ids: E1, E2, UV-E1, E3 -->

Abstraction: leaf states of the as-is model; substates inherit compound
dispositions unless the cell overrides them.

| state | E1 `arrive` | E2 `finish` |
| --- | --- | --- |
| **open** idle | transition → `busy` (observed-in-code, gate.ts:12 ("this.phase = 'busy'")) | ignore (documented) — nothing in flight (DR-001) |
| **open** busy | defer (queued) — one at a time (DR-001) | transition → `idle` (observed-in-code, gate.ts:20 ("this.phase = 'idle'")) |
| **closed** | reject (observed-in-code, gate.ts:28 ("throw new ClosedError")) | ignore (accidental) → Q-01 |

| state | UV-E1 `duplicate` | E3 `shutdown` |
| --- | --- | --- |
| **open** idle | UNSPECIFIED → Q-02 | transition → `closed` (observed-in-code, gate.ts:28 ("throw new ClosedError")) |
| **open** busy | UNSPECIFIED → Q-02 | transition → `closed` (observed-in-code, gate.ts:28 ("throw new ClosedError")) |
| **closed** | ignore (documented) — terminal (DR-001) | ignore (documented) — terminal (DR-001) |
