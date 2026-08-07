# Invariants and lint findings — silenceper/pool `channelPool`

## NAT invariants

- NAT-01 — A caller returns or closes one genuine borrowed connection exactly
  once and does not both `Put()` and `Close()` one borrow. The pool does not
  track lease identity, duplicate returns, or duplicate closes. [DR-002, DR-006]

## SYS invariants

- INV-01 — `openingConns >= 0` while the DR-002/DR-006 valid-caller contract
  holds. [DR-006]

### INV-01 state check

| state | result | basis |
|---|---|---|
| `Active_HasIdle` | holds under NAT | Valid callers do not duplicate or forge a return/close. [DR-002, DR-006] |
| `Active_IdleExhausted_UnderCap` | holds under NAT | Close accounting relies on NAT-01; no clamp is introduced. [DR-006] |
| `Active_IdleExhausted_AtCapacity` | holds under NAT | Waiting does not create a second ownership identity. [DR-002, DR-006] |
| `Released` | not mutable; terminal no-op | No new open counter is created by terminal Put. [DR-003] |

## Resolution lint checklist

| lint | result |
|---|---|
| terminal waiter outcome | Terminal Release resolves queued Get() calls with `ErrMaxActiveConnReached`. [DR-001] |
| waiter-path validation | Queued delivery receives configured Ping validation before return. [DR-004] |
| Factory capacity accounting | Factory error does not consume capacity; Factory does not run from the at-capacity waiter branch. [DR-005] |
| ownership tracking | No runtime lease identity, duplicate-close guard, or counter clamp is introduced. [DR-002, DR-006] |
| remaining undesired variants | Get variants remain Q-UV-01; Release variants remain Q-07. |
