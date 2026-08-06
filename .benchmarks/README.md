# Benchmarks — the falsifiable layer

Two kinds of measurement live here, on purpose kept apart:

1. **Tool regression (deterministic, CI-able).** Each `<case>/` is a
   golden mini repository: matrix, catalogue, manifest, sources, and
   `expected/` outputs. `run_benchmarks.py` executes the pack tools
   (sidecar generator, dsc_check, refresh_citations) against the case
   and asserts the expected result — green cases prove the gates pass
   valid input, red cases prove they catch drift. Run it after every
   tool change.

2. **Pilot-convergence probe (manual, per release).** The method's own
   calibration claim: pilot the same component twice in fresh sessions
   and diff the matrices. That is an LLM-in-the-loop measurement; it
   cannot run in CI. Protocol: pick one benchmark case's component,
   run `02-pilot.md` twice in fresh sessions, diff the two
   disposition matrices cell by cell, and record the divergence count
   in the case's `CONVERGENCE.md`. Rising divergence after a prompt
   change is a regression signal for the change.

Current cases: `golden-mini` (valid input, all gates green),
`red-mini` (deliberate violations, the gates must catch them),
`device-connection` (synthetic component for convergence calibration).
