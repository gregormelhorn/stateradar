# Stateful Component Scout — Candidate Selection Prompt

**How to use:** fill in the CONFIG block. Then paste this file into your coding agent at the repository root. The agent scans read-only. It proposes a ranked shortlist of components for the domain-behaviour pilot analysis. Each candidate card ends with a ready-to-paste CONFIG block for the pilot prompt. You can chain the two directly.

## CONFIG — fill in before running

```text
Repository root:        <.>
Focus (optional):       <dirs/packages to prioritize, or "all">
Exclude:                <vendored/generated dirs, e.g. node_modules, dist, build, migrations>
Max deep inspections:   <default: 12>
Shortlist size:         <default: 5>
```

---

## PROMPT

You scout a codebase for components that fit a StateRadar behaviour analysis (statecharts as specification and test oracle). You scan. You do not implement.

### Hard rules

1. Do not modify any file. Your only output is `domain-analysis/candidates.md`.
2. Every claim carries provenance. Cite file:line for code observations. Cite the command and a result summary for git-history observations. No candidate without evidence.
3. Statefulness alone does not qualify. Suitable means real **temporal** behaviour: lifecycles, connection management, protocol phases, asynchronous events, timeouts, retries, cancellation, recovery, sessions, mutually exclusive modes, concurrent coordination. Not suitable: pure calculations, stateless transformations, formatting, validation, and plain CRUD without temporal behaviour. A status column does not make a component suitable.
4. If nothing in the codebase qualifies: say so, explain briefly, and stop. A negative result is a valid result.

### Step 1 — Signal sweep

Make an inventory of the entry points and the long-lived objects (servers, workers, clients, sessions, managers, daemons). Then sweep the codebase for stateful signals. Adapt the patterns to the language in use:

* explicit state: state or status enums, state-pattern classes, `current_state` fields, transition tables
* implicit state: clusters of boolean flags (`is_*`, `has_*`, `*_pending`, `*_closing`), nullable references used as lifecycle markers, enum-plus-flag mixtures
* events and async work: handlers (`on_*`), callbacks, event emitters, subscriptions, queue or message consumers, sockets and websockets
* time: timers, deadlines, TTLs, backoff calculations, `sleep` inside loops, scheduled jobs
* retry and recovery: retry counters, `max_retries`, reconnect, resume, recover
* cancellation and shutdown: abort or cancel tokens, close, dispose, cleanup, drain, signal handlers
* concurrency coordination: locks, semaphores, in-memory queues and buffers, worker pools

Record every hit with file:line.

### Step 2 — Risk and pain evidence

Use git history if it is available. For the strongest hits, gather the bug-fix density and the churn over the last 12 months. Use `git log --oneline -- <path>`, filtered for fix, race, deadlock, timeout, leak, hang, stuck, retry. Collect TODO/FIXME/HACK/XXX comments and defensive oddities (broad exception handlers that mutate state, "should never happen" branches). Summarize per candidate with evidence. If there is no git history, note that and skip this step.

### Step 3 — Deep inspection and scoring

Inspect at most the configured number of candidates in depth. Score each dimension from 0 to 3:

* **Temporal richness.** Count states (explicit plus enumerated implicit flag combinations), events, timers, retry paths, and cancellation paths. Mark each count as measured or estimated.
* **Hole likelihood.** Look for contradictions, accidental fall-throughs, undocumented flag combinations, missing timeouts, unbounded retries, and absent cancellation handling.
* **Pain evidence.** Use the Step-2 results.
* **Seam quality.** Judge how feasible the later conformance seam is: a state-projection function, serialized single-event dispatch, and an injectable clock. 3 means a clean seam exists. 0 means the code smears state across globals, threads, or processes. Name the concrete projection you would use.
* **Boundedness.** The component must fit one bounded context and one pilot run. If it is too large, propose a sub-boundary and score that.

### Step 4 — Report

Write `domain-analysis/candidates.md` with four sections:

1. **Ranked shortlist.** One card per candidate with: name and paths; one or two lines on what it does; evidence bullets with file:line; the counts (states incl. implicit / events / timers / retries / cancellation paths); a risk summary; the seam assessment with the concrete state projection; the recommended machine boundary; the five scores; and a ready-to-paste CONFIG block for the pilot prompt:

   ```text
   Component under analysis:   <path>
   Entry points / public API:  <files, classes, handlers>
   Related tests:              <path, or "none">
   Requirements / docs:        <paths, or "none">
   Output directory:           domain-analysis/<component>/
   ```

2. **Recommended first pilot.** Pick one, with a rationale. Prefer high temporal richness, a decent seam, clear boundedness, and real pain evidence. Do not pick the biggest monster first. If one exists, list it separately as "highest long-term value, poor first pilot" and give the reason.

3. **Looks stateful, is not worth it.** List components that match on the surface but fail rule 3. Give one line of reasoning each.

4. **Coverage note.** State what you did not inspect and why (excluded dirs, inspection cap reached, unreadable areas).
