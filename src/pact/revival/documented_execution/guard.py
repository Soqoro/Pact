"""Explicit artifact-bound stage permissions, checked before creating a wallet.

An approval document is supplied by the operator after separate user review.
This package never creates approvals, signatures, or spending allowances.
"""
from pathlib import Path
from ...util import digest, read_json, file_hash
from ...studies.heterogeneity import immutable
from ..allocation_v3 import design as d, storage
from . import plan

STAGES=('preflight','assay-smoke','collect','branch','score','policy-freeze',
        'continuation','policy-lock','evaluation-smoke','evaluate')


def scope(stage, block=None, family=None, policy=None, seed=None):
    if stage not in STAGES:raise ValueError('unknown_stage')
    if stage=='branch':
        if block not in range(8) or family not in d.FAMILIES:raise ValueError('branch_scope_required')
        return {'stage':stage,'block':block,'family':family}
    if stage=='continuation':
        if family not in d.FAMILIES or policy not in d.POLICIES or seed not in d.SEEDS:
            raise ValueError('continuation_scope_required')
        return {'stage':stage,'family':family,'policy':policy,'seed':seed}
    if any(v is not None for v in (block,family,policy,seed)):raise ValueError('unexpected_stage_scope')
    return {'stage':stage}


def authorize(root, p, requested, approval, approval_sha, persistent=None):
    if not approval or not approval_sha:raise PermissionError('separate_artifact_bound_approval_required')
    approval=Path(approval)
    if file_hash(approval)!=approval_sha:raise PermissionError('approval_hash_mismatch')
    a=read_json(approval)
    expected={'version':'documented_stage2_stage_approval_v1','run_id':plan.RUN,
        'plan_hash':digest(p),'freeze':p['freeze'],'fixture':p['fixture'],
        'scope':requested,'limits':d.BUDGET,'historical_spending':None,
        'historical_budget_reset':False,'source_code':p['source_code']}
    if any(a.get(k)!=v for k,v in expected.items()):raise PermissionError('approval_binding_mismatch')
    # A digest is not a signature or a certification. It binds the separately
    # supplied user decision; the software does not invent that decision.
    if not isinstance(a.get('user_decision'),str) or not a['user_decision'].strip():
        raise PermissionError('user_decision_missing')
    if a.get('execution_approved') is not True:raise PermissionError('execution_not_approved')
    if requested['stage']=='preflight':
        if a.get('spending_approved') is not False:raise PermissionError('preflight_is_not_spending')
    else:
        if a.get('spending_approved') is not True:raise PermissionError('physical_spending_not_approved')
        ready=read_json(root/'execution-preflight.json')
        if (a.get('preflight_sha256')!=file_hash(root/'execution-preflight.json') or
            ready.get('plan_hash')!=digest(p) or ready.get('fixture')!=p['fixture'] or
            not all(ready.get(k) is True for k in ('gpu_runtime_checked','effective_S0_loading_checked','native_access_checked','context_checks_enabled'))):
            raise PermissionError('effective_preflight_required')
    if persistent is not None:
        persistent=Path(persistent)
        if persistent.name!=p['run_id']:raise ValueError('persistence_owner_mismatch')
        if any((persistent/n).exists() for n in ('SNAPSHOT_PENDING.json','INFLIGHT.json')):
            raise ValueError('unresolved_durable_boundary')
        snaps=sorted((persistent/'snapshots').glob('*'))
        if snaps:
            latest=snaps[-1]
            if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json'):
                raise ValueError('incomplete_latest_no_fallback')
            h=read_json(latest/'index.json')['files']['receipt.json']
            if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('invalid_receipt_address')
            obj=persistent/'objects'/h
            if obj.is_symlink() or file_hash(obj)!=h:raise ValueError('corrupt_durable_receipt')
            saved=read_json(obj)
            if saved['plan_hash']!=digest(p) or not saved['safe']:
                raise ValueError('durable_owner_or_boundary_changed')
    if not storage.safe(root):raise ValueError('unresolved_physical_attempt_no_retry')
    return a


def record(root, requested, approval_sha):
    immutable(root/'approvals'/f'{digest(requested)}.json',
              {'scope':requested,'approval_sha256':approval_sha})
