"""Standalone environment check; no PACT/model imports or study artifacts."""
import hashlib
import importlib.metadata as metadata
import json
import platform
import sys
from pathlib import Path

EXPECTED = {
    'torch': '2.11.0+cu130', 'transformers': '4.57.6', 'peft': '0.18.1',
    'accelerate': '1.12.0', 'tokenizers': '0.22.2', 'huggingface-hub': '0.36.2',
    'jinja2': '3.1.6', 'numpy': '2.1.3', 'safetensors': '0.8.0',
}
FINGERPRINT = 'e4e0376b3dc5b25abcec3b0bc314936d209d519b0b862af52f5255f7bd6532b0'


def main():
    mode, destination = sys.argv[1:]
    if mode not in ('install', 'gpu'):
        raise ValueError('Expected install or gpu mode')
    packages = {name: metadata.version(name) for name in EXPECTED}
    print(json.dumps({'python': platform.python_version(), 'packages': packages}), flush=True)
    if platform.python_version() != '3.13.15' or packages != EXPECTED:
        raise RuntimeError('Recorded Python/package versions do not match')
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import peft
    result = {'packages': packages, 'python': platform.python_version(),
              'python_executable_sha256': hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest(),
              'all_packages': dict(sorted((d.metadata['Name'], d.version)
                                         for d in metadata.distributions() if d.metadata['Name'])),
              'model_calls': 0, 'training_forwards': 0, 'study_state_changed': False,
              'gpu_verified': False}
    if mode == 'gpu':
        if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
            raise RuntimeError('Exactly one CUDA GPU required')
        runtime = {'python': platform.python_version(), 'platform': platform.system(),
                   'machine': platform.machine(), 'packages': packages,
                   'cuda': torch.version.cuda, 'gpu': torch.cuda.get_device_name(0)}
        actual = hashlib.sha256(json.dumps(runtime, sort_keys=True, ensure_ascii=True,
                                          separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        print(json.dumps({'runtime': runtime, 'fingerprint': actual}), flush=True)
        if actual != FINGERPRINT:
            raise RuntimeError('Recorded runtime mismatch; do not change the saved fingerprint')
        if not torch.cuda.is_bf16_supported():
            raise RuntimeError('BF16 required')
        with torch.inference_mode():
            x = torch.ones((32, 32), device='cuda', dtype=torch.bfloat16)
            if not torch.equal(x @ x, torch.full_like(x, 32)):
                raise RuntimeError('BF16 matrix check failed')
            q = torch.zeros((1, 1, 8, 16), device='cuda', dtype=torch.bfloat16)
            v = torch.ones_like(q)
            out = torch.nn.functional.scaled_dot_product_attention(q, q, v)
            if not torch.equal(out, v):
                raise RuntimeError('BF16 attention check failed')
            torch.cuda.synchronize()
        loaded = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                         if '/libcuda.so' in line})
        if not loaded or any(not p.startswith('/opt/pact-compat/compat/') for p in loaded):
            raise RuntimeError('Unexpected CUDA driver library')
        result.update(gpu_verified=True, runtime=runtime, fingerprint=actual, loaded_libcuda=loaded,
                      bf16_matmul=True, bf16_sdpa=True)
    with Path(destination).open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True)
    print('EXACT_RUNTIME_GPU_OK' if mode == 'gpu' else 'EXACT_PACKAGES_AND_IMPORTS_OK', flush=True)


if __name__ == '__main__':
    main()
