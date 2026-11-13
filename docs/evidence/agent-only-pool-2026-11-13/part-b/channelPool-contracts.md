# channelPool — contract texts (doc comments and schema descriptions, copied verbatim)

## pool.go:5-8
```
var (
	//ErrClosed 连接池已经关闭Error
	ErrClosed = errors.New("pool is closed")
)
```

## pool.go:10-21
```
// Pool 基本方法
type Pool interface {
	Get() (interface{}, error)

	Put(interface{}) error

	Close(interface{}) error

	Release()

	Len() int
}
```

## channel.go:12-15
```
var (
	//ErrMaxActiveConnReached 连接池超限
	ErrMaxActiveConnReached = errors.New("MaxActiveConnReached")
)
```

## channel.go:17-33
```
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
```

## channel.go:57-58
```
// NewChannelPool 初始化连接
func NewChannelPool(poolConfig *Config) (Pool, error) {
```

## channel.go:102-103
```
// Get 从pool中取一个连接
func (c *channelPool) Get() (interface{}, error) {
```

## channel.go:166-167
```
// Put 将连接放回pool中
func (c *channelPool) Put(conn interface{}) error {
```

## channel.go:201-202
```
// Close 关闭单条连接
func (c *channelPool) Close(conn interface{}) error {
```

## channel.go:215-216
```
// Ping 检查单条连接是否有效
func (c *channelPool) Ping(conn interface{}) error {
```

## channel.go:223-224
```
// Release 释放连接池中所有连接
func (c *channelPool) Release() {
```

## channel.go:245-246
```
// Len 连接池中已有的连接
func (c *channelPool) Len() int {
```
