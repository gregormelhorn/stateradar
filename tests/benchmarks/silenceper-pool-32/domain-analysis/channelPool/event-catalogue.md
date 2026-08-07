# Event catalogue — silenceper/pool `channelPool`

This catalogue preserves the twenty-event abstraction in the canonical as-is
sidecar at `../../analysis.json`. The Resolution matrix uses the same state and
event boundary; it does not redefine upstream behavior.

<!-- event-ids: Get Put Close Release FactoryFail IdleTimeout PingFail UV-Get-commission UV-Get-value UV-Put-loss UV-Put-duplication UV-Put-out-of-order UV-Put-commission UV-Close-duplication UV-Close-out-of-order UV-Close-contradiction UV-Release-duplication UV-Release-out-of-order UV-Release-contradiction UV-Release-commission -->

| id | event | source | classification | payload / trigger |
|---|---|---|---|---|
| Get | acquire connection | caller | external | boundary call |
| Put | return connection | caller | external | connection |
| Close | close borrowed connection | caller | external | connection |
| Release | release pool | caller | external | boundary call |
| FactoryFail | Factory error | Factory | internal | error result |
| IdleTimeout | idle expiry | timer | internal | timeout |
| PingFail | configured Ping error | Ping | internal | error result |
| UV-Get-commission | unsolicited Get | caller | undesired | spontaneous commission |
| UV-Get-value | malformed Get result use | caller | undesired | subtle value fault |
| UV-Put-loss | missing Put | caller | undesired | loss or failure |
| UV-Put-duplication | duplicate Put | caller | undesired | duplication |
| UV-Put-out-of-order | stale Put | caller | undesired | out-of-order arrival |
| UV-Put-commission | unsolicited Put | caller | undesired | spontaneous commission |
| UV-Close-duplication | duplicate Close | caller | undesired | duplication |
| UV-Close-out-of-order | stale Close | caller | undesired | out-of-order arrival |
| UV-Close-contradiction | Close and Put for one borrow | caller | undesired | contradictory inputs |
| UV-Release-duplication | duplicate Release | caller | undesired | duplication |
| UV-Release-out-of-order | stale Release | caller | undesired | out-of-order arrival |
| UV-Release-contradiction | Release concurrent with another action | caller | undesired | contradictory inputs |
| UV-Release-commission | unsolicited Release | caller | undesired | spontaneous commission |

The root sidecar retains the complete per-source undesired-variant coverage
table. This local catalogue declares the exact matrix columns for Resolution.
