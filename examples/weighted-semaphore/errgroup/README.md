# errgroup — unchanged upstream copy

Part of [weighted-semaphore](../README.md).

## Overview

Unchanged copy of `golang.org/x/sync/errgroup` (package `errgroup`) from the
pinned upstream revision named in the [parent README](../README.md). It is
present only because the upstream test
`examples/weighted-semaphore/semaphore/semaphore_test.go` imports it. It is
not part of the analyzed state machine.

## Interface

- `type Group` — a collection of goroutines working on subtasks of one task.
  The zero value is valid: no limit, and no cancellation on error.
- `WithContext(ctx context.Context) (*Group, context.Context)` — returns a
  Group and a derived Context created with `context.WithCancelCause`.
- `(*Group).Go(f func() error)` — runs `f` in a new goroutine, blocking while
  the limit is reached.
- `(*Group).TryGo(f func() error) bool` — starts `f` only if below the limit;
  reports whether it started.
- `(*Group).Wait() error` — waits for all goroutines and returns the first
  non-nil error.
- `(*Group).SetLimit(n int)` — limits the number of active goroutines; a
  negative `n` means no limit.

## Invariants

- Only the first non-nil error is recorded (`errOnce`). Recording it cancels
  the derived Context, if one exists, with that error as the cause.
- `Wait` cancels the derived Context (with `g.err`) after all goroutines
  return.
- `SetLimit`:
  - `SetLimit(n)` with `n >= 0` panics if a previously set limit still has
    active goroutines (`len(g.sem) != 0`), with
    `"errgroup: modify limit while %v goroutines in the group are still active"`;
  - `n < 0` removes the limit without checking;
  - a limit of zero blocks every `Go` and makes every `TryGo` return false.
- Documented caller obligations (doc comments, not enforced):
  - a Group should not be reused for different tasks;
  - the first call to `Go` must happen before a `Wait`.
- A panic in `f` is not recovered: it crashes the process and is not returned
  by `Wait`.

## Side Effects

- Spawns goroutines.
- Uses `sync.WaitGroup` and a buffered token channel `sem` for limiting.
- Calls the Context cancel function on the first error and in `Wait`.

## Verification

Commands run from the repository root and assume the dev requirements are
installed (see [System Verification](../../../README.md#system-verification)).
The Go command also needs Go ≥ 1.24.0 (CI installs the `go.mod` version).

This directory has no tests of its own. `errgroup` is exercised only through
`examples/weighted-semaphore/semaphore/semaphore_test.go`, which
`go test ./...` runs.

- Run: `cd examples/weighted-semaphore && go test -race ./...`
- CI step "weighted semaphore accepted decisions" (job `consistency`) runs the
  same `go test -race ./...` among its checks:
  - Run: `python3 examples/weighted-semaphore/verify_q01.py`
