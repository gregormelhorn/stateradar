# jd/tenacity — Retry Controller (v9.2.0)

**Date:** 2026-08-06

## Findings

- **0 bugs.** Most popular project analyzed (8.7k stars), active maintenance.
- **Action-pipeline state model:** 12 loop-phase states documented.
- **7 design observations:** TryAgain bypasses retry evaluation, reraise flag, retry_error_callback.
- **Issue #185:** Statechart terminal-state table used as v5→v7 migration guide.
- **Methodology impact:** Led to PA-19 (runtime boundary) and PA-20 (API contract vs state machine).
