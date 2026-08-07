# Remaining questions — silenceper/pool `channelPool`

## Q-UV-01: undesired Get variants

**Status:** OPEN.

`UV-Get-commission` and `UV-Get-value` remain unspecified in every state.
They are labelled `→ Q-UV-01` in the to-be matrix. DR-001 through DR-006 do
not decide caller authorization for `Get()` or ignored `ErrClosed` values.

## Q-07: undesired Release variants

**Status:** OPEN.

DR-001 decides only `Active_IdleExhausted_AtCapacity × Release`: terminal
`Release()` resolves queued `Get()` calls with `ErrMaxActiveConnReached`. It
does not decide `UV-Release-duplication`, `UV-Release-out-of-order`,
`UV-Release-contradiction`, or `UV-Release-commission` in any state. Those
sixteen cells remain `UNSPECIFIED → Q-07`.
