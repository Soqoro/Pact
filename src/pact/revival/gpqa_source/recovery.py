"""Reuse owned durable wallets; scheduler identity never supplies scientific state."""
from pathlib import Path
from contextlib import contextmanager
from ...artifacts import run_lock
from ...util import read_json,digest
from ..allocation_v3.storage import Wallet
from ..allocation_v3.design import BUDGET


def inspect(root,plan):
    root=Path(root)
    if not root.is_dir():raise ValueError('durable_owner_missing_no_reset')
    if not (root/'plan.json').is_file() or digest(read_json(root/'plan.json'))!=digest(plan):raise ValueError('durable_plan_owner_required')
    for marker in ('INFLIGHT.json','SNAPSHOT_PENDING.json'):
        if (root/marker).exists():raise ValueError('durable_operation_unresolved')
    wallet=Wallet(root,plan)
    counts=wallet.counts()
    return {'spent':counts,'remaining':{p:{k:BUDGET[p][k]-v for k,v in counts[p].items()} for p in counts},
            'plan_hash':digest(plan),'scheduler_identity_used':False,'resume_requires_exact_checkpoint_state':True}


@contextmanager
def owned(root,plan):
    """Single writer, including same-ID requeues. Stale lock is not auto-cleared."""
    if (Path(root)/'.lock').exists():raise RuntimeError('existing_owner_lock_requires_review')
    with run_lock(Path(root)):
        inspect(root,plan)
        yield Wallet(Path(root),plan)


def checkpoint_resume(path,contract,model,optimizer):
    # Existing typed tensor/model/optimizer/RNG restoration, including committed step.
    # This function is never called by source audit or CLI; no fresh-optimizer fallback.
    from .. import neural
    if not Path(path).is_dir():raise ValueError('committed_checkpoint_missing')
    return neural.load(Path(path),contract,model,optimizer)
