# snapview/tungstenite-rs — RFC 6455 WebSocket (v0.30.0)

**Date:** 2026-08-06

## Findings

- **0 bugs.** RFC 6455 compliance confirmed for all 7 design observations.
- **RFC compliance matrix:** Every (State, Event) cell traced to RFC 6455 section.
- **3 API consistency questions** (Q-01 Close in ClosedByPeer, Q-02 fragmented close, Q-03 pong during close).
- **Methodology impact:** Demonstrated statechart as compliance evidence.
