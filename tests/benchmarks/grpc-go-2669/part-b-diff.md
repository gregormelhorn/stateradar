# Part-B diff — grpc-go v1.18.0 `addrConn`

Classification of every blind-table row (part-b-blind-table.md, 40 ids:
26 catalogue events + 14 pair orderings) against disposition-matrix.md,
per 02-pilot PART B. Classes: `convergent` | `convergent-hole` |
`divergence` | `artefact` | `pass-B-blind-spot`. Every divergence ends
folded into an existing Q (no new Q was needed — both divergences are
faces of questions Part A already raised). Disputed dispositions were
re-verified against the frozen v1.18.0 clone (cited below); no later
sources consulted.

## Coverage verification (mechanical)

`tools/part_b_pack.py --check` run against the blind table: every
catalogue event id and every pair ordering appears exactly once —
40 of 40, no miscount (output at the end of this file).

## Structural decisions (prompt-mandated)

### `Connecting_HandshakeWait` — artefact (catalogue phrasing), repaired

The blind pass modelled a sub-state Part A does not have: "TCP dial
returned, SETTINGS preface not yet received", derived from E10's
"consumed only during handshake wait" phrasing plus the requirements'
CONNECTING definition. Verified against the clone: the preface wait is
a `select` **inside** `createTransport` before it returns
(clientconn.go:1190-1201, On mode; Hybrid spawns a watcher and returns;
Off returns immediately) — dial and handshake wait are one sequential
phase whose only outcomes are the phase-results E06/E16/E07. No event
is dispatched against a distinguishable HandshakeWait state. Every
blind HandshakeWait disposition (E07 advance-address, E08 attempt
fails, E09 closed-before-preface → E07 path, E10 → Ready, UV03 timer
close, UV04 deadline) maps 1:1 onto Part A's `Connecting_Dialing` cells
with identical outcomes. **Decision: artefact, not a granularity
divergence** — the finer state changes no disposition. Repair: the
catalogue's abstraction note now states that the handshake wait is
inside the dial phase (see event-catalogue.md, "Part-B repairs").

### `Transient_Failure` vs `TransientFailure` — artefact (naming), repaired

Vocabulary only: the blind pass PascalCased the API name
TRANSIENT_FAILURE as `Transient_Failure`, which collides with PA-17's
`_`-as-sub-state-separator rule (`_Failure` reads as a sub-state). All
dispositions map cleanly (`Transient_Failure_Backoff` ≡
`TransientFailure_Backoff`, etc.). **Decision: artefact.** Repair: the
catalogue now declares the canonical PA-17 leaf-state spellings, with
the collapse rule for multi-word API names.

### Third repair found during classification — E14 phrasing

The blind's E14 row assumed "the client-side health machinery has its
own stream retry/backoff upstream" continues after E14 — induced by the
catalogue's upstream-guard row ("retries stream with its own backoff").
Verified: the retry loop lives *inside* `healthCheckFunc`
(health/client.go:57-100, `continue retryConnection`); E14 fires only
when that function returns, i.e. retrying is over, and no monitoring
ever resumes (Part A's T-08/Q-08). Repaired in the catalogue (E14 gate
column + upstream-guard row).

## Classification table

