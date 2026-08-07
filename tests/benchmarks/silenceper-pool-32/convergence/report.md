# Ensemble Convergence Report

## Runs

- **Run 1 (code-informed)**
  States: 5, Events: 10
- **Run 2 (independent)**
  States: 4, Events: 8

## Structural divergence (not in cell rate)

- State granularity divergence: 'initializing' — run-1: Initializing; run-2: absent
- Event presence divergence: 'Close' — run-1: absent; run-2: Close
- Event presence divergence: 'E_Close' — run-1: E_Close; run-2: absent
- Event presence divergence: 'E_Close_Nil' — run-1: E_Close_Nil; run-2: absent
- Event presence divergence: 'E_Get' — run-1: E_Get; run-2: absent
- Event presence divergence: 'E_Len' — run-1: E_Len; run-2: absent
- Event presence divergence: 'E_Put' — run-1: E_Put; run-2: absent
- Event presence divergence: 'E_Put_Nil' — run-1: E_Put_Nil; run-2: absent
- Event presence divergence: 'E_Release' — run-1: E_Release; run-2: absent
- Event presence divergence: 'FactoryFailure' — run-1: absent; run-2: FactoryFailure
- Event presence divergence: 'FactorySuccess' — run-1: absent; run-2: FactorySuccess
- Event presence divergence: 'Get' — run-1: absent; run-2: Get
- Event presence divergence: 'I_FactoryFail' — run-1: I_FactoryFail; run-2: absent
- Event presence divergence: 'I_IdleTimeout' — run-1: I_IdleTimeout; run-2: absent
- Event presence divergence: 'I_PingFail' — run-1: I_PingFail; run-2: absent
- Event presence divergence: 'IdleTimeout' — run-1: absent; run-2: IdleTimeout
- Event presence divergence: 'PingFailure' — run-1: absent; run-2: PingFailure
- Event presence divergence: 'Put' — run-1: absent; run-2: Put
- Event presence divergence: 'Release' — run-1: absent; run-2: Release

## State alignment (case-insensitive exact match)

Aligned states: 4

- `active_hasidle` ← Active_HasIdle, Active_HasIdle
- `active_idleexhausted_atcapacity` ← Active_IdleExhausted_AtCapacity, Active_IdleExhausted_AtCapacity
- `active_idleexhausted_undercap` ← Active_IdleExhausted_UnderCap, Active_IdleExhausted_UnderCap
- `released` ← Released, Released

## Cell convergence (aligned grid only)

Aligned grid: 4 states × 0 events

| Metric | Value |
|---|---|
| Total aligned cells | 0 |
| Convergent | 0 |
| Disposition-divergent | 0 |
| Target-divergent | 0 |
| Hole noise (non-behavioural) | 0 |
| **Behavioural convergence rate** | **n/a (no aligned cells)** |
| New questions raised | 0 |
| Structural findings | 19 |
