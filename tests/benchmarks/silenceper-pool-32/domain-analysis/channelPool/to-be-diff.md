# To-be semantic diff — silenceper/pool `channelPool`

The canonical root sidecar remains the as-is record. This document records only
approved Resolution changes and explicit constraints; it is not an upstream
implementation request.

| area | as-is finding | to-be rule | provenance |
|---|---|---|---|
| terminal waiter lifecycle | `Active_IdleExhausted_AtCapacity × Release` was unanswered | Terminal `Release()` transitions to `Released` and resolves queued `Get()` calls with `ErrMaxActiveConnReached`. | DR-001 |
| queued Get validation | waiter-delivered connection had no decided Ping parity | Every queued `Get()` result passes configured Ping validation before return; a Ping failure discards the connection and retries acquisition. | DR-004 |
| Put misuse | ownership behavior was unspecified | Returning/closing exactly one genuine borrow exactly once is a NAT caller contract; the pool gains no lease identity or duplicate-return guard. | DR-002 |
| Put after terminal release | terminal behavior was unspecified | `Put()` after `Release()` is a safe terminal no-op; callers clean up outstanding borrows before `Release()`. | DR-003 |
| Factory failure | failure/accounting behavior was unspecified | Factory failure returns its error without consuming capacity; construction aborts on initial Factory failure. The at-capacity waiter branch does not invoke Factory. | DR-005 |
| close/counter safety | Close misuse could violate accounting | `openingConns >= 0` is a SYS invariant only under the DR-002/DR-006 valid-caller contract; no duplicate-close tracking or counter clamping is added. | DR-006 |

## Scope boundary

DR-001 decides only terminal `Active_IdleExhausted_AtCapacity × Release`.
Undesired Release variants remain `UNSPECIFIED → Q-07`; this document does not
extend DR-001 to them.

No upstream source, test, tag, or push was changed by this Resolution artifact set.
