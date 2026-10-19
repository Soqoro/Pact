"""Bounded, member-addressed revival snapshots. Plan-bound retention; no implicit migration."""
import os
import shutil
import tempfile
from pathlib import Path

from ..artifacts import _sync_run, safe_relative
from ..util import digest, file_hash, read_json, write_json

FORMAT = 'revival_files_v1'
MAX_OBJECT_BYTES = 32 * 1024**3


def persist_files(root, destination, *, progress=lambda message: None):
    from .runtime import recovery_files, recovery_safe
    root, destination = Path(root), Path(destination)
    pending = destination / 'SNAPSHOT_PENDING.json'
    if pending.exists():
        raise ValueError('Unfinished snapshot; preserve evidence, no automatic retry')
    snapshots = sorted((destination / 'snapshots').glob('*'))
    if snapshots:
        latest = snapshots[-1]
        if (latest / 'COMPLETE').read_text().strip() != file_hash(latest / 'index.json'):
            raise ValueError('Latest snapshot incomplete; no older fallback')
        index = read_json(latest / 'index.json')
        if 'recovery.json' not in index['files']:
            raise ValueError('Legacy persistence requires explicit reviewed migration; no overwrite')
        for name, sha in index['files'].items():
            safe_relative(name)
            if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):
                raise ValueError('Invalid existing object identifier')
            obj=destination/'objects'/sha
            if obj.is_symlink() or file_hash(obj)!=sha:
                raise ValueError('Latest snapshot object missing/corrupt; no overwrite')
    if snapshots:
        previous = read_json(destination/'objects'/index['files']['recovery.json'])
        if previous['format'] != FORMAT or previous['plan_hash'] != digest(read_json(root/'plan.json')):
            raise ValueError('Persistence format/plan mismatch; no migration')
    from .retention import POLICY
    policy = read_json(root/'plan.json').get('storage_retention')
    if policy is not None and policy != POLICY:
        raise ValueError('Unknown retention policy')
    if snapshots and previous.get('retention_policy') != policy:
        raise ValueError('Retention policy changed; no migration')
    marker = {'format': FORMAT, 'plan_hash': digest(read_json(root/'plan.json'))}
    write_json(pending, marker)
    if read_json(pending) != marker:
        raise OSError('Snapshot pending marker verification failed')
    # Capture under the caller's run lock. Hardlinks avoid a second scratch copy;
    # the synchronous worker completes before the next optimizer step can start.
    with tempfile.TemporaryDirectory(dir=root.parent, prefix='.revival-files-') as tmp:
        staging = Path(tmp)
        checks = {}
        for f in recovery_files(root):
            rel = f.relative_to(root).as_posix()
            if any(part.startswith('.') for part in Path(rel).parts):
                raise ValueError('Hidden run member cannot be omitted from recovery')
            if rel == 'recovery.json':
                raise ValueError('Reserved snapshot metadata in run')
            checks['run/' + rel] = file_hash(f)
            target = staging / 'run' / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            os.link(f, target)
        receipt = {'format': FORMAT, 'plan_hash': digest(read_json(root/'plan.json')),
                   'recovery_safe': recovery_safe(root), 'files': checks,
                   'max_object_bytes': MAX_OBJECT_BYTES, 'retention_policy': policy}
        write_json(staging/'recovery.json', receipt)
        objects = destination/'objects'
        existing = {}
        for p in objects.glob('*'):
            if p.is_symlink() or not p.is_file():
                raise ValueError('Unexpected object store entry')
            existing[p.name] = p.stat().st_size
        sizes = {file_hash(p): p.stat().st_size for p in staging.rglob('*') if p.is_file()}
        projected = sum(existing.values()) + sum(n for h,n in sizes.items() if h not in existing)
        # Reject corruption rather than replacing objects or undercounting growth.
        for sha in sizes.keys() & existing.keys():
            if existing[sha] != sizes[sha] or file_hash(objects/sha) != sha:
                raise ValueError('Existing object corrupt; no replacement')
        if projected > MAX_OBJECT_BYTES:
            raise ValueError('Revival object-store capacity exceeded; preserve scratch; no automatic pruning or resume')
        snapshot = _sync_run(staging, destination, progress=progress)
        written = read_json(snapshot/'index.json')['files']
        if written != {**checks, 'recovery.json': file_hash(staging/'recovery.json')}:
            raise ValueError('Persisted member map differs; preserve pending marker')
        if policy is not None:
            from .retention import prune
            prune(destination, receipt['plan_hash'])
        if receipt['recovery_safe']:
            (destination/'INFLIGHT.json').unlink(missing_ok=True)
        pending.unlink()
        return {'snapshot': str(snapshot), 'format': FORMAT,
                'projected_object_bytes': projected, 'max_object_bytes': MAX_OBJECT_BYTES, 'retention_policy': policy}


def restore_files(persistent, root, index, obj):
    """Latest only; validate every member before exposing a local destination."""
    from .runtime import Journal, recovery_safe
    from ..studies.forensics import private_root
    receipt = read_json(obj('recovery.json'))
    checks = receipt['files']
    if receipt['format'] != FORMAT or not receipt['recovery_safe']:
        raise ValueError('Latest file snapshot unsafe or incompatible')
    if index['files'] != {**checks, 'recovery.json': index['files']['recovery.json']}:
        raise ValueError('Snapshot receipt/index mismatch')
    if root.exists():
        raise ValueError('Absent destination required')
    paths = {}
    for name, sha in checks.items():
        safe_relative(name)
        if not name.startswith('run/'):
            raise ValueError('Snapshot member outside run')
        paths[name[4:]] = obj(name)
    plan = read_json(paths['plan.json'])
    if digest(plan) != receipt['plan_hash']:
        raise ValueError('Recovered plan differs')
    # A rejected journal/optimizer state never becomes the destination.
    with tempfile.TemporaryDirectory(dir=root.parent, prefix='.revival-restore-') as tmp:
        stage = Path(tmp)/'run'
        private_root(stage, plan['source']['fixture'])
        for name, source in paths.items():
            target = stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            if file_hash(target) != checks['run/'+name]:
                raise ValueError('Local restored copy checksum mismatch')
        Journal(stage)
        if not recovery_safe(stage):
            raise ValueError('Snapshot receipt contradicts unresolved execution state')
        stage.rename(root)
