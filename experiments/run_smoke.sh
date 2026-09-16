#!/usr/bin/env bash
set -euo pipefail
python -m pact smoke --config configs/smoke/qwen3_8b.yaml "$@"
