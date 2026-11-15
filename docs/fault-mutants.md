# Fault-mutant execution contract

Run `python tools/check_fault_mutants.py <analysis-dir>` after verifying generated
variant drift. Execution uses pristine component copies for baseline and every
mutant. The runner never treats variant generation or a projection declaration
as evidence that the suite can observe the fault.

## Required execution configuration

`fault-mutants.json` retains `formatVersion: 1`, the argv-array `testCommand`
with one `{analysis_dir}` placeholder, `workingDirectory`, `timeoutSeconds`,
and named `mutants` (id, fault, cell, target, variant). It now also requires
`expectedCells`: a positive integer giving the suite's completed representative
cell count. Migration is explicit: semaphore uses 34 (four documented contract
limits excluded), golden-mini 24. Missing, boolean, fractional or nonpositive
values are configuration errors; the runner does not infer completeness from
an arbitrarily short baseline. Mutant IDs must be unique directory names.

The baseline must exit 0, report exactly the declared nonzero count, and report
no failures. Otherwise the invocation is BLOCKED before mutations and no
kill-rate denominator is reported. Each mutant must report exactly one numeric
`CELL SUITE: <n> cells checked, <m> failed` summary and one unique
`CELL FAIL <state> x <event>` per failed cell. Malformed failure markers,
duplicate summaries/cells and inconsistent counts are invalid. The component
suite must tie these markers to real discovery/execution; the generic runner
checks the protocol, not the honesty of arbitrary test programs.

| Completed result | Mutant verdict |
|---|---|
| exit 0, expected cells, zero failures | SURVIVED |
| exit 1, expected cells, declared cell among failures | KILLED |
| wrong cell only, partial/empty execution, inconsistent exit/counts, timeout or launch error | BLOCKED |

A fault may legitimately fail several cells. It must fail the named cell;
unrelated failures never increase the killed count. The special semaphore
comparison uses the same classifier as the general runner.

## Executed projection dependencies

The runner reads the existing `mutant-generation.json` when present. There is
one source of projection metadata, not a second copy in `fault-mutants.json`:

```json
{
  "projections": {"capacity": {"kind": "public-try-acquire", "provenBy": "capacity-canary"}},
  "bindings": [
    {"id": "cancel-leak", "requiresProjection": "capacity"},
    {"id": "capacity-canary", "requiresProjection": "capacity"}
  ]
}
```

This excerpt shows only dependency fields; generated bindings also retain their
source/replacement fields. `provenBy` names an existing declared mutant with its
own target cell. The runner executes it first and caches its result only for
this invocation. Only KILLED authorizes dependents. A SURVIVED or BLOCKED canary
blocks them without copying, modifying or executing their component. Unrelated
mutants continue. Shared canaries execute once and count once, independent of
list order. Dependency chains are evaluated transitively.

A canary's self-reference bootstraps its own projection through execution. It
is not a declaration of success. Other cycles, undeclared required projections,
missing/unknown `provenBy`, and unknown/duplicate binding IDs are configuration
errors before baseline execution. Configurations without projection bindings
still run their independent mutants; they claim no executed projection proof.

After a valid baseline, each declared mutant belongs to exactly one of KILLED,
SURVIVED or BLOCKED, including canaries and skipped dependents. The retained
`errors` field counts timeout/launch errors **within BLOCKED** for diagnosis;
it is not another set of mutants to add to the denominator. Exit 0 requires all
mutants KILLED. Invalid configuration exits 2; a failed baseline, surviving
mutant or blocked outcome exits 1.

The existing generator still checks declarations and generated-source drift.
Always run it as well: the execution runner does not claim that a stored variant
is up to date merely because its tests produced a valid verdict.

## Late-completion adapters

The [late-completion oracle](late-completion.md) implements this verdict protocol
for declared scenario traces. `expectedCells` is the number of distinct scenario
cell references, regardless of repeated execution. The addrConn reference has
three such scenarios, four independent projection canaries and two F-04 mutants.
Its weak oracle still executes complete traces, but checks only the immediate
terminal state. A surviving weak canary blocks dependent mutations in the same
general runner; a separate direct weak replay demonstrates survival of each fault.
