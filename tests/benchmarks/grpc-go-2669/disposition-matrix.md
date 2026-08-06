# Disposition matrix — grpc-go v1.18.0 `addrConn`

<!-- states: Idle, Connecting_Dialing, Connecting_HealthChecking, Ready, TransientFailure_Backoff, TransientFailure_ServerUnhealthy, Shutdown -->

Abstraction (PA-10): completeness is relative to the catalogue in
event-catalogue.md (26 events incl. 9 undesired variants) and to the
guard predicates formalized in check_guards.py (G-01…G-12). Sub-state
dispositions are stated at leaf level; there is no compound-row
inheritance. Shutdown is NOT declared terminal (PA-18) because three
events still do something there (E01 reject, E03/E17/E05 mutations,
UV08 bug transition).

Wide matrix: four sub-tables; state rows repeat in full.

## Sub-table 1 — API events

| State | E01 `connect` | E02 `teardown` | E03 `update.addrs.keep` | E17 `update.addrs.drop` | E04 `get.ready.transport` | E05 `reset.backoff` |
|---|---|---|---|---|---|---|
| **Idle** | transition → Connecting_Dialing — clientconn.go:676 ("if ac.state != connectivity.Idle"), spawns resetTransport clientconn.go:684 | transition → Shutdown — clientconn.go:1326-1339 | transition → Shutdown — tryUpdateAddrs false (not Ready) clientconn.go:705; wrapper tears down + recreates, no connect (was Idle) balancer_conn_wrappers.go:285-311 | transition → Shutdown — same path balancer_conn_wrappers.go:285-311 | transition → Connecting_Dialing — idle triggers connect clientconn.go:1310-1317 | handle — backoffIdx=0, channel swapped, no observer clientconn.go:1291-1297 |
| **Connecting_Dialing** | ignore (documented) — non-Idle no-op clientconn.go:676-678 (DOC-17) | transition → Shutdown — clientconn.go:1326-1349; loop exits at clientconn.go:982/1003/1121 or dial aborts via ctx clientconn.go:1181; in-flight success window → UV08/Q-01 | transition → Shutdown — tryUpdateAddrs false clientconn.go:705; wrapper recreates + connects balancer_conn_wrappers.go:285-313 (V-11) | transition → Shutdown — same clientconn.go:705, balancer_conn_wrappers.go:285-313 | handle — returns (nil,false), no trigger clientconn.go:1304-1313 | handle — backoffIdx=0 clientconn.go:1294; pending iteration keeps stale backoffFor clientconn.go:975 → Q-03 note |
| **Connecting_HealthChecking** | ignore (documented) — clientconn.go:676-678 | transition → Shutdown — clientconn.go:1326-1364; hctx cancelled clientconn.go:1337 | transition → Shutdown — clientconn.go:705, balancer_conn_wrappers.go:285-313 | transition → Shutdown — same balancer_conn_wrappers.go:285-313 | handle — not Ready: (nil,false) clientconn.go:1304-1313 | handle — clientconn.go:1291-1297 |
| **Ready** | ignore (documented) — clientconn.go:676-678 (DOC-17) | transition → Shutdown — clientconn.go:1326-1348; errConnDrain → GracefulClose clientconn.go:1340-1347 | handle — curAddr in new list: addrs updated, connection kept clientconn.go:709-721 (DOC-18) | transition → Shutdown — curAddr dropped: tryUpdateAddrs false clientconn.go:717-721; wrapper tears down + recreates + connects balancer_conn_wrappers.go:285-313 | handle — returns (transport,true) clientconn.go:1304-1308 | handle — zeroes possibly-stale backoffIdx clientconn.go:1294 (idx only reset at transport death clientconn.go:1112 → useful here) |
| **TransientFailure_Backoff** | ignore (documented) — clientconn.go:676-678; backoff NOT preempted (DOC-17) | transition → Shutdown — ctx.Done unblocks select clientconn.go:1140-1142 | transition → Shutdown — clientconn.go:705, balancer_conn_wrappers.go:285-313 | transition → Shutdown — same balancer_conn_wrappers.go:285-313 | handle — (nil,false) clientconn.go:1304-1313 | transition → Connecting_Dialing — close(resetBackoff) wakes select clientconn.go:1138-1139, backoffIdx=0 clientconn.go:1294 (DOC-15); channel-identity race → Q-03 |
| **TransientFailure_ServerUnhealthy** | ignore (documented) — clientconn.go:676-678 | transition → Shutdown — clientconn.go:1326-1364 | transition → Shutdown — not Ready ⇒ false clientconn.go:705; wrapper kills live transport + recreates balancer_conn_wrappers.go:285-313 | transition → Shutdown — same balancer_conn_wrappers.go:285-313 | handle — (nil,false) despite live transport clientconn.go:1304-1313 | handle — idx reset only clientconn.go:1294; loop parked on reconnect, NO immediate reconnect despite DOC-15 → Q-15 |
| **Shutdown** | reject — returns errConnClosing clientconn.go:672-674 | ignore (documented) — idempotent no-op clientconn.go:1328-1331 | handle — mutates addrs on dead ac, returns true clientconn.go:698-701 → Q-09 note | handle — same clientconn.go:698-701 → Q-09 note | handle — (nil,false) clientconn.go:1304-1313 | handle — channel swap on dead ac clientconn.go:1291-1297 → Q-09 note |

