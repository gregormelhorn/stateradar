Inspect the source for significant behavior, edge cases, event ordering and contract limitations. Return JSON with exactly one key findings, an array of at most six entries. Each entry has a unique id, text describing the exact starting conditions, ordered events and observable result, a citation object {line: integer, fragment: exact substring of that line}, and question: either an OPEN: question where intent or source wording is unclear, or an empty string. Include supported ordinary controls as appropriate. Do not assume a surprising behavior is intended. Return JSON only.

REVIEW PARAGRAPH:
Examine ordinary success and failure as well as repeated operations, deferred work, cancellation and both event orderings. Trace state, object identity and effects across each lifecycle boundary. Compare contract language with behavior, including its exclusions and the possibility that a valid statement applies only to a narrower situation. Retain correct controls. Cite evidence and leave unanswered intent or contradictory requirements as OPEN questions.

SOURCE:
1: // BEGIN pinned channel.go
2: package pool
3: 
4: import (
5: 	"errors"
6: 	"fmt"
7: 	log "github.com/sirupsen/logrus"
8: 	"sync"
9: 	"time"
10: 	//"reflect"
11: )
12: 
13: var (
14: 	//ErrMaxActiveConnReached 连接池超限
15: 	ErrMaxActiveConnReached = errors.New("MaxActiveConnReached")
16: )
17: 
18: // Config 连接池相关配置
19: type Config struct {
20: 	//连接池中拥有的最小连接数
21: 	InitialCap int
22: 	//最大并发存活连接数
23: 	MaxCap int
24: 	//最大空闲连接
25: 	MaxIdle int
26: 	//生成连接的方法
27: 	Factory func() (interface{}, error)
28: 	//关闭连接的方法
29: 	Close func(interface{}) error
30: 	//检查连接是否有效的方法
31: 	Ping func(interface{}) error
32: 	//连接最大空闲时间，超过该事件则将失效
33: 	IdleTimeout time.Duration
34: }
35: 
36: type connReq struct {
37: 	idleConn *idleConn
38: }
39: 
40: // channelPool 存放连接信息
41: type channelPool struct {
42: 	mu                       sync.RWMutex
43: 	conns                    chan *idleConn
44: 	factory                  func() (interface{}, error)
45: 	close                    func(interface{}) error
46: 	ping                     func(interface{}) error
47: 	idleTimeout, waitTimeOut time.Duration
48: 	maxActive                int
49: 	openingConns             int
50: 	connReqs                 []chan connReq
51: }
52: 
53: type idleConn struct {
54: 	conn interface{}
55: 	t    time.Time
56: }
57: 
58: // NewChannelPool 初始化连接
59: func NewChannelPool(poolConfig *Config) (Pool, error) {
60: 	if !(poolConfig.InitialCap <= poolConfig.MaxIdle && poolConfig.MaxCap >= poolConfig.MaxIdle && poolConfig.InitialCap >= 0) {
61: 		return nil, errors.New("invalid capacity settings")
62: 	}
63: 	if poolConfig.Factory == nil {
64: 		return nil, errors.New("invalid factory func settings")
65: 	}
66: 	if poolConfig.Close == nil {
67: 		return nil, errors.New("invalid close func settings")
68: 	}
69: 
70: 	c := &channelPool{
71: 		conns:        make(chan *idleConn, poolConfig.MaxIdle),
72: 		factory:      poolConfig.Factory,
73: 		close:        poolConfig.Close,
74: 		idleTimeout:  poolConfig.IdleTimeout,
75: 		maxActive:    poolConfig.MaxCap,
76: 		openingConns: poolConfig.InitialCap,
77: 	}
78: 
79: 	if poolConfig.Ping != nil {
80: 		c.ping = poolConfig.Ping
81: 	}
82: 
83: 	for i := 0; i < poolConfig.InitialCap; i++ {
84: 		conn, err := c.factory()
85: 		if err != nil {
86: 			c.Release()
87: 			return nil, fmt.Errorf("factory is not able to fill the pool: %s", err)
88: 		}
89: 		c.conns <- &idleConn{conn: conn, t: time.Now()}
90: 	}
91: 
92: 	return c, nil
93: }
94: 
95: // getConns 获取所有连接
96: func (c *channelPool) getConns() chan *idleConn {
97: 	c.mu.Lock()
98: 	conns := c.conns
99: 	c.mu.Unlock()
100: 	return conns
101: }
102: 
103: // Get 从pool中取一个连接
104: func (c *channelPool) Get() (interface{}, error) {
105: 	conns := c.getConns()
106: 	if conns == nil {
107: 		return nil, ErrClosed
108: 	}
109: 	for {
110: 		select {
111: 		case wrapConn := <-conns:
112: 			if wrapConn == nil {
113: 				return nil, ErrClosed
114: 			}
115: 			//判断是否超时，超时则丢弃
116: 			if timeout := c.idleTimeout; timeout > 0 {
117: 				if wrapConn.t.Add(timeout).Before(time.Now()) {
118: 					//丢弃并关闭该连接
119: 					c.Close(wrapConn.conn)
120: 					continue
121: 				}
122: 			}
123: 			//判断是否失效，失效则丢弃，如果用户没有设定 ping 方法，就不检查
124: 			if c.ping != nil {
125: 				if err := c.Ping(wrapConn.conn); err != nil {
126: 					c.Close(wrapConn.conn)
127: 					continue
128: 				}
129: 			}
130: 			return wrapConn.conn, nil
131: 		default:
132: 			c.mu.Lock()
133: 			log.Debugf("openConn %v %v", c.openingConns, c.maxActive)
134: 			if c.openingConns >= c.maxActive {
135: 				req := make(chan connReq, 1)
136: 				c.connReqs = append(c.connReqs, req)
137: 				c.mu.Unlock()
138: 				ret, ok := <-req
139: 				if !ok {
140: 					return nil, ErrMaxActiveConnReached
141: 				}
142: 				if timeout := c.idleTimeout; timeout > 0 {
143: 					if ret.idleConn.t.Add(timeout).Before(time.Now()) {
144: 						//丢弃并关闭该连接
145: 						c.Close(ret.idleConn.conn)
146: 						continue
147: 					}
148: 				}
149: 				return ret.idleConn.conn, nil
150: 			}
151: 			if c.factory == nil {
152: 				c.mu.Unlock()
153: 				return nil, ErrClosed
154: 			}
155: 			conn, err := c.factory()
156: 			if err != nil {
157: 				c.mu.Unlock()
158: 				return nil, err
159: 			}
160: 			c.openingConns++
161: 			c.mu.Unlock()
162: 			return conn, nil
163: 		}
164: 	}
165: }
166: 
167: // Put 将连接放回pool中
168: func (c *channelPool) Put(conn interface{}) error {
169: 	if conn == nil {
170: 		return errors.New("connection is nil. rejecting")
171: 	}
172: 
173: 	c.mu.Lock()
174: 
175: 	if c.conns == nil {
176: 		c.mu.Unlock()
177: 		return c.Close(conn)
178: 	}
179: 
180: 	if l := len(c.connReqs); l > 0 {
181: 		req := c.connReqs[0]
182: 		copy(c.connReqs, c.connReqs[1:])
183: 		c.connReqs = c.connReqs[:l-1]
184: 		req <- connReq{
185: 			idleConn: &idleConn{conn: conn, t: time.Now()},
186: 		}
187: 		c.mu.Unlock()
188: 		return nil
189: 	} else {
190: 		select {
191: 		case c.conns <- &idleConn{conn: conn, t: time.Now()}:
192: 			c.mu.Unlock()
193: 			return nil
194: 		default:
195: 			c.mu.Unlock()
196: 			//连接池已满，直接关闭该连接
197: 			return c.Close(conn)
198: 		}
199: 	}
200: }
201: 
202: // Close 关闭单条连接
203: func (c *channelPool) Close(conn interface{}) error {
204: 	if conn == nil {
205: 		return errors.New("connection is nil. rejecting")
206: 	}
207: 	c.mu.Lock()
208: 	defer c.mu.Unlock()
209: 	if c.close == nil {
210: 		return nil
211: 	}
212: 	c.openingConns--
213: 	return c.close(conn)
214: }
215: 
216: // Ping 检查单条连接是否有效
217: func (c *channelPool) Ping(conn interface{}) error {
218: 	if conn == nil {
219: 		return errors.New("connection is nil. rejecting")
220: 	}
221: 	return c.ping(conn)
222: }
223: 
224: // Release 释放连接池中所有连接
225: func (c *channelPool) Release() {
226: 	c.mu.Lock()
227: 	conns := c.conns
228: 	c.conns = nil
229: 	c.factory = nil
230: 	c.ping = nil
231: 	closeFun := c.close
232: 	c.close = nil
233: 	c.mu.Unlock()
234: 
235: 	if conns == nil {
236: 		return
237: 	}
238: 
239: 	close(conns)
240: 	for wrapConn := range conns {
241: 		//log.Printf("Type %v\n",reflect.TypeOf(wrapConn.conn))
242: 		closeFun(wrapConn.conn)
243: 	}
244: }
245: 
246: // Len 连接池中已有的连接
247: func (c *channelPool) Len() int {
248: 	return len(c.getConns())
249: }
250: 
251: // BEGIN pinned pool.go
252: package pool
253: 
254: import "errors"
255: 
256: var (
257: 	//ErrClosed 连接池已经关闭Error
258: 	ErrClosed = errors.New("pool is closed")
259: )
260: 
261: // Pool 基本方法
262: type Pool interface {
263: 	Get() (interface{}, error)
264: 
265: 	Put(interface{}) error
266: 
267: 	Close(interface{}) error
268: 
269: 	Release()
270: 
271: 	Len() int
272: }