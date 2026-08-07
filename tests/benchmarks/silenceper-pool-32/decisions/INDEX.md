# Decision index — silenceper/pool channelPool

| Question | Decision record | Summary |
|---|---|---|
| Q-01 | [DR-001](DR-001.yaml) | `Release()` unblocks queued `Get()` calls with `ErrMaxActiveConnReached`. |
| Q-02 | [DR-002](DR-002.yaml) | The caller returns or closes one genuine borrowed connection exactly once. |
| Q-03 | [DR-003](DR-003.yaml) | `Put()` after `Release()` is a safe terminal no-op; callers clean up outstanding borrows. |
| Q-04 | [DR-004](DR-004.yaml) | Every `Get()` result passes configured Ping validation; failures are discarded and retried. |
| Q-05 | [DR-005](DR-005.yaml) | Factory errors return without consuming capacity; initialization failure aborts construction. |
| Q-06 | [DR-006](DR-006.yaml) | `openingConns >= 0` holds under valid caller ownership; no duplicate-close guard is added. |
