"""Storage-only transfer of the latest safe Stage I snapshot and final-weight archives."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

RUN = 'pact-revival-stage1-evaluation-amended-002'
TRAIN = 'pact-heterogeneous-receiver-training-continuation-003'
PLAN = '288a2f9bd5bcbe95c52fd9b7d99cdefd2cb52ebd69c71a0c2939c2428dc72bf5'
RESOLUTION = '6b9c89d431c7b988215bec34a52270b1d9e43c1f8c17693d10ce8e37e9aabbaa'
PRIVATE = TRAIN + '-PRIVATE-1792630912628874679.zip'
PRIVATE_SHA = '2d65cbe6bee279608ca472af081e1d1ca4305de44af7d73e859eb4581e870959'
RECOVERY = TRAIN + '-RECOVERY-1792630916259050432.zip'


def sha(stream):
    h = hashlib.sha256()
    while chunk := stream.read(8 * 1024 * 1024):
        h.update(chunk)
    return h.hexdigest()


def file_sha(path):
    with path.open('rb') as f:
        return sha(f)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def hexsha(value):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'Invalid SHA256')
    return value


def safe_name(name):
    p = PurePosixPath(name)
    require(name and not p.is_absolute() and '..' not in p.parts and '\\' not in name,
            'Unsafe archive name')


def safe_boundary(root):
    require(not any((root / n).exists() for n in ('SNAPSHOT_PENDING.json', 'INFLIGHT.json')),
            'Pending/ambiguous work: stop, no fallback')
    snaps = sorted((root / 'snapshots').iterdir())
    require(bool(snaps), 'No snapshot')
    snap = snaps[-1]
    raw = (snap / 'index.json').read_bytes()
    require((snap / 'COMPLETE').read_text().strip() == hashlib.sha256(raw).hexdigest(),
            'Latest snapshot incomplete/corrupt')
    index = json.loads(raw)['files']
    require(set(index) == {'state.zip', 'receipt.json'}, 'Expected compact snapshot')
    for h in index.values():
        hexsha(h)
    return snap, raw, index


def validate_state(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate state member')
        for n in names:
            safe_name(n)
        checks = json.loads(z.read('checksums.json'))
        require(set(names) == set(checks) | {'checksums.json', 'HANDOFF.json'}, 'State inventory mismatch')
        for i, (n, h) in enumerate(checks.items(), 1):
            with z.open(n) as stream:
                require(sha(stream) == hexsha(h), 'State member checksum mismatch')
            if i % 5000 == 0:
                print(f'Verified state members: {i}/{len(checks)}', flush=True)
        read = lambda n: json.loads(z.read(n))
        require(digest(read('contract_resolution.json')) == RESOLUTION, 'Unexpected resolution')
        require(digest(read('plan.json')) == PLAN, 'Unexpected plan')
        require(read('recovery.json')['recovery_safe'] is True, 'Unsafe state')
        for stage in ('smoke', 'validation', 'source_evaluation'):
            s = read(f'stages/{stage}.json')
            require(s.get('execution_complete') is True and s.get('fixture') is False
                    and s.get('plan_hash') == PLAN, 'Stage identity/completion mismatch')
        require('stages/fixed_history.json' not in names, 'Fixed history already recorded; review first')
        require(read('exports/source_evaluation.json')['complete_at_export'] is True, 'Missing export receipt')
        intents = {n.removeprefix('intents/').removesuffix('.json') for n in names
                   if n.startswith('intents/') and n.endswith('.json')}
        calls = {n.removeprefix('calls/shards/').removesuffix('.json') for n in names
                 if n.startswith('calls/shards/') and n.endswith('.json')}
        require(intents == calls and len(calls) == 11712, 'Unexpected or unresolved generation inventory')


def pack(drive, output):
    require(not output.exists(), 'Output exists; preserve it')
    persistent = drive / 'stage1-evaluation' / RUN
    snap, index_raw, index = safe_boundary(persistent)
    training = drive / 'revival' / TRAIN / 'bundles'
    recovery_sha = hexsha((training / (RECOVERY + '.sha256')).read_text().split()[0])
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent, prefix='transport-stage-') as tmp:
        stage = Path(tmp)
        files = {}
        sources = {
            'inputs/' + PRIVATE: (training / PRIVATE, PRIVATE_SHA),
            'inputs/' + RECOVERY: (training / RECOVERY, recovery_sha),
        }
        for name, h in index.items():
            sources['persistent/' + RUN + '/objects/' + h] = (persistent / 'objects' / h, h)
        required = 2 * sum(source.stat().st_size for source, _ in sources.values()) + 1024**3
        require(shutil.disk_usage(output.parent).free >= required, 'Insufficient local staging space')
        for name, (source, expected) in sources.items():
            print('Copying and hashing:', name, flush=True)
            require(not source.is_symlink(), 'Source symlink')
            target = stage / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            require(file_sha(target) == expected, 'Source/copy hash mismatch')
            files[name] = expected
        receipt = json.loads((stage / 'persistent' / RUN / 'objects' / index['receipt.json']).read_text())
        require(receipt.get('format') == 'stage1_compact_snapshot_v1' and receipt.get('recovery_safe') is True
                and receipt.get('resolution_hash') == RESOLUTION and receipt.get('sha256') == index['state.zip'],
                'Snapshot receipt mismatch')
        validate_state(stage / 'persistent' / RUN / 'objects' / index['state.zip'])
        for name in ('index.json', 'COMPLETE'):
            relative = 'persistent/' + RUN + '/snapshots/' + snap.name + '/' + name
            target = stage / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(snap / name, target)
            files[relative] = file_sha(target)
        after, after_raw, _ = safe_boundary(persistent)
        require(after.name == snap.name and after_raw == index_raw, 'Drive changed during transfer')
        manifest = {'format': 'aai_stage1_transport_v1', 'run_id': RUN, 'plan_hash': PLAN,
                    'resolution_hash': RESOLUTION, 'snapshot': snap.name, 'files': files,
                    'recovery_sha256': recovery_sha, 'generation_calls': 0, 'restored': False}
        with zipfile.ZipFile(output, 'x', zipfile.ZIP_STORED) as z:
            for name in files:
                z.write(stage / name, name)
            z.writestr('TRANSPORT.json', json.dumps(manifest, sort_keys=True, indent=2))
    result = {'path': str(output), 'sha256': file_sha(output), 'bytes': output.stat().st_size,
              'snapshot': snap.name, 'generation_calls': 0, 'restored': False}
    print(json.dumps(result, indent=2), flush=True)


def verify(bundle, expected):
    require(file_sha(bundle) == hexsha(expected), 'Transport archive checksum mismatch')
    with zipfile.ZipFile(bundle) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'Duplicate transport member')
        for n in names:
            safe_name(n)
        meta = json.loads(z.read('TRANSPORT.json'))
        require(meta.get('format') == 'aai_stage1_transport_v1' and meta.get('run_id') == RUN
                and meta.get('plan_hash') == PLAN and meta.get('resolution_hash') == RESOLUTION,
                'Wrong transfer identity')
        require(set(names) == set(meta['files']) | {'TRANSPORT.json'}, 'Transfer inventory mismatch')
        for n, h in meta['files'].items():
            with z.open(n) as stream:
                require(sha(stream) == hexsha(h), 'Transfer member checksum mismatch')
        print(json.dumps({'transport_verified': True, 'snapshot': meta['snapshot'],
                          'files': len(meta['files']), 'restored': False, 'generation_calls': 0}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    a = sub.add_parser('pack')
    a.add_argument('--drive-root', type=Path, required=True)
    a.add_argument('--output', type=Path, required=True)
    a = sub.add_parser('verify')
    a.add_argument('--bundle', type=Path, required=True)
    a.add_argument('--sha256', required=True)
    args = p.parse_args()
    if args.command == 'pack':
        pack(args.drive_root, args.output)
    else:
        verify(args.bundle, args.sha256)
