# Open questions — meilisearch S3 multipart upload

## Q-01: internal events in inactive states

**Status:** OPEN  
**Fault:** F-06 (undocumented state/event)  
**Trigger:** step-4 matrix walk

Events `create_succeeds`, `create_fails`, `part_ready`, `part_succeeds`,
`part_fails`, `part_permanent_fail`, `all_parts_done`, `complete_succeeds`,
`complete_fails` are structurally unreachable outside the active
upload path. In `NoUpload`, `UploadCreated`, `Completed`, `Aborted`
states they are `ignore (accidental)`. The function does not guard
against these transitions at the type level; correctness relies on
caller discipline and single-invocation semantics.

**Options:** document as structurally unreachable | add type-state guards

## Q-02: cancel orphans child tasks and S3 multipart upload — issue #6510

**Status:** OPEN  
**Fault:** F-07 (lifecycle coupling), secondary F-20 (blocked progress)  
**Trigger:** step-4 matrix walk; doctrine mapping (DOC-1 through DOC-4)

When `must_stop_processing.get()` returns true in the part loop,
`multipart_stream_to_s3` returns `Err(Error::AbortedTask)` immediately.
The local `in_flight: VecDeque<(JoinHandle<...>, Bytes)>` is dropped.
Each `JoinHandle::drop` detaches the spawned task per Tokio's documented
behavior. The retry loop inside the detached task can continue issuing
PUTs. No `AbortMultipartUpload` is sent to S3.

**Evidence:** `s3.rs:multipart_stream_to_s3` part loop — 
`if must_stop_processing.get() { return Err(Error::AbortedTask); }`

**Options:**
1. Join all `in_flight` tasks before returning, then send `AbortMultipartUpload`
2. Abort all `in_flight` tasks (`JoinHandle::abort()`), join, then abort upload
3. Track the upload ID across the cancel boundary and abort asynchronously

**Proposed:** Option 1 — join in_flight tasks, send AbortMultipartUpload,
return AbortedTask only after both complete. This satisfies DOC-1 through DOC-4.

## Summary

| Metric | Value |
|---|---|
| States | 5 (NoUpload, UploadCreated, Uploading, Completed, Aborted) |
| Events | 13 (10 base + 3 UV) |
| Interaction pairs | 0 (single external source) |
| Matrix cells | 5 × 13 = 65 |
| UNSPECIFIED cells | 4 (all Q-02: Uploading × cancel and UV variants) |
| ignore (accidental) | 18 (all Q-01) |
| Guard groups | 2, both not-formalizable |
| Proven | 0 |
| Violations | 0 |
| Findings | 2 (C-01 child detach, C-02 abort not sent) |
| Open questions | 2 |
