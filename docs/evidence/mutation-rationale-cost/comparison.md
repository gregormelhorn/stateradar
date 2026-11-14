# Matched gobreaker result

Keep Sol-controlled routed Flash/Jev analysis with selective output as the
standard. Keep the matrix renderer opt-in. This pair shows no cost or overall
quality advantage sufficient to promote it.

Both arms used pack **89a4798**, source
**27b8e2cfc65aacd09abb3968455e4b01df4a83fa**, Sol/medium, ChatGPT login,
selective output, Jev 1.14.0, the same Flash route, $2 provider ledger and
2700-second limit. The fixed order was routed then matrix. See the
[predeclared protocol](protocol.md) and [executable collection](scripts/collect.py).
No intervention or prompt tuning occurred between arms. Both ended normally.

| Measure | Routed | Routed + matrix renderer |
|---|---:|---:|
| Codex credits | 27.48612 | 28.51100 |
| Codex USD equivalent | 1.0994448 | 1.1404400 |
| Flash/Jev conservative ledger USD | 0.0226200 | 0.0276880 |
| Combined USD equivalent | **1.1220648** | **1.1681280** |
| Elapsed minutes | 18.08 | 16.37 |
| Retained-log reads | 11 | 14 |
| Completed MCP calls, including tool errors | 147 | 145 |
| Executed commands with retained exit codes | 136 | 131 |
| Nonzero command exits | 6 | 4 |
| Additional MCP argument errors | 0 | 2 |
| Actual blind requests, excluding package-only | 1 | 1 |
| Runner artifact gates | 7/7 | 9/9 |
| Independently audited blind situations | 126/126 | 178/178 |
| Primary behavioral controls found | 4/4 | 4/4 |

The matrix arm cost **4.1% more**, took **9.4% less elapsed time** and made
three additional retained-log reads. Codex accounts for about 98% of the
conservative total in both arms. Both have complete controller usage and no
unsettled provider reservation. All controller corrections and failed calls
within each run are included; no subsequent model repair was commissioned.
The measured pair totals **$2.2901928 equivalent** on this common basis.

These are rate-based equivalents, not observed account debits. Codex uses the
[official Standard credit rates](https://learn.chatgpt.com/docs/pricing) and an
explicit assumed $0.04/credit conversion. The provider ledger conservatively
uses peak Flash rates with no cache discount. Both runs occurred on Saturday;
with the official off-peak prices and the unretained cache split bounded from
all hits to all misses, combined equivalents are **$1.10993–1.11269 routed**
and **$1.15348–1.15610 matrix**. All four paid Flash responses in each arm
reconcile to its ledger. See [pricing verification](pricing-note.md).
Implementation work, this supervising audit chat and human review are not
metered by the runner. Outstanding semantic review is not priced as free.
This is not the complete invoice for the overall implementation task.

## Reliability and findings

All four predeclared cases are present in both reports and have behavior
probes: stale completion accounting, duplicate completion, an abandoned
HalfOpen allowance, and callback reentry. The independent controls passed
five race-detector repetitions before the pilots were reviewed. Both also
report policy-panic double accounting, notification-panic replacement,
Goexit abandonment, lazy expiry, and same-caller overlapping admissions.

Post-run, each unchanged pilot suite was repeated five times under the race
detector in a disposable copy. Both baselines pass. Disabling the source's
generation check then causes five failures in the specific stale-report test
in each suite. This is a supplementary diagnostic, not a predeclared primary
control or a general mutation score. The matrix pilot independently strengthened
its initially weaker stale-report probe before finishing (retained log 113);
no supervising intervention supplied that case. Both final suites detect the
fault. Results: [routed](stale-diagnostic/routed/result.json),
[matrix](stale-diagnostic/matrix/result.json).

The first diagnostic setup encountered macOS `/var` versus `/private/var`
overlay aliases and discovered zero tests. The diagnostic correctly refused to
score it. The corrected path is resolved before use; the original empty-discovery
output remains under `stale-diagnostic/routed-setup-failure/`.

Both lack the concrete serialized wrapper-reassignment outcome found in the
older reference. The separately repeated public-seam control confirms that an
old callback can write to the replacement breaker after `*a = *b`. Routed Q-08
states the original-breaker binding too broadly. Matrix Q-17 correctly says the
closure captures the wrapper, but does not trace reassignment to its consequence.
These are analysis/scope gaps, not new owner decisions or runtime fixes. They
prevent a claim of exhaustive finding equivalence with the older reference.
The full [coverage comparison](coverage.md) distinguishes grouping from actual
omission and from unequal test depth.

Both full upstream race runs retained a failure in TestCustomCircuitBreaker:
a private Counts read in the test races with a background request. Their final
isolated probe suites pass with race detection. Passing artifact gates do not
turn that upstream test failure into green. Neither existing tests nor library
code were changed.

## Repair work and evidence limits

Routed corrected a missing example path, matrix formatting, a rejected source
citation and an unsupported checker help call. Its six nonzero commands also
include an empty search and the upstream race finding. Matrix's four nonzero
commands include an early matrix check before questions existed, the upstream
race finding, unsupported help, and a sidecar reader that assumed keyed cells.
It additionally made two invalid read-log range requests exceeding the explicit
100-line limit. These argument errors are included in its 14 reads and cost.
Nonzero exits are not interchangeable with runner defects or domain findings.

The renderer reproduces the matrix exactly. Strict sidecar regeneration in a
fresh copy is byte-identical for both arms, and tracked source diffs are empty.
Blind classification audits reject a deliberately removed situation and confirm
126/126 and 178/178 classifications. Code-derived catalogue content still limits
blind independence; both reports disclose it. The fixed-order single pair is
screening evidence, not a reliability percentage or a causal estimate of renderer
savings. Models differ: 3 states/105 cells/30 pair orderings versus
4 states/120 cells/56 orderings. Broader validation should match behavioral
obligations, not only model settings or raw question counts.

The old Pool run's missing Codex balance remains **unknown**. No new Pool attempt,
retrospective substitute or cost estimate from gobreaker was used.

Full observations, including failed commands, remain under `runs/` with hashes.
The two raw archives are exempt from Git whitespace lint so numbered source
listings and model output stay byte-exact; code and authored reports remain
checked. No captured evidence was normalized to make an analysis gate pass.
