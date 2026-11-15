# Flash-writes pilot: comparison against the pre-registered criteria

Written afterwards, outside the pilot session. The pilot ran 02-pilot v1.21
with the routing variant `flash-writes` on silenceper/pool `channelPool` @
6084537. The pack was fc677c6 and the Jev model `jev-1.14.0`.

**The steering agent ran on Claude Sonnet 5.5, not Opus 5.5.** Gregor asked
for the cheaper model. The comparator (the second routed pilot) and the
agent-only baseline both ran on Opus 5.5. A model change was not part of the
pre-registered design (docs/roadmap.md entry 11 item 2), so every cost
figure below is confounded by the model as well as by the pack changes since
a331dae/v1.17.

## Verdict

**Does not hold as registered.** Gate 4 is red, and the cost condition
passes only because of the model change.

| # | Condition (registered) | Result | Holds |
|---|---|---|---|
| 1 | steering-agent cost at most $9.60 | $5.72 on Sonnet prices. At Opus prices the same token counts cost $11.43 | yes on paper. The variant alone does not get there |
| 2 | primary finding raised and executed | Q-01 (Release never wakes waiters in `connReqs`), executed by `TestAsIs_Release_DoesNotWakeWaiter` | yes |
| 3 | at least 17 of 28 aligned base cells agree with the agent-only baseline | 19 / 28 (counting below) | yes |
| 4 | every gate green | `check_reachability.py` FAIL: `state 'Open_Waiting_IdleAvailable' is unreachable from initial state 'Open_IdleAvailable'` | **no** |

The run has 8 states, so it is matched to the comparator (6 to 8 states).

## Cost

