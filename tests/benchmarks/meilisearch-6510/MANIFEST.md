# meilisearch — S3 Snapshot Multipart Cancel

**Issue:** [#6510](https://github.com/meilisearch/meilisearch/issues/6510)
**Commit:** fff2ef5a42658b16a937d922aabc3fb7f89f2018
**Date:** 2026-08-06
**Oracle:** Confirmed by internal investigation. Closed.

## Primary finding

**Missing transition:** `Uploading × cancel → Aborted` without child quiescence.

When an enterprise S3 snapshot is cancelled after `CreateMultipartUpload`
succeeds, `multipart_stream_to_s3` returns `Err(Error::AbortedTask)` but
drops the `in_flight` queue of spawned part-upload tasks. Each
`JoinHandle::drop` detaches the child task per Tokio's documented behavior.
The detached retry loops can continue issuing PUTs. No
`AbortMultipartUpload` is sent to S3.

**Defect class:** Structured-cancellation violation (F-07 lifecycle coupling,
F-20 blocked progress). Parent operation reports cancellation but child
tasks are not synchronized and the remote multipart transaction has reached
neither completion nor abort.

**Oracle match:** The issue describes "Cancelling an enterprise S3 snapshot
can detach part uploads without aborting the multipart upload." StateRadar
independently derived the identical mechanism from the source code.

## StateRadar output

- **Lifecycle disagreement (PA-21):** The parent function lifecycles
  (`multipart_stream_to_s3` returns) and child task lifecycles (spawned
  retry loops) are not synchronized on cancel.
- **Fix direction:** Join all `in_flight` tasks before returning, then
  send `AbortMultipartUpload` to S3.
