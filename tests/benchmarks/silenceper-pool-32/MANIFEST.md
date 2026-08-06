# silenceper/pool — Connection Pool Release Hang

**Issue:** [#32](https://github.com/silenceper/pool/issues/32)
**PR:** [#33](https://github.com/silenceper/pool/pull/33) (open, unmerged since 2021)
**Commit:** main (HEAD)
**Date:** 2026-08-06
**Oracle:** Confirmed by existing issue. PR unmerged for 5 years.

## Primary finding

**Missing transition:** `PoolReleased → WaitingCallersUnblocked`

`Release()` at `channel.go:197-213` closes the idle connection channel but
does NOT close the `connReqs` waiter channels. Goroutines blocked in `Get()`
on `<-req` are never unblocked. The pool terminates but waiting callers
remain blocked forever.

**Defect class:** Pool terminal, waiter lifecycle never notified (PA-21) — F-07 lifecycle coupling

ODC: fault F-07 (lifecycle coupling; secondary F-20 blocked progress after terminal event), trigger: doctrine mapping (PA-21)

## StateRadar output

- **Lifecycle disagreement (PA-21):** Pool lifecycle terminates without
  synchronizing with Waiter lifecycle.
- **Fix direction:** In `Release()`, iterate `connReqs` and close each channel.
