# Disposition matrix — meilisearch S3 multipart upload (as-is)

<!-- states: NoUpload UploadCreated Uploading Completed Aborted -->

Abstraction: five flat leaf states derived from the multipart upload
lifecycle; completeness is relative to the thirteen-event catalogue.
<!-- terminal: Completed, Aborted -->

| state | create_succeeds | create_fails | part_ready | part_succeeds | part_fails | part_permanent_fail | all_parts_done |
|---|---|---|---|---|---|---|---|
| **NoUpload** | transition →UploadCreated `s3.rs:create_multipart_upload OK` | transition →Aborted `s3.rs:create_multipart_upload error` | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |
| **UploadCreated** | ignore (documented) `s3.rs:1` | ignore (documented) `s3.rs:1` | transition →Uploading `s3.rs:part loop entry` | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 |
| **Uploading** | ignore (documented) `s3.rs:1` | ignore (documented) `s3.rs:1` | handle `s3.rs:spawn part upload into in_flight` | handle `s3.rs:collect etag` | handle `s3.rs:retry with backoff` | transition →Aborted `s3.rs:permanent error returned` | transition →Completed `s3.rs:complete_multipart_upload called` |

| state | cancel | complete_succeeds | complete_fails | UV-cancel-duplication | UV-cancel-out-of-order | UV-cancel-commission |
|---|---|---|---|---|---|---|
| **NoUpload** | ignore (documented) `s3.rs:1` | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (documented) `s3.rs:1` | ignore (documented) `s3.rs:1` | ignore (documented) `s3.rs:1` |
| **UploadCreated** | transition →Aborted `s3.rs:must_stop_processing before loop` | ignore (accidental) → Q-01 | ignore (accidental) → Q-01 | ignore (documented) `s3.rs:1` | ignore (documented) `s3.rs:1` | ignore (documented) `s3.rs:1` |
| **Uploading** | UNSPECIFIED → Q-02 **#6510**: returns Err(AbortedTask), drops in_flight queue. Each JoinHandle::drop detaches spawned task; retry loop can issue further PUTs. No AbortMultipartUpload sent to S3. | ignore (accidental) → Q-01 | transition →Aborted `s3.rs:complete error` | UNSPECIFIED → Q-02 | UNSPECIFIED → Q-02 | UNSPECIFIED → Q-02 |

## Guard notes

No formalizable guard groups. The only branch is `must_stop_processing.get()` (boolean), and `resp.status().is_client_error()` (external S3 status). Both are unstructured — `must_stop_processing` is runtime mutable, `is_client_error` depends on an external HTTP response.

- G-01 `must_stop_processing.get()`: not-formalizable: dynamic-state: set by scheduler in another task, not guarded by a type-level invariant.
- G-02 `status().is_client_error()`: not-formalizable: external-call: depends on S3 HTTP response, not formalizable within this boundary.
