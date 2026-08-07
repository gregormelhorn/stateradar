# silenceper/pool — Living Analysis Index

## Current status

The canonical root sidecar is the as-is observation record:
[`../analysis.json`](../analysis.json). The completed Resolution-only to-be
artifact set is in [`channelPool/`](channelPool/). The to-be matrix passed
`check_matrix.py`. The canonical sidecar passed `dsc_check.py` with 4 states,
20 events, and 80 cells.

This benchmark stops after Resolution. It has no Testgen result, upstream
implementation result, Reconcile result, release, tag, or push.

## As-is record

- [Canonical sidecar](../analysis.json)
- [Root question register](../open-questions.md)
- [Oracle manifest](../MANIFEST.md)
- [Convergence record](../CONVERGENCE.md)

## Resolution to-be record

- [As-is model](channelPool/as-is.machine.mmd)
- [To-be model](channelPool/to-be.machine.mmd)
- [Event catalogue](channelPool/event-catalogue.md)
- [Disposition matrix](channelPool/disposition-matrix.md)
- [Invariants and lints](channelPool/invariants-and-lints.md)
- [Semantic diff](channelPool/to-be-diff.md)
- [Local question register](channelPool/open-questions.md)
- [Remaining holes](channelPool/remaining-holes.md)

## Accepted decisions

| Decision | Scope |
|---|---|
| [DR-001](../decisions/DR-001.yaml) | `Active_IdleExhausted_AtCapacity × Release` resolves queued `Get()` waiters with `ErrMaxActiveConnReached`. |
| [DR-002](../decisions/DR-002.yaml) | Put integrity is a NAT caller contract. |
| [DR-003](../decisions/DR-003.yaml) | `Put()` after `Release()` is a safe terminal no-op. |
| [DR-004](../decisions/DR-004.yaml) | Queued `Get()` delivery uses configured Ping validation. |
| [DR-005](../decisions/DR-005.yaml) | Factory failure does not consume capacity. |
| [DR-006](../decisions/DR-006.yaml) | `openingConns >= 0` holds under the valid-caller contract. |

## Open questions

- **Q-UV-01 — OPEN:** canonical-sidecar undesired Get variants. See the
  [root question register](../open-questions.md) and the
  [local question register](channelPool/open-questions.md).
- **Q-07 — OPEN:** Resolution-local undesired Release variants. DR-001 does
  not decide these 16 cells. See the [remaining holes](channelPool/remaining-holes.md).
