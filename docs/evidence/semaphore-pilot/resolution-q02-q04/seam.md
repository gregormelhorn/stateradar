# Observation seam

Use the public constructor, Acquire/TryAcquire/Release, returned errors, panic
recovery and completion channels. Capacity is projected by TryAcquire and a
matching Release, never by reading or setting the counter. Queued scenarios
reuse DR-001's read-only enqueue barrier solely for deterministic setup.
Tests observe both successful notification after a valid release and preserved
capacity after a rejected call. Timeouts bound failed tests, not API latency.
