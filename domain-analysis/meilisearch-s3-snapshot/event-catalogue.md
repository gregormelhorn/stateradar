# Event catalogue — meilisearch S3 multipart upload

<!-- event-ids: create_succeeds create_fails part_ready part_succeeds part_fails part_permanent_fail all_parts_done cancel complete_succeeds complete_fails UV-cancel-duplication UV-cancel-out-of-order UV-cancel-commission -->

| id | event | source | classification | payload |
|---|---|---|---|---|
| create_succeeds | S3 CreateMultipartUpload returns OK | S3 | internal | upload_id |
| create_fails | S3 CreateMultipartUpload error | S3 | internal | error |
| part_ready | buffer full, spawn part upload | pipe | internal | part_number, body |
| part_succeeds | S3 PUT part returns etag | S3 | internal | etag |
| part_fails | S3 PUT transient error | S3 | internal | error (retried) |
| part_permanent_fail | S3 PUT client error | S3 | internal | error (fatal) |
| all_parts_done | reader exhausted, all parts uploaded | pipe | internal | etags list |
| cancel | scheduler sets must_stop_processing | scheduler | external | flag |
| complete_succeeds | CompleteMultipartUpload OK | S3 | internal | success |
| complete_fails | CompleteMultipartUpload error | S3 | internal | error |
| UV-cancel-duplication | duplicate cancel | scheduler | undesired | duplication |
| UV-cancel-out-of-order | stale cancel after completion | scheduler | undesired | out-of-order |
| UV-cancel-commission | unsolicited cancel | scheduler | undesired | commission |

## Event annotations

### cancel
- gate: flag
- upstream_guards: set by scheduler task cancellation (`s3.rs:process_snapshot_to_s3`, `must_stop_processing` flag)
- coverage:
  - loss: n/a: atomic flag, no loss possible
  - delay: n/a: flag check is synchronous in loop
  - duplication: UV-cancel-duplication
  - out-of-order: UV-cancel-out-of-order
  - contradiction: n/a: cancel is monotonic (once set, stays set)
  - commission: UV-cancel-commission
  - value: n/a: boolean flag, no value fault possible

### create_succeeds
- gate: result identity
- upstream_guards: S3 response status check (`s3.rs:CreateMultipartUpload response`)
- coverage:
  - loss: n/a: internal
  - delay: n/a: already awaited
  - duplication: n/a: single result
  - out-of-order: n/a: single invocation
  - contradiction: n/a: single invocation
  - commission: n/a: only delivered by known call
  - value: n/a: S3 validated

### create_fails
- gate: result identity
- upstream_guards: S3 response status check
- coverage:
  - loss: n/a: internal
  - delay: n/a: already awaited
  - duplication: n/a: single result
  - out-of-order: n/a: single invocation
  - contradiction: n/a: single invocation
  - commission: n/a: only delivered by known call
  - value: n/a: S3 validated

### part_ready
- gate: buffer capacity
- upstream_guards: pipe reader chunk read (`s3.rs:reader loop`)
- coverage:
  - loss: n/a: internal
  - delay: n/a: synchronous
  - duplication: n/a: part_number sequenced
  - out-of-order: n/a: sequential loop
  - contradiction: n/a: single producer
  - commission: n/a: loop body only
  - value: n/a: size validated

### part_succeeds
- gate: result identity
- upstream_guards: S3 response, etag extraction (`s3.rs:collect etag`)
- coverage:
  - loss: n/a: internal
  - delay: n/a: already awaited
  - duplication: n/a: single etag per part_number
  - out-of-order: n/a: etags collected in order
  - contradiction: n/a: single result per spawn
  - commission: n/a: only from spawned task
  - value: n/a: S3 validated

### part_fails
- gate: retry
- upstream_guards: transient error classification in retry loop (`s3.rs:transient error match`)
- coverage:
  - loss: n/a: retry loop
  - delay: n/a: backoff in retry
  - duplication: n/a: idempotent PUT
  - out-of-order: n/a: part numbers sequenced
  - contradiction: n/a: single result per spawn
  - commission: n/a: spawned by known loop
  - value: n/a: S3 validates on success

