# channelPool — Disposition matrix (as-is, Step 4)

<!-- states: Open_Idle, Open_IdleFull, Open_Empty_BelowCap, Open_Empty_AtCap, Open_Waiting, Open_Waiting_BelowCap, Open_Waiting_IdleStranded, Open_Creating, Released -->

Abstraction: completeness is relative to (1) the leaf states below, defined by the pool's bookkeeping — i = idle count, M = MaxIdle, o = openingConns (the pool's live count), X = MaxCap, w = waiting Gets, "Creating" = a Get holds the mutex while Factory runs — and (2) one event delivered at a time to completion (PA-8), with the mutex as the only serialization point. Concurrency is modelled by the Open_Creating state (the mutex is held across an external call) and by the interaction pairs; the transient window between a Get's empty `select` and its `Lock` is not a state but the race of pair P-01b. Guard predicates over (i, M, o, X, w, released, idle age, Ping result) are in guard groups G-01..G-09 (`check_guards.py`, `guard-results.txt`). Callback results are internal delivered-result events: a Factory result can only exist in Open_Creating, because Factory is called synchronously there; other rows record that with `ignore (documented)` and the single call site. A panic (nil-function call) has no vocabulary value; such cells say `handle` with the panic stated and a question.

State definitions (PA-17; condition-named):

| Leaf | Condition |
|---|---|
| Open_Idle | pool open, 1 ≤ i < M, no waiting Get |
| Open_IdleFull | pool open, i = M ≥ 1, no waiting Get |
| Open_Empty_BelowCap | pool open, i = 0, o < X, no waiting Get |
| Open_Empty_AtCap | pool open, i = 0, o ≥ X, no waiting Get |
| Open_Waiting | pool open, i = 0, o ≥ X, w ≥ 1 |
| Open_Waiting_BelowCap | pool open, i = 0, o < X, w ≥ 1 (waiters stranded although capacity is free) |
| Open_Waiting_IdleStranded | pool open, i ≥ 1, w ≥ 1 (waiters stranded although an idle conn exists) |
| Open_Creating | a Get holds the mutex while Factory runs |
| Released | Release has run: idle store, Factory, Close callback and Ping cleared |

Provenance: every cell is `observed-in-code` at its cited line unless it says otherwise. "→ Q-nn" on a non-hole cell links the question the cell raises; on a hole cell it is the mandatory hole reference.

