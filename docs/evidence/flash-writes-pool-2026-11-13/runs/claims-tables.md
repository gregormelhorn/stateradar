### Drafted claims — channel.go (observed-in-code)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| channel:C1 | claim | channel.go:14 | unclear | The package defines ErrMaxActiveConnReached as an error message used when the max active connection limit is reached via the waiting-request channel path. |
| channel:C2 | claim | channel.go:18 | unclear | Config has InitialCap, MaxCap, MaxIdle, Factory, Close, Ping, and IdleTimeout fields. |
| channel:C3 | claim | channel.go:40 | supported | channelPool stores synchronization via sync.RWMutex, a conns channel of idleConn pointers, factory/close/ping callbacks, idleTimeout and waitTimeOut durations, maxActive and openingConns counters, and a connReqs slice of chan connReq. |
| channel:C4 | claim | channel.go:52 | supported | idleConn wraps a conn interface value and the time t it was recorded. |
| channel:C5 | claim | channel.go:59 | supported | NewChannelPool rejects configurations unless InitialCap <= MaxIdle, MaxCap >= MaxIdle, and InitialCap >= 0, returning error 'invalid capacity settings'. |
| channel:C6 | claim | channel.go:62 | supported | NewChannelPool rejects a nil Factory with error 'invalid factory func settings'. |
| channel:C7 | claim | channel.go:65 | supported | NewChannelPool rejects a nil Close with error 'invalid close func settings'. |
| channel:C8 | claim | channel.go:70 | unclear | NewChannelPool creates the conns channel with capacity MaxIdle, copies factory, close, idleTimeout, and maxActive from config, and sets openingConns to InitialCap. |
| channel:C9 | claim | channel.go:78 | supported | NewChannelPool sets the ping callback only when poolConfig.Ping is non-nil. |
| channel:C10 | claim | channel.go:83 | supported | NewChannelPool pre-fills the pool by calling factory InitialCap times; on factory error it invokes Release and returns a wrapped error. |
| channel:C11 | claim | channel.go:85 | supported | On factory failure during initialization, Release is called before returning the wrapped factory error. |
| channel:C12 | claim | channel.go:88 | supported | Each successfully factory-created initial connection is placed into conns as an idleConn with timestamp time.Now(). |
| channel:C13 | claim | channel.go:96 | unclear | getConns acquires the write lock, copies c.conns to a local, releases the lock, and returns the local channel. |
| channel:C14 | claim | channel.go:105 | supported | Get calls getConns and returns ErrClosed if the returned channel is nil. |
| channel:C15 | ordering | channel.go:108 | supported | Get loops selecting: first on receiving from conns, else defaulting to the slow path that locks c.mu. |
| channel:C16 | claim | channel.go:111 | supported | If a received wrapConn from conns is nil, Get returns ErrClosed. |
| channel:C17 | claim | channel.go:116 | supported | When idleTimeout > 0 and the idleConn timestamp plus timeout is before now, Get closes that connection and continues looping. |
| channel:C18 | claim | channel.go:123 | supported | If c.ping is non-nil, Get pings the connection; on ping error it closes the connection and continues looping. |
| channel:C19 | claim | channel.go:129 | supported | A connection that passes idle-timeout and ping checks is returned to the caller from Get. |
| channel:C20 | claim | channel.go:131 | unclear | In the default branch, Get acquires c.mu, logs openingConns and maxActive, and checks whether openingConns >= maxActive. |
| channel:C21 | claim | channel.go:134 | supported | When openingConns >= maxActive, Get creates a buffered connReq channel of capacity 1, appends it to connReqs, unlocks, then blocks receiving from that request channel. |
| channel:C22 | claim | channel.go:139 | supported | If the waiting request channel is closed (ok false), Get returns ErrMaxActiveConnReached. |
| channel:C23 | claim | channel.go:142 | supported | After receiving a connReq from the waiting channel, if idleTimeout > 0 and its timestamp is expired, Get closes that connection and continues the loop. |
| channel:C24 | claim | channel.go:148 | supported | A waited-for idleConn that is not expired is returned to the caller from Get. |
| channel:C25 | claim | channel.go:150 | supported | If c.factory is nil in the default path, Get unlocks and returns ErrClosed. |
| channel:C26 | claim | channel.go:154 | supported | In the default path below maxActive, Get invokes c.factory while holding c.mu; on error it unlocks and returns the error. |
| channel:C27 | claim | channel.go:159 | supported | On successful factory call in the default path, Get increments openingConns, unlocks, and returns the new connection. |
| channel:C28 | claim | channel.go:169 | supported | Put returns error 'connection is nil. rejecting' when conn is nil. |
| channel:C29 | claim | channel.go:172 | supported | Put acquires c.mu before inspecting conns and connReqs. |
| channel:C30 | claim | channel.go:174 | supported | If c.conns is nil in Put, it unlocks and delegates to Close(conn). |
| channel:C31 | ordering | channel.go:179 | supported | When connReqs is non-empty, Put takes the first waiting request, shifts the slice via copy, shrinks connReqs, sends a new idleConn with current time into the request, unlocks, and returns nil. |
| channel:C32 | ordering | channel.go:190 | supported | When connReqs is empty, Put tries a non-blocking send of a new idleConn into conns; on success it unlocks and returns nil. |
| channel:C33 | claim | channel.go:196 | supported | If the non-blocking send in Put's empty-connReqs branch fails, Put unlocks and calls Close(conn), returning its result. |
| channel:C34 | claim | channel.go:204 | supported | Close returns error 'connection is nil. rejecting' when conn is nil. |
| channel:C35 | claim | channel.go:206 | supported | Close acquires c.mu and defers its release. |
| channel:C36 | claim | channel.go:208 | contradicted | If c.close is nil, Close returns nil without decrementing openingConns. |
| channel:C37 | claim | channel.go:212 | supported | Close decrements openingConns then invokes c.close(conn) under the mutex. |
| channel:C38 | claim | channel.go:218 | supported | Ping returns error 'connection is nil. rejecting' when conn is nil. |
| channel:C39 | claim | channel.go:220 | supported | Ping directly invokes c.ping(conn); it does not acquire c.mu. |
| channel:C40 | claim | channel.go:225 | unclear | Release acquires c.mu, nils conns, factory, ping, and close, saves closeFun locally, then unlocks. |
| channel:C41 | claim | channel.go:234 | supported | Release returns immediately if the saved conns channel was nil. |
| channel:C42 | ordering | channel.go:238 | supported | Release closes the conns channel, then ranges over it calling closeFun on each connection. |
| channel:C43 | claim | channel.go:247 | supported | Len returns len(c.getConns()), which acquires and releases c.mu inside getConns. |
| channel:C44 | claim | channel.go:155 | unclear | Get's factory invocation in the default slow path occurs while c.mu is held, so the factory callback runs under the lock. |
| channel:C45 | claim | channel.go:207 | supported | Close's user-supplied close callback is invoked while c.mu is held (via deferred unlock). |
| channel:C46 | claim | channel.go:241 | supported | Release invokes closeFun on each connection after unlocking c.mu, so the close callback during Release runs without the lock. |
| channel:C47 | claim | channel.go:46 | supported | waitTimeOut is declared as a field but is never assigned or read in this file. |
| channel:C48 | claim | channel.go:86 | supported | Factory's error return in NewChannelPool is wrapped with 'factory is not able to fill the pool'. |

