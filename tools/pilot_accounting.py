"""Incremental, conservative usage checkpoints for one fresh Codex CLI session.

Rollout token_count is a version-dependent local format, not a billing API.
Only the exact thread ID emitted by this child process is read. Missing or
invalid records remain unknown; cumulative snapshots are never added together.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def valid_usage(usage):
    if not isinstance(usage, dict):
        raise ValueError('Codex usage is not an object')
    for key in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
        if type(usage.get(key)) is not int or usage[key] < 0:
            raise ValueError(f'missing or invalid Codex usage field: {key}')
    if usage['cached_input_tokens'] > usage['input_tokens']:
        raise ValueError('cached Codex input exceeds total input')
    return usage


class JsonlTail:
    def __init__(self):
        self.offset = 0

    def read(self, path):
        if not path.is_file():
            return
        with path.open('rb') as stream:
            stream.seek(self.offset)
            while line := stream.readline():
                if not line.endswith(b'\n'):
                    break  # A concurrent writer has not finished this record.
                self.offset = stream.tell()
                yield json.loads(line)


class UsageCheckpoint:
    def __init__(self, root):
        self.root = root
        self.sessions = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'sessions'
        self.thread_id = None
        self.rollout = None
        self.usage = None
        self.events = JsonlTail()
        self.records = JsonlTail()
        self.diagnostic = None
        self.write('running')

    def poll(self):
        try:
            for event in self.events.read(self.root / 'events.jsonl'):
                if event.get('type') == 'thread.started':
                    thread_id = event.get('thread_id', '')
                    if not re.fullmatch(r'[0-9a-fA-F-]{36}', thread_id):
                        raise ValueError('invalid child thread ID')
                    if self.thread_id and self.thread_id != thread_id:
                        raise ValueError('more than one child thread')
                    self.thread_id = thread_id
            if self.thread_id and self.rollout is None:
                matches = list(self.sessions.glob(f'*/*/*/rollout-*{self.thread_id}.jsonl'))
                if len(matches) > 1:
                    raise ValueError('ambiguous child rollout')
                if matches:
                    self.rollout = matches[0]
            if self.rollout:
                for record in self.records.read(self.rollout):
                    payload = record.get('payload', {})
                    if record.get('type') != 'event_msg' or payload.get('type') != 'token_count':
                        continue
                    info = payload.get('info')
                    if not info:
                        continue
                    usage = valid_usage(info.get('total_token_usage'))
                    if self.usage and any(usage[k] < self.usage[k] for k in
                                          ('input_tokens', 'cached_input_tokens', 'output_tokens')):
                        raise ValueError('cumulative usage decreased')
                    if usage != self.usage:
                        self.usage = usage
                        with (self.root / 'usage-history.jsonl').open('a', encoding='utf-8') as history:
                            history.write(json.dumps({'timestamp': record.get('timestamp'), 'usage': usage}) + '\n')
                        self.write('running')
        except (OSError, ValueError, TypeError) as exc:
            self.diagnostic = str(exc)
            self.write('running')

    def write(self, status):
        atomic_json(self.root / 'usage-checkpoint.json', {
            'status': status, 'usage': self.usage, 'thread_id': self.thread_id,
            'source': str(self.rollout) if self.rollout else None,
            'diagnostic': self.diagnostic,
            'complete': status == 'complete',
            'limitation': 'Only reported usage; an unfinished request may add unreported cost. Not a billing receipt.',
        })

    def finish(self, usage=None):
        self.poll()
        if usage is not None:
            self.usage = valid_usage(usage)
            self.write('complete')
        else:
            self.write('partial' if self.usage else 'unavailable')


def cost_report(checkpoint, routing, model, usd_per_credit=0.04):
    """Rate-based estimate, never an invoice; null total when any usage is missing."""
    rates = {'gpt-6.1-sol': (50, 2.5, 250), 'gpt-6.1-terra': (25, 1.25, 125)}
    usage = checkpoint.get('usage')
    credits = None
    if usage and model in rates:
        valid_usage(usage)
        normal, cached, output = rates[model]
        credits = ((usage['input_tokens'] - usage['cached_input_tokens']) * normal +
                   usage['cached_input_tokens'] * cached + usage['output_tokens'] * output) / 1_000_000
    codex_usd = credits * usd_per_credit if credits is not None else None
    provider_usd = routing['charged_microdollars'] / 1_000_000
    known = provider_usd + (codex_usd or 0)
    complete = checkpoint.get('complete', False) and credits is not None and not routing['reserved_microdollars']
    return {
        'model': model, 'reported_codex_credits': credits, 'reported_codex_usd_estimate': codex_usd,
        'settled_routing_usd': provider_usd, 'unsettled_routing_microdollars': routing['reserved_microdollars'],
        'known_subtotal_usd_estimate': round(known, 9),
        'total_usd_estimate': round(known, 9) if complete else None,
        'complete': complete, 'usd_per_credit_assumption': usd_per_credit,
        'rate_basis': '2026-11-14 standard speed, https://learn.chatgpt.com/docs/pricing#token-rates',
        'limitation': 'Rate-based estimate, not account debit. Supervising chat and human rework are not metered. '
                      'Incomplete calls may incur additional unreported cost; never price them as zero.',
    }
