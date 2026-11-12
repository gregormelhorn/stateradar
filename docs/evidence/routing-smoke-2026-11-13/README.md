# Routing smoke run, 2026-11-13

First live run of the model routing on the maintainer's machine, against
`examples/device-connection/README.md`, at commit 1937f0a of the
`model-routing-flash-jev` branch. Ledger limit 500,000 microdollars.
These files are the unedited outputs; `ledger-status.json` was read
afterwards at e4f5243 (the ledger format is unchanged).

| File | Command |
|---|---|
| `task.md`, `draft-verify.json` | `draft-verify examples/device-connection/README.md task.md --output draft-verify.json --model jev-1.14.0` |
| `checks.json`, `jev-batch.json` | `jev-batch examples/device-connection/README.md checks.json --model jev-1.14.0` |
| `blind.md`, `blind.stdout` | `blind examples/device-connection/domain-analysis/device-connection/run1 --requirements examples/device-connection/README.md --contracts examples/device-connection/README.md` |
| `ledger-status.json` | `status` |

What the files show:

* No provider error; all four calls settled, 8,245 microdollars in total.
* `draft-verify`: 23 claims, all citations `ok`, all 23 judged `supported`.
  Ordering claims C21 and C22 came back `supported` with
  `ordering_scope_probability` 0.17 and 0.11.
* `jev-batch`: S1 (retry exhaustion enters FAILED) `supported` at 0.71,
  while the same statement as draft claim C10 scored 1.0 with a different
  fragment. O1 (disconnect after FAILED) `unclear`, scope 0.03.
* `blind`: coverage OK with 21 events and 0 pair orderings, because the
  example catalogue carries no `P-` ids. `blind.stdout` still shows the
  temporary package path that was fixed afterwards. The README stood in
  for contract text, since the example has none.
