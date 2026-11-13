# Part B diff — channelPool

Dispatch: `tools/local_models.py blind` (DeepSeek Flash `deepseek-flash`, fresh request,
no tools, no history). Inputs: `event-catalogue.md`, `requirements.md` (README.md
verbatim), `contracts.md` (20 doc-comment lines copied verbatim from pool.go and
channel.go, each headed by its `file:line`). Package: `blind-output.package.md`
(23 127 characters). Output: `blind-output.md`. finish_reason `stop`; 6 091 input /
2 334 output tokens; 4 629 µ$.

## Package inspection (rule 7)

* First `--package-only` build: no code blocks, but the catalogue's citations carried
  16 verbatim code-line fragments (for example `("ret, ok := <-req")`) and three
  references to pass-A questions and lints (`Finding → Q-12`, `(Q-07)`, `lint L-4/L-5`).
  I judged these implementation and analysis leakage, removed them from
  `event-catalogue.md` (file:line citations kept; the pre-strip copy is
  `event-catalogue.pre-strip.md` among the routing outputs), and rebuilt the package.
* Second package: the only code-like text is the README usage example (client code,
  part of the requirements). No implementation code. Sent unchanged.
* Contamination that remains by design: the catalogue's remembrance semantics and
  lock-discipline annotation (both mandatory, Step 3) state the as-is behaviour — for
  example that a waiter present at Release stays blocked. The blind pass therefore
  learns the as-is outcome of the primary finding from the catalogue. See "Assessment".

## Coverage verification

`PART-B COVERAGE: OK (22 events, 10 pair orderings)` (tool). My count: 32 rows = 22
catalogue events + 10 pair orderings; the pairs table has 5 pairs × 2 orderings = 10.
No missing or duplicate row.

## Vocabulary drift

Rows whose disposition cell is outside the closed vocabulary (compound or annotated
values), with the mapping I used:

| row | blind value | mapping |
|---|---|---|
| get | `handle` (may `transition → Error_Closed`-equivalent refusal …) | per-situation text maps unambiguously: Open idle → handle; at max → defer (queued); released → reject |
| ping | `handle` / `reject` on nil | Open → handle; nil → reject (UV-11 row); Released → UNSPECIFIED (stated in the text) |
| release | `transition → Released` / `ignore (documented)` on repeat | Open → transition → Released; repeat → ignore (documented) |
| UV-02 | `ignore (accidental)` / resource leak | ignore (accidental) |
| UV-12 | `UNSPECIFIED` / `defer (queued)`-side-effect | UNSPECIFIED (the defer describes the other callers, not the event) |
| P-01a | `UNSPECIFIED` (`transition → Released` mid-Get …) | UNSPECIFIED |
| P-04b | `reject` (panic) / `UNSPECIFIED` | ambiguous between reject and UNSPECIFIED; the text calls the outcome undefined → UNSPECIFIED; matches the matrix either way as a hole (Q-05) |

## Row classification

