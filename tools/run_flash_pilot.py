#!/usr/bin/env python3
"""Run the pinned Pool pilot with DeepSeek Flash steering and a Codex blind pass."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from local_budget import Budget, BudgetExceeded
from local_models import FLASH_URL, _post, _tokens, _usage
from run_sol_pilot import (
    MODEL as BLIND_MODEL, POOL_SHA, TOOL, brief, codex_environment, command_result,
    git, prepare, read_log, read_usage, save, verify_artifacts,
)

OUTPUT = 'domain-analysis/channelPool/part-b-blind.md'
MODEL = 'deepseek-flash'
MAX_OUTPUT = 16384
TOOL_SPEC = {'type': 'function', 'function': {
    'name': TOOL['name'], 'description': TOOL['description'], 'parameters': TOOL['inputSchema'],
}}


def cost(usage, created):
    hits = _tokens(usage.get('prompt_cache_hit_tokens'))
    misses = _tokens(usage.get('prompt_cache_miss_tokens'))
    output = _tokens(usage.get('completion_tokens'))
    if hits + misses != _tokens(usage.get('prompt_tokens')):
        raise ValueError('DeepSeek cache counters do not sum to input tokens')
    # Integer nanodollars avoid rounded intermediate token rates. Published
    # weekday peak windows apply except for Chinese public holidays.
    peak = created.weekday() < 5 and (1 <= created.hour < 4 or 6 <= created.hour < 10)
    return ((hits * 3 + misses * 150 + output * 600) * (2 if peak else 1) + 999) // 1000


def tool_arguments(function):
    if function.get('name') != 'command':
        raise ValueError('unknown tool')
    arguments = json.loads(function.get('arguments', ''))
    if not isinstance(arguments, dict) or set(arguments) != {'argv'}:
        raise ValueError('tool arguments must contain exactly one argv field')
    argv = arguments['argv']
    if not isinstance(argv, list) or not argv or not all(
        isinstance(arg, str) and '\x00' not in arg for arg in argv
    ) or not argv[0]:
        raise ValueError('expected a nonempty argv list of strings')
    return argv


def blind_dispatch(root, argv, sequence, python, codex):
    # Rebuild and compare the exact inspected package. The sandboxed
    # --package-only invocation validates the same inputs as the normal route.
    destination = root / 'pool' / OUTPUT
    package = destination.with_suffix('.package.md')
    if argv.count('--output') != 1 or argv[-2:] != ['--output', OUTPUT]:
        raise ValueError(f'put --output {OUTPUT} last for blind dispatch')
    if destination.exists():
        raise ValueError('retain the previous blind result under another name before dispatching again')
    if not package.is_file():
        raise ValueError('first run blind with --package-only and inspect its complete package')
    inspected = package.read_bytes()
    assembled = command_result(root, 'selective', [*argv, '--package-only'], sequence, python)
    if assembled['exit_code'] != 0 or package.read_bytes() != inspected:
        return {'exit_code': 2, 'stderr': 'Package failed validation or changed. Inspect the regenerated package.',
                'assembly': assembled}
    # The fresh Codex session sees only the package on stdin and has no MCP,
    # shell or working files. The steering model remains responsible for the diff.
    scratch = root / 'blind-output'
    scratch.mkdir(exist_ok=True)
    written = scratch / f'{sequence:03}.md'
    events = scratch / f'{sequence:03}.jsonl'
    argv_codex = [
        codex, '-a', 'never', 'exec', '--ignore-user-config', '--ephemeral',
        '--disable', 'shell_tool', '--disable', 'unified_exec',
        '-c', 'forced_login_method="chatgpt"', '-c', 'model_reasoning_effort="medium"',
        '-c', 'web_search="disabled"', '--model', BLIND_MODEL, '--json', '--sandbox', 'read-only',
        '-C', str(scratch), '-o', str(written), '-',
    ]
    with events.open('wb') as out, (scratch / f'{sequence:03}.stderr').open('wb') as err:
        completed = subprocess.run(argv_codex, input=inspected, stdout=out, stderr=err,
                                   env=codex_environment(), timeout=240)
    if completed.returncode or not written.is_file():
        return {'exit_code': 1, 'stderr': f'Isolated Codex blind pass failed; dispatch {sequence}'}
    destination.write_bytes(written.read_bytes())
    usage = read_usage(events)
    save(scratch / f'{sequence:03}.usage.json', usage)
    # The normal pack coverage gate is run independently as well.
    return {'exit_code': 0, 'stdout': f'Blind output is in {OUTPUT}', 'usage': usage}


def execute_call(root, function, sequence, python, codex):
    argv = tool_arguments(function)
    if argv[0] == 'read-log':
        content = read_log(root, argv)
        save(root / 'logs' / f'{sequence:03}.read.json', {'argv': argv})
        return content
    if (len(argv) > 4 and argv[0] == 'python3'
            and (root / 'pool' / argv[1]).resolve() == root / 'pack/tools/local_models.py'
            and argv[4] == 'blind' and '--package-only' not in argv):
        return blind_dispatch(root, argv, sequence, python, codex)
    return command_result(root, 'selective', argv, sequence, python)


def run(root, prompt, timeout, codex, python, key):
    ledger = Budget(root / 'routing.sqlite')
    (root / 'logs').mkdir()
    messages = [{'role': 'user', 'content': prompt}]
    start = time.monotonic()
    requests = sequence = 0
    with (root / 'provider-usage.jsonl').open('w', encoding='utf-8', buffering=1) as log:
        while time.monotonic() - start < timeout:
            payload = {'model': MODEL, 'thinking': {'type': 'disabled'},
                       'tools': [TOOL_SPEC], 'messages': messages, 'max_tokens': MAX_OUTPUT}
            estimated = len(json.dumps(payload, ensure_ascii=False).encode('utf-8'))
            ticket = ledger.reserve('deepseek-flash-steering', (estimated * 3 + 9) // 10 + 2 * MAX_OUTPUT)
            response = _post(ticket, FLASH_URL, payload, key)
            created = datetime.fromtimestamp(response['created'], timezone.utc)
            usage = _usage(response)
            charged = cost(usage, created)
            ledger.settle(ticket, charged)
            choice = response['choices'][0]
            reason = choice['finish_reason']
            requests += 1
            log.write(json.dumps({'request': requests, 'id': response['id'], 'model': response['model'],
                                  'created': created.isoformat(), 'usage': usage, 'finish_reason': reason,
                                  'cost_microdollars': charged}) + '\n')
            message = choice['message']
            if reason == 'stop':
                (root / 'final.txt').write_text(message.get('content') or '', encoding='utf-8')
                save(root / 'result.json', {'requests': requests, 'tool_calls': sequence,
                                            'elapsed_seconds': time.monotonic() - start})
                return
            if reason != 'tool_calls' or not message.get('tool_calls'):
                raise ValueError(f'DeepSeek stopped with {reason!r}; see provider-usage.jsonl')
            messages.append(message)
            for call in message['tool_calls']:
                sequence += 1
                try:
                    result = execute_call(root, call['function'], sequence, python, codex)
                except (ValueError, OSError, subprocess.SubprocessError) as error:
                    result = {'exit_code': 2, 'stderr': str(error)}
                    save(root / 'logs' / f'{sequence:03}.error.json', {'error': str(error)})
                messages.append({'role': 'tool', 'tool_call_id': call['id'],
                                 'content': json.dumps(result, ensure_ascii=False)})
    raise ValueError(f'Flash exceeded the {timeout}s pilot time limit')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pool-repo', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--pack-sha', default='HEAD')
    parser.add_argument('--timeout', type=int, default=2400)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    root = args.output.resolve()
    if sys.platform != 'darwin' or not root.is_relative_to('/private/tmp') or root == Path('/private/tmp'):
        parser.error('requires macOS and a new output directory under /tmp')
    key = os.environ.get('DEEPSEEK_API_KEY')
    codex = shutil.which(os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or 'codex')
    if not key or not os.environ.get('TYPESAFE_API_KEY') or not codex:
        parser.error('requires DeepSeek and TypeSafe credentials and the signed-in Codex CLI')
    os.umask(0o077)
    pack = Path(__file__).resolve().parents[1]
    python = Path(sys.executable).absolute()
    sha = git('rev-parse', '--verify', f'{args.pack_sha}^{{commit}}', cwd=pack).decode().strip()
    prepare(root, pack, sha, args.pool_repo.resolve(), POOL_SHA)
    save(root / 'experiment.json', {'pack_sha': sha, 'pool_sha': POOL_SHA, 'steering_model': MODEL,
                                    'thinking': 'disabled', 'blind_model': BLIND_MODEL, 'blind_effort': 'medium',
                                    'output_mode': 'selective', 'timeout_seconds': args.timeout,
                                    'smoke': args.smoke})
    prompt = ('Use the command tool to read go.mod and report its module name.'
              if args.smoke else brief(root / 'pack', routing_variant='routed') + '''
- The command tool dispatches Part B through a fresh Codex session. Use the
  normal local_models.py blind workflow, with --output last, including
  --package-only and package inspection before the real dispatch. Base Part B
  on the material prepared for it. Preserve every returned table, including
  incomplete ones. A fresh blind dispatch may repair coverage; the steering
  model never writes or edits the blind table.
- Steering work is your own. Use Jev for the indicated narrow checks.
  Write artifacts incrementally with the command tool, one file or one
  section per write. Keep large calls below the response budget and run
  format checks as each artifact becomes available.
- Finish by running all five pack gates and returning a short evidence summary.
''')
    try:
        run(root, prompt, args.timeout, codex, python, key)
        if args.smoke:
            if 'github.com/silenceper/pool' not in (root / 'final.txt').read_text():
                raise ValueError('smoke did not report the tool result')
            return 0
        return 0 if verify_artifacts(root, python) else 1
    except (OSError, ValueError, BudgetExceeded, subprocess.SubprocessError) as error:
        save(root / 'failure.json', {'error': str(error)})
        print(f'FLASH PILOT: {error}', file=sys.stderr)
        return 1
    finally:
        save(root / 'routing-cost.json', Budget(root / 'routing.sqlite').calls())


if __name__ == '__main__':
    raise SystemExit(main())
