# Summary — channelPool pilot (silenceper/pool)

model routing: on (unevaluated, cascade plan stage 3)

* Component: `channelPool` (channel.go), silenceper/pool @ `6084537e520652192f41aebfd88d822c00b9447a`
* Pack: stateradar @ `da655aa0b80817910a941f94ca8153f50bd2c2fd`, prompt `prompts/02-pilot.md` v1.16
* Models: Flash `deepseek-flash`, Jev pinned `jev-1.14.0` on every Jev call
* Run date: 2026-11-12 (UTC)

## Counts (Step 7)

| item | count |
|---|---|
| states | 7 (2 terminal) |
| events incl. undesired variants | 22 (10 base + 12 UV) |
| interaction pairs | 5 (10 orderings) |
| matrix cells | 154 |
| UNSPECIFIED | 2 |
| accidental ignores | 24 |
| guard groups proven | 6 |
| guard violations | 0 (SYS-invariant z3 checks: 2 violations, SYS-3 and SYS-4) |
| not-formalizable | 2 (external-call, dynamic-state) |
| findings | 23 |
| open questions | 23 |

Primary findings: **Q-01** — Release never wakes or fails Gets waiting in `connReqs`;
they block forever (PA-21 / PA-24, F-07). **Q-02** — Close and internal discards free
capacity without waking a waiter (lost wake-up). **Q-04** — Put and Close after Release
return nil and never close the connection. **Q-05** — Ping after Release (or with no
Ping callback) panics. **Q-09** — no wait timeout; `ErrMaxActiveConnReached` is
unreachable although TestPool_Get expects it.

## Model routing record

| step | command | calls | result |
|---|---|---|---|
| 1 | `draft-verify` README.md | 1 Flash + 1 Jev | 14 claims, 0 citation failures, 14 supported, 12 draft questions |
| 1 | `draft-verify` pool.go | 1 + 1 | 7 claims, 0 failures, 7 supported, 9 questions |
| 1 | `draft-verify` channel_rpc_test.go | 1 + 1 | 34 claims, 0 failures, 30 supported / 4 unclear, 13 questions |
| 1 | `draft-verify` channel.go | 1 Flash, no Jev | **rejected draft**: `LOCAL MODELS: DeepSeek response incomplete (finish_reason=length); usage was recorded` (default `--max-tokens` 4096; 4 096 output tokens; 5 752 µ$) |
| 1 | `draft-verify` channel.go, same task, `--max-tokens 12000` | 1 + 1 | 78 claims, 0 failures, 68 supported / 8 unclear / 2 contradicted, 23 questions |
| 1 | README_ZH_CN.md | not run | Chinese source; the provider documents English as Jev's primary language. Extracted by me |
| 6 | `jev-batch` README.md, 5 ordering checks (O1-O5) | 1 Jev | all `unclear`, scope 0.02-0.05 |
| 6 | `jev-batch` pool.go, 1 ordering check (O6) | 1 Jev | `unclear`, scope 0.03 |
| 8 | `jev-batch` channel.go, 22 claim checks (K1-K22) | 1 Jev | 17 supported, 4 unclear (K1, K3, K11, K21), 1 contradicted (K5) |
| 8 | `jev-batch` channel_rpc_test.go, 4 claims (T1-T4) | 1 Jev | 3 supported, 1 unclear (T3) |
| 8 | `jev-batch` pool.go, 1 claim (P1) | 1 Jev | supported |
| B | `blind --package-only`, twice; `blind` once | 1 Flash | `PART-B COVERAGE: OK (22 events, 10 pair orderings)` |

Totals: drafts 5 (1 rejected), drafted claims 133, citation failures 0, Jev judgments
166 (133 draft claims + 6 orderings + 27 Step-8 claims), draft questions 57 (all
carried into Q-01..Q-23, fold table in open-questions.md).

Questions that the routing added: 4 (Q-20, Q-21, Q-22, Q-23). Each comes from a
control-trace verdict that Jev did not back under routing rules 4-5. Jev removed
nothing.

Every failed or not-run model call:

* channel.go `draft-verify` run 1 — rejected, finish_reason=length (above). Re-run with
  a larger output budget, same task and citation check. Judgment call: rule 8 forbids
  retrying "by loosening the task"; raising the output limit is not listed and I
  treated it as allowed.
* README_ZH_CN.md — `draft-verify` not run (language).
* No Jev check is `failed` or `not run`; every Step-6 scope line carries a Jev result.
* Two shell invocations of mine failed before any request (zsh word splitting):
  `LOCAL MODELS: [Errno 2] No such file or directory: '../pool/pool.go pool'`. No
  ledger entry; the batches were re-run correctly.

Claims kept despite a non-`supported` Jev answer (re-read with the line, rule 2):
channel.go C59 and K5 (`contradicted`, both on "Close returns nil before the decrement
when close is nil" — channel.go:208-211 shows the return precedes `c.openingConns--`;
Jev judged the identical claim C78 `supported`); K1, K3 (grep: no `connReqs` in
Release or Close); K11 (grep: `waitTimeOut` only at channel.go:46); K21
(channel.go:189-192, no identity check); T3 (channel_rpc_test.go:166-189, no
`t.Error`/`t.Fatal`). Dropped: channel.go C22 (Jev `contradicted` was right; the
statement put the return under the lock).

Step-8 re-read: I re-read every cited line of every finding myself (Jev ordered nothing
out). No reclassification removed a finding. Severity: bugs Q-01, Q-02, Q-04, Q-05;
API-contract issues Q-09, Q-14; design observations Q-03, Q-10, Q-12, Q-16, Q-18;
documentation gaps Q-06, Q-07, Q-08, Q-11, Q-13, Q-15, Q-20-Q-23;
`unverifiable-runtime` Q-17 (scheduler-dependent receive race; needs a separate test);
test quality Q-19.

