"""Format pilot command results and read evidence from their full logs."""
from __future__ import annotations

import re

SHORT_LIMIT = 2000
READ_LIMIT = 12000
GO_NUMBER = re.compile(r'^[ ]*\d+(?:\t| +)')
GO_FUNCTION = re.compile(r'^func\s+(?:\([^)]*\)\s+)?(\w+)(?:\[.*?\])?\s*\(')
TABLE_KEY = re.compile(r'^\s*\|\s*[`*]*([\w-]+)(?![\w-])(?:[`*\s]|\|)')


def go_functions(lines):
    """Find named declarations in plain or nl-numbered Go source."""
    if not any(GO_NUMBER.sub('', line).startswith('package ') for line in lines[:10]):
        return []
    return [(i, match[1]) for i, line in enumerate(lines)
            if (match := GO_FUNCTION.match(GO_NUMBER.sub('', line)))]


def table_rows(lines):
    return [(i, match[1]) for i, line in enumerate(lines) if (match := TABLE_KEY.match(line))
            and re.search(r'\w', match[1])]


def failure_excerpt(output):
    """Keep blocked test stacks and conflicting access frames in Go reports."""
    lines = output.splitlines()
    timeout = next((i for i, line in enumerate(lines) if line.startswith('panic: test timed out')), None)
    if timeout is not None:
        stack_start = next((i for i in range(timeout + 1, len(lines))
                            if lines[i].startswith('goroutine ')), len(lines))
        header = lines[timeout:stack_start][:20]
        tests = re.findall(r'^\s*(Test\w+)(?:/\S+)?\s+\(', '\n'.join(header), re.M)
        starts = [i for i in range(stack_start, len(lines)) if lines[i].startswith('goroutine ')]
        relevant = []
        for start, end in zip(starts, starts[1:] + [len(lines)]):
            block = '\n'.join(lines[start:end]).rstrip()
            if any(re.search(r'\.' + re.escape(test) + r'(?:\.func\d+)?\(', block) for test in tests):
                relevant.append(f'Full log, stack starts at line {start + 1}:\n{block}')
                if len(relevant) == 4:
                    break
        if relevant:
            return (f'Full log, timeout starts at line {timeout + 1}:\n'
                    + '\n'.join(header) + '\n' + '\n\n'.join(relevant)[:5000])
    if 'WARNING: DATA RACE' in lines:
        # Keep conflicting access stacks and discard goroutine creation stacks.
        excerpts = []
        for i, line in enumerate(lines):
            if line == 'WARNING: DATA RACE':
                end = next((j for j in range(i + 1, len(lines))
                            if lines[j].startswith(('Goroutine ', '=================='))), len(lines))
                excerpts.append(f'Full log, race starts at line {i + 1}:\n' + '\n'.join(lines[i:end]))
                if len(excerpts) == 3:
                    break
        return '\n\n'.join(excerpts)[:6000]
    return None


def document_page(output: str, start: int = 1, column: int = 1) -> tuple[str, tuple[int, int] | None]:
    """Return a contiguous page and the exact position of the next one."""
    lines = output.splitlines(keepends=True)
    if not 1 <= start <= len(lines) or not 1 <= column <= len(lines[start - 1]):
        raise ValueError('page must start at a valid line and column')
    budget = READ_LIMIT
    chunks: list[str] = []
    for index in range(start - 1, len(lines)):
        offset = column - 1 if index == start - 1 else 0
        line = lines[index][offset:]
        if len(line) > budget:
            if chunks:
                return ''.join(chunks), (index + 1, offset + 1)
            # A single oversized line still has a lossless continuation.
            return line[:budget], (index + 1, offset + budget + 1)
        chunks.append(line)
        budget -= len(line)
    return ''.join(chunks), None


def selective_output(output: str, exit_code: int):
    if len(output) > SHORT_LIMIT and exit_code and (stack := failure_excerpt(output)) is not None:
        excerpt = stack.rstrip() + '\n… other log lines omitted …\n'
        if len(excerpt) < len(output):
            return excerpt, None
    if len(output) <= READ_LIMIT:
        return output, None
    return document_page(output)


def compact_output(output, exit_code, fallback):
    if len(output) <= SHORT_LIMIT:
        return output
    if exit_code:
        stack = failure_excerpt(output)
        if stack is not None:
            return stack.rstrip() + '\n… other log lines omitted …\n'
        # Keep actionable checker diagnostics together when the report is moderate.
        if output.startswith(('DSC CHECK: FAIL', 'CHECK MATRIX: FAIL',
                              'REACHABILITY CHECK: FAIL', 'PART-B COVERAGE: FAIL')) and len(output) <= READ_LIMIT:
            return output
    if output.startswith('group G-') and len(output) <= 4000:
        return output
    lines = output.splitlines()
    functions = go_functions(lines)
    if functions:
        names = ', '.join(dict.fromkeys(name for _, name in functions))
        return f'Go source ({len(lines)} lines). Functions: {names[:1000]}\n'
    rows = table_rows(lines)
    first_table = next((i for i, line in enumerate(lines) if line.lstrip().startswith('|')), None)
    if len(rows) >= 5 and first_table is not None and first_table < 5:
        # A standalone table is best navigated by key. Mixed drafts also have
        # review prose after their tables; keep their end excerpt.
        last_row = max(i for i, _ in rows)
        if all(not line.strip() or line.lstrip().startswith(('|', '- ['))
               or re.fullmatch(r'(?:#+\s*)?coverage checklist:?', line.strip(), re.I)
               for line in lines[last_row + 1:]):
            names = ', '.join(dict.fromkeys(key for i, key in rows if i != first_table))
            return f'{lines[first_table]}\n{len(rows) - 1} rows. Keys: {names[:1000]}\n'
    return fallback(output, exit_code)


def select_lines(output, mode, args):
    """Return bounded evidence with original line numbers."""
    lines = output.splitlines()
    if mode == 'lines' and len(args) == 2:
        start, end = map(int, args)
        if not 1 <= start <= end <= len(lines) or end - start >= 100:
            raise ValueError('line range must contain up to 100 valid lines')
        indices = list(range(start - 1, end))
    elif mode == 'find' and len(args) == 1 and args[0]:
        indices = [i for i, line in enumerate(lines) if args[0].casefold() in line.casefold()]
    elif mode == 'rows' and args:
        keys = set(args)
        indices = [i for i, key in table_rows(lines) if key in keys]
    elif mode == 'function' and len(args) == 1:
        indices = []
        for start, name in go_functions(lines):
            if name == args[0]:
                end = next((i for i in range(start + 1, len(lines))
                            if GO_NUMBER.sub('', lines[i]) == '}'), start)
                indices.extend(range(start, end + 1))
    else:
        raise ValueError('use lines START END, find LITERAL, rows KEY [KEY ...], or function NAME')

    selected = []
    budget = READ_LIMIT
    for index in indices[:100 if mode in ('lines', 'function') else 20]:
        line = lines[index]
        if len(line) > budget:
            if not selected:
                selected.append((index + 1, line[:budget] + ' … line truncated …'))
            break
        selected.append((index + 1, line))
        budget -= len(line) + 1
    return {'matches': len(indices), 'lines': selected, 'total_lines': len(lines),
            'truncated': len(selected) < len(indices) or any(
                text != lines[index - 1] for index, text in selected)}
