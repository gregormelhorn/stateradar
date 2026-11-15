# channelPool pilot — summary

model routing: on (unevaluated, cascade plan stage 3)
routing variant: flash-writes

Pilot agent model: Claude Sonnet 5.5 (claude-sonnet-5-5), by the coordinator's choice (cheaper model).
Pack: stateradar fc677c6a6d8af5c582faf1c5e107a4a8dc4d69d0 (branch flash-writes-cells), prompt 02-pilot.md v1.21.
Target: github.com/silenceper/pool 6084537e520652192f41aebfd88d822c00b9447a, component channelPool (channel.go).

step 0 start: 2026-11-13T10:10:04Z
step 1 start: 2026-11-13T10:10:21Z (draft-verify launched; first launch failed on my shell wrapper, drafts started 10:10:31Z)
step 4 start: 2026-11-13T10:29:36Z (draft-cells base+uv launched; steps 2/3 artifacts are written after, see timing.md)
step 2 start: 2026-11-13T10:30:30Z (approximate; model file written after the matrix)
step as-is tests start: 2026-11-13T10:34:00Z
step 5 start (invariants/doctrine): 2026-11-13T10:39:23Z
step 8 start: 2026-11-13T10:40:00Z
step part-B package start: 2026-11-13T10:40:25Z
step 3 start: 2026-11-13T10:31:12Z (approximate, from timing.md)
step 5 start: 2026-11-13T10:37:34Z
step 6 start: 2026-11-13T10:38:55Z
step 7 start: 2026-11-13T10:36:30Z (questions were written before the invariants file)
step 7a: not run (no traditional review exists)
step 8 start: 2026-11-13T10:40:00Z
part B start: 2026-11-13T10:40:25Z

