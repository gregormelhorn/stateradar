# Independent review record

The reviewing session was Codex agent `/root/independent_review`, distinct from
the catalog author. It examined source/contract fragments, the retained test
code and outputs, wrote `review.json`, and subsequently reviewed each new
baseline finding in `../runs/review-NNN.json`. It is not a human reviewer and
made no domain-policy decision. The catalog author checked the disputed
interpretations and the complete reviews are replayed by the deterministic audit.

The reviewer caught an erroneous initial claim that three Gobreaker runs all
used the fixed seed: only call 000 did; calls 004 and 008 used different GEPA
proposals. It also required the Pool cases to specify an open pool, no expiry,
no interfering consumer except the stated later Get, and the first/sole waiter
for the handoff. These corrections were made before the catalog was frozen.

Recorded environment: Go 1.27.3, darwin/arm64; every successful named case has
five `run` and `pass` events plus a package pass. The timer archive includes the
parent and four subtests in each repetition. The following commands document the review and provide equivalent reproduction
commands. Temporary paths are from the original session; `go test -C` is
equivalent to changing into that working directory. Output redirections are
omitted here except where essential:

```text
env -u GODEBUG go test -C /tmp/gepa-independent-controls -race -count=5 -timeout=20s -json ./...
go test -C /tmp/stateradar-mutation-cost-routed/selective/pool -overlay /tmp/gepa-independent-b05-overlay.json -race -count=5 -timeout=30s -run '^(TestBenchmarkWrapperReassignment|TestBenchmarkOutstandingAllow)$' -json .
go test -C /tmp/stateradar-mutation-cost-routed/selective/pool -overlay /tmp/gepa-independent-rebinding-overlay.json -race -count=5 -timeout=30s -run '^TestIndependentCallerRebinding$' -json .
GODEBUG=panicnil=1 go test -C docs/evidence/gepa-discovery/reference -race -count=5 -timeout=20s -run '^TestWaitGroupGoPanicNilLegacy$' -json ./...
go test -C docs/evidence/gepa-discovery/reference -race -count=5 -timeout=20s -run '^TestWaitGroupSynctestOutsideWait$' -json ./...
python3 -c 'from pathlib import Path; import runpy; runpy.run_path("docs/evidence/gepa-bounded/scripts/reference.py")["run"](Path("/tmp/gepa-independent-timer-overlap.jsonl"))'
python3 /tmp/gepa-independent-pool/reproduce.py /tmp/stateradar-v124-repeat-get.Bvb1Kl/pool
python3 /tmp/gepa-independent-pool/reproduce.py /tmp/stateradar-v124-repeat-get.Bvb1Kl/pool --control
```

For the Go reference and initial Gobreaker replays, the literal commands ran
inside their respective working directories (rather than using `-C`), with
stdout redirected to the corresponding JSONL files. For example, the legacy
control ran from `docs/evidence/gepa-discovery/reference` with
`GODEBUG=panicnil=1 go test -race -count=5 -timeout=20s -run '^TestWaitGroupGoPanicNilLegacy$' -json ./... > /tmp/gepa-independent-panicnil.jsonl`.
The JSON Pool replay used the retained five-repeat script and redirected stdout
and stderr to the archived `gepa-independent-pool-*` files.

The last command is intentionally red: the test-only idle recheck makes the
first Get return early and fails the named assertion. An initial Gobreaker
attempt failed because the overlay fixture path was wrong; the failed log is
retained and the corrected overlay run supplies evidence. No failure was
silently counted as a passing behavioral test.

`pool-json-reproduce.py` is the reviewer's retained script and expects a sibling
file named `p04a_test.go`. Its matching test is archived as
`pool-p04a_test.go.txt` to avoid accidental Go test discovery; when replaying,
copy the script and test into a temporary directory under the expected names,
then pass a Pool git checkout containing pinned SHA `6084537e520652192f41aebfd88d822c00b9447a`.
The Gobreaker overlay JSON files similarly record original absolute temporary
paths; regenerate them for a different checkout rather than treating them as
portable.

`TestDefaultPanicNilRecoverIsNonNil` deliberately removes `GODEBUG`; the separate
legacy probe explicitly uses `GODEBUG=panicnil=1`. The Cond time-bound assertion
is an observation of nonreturn over a bounded interval, not a proof of indefinite
blocking. The contractual or intended behavior for wrapper copying, Pool fairness
and outside-bubble Wait remains OPEN.
