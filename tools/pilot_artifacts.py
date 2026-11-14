#!/usr/bin/env python3
"""Render reviewed catalogue fields, or copy exact source lines for citations.

These helpers do not infer behavior, rewrite findings or repair blind outputs.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import tomllib

CATEGORIES = tuple(item['key'] for item in tomllib.loads(
    (Path(__file__).resolve().parents[1] / 'formats/rules.toml').read_text())['uv_categories'])


def text(value, name):
    if not isinstance(value, str) or not value.strip() or '\n' in value or '\r' in value:
        raise ValueError(f'{name}: needs nonempty single-line text')
    return value.strip()


def token(value, name, pattern=r'[A-Za-z][A-Za-z0-9_-]*'):
    value = text(value, name)
    if not re.fullmatch(pattern, value):
        raise ValueError(f'{name}: invalid ID {value!r}')
    return value


def cell(value):
    return re.sub(r'(?<!\\)\|', r'\\|', value)


def render_catalogue(data):
    events = data.get('events')
    if not isinstance(events, list) or not events:
        raise ValueError('events: needs a nonempty array')
    ids = [token(event.get('id'), 'event id') for event in events]
    if len(set(ids)) != len(ids):
        raise ValueError('duplicate event ID')
    variants = set()
    for event, ident in zip(events, ids):
        if type(event.get('undesired')) is not bool or event['undesired'] != ident.startswith('UV-'):
            raise ValueError(f'{ident}: undesired must be boolean and match the UV- prefix')
        if event['undesired']:
            variants.add(ident)
    rows, annotations, coverage_rows = [], [], []
    for event, ident in zip(events, ids):
        classification = event.get('classification')
        if classification not in ('external', 'internal'):
            raise ValueError(f'{ident}: classification must be external or internal')
        source = text(event.get('source'), f'{ident} source')
        description = text(event.get('description'), f'{ident} description')
        gate = text(event.get('gate'), f'{ident} gate')
        guards = event.get('upstream_guards')
        if not isinstance(guards, list) or not guards:
            raise ValueError(f'{ident}: upstream_guards needs explicit entries, including documented absence')
        guards = [text(guard, f'{ident} upstream guard') for guard in guards]
        rows.append('| ' + ' | '.join(map(cell, (ident, classification, source, description))) + ' |')
        annotations.extend([f'### {ident}', f'- gate: {gate}', '- upstream_guards: ' + ', '.join(guards)])
        coverage = event.get('coverage', {})
        if ident not in variants or coverage:
            if not isinstance(coverage, dict) or set(coverage) != set(CATEGORIES):
                raise ValueError(f'{ident}: coverage needs all seven categories: {", ".join(CATEGORIES)}')
            annotations.append('- coverage:')
            values = []
            for category in CATEGORIES:
                value = text(coverage[category], f'{ident} {category}')
                if value.startswith('n/a:'):
                    text(value[4:], f'{ident} {category} n/a reason')
                else:
                    references = re.split(r'[,\s]+', value)
                    if not references or any(ref not in variants for ref in references):
                        raise ValueError(f'{ident} {category}: unknown variant in {value!r}; use UV- IDs or n/a: reason')
                annotations.append(f'  - {category}: {value}')
                values.append(cell(value))
            coverage_rows.append('| ' + ' | '.join([cell(ident + ': ' + source), *values]) + ' |')
        annotations.append('')
    pairs = data.get('pairs')
    if not isinstance(pairs, list):
        raise ValueError('pairs: needs an explicit array')
    pair_rows, pair_ids = [], set()
    for pair in pairs:
        ident = token(pair.get('id'), 'pair id', r'P-\d+')
        if ident in pair_ids:
            raise ValueError(f'duplicate pair: {ident}')
        pair_ids.add(ident)
        first, second = pair.get('first'), pair.get('second')
        if first not in ids or second not in ids:
            raise ValueError(f'{ident}: pair events must be declared')
        entity = text(pair.get('entity'), f'{ident} shared entity')
        for suffix, ordering in [('a', f'{first} → {second}'), ('b', f'{second} → {first}')]:
            pair_rows.append(f'| {ident}{suffix} | {ordering} | {cell(entity)} |')
    if not pairs:
        pair_rows.append(text(data.get('no_pairs_reason'), 'no_pairs_reason'))
    sections = ['# Event catalogue', '', '<!-- event-ids: ' + ' '.join(ids) + ' -->', '',
                '| id | classification | source | description, payload and evidence |', '|---|---|---|---|',
                *rows, '', '## Undesired-coverage', '',
                '| source | ' + ' | '.join(CATEGORIES) + ' |', '|---|' + '---|' * len(CATEGORIES),
                *coverage_rows, '', '## Interaction pairs', '',
                '| id | ordering | shared entity |', '|---|---|---|', *pair_rows, '',
                '## Remembrance semantics', '', text(data.get('remembrance'), 'remembrance'), '',
                '## Lock-discipline annotation', '', text(data.get('lock_discipline'), 'lock_discipline'), '']
    if data.get('notes'):
        sections.extend(['## Catalogue notes', '', text(data['notes'], 'notes'), ''])
    sections.extend(['## Event annotations', '', *annotations])
    return '\n'.join(sections) + '\n'


def citations(source, lines):
    content = source.read_text(encoding='utf-8').splitlines()
    result = []
    for line in lines:
        if line < 1 or line > len(content) or not content[line - 1].strip():
            raise ValueError(f'{source}:{line}: missing or blank source line')
        result.append({'file': str(source), 'line': line, 'fragment': content[line - 1]})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    catalogue = commands.add_parser('catalogue', help='render reviewed fields; --check verifies identical output')
    catalogue.add_argument('fields', type=Path)
    catalogue.add_argument('output', type=Path)
    catalogue.add_argument('--check', action='store_true')
    cite = commands.add_parser('citations', help='copy exact source lines as JSON; no claim judgment')
    cite.add_argument('source', type=Path)
    cite.add_argument('lines', nargs='+', type=int)
    args = parser.parse_args()
    try:
        if args.command == 'citations':
            print(json.dumps(citations(args.source, args.lines), ensure_ascii=False, indent=2))
        else:
            rendered = render_catalogue(json.loads(args.fields.read_text(encoding='utf-8')))
            if args.check:
                if args.output.read_text(encoding='utf-8') != rendered:
                    raise ValueError('catalogue differs from reviewed fields; correct fields and regenerate')
            else:
                args.output.write_text(rendered, encoding='utf-8')
            print('PILOT CATALOGUE: OK')
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(f'PILOT ARTIFACTS: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
