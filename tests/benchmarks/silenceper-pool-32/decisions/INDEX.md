# Decision index — silenceper/pool channelPool

| Question | Decision record | Summary |
|---|---|---|
| Q-01 | [DR-001](DR-001.yaml) | `Release()` unblocks queued `Get()` calls with `ErrMaxActiveConnReached`. |
| Q-02 | [DR-002](DR-002.yaml) | The caller returns or closes one genuine borrowed connection exactly once. |
| Q-03 | [DR-003](DR-003.yaml) | `Put()` after `Release()` is a safe terminal no-op; callers clean up outstanding borrows. |
