# Independent public-boundary controls

These five as-is probes were written separately from the pilot session and
kept outside its sandbox. They assert observed outcomes, not approved domain
semantics. They are not a complete cell suite and do not establish Step 04.

Pinned source: golang.org/x/sync v0.17.0,
04914c200cb38d4ea960ee6a4c314a028c632991. Go 1.27.3, race detector enabled.
Public seam only: constructor, Acquire, TryAcquire, Release and context result.
No component source or existing test was changed.

| Control | Observed result |
| --- | --- |
| Pre-canceled context with available capacity | Acquire returns context.Canceled; the full capacity remains acquirable. |
| Second acquisition while the first weight is held | Each successful call consumes capacity independently. |
| Oversized request and cancellation | Cancellation completes the oversized call; a concurrent regular request succeeds. This probe does not force the oversized caller to reach its blocking point first. |
| Negative TryAcquire weight | It succeeds, after which a positive request larger than configured capacity succeeds. Intended invalid-input policy remains open. |
| Recovering an over-release panic | The instance subsequently admits above its configured capacity. Recovery policy remains open. |

Executed command after installing a Go overlay for the retained test file:

```sh
go test -race -count=1 -timeout=30s -overlay=/absolute/path/overlay.json -run '^TestControl' -v ./semaphore
```

The overlay maps the **canonical absolute** checkout path
`semaphore/independent_control_test.go` to `control_test.go.txt`. The original
/tmp-spelled key on macOS did not match /private/tmp: Go exited 0 with no tests.
That vacuous result is retained in `discovery-failure.txt` and is not a pass.
After correcting the path, `results.txt` contains all five named RUN/PASS pairs.
The unchanged upstream `go test -race -count=1 -timeout=60s ./semaphore` also
passed (5.236s). No issue history or expected-finding list was used.
