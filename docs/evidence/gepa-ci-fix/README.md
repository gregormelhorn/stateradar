# GEPA CI dependency correction

The first push of `719a684` passed the GEPA job but failed the general job's
pack-wide mypy check: only the GEPA job installed the optional package. Local
validation had already installed it, hiding that environment difference.

The general CI job now installs the same pinned optional experiment requirements
before checking all tools. Consumer requirements and the frozen experiment code,
prompts, reports and costs are unchanged. No paid model calls were repeated.

Reproduced in a fresh environment with only `tools/requirements-dev.txt`:

```text
Found 3 errors in 3 files (checked 81 source files)
```

After installing `docs/evidence/gepa-bounded/requirements.txt` in that environment:

```text
Success: no issues found in 81 source files
```

See `typecheck-red.txt`, `typecheck-green.txt`, `full-gates.txt` and
`full-gates-status.json`. The local reproduction used Python 3.13.12 with mypy's
configured Python 3.12 target; GitHub's job uses Python 3.12 directly.