## Deterministic checks (executed)

Final run, all from `/tmp/routed-pilot-EsX9/pool`:

```text
$ python3 domain-analysis/channelPool/check_matrix.py
CHECK MATRIX: OK (7 rows x 22 events)
$ python3 ../pack/tools/gen_analysis_sidecar.py --root . channelPool
OK channelPool: 7 states x 22 events = 154 cells, 23 questions, DRs []
$ python3 domain-analysis/channelPool/merge_sidecar.py
pairs [('P-01a', 'T-P01a'), … ('P-05b', 'T-P05b')]   (10)
guards [('G-01', 'proven'), ('G-02', 'proven'), ('G-03', 'proven'), ('G-04', 'proven'), ('G-05', 'proven'), ('G-08', 'proven'), ('G-06', 'not-formalizable'), ('G-07', 'not-formalizable')]
questions with ODC 23
$ venv/bin/python ../pack/tools/dsc_check.py domain-analysis/channelPool --repo . --model as-is.machine.mmd
DSC CHECK: OK (7 states x 22 events, 154 cells, 8 guard groups)
$ python3 ../pack/tools/check_reachability.py domain-analysis/channelPool
REACHABILITY CHECK: OK (7/7 states reachable from 'Open_Idle', 2 terminal)
$ STATERADAR_PACK=../pack venv/bin/python domain-analysis/channelPool/check_guards.py
group G-01..G-05, G-08: proven; G-06, G-07: not-formalizable (full output: guard-results.txt)
SYS-3 preserved by Close: violation (witness: idle=0, maxActive=0, openingConns=0, waiters=1)
SYS-4 established by Release: violation
$ python3 domain-analysis/channelPool/verify_fragments.py
fragments ok=174 failed=0
```

Red runs on the way (fixed openly):

* `check_reachability.py` first run: FAIL — 5 states unreachable from Open_Idle; Released
  and Released_WaitersStranded "no outgoing transitions and is not marked terminal".
  Causes: I had written two guarded state changes (last idle connection taken; factory
  reaching MaxCap) as `handle`, and I had not declared the terminal states. Fix: the two
  cells now use the guarded-transition form (`transition → … guarded: …; otherwise
  handle`), and `<!-- terminal: Released, Released_WaitersStranded -->` was added. The
  model content did not change; the diagram already had both edges.
* Red probes I ran to make sure green checks can fail: dsc_check with a wrong fragment
  and a wrong line → `DSC CHECK: FAIL` (2 citation errors); verify_fragments.py with a
  wrong line → `failed=1`.

Why `verify_fragments.py` exists: `gen_analysis_sidecar.py` drops the `("fragment")`
part of every citation (0 of 136 cell citations in the generated sidecar carry a
fragment), so dsc_check's fragment verification never runs on a generated sidecar.
The script applies the pack's ±3-line rule to every citation in the markdown.

Tests were not executed: the environment's permission policy denied `go test` on the
downloaded repository. as-is-validation.md is a static walk.

## Part B

`blind` (Flash) — 32 rows (22 events + 10 pair orderings): convergent 15,
convergent-hole 11, divergence 1 (folded into Q-09), artefact 4 (catalogue repaired),
pass-B-blind-spot 1. Vocabulary drift: 7 rows (compound values). No new question.
Before sending, I stripped 16 verbatim code fragments and 3 pass-A references from the
catalogue (details in part-b-diff.md). The blind pass learns the as-is outcome of the
primary finding from the mandatory remembrance semantics, so its agreement on P-01a is
not independent evidence.

## Reviewer findings outside scope

Step 7a was not run (no separate traditional review in this pilot).

## Ledger

Ledger file: `ledger.db` (limit 1 000 000 µ$).

```json
{
  "committed_or_reserved_microdollars": 25038,
  "limit_microdollars": 1000000,
  "calls": [
    {"id": 1, "provider": "deepseek-flash", "amount_microdollars": 1490, "status": "settled"},
    {"id": 2, "provider": "deepseek-flash", "amount_microdollars": 5752, "status": "settled"},
    {"id": 3, "provider": "deepseek-flash", "amount_microdollars": 758, "status": "settled"},
    {"id": 4, "provider": "deepseek-flash", "amount_microdollars": 3698, "status": "settled"},
    {"id": 5, "provider": "jev", "amount_microdollars": 58, "status": "settled"},
    {"id": 6, "provider": "jev", "amount_microdollars": 140, "status": "settled"},
    {"id": 7, "provider": "jev", "amount_microdollars": 379, "status": "settled"},
    {"id": 8, "provider": "deepseek-flash", "amount_microdollars": 7032, "status": "settled"},
    {"id": 9, "provider": "jev", "amount_microdollars": 604, "status": "settled"},
    {"id": 10, "provider": "jev", "amount_microdollars": 105, "status": "settled"},
    {"id": 11, "provider": "jev", "amount_microdollars": 27, "status": "settled"},
    {"id": 12, "provider": "jev", "amount_microdollars": 231, "status": "settled"},
    {"id": 13, "provider": "jev", "amount_microdollars": 113, "status": "settled"},
    {"id": 14, "provider": "jev", "amount_microdollars": 22, "status": "settled"},
    {"id": 15, "provider": "deepseek-flash", "amount_microdollars": 4629, "status": "settled"}
  ]
}
```

Failed or skipped model calls: channel.go draft run 1 (rejected, length; 5 752 µ$
spent, no output used); README_ZH_CN.md draft (not run, language). The calling agent's
own model costs are not in this ledger.
