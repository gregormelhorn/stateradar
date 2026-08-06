# pladaria/reconnecting-websocket — Reconnecting WebSocket (TS)

**Date:** 2026-08-06

## Findings

- **1 Critical bug:** Terminal lock leak after maxRetries (QLock stuck, reconnect() bricked).
- **4:8 state gap:** README documents 4 states, code has 8 behaviorally distinct implicit states.
- **14 questions identified**, 13 doctrine lines mapped.
- **Blind diff:** 52% convergent (strong signal), 13% divergent (genuine findings).
- **Methodology impact:** Led to PA-17 (state naming convention) and the first complete Part A + Part B + Diff workflow.