| id | class | one-line reason | Q-ref |
|---|---|---|---|
| E01 | convergent | All five state dispositions match row-for-row (reject in Shutdown, no-op elsewhere, dial from Idle). | — |
| E02 | divergence | Blind expects a hard transport close on non-drain teardown ("Close transport hard"); the code nils the field and relies on ctx propagation only (clientconn.go:1332-1349, no `curTr.Close()`) — exactly Q-11's question; the rest of the row (drain/GracefulClose, idempotence, tearDownErr, channelz) converges. | Q-11 (fold) |
| E03 | convergent | Blind "reject — returns false → wrapper recreates" ≡ matrix "transition → Shutdown" (vocabulary only); the Shutdown dead-object anomaly restates the catalogued Q-09; nuance noted below (Idle branch skips the replacement's connect). | — |
| E17 | convergent | Same false→recreate mapping and Q-09 restatement as E03. | — |
| E04 | convergent | Blind "reject (nil, no side effect)" ≡ matrix "handle — returns (nil,false)": the same observable refusal, vocabulary only; Idle-kicks-connect and Ready-returns-transport match. | — |
| E05 | pass-B-blind-spot | Blind omits the TransientFailure_ServerUnhealthy sub-state, where Part A found DOC-15's "reconnect immediately" promise unmet (only backoffIdx zeroed) — Q-15; every sub-row the blind does give converges. | Q-15 (note) |
| E06 | convergent | Connecting_Dialing → Ready plus sequential-phase ignores match; the post-teardown exception correctly routed to UV08. | — |
| E16 | convergent | → Connecting_HealthChecking with curAddr withheld until the first serving report — matches the matrix and the G-08 gate. | — |
| E07 | convergent-hole | Independently flags that per-address failures staying CONNECTING skip DOC-7's TF notification — Part A's Q-14; rest of the row (errConnClosing exit, last-address → E15) converges. | Q-14 |
| E08 | convergent-hole | Independently flags GOAWAY-with-no-RPCs → IDLE as required-but-absent at this boundary — Part A's Q-06; reconnect, keepalive and stale-generation sub-rows converge (the blind accepts the monotonic keepalive ratchet that Q-16 questions — noted below). | Q-06 |
| E09 | divergence | Blind expects the post-success TF dwell to reflect the reset backoffIdx ("dwell may be zero-length"); the code sleeps the stale `backoffFor` (clientconn.go:975→1129) — folded into Q-03; its TF-visit open point is answered convergent: cell (Ready, E09) = transition → TransientFailure_Backoff, the notification is emitted. | Q-03 (fold) |
| E10 | convergent-hole | Marks the Off-mode never-read preface an accidental ignore and derives the unwitnessed reset-on-SETTINGS obligation from the backoff doc — Q-04 substance; handshake-wait and Hybrid death-check sub-rows converge. | Q-04 |
| E11 | convergent | Timer wake → Connecting_Dialing; Shutdown wake exits without dialing — matches. | — |
| E12 | convergent-hole | Independently flags TF→READY as forbidden by the requirements' legal-transition table — Part A's Q-07; serving/repeat/stale/Shutdown sub-rows converge (blind "ignore" vs matrix "handle — same-state no-op" is vocabulary). | Q-07 |
| E13 | convergent | → TransientFailure_ServerUnhealthy from Ready and HealthChecking; identity-guarded ignores match. | — |
| E14 | convergent-hole | Flags stream-end-before-verdict stranding (UV09 adjacency) and the no-state-write monitoring loss — Q-08; its "retries upstream" assumption was catalogue phrasing, repaired (see above). | Q-08 |
| E15 | convergent | → TransientFailure_Backoff with the Shutdown check at TF entry — matches. | — |
| UV01 | convergent | Generation isolation, ignore (documented) — matches. | — |
| UV02 | convergent | Idempotent Fire + monotonic adjustParams — matches. | — |
| UV03 | convergent-hole | Off-arm unverified publish + backoff reset without SETTINGS flagged as defect — Q-04; On/Hybrid arms converge (Hybrid false-READY judged "legal but exposed", matching V-07). | Q-04 |
| UV04 | convergent | connectCtx deadline fails the attempt (G-04 proven) — matches. | — |
| UV05 | convergent | Both fire one idempotent event, order-independent — matches. | — |
| UV06 | convergent | Not producible; late reports identity-guarded — matches. | — |
| UV07 | convergent | Transport-identity guard — matches. | — |
| UV08 | convergent-hole | Required disposition (close the new transport, stay Shutdown) independently derived from DOC-5's terminal-state text; the actual resurrection defect is Q-01 (the gap itself was carried in the catalogue's UV row). | Q-01 |
| UV09 | convergent-hole | UNSPECIFIED verdictless-stream gap plus the DOC-3 "eventually CONNECTING" breach for the stranded TF sub-state — Q-08. | Q-08 |
| P-01a | convergent-hole | Resurrection ordering marked required-ignore / actual-Ready through the documented unlock window — Q-01. | Q-01 |
| P-01b | convergent | Publish-then-teardown; GracefulClose iff drain — matches the control trace. | — |
| P-02a | convergent-hole | Reset-before-TF-entry loses the wake (fresh channel) and keeps the stale sleep — Q-03; the blind adds the backoff-doc intent reading ("reset ⇒ behave like a new connection" honoured only next cycle). | Q-03 |
| P-02b | convergent | Channel close wakes the select immediately; the sanctioned TF→CONNECTING exit — matches. | — |
| P-03a | convergent-hole | Lock-order-inversion deadlock marked UNSPECIFIED-defect; "no requirement permits a public API call to wedge the channel" — Q-02. | Q-02 |
| P-03b | convergent | Serialized order disposes per base rows; the order-decides-survival asymmetry matches trace P-03b. | — |
| P-04a | convergent | Keep-or-recreate per curAddr membership; stale E09 on a replaced ac ignored — matches (on the keep branch the same ac walks the new list, trace P-04a). | — |
| P-04b | convergent | Mid-reconnect update → teardown+recreate (only Ready keeps) — matches V-11. | — |
| P-05a | convergent | One idempotent reconnect, params adjusted — matches. | — |
| P-05b | convergent | Late goaway adjusts params only (monotonic max) — matches. | — |
| P-06a | convergent | TF_ServerUnhealthy → TF_Backoff on transport death — matches. | — |
| P-06b | convergent | Stale verdict identity-guarded — matches. | — |
| P-07a | convergent | Post-teardown connect rejected with errConnClosing — matches. | — |
| P-07b | convergent | Ctx-abort of the in-flight dial via the Shutdown checks; the success window correctly deferred to P-01a — matches. | — |