(Step times were written when each step started; steps 2, 3 and 7 ran in a different order from the prompt's numbering, as `timing.md` shows. Wall-clock per step and per call: `timing.md`, outside the repository.)

## Counts

states 8 / events incl. undesired variants 11 (6 base + 5 UV) / interaction pairs 12 orderings (6 pairs) / matrix cells 88 / UNSPECIFIED 0 / accidental ignores 34 (hole cells, each with a Q) / one crash cell (Closed x Ping: `handle crash`) / guard groups proven 5 / guard violations 0 / not-formalizable 3 / findings: 5 SYS violations (SYS-01, 02, 05, 06, 07), 12 lint rows (11 flagged, 1 no finding) / open questions 24 (all OPEN).

## Checker outputs (executed)

* `gen_analysis_sidecar.py --strict`: `OK channelPool: 8 states x 11 events = 88 cells, 24 questions, DRs []`
* `check_matrix.py`: `CHECK MATRIX: OK (8 rows x 11 events)`
* `dsc_check.py ... --model as-is.machine.mmd`: `DSC CHECK: OK (8 states x 11 events, 88 cells, 8 guard groups)`
* `check_reachability.py`: `REACHABILITY CHECK: FAIL - state 'Open_Waiting_IdleAvailable' is unreachable from initial state 'Open_IdleAvailable'`
* `check_guards.py`: five groups proven, three not-formalizable (guard-results.txt).

**Known limit of check_reachability (recorded, targets not reordered):** `Open_Waiting_IdleAvailable` is reached only by an interleaving of two events (Get overlapped by Put, pair P-04a), not by a single event, so no `transition` cell can name it. It has a documenting edge in the diagram; the matrix cells leaving it are real. dsc_check (model sync) is green.

## Model-routing record

* `model routing: on` / `routing variant: flash-writes` (top of file). Ledger file: `ledger.db`. Every model call went through `tools/local_models.py --ledger <ledger.db>`; every Jev call pinned `--model jev-1.14.0`.
* Pilot agent model: Claude Sonnet 5.5, as the coordinator and Gregor asked.
* Ledger `status` (runs/status-final.json): committed_or_reserved 40,396 of 1,000,000 microdollars, 20 calls, all settled.
* Failed or skipped model calls: none. Rejected Flash drafts: none (5 draft-verify, 2 draft-cells, 1 flash for tests, 1 blind: all finished with `finish_reason stop`). Provider errors: none. Jev control-trace checks: 4 answered (all `unclear`, scope 0.04-0.14); no `failed` or `not run`.
* Tool errors seen: (1) my own wrapper call failed with exit 127 (`../run.sh: line 6: python3 ../stateradar/tools/local_models.py --ledger ../ledger.db: No such file or directory`; no API call was made); (2) `dsc_check.py` reported every event as missing gate-type and upstream-guard annotation and every base event x category as missing coverage, because `gen_analysis_sidecar.py` matches the heading with `^## Event annotations\s*$` and my first catalogue had the suffix ` (observed in code)` on it. The prompt text names the labelled headings only for the Part-B copy; it does not say the sidecar needs the plain heading. Fixed by plain headings.
* Dependency install: `python3 -m venv venv && pip install z3-solver jsonschema pyyaml` (the system python lacked z3; no change to the pack or to the analysed repo).

## Draft measurements (variant point 4)

* Step 1: 146 claims drafted (channel.go 48, pool.go 8, channel_rpc_test.go 41, README.md 29, README_ZH_CN.md 20); 0 citation failures; Jev: 136 supported, 9 unclear, 1 contradicted (the contradicted one, "Close returns nil when c.close is nil", is true at channel.go:208-210; kept and re-checked in step 8, where Jev again said `contradicted`, confidence 0.09, for the same fact). 86 draft questions, each disposed in extraction.md. Step-1 items added by the agent: 9 (A1-A9).
* Cells: 88 drafted in 2 calls, 0 cells with problems, 0 missing, 0 second cells; Jev choices on cells: supported 78, unclear 9, contradicted 1.
* Tests: 19 drafted by Flash (578 lines); 2 changed by the agent; compiled and vetted on first try.
* Step 8: 33 claim checks in 3 batches (channel.go 28, channel_rpc_test.go 3, README.md 2): 32 supported, 1 contradicted (L209, see above); every cited line was also re-read.

### draft_cells.py compare output

```json
{
  "by_jev_choice": {
    "unclear": {
      "unchanged": 3,
      "changed": 6,
      "dropped": 0
    },
    "supported": {
      "unchanged": 42,
      "changed": 36,
      "dropped": 0
    },
    "contradicted": {
      "unchanged": 0,
      "changed": 1,
      "dropped": 0
    }
  },
  "changed_fields": {
    "disposition": 39,
    "target": 8,
    "citation": 2
  },
  "drafted": 88,
  "missing_in_draft": 0,
  "second_cells_in_draft": 0,
  "final_cells_not_drafted": [],
  "cells": [
    {
      "state": "Open_IdleAvailable",
      "event": "Get",
      "jev": "unclear",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleAvailable",
      "event": "Put",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition",
        "target"
      ]
    },
    {
      "state": "Open_IdleAvailable",
      "event": "Close",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleAvailable",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleAvailable",
      "event": "Release",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleAvailable",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "Get",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "Put",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "Close",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "Release",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "Get",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "Put",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "Close",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "Release",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "Get",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "Put",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "Close",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition",
        "target"
      ]
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "Release",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "Get",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition",
        "target"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "Put",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "target"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "Close",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition",
        "target"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "Release",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "Get",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "Put",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "target"
      ]
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "Close",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "Release",
      "jev": "unclear",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "Get",
      "jev": "unclear",
      "outcome": "changed",
      "fields": [
        "target"
      ]
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "Put",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "target"
      ]
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "Close",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "Ping",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "Release",
      "jev": "unclear",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Closed",
      "event": "Get",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Closed",
      "event": "Put",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "Close",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "Ping",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "Release",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Closed",
      "event": "Len",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleAvailable",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleFull",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Closed",
      "event": "UV-Conn-nil",
      "jev": "supported",
      "outcome": "unchanged",
      "fields": []
    },
    {
      "state": "Open_IdleAvailable",
      "event": "UV-Put-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_IdleFull",
      "event": "UV-Put-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "UV-Put-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "UV-Put-dup",
      "jev": "unclear",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "UV-Put-dup",
      "jev": "unclear",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "UV-Put-dup",
      "jev": "unclear",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "UV-Put-dup",
      "jev": "unclear",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "UV-Put-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_IdleAvailable",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_IdleFull",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "UV-Close-dup",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition",
        "citation"
      ]
    },
    {
      "state": "Open_IdleAvailable",
      "event": "UV-Put-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_IdleFull",
      "event": "UV-Put-foreign",
      "jev": "unclear",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "UV-Put-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "UV-Put-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "UV-Put-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "UV-Put-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "UV-Put-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "UV-Put-foreign",
      "jev": "contradicted",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_IdleAvailable",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_IdleFull",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_BelowCap",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_NoIdle_AtCap",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_AtCap",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_BelowCap",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Open_Waiting_IdleAvailable",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition"
      ]
    },
    {
      "state": "Closed",
      "event": "UV-Close-foreign",
      "jev": "supported",
      "outcome": "changed",
      "fields": [
        "disposition",
        "citation"
      ]
    }
  ]
}
```

Reading of the compare: 45 of 88 drafted cells changed (39 disposition, 8 target, 2 citation, some in more than one field), 43 unchanged, 0 dropped, 0 not drafted. 32 of the 39 disposition changes are the agent re-deciding `handle`/`reject` as `ignore (accidental)` with a question on the undesired-variant columns, where nothing in the code detects the anomaly; that is a judgment, not a correction of what the code does. Jev's `supported` cells changed 36 of 78 times.

## Ledger status output

```json
{
  "committed_or_reserved_microdollars": 40396,
  "limit_microdollars": 1000000,
  "calls": [
    {
      "id": 1,
      "provider": "deepseek-flash",
      "amount_microdollars": 5816,
      "status": "settled"
    },
    {
      "id": 2,
      "provider": "deepseek-flash",
      "amount_microdollars": 2598,
      "status": "settled"
    },
    {
      "id": 3,
      "provider": "deepseek-flash",
      "amount_microdollars": 4356,
      "status": "settled"
    },
    {
      "id": 4,
      "provider": "deepseek-flash",
      "amount_microdollars": 801,
      "status": "settled"
    },
    {
      "id": 5,
      "provider": "deepseek-flash",
      "amount_microdollars": 2172,
      "status": "settled"
    },
    {
      "id": 6,
      "provider": "jev",
      "amount_microdollars": 66,
      "status": "settled"
    },
    {
      "id": 7,
      "provider": "jev",
      "amount_microdollars": 177,
      "status": "settled"
    },
    {
      "id": 8,
      "provider": "jev",
      "amount_microdollars": 219,
      "status": "settled"
    },
    {
      "id": 9,
      "provider": "jev",
      "amount_microdollars": 378,
      "status": "settled"
    },
    {
      "id": 10,
      "provider": "jev",
      "amount_microdollars": 439,
      "status": "settled"
    },
    {
      "id": 11,
      "provider": "deepseek-flash",
      "amount_microdollars": 5367,
      "status": "settled"
    },
    {
      "id": 12,
      "provider": "deepseek-flash",
      "amount_microdollars": 4371,
      "status": "settled"
    },
    {
      "id": 13,
      "provider": "jev",
      "amount_microdollars": 450,
      "status": "settled"
    },
    {
      "id": 14,
      "provider": "jev",
      "amount_microdollars": 518,
      "status": "settled"
    },
    {
      "id": 15,
      "provider": "deepseek-flash",
      "amount_microdollars": 6236,
      "status": "settled"
    },
    {
      "id": 16,
      "provider": "jev",
      "amount_microdollars": 94,
      "status": "settled"
    },
    {
      "id": 17,
      "provider": "jev",
      "amount_microdollars": 107,
      "status": "settled"
    },
    {
      "id": 18,
      "provider": "jev",
      "amount_microdollars": 50,
      "status": "settled"
    },
    {
      "id": 19,
      "provider": "jev",
      "amount_microdollars": 265,
      "status": "settled"
    },
    {
      "id": 20,
      "provider": "deepseek-flash",
      "amount_microdollars": 5916,
      "status": "settled"
    }
  ]
}
```

## Part B

See part-b-diff.md. PART-B INDEPENDENCE line: absent (Part B marked 0 rows `as-is:`). 23 rows: 17 convergent-hole, 5 divergence (all folded into existing questions), 1 artefact (catalogue repaired after the run, Part B not re-run).

## Reviewer findings outside scope (test quality)

channel_rpc_test.go:54 and :123 messages do not match their assertions; TestPoolConcurrent and TestPoolConcurrent2 assert nothing; `wg.Add(1)` is called inside a goroutine (:213-214); TestPoolWriteRead never returns its connection; TestPool_Get hangs against the current code (Q-21).

## Level

Below L3 (no cell tests for the matrix; only 19 as-is tests that observe selected claims). The standing instruction's "green means conforming" does not apply to this component.
