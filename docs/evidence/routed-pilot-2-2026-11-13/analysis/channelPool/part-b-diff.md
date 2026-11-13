# channelPool — Part B diff (blind pass vs disposition matrix)

## Dispatch record

* Route: `tools/local_models.py blind` (DeepSeek Flash, one fresh request), ledger of this pilot. `--package-only` first; the package (`routing/part-b-blind.package.md` in the evidence bundle, 27,267 bytes) was read in full before the real run; the real run sent it unchanged (the tool refuses a changed package).
* Inputs: `event-catalogue.md` (stripped by the tool), requirements README.md and README_ZH_CN.md (whole files), contracts `part-b-contracts.md` (verbatim Go doc comments and exported declarations of channel.go and pool.go, each headed by its `file:line`, no added text). No source file, no matrix, no traces, no questions.
* Package inspection: no implementation code. Present and accepted: the README usage example (documentation) and the exported declarations in the contracts file (`Config`, `Pool`, the two error variables — API schema, no function bodies). Doctrine lines arrive with their prose quotes from README.md / README_ZH_CN.md; quotes cited from channel.go and pool.go are stripped by the tool (a `.go` file is not a prose source).
* Id lists on stderr: the tool printed neither a "kept" nor a "removed" list — the catalogue and doctrine lines contain no L-, G-, F- or T- ids. No kept id to justify; no removed domain term.
* Result: `finish_reason=stop`, 7,440 input / 3,380 output tokens, 6,288 µ$. Coverage check: `PART-B COVERAGE: OK (22 events, 18 pair orderings)`. Pair count confirmed against the pairs table: 9 pairs × 2 = 18 rows P-01a … P-09b, each present once.

## Known leaks (rule 7) — Part B's agreement on these rows is not independent

The catalogue prose states as-is conclusions. Listed, not rephrased:

1. Events table, I-IDLE-EXPIRE: "no producer (no timer); evaluated when Get receives the connection" (lazy expiry).
2. Gate-type, E-CLOSE: "The connection's identity is never checked: the pool does not record which connections it handed out."
3. Gate-type, E-LEN: "returns the number of idle connections (0 after Release)".
4. Gate-type, I-IDLE-EXPIRE: "only examined when a Get receives that connection".
5. Remembrance: "any non-nil value is accepted"; "An idle connection that ages past `IdleTimeout` is not removed until a Get receives it or Release drains it"; "Each blocked Get is one entry in a FIFO queue, with no bound and no expiry. An entry leaves the queue only when a Put hands it a connection"; "it keeps the open-connection count and the waiter queue untouched"; "a late `Put` or `Close` resolves to a nil return without calling any close function".
6. Upstream-guard: "no wait bound, no cancellation"; "Absent here: ownership check, duplicate check"; "Absent here: coordination with in-flight Gets or with connections still held by callers"; "`MaxCap == 0` and `IdleTimeout <= 0` are accepted".
7. Lock-discipline: "A `Factory` or `Close` callback that calls … of the same pool waits for the mutex held by its own call chain" (the re-entry deadlock).
8. Undesired-coverage n/a reasons: "the idle timestamp is taken at the Put itself"; Ping "not under the mutex".
9. Pairs table wording: P-02a "Put runs before the Get queues itself, then the Get queues" and P-04a "checked that Ping is set" describe the interleavings (not their outcomes).

Residual line numbers (tool defect, not code): the stripped lock-discipline table still shows "unlock at 136, 151, 156 or 160" and "194" — bare numbers that followed a `file:line` citation survive `part_b_pack.py`'s citation stripper. They carry no code; recorded, the inputs were not edited before the run.

## Row classification

