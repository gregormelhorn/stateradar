# Routed pilot vs. benchmark silenceper-pool-32 — comparison

Routed run: pack da655aa, prompt v1.16, pool @ 6084537, routing on (Flash + Jev 1.14.0).
Oracle: `pack/tests/benchmarks/silenceper-pool-32/` (read only after the pilot finished).

## Blinding caveat

The coordinator's brief named the primary finding ("Release() does not unblock waiters in
connReqs, PA-21 / F-07") before the pilot started, so the Part-A agent was **not blind** to
the oracle's main finding. The benchmark directory, issue #32 and PR #33 were not read.
Independent evidence: Flash, which never saw the brief, raised the finding in its own
Step-1 draft of channel.go (`dv-channel-r2.json`, question 4: "Release closes c.conns but
never closes the connReqs channels; what happens to a Get blocked on <-req when Release
runs concurrently? Is the waiter leaked forever?", and question 23 on line 139's
`!ok` branch having no producer).

## Primary finding

Found: **yes**. Q-01 (F-07, F-20; PA-21 and PA-24 lints; SYS-4 z3 violation; trace T-P01a;
Part B convergent-hole on P-01a). Expected phrases `connReqs` and `waiter` are present.

Disposition label differs: the baseline marks `Active_IdleExhausted_AtCapacity × Release`
as `UNSPECIFIED → Q-01`; the routed matrix records the observed behaviour as
`transition → Released_WaitersStranded … → Q-01` (Open_Waiting / Open_Waiting_CapacityFree
rows) plus two hole cells in the new state Released_WaitersStranded (`handoff`, `UV-01`
= `ignore (accidental) → Q-01`). A scorer that requires the literal `UNSPECIFIED` on that
cell would count it as missed.

`expected.json` unspecified cells:

| expected | routed | match |
|---|---|---|
| Released × Put | Released × put = `ignore (accidental) → Q-04` | hole: yes; literal UNSPECIFIED: no |
| Active_IdleExhausted_AtCapacity × Release | Open_Empty_AtCap × release = transition → Released (no waiter yet); Open_Waiting × release = transition → Released_WaitersStranded → Q-01 | finding: yes; hole label: no |

## Cell-level agreement (aligned base grid, 4 states × 7 events = 28 cells)

State alignment: Active_HasIdle ↔ Open_Idle; Active_IdleExhausted_UnderCap ↔
Open_Empty_BelowCap; Active_IdleExhausted_AtCapacity ↔ Open_Empty_AtCap ∪ Open_Waiting;
Released ↔ Released ∪ Released_WaitersStranded. Events: Get, Put, Close, Release,
FactoryFail, IdleTimeout, PingFail ↔ get, put, close_conn, release, factory_error,
idle_expired, ping_failed.

| baseline state | Get | Put | Close | Release | FactoryFail | IdleTimeout | PingFail |
|---|---|---|---|---|---|---|---|
| Active_HasIdle | = (handle; routed: guarded transition, else handle) | = | = | = | **≠** handle vs ignore (documented) | = | = |
| Active_IdleExhausted_UnderCap | = (guarded transition, else handle) | = | **≠** UNSPECIFIED Q-06 vs handle | = | **≠** UNSPECIFIED Q-05 vs handle | = | = |
| Active_IdleExhausted_AtCapacity | = (defer; routed: transition → Open_Waiting / defer) | = (handle; routed: transition → Open_Idle / handoff) | **≠** UNSPECIFIED Q-06 vs transition (→ Q-02 lost wake-up) | **≠ label** UNSPECIFIED Q-01 vs transition → Q-01 | **≠** UNSPECIFIED Q-05 vs ignore (documented) | = | = (routed adds the handoff-path hole Q-07) |
| Released | = reject | = hole (UNSPECIFIED vs ignore (accidental)) | **≠** ignore (documented) vs ignore (accidental) → Q-04 | = | = | = | = |

Convergent 21 / 28 (75 %); divergent 7, of which 1 is label-only (same finding).
The baseline's own CONVERGENCE.md reports 28/28 between its two runs.

Divergences, assessed against channel.go @ 6084537:

* FactoryFail (3 cells): the baseline holes rest on "factory failure … without
  decrementing openingConns … the counter can drift" (baseline Q-05). The code increments
  only after success (channel.go:155-159), so nothing drifts; at the cap the factory is not
  called (channel.go:133). The baseline's later DR-005 says the same. The routed cells
  (handle / ignore (documented)) match the code.
* Close in UnderCap/AtCapacity (2 cells): baseline hole for counter underflow (Q-06). The
  routed run models misuse as separate variants (UV-07, UV-08 → Q-11) and the base Close as
  handle; at the cap it found a different, new issue: the freed slot does not wake waiters
  (Q-02).
* Released × Close: baseline `ignore (documented)` (code returns nil); routed `ignore
  (accidental) → Q-04` because the doc comment "Close 关闭单条连接" (closes a single
  connection, channel.go:201) is contradicted.

## Finding / question level

| baseline question | routed | match |
|---|---|---|
| Q-01 Release/connReqs leak | Q-01 | matched |
| Q-02 Put integrity (loss, duplicate, foreign) | Q-10 (loss), Q-11 (duplicate, foreign, double close) | matched |
| Q-03 Put after Release | Q-04 | matched |
| Q-04 waiter-path Ping skipped | Q-07 | matched |
| Q-05 FactoryFail handling | Q-16 (fill-failure counter) | partial; the counter-drift claim is contradicted by the code (see above) |
| Q-06 Close / openingConns underflow | Q-11 | matched for double/foreign Close; the "close-after-Release drives the counter negative" part is contradicted (channel.go:208-211 returns before the decrement) |
| Q-UV-01 Get commission / value | asserted absence (`n/a` with reasons) in the coverage table | missed as a question |
| Q-07 (to-be) undesired Release variants | UV-10 (duplicate) handled; contradiction/commission covered by pairs P-01..P-05 | partial |

New in the routed run (not in the baseline): Q-02 lost wake-up on Close/discard; Q-03
enqueue race and waiter fairness; Q-05 Ping panic after Release / without callback, and
the unsynchronized read of `c.ping`; Q-06 Release does not close checked-out connections;
Q-08 Len semantics; Q-09 no wait timeout, `waitTimeOut` unused, `ErrMaxActiveConnReached`
unreachable, TestPool_Get expects it; Q-12 callbacks under the mutex (deadlock on
reentrancy, slow factory stalls the pool); Q-13 InitialCap documented as minimum; Q-14
MaxCap = 0 accepted; Q-15 API contract; Q-17 Get racing the drain; Q-18 multi-instance;
Q-19 test-oracle gaps; Q-20..Q-23 voided control verdicts (routing rule 5).

Contradictions with the baseline: (1) Q-05 counter drift on factory failure — refuted by
channel.go:155-159; (2) Q-06 underflow via Close after Release — refuted by
channel.go:208-211; (3) Released × Close documented vs accidental (doc comment
channel.go:201); (4) the baseline's line citations (Release "channel.go:197-213" / ":215",
waiter ":139", Put→Close ":190") do not match HEAD 6084537 (Release 224-243, waiter 137,
Put→Close 176), although the manifest says "Commit: main (HEAD)"; (5) proposed fix: the
baseline (DR-001) resolves waiters with ErrMaxActiveConnReached; the routed run proposes
ErrClosed (a proposal, not a contradiction of fact).
