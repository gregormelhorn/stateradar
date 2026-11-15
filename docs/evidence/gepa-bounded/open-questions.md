# Remaining contract question from supervising review

## Q-GEPA-01 — OPEN: scope of the func-timer Stop documentation

`upstream/timer/sleep.go:67` says Stop returns false if a timer expired **or was
already stopped**. Lines 70–72 then say, for a func timer, false means it expired
and the callback started. These statements cannot both be universal: stopping a
far-future AfterFunc timer successfully and then stopping it again returns false
although the first stop prevented the callback. The independent public-seam
control `TestRepeatedStopFalseBeforeCallback` executes this counterexample.

Question: should the func-timer sentence be scoped to an expired timer excluding
already-stopped registrations, or should its upstream wording be corrected?
The Go contract owner must decide normative wording; this experiment does not.
Proposed interpretation: distinguish first-stop/expiry from repeated-stop causes,
report the observed behavior and retain the scope question. No upstream issue or
message was sent and no requirement was silently changed.

Three Flash drafts generalize the narrower sentence (timer repetitions 0/C2,
1/C2 and 2/C3); Jev calls it supported because its cited text says so. This is
exactly why source-fragment checks and Jev confidence are not semantic proof.
The claim is outside the frozen seven timer obligations, so the primary 7/7 score
does not assess it. The supervising review found this limitation; it is **not**
credited as a GEPA or fixed-review discovery. Historical model outputs stay intact.
