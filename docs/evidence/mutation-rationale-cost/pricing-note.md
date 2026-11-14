# Pricing verification during execution

The frozen runner and both arms keep identical accounting. No live settings or
ledger amounts were changed after the first arm started.

Official prices checked on 2026-11-14:

- [OpenAI Standard credit rates](https://learn.chatgpt.com/docs/pricing): Sol
  uses 50 / 2.5 / 250 credits per million uncached input / cached input / output.
  The $0.04 per credit conversion is an assumption. Subscription inclusion,
  purchased-credit discounts and actual account debits are not observed.
- [DeepSeek prices](https://api-docs.deepseek.com/quick_start/pricing/): Flash
  off-peak rates are $0.15 uncached input, $0.003 cached input and $0.60 output
  per million. Weekends are entirely off-peak. Peak prices are twice those.
  The official current model behind `deepseek-flash` is V4.1-Flash-1017.
- [Jev prices](https://help.typesafe.ai/articles/5187202169-how-much-does-jev-cost):
  $0.042 per million input tokens; output is free.

The existing provider ledger uses peak Flash prices and treats all input as
uncached. Its settled amount is a conservative estimate, not a confirmed debit.
The final comparison keeps that common basis visible. Where every paid Flash
response's input/output usage can be reconciled to the ledger, also report an
off-peak range: all input cached to all input uncached. Do not infer cache hits
from another call or equate unreported usage with zero. Jev's recorded estimate
is added unchanged. The Codex conversion remains an assumption in either total.

The supervising implementation/audit chat and human review are excluded from
per-arm metering. Within-controller corrections, failed calls and follow-up
reads are included. No claim of a complete invoice for this whole task is made.
