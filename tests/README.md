# Tests

Two kinds of tests live here:

## 1. Tool regression (`golden-mini`, `red-mini`)

Deterministic, CI-able. Each case is a golden mini repository:
matrix, catalogue, manifest, sources, and expected outputs.
`tools/run_tool_tests.py` executes the pack tools against the case
and asserts the expected result — green cases prove the gates pass
valid input, red cases prove they catch drift.

## 2. Oracle benchmark evidence (`benchmarks/`)

Evidence archive with expected findings per confirmed upstream bug.
`tools/run_benchmark.py` validates that pre-generated matrices
still produce the expected UNSPECIFIED cells and questions.
3/3 Oracle-confirmed, 4/4 total confirmed.

See `benchmarks/` for the full evidence archive.

## 3. Convergence calibration (`device-connection/`)

Protocol for two-pass pilot calibration on the synthetic Device
Connection component. Run the pilot twice in independent sessions,
diff the matrices, record divergence rate in CONVERGENCE.md.
