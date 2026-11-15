"""Replay the pinned reference controls without overwriting archived evidence."""
import argparse
from pathlib import Path
import runpy
import tempfile

ROOT=Path(__file__).resolve().parents[1]

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args()
 reference=runpy.run_path(str(ROOT/'docs/evidence/gepa-bounded/scripts/reference.py'))
 with tempfile.TemporaryDirectory(prefix='gepa-reference-output-') as td:
  reference['run'](a.output or Path(td)/'go.jsonl')
if __name__=='__main__':main()
