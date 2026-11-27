# domain-analysis — StateRadar artifacts

Part of [weighted-semaphore](../README.md).

## Overview

StateRadar analysis artifacts for the weighted-semaphore evaluation copy. It
holds one analyzed component. For the prerequisites of its checkers, see the
[child prerequisites](weightedSemaphore/README.md#verification).

## Subdirectories & Boundaries

- weightedSemaphore:
  [`./weightedSemaphore/README.md`](./weightedSemaphore/README.md) - the
  reconciled state model (states, events and cell count are defined there),
  its [sidecar](../../../README.md#glossary) `analysis.json`, the
  [decision records (DRs)](../../../README.md#glossary) and the checkers for
  the analysis and for `examples/weighted-semaphore/semaphore`. The semaphore
  contract itself is in [the parent README](../README.md#semaphore).
