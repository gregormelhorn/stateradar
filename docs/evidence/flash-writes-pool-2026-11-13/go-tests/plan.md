# As-is test plan (channelPool, routing variant flash-writes, point 3)

Each test observes what the code does today through the Pool interface and the Factory/Close/Ping callbacks (fake connections with counters). Package `pool`, file asis_test.go. Cite = channel.go line that decides the claim.

| test | claim observed | cite |
|---|---|---|
| TestAsIs_Get_IdleAvailable | with InitialCap 2 (MaxIdle 3, MaxCap 5) Get returns an idle connection without calling the factory again; Len drops by one | channel.go:110-129 |
| TestAsIs_Get_NoIdleBelowCap | with InitialCap 0, Get calls the factory once and returns its connection | channel.go:154-161 |
| TestAsIs_Put_StoresIdle | Get then Put makes Len 1 | channel.go:190 |
| TestAsIs_Put_IdleFull_ClosesConnection | MaxIdle 1: when the idle channel is full, Put closes the returned connection through the close callback | channel.go:189-196 |
| TestAsIs_Get_AtCap_BlocksUntilPut | MaxCap 1: a second Get blocks (does not return within 200 ms); after Put it returns the same connection | channel.go:133-137, 179-185 |
| TestAsIs_Get_ExpiredIdle_Replaced | IdleTimeout 50 ms: after 150 ms Get closes the stale idle connection and returns a newly created one | channel.go:115-119 |
| TestAsIs_Get_PingFails_DiscardsIdle | with a Ping callback that fails once, Get closes that idle connection and returns another | channel.go:123-128 |
| TestAsIs_Release_ClosesIdleThenGetErrClosed | Release closes every idle connection; afterwards Get returns ErrClosed and Len is 0 | channel.go:224-243, 105-107 |
| TestAsIs_Release_Twice | a second Release returns without panic | channel.go:234 |
| TestAsIs_Put_AfterRelease_NoClose | after Release, Put returns nil and the close callback is not called for the returned connection | channel.go:174-176, 208-210 |
| TestAsIs_Release_DoesNotWakeWaiter | MaxCap 1: a Get blocked at capacity is still blocked 300 ms after Release | channel.go:137, 224-243 |
| TestAsIs_Close_DoesNotServeWaiter | MaxCap 1: a Get blocked at capacity is still blocked 300 ms after another caller Closes the borrowed connection; a new Get from a third goroutine succeeds by creating a connection | channel.go:206-212, 133, 154 |
| TestAsIs_Nil_Rejected | Put(nil) and Close(nil) return an error | channel.go:168-170, 204-206 |
| TestAsIs_Close_Twice_ExceedsMaxCap | MaxCap 2: after Close of the same connection twice, two further Gets succeed immediately, so three unclosed connections exist | channel.go:211 |
| TestAsIs_Len_CountsIdleOnly | Len equals the number of idle connections, not borrowed ones | channel.go:246-248 |
| TestAsIs_New_FactoryError | InitialCap 3 with a factory that fails on the third call: NewChannelPool returns an error and the two created connections are closed | channel.go:83-87 |
| TestAsIs_New_InvalidConfig | the capacity, factory and close validations return errors | channel.go:59-67 |
| TestAsIs_New_ZeroCapAccepted | a Config with MaxCap 0, MaxIdle 0, InitialCap 0 is accepted | channel.go:59 |
| TestAsIs_Get_ConcurrentWithRelease | 200 rounds of Get racing Release with a Ping callback configured: observe whether a panic or a race report occurs (outcome recorded, not asserted beyond no panic) | channel.go:123, 220, 229 |