## Sub-table 2 — dial results and transport callbacks

| State | E06 `dial.ok` | E16 `dial.ok.healthmanaged` | E07 `dial.err` | E08 `transport.goaway` | E09 `transport.closed` | E10 `preface.received` | E11 `backoff.timer.fired` |
|---|---|---|---|---|---|---|---|
| **Idle** | ignore (documented) — no dial in flight; results consumed synchronously inside the loop clientconn.go:966-1145 | ignore (documented) — clientconn.go:966-1145 | ignore (documented) — clientconn.go:966-1145 | ignore (documented) — callbacks are closures of a created transport; none exists clientconn.go:1163-1174 | ignore (documented) — clientconn.go:1163-1174 | ignore (documented) — clientconn.go:1176-1179 | ignore (documented) — timer exists only in the TF sleep clientconn.go:1129 |
| **Connecting_Dialing** | transition → Ready — publish curAddr/transport clientconn.go:1026-1030, Ready clientconn.go:1049-1052 (guard G-08 false) | transition → Connecting_HealthChecking — spawn health goroutine clientconn.go:1039-1048 (guard G-08 true) | handle — next address, stays Connecting clientconn.go:1054-1063, 986-987; Hybrid emits TF blip clientconn.go:1097 → Q-14 | handle — adjustParams + reconnect pre-fired clientconn.go:1163-1168; attempt resolves via E06/E07 | handle — closed-before-preface → error clientconn.go:1198-1200 → E07 path | handle — stops preface timer, closes prefaceReceived clientconn.go:1176-1179; unblocks On-mode wait clientconn.go:1196 | ignore (documented) — no timer in this phase clientconn.go:1129 |
| **Connecting_HealthChecking** | ignore (documented) — sequential loop parked clientconn.go:1070 | ignore (documented) — clientconn.go:1070 | ignore (documented) — clientconn.go:1070 | transition → TransientFailure_Backoff — reconnect fires clientconn.go:1163-1168, loop resumes clientconn.go:1070, hcancel 1071, TF clientconn.go:1125 | transition → TransientFailure_Backoff — same path clientconn.go:1170-1174, 1070-1131 | handle — one-shot close clientconn.go:1176-1179; read at Hybrid death-check clientconn.go:1080 | ignore (documented) — clientconn.go:1129 |
| **Ready** | ignore (documented) — loop parked clientconn.go:1070 | ignore (documented) — clientconn.go:1070 | ignore (documented) — clientconn.go:1070 | transition → TransientFailure_Backoff — adjustParams clientconn.go:954-964, reconnect clientconn.go:1070-1131; old transport drains server-side, ac re-dials | transition → TransientFailure_Backoff — clientconn.go:1070-1131 (V-04); sleeps stale backoffFor → Q-03 | handle — late preface (Off/Hybrid) stops watcher clientconn.go:1176-1179 | ignore (documented) — clientconn.go:1129 |
| **TransientFailure_Backoff** | ignore (documented) — no dial during sleep clientconn.go:1133-1143 | ignore (documented) — clientconn.go:1133-1143 | ignore (documented) — clientconn.go:1133-1143 | handle — stale-generation goaway still runs adjustParams clientconn.go:954-964; reconnect event of dead generation clientconn.go:1023 | ignore (documented) — dead generation, event already consumed clientconn.go:1023 | ignore (documented) — one-shot channel of a finished attempt clientconn.go:1176-1179 | transition → Connecting_Dialing — backoffIdx++ clientconn.go:1134-1137; resolveNow next iteration clientconn.go:971-973 |
| **TransientFailure_ServerUnhealthy** | ignore (documented) — loop parked clientconn.go:1070 | ignore (documented) — clientconn.go:1070 | ignore (documented) — clientconn.go:1070 | transition → TransientFailure_Backoff — clientconn.go:1163-1168, 1070-1131 | transition → TransientFailure_Backoff — clientconn.go:1070-1131 | handle — clientconn.go:1176-1179 | ignore (documented) — clientconn.go:1129 |
| **Shutdown** | ignore (documented) — loop exits at Shutdown checks clientconn.go:982/1003/1121 before any *new* dial; the in-flight race case is UV08 | ignore (documented) — same clientconn.go:982-1006; race case → UV08 | handle — error path detects Shutdown, returns errConnClosing, goroutine exits clientconn.go:1221-1226, 1056-1058 | handle — late goaway of dying transport still bumps cc.mkp clientconn.go:954-964 (monotonic, harmless) | ignore (documented) — reconnect event unread after loop return clientconn.go:1023 | ignore (documented) — one-shot, no reader clientconn.go:1176-1179 | ignore (documented) — timer stopped on ctx exit clientconn.go:1140-1142 |

