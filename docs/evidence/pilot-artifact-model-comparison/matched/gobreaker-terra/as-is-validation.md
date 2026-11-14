# Validation — incomplete

The existing suite passed: `go test -timeout 60s ./...` (pilot log 011). It exercises Closed → Open → HalfOpen → Open → HalfOpen → Closed and two-step equivalents (gobreaker_test.go:178 ("// StateClosed to StateOpen"), gobreaker_test.go:193 ("// StateOpen to StateHalfOpen"), gobreaker_test.go:198 ("// StateHalfOpen to StateOpen"), gobreaker_test.go:209 ("// StateHalfOpen to StateClosed")). Full test-by-test replay and probes are outstanding.