### Drafted claims — pool.go (observed-in-code)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| pool:C1 | claim | pool.go:7 | supported | The exported variable ErrClosed is declared as an error created with errors.New whose text is "pool is closed". |
| pool:C2 | claim | pool.go:12 | supported | The Pool interface declares a method Get that takes no arguments and returns (interface{}, error). |
| pool:C3 | claim | pool.go:14 | supported | The Pool interface declares a method Put that takes one interface{} argument and returns an error. |
| pool:C4 | claim | pool.go:16 | supported | The Pool interface declares a method Close that takes one interface{} argument and returns an error. |
| pool:C5 | claim | pool.go:18 | supported | The Pool interface declares a method Release that takes no arguments and returns nothing. |
| pool:C6 | claim | pool.go:20 | supported | The Pool interface declares a method Len that takes no arguments and returns an int. |
| pool:C7 | claim | pool.go:6 | supported | The comment on ErrClosed states that it is the error for when the connection pool has already been closed. |
| pool:C8 | claim | pool.go:10 | supported | The comment on the Pool interface describes it as having basic methods. |

### Drafted claims — channel_rpc_test.go (observed-in-tests)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| test:C1 | claim | channel_rpc_test.go:38 | supported | TestNew calls newChannelPool and reports an error if it fails. |
| test:C2 | claim | channel_rpc_test.go:39 | supported | TestNew defers p.Release(). |
| test:C3 | claim | channel_rpc_test.go:41 | supported | TestNew expects newChannelPool to return no error. |
| test:C4 | claim | channel_rpc_test.go:50 | supported | TestPool_Get_Impl gets a connection and expects no error. |
| test:C5 | claim | channel_rpc_test.go:52 | supported | TestPool_Get_Impl asserts the returned connection type-asserts to *rpc.Client. |
| test:C6 | claim | channel_rpc_test.go:54 | supported | TestPool_Get_Impl's failure message says the connection is not of type poolConn. |
| test:C7 | claim | channel_rpc_test.go:56 | supported | TestPool_Get_Impl puts the connection back into the pool. |
| test:C8 | claim | channel_rpc_test.go:69 | supported | TestPool_Get expects the pool length to equal InitialCap-1 after one Get. |
| test:C9 | ordering | channel_rpc_test.go:76 | supported | TestPool_Get launches MaximumCap-1 goroutines that each call Get, then waits on the WaitGroup. |
| test:C10 | claim | channel_rpc_test.go:82 | supported | TestPool_Get expects each concurrent Get to return no error. |
| test:C11 | claim | channel_rpc_test.go:88 | supported | TestPool_Get expects the pool length to be 0 after acquiring all connections. |
| test:C12 | claim | channel_rpc_test.go:94 | supported | TestPool_Get expects a further Get to return ErrMaxActiveConnReached. |
| test:C13 | claim | channel_rpc_test.go:101 | supported | TestPool_Put configures a pool with InitialCap 5, MaxCap 100, MaxIdle 10, and IdleTimeout 20s. |
| test:C14 | claim | channel_rpc_test.go:111 | supported | TestPool_Put fetches MaximumCap connections with Get into a slice. |
| test:C15 | claim | channel_rpc_test.go:118 | supported | TestPool_Put puts all MaximumCap connections back via Put. |
| test:C16 | claim | channel_rpc_test.go:121 | supported | TestPool_Put expects the pool length to equal MaxIdleCap after putting all back. |
| test:C17 | claim | channel_rpc_test.go:123 | supported | TestPool_Put's failure message formats the expected value as 1, not MaxIdleCap. |
| test:C18 | claim | channel_rpc_test.go:134 | supported | TestPool_UsedCapacity expects Len() to equal InitialCap initially. |
| test:C19 | claim | channel_rpc_test.go:146 | supported | TestPool_Close calls Release and then type-asserts the pool to *channelPool. |
| test:C20 | claim | channel_rpc_test.go:148 | supported | After Release, TestPool_Close expects the conns channel to be nil. |
| test:C21 | claim | channel_rpc_test.go:152 | supported | After Release, TestPool_Close expects c.factory to be nil. |
| test:C22 | claim | channel_rpc_test.go:157 | supported | After Release, TestPool_Close expects Get to return a non-nil error. |
| test:C23 | claim | channel_rpc_test.go:161 | supported | After Release, TestPool_Close expects Len() to be 0. |
| test:C24 | ordering | channel_rpc_test.go:171 | supported | TestPoolConcurrent starts a goroutine that calls p.Release while Get/Put goroutines are launched in a loop of MaximumCap iterations using an unbuffered pipe. |
| test:C25 | claim | channel_rpc_test.go:176 | supported | TestPoolConcurrent does not assert on any Get or Put results or errors. |
| test:C26 | claim | channel_rpc_test.go:183 | supported | TestPoolConcurrent's consumer returns early if the received connection is nil. |
| test:C27 | claim | channel_rpc_test.go:197 | supported | TestPoolWriteRead calls 'Arith.Multiply' with Args{1,2} over the rpc client. |
| test:C28 | claim | channel_rpc_test.go:199 | supported | TestPoolWriteRead expects the call to return no error. |
| test:C29 | claim | channel_rpc_test.go:201 | supported | TestPoolWriteRead expects resp to equal 2. |
| test:C30 | ordering | channel_rpc_test.go:218 | supported | TestPoolConcurrent2 launches 10 goroutines that Get, sleep a random duration, then call p.Close(conn). |
| test:C31 | claim | channel_rpc_test.go:216 | supported | TestPoolConcurrent2 does not assert on Get errors or results; it ignores them. |
| test:C32 | claim | channel_rpc_test.go:229 | unclear | TestPoolConcurrent2 launches a second set of 10 goroutines outside a wrapping goroutine that also Get, sleep, and Close. |
| test:C33 | claim | channel_rpc_test.go:234 | supported | TestPoolConcurrent2 waits on wg after launching goroutines. |
| test:C34 | claim | channel_rpc_test.go:238 | supported | TestPoolConcurrent3 is commented out. |
| test:C35 | claim | channel_rpc_test.go:239 | supported | The commented-out test pool construction line is also commented out. |
| test:C36 | claim | channel_rpc_test.go:257 | supported | newChannelPool builds a Config with InitialCap 5, MaxCap 100, MaxIdle 10, and IdleTimeout 20s, and calls NewChannelPool. |
| test:C37 | claim | channel_rpc_test.go:21 | supported | The factory dials RPC over tcp at the configured address. |
| test:C38 | claim | channel_rpc_test.go:24 | supported | The closeFac closes the value by asserting it to *rpc.Client. |
| test:C39 | claim | channel_rpc_test.go:32 | supported | The init function starts an rpcServer goroutine and sleeps 300ms. |
| test:C40 | claim | channel_rpc_test.go:271 | unclear | rpcServer registers Arith and serves HTTP on the configured address. |
| test:C41 | claim | channel_rpc_test.go:281 | supported | Arith.Multiply writes the product of args.A and args.B into reply and returns nil. |