### part_permanent_fail
- gate: result identity
- upstream_guards: client error status check (`s3.rs:client_error match`)
- coverage:
  - loss: n/a: internal
  - delay: n/a: already awaited
  - duplication: n/a: single result
  - out-of-order: n/a: single invocation
  - contradiction: n/a: permanent error by definition
  - commission: n/a: only from spawned task
  - value: n/a: S3 validated

### all_parts_done
- gate: reader EOF
- upstream_guards: pipe reader exhaustion (`s3.rs:reader EOF`)
- coverage:
  - loss: n/a: internal
  - delay: n/a: synchronous after last part
  - duplication: n/a: single transition
  - out-of-order: n/a: after all parts complete
  - contradiction: n/a: single producer
  - commission: n/a: only from loop completion
  - value: n/a: etags already validated

### complete_succeeds
- gate: result identity
- upstream_guards: S3 response status check (`s3.rs:CompleteMultipartUpload response`)
- coverage:
  - loss: n/a: internal
  - delay: n/a: already awaited
  - duplication: n/a: single invocation
  - out-of-order: n/a: only after all parts
  - contradiction: n/a: only called once
  - commission: n/a: only from known path
  - value: n/a: S3 validated

### complete_fails
- gate: result identity
- upstream_guards: S3 response status check
- coverage:
  - loss: n/a: internal
  - delay: n/a: already awaited
  - duplication: n/a: single invocation
  - out-of-order: n/a: only after all parts
  - contradiction: n/a: only called once
  - commission: n/a: only from known path
  - value: n/a: S3 validated

## Remembrance semantics

The multipart upload leaves behind a `multipart` object carrying the
`upload_id`. When the function returns `Err(AbortedTask)`, the
`multipart` goes out of scope. The `upload_id` is not remembered. Late
references (the spawned retry tasks) continue running but can no longer
complete or abort the upload because the `multipart` object is gone.

## Undesired-coverage

| source | loss | delay | duplication | out-of-order | contradiction | commission | value |
|---|---|---|---|---|---|---|---|
| scheduler (cancel) | n/a: atomic flag | n/a: synchronous check | UV-cancel-duplication | UV-cancel-out-of-order | n/a: monotonic | UV-cancel-commission | n/a: boolean |
| S3 (create_succeeds) | n/a: internal | n/a: awaited | n/a: single result | n/a: single invocation | n/a: single invocation | n/a: known call | n/a: S3 validated |
| S3 (create_fails) | n/a: internal | n/a: awaited | n/a: single result | n/a: single invocation | n/a: single invocation | n/a: known call | n/a: S3 validated |
| S3 (part_succeeds) | n/a: internal | n/a: awaited | n/a: single etag | n/a: order preserved | n/a: single result | n/a: spawned task | n/a: S3 validated |
| S3 (part_fails) | n/a: retry loop | n/a: backoff | n/a: idempotent PUT | n/a: sequenced parts | n/a: single result per spawn | n/a: known loop | n/a: S3 validates on success |
| S3 (part_permanent_fail) | n/a: internal | n/a: awaited | n/a: single result | n/a: single invocation | n/a: permanent error | n/a: spawned task | n/a: S3 validated |
| S3 (complete_succeeds) | n/a: internal | n/a: awaited | n/a: single invocation | n/a: only after parts | n/a: only called once | n/a: known path | n/a: S3 validated |
| S3 (complete_fails) | n/a: internal | n/a: awaited | n/a: single invocation | n/a: only after parts | n/a: only called once | n/a: known path | n/a: S3 validated |
| pipe (part_ready) | n/a: internal | n/a: synchronous | n/a: part_number sequenced | n/a: sequential loop | n/a: single producer | n/a: loop body only | n/a: size validated |
| pipe (all_parts_done) | n/a: internal | n/a: synchronous | n/a: single transition | n/a: after all parts | n/a: single producer | n/a: loop completion | n/a: etags validated |

## Interaction pairs

No cross-source interaction pairs. The only external event source is the
scheduler; all other events are internal (S3 responses, pipe reads). A
per-source checklist covers `cancel` variants; there is no second
external source to race against.
