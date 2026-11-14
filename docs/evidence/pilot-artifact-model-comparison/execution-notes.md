# Execution notes

- Local implementation pack `8b8e854` passed the full gate set before live calls.
- A Terra availability smoke successfully read go.mod and called Jev through
  ChatGPT-authenticated Codex. It did not ask for artifact writes, so it did
  not detect the later permission contradiction. Smoke: 14.226 seconds,
  0.565435 Codex credits plus $0.000013 Jev; $0.0226304 at the stated credit
  conversion assumption. It is separate from pilot costs.
- The first driver accidentally chose macOS's default temporary directory
  outside `/tmp`. All four preparations were refused before model execution.
  The correct `/tmp` driver then started; no provider cost was incurred by
  those preparation refusals.
- Diagnostic root: `/tmp/stateradar-controller-4us5gpyo`, pack `8b8e854`.
  Terra/gobreaker ended after 36.661 seconds and eight successful commands,
  explicitly declining artifact writes because Codex declared read-only.
  Its completed usage is retained; this was not a service safety refusal.
- The runner permission declaration was corrected in `394ff35`, with an
  observed red regression, green regression and full gates. The independent
  command-server sandbox and credential restrictions were preserved.
- Matched root: `/tmp/stateradar-controller-matched-czn61wf4`, pack `394ff35`.
  All matched controllers use workspace-write in disposable checkouts,
  the same prompt, routed workflow, selective output and medium effort.
- Already-started diagnostic Sol runs were allowed to finish to preserve
  complete usage accounting. The diagnostic driver's later Pool/Terra call
  uses the corrected executable permission with the older pack archive;
  this is explicitly outside the matched comparison. No result from that
  heterogeneous diagnostic set is presented as a controlled model comparison.
- Matched Pool runs wait for diagnostic Pool runs to release port 7777.
  Gobreaker has no shared fixed port; its disposable checkouts can overlap.
- Matched Terra/gobreaker completed its Codex turn after 166.654 seconds
  but explicitly delivered an incomplete pilot. It wrote preliminary
  artifacts and made successful routing calls, so the prior write issue
  was resolved. It produced no accepted matrix, sidecar or blind pass.
  Completed controller usage and all seven settled provider calls are
  included in its cost; no missing work is scored as a saving.

- Matched Pool/Sol ended after 1113.858 seconds with `turn.failed`: the
  OpenAI service flagged possible cybersecurity risk. The summary had
  already been written. No subsequent Sol retry or prompt workaround was
  attempted. Pool/Terra had already started as the separately preplanned
  comparison arm; its prompt and settings were not changed to evade this.
- Pool/Sol's saved artifacts pass all six local postflight gates, strict
  regeneration is unchanged, and the 101-row blind classification audit
  passes. These post-abort checks were executed by the supervising session;
  they were not emitted by a successful runner exit.
- No Pool/Sol `turn.completed` usage event or usage.json exists. Provider
  ledger cost is $0.018026, but controller and combined cost remain null.
  The earlier diagnostic Pool/Sol cost is not substituted for the missing
  matched-run cost. BLOCKED(Pool full-cost comparison): missing final
  controller usage after service termination.
- Matched Pool/Terra ended after 161.758 seconds with an explicit incomplete
  report. Its final controller usage is available; all six postflight gates
  fail on missing artifacts. All four extraction calls succeeded.