| row | blind | matrix (pass A) | class | action |
|---|---|---|---|---|
| get | handle / defer / reject; expects ErrMaxActiveConnReached "without wait capacity"; factory error → reject | handle / transition → Open_Waiting / defer / reject; ErrMaxActiveConnReached never produced; factory_error = handle | divergence (one sub-claim) | the ErrMaxActiveConnReached expectation folds into Q-09 (noted there). Factory error `reject` vs `handle`: same behaviour (error to caller, state unchanged), label only |
| put | handle; Released → ignore (documented) | handle; Released → ignore (accidental) → Q-04 | artefact | catalogue remembrance semantics read as intent; repaired (section now states that it is observed-in-code, not documented intent) |
| close_conn | handle; Released → ignore (documented) | handle; Released → ignore (accidental) → Q-04 | artefact | same repair |
| ping | handle; Released → UNSPECIFIED (panic) | handle; Released → UNSPECIFIED → Q-05 | convergent-hole | noted on Q-05 |
| release | transition → Released; waiters orphaned (`assumed-state: Released_WithOrphanWaiters`) | transition → Released / Released_WaitersStranded | convergent | — (B names the stranded state but does not flag it on this row; it does on P-01a) |
| len | handle | handle | convergent | — |
| idle_expired | handle, lazy | handle, lazy | convergent | — |
| ping_failed | handle; not evaluated on handoff path | handle; Open_Waiting × ping_failed = ignore (accidental) → Q-07 | convergent | B restates the handoff gap without flagging it (pass-B-blind-spot on the Q-07 aspect) |
| factory_error | handle (propagate); deadlock hazard | handle; Q-12 | convergent | — |
| handoff | handle, FIFO | handle | convergent | — |
| UV-01 | UNSPECIFIED (no bound) | defer (queued) → Q-09 | convergent-hole | noted on Q-09 |
| UV-02 | ignore (accidental) | ignore (accidental) → Q-10 | convergent-hole | — |
| UV-03 | handle, "should ideally be reject" | handle → Q-11 | convergent-hole | — |
| UV-04 | ignore (accidental) — contradiction not detected | handle (serialized) → Q-11 | convergent-hole | same behaviour (both applied); B labels the non-detection a hole; Q-11 covers it |
| UV-05 | handle, open point | handle → Q-11 | convergent-hole | — |
| UV-06 | reject | reject | convergent | — |
| UV-07 | handle, open point | handle → Q-11 | convergent-hole | B omits the counter undercount (pass A's T-F05) |
| UV-08 | handle; an idle connection closed stays in the idle set | handle → Q-11 | convergent-hole | new detail (closed connection left idle) folded into Q-11 |
| UV-09 | reject | reject | convergent | — |
| UV-10 | ignore (documented) | Released rows ignore (documented); Open rows transition (first caller) | convergent | — |
| UV-11 | reject | reject | convergent | — |
| UV-12 | UNSPECIFIED; pool stalls | handle → Q-12 | convergent-hole | — |
| P-01a | UNSPECIFIED; waiter blocks forever; factory case leaks the new connection | T-P01a → Q-01; variant 2 → Q-04/Q-06 | convergent-hole | strengthens Q-01 |
| P-01b | reject ErrClosed | reject | convergent | — |
| P-02a | handle | transition → Released after Put (T-P02a, verdict voided → Q-20) | convergent | — |
| P-02b | ignore (documented), leak | ignore (accidental) → Q-04 | artefact | same remembrance repair |
| P-03a | handle | control trace | convergent | — |
| P-03b | ignore (documented), leak | ignore (accidental) → Q-04 | artefact | same remembrance repair |
| P-04a | handle — "no interference, Ping holds no lock" | unsynchronized read of `c.ping` vs Release's write → Q-05 | pass-B-blind-spot | — |
| P-04b | UNSPECIFIED (panic) | UNSPECIFIED → Q-05 | convergent-hole | — |
| P-05a | handle | control trace | convergent | — |
| P-05b | handle, 0 | handle, 0 | convergent | — |

Counts: convergent 15, convergent-hole 11, divergence 1 (folded into Q-09), artefact 4,
pass-B-blind-spot 1. Total 32. No new question; two existing questions (Q-09, Q-11)
received the blind pass's additions. No divergence stays unclosed.

## Assessment

The blind pass agreed with pass A on every behaviour that the catalogue's
remembrance semantics describe, including the primary finding (P-01a: waiter blocked
forever). That agreement is not independent: the mandatory remembrance annotation
tells the blind reader the as-is outcome. The pass contributed one new detail
(UV-08) and one external expectation (ErrMaxActiveConnReached as a refusal, Q-09).
The four `artefact` rows are one divergence class: **remembrance semantics stated as
observed behaviour are read as documented intent** (`ignore (documented)` instead of
a hole). This is a single finding in this run; per the feedback-loop rule it goes into
the pilot changelog only if it recurs on a second component.
