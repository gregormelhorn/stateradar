#!/bin/bash
# usage: run.sh <label> <stdout-file> <stderr-file> cmd...
# logs UTC start/end + exit code to timing.md
label="$1"; out="$2"; err="$3"; shift 3
echo "$(date -u +%FT%TZ) START $label" >> /tmp/flash-writes-MBhG/timing.md
"$@" >"$out" 2>"$err"; rc=$?
echo "$(date -u +%FT%TZ) END   $label (exit $rc)" >> /tmp/flash-writes-MBhG/timing.md
exit $rc
