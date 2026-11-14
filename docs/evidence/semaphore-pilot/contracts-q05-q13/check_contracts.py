"""Validate exact normative clauses, decision links and executable test coverage."""
import argparse
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
PACK=HERE.parents[3]
COMPONENT=PACK/'examples/weighted-semaphore'


def render(data):
    lines=['# Weighted semaphore evaluation contract', '',
           'This is the owner-approved evaluation contract, not an upstream Go contract.',
           'DR-001 through DR-004 retain zero-weight FIFO progress, negative-input panic,',
           'state-preserving over-release rejection and immediate oversized-request errors.',
           'The following clauses complete DR-005 through DR-013.', '']
    for dr, item in data['decisions'].items():
        lines += [f'## {dr}', '']
        for clause in item['clauses']:
            lines += [f'<!-- clause:{clause} -->',data['clauses'][clause],'']
    lines += ['## Use', '', '```go', 'if err := sem.Acquire(ctx, weight); err != nil {',
              '    return err', '}', 'defer sem.Release(weight)', '// Perform the protected work.', '```', '',
              'Race tests use bounded waits to detect stalled execution, not to establish latency promises.',
              'Invalid caller behavior is outside the valid-use contract even where detection is limited.', '']
    return '\n'.join(lines)


def check(data, document):
    expected={f'DR-{n:03}' for n in range(5,14)}
    assert set(data['decisions'])==expected, 'missing accepted decision'
    assert document.read_text()==render(data), 'normative contract text missing or drifted'
    clauses=[]; mapped=set()
    for dr,item in data['decisions'].items():
        record=(HERE.parent/'resolution-q02-q04/decisions'/f'{dr}.yaml').read_text().splitlines()
        assert f'id: {dr}' in record and 'status: accepted' in record
        assert item['tests'] and item['clauses'] and item['events'], 'decision missing tests/clauses/events'
        clauses+=item['clauses'];mapped.update(item['tests'])
    assert len(clauses)==len(set(clauses)) and set(clauses)==set(data['clauses'])
    regular=set(re.findall(r'^func (TestDR\w+)\(', (COMPONENT/'semaphore/decision_contract_test.go').read_text(),re.M))
    schedule=set(re.findall(r'^func (TestScheduleDR\w+)\(', (COMPONENT/'schedule/checkpoints_test.go.txt').read_text(),re.M))
    assert regular==set(data['regularTests']) and regular, 'ordinary test inventory drift'
    assert schedule==set(data['scheduleTests']) and schedule, 'schedule test inventory drift'
    assert mapped == regular | schedule | {'TestDR001FullSingleZero'}, 'decision/test reverse coverage incomplete'
    events={e['id'] for e in json.loads((HERE.parent/'analysis/analysis.json').read_text())['events']}
    assert all(set(item['events']) <= events for item in data['decisions'].values())
    questions=(HERE.parent/'resolution-q02-q04/open-questions.md').read_text()
    assert questions.count('Status: RESOLVED')==13 and 'Status: OPEN' not in questions
    print(f'CONTRACT CHECK: {len(expected)} decisions, {len(clauses)} normative clauses, '
          f'{len(regular)} ordinary + {len(schedule)} scheduled tests; all 13 questions decided')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path,default=HERE/'contracts.json')
    parser.add_argument('--document',type=Path,default=COMPONENT/'CONTRACT.md')
    args=parser.parse_args()
    check(json.loads(args.manifest.read_text()),args.document)
