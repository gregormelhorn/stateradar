# Focused DR-001 decision matrix

This refines the cancellation branch of the original 57-cell instance matrix.
Setup conditions describe reachable queues, not extra runtime API methods.
All dispositions below carry DR-001; the table does not decide other branches
of the original cells. Each named scenario has a separately collected test.

| Scenario / starting condition | Event | Decided disposition and observable result | Authority |
| --- | --- | --- | --- |
| Full, positive head then one live zero waiter | Cancel head | transition → ZeroGranted; head returns context.Canceled, zero returns nil without any Release | DR-001 |
| Full, positive head then three live zero waiters and positive tail | Cancel head | transition → ZeroPrefixGranted; all zero calls return nil, positive tail remains blocked until real capacity is released | DR-001 |
| One free unit, weight-two head then zero waiter | Cancel head | transition → ZeroGranted; zero completes and the free positive unit remains available | DR-001 |
| Full, positive head then positive middle then zero waiter | Cancel middle | handle; middle returns context.Canceled, original positive head still prevents zero admission; canceling that head then admits zero | DR-001 |
| Full, positive head then zero waiter | Attempt TryAcquire(0) before removing head | reject with false; zero does not bypass the earlier blocker | DR-001 |

SYS-Q01 applies in every row: a live eligible zero prefix gets notified on head
removal; a zero behind a still-blocking positive head does not. SYS-01 applies
throughout: zero completion does not manufacture positive capacity. The tests
check these externally through TryAcquire results and Acquire return channels.