## Sub-table 3 — health and internal loop events

| State | E12 `health.report.serving` | E13 `health.report.notserving` | E14 `health.stream.ended` | E15 `addrs.exhausted` | UV01 `stale.transport.callback` | UV02 `goaway.duplicate` |
|---|---|---|---|---|---|---|
| **Idle** | ignore (documented) — no health goroutine before dial success clientconn.go:1045 | ignore (documented) — clientconn.go:1045 | ignore (documented) — clientconn.go:1045 | ignore (documented) — loop not running clientconn.go:684 | ignore (documented) — a fresh ac has no previous generation clientconn.go:592-601 | ignore (documented) — clientconn.go:1163-1174 |
| **Connecting_Dialing** | ignore (documented) — guard clientconn.go:1262 (transport nil or mismatched) | ignore (documented) — clientconn.go:1262 | ignore (documented) — no health goroutine yet clientconn.go:1045 | transition → TransientFailure_Backoff — clientconn.go:1118-1131 | ignore (documented) — per-attempt events clientconn.go:1023-1024 | handle — idempotent fire, monotonic adjustParams clientconn.go:1023, 954-964 |
| **Connecting_HealthChecking** | transition → Ready — clientconn.go:1265-1270; first report sets curAddr clientconn.go:1266-1269 | transition → TransientFailure_ServerUnhealthy — clientconn.go:1271-1273 | handle — log only, no state write clientconn.go:1276-1288; Unimplemented already reported serving upstream (health client contract) | ignore (documented) — loop parked clientconn.go:1070 | ignore (documented) — clientconn.go:1023-1024 | handle — clientconn.go:1023, 954-964 |
| **Ready** | handle — same-state no-op clientconn.go:936-938 | transition → TransientFailure_ServerUnhealthy — clientconn.go:1271-1273 (health-managed only, gate G-08) | handle — log only clientconn.go:1276-1288; connection stays Ready unmonitored → Q-08 note | ignore (documented) — loop parked clientconn.go:1070 | ignore (documented) — clientconn.go:1023-1024 | handle — clientconn.go:1023, 954-964 |
| **TransientFailure_Backoff** | ignore (documented) — hcancel'd clientconn.go:1071; late report guarded clientconn.go:1262 | ignore (documented) — clientconn.go:1262 | ignore (documented) — health goroutine ended with attempt clientconn.go:1071 | ignore (documented) — not in addrLoop clientconn.go:1133-1143 | ignore (documented) — clientconn.go:1023 | handle — adjustParams still monotonic clientconn.go:954-964 |
| **TransientFailure_ServerUnhealthy** | transition → Ready — clientconn.go:1265-1270; contradicts DOC-6 legal table → Q-07 note | handle — same-state no-op clientconn.go:936-938 | handle — log only clientconn.go:1276-1288 | ignore (documented) — loop parked clientconn.go:1070 | ignore (documented) — clientconn.go:1023-1024 | handle — clientconn.go:1023, 954-964 |
| **Shutdown** | ignore (documented) — guard clientconn.go:1262 (transport==nil after tearDown clientconn.go:1333) | ignore (documented) — clientconn.go:1262 | handle — log only clientconn.go:1276-1288 | ignore (documented) — loop returned clientconn.go:1121-1123 | ignore (documented) — clientconn.go:1023 | handle — clientconn.go:954-964 |

