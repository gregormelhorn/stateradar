# Scope-line decisions written before any Step-6 Jev call (routing rule 5)

| Check id | Trace | Source | Quoted text | My decision: cited text contemplates this ordering |
|---|---|---|---|---|
| CT-A | T-01 | README.md:15 | "When the connection pool is full, support for connection waiting" | yes |
| CT-E | P-06a | README.md:55 | "Release all connections in the connection pool" | no |
| CT-F | P-09a | README.md:13 | "the timeout connection will be closed and discarded" | no |
| CT-B | T-02 | channel.go:195 | "连接池已满，直接关闭该连接" | yes |
| CT-C | T-03 | channel.go:122 | "判断是否失效，失效则丢弃" | yes |
| CT-D | T-04 | pool.go:6 | "ErrClosed 连接池已经关闭Error" | no |
