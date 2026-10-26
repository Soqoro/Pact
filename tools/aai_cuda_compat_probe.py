"""Allocated-GPU driver API diagnostic. No models, Torch or scientific calls."""
import ctypes as C
import hashlib
import json
import os
from pathlib import Path


def main():
    base = Path('/opt/pact-compat')
    receipt = json.loads((base / 'compat-receipt.json').read_text())
    libpath = base / 'compat/usr/local/cuda-13.0/compat/libcuda.so.1'
    assert hashlib.sha256(libpath.read_bytes()).hexdigest() == receipt['libcuda_sha256']
    cuda = C.CDLL(str(libpath))

    def call(name, argtypes, *args):
        fn = getattr(cuda, name)
        fn.argtypes = argtypes
        fn.restype = C.c_int
        rc = fn(*args)
        if rc:
            raise RuntimeError(f'{name}: CUDA driver error {rc}; no fallback')

    call('cuInit', [C.c_uint], 0)
    version = C.c_int()
    call('cuDriverGetVersion', [C.POINTER(C.c_int)], C.byref(version))
    assert version.value >= 13000, 'CUDA 13 driver API not available'
    count = C.c_int()
    call('cuDeviceGetCount', [C.POINTER(C.c_int)], C.byref(count))
    assert count.value == 1, f'Expected one Slurm-visible device; got {count.value}'
    device = C.c_int()
    call('cuDeviceGet', [C.POINTER(C.c_int), C.c_int], C.byref(device), 0)
    name = C.create_string_buffer(256)
    call('cuDeviceGetName', [C.c_void_p, C.c_int, C.c_int], name, len(name), device)
    gpu = name.value.decode()
    assert gpu == 'NVIDIA A100-SXM4-80GB', gpu
    context = C.c_void_p()
    call('cuDevicePrimaryCtxRetain', [C.POINTER(C.c_void_p), C.c_int], C.byref(context), device)
    try:
        call('cuCtxSetCurrent', [C.c_void_p], context)
        pointer = C.c_uint64()
        call('cuMemAlloc_v2', [C.POINTER(C.c_uint64), C.c_size_t], C.byref(pointer), 4096)
        call('cuMemFree_v2', [C.c_uint64], pointer)
    finally:
        call('cuDevicePrimaryCtxRelease_v2', [C.c_int], device)
    target = Path('/content/pact-stage1/verified-final-tensors')
    assert target.is_dir()
    assert not any(p.is_symlink() for p in (target, *target.parents))
    mapped = sorted({line.split()[-1] for line in Path('/proc/self/maps').read_text().splitlines()
                     if 'libcuda.so' in line})
    assert mapped and all('/opt/pact-compat/' in p for p in mapped), mapped
    print(json.dumps({'status': 'driver_api_and_bind_probe_passed', 'gpu': gpu,
                     'cuda_driver_api_version': version.value, 'visible_devices': count.value,
                     'cuda_visible_devices': os.environ.get('CUDA_VISIBLE_DEVICES'),
                     'allocated_and_freed_bytes': 4096, 'loaded_libcuda': mapped,
                     'package_receipt': receipt, 'recorded_tensor_path_available': True,
                     'torch_verified': False, 'model_calls': 0, 'training_forwards': 0,
                     'study_state_changed': False}, indent=2), flush=True)


if __name__ == '__main__':
    main()
