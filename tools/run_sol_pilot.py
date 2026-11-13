#!/usr/bin/env python3
"""Run a StateRadar pilot or compare tool output modes via the signed-in Codex CLI."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import signal
import shutil
import subprocess
import sys
import time

from local_budget import Budget
from pilot_output import compact_output, document_page, selective_output, select_lines

MODEL = 'gpt-6.1-sol'
POOL_SHA = '6084537e520652192f41aebfd88d822c00b9447a'
GOBREAKER_SHA = '27b8e2cfc65aacd09abb3968455e4b01df4a83fa'
COMPONENTS = {
    'pool': (POOL_SHA, 'github.com/silenceper/pool', 'channelPool',
             'channelPool, public Pool interface, channel.go and pool.go', 'channel_rpc_test.go'),
    'gobreaker': (GOBREAKER_SHA, 'github.com/sony/gobreaker', 'circuitBreaker',
                  'one CircuitBreaker instance, including the TwoStepCircuitBreaker public wrapper, gobreaker.go',
                  'gobreaker_test.go'),
}
TOOL = {
    'name': 'command',
    'description': 'Run an argv list in the isolated component checkout. Use read-log to retrieve evidence from retained command results.',
    'inputSchema': {'type': 'object', 'properties': {'argv': {'type': 'array', 'items': {'type': 'string'}}},
                    'required': ['argv'], 'additionalProperties': False},
}


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def brief(pack, component='pool'):
    _, _, output_name, scope, tests = COMPONENTS[component]
    return (pack / 'prompts/02-pilot.md').read_text(encoding='utf-8') + f'''

Run brief for the benchmark:
- Component: {scope}.
- Requirements: README.md. Existing tests: {tests}.
- Output directory: domain-analysis/{output_name}. Use the complete pilot above.
- routing variant: flash-writes
- Use ../pack for the pack, python3 for its tools, and ../routing.sqlite for
  the one model ledger. Pin jev-1.14.0. Execute all gates and preserve failures.
- Model routing is configured through the pilot command tool. Credentials are
  provided only when it runs python3 ../pack/tools/local_models.py with the
  pilot ledger. Generic environment inspection cannot check routing access.
  Attempt the prescribed routing calls and report actual provider failures.
- Use the pilot command tool for every operation. Write analysis artifacts with python3 via argv (or mkdir/cp); keep test-only
  probes separate from existing tests and report every test failure.
- Use domain-analysis/{output_name}/part-b-blind.md as the blind output path.
- Run without --companion-claims in this comparison.
- Run Go tests with a finite timeout. When a document must be read in full,
  follow read_more.next_stdout or read_more.next_stderr and each returned next
  until it is null. For a specific piece of evidence, use the read_more argv
  prefix with function NAME, rows KEY [KEY ...], find LITERAL, or lines START END
  (up to 100 lines). Append .stderr to the log ID to read stderr.
- Stop with a summary of findings and executed checks. Domain questions stay open.
'''


def excerpt(output, exit_code):
    if len(output) <= 2000:
        return output
    lines = output.splitlines()
    signals = [line for line in lines if re.match(r'^(--- FAIL:|FAIL\b|panic:|\s*running tests:)', line)]
    tests = [line for line in lines if line.startswith('=== RUN')]
    relevant = '\n'.join((tests[-1:] if exit_code else []) + signals)[:500]
    return output[:500] + '\n… full log on disk …\n' + relevant + '\n' + output[-700:]


def command_result(root, arm, argv, sequence, python):
    code, stdout, stderr = execute(root, argv, sequence, python)
    logs = root / 'logs'
    logs.mkdir(exist_ok=True)
    name = f'{sequence:03}'
    for stream, content in (('stdout', stdout), ('stderr', stderr)):
        (logs / f'{name}.{stream}').write_text(content, encoding='utf-8')
    save(logs / f'{name}.json', {'argv': argv, 'exit_code': code})
    return format_result(name, f'../logs/{name}.{{stdout,stderr}}', stdout, stderr, code, arm)


def format_result(name, log, stdout, stderr, code, arm):
    result = {'exit_code': code, 'stdout': stdout, 'stderr': stderr, 'log': log}
    continuations = {}
    for stream, output in (('stdout', stdout), ('stderr', stderr)):
        if arm == 'compact':
            result[stream] = compact_output(output, code, excerpt)
        elif arm == 'selective':
            result[stream], position = selective_output(output, code)
            if position is not None:
                line, column = position
                continuations[f'next_{stream}'] = ['read-log', f'{name}.{stream}', 'page', str(line), str(column)]
    if result['stdout'] != stdout or result['stderr'] != stderr:
        result['read_more'] = {
            'argv_prefix': ['read-log', name],
            'modes': ['function NAME', 'rows KEY [KEY ...]', 'find LITERAL', 'lines START END'],
            **continuations,
        }
    return result


def read_log(root, argv):
    if len(argv) < 3 or not (match := re.fullmatch(r'(\d{3,})(?:\.(stdout|stderr))?', argv[1])):
        raise ValueError('read-log needs a recorded ID, optionally followed by .stdout or .stderr')
    number, stream = match[1], match[2] or 'stdout'
    path = root / 'logs' / f'{number}.{stream}'
    with path.open(encoding='utf-8', newline='') as retained:
        return read_output(retained.read(), argv)


def read_output(output, argv):
    if argv[2] == 'page' and len(argv) == 5:
        start, column = map(int, argv[3:])
        page, position = document_page(output, start, column)
        return {
            'text': page,
            'start_line': start,
            'start_column': column,
            'next': ['read-log', argv[1], 'page', *map(str, position)] if position else None,
        }
    return select_lines(output, argv[2], argv[3:])


def serve_tools(root, arm):
    """Serve only the experiment command through MCP stdio."""
    sequence = 0
    python = Path(sys.executable).absolute()
    for line in sys.stdin:
        request = json.loads(line)
        if 'id' not in request:
            continue
        method = request.get('method')
        message = {'jsonrpc': '2.0', 'id': request['id']}
        try:
            if method == 'initialize':
                result = {'protocolVersion': request['params']['protocolVersion'],
                          'capabilities': {'tools': {}},
                          'serverInfo': {'name': 'stateradar-pilot', 'version': '1.0'}}
            elif method == 'tools/list':
                result = {'tools': [TOOL]}
            elif method == 'ping':
                result = {}
            elif method == 'tools/call':
                params = request['params']
                argv = params['arguments']['argv']
                if (params['name'] != 'command' or not isinstance(argv, list) or not argv
                        or not all(isinstance(arg, str) and '\x00' not in arg for arg in argv)):
                    raise ValueError('expected command with a nonempty argv list')
                sequence += 1
                if argv[0] == 'read-log':
                    data = read_log(root, argv)
                    save(root / 'logs' / f'{sequence:03}.read.json', {'argv': argv})
                else:
                    data = command_result(root, arm, argv, sequence, python)
                result = {'content': [{'type': 'text', 'text': json.dumps(data, ensure_ascii=False)}]}
            else:
                message['error'] = {'code': -32601, 'message': 'Method not found'}
                print(json.dumps(message), flush=True)
                continue
            message['result'] = result
        except (KeyError, OSError, ValueError) as error:
            message['error'] = {'code': -32602, 'message': str(error)}
        print(json.dumps(message, ensure_ascii=False), flush=True)


def codex_environment():
    env = os.environ.copy()
    for name in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'CODEX_ACCESS_TOKEN', 'OPENAI_BASE_URL',
                 'CODEX_THREAD_ID', 'CODEX_SESSION_ID', 'CODEX_TOOL_CALL_ID'):
        env.pop(name, None)
    return env


def read_usage(events):
    completed = []
    for line in events.read_text(encoding='utf-8').splitlines():
        event = json.loads(line)
        if event.get('type') == 'turn.completed':
            completed.append(event['usage'])
    if len(completed) != 1:
        raise ValueError('expected exactly one completed Codex turn')
    usage = completed[0]
    for key in ('input_tokens', 'cached_input_tokens', 'output_tokens'):
        if type(usage.get(key)) is not int or usage[key] < 0:
            raise ValueError(f'missing or invalid Codex usage field: {key}')
    return usage


def run_arm(root, arm, prompt, codex, python, timeout, *, replay_server=None):
    logs = root / 'logs'
    logs.mkdir(exist_ok=True)
    events = root / 'events.jsonl'
    server = replay_server or Path(__file__).resolve()
    args = [
        codex, '-a', 'never', 'exec', '--ignore-user-config', '--ephemeral',
        '--disable', 'shell_tool', '--disable', 'unified_exec',
        '-c', 'forced_login_method="chatgpt"', '-c', 'model_reasoning_effort="medium"',
        '-c', 'web_search="disabled"',
        '-c', f'mcp_servers.pilot.command={json.dumps(str(python))}',
        '-c', f'mcp_servers.pilot.args={json.dumps([str(server), "--serve-tools", str(root), arm])}',
        '-c', 'mcp_servers.pilot.required=true', '-c', 'mcp_servers.pilot.tool_timeout_sec=160',
        '-c', 'mcp_servers.pilot.tools.command.approval_mode="approve"',
        '-c', 'mcp_servers.pilot.tools.command.output_token_limit=60000',
        *([] if replay_server else ['-c', 'mcp_servers.pilot.env_vars=["DEEPSEEK_API_KEY","TYPESAFE_API_KEY"]']),
        '--model', MODEL, '--json', '--sandbox', 'read-only',
        '-C', str(root / 'pool'), '-o', str(root / 'final.txt'), '-',
    ]
    start = time.monotonic()
    try:
        with events.open('w', encoding='utf-8') as stdout, (root / 'codex.stderr').open('w', encoding='utf-8') as stderr:
            proc = subprocess.run(args, input=prompt, text=True, env=codex_environment(),
                                  stdout=stdout, stderr=stderr, timeout=timeout)
        if proc.returncode:
            raise ValueError(f'Codex exited {proc.returncode}; see {events}')
        usage = read_usage(events)
        save(root / 'usage.json', usage)
        save(root / 'result.json', {'elapsed_seconds': round(time.monotonic() - start, 3),
                                    'tool_calls': len(list(logs.glob('[0-9]*.json')))})
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        save(root / 'failure.json', {'error': str(exc), 'elapsed_seconds': round(time.monotonic() - start, 3)})
        raise


def git(*args, cwd):
    return subprocess.run(['git', *args], cwd=cwd, check=True, capture_output=True).stdout


def prepare(root, pack, pack_sha, repo, source_sha=POOL_SHA):
    root.mkdir()
    for name in ('pool', 'pack', 'scratch', 'go-mod', 'go-build'):
        (root / name).mkdir()
    checkout = root / 'pool'
    git('init', '--quiet', cwd=checkout)
    git('fetch', '--quiet', '--depth=1', '--no-tags', str(repo), source_sha, cwd=checkout)
    git('checkout', '--quiet', '--detach', 'FETCH_HEAD', cwd=checkout)
    packed = git('archive', pack_sha, 'AGENTS.md', 'prompts', 'formats', 'tools',
                 'docs/local-model-routing.md', cwd=pack)
    subprocess.run(['tar', '-xf', '-'], cwd=root / 'pack', input=packed, check=True)
    env = execution_env(root)
    subprocess.run(['go', 'mod', 'download'], cwd=checkout, env=env, check=True, timeout=120)


def execution_env(root):
    return {'PATH': '/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin', 'HOME': str(root / 'scratch'),
            'PWD': str(root / 'pool'), 'TMPDIR': str(root / 'scratch'), 'GOMODCACHE': str(root / 'go-mod'),
            'GOCACHE': str(root / 'go-build'), 'GOTOOLCHAIN': 'local',
            'PYTHONDONTWRITEBYTECODE': '1', 'STATERADAR_PACK': str(root / 'pack')}


def execute(root, argv, _sequence, python):
    # The pack's own routing tool is the only subprocess with credentials or network access.
    routing = (len(argv) > 2 and argv[0] == 'python3' and
               (root / 'pool' / argv[1]).resolve() == root / 'pack/tools/local_models.py')
    env = execution_env(root)
    if routing and '--companion-claims' in argv:
        return 2, '', 'Companion Noul is evaluated separately.'
    if argv[0] == 'python3':
        argv = [str(python), *argv[1:]]
    if routing:
        required = ('DEEPSEEK_API_KEY', 'TYPESAFE_API_KEY')
        if not all(os.environ.get(name) for name in required):
            return 2, '', 'The pilot tool did not receive its provider credentials.'
        env.update({name: os.environ[name] for name in required})
        # Require the canonical ledger and command before any optional arguments.
        allowed = {'status', 'flash', 'jev', 'jev-batch', 'draft-verify', 'draft-cells', 'blind'}
        if len(argv) < 5 or argv[2:4] != ['--ledger', '../routing.sqlite'] or argv[4] not in allowed:
            return 2, '', 'Use --ledger ../routing.sqlite and a model or status command.'
    else:
        env['GOPROXY'] = 'off'
    home = Path.home().resolve()
    # Resolve only the containing directory: the venv executable is a symlink.
    venv = python.parent.parent if (python.parent.parent / 'pyvenv.cfg').is_file() else None
    readable = f'(subpath {json.dumps(str(root))})'
    readable += ' ' + ' '.join(f'(literal {json.dumps(str(parent))})' for parent in root.parents)
    if venv is not None:
        readable += f' (subpath {json.dumps(str(venv))})'
    writable = ' '.join(f'(subpath {json.dumps(str(root / part))})'
                        for part in ('pool', 'scratch', 'go-build', 'go-mod'))
    ledger = ' '.join(f'(literal {json.dumps(str(root / ("routing.sqlite" + suffix)))})'
                      for suffix in ('', '-journal', '-shm', '-wal'))
    profile = f'''(version 1)
(allow default)
(deny file-read-data (subpath {json.dumps(str(home))}) (subpath "/private/tmp")
                    (subpath "/private/var/folders") (subpath "/Volumes"))
(allow file-read-data {readable})
(deny file-read-data (subpath {json.dumps(str(root / 'responses'))}))
(deny file-write*)
(allow file-write* {writable} {ledger} (literal "/dev/null"))
'''
    if not routing:
        profile += '''(deny network*)
(allow network-bind (local ip "localhost:7777"))
(allow network-inbound (local ip "localhost:7777"))
(allow network-outbound (remote ip "localhost:7777"))
'''
    # Isolated Python ignores PYTHONPATH and the checkout's module shadowing.
    if routing:
        routing_script = str(root / 'pack/tools/local_models.py')
        entry = '''import runpy
import sys
script = sys.argv.pop(1)
sys.path.insert(0, script.rsplit('/', 1)[0])
runpy.run_path(script, run_name='__main__')
'''
        argv = [str(python), '-I', '-c', entry, routing_script, *argv[2:]]
    with subprocess.Popen(['/usr/bin/sandbox-exec', '-p', profile, *argv], cwd=root / 'pool',
                          env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          start_new_session=True) as proc:
        try:
            stdout, stderr = proc.communicate(timeout=150)
            return proc.returncode, stdout.decode('utf-8', 'replace'), stderr.decode('utf-8', 'replace')
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            stdout, stderr = proc.communicate()
            return 124, stdout.decode('utf-8', 'replace'), (
                stderr.decode('utf-8', 'replace') + '\nCommand timed out after 150 seconds.')



def verify_artifacts(root, python, output_name='channelPool'):
    base = f'domain-analysis/{output_name}'
    commands = {
        'matrix': [f'{base}/check_matrix.py'],
        'guards': [f'{base}/check_guards.py'],
        'sidecar': ['../pack/tools/dsc_check.py', base, '--repo', '.', '--model', 'as-is.machine.mmd'],
        'reachability': ['../pack/tools/check_reachability.py', base],
        'blind-coverage': ['../pack/tools/part_b_pack.py', base, '--repo', '.',
                           '--check', f'{base}/part-b-blind.md'],
    }
    outcomes = {}
    for name, arguments in commands.items():
        code, stdout, stderr = execute(root, ['python3', *arguments], 0, python)
        (root / 'logs' / f'acceptance-{name}.stdout').write_text(stdout, encoding='utf-8')
        (root / 'logs' / f'acceptance-{name}.stderr').write_text(stderr, encoding='utf-8')
        outcomes[name] = code
    save(root / 'acceptance.json', outcomes)
    return all(code == 0 for code in outcomes.values())


def main():
    if len(sys.argv) == 4 and sys.argv[1] == '--serve-tools':
        serve_tools(Path(sys.argv[2]).resolve(), sys.argv[3])
        return 0
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--component', choices=COMPONENTS, default='pool')
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument('--component-repo', type=Path, help='local clone containing the pinned component SHA')
    source.add_argument('--pool-repo', type=Path, help='local Pool clone (alias for --component-repo)')
    parser.add_argument('--output', required=True, type=Path, help='new experiment directory under /tmp')
    parser.add_argument('--pack-sha', default='HEAD')
    parser.add_argument('--prepare-only', action='store_true', help='verify clean inputs and sandbox without model calls')
    parser.add_argument('--codex-bin', default=os.environ.get('CODEX_APP_RUNTIME_CLI_PATH') or 'codex')
    parser.add_argument('--timeout', type=int, default=2400, help='wall-clock seconds per arm')
    parser.add_argument('--output-mode', choices=('selective', 'standard', 'compact', 'compare'),
                        help='selective (default), full standard, compact, or compare standard and compact')
    parser.add_argument('--compact-first', action='store_true', help='compare with compact before standard')
    parser.add_argument('--smoke', action='store_true', help='verify selected output modes with a small live command')
    args = parser.parse_args()
    if args.pool_repo and args.component != 'pool':
        parser.error('--pool-repo is only valid for the Pool component')
    repo = (args.component_repo or args.pool_repo).resolve()
    source_sha, module, output_name, _, _ = COMPONENTS[args.component]
    output_mode = args.output_mode or ('compare' if args.compact_first else 'selective')
    if args.compact_first and output_mode != 'compare':
        parser.error('--compact-first requires --output-mode compare')
    if output_mode == 'compare':
        arm_order = ('compact', 'standard') if args.compact_first else ('standard', 'compact')
    else:
        arm_order = (output_mode,)
    root = args.output.resolve()
    pack = Path(__file__).resolve().parents[1]
    if not root.is_relative_to(Path('/private/tmp')) or root == Path('/private/tmp'):
        parser.error('--output must name a new directory under /tmp')
    if args.timeout < 1:
        parser.error('--timeout must be positive')
    codex = shutil.which(args.codex_bin)
    if not codex and not args.prepare_only:
        parser.error('Codex CLI not found')
    if sys.platform != 'darwin' or not Path('/usr/bin/sandbox-exec').is_file():
        parser.error('this runner needs the macOS sandbox to isolate the pilots')
    required = ('DEEPSEEK_API_KEY', 'TYPESAFE_API_KEY')
    missing = [name for name in required if not os.environ.get(name)]
    if missing and not args.prepare_only:
        parser.error('missing ' + ', '.join(missing))
    os.umask(0o077)
    python = Path(sys.executable).absolute()
    try:
        subprocess.run([str(python), '-c', 'import jsonschema, z3'], check=True)
        sha = git('rev-parse', '--verify', f'{args.pack_sha}^{{commit}}', cwd=pack).decode().strip()
        root.mkdir()
        if not args.prepare_only:
            login = subprocess.run([codex, 'login', 'status'], capture_output=True, text=True,
                                   env=codex_environment(), check=True)
            if 'Logged in using ChatGPT' not in login.stdout + login.stderr:
                raise ValueError('Codex CLI must be signed in using ChatGPT')
        source_identity = ({'pool_sha': source_sha} if args.component == 'pool'
                           else {'component': args.component, 'component_sha': source_sha})
        save(root / 'experiment.json', {'pack_sha': sha, **source_identity,
                                         'model': MODEL, 'effort': 'medium', 'auth': 'chatgpt',
                                         'timeout_seconds': args.timeout, 'smoke': args.smoke,
                                         'arm_order': arm_order,
                                         'output_mode': output_mode})
        for arm in arm_order:
            folder = root / arm
            prepare(folder, pack, sha, repo, source_sha)
            status, _, stderr = execute(folder, ['python3', '-c', 'import jsonschema, z3'], 0, python)
            if status:
                raise ValueError(f'{arm} sandbox dependency check failed: {stderr.strip()}')
            status, out, stderr = execute(folder, ['git', 'rev-parse', 'HEAD'], 0, python)
            if status or out.strip() != source_sha:
                raise ValueError(f'{arm} sandbox checkout check failed: {stderr.strip()}')
            status, out, stderr = execute(folder, ['cat', 'go.mod'], 0, python)
            if status or f'module {module}' not in out.splitlines():
                raise ValueError(f'{arm} sandbox source read failed: {stderr.strip()}')
            status, _, _ = execute(folder, ['cat', str(root / 'experiment.json')], 0, python)
            if status == 0:
                raise ValueError(f'{arm} sandbox can read the parent experiment file')
        if args.prepare_only:
            print(f'{len(arm_order)} isolated checkout(s) verified at {root}.')
            return 0
        gates_passed = []
        for arm in arm_order:
            folder = root / arm
            Budget(folder / 'routing.sqlite')
            print(f'Starting {arm} at {folder}', flush=True)
            prompt = ('''Use the pilot command tool to run ["cat", "go.mod"] and then
["python3","../pack/tools/local_models.py","--ledger","../routing.sqlite","jev",
"go.mod","Does the source name a Go module?","--model","jev-1.14.0"].
Report the module name and whether the Jev call succeeded.'''
                      if args.smoke else brief(folder / 'pack', args.component))
            try:
                run_arm(folder, arm, prompt, codex, python, args.timeout)
            finally:
                calls = Budget(folder / 'routing.sqlite').calls()
                save(folder / 'routing-cost.json', {'calls': calls, 'charged_microdollars': sum(
                    call['amount_microdollars'] for call in calls if call['status'] == 'settled'),
                    'reserved_microdollars': sum(call['amount_microdollars'] for call in calls
                                                  if call['status'] == 'reserved')})
            if args.smoke:
                text = (folder / 'final.txt').read_text(encoding='utf-8')
                if module not in text or not any(
                    call['provider'] == 'jev' and call['status'] == 'settled' for call in calls
                ):
                    raise ValueError(f'{arm} smoke did not demonstrate the pilot tool and live Jev')
            else:
                gates_passed.append(verify_artifacts(folder, python, output_name))
        print(f'{len(arm_order)} Codex session(s) ended. Review usage and artifacts in {root}.')
        return 0 if all(gates_passed) else 1
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        print(f'SOL PILOT: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
