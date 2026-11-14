# Rejected diagnostic setup

The first copied-overlay attempt used macOS /var aliases while Go resolved the
working directory under /private/var. Go returned exit 0 with `no tests to run`.
The diagnostic found zero started tests and raised:

`ValueError: incomplete test discovery or compile/runtime failure; not a behavioral verdict`

No mutant was scored. The driver now resolves the copy path before constructing
overlay keys. The successful baseline and actual mutation result are in the
sibling `routed/` directory. These setup outputs remain unchanged.
