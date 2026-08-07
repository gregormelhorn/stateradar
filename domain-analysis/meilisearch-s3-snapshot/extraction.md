# Extraction — meilisearch S3 multipart upload

**Component:** `multipart_stream_to_s3()` in
`crates/index-scheduler/src/scheduler/enterprise_edition/s3.rs` at
commit `fff2ef5a42658b16a937d922aabc3fb7f89f2018`.
~200 LOC, Rust async/tokio.

## Scope statement

Machine boundary: the `multipart_stream_to_s3()` async function and its
immediate caller `process_snapshot_to_s3()`. This is one bounded
streaming-upload operation.

Actors: the scheduler (sets `must_stop_processing`), the S3 service
(receives HTTP multipart requests), the pipe reader (provides snapshot
bytes), the tokio runtime (spawns and detaches tasks).

Excluded: S3 bucket lifecycle management, credential rotation, snapshot
scheduling policies, index-scheduler task queue, and the broader snapshot
feature outside this one function.

## States (from loop-based model per v1.15)

The `for part_number in 1u16..` loop is the state transition engine. The
phase when a condition is checked determines the state.

| State | Condition | Terminal? |
|---|---|---|
| `NoUpload` | `CreateMultipartUpload` not yet called | No |
| `UploadCreated` | `CreateMultipartUpload` returned `upload_id` | No |
| `Uploading` | Inside part loop, `in_flight` queue exists | No |
| `Completed` | `CompleteMultipartUpload` returned OK | Yes |
| `Aborted` | Function returned `Err(AbortedTask)` or permanent error | Yes |

## Events

### External

| Event | Source | Payload |
|---|---|---|
| `cancel` | Scheduler | `must_stop_processing` flag set |

### Internal

| Event | Source | Payload |
|---|---|---|
| `create_succeeds` | S3 | `upload_id` |
| `create_fails` | S3 | error |
| `part_ready` | Pipe reader | part_number, body buffer |
| `part_succeeds` | S3 | etag string |
| `part_fails` | S3 | transient error (retried) |
| `part_permanent_fail` | S3 | client error (not retried) |
| `all_parts_done` | Pipe reader | EOF, etags list |
| `complete_succeeds` | S3 | success response |
| `complete_fails` | S3 | error response |

## Seam-contract sweep

| Seam | Contract | NAT candidate | Source |
|---|---|---|---|
| `tokio::spawn` | `JoinHandle::drop` detaches the task; it continues running | NAT-01: dropping a JoinHandle does not stop the task | Tokio 1.52.3 docs |
| S3 `CreateMultipartUpload` | Returns `upload_id` or HTTP error | NAT-02: S3 response is well-formed | AWS S3 API |
| S3 `UploadPart` | Returns etag or HTTP error | NAT-02 | AWS S3 API |
| S3 `CompleteMultipartUpload` | Finalizes upload with etags or returns error | NAT-02 | AWS S3 API |
| S3 `AbortMultipartUpload` | Best-effort cleanup of upload ID | NAT-02; exists in SDK but NOT called on cancel | AWS S3 API |
| `must_stop_processing.get()` | Returns true when scheduler cancels task | NAT-03: flag is set atomically, observed within one loop iteration | `s3.rs:caller` |

## Transitions

| From | Event | To | Code | Provenance |
|---|---|---|---|---|
| `NoUpload` | `create_succeeds` | `UploadCreated` | S3 CreateMultipartUpload returns OK | `s3.rs:create_multipart_upload` |
| `NoUpload` | `create_fails` | `Aborted` | Error propagated | `s3.rs:create error path` |
| `UploadCreated` | `part_ready` | `Uploading` | First part buffer filled | `s3.rs:part loop entry` |
| `Uploading` | `part_ready` | `Uploading` | Spawn part upload into `in_flight` | `s3.rs:spawn part` |
| `Uploading` | `part_succeeds` | `Uploading` | Collect etag | `s3.rs:collect etag` |
| `Uploading` | `part_fails` | `Uploading` | Backoff retry | `s3.rs:retry loop` |
| `Uploading` | `part_permanent_fail` | `Aborted` | Permanent error returned | `s3.rs:permanent error` |
| `Uploading` | `all_parts_done` | `Completed` | `CompleteMultipartUpload` called | `s3.rs:complete` |
| `Uploading` | `cancel` | `Aborted` | `must_stop_processing.get()` returns true, `Err(AbortedTask)` returned | `s3.rs:cancel path` |
| `UploadCreated` | `cancel` | `Aborted` | `must_stop_processing` check before loop | `s3.rs:early cancel` |

## Doctrine-line sweep (from issue #6510)

- DOC-1: Cancelling a snapshot must quiesce all child upload activity. [issue #6510 description]
- DOC-2: Every created multipart upload must reach `Complete` or `Abort` at S3. [issue #6510 invariant]
- DOC-3: Returning `Error::AbortedTask` means child activity has stopped. [issue #6510 structured-cancellation invariant]
- DOC-4: Dropping `in_flight` must not orphan network work. [issue #6510 ownership mismatch]

## Contradictions

C-01: The code returns `Err(AbortedTask)` which documents "child activity
has stopped" per DOC-3, but the dropped `in_flight` queue detaches
spawned retry tasks which can continue issuing PUTs. No
`AbortMultipartUpload` is sent. **This is the #6510 finding.**

C-02: `multipart_stream_to_s3` calls `bucket.upload_part()` which exists
in the S3 SDK, but `bucket.abort_multipart_upload()` is never called on
the cancel path. The abort method exists and is unused on this path.