The token counts come from the session transcript
(`f0edf73b-….jsonl` on the operator's machine). There were 74 assistant
messages: 72 `claude-sonnet-5-5` and 2 synthetic. One session ran with no
subagent.

| | flash-writes (Sonnet 5.5) | routed pilot 2 (Opus 5.5) |
|---|---|---|
| messages | 72 | 84 |
| input | 148 | 168 |
| cache write | 570,509 | 425,616 |
| cache read | 20,026,798 | 26,100,528 |
| output | 143,046 | 210,476 |
| cost at the run's prices | **$5.72** | $12.84 |
| cost at Opus prices | $11.43 | $12.84 |
| Flash + Jev (ledger) | $0.040 (20 calls) | $0.023 (20 calls) |
| wall clock | about 36 min | about 37 min |

Sonnet 5.5 prices per MTok: input $2, output $10, cache read $0.10, and
cache write $4 at the 1-hour TTL. With the 5-minute TTL the total is $4.86.
The TTL is not recorded per message, and the 1-hour figure matches how the
comparator was priced.

The variant cut output by 32 % and cache reads by 23 %, and it needed 12
fewer rounds. Cache writes rose by 34 %, because the drafted texts and
cells enter the context as tool output. At equal prices, that comes to about
11 % below the comparator ($1.41), not the registered quarter. The other
$5.71 of the $7.12 saving (about 80 %) comes from the cheaper model. The size of that 11 % is itself
unmeasured: the two Opus runs so far differed by $0.32, and there is still
no matched agent-only run on the same pack.

## Cells (condition 3)

The counting rule and baseline values are those of
`routed-pilot-2-2026-11-13/comparison.md`.

State alignment:

- Active_HasIdle ↔ Open_IdleAvailable ∪ Open_IdleFull.
- Active_IdleExhausted_UnderCap ↔ Open_NoIdle_BelowCap.
- Active_IdleExhausted_AtCapacity ↔ Open_NoIdle_AtCap ∪ Open_Waiting_AtCap.
- Released ↔ Closed.

Open_Waiting_BelowCap and Open_Waiting_IdleAvailable have no baseline
counterpart, like Open_Waiting_Stranded before, and are left out. This run
has no FactoryFail, IdleTimeout or PingFail column: all three are guard
branches of Get (G-01/G-02, Q-16, Q-19). They are compared against those
branches, as the comparator did for PingFail.

| baseline state | Get | Put | Close | Release | FactoryFail | IdleTimeout | PingFail |
|---|---|---|---|---|---|---|---|
| Active_HasIdle | = | = | = | = | ≠ (factory not reached with an idle connection; error returned) | ≠ lazy expiry questioned (Q-16) | = |
| Active_IdleExhausted_UnderCap | = | = | ≠ UNSPECIFIED vs handle | = | ≠ UNSPECIFIED vs error returned | = | = |
| Active_IdleExhausted_AtCapacity | = (queued waiter, Q-02 fold) | = | ≠ UNSPECIFIED vs transition (Q-03) | ≠ label, UNSPECIFIED vs transition → Q-01 | ≠ UNSPECIFIED vs factory not called | = | = |
| Released | = | ≠ label, UNSPECIFIED vs ignore (accidental) → Q-05 | ≠ ignore (documented) vs ignore (accidental) | = | = | = | = |

That gives **19 / 28 convergent**, the same count as both earlier runs under
this rule. The divergences fall in the same places: FactoryFail, Close,
Released × Close, and lazy idle expiry. The alignment and these judgments
are mine, made afterwards and not by the pilot agent, so treat the count as
±1.

## Gate 4: reachability

Open_Waiting_IdleAvailable can only be entered when a Put lands between Get's
first look and its lock (pair P-04a). No single transition cell names it as
a target, so `check_reachability.py` fails. The agent recorded this as a
known limit and did not edit cell targets to silence the check. The
comparator modelled its race-only state as the target of a Close cell (the
lost wake-up), and its gate stayed green. The pack has no rule for a state
that is reachable only through a pair ordering. That gap is a tool question,
not a defect of this run, but the registered condition is "every gate green".

## Flash drafting (what the variant measured)

- **Step 1:** 5 draft-verify calls produced 146 claims with 0 citation
  failures. Jev judged them 136 supported, 9 unclear and 1 contradicted.
  The agent added 9 items.
- **Cells:** Flash drafted 88 cells, with 0 problems and 0 missing. Jev
  judged them 78 supported, 9 unclear and 1 contradicted. The agent changed
  45 and kept 43:

  | Jev choice | unchanged | changed |
  |---|---|---|
  | supported | 42 | 36 |
  | unclear | 3 | 6 |
  | contradicted | 0 | 1 |

  The 45 changes touched 39 dispositions, 8 targets and 2 citations. 32 of
  the 39 disposition changes re-decide the five undesired-variant columns as
  `ignore (accidental)` plus a question. Flash had filled them from the
  happy path.

  A `supported` verdict says nothing about whether a cell is final: 36 of 78
  supported cells were changed. Jev checks that the cited fragment backs the
  statement. It does not check that the disposition is the right reading of
  intent.
- **Tests:** Flash drafted 19 as-is tests and the agent changed 2. With
  `-skip '^TestPool_Get$'` all of them pass under `-race`. The repository's
  own `TestPool_Get` hangs at the 60 s timeout, with its goroutines blocked
  at channel.go:137 (Q-21).

## Part B (PR #11's open measurement)

Part B marked 0 rows `as-is:`, so the `PART-B INDEPENDENCE` line was absent.
It did write "as-is" in prose in 6 rows (Put, Close, Ping, Release,
UV-Conn-nil, P-06a), and the agent treats agreement on those rows as not
independent. Of the 23 rows, 17 are convergent holes, 5 are divergences
(all folded into questions) and 1 is an artefact.

Leaks the label did not cover: implementation names in prose (`c.mu`,
`openingConns`), and pair orderings that name implementation steps (P-02b,
P-04a, P-06a, P-06b). These sit outside the labelled sections.

Part B was Flash (`blind`), not a Claude subagent. Whether a model follows
the `as-is:` instruction therefore remains unmeasured for the steering
model.

## Tool and prompt problems from this run

1. `gen_analysis_sidecar.py` `_parse_event_annotations` matches only the
   plain heading `## Event annotations`. A catalogue whose heading already
   carries "(observed in code)" made `dsc_check.py` report every annotation
   as missing. The agent used plain headings, because the Part-B packager
   adds the label itself. Neither the prompt nor the tool says so.
2. The reachability gap above.
3. The system python had no z3, so the agent created a venv. This is not a
   pack defect.
