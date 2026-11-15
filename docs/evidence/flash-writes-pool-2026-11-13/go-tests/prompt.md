Write one Go test file `asis_test.go` (package `pool`, standard `testing` only, no third-party packages) for the connection pool in the source below. Implement exactly the tests in the plan, one function per plan row, named as in the plan. Each test builds its own pool with a fake connection type (a struct pointer with an id) and callbacks that count calls with sync/atomic: a Factory that returns a new fake connection (and optionally an error on a given call), a Close callback that marks the connection closed and counts, and where the plan says so a Ping callback. Use short sleeps (<= 300 ms) and channels with time.After to detect "blocked" versus "returned". Do not use the network. Assert only what the plan row states. Return only the Go file, no prose.

PLAN:
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

SOURCE channel.go:
```go
package pool

import (
	"errors"
	"fmt"
	log "github.com/sirupsen/logrus"
	"sync"
	"time"
	//"reflect"
)

var (
	//ErrMaxActiveConnReached 连接池超限
	ErrMaxActiveConnReached = errors.New("MaxActiveConnReached")
)

// Config 连接池相关配置
type Config struct {
	//连接池中拥有的最小连接数
	InitialCap int
	//最大并发存活连接数
	MaxCap int
	//最大空闲连接
	MaxIdle int
	//生成连接的方法
	Factory func() (interface{}, error)
	//关闭连接的方法
	Close func(interface{}) error
	//检查连接是否有效的方法
	Ping func(interface{}) error
	//连接最大空闲时间，超过该事件则将失效
	IdleTimeout time.Duration
}

type connReq struct {
	idleConn *idleConn
}

// channelPool 存放连接信息
type channelPool struct {
	mu                       sync.RWMutex
	conns                    chan *idleConn
	factory                  func() (interface{}, error)
	close                    func(interface{}) error
	ping                     func(interface{}) error
	idleTimeout, waitTimeOut time.Duration
	maxActive                int
	openingConns             int
	connReqs                 []chan connReq
}

type idleConn struct {
	conn interface{}
	t    time.Time
}

// NewChannelPool 初始化连接
func NewChannelPool(poolConfig *Config) (Pool, error) {
	if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {
		return nil, errors.New("invalid capacity settings")
	}
	if poolConfig.Factory == nil {
		return nil, errors.New("invalid factory func settings")
	}
	if poolConfig.Close == nil {
		return nil, errors.New("invalid close func settings")
	}

	c := &channelPool{
		conns:        make(chan *idleConn, poolConfig.MaxIdle),
		factory:      poolConfig.Factory,
		close:        poolConfig.Close,
		idleTimeout:  poolConfig.IdleTimeout,
		maxActive:    poolConfig.MaxCap,
		openingConns: poolConfig.InitialCap,
	}

	if poolConfig.Ping != nil {
		c.ping = poolConfig.Ping
	}

	for i := 0; i < poolConfig.InitialCap; i++ {
		conn, err := c.factory()
		if err != nil {
			c.Release()
			return nil, fmt.Errorf("factory is not able to fill the pool: %s", err)
		}
		c.conns <- &idleConn{conn: conn, t: time.Now()}
	}

	return c, nil
}

// getConns 获取所有连接
func (c *channelPool) getConns() chan *idleConn {
	c.mu.Lock()
	conns := c.conns
	c.mu.Unlock()
	return conns
}

// Get 从pool中取一个连接
func (c *channelPool) Get() (interface{}, error) {
	conns := c.getConns()
	if conns == nil {
		return nil, ErrClosed
	}
	for {
		select {
		case wrapConn := <-conns:
			if wrapConn == nil {
				return nil, ErrClosed
			}
			//判断是否超时，超时则丢弃
			if timeout := c.idleTimeout; timeout > 0 {
				if wrapConn.t.Add(timeout).Before(time.Now()) {
					//丢弃并关闭该连接
					c.Close(wrapConn.conn)
					continue
				}
			}
			//判断是否失效，失效则丢弃，如果用户没有设定 ping 方法，就不检查
			if c.ping != nil {
				if err := c.Ping(wrapConn.conn); err != nil {
					c.Close(wrapConn.conn)
					continue
				}
			}
			return wrapConn.conn, nil
		default:
			c.mu.Lock()
			log.Debugf("openConn %v %v", c.openingConns, c.maxActive)
			if c.openingConns >= c.maxActive {
				req := make(chan connReq, 1)
				c.connReqs = append(c.connReqs, req)
				c.mu.Unlock()
				ret, ok := <-req
				if !ok {
					return nil, ErrMaxActiveConnReached
				}
				if timeout := c.idleTimeout; timeout > 0 {
					if ret.idleConn.t.Add(timeout).Before(time.Now()) {
						//丢弃并关闭该连接
						c.Close(ret.idleConn.conn)
						continue
					}
				}
				return ret.idleConn.conn, nil
			}
			if c.factory == nil {
				c.mu.Unlock()
				return nil, ErrClosed
			}
			conn, err := c.factory()
			if err != nil {
				c.mu.Unlock()
				return nil, err
			}
			c.openingConns++
			c.mu.Unlock()
			return conn, nil
		}
	}
}

// Put 将连接放回pool中
func (c *channelPool) Put(conn interface{}) error {
	if conn == nil {
		return errors.New("connection is nil. rejecting")
	}

	c.mu.Lock()

	if c.conns == nil {
		c.mu.Unlock()
		return c.Close(conn)
	}

	if l := len(c.connReqs); l > 0 {
		req := c.connReqs[0]
		copy(c.connReqs, c.connReqs[1:])
		c.connReqs = c.connReqs[:l-1]
		req <- connReq{
			idleConn: &idleConn{conn: conn, t: time.Now()},
		}
		c.mu.Unlock()
		return nil
	} else {
		select {
		case c.conns <- &idleConn{conn: conn, t: time.Now()}:
			c.mu.Unlock()
			return nil
		default:
			c.mu.Unlock()
			//连接池已满，直接关闭该连接
			return c.Close(conn)
		}
	}
}

// Close 关闭单条连接
func (c *channelPool) Close(conn interface{}) error {
	if conn == nil {
		return errors.New("connection is nil. rejecting")
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	if c.close == nil {
		return nil
	}
	c.openingConns--
	return c.close(conn)
}

// Ping 检查单条连接是否有效
func (c *channelPool) Ping(conn interface{}) error {
	if conn == nil {
		return errors.New("connection is nil. rejecting")
	}
	return c.ping(conn)
}

// Release 释放连接池中所有连接
func (c *channelPool) Release() {
	c.mu.Lock()
	conns := c.conns
	c.conns = nil
	c.factory = nil
	c.ping = nil
	closeFun := c.close
	c.close = nil
	c.mu.Unlock()

	if conns == nil {
		return
	}

	close(conns)
	for wrapConn := range conns {
		//log.Printf("Type %v\n",reflect.TypeOf(wrapConn.conn))
		closeFun(wrapConn.conn)
	}
}

// Len 连接池中已有的连接
func (c *channelPool) Len() int {
	return len(c.getConns())
}
```
SOURCE pool.go:
```go
package pool

import "errors"

var (
	//ErrClosed 连接池已经关闭Error
	ErrClosed = errors.New("pool is closed")
)

// Pool 基本方法
type Pool interface {
	Get() (interface{}, error)

	Put(interface{}) error

	Close(interface{}) error

	Release()

	Len() int
}
```
