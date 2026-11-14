"""Check that a post-review retains its baseline findings without rewriting them."""


def audit(baseline, final, supplement):
    before = baseline['findings']
    after = final['findings']
    if not before:
        raise ValueError('nonempty baseline required')
    for rows in (before, after):
        if len({r['id'] for r in rows}) != len(rows):
            raise ValueError('distinct finding IDs required')
    indexed = {r['id']: r for r in after}
    for row in before:
        if row['id'] not in indexed:
            raise ValueError(f'missing baseline finding: {row["id"]}')
        if indexed[row['id']] != row:
            raise ValueError(f'changed baseline finding: {row["id"]}')
    qualifications = supplement['qualifications']
    bindings = supplement['test_bindings']
    if len({r['id'] for r in qualifications}) != len(qualifications):
        raise ValueError('distinct qualification IDs required')
    for row in qualifications + bindings:
        if row['id'] not in indexed:
            raise ValueError('supplement references unknown finding')
    for row in qualifications:
        if row.get('status') not in ('qualified', 'contradicted') or not row.get('rationale') or not row.get('citation'):
            raise ValueError('qualification requires status, rationale and citation')
    for row in bindings:
        if not isinstance(row.get('test'), str) or not row['test'].startswith('TestIdentity') or not row.get('scope'):
            raise ValueError('test binding requires named probe and scope')
    return {'retained': len(before), 'added': len(after) - len(before),
            'qualified': len(qualifications), 'test_bindings': len(bindings)}
