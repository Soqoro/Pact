#!/usr/bin/env bash
set -euo pipefail
python -m pact profile --config configs/pilot/profile_20.yaml "$@"