| Row | Blind disposition (abridged) | Matrix | Class | Action |
|---|---|---|---|---|
| E-GET | idle: handle (discard expired at age ≥ IdleTimeout, discard on Ping failure); below cap: handle via Factory; at capacity: `defer (queued)`; Released: reject ErrClosed | Open_IdleAvailable: transition → Open_Empty on the last idle connection, otherwise stays; Open_Empty: transition → Open_AtCapacity on the MaxCap-th creation, otherwise stays; Open_AtCapacity: transition → Open_AtCapacity_Waiting; Released: reject | divergence | expiry boundary: Part B discards at age = IdleTimeout, the code keeps it (strict `Before`, G-02 probe) → new **Q-25**. Mapping stated: Part B's `defer (queued)` for the waiting Get and Part A's transition into `Open_AtCapacity_Waiting` describe the same FIFO wait (Part A models the queue as state) |
| E-PUT | waiter: handoff; idle below MaxIdle: enqueue; idle full: close; nil: "handle — nil/error return"; Released: `ignore (documented)` | same Open dispositions; nil → reject (G-06); Released: `ignore (accidental)` | artefact | Released: Part B read the remembrance line (leak 5) as documented intent. Repaired: remembrance and upstream lines now carry the provenance "observed in code" (rule 7, provenance only). The hole stays Q-06. Nil payload: Part B wrote `handle` for an error return where the vocabulary says `reject`; behaviour identical |
| E-CLOSE | Open: decrement + callback; Released: `ignore (documented)` | Open: handle; Released: `ignore (accidental)` | artefact | same repair as E-PUT; hole stays Q-06 |
| E-RELEASE | Open: transition → Released, waiter queue untouched; Released: ignore (documented) | same | convergent | leak-dependent (leak 5, 6) |
| E-LEN | idle count; 0 after Release | same | convergent | leak-dependent (leak 3) |
| I-IDLE-EXPIRE | received by Get and expired: close and discard; idle with no Get: `ignore (documented)` (lazy); Released: `ignore (accidental)` | Open idle states: `ignore (accidental)` → Q-13; Released: `ignore (documented)` | divergence | lazy expiry read as documented (leak 1, 4) → reasoned fold into Q-13 (that is the question). Released: Part B thinks idle connections are "dropped, never evaluated"; Release closes them (channel.go:241) — no gap. Boundary → Q-25 |
| UV-GET-DELAY | UNSPECIFIED (no deadline, requirement silent); released waiter UNSPECIFIED | `ignore (accidental)` → Q-02 / Q-01 | convergent-hole | noted on Q-02 and Q-01 |
| UV-GET-STALE | handle — the stale Get completes with the connection it already took; not rejected | UNSPECIFIED → Q-07 (several timing-dependent outcomes incl. waiting forever and a nil-function panic) | divergence | reasoned fold into Q-07: Part B proposes "run to completion" as the expected outcome; it does not see the other outcomes. Added as Part B's position on Q-07 |
| UV-PUT-LOSS | `ignore (documented)` — never reclaimed; Released: "n/a (no Put arrives)" | `ignore (accidental)` → Q-12; Released → Q-06 | artefact | upstream line "the pool trusts the caller …" read as a contract; repaired with provenance "observed in code". **vocabulary-drift**: "n/a" is outside the vocabulary; it maps unambiguously to "nothing happens" (an ignore); documented vs accidental is the open point of Q-06 |
| UV-PUT-DUP | handle twice, same value idled twice / handed to a waiter | handle → Q-11 | convergent | leak-dependent (leak 2, 6) |
| UV-PUT-FOREIGN | handle (accepted); Released ignore (documented) | handle → Q-10; Released accidental → Q-06 | convergent | Open rows agree (leak-dependent); Released sub-cell is the E-PUT artefact |
| UV-PUT-BROKEN | handle; detected later by Ping at next Get | handle; on the waiter path no Ping → Q-14 | pass-B-blind-spot | Part A saw the handoff path skipping Ping (Q-14); Part B assumes Ping always runs on Get |
| UV-PUT-CLOSE-SAME | both accepted independently, closed connection may circulate | handle → Q-10 | convergent | leak-dependent |
| UV-CLOSE-DUP | decrement twice, count skewed | handle / transition → Q-10 | convergent | leak-dependent |
| UV-CLOSE-FOREIGN | decrement + callback, no ownership check | handle / transition → Q-10 | convergent | leak-dependent |
| UV-CLOSE-IDLE | decrement + callback, idle entry stays, later Get may hand out a closed connection | handle → Q-10 | convergent | leak-dependent |
| UV-FACTORY-ERR | reject — error to caller, count unchanged | reject | convergent | — |
| UV-FACTORY-SLOW | UNSPECIFIED; "Mutex released before Factory (per lock annotation), so other Gets/Puts not blocked" | handle — Factory runs under mu, every other operation blocks → Q-09 | artefact | Part B misread the lock-discipline table: with the factory call's line number stripped and bare unlock numbers left, the row does not say the order. Repaired: the lock-discipline section now states, with provenance "observed in code", that Factory runs while the mutex is held and that the Close callback runs before the deferred unlock; lock sites are written as full citations so the stripper removes them |
| UV-FACTORY-NILCONN | UNSPECIFIED (requirement silent; assumed handle-as-returned) | handle → Q-19 | convergent-hole | noted on Q-19 |
| UV-CLOSEFN-ERR | handle — error returned, decrement persists; Released ignore (documented) | handle → Q-18; Released ignore (documented) | convergent | — |
| UV-CLOSEFN-SLOW | UNSPECIFIED; "mutex released before callback (per lock annotation) so pool not wedged" | handle — callback under mu → Q-09 | artefact | same repair as UV-FACTORY-SLOW |
| UV-CB-REENTER | UNSPECIFIED / deadlock risk; Ping re-entry tolerated | handle (deadlock) → Q-09 | convergent-hole | leak-dependent (leak 7); noted on Q-09 |
| P-01a | waiter stays queued indefinitely: UNSPECIFIED | Q-01 | convergent-hole | leak-dependent (leak 5); noted on Q-01 |
| P-01b | reject ErrClosed | reject | convergent | — |
| P-02a | Put idles the connection, then the Get is served from idle | the Get queues itself while the connection sits idle → Q-05 | divergence | reasoned fold into Q-05: Part B's expectation is the option "re-check the idle store before queueing". Independent: the catalogue describes the interleaving, not its outcome |
| P-02b | Put idles, Get takes it | same | convergent | — |
| P-03a | waiter remains blocked: UNSPECIFIED | Q-04 | convergent-hole | leak-dependent (leak 5); noted on Q-04 |
| P-03b | Factory below cap or queue at cap | same | convergent | — |
| P-04a | Get completes with the connection; Release drops the idle channel | data race on the ping field, possible nil-function panic → Q-08; connection handed out during Release → Q-07 | pass-B-blind-spot | Part A saw the unlocked read; Part B could not |
| P-04b | reject ErrClosed, no Ping | same | convergent | — |
| P-05a | Release proceeds while Factory runs; Get then returns the connection; later Put/Close silently ignored | Release waits for the mutex until Factory returns; then the same end state → Q-07, Q-06, Q-09 | artefact | end state convergent; the order (Release not blocked) comes from the same lock-table misreading as UV-FACTORY-SLOW; same repair |
| P-05b | reject ErrClosed, Factory never invoked | same | convergent | — |
| P-06a | Put idles, Release drains and closes it | same (control verdict voided by scope, folded into Q-06) | convergent | — |
| P-06b | `ignore (documented)` — connection leaked | `ignore (accidental)` → Q-06 | artefact | same repair as E-PUT (leak 5) |
| P-07a | Close then Release drains | same | convergent | — |
| P-07b | `ignore (documented)` | `ignore (accidental)` → Q-06 | artefact | same repair as E-PUT |
| P-08a | both handled, double accounting | handle → Q-10 | convergent | leak-dependent |
| P-08b | Close then Put idles a closed connection | handle → Q-10 | convergent | leak-dependent |
| P-09a | expired connection discarded at Get, Get retries | same (control verdict voided, Q-13) | convergent | — |
| P-09b | connection served; Part B labels the expiry `ignore (accidental)` | served; age restarts on the next Put (control) | convergent | behaviour identical; Part B's `ignore (accidental)` label for "not expired yet" is a vocabulary misapplication, not a different expectation |

