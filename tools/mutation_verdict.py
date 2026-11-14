"""Parse completed cell-loop evidence; process failure alone never proves a kill."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class CellVerdict:
    checked: int
    failed: frozenset[str]


def cell_verdict(output: str, expected: int | None = None) -> CellVerdict:
    summaries = re.findall(r'^CELL SUITE: ([0-9]+) cells checked, ([0-9]+) failed\s*$',output,re.M)
    if len(summaries)!=1:
        raise ValueError('suite did not run to completion (one CELL SUITE line required)')
    checked, count = map(int,summaries[0])
    cells = re.findall(r'^CELL FAIL (.+? x .+?)\s*$',output,re.M)
    if checked<=0 or (expected is not None and checked!=expected):
        raise ValueError('empty or incomplete cell discovery')
    if count and not cells:
        raise ValueError('suite reported no cell failure')
    if count>checked or len(cells)!=count or len(set(cells))!=count:
        raise ValueError('inconsistent cell-failure accounting')
    return CellVerdict(checked,frozenset(cells))
