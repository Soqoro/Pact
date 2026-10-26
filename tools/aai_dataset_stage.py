"""Copy verified Stage I inputs to private dataset storage; never run study code."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import zipfile

import aai_stage1_transport as transport
from aai_stage1_restore import TRANSPORT, COMMIT

TENSORS = {
    'independent_adversarial_sft/Q': '6262b3445b39066c8f1349e832145b549d226e289ae777f0cd5cb6096f11c7a2',
    'independent_adversarial_sft/L': 'b31db056bcc7d6caf2eebacc6def9fc5758d6ce032538af72c23300e33089548',
    'independent_adversarial_sft/M': '7e3686976e2e850d02f14f97ff4f196b2db6a6138c189251e92286aaa1dcc8b9',
    'uniform_joint_sft/Q': '0add7fa4ef0fcdb96ce57ed8506c30969bba82fd4c531566cf5e59cdbd175039',
    'uniform_joint_sft/L': '7bafbf347cfc3325923fd888b45b16dbfc74ada3aa1fe88d72b8d96d8984114c',
    'uniform_joint_sft/M': 'af864d7109fc30b4e9c138e129e19ebda1554952deb40bd948b95cdd492ed8bb',
}


def no_symlinks(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('Symlink in storage path')


def write_copy(source, target, expected):
    no_symlinks(source)
    no_symlinks(target)
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst, 8 * 1024**2)
        dst.flush()
        os.fsync(dst.fileno())
    transport.require(transport.file_sha(target) == expected, 'Copied file checksum mismatch')
    transport.require(stat.S_IMODE(target.stat().st_mode) == 0o600, 'Private file mode required')


def stage(home, user_root):
    os.umask(0o077)
    no_symlinks(user_root)
    transport.require(user_root.is_dir() and user_root.stat().st_uid == os.getuid(),
                      'Existing user-owned dataset directory required')
    project = user_root / 'PACT'
    no_symlinks(project)
    if not project.exists():
        project.mkdir(mode=0o700)
    transport.require(project.is_dir() and project.stat().st_uid == os.getuid(), 'Wrong project owner')
    base = project / 'stage1-migration-v1'
    transport.require(not base.exists(), 'Destination exists; preserve and review before retry')
    bundle = home / 'pact-aai-transfer/incoming/stage1-AAI-PRIVATE.zip'
    original = home / 'pact-aai-transfer/restoration-v1'
    # Independent Drive comparison binds this exact transport hash.
    transport.verify(bundle, TRANSPORT)
    with zipfile.ZipFile(bundle) as z:
        manifest = json.loads(z.read('TRANSPORT.json'))
    receipt_path = original / 'restore-receipt.json'
    receipt = json.loads(receipt_path.read_text())
    transport.require(receipt['transport_sha256'] == TRANSPORT and receipt['scientific_commit'] == COMMIT
                      and receipt['snapshot'] == manifest['snapshot']
                      and receipt['plan_hash'] == transport.PLAN
                      and receipt['resolution_hash'] == transport.RESOLUTION,
                      'Restoration receipt identity mismatch')
    transport.require(receipt['stages'] == dict(smoke=True, validation=True, source_evaluation=True, fixed_history=False)
                      and receipt['fixed_history_started'] is False, 'Unexpected study boundary')
    rows = {r['fit']: r for r in receipt['tensors']}
    transport.require(set(rows) == set(TENSORS), 'Expected six tensor receipts')
    copies = {'incoming/stage1-AAI-PRIVATE.zip': (bundle, TRANSPORT),
              'provenance/restore-receipt.json': (receipt_path, transport.file_sha(receipt_path))}
    for n, h in manifest['files'].items():
        transport.safe_name(n)
        copies['verified-inputs/' + n] = (original / 'transport' / n, h)
    tensor_root = original / 'content/pact-stage1/verified-final-tensors'
    mapping_path = tensor_root / 'checkpoint-map.json'
    mapping = json.loads(mapping_path.read_text())
    transport.require(set(mapping) == set(TENSORS), 'Unexpected checkpoint map')
    for fit, h in TENSORS.items():
        transport.require(rows[fit]['file_sha256'] == h and rows[fit]['historical_tensor_verified'] is True
                          and rows[fit]['structural_validity'] is True, 'Tensor receipt mismatch')
        transport.require(mapping[fit] == '/content/pact-stage1/verified-final-tensors/' + fit + '/tensors.safetensors',
                          'Recorded tensor path mismatch')
        n = 'content/pact-stage1/verified-final-tensors/' + fit + '/tensors.safetensors'
        copies[n] = (tensor_root / fit / 'tensors.safetensors', h)
    copies['content/pact-stage1/verified-final-tensors/checkpoint-map.json'] = (mapping_path, transport.file_sha(mapping_path))
    needed = sum(p.stat().st_size for p, _ in copies.values()) + 2 * 1024**3
    transport.require(shutil.disk_usage(project).free >= needed, 'Insufficient dataset storage')
    base.mkdir(mode=0o700)
    checks = {}
    for i, (name, (source, h)) in enumerate(copies.items(), 1):
        print(f'Copying and verifying {i}/{len(copies)}: {name}', flush=True)
        write_copy(source, base / name, h)
        checks[name] = h
    # Preserve the original evidence snapshot as inputs, not an execution persistence root.
    result = {'format': 'aai_private_dataset_stage_v1', 'transport_sha256': TRANSPORT,
              'snapshot': manifest['snapshot'], 'plan_hash': transport.PLAN,
              'files': checks, 'bytes': sum((base / n).stat().st_size for n in checks),
              'generation_calls': 0, 'training_forwards': 0, 'optimizer_updates': 0,
              'home_evidence_preserved': True, 'execution_started': False}
    receipt_file = base / 'DATASET_COPY_VERIFIED.json'
    with receipt_file.open('x') as f:
        json.dump(result, f, indent=2)
        f.flush()
        os.fsync(f.fileno())
    transport.require(json.loads(receipt_file.read_text()) == result, 'Receipt readback mismatch')
    print(json.dumps({'status': 'private_dataset_copy_verified', 'destination': str(base),
                      'verified_files': len(checks), 'bytes': result['bytes'],
                      'receipt_sha256': transport.file_sha(receipt_file),
                      'generation_calls': 0, 'home_evidence_preserved': True,
                      'execution_started': False}, indent=2), flush=True)


if __name__ == '__main__':
    import pwd
    user = pwd.getpwuid(os.getuid()).pw_name
    stage(Path.home(), Path('/dataset') / user)