## Summary counts

| class | count | ids |
|---|---|---|
| convergent | 26 | E01, E03, E17, E04, E06, E16, E11, E13, E15, UV01, UV02, UV04, UV05, UV06, UV07, P-01b, P-02b, P-03b, P-04a, P-04b, P-05a, P-05b, P-06a, P-06b, P-07a, P-07b |
| convergent-hole | 11 | E07 (Q-14), E08 (Q-06), E10 (Q-04), E12 (Q-07), E14 (Q-08), UV03 (Q-04), UV08 (Q-01), UV09 (Q-08), P-01a (Q-01), P-02a (Q-03), P-03a (Q-02) |
| divergence | 2 | E02 (→ fold Q-11), E09 (→ fold Q-03) — both closed by fold, no new Q |
| artefact | 0 id-level | 3 cross-cutting artefacts repaired in the catalogue: HandshakeWait granularity, Transient_Failure naming, E14 retry phrasing (see "Structural decisions") |
| pass-B-blind-spot | 1 | E05 (missing TF_ServerUnhealthy sub-row — Q-15) |
| **total** | **40** | |

## Divergence folds (each with its reasoned sentence)

* **E02 → Q-11.** The blind's expected hard close on non-drain teardown
  is exactly the disposition Q-11 already proposes ("close explicitly");
  the code's actual behaviour — nil the field, cancel ctx, rely on
  NAT-5 eventual propagation (clientconn.go:1332-1349) — is the current
  behaviour Q-11 records, so the divergence is that question, not a new
  one.
* **E09 → Q-03.** The blind's zero-length-dwell expectation after a
  successful connection dies is the natural DOC-13/DOC-15 reading; the
  stale `backoffFor` computed pre-reset (clientconn.go:975, used at
  1129) is precisely the mechanism Q-03 records (trace T-05, up to 120s
  dead air), so the divergence folds there.

## Vocabulary-only differences (noted, all convergent per 02's rule)

* E03/E17 non-Ready: blind `reject` (returns false) ≡ matrix
  `transition → Shutdown` (the false return *is* the teardown+recreate
  trigger — same observable).
* E04 non-Ready/Shutdown: blind `reject` ≡ matrix `handle — returns
  (nil,false)` (declared not-ready signal).
* E12 Ready-repeat: blind `ignore (documented)` ≡ matrix `handle —
  same-state no-op`.
* E08 Shutdown: blind `ignore (documented)` with params residue ≡
  matrix `handle — bumps cc.mkp (monotonic, harmless)`.

## Sub-row nuances and pass-A-only findings (no action)

* **E03 Idle branch:** blind says "replacement ac starts at
  Connecting"; verified in the clone the wrapper skips `connect()` when
  the old ac was Idle (`if acState != connectivity.Idle`,
  balancer_conn_wrappers.go:311-313) and recreates nothing at all when
  it was already Shutdown. Neighbouring-instance detail, this ac's
  disposition converges.
* **E08 keepalive:** the blind treats the monotonic mkp ratchet as
  by-design and never questions its lack of decay — pass A's Q-16
  (ClientConn model link) has no blind counterpart within the row.
* **Not row-classifiable (no blind row can expose them):** Q-05
  (upstream env-parse defect), Q-09's empty-addrs degenerate (T-10,
  NAT-4), Q-10 (dead `tryNextAddrFromStart` mechanism), Q-12 (defer
  accumulation), Q-13 (multi-instance herd — the blind table has no
  multi-instance rows by design). All code-internal or out of the blind
  pass's scope; they remain pass-A-only by construction, not blind-pass
  misses of presented material.

## Question updates made

* Convergent-hole notes added to Q-01, Q-02, Q-03, Q-04, Q-06, Q-07,
  Q-08, Q-14 (`part-B:` line each).
* Fold notes added to Q-03 and Q-11.
* No new Q. No matrix cell changed hole status →
  disposition-matrix.md and analysis.json unchanged.

## Checker outputs (executed after the edits, 2026-08-07)

```text
$ python3 tests/benchmarks/grpc-go-2669/check_matrix.py
CHECK MATRIX: OK (7 rows x 26 events)

$ python3 tools/part_b_pack.py tests/benchmarks/grpc-go-2669 --repo . \
    --check tests/benchmarks/grpc-go-2669/part-b-blind-table.md
PART-B COVERAGE: OK (26 events, 14 pair orderings)

$ uv run --with-requirements tools/requirements-dev.txt python3 \
    tools/dsc_check.py tests/benchmarks/grpc-go-2669 \
    --repo <frozen grpc-go v1.18.0 clone> --model as-is.machine.mmd
DSC CHECK: OK (7 states x 26 events, 182 cells, 12 guard groups)
```

analysis.json not regenerated: no matrix cell, state, event, pair,
guard outcome, or question id changed (Q set stays Q-01..Q-16; the
part-B edits add provenance notes only). The sidecar remains valid, as
dsc_check confirms above.