### Drafted claims — README.md (explicit-requirement)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| readme:C1 | claim | README.md:8 | supported | The pool is a golang universal network connection pool. |
| readme:C2 | claim | README.md:12 | supported | The connection type in the connection pool is interface{}, making it more versatile. |
| readme:C3 | claim | README.md:13 | supported | The connection supports setting the maximum idle time. |
| readme:C4 | claim | README.md:13 | supported | The timeout connection will be closed and discarded. |
| readme:C5 | claim | README.md:13 | supported | Setting the maximum idle time can avoid the problem of automatic connection failure when idle. |
| readme:C6 | claim | README.md:14 | supported | The pool supports user setting a ping method. |
| readme:C7 | claim | README.md:14 | supported | The ping method is used to check the connectivity of connection. |
| readme:C8 | claim | README.md:14 | supported | Invalid connection will be discarded. |
| readme:C9 | claim | README.md:15 | supported | The pool supports connection waiting. |
| readme:C10 | claim | README.md:15 | supported | When the connection pool is full, it supports connection waiting (like the go db connection pool). |
| readme:C11 | claim | README.md:21 | supported | The factory specifies the method to create the connection. |
| readme:C12 | claim | README.md:24 | supported | The close function specifies the method to close the connection. |
| readme:C13 | claim | README.md:27 | supported | The ping function specifies the method to detect whether the connection is invalid. |
| readme:C14 | claim | README.md:30 | supported | InitialCap initializes the number of connections to 5. |
| readme:C15 | claim | README.md:30 | supported | MaxIdle is the maximum idle connection, set to 20. |
| readme:C16 | claim | README.md:30 | supported | MaxCap is the maximum concurrent connection, set to 30. |
| readme:C17 | claim | README.md:38 | supported | IdleTimeout is the maximum idle time of the connection. |
| readme:C18 | claim | README.md:38 | supported | The connection exceeding the idle time will be closed. |
| readme:C19 | claim | README.md:38 | supported | The maximum idle time can avoid the problem of automatic failure when connecting to EOF when idle. |
| readme:C20 | claim | README.md:41 | supported | The pool is created with pool.NewChannelPool(poolConfig). |
| readme:C21 | claim | README.md:46 | supported | Get gets a connection from the connection pool. |
| readme:C22 | claim | README.md:47 | supported | The connection is retrieved from the pool via p.Get(). |
| readme:C23 | claim | README.md:52 | supported | The connection is put back into the connection pool when the connection is no longer in use. |
| readme:C24 | claim | README.md:53 | supported | The connection is returned via p.Put(v). |
| readme:C25 | claim | README.md:55 | supported | Release releases all connections in the connection pool when resources need to be destroyed. |
| readme:C26 | claim | README.md:56 | supported | Release is invoked via p.Release(). |
| readme:C27 | claim | README.md:58 | supported | Len views the number of connections in the current connection pool. |
| readme:C28 | claim | README.md:59 | supported | The current number of connections is obtained via p.Len(). |
| readme:C29 | claim | README.md:66 | supported | The connection pool implementation refers to pool github.com/fatih/pool. |

