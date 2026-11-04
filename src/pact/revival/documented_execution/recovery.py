"""Latest-only owned recovery with no model dispatch or spending reset."""
from pathlib import Path
from ...util import file_hash, read_json
from ..allocation_v3 import storage
from ..documented_freeze import no_symlinks
from . import plan


def restore(destination,root,expected_hash):
    destination,root=map(Path,(destination,root))
    no_symlinks(destination);no_symlinks(root)
    if destination.name!=plan.RUN or root.name!=plan.RUN or root.exists():
        raise ValueError('exact_new_restore_destination_required')
    if any((destination/n).exists() for n in ('INFLIGHT.json','SNAPSHOT_PENDING.json')):
        raise ValueError('unsafe_latest_boundary')
    snaps=sorted((destination/'snapshots').glob('*'))
    if not snaps:raise ValueError('no_snapshot')
    latest=snaps[-1]
    if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json'):
        raise ValueError('incomplete_latest_no_fallback')
    h=read_json(latest/'index.json')['files']['receipt.json']
    if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('invalid_object')
    obj=destination/'objects'/h
    if file_hash(obj)!=h:raise ValueError('corrupt_receipt')
    r=read_json(obj)
    if not r['safe'] or r['plan_hash']!=expected_hash:raise ValueError('unsafe_or_wrong_owner')
    storage.restore(destination,root)
    # Restored evidence is retained on validation failure; it cannot dispatch.
    plan.validate(root,expected_hash)
    return {'restored':True,'model_calls':0,'execution_authorized':False}
