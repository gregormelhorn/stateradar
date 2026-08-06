# recws-org/recws — Reconnecting WebSocket Client

**Date:** 2026-08-06
**Issues filed:** #64 (Shutdown panic), plus comparison against existing tracker

## Key findings

- **3 Critical bugs:** `log.Fatalf` kills process, keepalive CPU busy-spin, Shutdown nil-panic
- **7 total bugs:** plus normal-close indistinguishable, infinite reconnect, Dial blocks, rand.Seed deprecated
- **Issue tracker coverage:** 7/7 bugs at least partially covered by existing issues
- **2 novel Critical bugs:** Issues #64 filed (Shutdown panic confirmed by code review)
