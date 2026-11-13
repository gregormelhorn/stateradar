## pool.go:6

//ErrClosed 连接池已经关闭Error

## pool.go:10

// Pool 基本方法

## channel.go:13

//ErrMaxActiveConnReached 连接池超限

## channel.go:17

// Config 连接池相关配置

## channel.go:19

//连接池中拥有的最小连接数

## channel.go:21

//最大并发存活连接数

## channel.go:23

//最大空闲连接

## channel.go:25

//生成连接的方法

## channel.go:27

//关闭连接的方法

## channel.go:29

//检查连接是否有效的方法

## channel.go:31

//连接最大空闲时间，超过该事件则将失效

## channel.go:39

// channelPool 存放连接信息

## channel.go:57

// NewChannelPool 初始化连接

## channel.go:94

// getConns 获取所有连接

## channel.go:102

// Get 从pool中取一个连接

## channel.go:166

// Put 将连接放回pool中

## channel.go:201

// Close 关闭单条连接

## channel.go:215

// Ping 检查单条连接是否有效

## channel.go:223

// Release 释放连接池中所有连接

## channel.go:245

// Len 连接池中已有的连接
