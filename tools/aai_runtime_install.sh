#!/bin/bash
# Executed inside the verified Ubuntu container by aai_runtime_setup.sbatch.
set -euo pipefail
PACT_ENV_ROOT="$1"
PACT_TOOLS="$2"
export UV_CACHE_DIR="$PACT_ENV_ROOT/cache"
export UV_PYTHON_INSTALL_DIR="$PACT_ENV_ROOT/python"
export UV_PYTHON_BIN_DIR="$PACT_ENV_ROOT/bin"
export TMPDIR="$PACT_ENV_ROOT/tmp"
export UV_LINK_MODE=copy
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
UV="$PACT_ENV_ROOT/bootstrap/bin/uv"
"$UV" --version
"$UV" python install 3.13.15
"$UV" venv --python 3.13.15 --managed-python "$PACT_ENV_ROOT/venv"
PYTHON="$PACT_ENV_ROOT/venv/bin/python"
"$UV" pip install --python "$PYTHON" 'torch==2.11.0+cu130' \
  --index-url https://download.pytorch.org/whl/cu130
"$UV" pip install --python "$PYTHON" \
  'torch==2.11.0+cu130' 'transformers[chat-template]==4.57.6' \
  'peft==0.18.1' 'accelerate==1.12.0' 'tokenizers==0.22.2' \
  'huggingface-hub==0.36.2' 'jinja2==3.1.6' 'numpy==2.1.3' \
  'safetensors==0.8.0' 'pyarrow==22.0.0' \
  --index-url https://pypi.org/simple
"$UV" pip check --python "$PYTHON"
"$UV" pip freeze --python "$PYTHON" > "$PACT_ENV_ROOT/installed-requirements.txt"
"$PYTHON" -I -u "$PACT_TOOLS/aai_runtime_probe.py" install "$PACT_ENV_ROOT/install-receipt.json"
