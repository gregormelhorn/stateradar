# Focused numeric decision matrix

Each row refines only the stated numeric branch of a historical cell.
No other branch in that cell is approved. Full identities are in matrix-coverage.json.

| Starting condition | Event | Disposition | Authority |
| --- | --- | --- | --- |
| Any / constructing | Negative size | reject: panic before construction | DR-002 |
| Empty, held or queued | Negative Acquire/TryAcquire/Release | reject: panic; counter and queue unchanged | DR-002 |
| No queue | Zero or representable positive weights within capacity | handle: preserve supported boundary behavior | DR-002, DR-001 |
| Empty, partially held, fully held, queued | Release greater than total held | reject: panic; counter and queue unchanged | DR-003 |
| Live context, with or without existing queue | Acquire greater than size | reject: explanatory size error, no context wait | DR-004 |
| Already canceled context | Oversized Acquire | reject: existing context error priority retained | DR-004, remaining Q-10 |

Valid releases after rejection must still grant eligible queued requests.
Negative arguments are rejected even with an already canceled context.
