"""Structural, preservation and immutable-input checks; no semantic grading."""
import hashlib
import json
from pathlib import Path
from finding_preservation import audit
from validate_report import validate


def check():
    for name, expected in json.loads(Path('immutable.json').read_text()).items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError('immutable input changed: ' + name)
    for name in ('initial', 'final'):
        validate(Path(f'analysis/{name}.json'))
    baseline = json.loads(Path('analysis/initial.json').read_text())
    final = json.loads(Path('analysis/final.json').read_text())
    supplement = json.loads(Path('analysis/supplement.json').read_text())
    result = audit(baseline, final, supplement)
    for qualification in supplement['qualifications']:
        c = qualification['citation']
        if c['file'] not in ('component.go', 'gobreaker.go'):
            raise ValueError('qualification citation must name input source')
        lines = Path(c['file']).read_text().splitlines()
        if type(c['line']) is not int or not 1 <= c['line'] <= len(lines) or not c['fragment'].strip() or c['fragment'] not in lines[c['line'] - 1]:
            raise ValueError('qualification fragment mismatch')
    old = json.loads(Path('analysis/overlay.json').read_text())['Replace']
    new = json.loads(Path('analysis/overlay-final.json').read_text())['Replace']
    if not old.items() <= new.items():
        raise ValueError('old overlay entry removed or changed')
    for target, source in new.items():
        p = Path(target)
        if p.is_absolute() or '..' in p.parts or not p.name.endswith('_test.go') or p.exists():
            raise ValueError('overlay must inject a new relative test file')
        source_path = Path(source)
        if source_path.is_absolute() or '..' in source_path.parts or not source_path.is_file():
            raise ValueError('overlay source must exist inside checkout')
    print('PRESERVATION CHECK: ' + json.dumps(result, sort_keys=True))
    return result


if __name__ == '__main__':
    check()