Class counts (40 rows): convergent 21, convergent-hole 5, divergence 4, artefact 8, pass-B-blind-spot 2. Leak-dependent convergent or convergent-hole rows: 13.

## Closure of divergences

* E-GET (expiry boundary) → new Q-25.
* I-IDLE-EXPIRE → folded into Q-13 (documented-vs-accidental lazy expiry), boundary into Q-25.
* UV-GET-STALE → folded into Q-07 (Part B's "run to completion" recorded as an option).
* P-02a → folded into Q-05 (Part B's expectation = "re-check before queueing").

Note: after this diff, `check_reachability.py` led to guarded matrix cells naming their state-changing branch (`transition → …` instead of `handle`; see `summary.md`). The behaviour in every compared row is unchanged; the comparison above uses the current wording.

## Artefact repairs made to `event-catalogue.md` after this diff

1. Remembrance semantics and upstream-guard lines carry the provenance "observed in code (not a requirement)". Nothing restated as intent, hole or question.
2. Lock-discipline: two provenance-only sentences state that the `Factory` callback runs while the mutex is held and that the `Close` callback runs before the deferred unlock; the lock-site column uses full `file:line` citations so the Part-B stripper removes them (no bare line numbers).

Recurring divergence class (for the feedback loop): **as-is remembrance and upstream statements read as documented intent** (8 artefact rows) — the same leak mechanism the v1.17 changelog names; candidate rule: prefix every remembrance and upstream statement with its provenance label.
