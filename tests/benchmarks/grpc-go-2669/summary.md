# Summary — grpc-go v1.18.0 `addrConn` pilot (Part A)

Component: `addrconn` — the `addrConn` sub-connection lifecycle,
clientconn.go, grpc-go tag v1.18.0
(SHA a02b0774206b209466313a0b525d2c738fe407eb, frozen tree; no
post-freeze sources consulted). Analysis only; no code changed.

## Counts

| metric | value |
|---|---|
| states (leaf) | 7 (Idle, Connecting_Dialing, Connecting_HealthChecking, Ready, TransientFailure_Backoff, TransientFailure_ServerUnhealthy, Shutdown) |
| events incl. undesired variants | 26 (17 base + 9 UV) |
| interaction pairs | 7 (14 traced orderings) |
| matrix cells | 182 |
| UNSPECIFIED | 0 |
| ignore (accidental) | 2 (both → Q-08) |
| guard groups | 12 — 9 proven, 1 violation (G-05 → Q-01), 2 not-formalizable (G-11, G-12) |
| doctrine lines | 20 (DOC-1..20), all mapped or explicitly rejected (invariants-and-lints.md) |
| SYS invariants | 7 — 4 hold, SYS-1/SYS-3/SYS-6/SYS-7 violated |
| adversarial traces | 14 systematic + 10 free + 3 multi-instance |
| findings | 16, all carried as questions |
| open questions | 16 (Q-01..Q-16, all OPEN) |

## Top findings (severity-ordered)

1. **Q-01 — Shutdown resurrection race** (F-04). Cell
   (Shutdown, UV08) = `transition → Ready`: a dial that completes after
   `tearDown` re-publishes `curAddr`/`transport`
   (clientconn.go:1027-1030) and sets Ready (clientconn.go:1051)
   because neither the publication window nor
   `updateConnectivityState` (clientconn.go:936-942) re-checks
   Shutdown. Violates DOC-5/DOC-6, SYS-1/SYS-3; z3 witness G-05.
2. **Q-02 — lock-order inversion deadlock** (F-11).
   `cc.ResetConnectBackoff` takes cc.mu→ac.mu
   (clientconn.go:843-849→1292); every state update takes ac.mu→cc.mu
   (clientconn.go:949→578, 998-1001). Trace P-03a.
3. **Q-03 — stale backoff duration** (F-18). `backoffFor` computed once
   per iteration (clientconn.go:975) is used for the post-disconnect
   sleep (clientconn.go:1129) even after `backoffIdx` was reset —
   up to 120s dead-air after a healthy connection dies (T-05), and
   ResetConnectBackoff arriving pre-sleep is lost (P-02a).

## Maturity

L2 (decided-pending): analysis artifacts + questions exist; no DRs, no
cell tests, no coverage map. Per 00-methods "Maturity levels", this is
analysis, not governance — "green means conforming" does not apply.

## Checker outputs (executed, not claimed)

```text
$ python3 tests/benchmarks/grpc-go-2669/check_matrix.py
CHECK MATRIX: OK (7 rows x 26 events)

$ uv run --with-requirements tools/requirements-dev.txt python3 check_guards.py
(guard-results.txt)
group G-01 connect-state-dispatch: proven
group G-02 tryUpdateAddrs-dispatch: proven
group G-03 getReadyTransport-dispatch: proven
group G-04 dial-deadline-max: proven
group G-05 updateConnectivityState-terminality: violation
  - SYS-1: write guard (s_new != s_cur) admits transitions out of Shutdown — witness s_cur=4, s_new=0 (clientconn.go:936-942 has no terminal guard; contrast clientconn.go:340-342). Reached via cell (Shutdown, UV08) -> Q-01.
group G-06 reportHealth-dispatch: proven
group G-07 adjustParams-dispatch: proven
group G-08 health-managing-gate: proven
group G-09 reqHandshake-mode-dispatch: proven
group G-10 backoff-first-retry: proven
group G-11 envconfig-requirehandshake-parse: not-formalizable (unstructured-payload -> Q-05)
group G-12 backoff-select-ordering: not-formalizable (dynamic-state)
(boundary probes: see guard-results.txt)

$ uv run --with-requirements tools/requirements-dev.txt python3 tools/dsc_check.py \
    tests/benchmarks/grpc-go-2669 --repo <grpc-go clone> --model as-is.machine.mmd
DSC CHECK: OK (7 states x 26 events, 182 cells, 12 guard groups)

$ uv run --with-requirements tools/requirements-dev.txt python3 tools/selftest/run_selftest.py
SELFTEST: OK   (pack selftests re-run after the harness fix below)
```

## Step-8 verification notes (claims re-read against the code)

* Q-01 concurrency claim: all writes are under `ac.mu` (no data race);
  the defect is a TOCTOU between createTransport's last guard
  (clientconn.go:1243-1248) and publication (1027) — the lock is
  dropped between them. Verified; stands as a bug.
* Q-02: cycle re-verified at the four lock sites; `cc.mu.RLock` at 999
  participates because Go's RWMutex blocks new readers while a writer
  waits. Stands as a bug.
* Q-03: `backoffFor` read once at 975, used at 1129 — re-read confirmed;
  reset sites 1084/1112/1294 never touch the local. Stands.
* Q-05 downgrade note: envconfig is outside the strict symbol scope;
  kept as a neighbouring-scope finding feeding gate G-09/G-11, not a
  matrix cell.
* T-09 keepalive ratchet reclassified from ac-defect to model-link
  question (Q-16): the mutated field belongs to ClientConn.
* Sentinel check: `errConnClosing` comparisons (clientconn.go:1056) are
  against a package-level singleton (clientconn.go:69) — literal
  identity, safe.
* V-08 jitter flakiness labelled `unverifiable-runtime` (timing), not a
  model error.
* No finding was removed in verification.

## Deviations from a vanilla pilot run (recorded)

* Pack harness fix (not analysis data): `tools/check_matrix.py`
  accepted only `.py:` citations; generalized to any `file.<ext>:NNN`
  (pack selftests re-run: OK). Method rule "never fix the data to
  silence a check" respected — the checker, not the matrix, was wrong.
* Sidecar generated via a temp `domain-analysis/addrconn` layout
  (generator assumes that layout), then `analysis.json` copied here and
  the pairs/guardGroups/coverage sections merged in (the generator
  derives cells only); `dsc_check` run with `--repo` = the grpc-go
  clone so fragment citations verify against the frozen tree.
* Step 7a (reviewer cross-check) and Part B not run, per instruction.

## Reviewer findings outside scope

None (no traditional review session was run in this pilot).
