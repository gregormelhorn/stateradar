# Late-completion scenario checks

`tools/late_completion.py` is a reusable, language-neutral behavioral oracle.
The component adapter controls execution and emits observations; the oracle
chooses the verdict. It integrates with `tools/check_fault_mutants.py` through
its existing complete-cell protocol. The first executed binding is grpc-go
addrConn. A second-component binding has not yet been validated.

## Contract and scope

A profile declares two orderings of one started operation:

1. `start → terminate → complete → observe`: completion cannot revive the
   component, publish the returned resource or emit a new effect; the returned
   resource must be released exactly once.
2. `start → complete → terminate → observe`: the positive control must actually
   observe accepted state, resource publication, a live resource and the declared
   acceptance effect before termination. Termination removes publication and
   releases that idle resource exactly once.

These obligations must be supported by the component's accepted contract/DR.
They are not universal semantics for every async API: draining resources with
active users or APIs with allowed post-terminal effects need a different profile
contract, not fabricated observations or silently relaxed checks. This version
checks the stated terminal/idle-resource contract. It does not cover retries,
duplicate completion, replacement instances, arbitrary concurrent schedules or
whole-system liveness. Watchdogs bound the experiment, not domain latency.

## Profile

The reference is `examples/grpc-addrconn/late-completion/profile.json`:

```json
{
  "formatVersion": 1,
  "terminalState": "Stopped",
  "acceptedState": "Active",
  "acceptanceEffect": "accepted",
  "cases": [
    {"id":"late","cell":"Stopped x Complete","order":["start","terminate","complete","observe"]},
    {"id":"early","cell":"Starting x Complete","order":["start","complete","terminate","observe"]}
  ]
}
```

Both orderings, distinct scenario IDs/cell references and distinct accepted and
terminal states are mandatory. The component may attach extra adapter metadata
(e.g. `checkpoint`) or decision links. These extra fields are not domain proofs.
`cell` links the scenario to the declared behavioral target; the scenario list
is not a total state/event matrix. One scenario can perform several transitions.

## Observations and adapter obligations

Each executed repetition emits one record per scenario:

```json
{
  "case": "late", "repeat": 0,
  "steps": [
    {"action":"start", "state":"Starting", "published":false,
     "releaseCount":0, "effects":[], "resource":"operation-resource-1", "parentAlive":true},
    {"action":"terminate", "state":"Stopped", "published":false,
     "releaseCount":0, "effects":[], "resource":"operation-resource-1", "parentAlive":true},
    {"action":"complete", "state":"Stopped", "published":false,
     "releaseCount":1, "effects":[], "resource":"operation-resource-1", "parentAlive":true},
    {"action":"observe", "state":"Stopped", "published":false,
     "releaseCount":1, "effects":[], "resource":"operation-resource-1", "parentAlive":true}
  ]
}
```

Observations are taken after the named action. `start` means the operation has
reached the selected pending-completion checkpoint; it may already own the
resource when testing delayed notification. `published` means the resource is
attached as usable to the component. `effects` is the cumulative sequence at
the actual outward notification seam. `releaseCount` counts logical releases
of this resource, not incidental cleanup of another object. Resource identity
must remain stable within each trace. `parentAlive` witnesses independence from
parent shutdown; APIs without a parent can use an explicitly documented always
live environment scope. Do not claim a parent-lifecycle test in that case.

The adapter must establish the exact test identity set and repetition counts,
normal package/test completion and complete traces. Compilation failures,
crashes, missing tests and watchdog timeouts are execution failures, not kills.
It must read projections and effects rather than write the expected state, and
perform parent cancellation/emergency cleanup only after observations. The
shared parser rejects duplicate/missing/foreign records, invalid order/types,
changed identities, lost effects and decreasing release counts. It cannot
prove that an arbitrary producer reports honestly: independent executed
projection canaries and review of the adapter are required.

## Running and integrating

Replay previously captured observations:

```sh
python tools/late_completion.py profile.json observations.json --count 10
```

The adapter can call `report(profile, observations, repetitions)` directly.
Exit 0 means all scenario checks passed; exit 1 means complete behavioral
failures with named `CELL FAIL` and one `CELL SUITE` summary. Malformed evidence
raises `EvidenceError` (CLI exit 2). `--weak` preserves structural/discovery
checks but asserts only the immediate terminal state. It exists for diagnostic
weak/full comparisons and must never be used as the acceptance suite.

Set `expectedCells` to the number of distinct scenario cell references, not
repetitions or total intermediate transitions. Require projection canaries via
`mutant-generation.json`; the [generic dependency runner](fault-mutants.md)
executes them and blocks dependent mutants unless each prerequisite is KILLED.
Use independently targeted canaries for state/publication, output and resource
release. A CANARY label alone does not establish independence: the addrConn
reference replays each canary and checks its exact, isolated failure reason.

Reference acceptance:

```sh
python tools/addrconn_late.py --checkout /path/to/clean/pinned/grpc-go --output-dir /tmp/late-evidence
```

The reference substitutes an idle transport factory, retains the actual
`createTransport` guards, and places scheduling barriers after its return and
before notification. It invokes real `tearDown` and `resetTransport`, observes
real state/publication and the ClientConn notification boundary, and keeps
ClientConn live. The fake Close releases the fake resource and reenters the
addrConn state accessor; it does not prove real HTTP/2 transport internals.
The baseline's missing guards are a historical defect; only guard removals
from the corrected DR-001 evaluation source are scored as mutants.

The retained historical regression tests have a separate adapter: the pinned
recording-balancer builder shares mutable state between connections. An observed
race is retained as evidence. A public-registry builder adapter returns a new
recorder per connection while leaving all test files and assertions unchanged.
Both historical and corrected source run those same adapted tests. See the
evidence report for the original failure and the non-reproducing pristine sample.
