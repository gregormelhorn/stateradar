#!/bin/bash
# usage: tl.sh "label"  -> appends UTC timestamp line to timing.md
echo "$(date -u +%FT%TZ) $*" >> /tmp/flash-writes-MBhG/timing.md
