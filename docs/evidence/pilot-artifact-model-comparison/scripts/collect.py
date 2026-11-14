"""Read the matched runner's completed events, ledgers and gate evidence."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(sys.argv[1])
COMPONENTS = {'pool': 'channelPool', 'gobreaker': 'circuitBreaker'}
VARIANTS = ('sol', 'terra')

def read_json(path):
    return json.loads(path.read_text()) if path.is_file() else None

def load_events(path):
    if not path.is_file():
        return []
    result = []
    for line in path.read_text().splitlines():
        try:
            result.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return result

def usage_fields(events, recorded):
    completed = [event['usage'] for event in events if event.get('type') == 'turn.completed']
    if len(completed) != 1:
        return {'completed_turns': len(completed), 'counters': None}
    counts = completed[0]
    if recorded is not None and recorded != counts:
        raise ValueError('usage.json and completed event disagree')
    for key in ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens',
                'output_tokens', 'reasoning_output_tokens'):
        if key in counts and (not isinstance(counts[key], int) or counts[key] < 0):
            raise ValueError(f'invalid token count: {key}')
    return {'completed_turns': 1, 'counters': counts,
            'input_excluding_cache_hits': counts['input_tokens'] - counts['cached_input_tokens'],
            'input_plus_output': counts['input_tokens'] + counts['output_tokens']}

def collect(component, name, variant, run_name=None):
    run = ROOT / (run_name or f'{component}-{variant}')
    if not run.is_dir():
        return None
    arm = run / 'selective'
    analysis = arm / 'pool' / 'domain-analysis' / name
    events = load_events(arm / 'events.jsonl')
    mcp = [event['item'] for event in events
           if event.get('type') == 'item.completed'
           and event.get('item', {}).get('type') == 'mcp_tool_call']
    exit_path = run.with_suffix('.exit')
    result = {'settings': read_json(run / 'experiment.json'),
              'exit': int(exit_path.read_text()) if exit_path.is_file() else None,
              'codex': usage_fields(events, read_json(arm / 'usage.json')),
              'result': read_json(arm / 'result.json'),
              'failure': read_json(arm / 'failure.json'),
              'mcp_completed': len(mcp),
              'retained_log_reads': sum(isinstance(item.get('arguments'), dict)
                  and item['arguments'].get('argv', [])[:1] == ['read-log'] for item in mcp),
              'acceptance_exit_codes': read_json(arm / 'acceptance.json')}
    result['model_calls_by_command_status'] = dict(sorted(Counter(
        f"{entry['argv'][4]}/exit-{entry['exit_code']}"
        for log in (arm / 'logs').glob('[0-9]*.json')
        if (entry := read_json(log)) and 'exit_code' in entry and len(entry.get('argv', [])) > 4
        and Path(entry['argv'][1]).name == 'local_models.py'
    ).items()))
    ledger = read_json(arm / 'routing-cost.json')
    if ledger:
        amounts = Counter()
        for call in ledger['calls']:
            amounts[f"{call['provider']}/{call['status']}"] += call['amount_microdollars']
        result['provider_ledger_microdollars'] = {
            'by_provider_status': dict(sorted(amounts.items())),
            'settled': ledger['charged_microdollars'],
            'reserved': ledger['reserved_microdollars'],
        }
    sidecar = read_json(analysis / 'analysis.json')
    if sidecar:
        result['sidecar_counts'] = {key: len(sidecar.get(key, [])) for key in
                                    ('states', 'events', 'cells', 'pairs', 'questions', 'guardGroups')}
        result['pair_reachability_edges'] = [row for row in sidecar.get('pairs', [])
                                             if 'reachability' in row]
    result['gates'] = {}
    for path in sorted((arm / 'logs').glob('acceptance-*.stdout')):
        result['gates'][path.stem.removeprefix('acceptance-')] = path.read_text().splitlines()[:2]
    result['artifact_sha256'] = {
        stem: hashlib.sha256(path.read_bytes()).hexdigest()
        for stem in ('catalogue-fields.json', 'matrix-fields.json', 'disposition-matrix.md', 'analysis.json', 'part-b-blind.md')
        if (path := analysis / stem).is_file()
    }
    result['schedule_outputs'] = []
    for path in sorted(analysis.rglob('*.json')):
        if path.name.endswith('.raw.json') or 'window' not in path.name:
            continue
        payload = read_json(path)
        if isinstance(payload, dict) and 'source_sha256' in payload and isinstance(payload.get('candidates'), list):
            result['schedule_outputs'].append({
                'file': str(path.relative_to(analysis)),
                'draft': payload['draft'], 'candidates': len(payload['candidates']),
                'with_shape_or_citation_problems': sum(bool(row['problems']) for row in payload['candidates']),
            })
    return result

if __name__ == '__main__':
    result = {component: {variant: collect(component, name, variant)
                          for variant in VARIANTS} for component, name in COMPONENTS.items()}
    for component, arms in result.items():
        if all(arm and arm['settings'] for arm in arms.values()):
            assert len({json.dumps({key: value for key, value in arm['settings'].items()
                                    if key != 'model'}, sort_keys=True)
                        for arm in arms.values()}) == 1, component
    print(json.dumps(result, indent=2))
