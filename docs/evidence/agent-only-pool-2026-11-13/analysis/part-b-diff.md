# channelPool — Part-B diff (blind pass vs disposition matrix)

Model routing: OFF (agent-only run). Part B was dispatched to a fresh blind subagent (general-purpose agent, no shared context). It received only the package that `tools/part_b_pack.py --for-dispatch` produced: the stripped catalogue, the doctrine lines, README.md, README_ZH_CN.md, and a contracts file holding the doc comments of channel.go and pool.go copied verbatim. The pilot agent did not write or edit the blind table.

* Package: `part-b-dispatch-package.md` (31,554 bytes, sha256 de1ed12e…c254). The dispatch prompt is this file, inlined by the pilot agent.
* Blind output: `blind-output.md` (the subagent's report, saved verbatim).
* Package inspection (rule 7): no implementation code. The contracts file carries the declaration signatures of the documented functions (`func (c *channelPool) Get() (interface{}, error) {` etc.) next to their comments. Those are declarations, not bodies, and they were left in.
* Ids removed by the tool (stderr): F-12, F-13, F-14, F-15, F-16, F-17, F-18, G-01, G-03. These are fault-class and guard-group references of the analysis, not domain terms, so nothing was lost from the domain vocabulary. Ids kept: none reported.
* Cosmetic stripping debris: "guard group , branch discard", "that gap is itself a finding .", and "Its validation is guard group and its outcomes are the initial edges of `as-is.machine.mmd`". The last one names a Part-A artefact file, but none of its content.
* Coverage: `part_b_pack.py --check` → `PART-B COVERAGE: OK (27 events, 18 pair orderings)`. Pair-row count in the blind table: 18, which matches the pairs table (P-01..P-09 × a/b).

## Known leaks (as-is conclusions in the catalogue prose)

Agreement on the rows below is **not independent**: the catalogue told Part B the as-is fact.

| Leak in the catalogue | Affected rows |
|---|---|
| "Connection identity is not examined" (PUT gate), "Identity not examined" (CLOSE gate), and remembrance: "Close decrements the count again and calls the Close callback again" | UV-03, UV-04, UV-05, UV-06, UV-07, UV-08, P-05a, P-05b |
| PING gate: "calls the configured Ping without checking that one is configured"; remembrance: "a later Ping calls the cleared Ping reference" | PING (not configured, Closed), P-08a, P-08b |
| FACTORY_OK gate: "Whether the connection value is nil is not examined" | UV-14 |
| CLOSEFN_OK gate: error "discarded on Get's discard path and in Release" | UV-15, GET (discard error) |
| IDLE_TIMEOUT gate and coverage row: "no handler runs when the time passes", "nothing happens at expiry time" | IDLE_TIMEOUT, P-07a |
| Remembrance: the waiter list "not cleared, not signalled" at Release; "a later Put or Close resolves against the cleared Close callback" | RELEASE (waiters), PUT/CLOSE in Closed, P-03b |
| Upstream: "MaxCap = 0 is accepted" | GET (MaxCap = 0) |
| Lock discipline: re-entrant Factory or Close callback "blocks forever" | UV-17, UV-18 |
| Lock discipline: Factory runs inside the mutex-held section "Get, no idle connection" | UV-12 (Part B did **not** draw the pool-wide-block conclusion from it) |
| GET coverage: "waiting without bound is the GET disposition in the waiting rows" | GET at MaxCap, UV-02 |

## Vocabulary drift

| Blind row | Blind wording | Mapping |
|---|---|---|
| GET at MaxCap | `defer (queued) → Open_AtMaxCap_Waiting` | maps unambiguously to `transition → Open_Waiting` (the Get is parked in the waiter list); same behaviour as the matrix |
| PUT, no waiter | `handle → Open_IdleAvailable` | `transition → Open_Idle` (matrix: transition from the Empty rows, stays in Open_Idle) |
| UV-02 | `defer (queued) for the Gets, then handle` | the matrix's `ignore (accidental) → Q-02` for the waiting rows; the behaviour described (Gets stay queued, the late Put serves a waiter) is the same |
| P-03a | `handle, then transition → Closed` | two events; matches PUT then RELEASE |
| P-09a, P-09b | `transition → Closed, then UNSPECIFIED` | first RELEASE matches; the second is a hole → Q-20 |
| FACTORY_OK (Release during Factory) | `see P-06b` | a reference, not a disposition; classified under P-06b |
| UV-11 | `reject` | the matrix has `transition → Open_Empty_BelowCap` with the error returned to the caller. Part B uses `reject` for "error returned to the caller", and the behaviour is the same |

State-name mapping (PA-17): Open_IdleAvailable ≈ Open_Idle ∪ Open_IdleFull; Open_NoIdle_BelowMaxCap = Open_Empty_BelowCap; Open_NoIdle_AtMaxCap = Open_Empty_AtCap; Open_AtMaxCap_Waiting = Open_Waiting; Closed = Released. Part B has no counterpart for Open_Waiting_BelowCap, Open_Waiting_IdleStranded or Open_Creating. It does describe the first two as failure modes it should not reach (P-04b, P-01b).

## Row classification

| Blind row | Class | Note / Q |
|---|---|---|
| GET idle path (hand out) | convergent | |
| GET expired idle conn | convergent; Close-callback error on this path: convergent-hole | Q-17 (leak noted) |
| GET Ping-failed idle conn | convergent | |
| GET below MaxCap (create) | convergent | |
| GET at MaxCap (wait) | convergent-hole | Part B raises (a) error vs wait, (b) bound, (c) FIFO → Q-01, Q-02. FIFO is observed in code (append/pop-front), so no new Q |
| GET Closed | convergent | |
| GET MaxCap = 0 | convergent-hole | Q-01 (leak noted) |
| PUT waiter exists | convergent | |
| PUT no waiter, not full | convergent (vocabulary-drift) | |
| PUT idle full | convergent; callback error: convergent-hole | Q-17 |
| PUT Closed | convergent-hole | Q-06 |
| CLOSE open | **divergence** | Part B expects the freed capacity to serve waiters; the matrix has no wake-up (Open_Waiting x CLOSE → Open_Waiting_BelowCap). Folded into Q-03, which asks exactly this; Part B's proposal is recorded there |
| CLOSE Closed | convergent-hole | Q-06 |
| RELEASE open | convergent; (a) checked-out conns, (b) waiters, (c) count reset: convergent-hole | Q-06, Q-05; (c) the count is irrelevant once released (Factory cleared), so it is folded into Q-06 |
| RELEASE Closed | **divergence** | the matrix says `ignore (documented)`, citing only the code's explicit nil check (channel.go:234). Part B finds no requirement and marks the cell UNSPECIFIED. The matrix's "documented" rests on code intent, not on a requirement → new **Q-20** |
| LEN open | convergent-hole | Q-15 |
| LEN Closed | convergent | |
| PING configured | convergent | |
| PING not configured | convergent-hole | Q-11 (leak noted) |
| PING Closed | convergent-hole | Q-11 (leak noted) |
| FACTORY_OK | convergent | |
| FACTORY_OK during Release | see P-06b | |
| CLOSEFN_OK | convergent | |
| IDLE_TIMEOUT open | convergent-hole (lazy vs proactive; replenish to InitialCap) | Q-12, Q-14 (leak noted) |
| IDLE_TIMEOUT, IdleTimeout ≤ 0 | **divergence** (the matrix treats ≤ 0 as "disabled" from the code, guard G-03; no requirement says so) | folded into Q-12, which now also asks about the ≤ 0 meaning |
| IDLE_TIMEOUT Closed | convergent | |
| UV-01 | convergent-hole | Q-16 |
| UV-02 | convergent-hole (vocabulary-drift) | Q-02 |
| UV-03 | convergent-hole | Q-09 (leak noted) |
| UV-04 | convergent-hole | Q-09 (leak noted) |
| UV-05 | convergent-hole | Q-09 (leak noted) |
| UV-06 | convergent-hole | Q-09 (leak noted) |
| UV-07 | convergent-hole | Q-09 (leak noted) |
| UV-08 | convergent-hole | Q-09 (leak noted) |
| UV-09 | pass-B-blind-spot | the matrix has the observed `reject` with the "connection is nil. rejecting" error; Part B, without the code, proposes exactly that. No action |
| UV-10 | convergent; hand-off path: pass-B-blind-spot | Part B did not notice that a conn handed to a waiter skips Ping (Q-13) |
| UV-11 | convergent (vocabulary-drift) | Part B's "waiter woken by the freed slot" does not apply: a failed Factory call frees no slot (the count was never incremented). No action |
| UV-12 | convergent-hole | Part B asks whether other operations block and proposes that they should not; the matrix shows that they do → Q-08, Q-19 |
| UV-13 | convergent-hole | Q-07 |
| UV-14 | convergent-hole | Q-07 (leak noted) |
| UV-15 | convergent-hole | Q-17 (leak noted) |
| UV-16 | convergent-hole | Q-08 |
| UV-17 | convergent-hole | Q-08 (leak noted) |
| UV-18 | convergent-hole | Q-08 (leak noted) |
| P-01a | convergent | |
| P-01b | convergent-hole | Q-04 (independent: the catalogue states the ordering, not the outcome) |
| P-02a | convergent | Q-06 for the later Put |
| P-02b | convergent-hole | Q-05, Q-06, Q-10 |
| P-03a | convergent (vocabulary-drift) | |
| P-03b | convergent-hole | Q-06 (leak noted) |
| P-04a | convergent | |
| P-04b | convergent-hole | Q-03 (independent: Part B derived the lost wake-up from DOC-4 itself) |
| P-05a | convergent-hole | Q-09 |
| P-05b | convergent-hole | Q-09 |
| P-06a | convergent | |
| P-06b | convergent-hole | Q-06; Part B's "must Release wait for Factory?" is folded into Q-19 |
| P-07a | convergent | (leak noted) |
| P-07b | convergent-hole | the boundary: both passes read "exceeding" as strict, and Part B asks the owner to confirm → Q-12 |
| P-08a | convergent-hole | Q-10 (leak noted) |
| P-08b | convergent-hole | Q-10 (leak noted) |
| P-09a | convergent / divergence on the second Release | Q-20 |
| P-09b | convergent / divergence on the second Release | Q-20 |

Counts: the blind table has 62 rows (44 event rows, since several events have more than one situation row, plus 18 pair rows). Each row is counted by its first class: convergent 22, convergent-hole 33, divergence 5 (CLOSE open, RELEASE Closed, IDLE_TIMEOUT ≤ 0, P-09a, P-09b), pass-B-blind-spot 1 (UV-09), artefact 0, reference-only 1 (FACTORY_OK during Release → P-06b). Total 62. Secondary aspects inside a row (for example UV-10's hand-off blind spot, or the callback-error convergent-hole on GET expired and PUT idle full) are named in the note column and not counted twice.

Every divergence is closed: CLOSE open → folded into Q-03; RELEASE Closed, P-09a, P-09b → new Q-20; IDLE_TIMEOUT ≤ 0 → folded into Q-12.

## Recurring divergence classes (feedback loop)

The single findings stay findings. One class showed up: **code-intent `ignore (documented)`**. The matrix cited a deliberate code construct, not a requirement, as the documentation for an ignore (RELEASE in Released), and the blind pass, which works from requirements, could not reproduce it. This is the first occurrence in this run. It becomes a rule only if it recurs on a second component.
