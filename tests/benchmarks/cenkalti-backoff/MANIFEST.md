# cenkalti/backoff — Retry Controller (v7.0.0)

**Date:** 2026-08-06

## Findings

- **0 bugs.** Well-maintained, active project (70+ issues, 20+ PRs).
- **5 terminal states documented** as API reference — used directly in issue #185 to help a user migrate v5→v7.
- **Design observations:** Default MaxElapsedTime=15min surprising (confirmed by issue #159), Permanent+RetryAfter priority undocumented.
- **Methodology impact:** Led to PA-18 (terminal states) and loop-phase extraction.
