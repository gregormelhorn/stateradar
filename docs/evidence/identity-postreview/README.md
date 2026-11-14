# Identity check as a final review

This experiment preserves the prior bounded baseline reports and adds a final
review phase. Generic review and identity-focused review start from identical
29-finding gobreaker / 74-finding transfer reports and their unchanged probe
suites. The identity paragraph is the sole difference within each matched pair.
Both transfer arms must add a direct caller-variable-rebinding test. See the
predeclared [protocol](protocol.md) and English [task](prompts/task.md).

The [completed comparison](comparison.md) preserves 29/29 gobreaker and 74/74
transfer findings in both variants. Gobreaker stays at 8/8 benchmark cases; both
transfer runs close the caller-variable test gap and reach 6/6 full test bindings.
Identity's total cost versus generic final review is 1.6% lower on gobreaker and
0.7% higher on transfer. The standard prompt remains unchanged. Raw runs, complete
incremental/strategy costs, independent replays and attributed reviews are retained.

`tools/finding_preservation.py` rejects removal or modification of an original
finding, including its steps and open intent question. New findings append;
qualifications and additional test bindings live in a separate supplement.
Preservation is not semantic endorsement: the final comparison must review every
qualification and any claim that contradicts a retained row. Structural retention
does not prove that an added finding or a test is correct.

`results/preservation-red.txt` records the first seven failing probes against the
unimplemented mechanism; `preservation-green.txt` records their passing result.
Preflight accepts unchanged reports and rejects a changed ordering and changed
immutable source. The standalone public-seam caller-variable reference passes
five race repetitions, with before/after assertions on both accounts and the old
Port alias. This oracle and the answers are excluded from the model inputs and
are never credited as a model-generated test.

Model sessions use the existing isolated pilot transport, complete incremental
Codex accounting and the Flash/Jev ledger. They are bounded final reviews, not
full pilots or blind Part B. Original and additional tests must execute together.
The standard prompt and routing are unchanged during the experiment. Transfer
fixtures are same-author synthetic controls, not independent held-out evidence.

## Reproduction

From the repository root, with a signed-in Codex CLI and existing provider keys:

```sh
.venv/bin/python tools/selftest/test_finding_preservation.py
.venv/bin/python docs/evidence/identity-postreview/scripts/reference.py
.venv/bin/python docs/evidence/identity-postreview/scripts/run.py /tmp/postreview-repeat --source-repo /path/to/gobreaker
```

`freeze.json` binds the prompts, protocol and validators before calls. The runner
refuses to overwrite a measured session. Collection/replay scripts retain results
and refuse to replace existing archived runs. Do not regenerate timestamped
evidence during ordinary CI. Cost totals distinguish incremental review expense
from the original baseline plus review; they do not claim a reused baseline was
executed again. Common implementation and supervising review are unmetered, not
free. See the comparison for measured findings, repair work and cost limitations.

The collector also accepts actual `go test` tool logs when a controller keeps
the complete output there instead of copying it to `analysis/*.jsonl`. This
measurement fix was made outside the model sessions; no model output was repaired.
Its red/green tests distinguish executed commands from log reads and reject zero
discovery, failed tests and skips. Counts of `read-log` calls include first-read
pagination of supplied reports; they are not automatically correction attempts.
