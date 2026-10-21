"""Opt-in tensor retention for new revival stores; never repair ambiguous history."""
from pathlib import Path
import re

from ..util import digest, file_hash, read_json, write_json
from ..artifacts import safe_relative

POLICY = {'version': 'revival_tensor_retention_v1', 'keep_latest_snapshots': 2,
          'keep_initial_and_epochs': True, 'delete_metadata': False}
TENSOR = re.compile(r'run/.+/checkpoints/step-[0-9]{6}/tensors\.safetensors\Z')


def retention_plan(destination, plan_hash):
    """Read-only, exact reference analysis. Unknown objects are never candidates."""
    from .persistence import FORMAT
    destination = Path(destination)
    snapshots = sorted((destination/'snapshots').iterdir())
    deleted = set()
    for audit in sorted((destination/'retention-audit').glob('*')):
        manifest = read_json(audit/'manifest.json')
        if (audit/'COMPLETE').read_text().strip() != file_hash(audit/'manifest.json'):
            raise ValueError('Incomplete retention audit; no retry')
        if manifest['plan_hash'] != plan_hash or manifest['policy'] != POLICY:
            raise ValueError('Retention audit identity mismatch')
        for sha, size in manifest['candidates'].items():
            if read_json(audit/'deleted'/f'{sha}.json') != {'object': sha, 'bytes': size}:
                raise ValueError('Retention deletion receipt mismatch')
        deleted.update(manifest['candidates'])
    refs, protect, indexes = set(), set(), {}
    # Invocation-local only: the caller holds the single-writer run lock. Never
    # reuse trust across checkpoints/processes or skip hashing on restore.
    verified_objects = {}
    presence = {}
    def exists(sha):
        if sha not in presence:
            presence[sha] = (destination/'objects'/sha).exists()
        return presence[sha]
    def verified(sha):
        if not re.fullmatch('[0-9a-f]{64}', sha):raise ValueError('Invalid object name')
        if sha not in verified_objects:
            obj = destination/'objects'/sha
            if obj.is_symlink() or file_hash(obj) != sha:raise ValueError('Corrupt retention reference')
            verified_objects[sha] = obj
        return verified_objects[sha]
    for snap in snapshots:
        idx = read_json(snap/'index.json')
        index_hash = file_hash(snap/'index.json')
        if (snap/'COMPLETE').read_text().strip() != index_hash:
            raise ValueError('Incomplete snapshot; no retention')
        indexes[snap.name] = index_hash
        receipt = read_json(verified(idx['files']['recovery.json']))
        if (receipt['format'] != FORMAT or receipt['plan_hash'] != plan_hash
                or receipt.get('retention_policy') != POLICY):
            raise ValueError('Unreviewed/legacy store; no retention')
        if idx['files'] != {**receipt['files'], 'recovery.json': idx['files']['recovery.json']}:
            raise ValueError('Receipt/index mismatch')
        for name, sha in idx['files'].items():
            safe_relative(name)
            if not re.fullmatch('[0-9a-f]{64}', sha):raise ValueError('Invalid object name')
            refs.add(sha)
            if snap in snapshots[-2:] or not TENSOR.fullmatch(name):
                protect.add(sha)
            obj = destination/'objects'/sha
            if not exists(sha) and sha not in deleted:
                raise ValueError('Unexplained missing historical object; no retention')
    # Latest two receipts may be unsafe; they are still fully protected evidence.
    for sha in protect:
        verified(sha)
    candidates = {}
    for sha in sorted(refs - protect):
        obj = destination/'objects'/sha
        if not exists(sha) and sha in deleted:continue
        verified(sha)
        candidates[sha] = obj.stat().st_size
    return {'policy': POLICY, 'plan_hash': plan_hash, 'indexes': indexes,
            'protected_objects': sorted(protect), 'candidates': candidates,
            'candidate_bytes': sum(candidates.values())}


def prune(destination, plan_hash):
    """Called only within pending snapshot transaction and single-writer lock."""
    destination = Path(destination)
    if not (destination/'SNAPSHOT_PENDING.json').is_file():
        raise ValueError('Retention requires active snapshot transaction')
    manifest = retention_plan(destination, plan_hash)
    if not manifest['candidates']:return {'deleted_objects': 0}
    audit = destination/'retention-audit'/digest(manifest)
    if audit.exists():raise ValueError('Existing retention transaction; inspect before retry')
    write_json(audit/'manifest.json', manifest)
    if read_json(audit/'manifest.json') != manifest:raise OSError('Retention manifest verification')
    # All candidate hashes checked before first mutation. Keep a durable record of
    # each completed deletion; a failure leaves SNAPSHOT_PENDING and no COMPLETE.
    for sha, size in manifest['candidates'].items():
        obj = destination/'objects'/sha
        if obj.is_symlink() or obj.stat().st_size != size:raise ValueError('Candidate changed')
        obj.unlink()
        write_json(audit/'deleted'/f'{sha}.json', {'object': sha, 'bytes': size})
    if any((destination/'objects'/h).exists() for h in manifest['candidates']):
        raise OSError('Retention deletion not confirmed')
    marker = file_hash(audit/'manifest.json')
    (audit/'COMPLETE').write_text(marker)
    if (audit/'COMPLETE').read_text() != marker:raise OSError('Retention completion verification')
    return {'deleted_objects': len(manifest['candidates']), 'removed_bytes': manifest['candidate_bytes']}


def prune_scratch(root):
    """After successful durable checkpoint only; keep two local steps plus epochs."""
    root=Path(root)
    if read_json(root/'plan.json').get('storage_retention')!=POLICY:return
    candidates={}
    for base in root.rglob('checkpoints'):
        if not base.is_dir() or base.is_symlink():continue
        steps=sorted(p for p in base.glob('step-*') if p.is_dir())
        keep={p.name for p in steps[-2:]}|{'step-000000'}
        for epoch in base.parent.glob('epoch*.json'):keep.add(f"step-{read_json(epoch)['step']:06d}")
        for step in steps:
            f=step/'tensors.safetensors'
            if step.name in keep or not f.exists():continue
            if f.is_symlink():raise ValueError('Symlink local tensor')
            candidates[f.relative_to(root).as_posix()]=file_hash(f)
    if not candidates:return
    manifest={'policy':POLICY,'files':candidates,'durable_checkpoint_completed':True}
    path=root/'scratch-retention'/f'{digest(manifest)}.json'
    write_json(path,manifest)
    for name,sha in candidates.items():
        f=root/name
        if file_hash(f)!=sha:raise ValueError('Local tensor changed during retention')
        f.unlink()
