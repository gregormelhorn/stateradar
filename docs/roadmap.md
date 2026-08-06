# Roadmap (post-v1.33)

## 1. CONVERGENCE.md — calibration data

**Status:** Framework ready. `tests/device-connection/CONVERGENCE.md`
has the protocol and template. Needs two independent pilot runs on the
synthetic Device Connection component. Run the pilot twice in fresh
sessions, diff the matrices, record the divergence rate. Repeat per
release to establish a baseline.

## 2. Synthetic example ("Device Connection")

**Status:** ✅ Done. `examples/device-connection/` contains a 130 LOC
Python component, a README with 9 requirements, and a full Part A
analysis with Mermaid statechart and critical finding Q-02 (FAILED
backdoor via disconnect).

## 3. XState / Semantic Analysis

**Status:** ✅ Minimal version shipped. `tools/check_reachability.py`
verifies all states are reachable from the initial state and that
terminal states are marked. Selftest red case, CI-wired on golden-mini.
Full reachability over hierarchy/parallel regions is deferred until
needed — the `formats/analysis.schema.json` carries enough data.
