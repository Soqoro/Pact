"""AAI storage-only restore. Never invokes model, verification or execution stages."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

COMMIT = 'a2ad51f60530e6dafaf1377eba03d0753f87ff92'
TRANSPORT = '13219f390910046bfcd7c065a0353cb823ca3a3ca2f95fcec032bcd88da4f411'
EXPECTED_FILES = {
    'inputs/pact-heterogeneous-receiver-training-continuation-003-PRIVATE-1792630912628874679.zip': '2d65cbe6bee279608ca472af081e1d1ca4305de44af7d73e859eb4581e870959',
    'inputs/pact-heterogeneous-receiver-training-continuation-003-RECOVERY-1792630916259050432.zip': '2ea19eae5697a12470c9cca55c3be55ba847fbe5f0a22bb71b5e1af92a0a48ba',
}


def prepare_git(destination):
    """Carry real node Git + its linked libraries, isolated from Python's loader."""
    destination.mkdir()  # exclusive: retain partial preparation on failure
    binary = Path(shutil.which('git') or '/usr/bin/git').resolve(strict=True)
    linked = subprocess.check_output(['ldd', str(binary)], text=True)
    if 'not found' in linked:
        raise RuntimeError('Host Git has missing libraries')
    paths = {Path(p).resolve(strict=True) for p in re.findall(r'(/[^\s()]+)', linked)}
    loader = [p for p in paths if p.name.startswith('ld-linux')]
    if len(loader) != 1:
        raise RuntimeError('Expected one Linux dynamic loader')
    libs = destination / 'lib'
    libs.mkdir()
    # Preserve names from ldd as aliases can differ from resolved library names.
    receipt = {}
    for raw in re.findall(r'(/[^\s()]+)', linked):
        p = Path(raw)
        target = libs / p.name
        shutil.copyfile(p, target)
        target.chmod(0o700)
        receipt[str(target)] = hashlib.sha256(target.read_bytes()).hexdigest()
    target = destination / 'git.real'
    shutil.copyfile(binary, target)
    target.chmod(0o700)
    receipt[str(target)] = hashlib.sha256(target.read_bytes()).hexdigest()
    import shlex
    loader_name = next(Path(p).name for p in re.findall(r'(/[^\s()]+)', linked)
                       if Path(p).resolve() == loader[0])
    command = [str(libs / loader_name), '--library-path', str(libs), str(target)]
    wrapper = destination / 'git'
    wrapper.write_text('#!/bin/sh\nexec ' + shlex.join(command) + ' "$@"\n')
    wrapper.chmod(0o700)
    (destination / 'receipt.json').write_text(json.dumps(receipt, indent=2))
    subprocess.run([str(wrapper), '--version'], check=True)


def restore(base, checkout, bundle):
    import aai_stage1_transport as transport
    require = transport.require
    require(subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip() == COMMIT,
            'Wrong scientific commit')
    require(not subprocess.check_output(['git', '-C', str(checkout), 'status', '--porcelain'], text=True).strip(),
            'Scientific checkout has changes')
    # Only explicitly pinned repository code may be imported; no bundle code is executed.
    sys.path.insert(0, str(checkout / 'src'))
    from pact.revival.stage1 import io, weights, evidence
    from pact.util import read_json, digest
    transport.verify(bundle, TRANSPORT)
    destination = base / 'transport'
    tensors = Path('/content/pact-stage1/verified-final-tensors')
    run = Path('/content/pact-stage1/runs') / transport.RUN
    require(not any(p.exists() for p in (destination, tensors, run, base / 'restore-receipt.json')),
            'Restore target exists; preserve it and review, no automatic retry')
    require(shutil.disk_usage(base).free >= 8 * 1024**3, 'At least 8GiB free required for storage check')
    with zipfile.ZipFile(bundle) as z:
        meta = json.loads(z.read('TRANSPORT.json'))
        require(len(meta['files']) == 6, 'Unexpected transfer inventory')
        for n, h in EXPECTED_FILES.items():
            require(meta['files'].get(n) == h, 'Prerequisite archive mismatch')
        destination.mkdir(mode=0o700)
        for name in meta['files']:
            transport.safe_name(name)
            target = destination / name
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as source, target.open('xb') as output:
                shutil.copyfileobj(source, output)
            require(transport.file_sha(target) == meta['files'][name], 'Extracted transport checksum mismatch')
    persistent = destination / 'persistent' / transport.RUN
    print('Restoring compact snapshot with pinned reader...', flush=True)
    restored = io.restore(persistent, run)
    require(digest(read_json(run / 'plan.json')) == transport.PLAN, 'Restored plan mismatch')
    print('Mapping six exact final tensor files...', flush=True)
    recovery_name = next(n for n in EXPECTED_FILES if '-RECOVERY-' in n)
    private_name = next(n for n in EXPECTED_FILES if '-PRIVATE-' in n)
    mapped = io.map_recovery(destination / recovery_name, EXPECTED_FILES[recovery_name],
                             destination / private_name, tensors)
    mapping = read_json(tensors / 'checkpoint-map.json')
    lineage = read_json(run / 'training_lineage_map.json')
    require(len(mapping) == 6 and set(mapping) == set(lineage), 'Expected six lineage-bound adapters')
    verified = []
    for fit in sorted(mapping):
        require(mapping[fit] == lineage[fit]['tensor_path'], 'Historical tensor path mismatch')
        print('Checking tensor inventory:', fit, flush=True)
        values, row = weights.tensor_inventory(run, fit)
        verified.append({k: row[k] for k in ('fit', 'file_sha256', 'adapter_hash', 'structural_validity', 'historical_tensor_verified')})
        del values
    evidence.guard(run)
    # These are reads only; no report rewrite, journal dispatch or synthetic verification.
    stages = {name: (run / 'stages' / (name + '.json')).exists()
              for name in ('smoke', 'validation', 'source_evaluation', 'fixed_history')}
    require(stages == dict(smoke=True, validation=True, source_evaluation=True, fixed_history=False),
            'Unexpected completed-stage boundary')
    require(io.safety(run), 'Unsafe restored dispatch boundary')
    result = {'format': 'aai_storage_restore_v1', 'snapshot': restored['snapshot'],
              'transport_sha256': TRANSPORT, 'scientific_commit': COMMIT,
              'plan_hash': transport.PLAN, 'resolution_hash': transport.RESOLUTION,
              'stages': stages, 'tensors': verified, 'generation_calls': 0,
              'training_forwards': 0, 'optimizer_updates': 0, 'synthetic_forwards': 0,
              'fixed_history_started': False, 'scientific_hot_storage_ready': False}
    with (base / 'restore-receipt.json').open('x') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result, indent=2), flush=True)
    print('STORAGE_RESTORE_AND_SIX_TENSORS_OK', flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['prepare-git', 'restore'])
    p.add_argument('--base', type=Path, required=True)
    p.add_argument('--checkout', type=Path)
    p.add_argument('--bundle', type=Path)
    a = p.parse_args()
    os.umask(0o077)
    if a.mode == 'prepare-git':
        prepare_git(a.base / 'git-runtime')
    else:
        restore(a.base, a.checkout, a.bundle)
