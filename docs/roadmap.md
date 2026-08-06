# Roadmap (post-v1.33)

## 1. CONVERGENCE.md — calibration data

**Status:** Framework ready. `.benchmarks/device-connection/CONVERGENCE.md`
has the protocol and template. Needs two independent pilot runs on the
synthetic Device Connection component. Run the pilot twice in fresh
sessions, diff the matrices, record the divergence rate. Repeat per
release to establish a baseline.

## 2. Synthetic example ("Device Connection")

**Status:** ✅ Done. `examples/device-connection/` contains a 130 LOC
Python component, a README with 9 requirements, and a full Part A
analysis with Mermaid statechart and critical finding Q-02 (FAILED
backdoor via disconnect).

## 3. XState / Semantic Analysis (deferred)

**Status:** Deferred. `formats/analysis.schema.json` carries enough
data for an eventual reachability checker (`tools/check_reachability.py`).
No prompt changes needed — the schema already supports it. Priority
is low: the current method finds bugs without semantic analysis.
