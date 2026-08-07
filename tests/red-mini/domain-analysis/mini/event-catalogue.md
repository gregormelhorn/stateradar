# Event catalogue — mini

<!-- event-ids: M1 M2 UV-M1-dup -->

| id | name | source | ext/int | payload | produced | consumed |
|---|---|---|---|---|---|---|
| M1 | open | operator | external | id | op | svc |
| M2 | close | operator | external | id | op | svc |
| UV-M1-dup | duplicate open | operator | external | id | op | svc |

## Event annotations

### M1
- gate: payload content
- upstream_guards: validated upstream
- coverage:
  - loss: n/a: local
  - delay: n/a: sync
  - duplication: n/a: sync
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: n/a: sync
  - value: n/a: payload validated

### M2
- gate: payload content
- upstream_guards: validated upstream
- coverage:
  - loss: n/a: local
  - delay: n/a: sync
  - duplication: n/a: sync
  - out-of-order: n/a: sync
  - contradiction: n/a: sync
  - commission: n/a: sync
  - value: n/a: payload validated