## Sub-table 4 — undesired variants (handshake, contradiction, value, shutdown race)

| State | UV03 `preface.never` | UV04 `handshake.timeout` | UV05 `goaway.close.simultaneous` | UV06 `health.report.spurious` | UV07 `health.report.stale.transport` | UV08 `dial.result.after.teardown` | UV09 `health.stream.silent` |
|---|---|---|---|---|---|---|---|
| **Idle** | ignore (documented) — no dial in flight clientconn.go:966-1145 | ignore (documented) — clientconn.go:966-1145 | ignore (documented) — clientconn.go:1163-1174 | ignore (documented) — reportHealth closure only invocable by healthCheckFunc clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 | ignore (documented) — requires a completed teardown, i.e. state Shutdown; see (Shutdown, UV08) clientconn.go:1326-1339 | ignore (documented) — no health stream clientconn.go:1045 |
| **Connecting_Dialing** | handle — On: preface timer closes transport, attempt fails clientconn.go:1192-1195; Off: never checked, publishes unverified connection → Q-04 note | handle — connectCtx deadline fails the dial clientconn.go:1181, 991-996 | handle — both fire one idempotent event; order-independent clientconn.go:1163-1174 | ignore (documented) — clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 | ignore (documented) — see (Shutdown, UV08) clientconn.go:1326-1339 | ignore (documented) — no health stream yet clientconn.go:1045 |
| **Connecting_HealthChecking** | handle — Hybrid watcher may close the live transport on preface timeout clientconn.go:1202-1213 → E09 follows | ignore (documented) — dial already completed clientconn.go:1026-1030 | handle — clientconn.go:1163-1174 | ignore (documented) — clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 | ignore (documented) — see (Shutdown, UV08) clientconn.go:1326-1339 | ignore (accidental) → Q-08 — no verdict timeout; ac stuck Connecting indefinitely (no code path leaves this state on silence) |
| **Ready** | handle — Hybrid watcher closes a READY transport on preface timeout clientconn.go:1202-1213 (V-07) → E09 | ignore (documented) — dial done clientconn.go:1026-1030 | handle — clientconn.go:1163-1174 | ignore (documented) — clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 | ignore (documented) — see (Shutdown, UV08) clientconn.go:1326-1339 | ignore (documented) — silence leaves Ready; the only writer is reportHealth clientconn.go:1259-1274; monitoring gap noted in Q-08 |
| **TransientFailure_Backoff** | ignore (documented) — no dial during sleep clientconn.go:1133-1143 | ignore (documented) — clientconn.go:1133-1143 | handle — idempotent + monotonic clientconn.go:1163-1174, 954-964 | ignore (documented) — clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 | ignore (documented) — see (Shutdown, UV08) clientconn.go:1326-1339 | ignore (documented) — no stream clientconn.go:1071 |
| **TransientFailure_ServerUnhealthy** | handle — Hybrid watcher may close the transport clientconn.go:1202-1213 → E09 | ignore (documented) — clientconn.go:1026-1030 | handle — clientconn.go:1163-1174 | ignore (documented) — clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 | ignore (documented) — see (Shutdown, UV08) clientconn.go:1326-1339 | ignore (accidental) → Q-08 — silent stream leaves TF forever while the transport lives; DOC-3 "eventually CONNECTING" has no path |
| **Shutdown** | ignore (documented) — no dial clientconn.go:982-1006 | ignore (documented) — clientconn.go:982-1006 | ignore (documented) — events unread after loop return clientconn.go:1023 | ignore (documented) — clientconn.go:1275 | ignore (documented) — guard clientconn.go:1262 holds only because tearDown nil'd transport clientconn.go:1333; broken after resurrection → Q-01 note | transition → Ready — **BUG** clientconn.go:1026-1052: curAddr/transport re-published (1027-1030) and Ready set (1051) with no Shutdown re-check after clientconn.go:1243-1248; health-managed variant re-arms reportHealth via 1029 → Q-01 | ignore (documented) — no stream clientconn.go:1071 |

