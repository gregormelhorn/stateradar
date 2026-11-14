"""Bounded aggregate/queue model, not a proof of the Go implementation."""
import argparse
from collections import deque


def notify(size, state):
    held, queue = state
    queue = list(queue)
    while queue and queue[0] <= size - held:
        held += queue.pop(0)
    return held, tuple(queue)


def explore(size, old_guard):
    start = (0, ())
    paths = {start: []}
    pending = deque([start])
    failures = []
    while pending:
        state = pending.popleft()
        held, queue = state
        if notify(size, state) != state:
            failures.append((state, paths[state]))
        next_states = []
        for weight in range(size + 1):
            # With no queued predecessor a fitting Acquire or TryAcquire grants.
            # Failed TryAcquire, invalid input and oversized rejection are no-ops.
            if not queue and weight <= size - held:
                after = (held + weight, queue)
            elif len(queue) < 4:
                after = (held, queue + (weight,))
            else:
                continue  # Exploration bound only, not an API rejection rule.
            next_states.append((f'Acquire({weight})', after))
        # Successful holder releases and granted-call rollback share this effect.
        for weight in range(held + 1):
            next_states.append((f'Release({weight})', notify(size, (held - weight, queue))))
        for index in range(len(queue)):
            after = (held, queue[:index] + queue[index+1:])
            if index == 0 and (not old_guard or size > held):
                after = notify(size, after)
            next_states.append((f'CancelQueued({index})', after))
        for event, after in next_states:
            assert 0 <= after[0] <= size
            if after not in paths:
                paths[after] = paths[state] + [event]
                pending.append(after)
    return len(paths), failures


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--old-head-guard', action='store_true')
    args = parser.parse_args()
    total = failures = 0
    for size in range(5):
        count, counterexamples = explore(size, args.old_head_guard)
        total += count
        failures += len(counterexamples)
        print(f'capacity={size}, reachable={count}, Release(0)-changes={len(counterexamples)}')
        if counterexamples:
            state, trace = counterexamples[0]
            print(f'  example: {trace} -> held/queue={state}; Release(0) -> {notify(size,state)}')
    print(f'BOUND: capacities 0..4, queue length <=4; {total} reachable aggregate/queue states')
    print(f'RESULT: {failures} states where Release(0) changes holdings or queue')
    raise SystemExit(1 if failures else 0)