### Drafted claims — README_ZH_CN.md (explicit-requirement)

| id | kind | cite | Jev | statement |
|---|---|---|---|---|
| readme-zh:C1 | claim | README_ZH_CN.md:5 | supported | The connection pool is implemented in Golang. |
| readme-zh:C2 | claim | README_ZH_CN.md:10 | supported | The connection type inside the pool is interface{}, making it more general. |
| readme-zh:C3 | claim | README_ZH_CN.md:11 | supported | There is a maximum idle time for connections; connections exceeding it are closed and discarded, which can avoid automatic invalidation during idle. |
| readme-zh:C4 | claim | README_ZH_CN.md:12 | supported | The pool supports a user-set ping method to check connection connectivity; invalid connections are discarded. |
| readme-zh:C5 | claim | README_ZH_CN.md:13 | supported | Channels are used to handle connections in the pool, described as efficient. |
| readme-zh:C6 | claim | README_ZH_CN.md:20 | supported | The factory field is the method for creating connections, returning net.Dial to tcp 127.0.0.1:4000 in the example. |
| readme-zh:C7 | claim | README_ZH_CN.md:23 | supported | The close field is the method for closing a connection, calling Close on the net.Conn in the example. |
| readme-zh:C8 | claim | README_ZH_CN.md:26 | supported | The ping field is a method for checking connections, as shown commented out. |
| readme-zh:C9 | claim | README_ZH_CN.md:28 | supported | A connection pool is created with InitialCap 5, MaxIdle 20, and MaxCap 30 in the example. |
| readme-zh:C10 | claim | README_ZH_CN.md:30 | supported | The InitialCap configuration field is the initial number of connections in the resource pool. |
| readme-zh:C11 | claim | README_ZH_CN.md:31 | supported | The MaxIdle configuration field is the maximum number of idle connections. |
| readme-zh:C12 | claim | README_ZH_CN.md:32 | supported | The MaxCap configuration field is the maximum number of concurrent connections. |
| readme-zh:C13 | claim | README_ZH_CN.md:37 | supported | The IdleTimeout configuration field is the maximum idle time; connections exceeding this time are closed, which can avoid idle EOF and automatic invalidation. |
| readme-zh:C14 | claim | README_ZH_CN.md:39 | supported | A pool is created via pool.NewChannelPool using the poolConfig. |
| readme-zh:C15 | claim | README_ZH_CN.md:41 | supported | An error from pool.NewChannelPool is printed. |
| readme-zh:C16 | claim | README_ZH_CN.md:45 | supported | A connection is obtained from the pool via p.Get. |
| readme-zh:C17 | claim | README_ZH_CN.md:51 | supported | A connection is returned to the pool via p.Put. |
| readme-zh:C18 | claim | README_ZH_CN.md:54 | supported | All connections in the pool are released via p.Release. |
| readme-zh:C19 | claim | README_ZH_CN.md:57 | supported | The current number of connections is viewed via p.Len. |
| readme-zh:C20 | claim | README_ZH_CN.md:64 | supported | The pool is implemented with reference to fatih/pool, changing and adding some existing features. |