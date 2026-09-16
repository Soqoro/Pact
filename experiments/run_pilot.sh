#!/usr/bin/env bash
set -euo pipefail
python -m pact pilot --config configs/pilot/validation_80.yaml "$@"
