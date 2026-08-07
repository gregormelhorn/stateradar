# Invariants and lint findings — meilisearch S3 multipart upload

<!-- doc-ids: DOC-1 DOC-2 DOC-3 DOC-4 -->

## NAT invariants

- NAT-01: `tokio::spawn` returns a `JoinHandle` whose `drop` detaches the
  task; the task continues running. [Tokio 1.52.3 docs]
- NAT-02: S3 responses are well-formed per the AWS S3 REST API.
- NAT-03: `must_stop_processing.get()` returns true within one loop
  iteration after the scheduler sets it. [inferred from tokio flag
  semantics]

## SYS invariants

- INV-01: Every created multipart upload reaches a terminal S3 state
  (`CompleteMultipartUpload` or `AbortMultipartUpload`) before the
  function returns. **VIOLATED** on the cancel path: dropping
  `in_flight` detaches child tasks and no `AbortMultipartUpload` is
  sent. [Q-02]
- INV-02: When `Error::AbortedTask` is returned, no child network
  activity continues. **VIOLATED**: detached retry tasks can issue
  further PUTs after the function returns. [Q-02]

## Doctrine mapping

| DOC | target | detail |
|---|---|---|
| DOC-1 | cell | Uploading x cancel | UNSPECIFIED — code returns AbortedTask without quiescing children |
| DOC-2 | invariant | SYS-INV-01 | Every multipart upload must reach terminal S3 state — violated on cancel |
| DOC-3 | invariant | SYS-INV-02 | AbortedTask means child activity stopped — violated on cancel |
| DOC-4 | cell | Uploading x cancel | in_flight dropped without joining children — same cell as DOC-1 |

## Lint checklist

| lint | result |
|---|---|
| waiting/connecting/stopping without timeout | `in_flight` has no join timeout; spawned tasks are never awaited on cancel |
| retries without maximum | `backoff::ExponentialBackoff` used without explicit `max_elapsed_time` on part uploads. Defaults exist but are not citable from source. |
| external operations without failure outcome | `AbortMultipartUpload` exists in SDK but is never called on cancel path |
| cancellation handling | Cancel returns without quiescing children. [Q-02] |
| terminal/error states without documented meaning | `Aborted` returns `Err(AbortedTask)` but leaves S3 and child tasks in unknown state |
| startup/shutdown | No explicit shutdown sequence; cancel is the only termination |
| lifecycle disagreement (PA-21) | Parent (multipart_stream_to_s3) and child (spawned task) lifecycles are not synchronized on cancel. [Q-02] |
| dual ownership cleanup (PA-23) | `multipart` object is owned by the function; spawned tasks hold cloned references. Drop order determines cleanup — JoinHandles drop first, detaching tasks, then multipart drops, making upload_id unreachable. |
| async cancellation isolation (PA-24) | Uploaded body bytes (`Bytes`) are transferred to spawned tasks via `in_flight`. When in_flight drops, the Bytes may still be referenced by detached tasks. |
