# Open questions

These questions concern the current API and documented behavior. References point to the as-is outcome and its source and probe citations in `final.json`.

- **F01**. Should a callback follow replacement of its wrapper when the replacement accepts the captured generation?
- **F02**. Is sharing A via a shallow wrapper copy a supported public use?
- **F03**. Should replacement mismatches be silent and should the original admission remain charged? README.md:77-79 covers clearing on one breaker.
- **F04**. Should an unrelated callback be able to advance a replacement's state even when its result is discarded?
- **F05**. Should a foreign completion be able to close a replacement when the numeric generation matches after expiry?
- **F06**. Should a foreign completion be able to reopen a replacement before it has admitted a probe?
- **F07**. What validity contract applies to a captured wrapper overwritten with a zero value?
- **F08**. What public contract applies when the active receiver storage is overwritten from an unused breaker value during req? Go sync.Mutex documents the separate constraint that a mutex must not be copied after first use.
- **F09**. Is done defined as exactly once, repeatable, or expected to signal misuse?
- **F10**. Can repeated reports from one admission satisfy the full half-open threshold?
- **F11**. What is the expected recovery when a half-open owner leaves without reporting? README.md:41-43 limits admission but says nothing about abandonment.
- **F13**. explicit-requirement README.md:77-79 covers outcome exclusion after clearing. Should Counts itself advance an expired window, and should completion be allowed to trigger the reset?
- **F14**. Should documentation specify that caller departure leaves both worker cancellation and delivery cleanup to the caller, while a later return can still account?
- **F15**. Should an obsolete result still run IsSuccessful and its external side effects?
- **F16**. explicit-requirement README.md:90-91 covers a request panic. Should classifier panics have the same failure-reporting semantics?
- **F17**. Should a trip predicate panic trigger a second accounting attempt, and should it count again if the generation is still current?
- **F18**. Which panic should escape when retry accounting also panics?
- **F19**. What commit and propagation contract applies to a failed completion notification, including a later expiry observed during Execute's recovery attempt?
- **F20**. Should a failed expiry notification abort first admission while preserving the new state?
- **F21**. Should a result headed for discard surface an expiry notification panic, and should Execute and TwoStep behave differently if their panic paths differ?
- **F22**. Which callbacks are allowed to reenter breaker APIs or wait for work using the same breaker?
- **F23**. explicit-requirement README.md:25-36 frames Settings as constructor configuration. Should capture lifetime and subsequent mutation be documented?
- **F24**. Should the TwoStep constructor explicitly document that done bypasses the configured IsSuccessful function?

F12 is a documented control. README.md:77–79 covers accounting exclusion after clearing on the same breaker. It leaves replacement identity and pre-guard refresh effects open.

- **F13/F17**. When a trip predicate runs across a closed deadline, should the original failure and the sampled time govern the trip or should the elapsed deadline take precedence? If the hook panics, may another state-aware operation win the order before recovery reports?
- **F19/F21**. If a completion hook consumes the whole Open timeout, should Execute recovery also deliver the HalfOpen notification? Which panic should the caller see if that second hook fails?
