# Event catalogue — mini

<!-- event-ids: M1 M2 UV-M1-dup UV-M2-stale UV-M1-lost UV-M2-conflict UV-M1-spurious svc-ack -->

| id | name | source | ext/int | payload | produced | consumed |
|---|---|---|---|---|---|---|
| M1 | open | operator | external | id | op | svc |
| M2 | close | operator | external | id | op | svc |
| UV-M1-dup | duplicate open | operator | external | id | op | svc |
| UV-M2-stale | out-of-order close: early or after shutdown | operator | external | id | op | svc |
| UV-M1-lost | lost open | operator | external | id | op | svc |
| UV-M2-conflict | contradictory close | operator | external | id | op | svc |
| UV-M1-spurious | spurious open | operator | external | id | op | svc |
| svc-ack | service acknowledges the open | svc | internal | id | svc | op |

## Event annotations

### M1
- gate: payload content
- upstream_guards: validated upstream
- coverage:
  - loss: UV-M1-lost
  - delay: n/a: sync
  - duplication: UV-M1-dup
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: UV-M1-spurious
  - value: n/a: payload validated

### M2
- gate: payload content
- upstream_guards: validated upstream
- coverage:
  - loss: n/a: local
  - delay: n/a: sync
  - duplication: n/a: sync
  - out-of-order: UV-M2-stale
  - contradiction: UV-M2-conflict
  - commission: n/a: sync
  - value: n/a: payload validated

### svc-ack
- gate: correlation id matches a delivered M1
- upstream_guards: the service emits an ack only in response to a delivered M1; an ack without one cannot reach this boundary
- coverage:
  - loss: n/a: local
  - delay: n/a: sync
  - duplication: n/a: sync
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: n/a: sync
  - value: n/a: correlation id checked
