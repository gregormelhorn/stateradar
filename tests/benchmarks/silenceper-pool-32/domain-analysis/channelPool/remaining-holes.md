# Remaining holes — silenceper/pool `channelPool`

## Q-UV-01: undesired Get variants

- `Active_HasIdle × UV-Get-commission` → Q-UV-01
- `Active_HasIdle × UV-Get-value` → Q-UV-01
- `Active_IdleExhausted_UnderCap × UV-Get-commission` → Q-UV-01
- `Active_IdleExhausted_UnderCap × UV-Get-value` → Q-UV-01
- `Active_IdleExhausted_AtCapacity × UV-Get-commission` → Q-UV-01
- `Active_IdleExhausted_AtCapacity × UV-Get-value` → Q-UV-01
- `Released × UV-Get-commission` → Q-UV-01
- `Released × UV-Get-value` → Q-UV-01

## Q-07: undesired Release variants

DR-001 decides only `Active_IdleExhausted_AtCapacity × Release`; it does not
cover undesired Release variants.

- `Active_HasIdle × UV-Release-duplication` → Q-07
- `Active_HasIdle × UV-Release-out-of-order` → Q-07
- `Active_HasIdle × UV-Release-contradiction` → Q-07
- `Active_HasIdle × UV-Release-commission` → Q-07
- `Active_IdleExhausted_UnderCap × UV-Release-duplication` → Q-07
- `Active_IdleExhausted_UnderCap × UV-Release-out-of-order` → Q-07
- `Active_IdleExhausted_UnderCap × UV-Release-contradiction` → Q-07
- `Active_IdleExhausted_UnderCap × UV-Release-commission` → Q-07
- `Active_IdleExhausted_AtCapacity × UV-Release-duplication` → Q-07
- `Active_IdleExhausted_AtCapacity × UV-Release-out-of-order` → Q-07
- `Active_IdleExhausted_AtCapacity × UV-Release-contradiction` → Q-07
- `Active_IdleExhausted_AtCapacity × UV-Release-commission` → Q-07
- `Released × UV-Release-duplication` → Q-07
- `Released × UV-Release-out-of-order` → Q-07
- `Released × UV-Release-contradiction` → Q-07
- `Released × UV-Release-commission` → Q-07

Q-01 through Q-06 have accepted decision records for their documented scopes.
No Testgen or implementation phase is included in this benchmark task.
