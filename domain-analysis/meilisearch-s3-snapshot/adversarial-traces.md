# Adversarial traces — meilisearch S3 multipart upload

## Interaction pairs

No cross-source pairs — only one external event source (scheduler).
Per-source checklist covers `cancel` variants.

## Systematic traces

### T-01: Happy path (control trace)

1. `NoUpload` × `create_succeeds` → `UploadCreated` (`s3.rs:create OK`)
2. `UploadCreated` × `part_ready` → `Uploading` (`s3.rs:first part`)
3. `Uploading` × `part_succeeds` → `Uploading` (`s3.rs:etag collected`)
4. `Uploading` × `all_parts_done` → `Completed` (`s3.rs:complete OK`)
none — control trace

### T-02: Cancel during upload — the #6510 defect

1. `Uploading` — 3 parts spawned into `in_flight`
2. Scheduler sets `must_stop_processing`
3. `Uploading` × `cancel` → function returns `Err(AbortedTask)`
4. `in_flight` dropped — 3 `JoinHandle`s detach
5. Detached retry task #1: PUT succeeds, etag received — but nobody collects it
6. Detached retry task #2: transient error, retries, succeeds
7. No `AbortMultipartUpload` sent → upload ID leaked at S3
8. **Q-02:** claimed `Aborted` but child activity continued, no abort sent

### T-03: Cancel before any upload

1. `NoUpload` × `cancel` → `ignore (documented)` — nothing to cancel
none — control trace

### T-04: Cancel after CreateMultipartUpload, before loop

1. `NoUpload` × `create_succeeds` → `UploadCreated`
2. `UploadCreated` × `cancel` → `Aborted` (`s3.rs:must_stop_processing before loop`)
3. `multipart` drops — upload ID leaked (no AbortMultipartUpload sent)
4. **Q-02:** same as T-02 — upload ID abandoned

### T-05: Permanent part failure

1. `Uploading` — part spawned
2. S3 returns 4xx client error (non-retryable) → `part_permanent_fail`
3. `Uploading` × `part_permanent_fail` → `Aborted`
4. `in_flight` dropped, no `AbortMultipartUpload` sent
5. **Q-02:** same cleanup gap

### T-06: CompleteMultipartUpload fails

1. `Uploading` — all parts done
2. `Uploading` × `all_parts_done` → calls `CompleteMultipartUpload`
3. S3 returns error → `complete_fails` → `Aborted`
4. No `AbortMultipartUpload` sent — upload ID leaked
5. **Q-02:** same gap

### T-07: Cancel duplication

1. `Uploading` — scheduler sets `must_stop_processing`
2. `Uploading` × `cancel` → returns `Err(AbortedTask)`
3. Caller receives error, but scheduler flag remains set
4. Caller retries? UV-cancel-duplication: second cancel arrives on already-cancelled state
5. Function not re-entrant — second cancel is meaningless at this boundary

### T-08: Cancel after completion

1. `Uploading` × `all_parts_done` → `Completed`
2. Scheduler sets `must_stop_processing` — UV-cancel-out-of-order
3. Function already returned — late cancel has no effect at this boundary

### T-09: Detached retry issues PUT after function returns

1. Part spawned, in retry backoff
2. Cancel sets `must_stop_processing`, function returns
3. Retry timer fires — task is detached, continues running
4. Issues new PUT to S3 — succeeds, gets etag
5. Nobody collects the etag; nobody completes or aborts the upload
6. **Q-02:** detached work violates structured cancellation

### T-10: Spurious cancel (commission)

1. `Uploading` — `must_stop_processing.get()` returns true
2. But scheduler never set it — UV-cancel-commission (flag corruption, cosmic ray, etc.)
3. Function aborts unnecessarily
4. `Aborted` transition with same cleanup gap

### T-11: Connection failure during CompleteMultipartUpload

1. All parts done, `CompleteMultipartUpload` POST sent
2. Network error → retry with backoff
3. Retries succeed or fail → `complete_succeeds` or `complete_fails`
4. On failure, same `Aborted` gap as T-06

## Multi-instance probes

Not applicable — `multipart_stream_to_s3` processes a single snapshot
stream. No shared external resource across instances within this boundary.
