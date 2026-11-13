## channel.go:13-14

```go
	//ErrMaxActiveConnReached 连接池超限
	ErrMaxActiveConnReached = errors.New("MaxActiveConnReached")
```

## channel.go:17-33

```go
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

## channel.go:57

```go
// NewChannelPool 初始化连接
```

## channel.go:102

```go
// Get 从pool中取一个连接
```

## channel.go:166

```go
// Put 将连接放回pool中
```

## channel.go:201

```go
// Close 关闭单条连接
```

## channel.go:215

```go
// Ping 检查单条连接是否有效
```

## channel.go:223

```go
// Release 释放连接池中所有连接
```

## channel.go:245

```go
// Len 连接池中已有的连接
```

## pool.go:6-7

```go
	//ErrClosed 连接池已经关闭Error
	ErrClosed = errors.New("pool is closed")
```

## pool.go:10-21

```go
// Pool 基本方法
type Pool interface {
	Get() (interface{}, error)

	Put(interface{}) error

	Close(interface{}) error

	Release()

	Len() int
}
```