## Guard notes (groups formalized in check_guards.py; outcomes from guard-results.txt)

* **G-01 connect state dispatch** (clientconn.go:671-679): guards
  {state==Shutdown → reject; state==Idle → dial; else → no-op}.
  Boundary: every enum value. Outcome: proven.
* **G-02 tryUpdateAddrs dispatch** (clientconn.go:698-721): guards
  {Shutdown; ¬Shutdown∧¬Ready; Ready∧curAddrFound; Ready∧¬curAddrFound}.
  Outcome: proven.
* **G-03 getReadyTransport dispatch** (clientconn.go:1304-1318): guards
  {Ready∧transport≠nil; ¬(Ready∧transport≠nil)∧Idle; else}. Boundary
  probe Ready∧transport==nil → falls to else (returns nil, no connect).
  Outcome: proven.
* **G-04 dial deadline max** (clientconn.go:991-995): dialDuration =
  minConnectTimeout unless backoffFor greater. Boundaries backoffFor
  19.9s/20s/20.1s. Outcome: proven (DOC-10 conformant).
* **G-05 updateConnectivityState terminality** (clientconn.go:936-942):
  the only guard is `s==ac.state`; SYS-1 requires `ac.state==Shutdown ⇒
  no write`. z3 finds the witness (state=Shutdown, s=Ready). Outcome:
  **violation** → Q-01.
* **G-06 reportHealth dispatch** (clientconn.go:1262-1273): guards
  {transport≠newTr; transport==newTr∧ok; transport==newTr∧¬ok}.
  Outcome: proven.
* **G-07 adjustParams** (clientconn.go:955-963): guards
  {r==TooManyPings∧v>mkp.Time; r==TooManyPings∧v≤mkp.Time;
  r≠TooManyPings}. Boundary v==mkp.Time → no bump (strict >). Outcome:
  proven.
* **G-08 health-managing gate** (clientconn.go:1039-1043):
  managing = ¬disableHealthCheck ∧ cfg≠nil ∧ scoptsEnabled ∧ fn≠nil;
  {managing; ¬managing}. Outcome: proven.
* **G-09 reqHandshake mode dispatch** (clientconn.go:1073/1104,
  1190/1202): {Hybrid; On; Off} over the 3-value enum. Outcome: proven.
* **G-10 backoff first-retry branch** (internal/backoff/backoff.go:60-62):
  {retries==0; retries>0} under NAT retries≥0; boundaries 0/1. Outcome:
  proven.
* **G-11 envconfig RequireHandshake parse**
  (internal/envconfig/envconfig.go:58-68): not-formalizable:
  unstructured-payload — env string switch; inspection shows `case "on":`
  has an empty body, so "on" yields the zero value Hybrid while unset
  yields On (contradicts envconfig.go:41-43) → Q-05. Unproven
  inspection reasoning.
* **G-12 backoff select ordering** (clientconn.go:1133-1143):
  not-formalizable: dynamic-state — outcome depends on runtime channel
  readiness (timer vs resetBackoff vs ctx); dispositions covered by
  cells (TransientFailure_Backoff, E11/E05/E02) and pair P-02.
