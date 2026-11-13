# channelPool — Step 4 disposition matrix (as-is)

<!-- states: Open_IdleAvailable, Open_IdleFull, Open_Empty, Open_AtCapacity, Open_AtCapacity_Waiting, Open_Waiting_Stranded, Released -->

Abstraction: completeness is relative to the seven leaf states below (the reachable combinations of idle count, open-connection count against MaxCap, waiter queue, and released flag; `Open` is a grouping with no own row) and to the 22 catalogue events. Exact counter values are abstracted into the guard predicates G-01 … G-09 (`check_guards.py`); a cell whose target depends on a counter names its state-changing branch as `transition → <target>` and lists the staying branch and any other target in the same cell (guard noted). One event is processed at a time (PA-8); interleavings inside one event (the Get/Put race, the Release window) are modelled as the state `Open_Waiting_Stranded`, the variant `UV-GET-STALE`, and the pairs in `adversarial-traces.md`.

Provenance: every disposition is observed-in-code at the cited line unless marked inferred. Hole cells carry `→ Q-nn`; other cells name related questions after `→`.

`Released` is terminal (PA-18: no event leaves it) and is declared after the matrix; its row stays explicit because its events are not uniformly ignored (Get is rejected, Put/Close are accidental ignores).

## Matrix
