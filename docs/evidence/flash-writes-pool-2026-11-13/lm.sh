#!/bin/bash
# local_models.py with the run's ledger (never prints keys)
exec python3 /tmp/flash-writes-MBhG/stateradar/tools/local_models.py --ledger /tmp/flash-writes-MBhG/ledger.db "$@"
