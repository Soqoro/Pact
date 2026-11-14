"""Apply the user-approved checksum-only transition as a separate inactive copy.

Run using pact from the approved 93b89ce3 checkout, not the helper's checkout.
No source validator is changed and the original plan/snapshot stays intact.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from pact.util import canonical, digest, file_hash, read_json, write_json
from pact.environment import code_identity
from pact.artifacts import run_lock
from pact.revival.documented_execution import plan, report
from pact.revival.documented_freeze import no_symlinks
from pact.revival.gpqa_source.sources import private_path
from pact.revival.allocation_v3 import storage

PROPOSAL_SHA='6e217d91d3b00464013ad3734a4ee1d23a476c619237c93e303c0e6c4d376d6a'
OLD_PLAN='5ff472604f74ed80cdbdecb574dc83c9306e6a912f0159249b1861a689fdd025'
TARGET={'git_commit':'93b89ce38be743acd6a3aa38177237ce99a3eeeb','dirty':False,
        'source_hash':'c7dbf4bccc7501456ee96aed79e7897e638674fe22faf4fb27a2ef30e54a4719'}
OLD_SNAPSHOT='1794641113259988805-22b145006de1'
FORBIDDEN={'attempts','events','outputs','scores','resources','branches','continuations','approvals','stages'}


def assert_inactive(root):
    for name in FORBIDDEN:
        p=root/name
        if p.is_symlink() or p.is_file() or any(v.is_file() or v.is_symlink() for v in p.rglob('*')):
            raise ValueError('original_child_has_execution_artifacts')
    if any((root/n).exists() for n in ('execution-preflight.json','policies.json','policy-lock.json')):
        raise ValueError('original_child_already_advanced')


def successor(original, target, root):
    """Only source identity and location change; all scientific fields survive."""
    if original.get('execution_authorized_by_plan') is not False or original.get('historical_spending') is not None:
        raise ValueError('not_the_inactive_uncertainty_preserving_plan')
    p=copy.deepcopy(original)
    p['source_code']=copy.deepcopy(target);p['scratch_root']=str(root.resolve())
    if {k for k in p if p[k]!=original[k]}!={'source_code','scratch_root'}:
        raise ValueError('exact_two_field_transition_required')
    return p


def verify_durable(root):
    if any((root/n).exists() for n in ('SNAPSHOT_PENDING.json','INFLIGHT.json')):
        raise ValueError('old_persistence_pending')
    snaps=sorted((root/'snapshots').iterdir())
    if not snaps or snaps[-1].name!=OLD_SNAPSHOT:raise ValueError('old_boundary_changed')
    snap=snaps[-1]
    if (snap/'COMPLETE').read_text().strip()!=file_hash(snap/'index.json'):raise ValueError('bad_complete_marker')
    idx=read_json(snap/'index.json')['files']
    def obj(name):
        h=idx[name]
        if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('invalid_object')
        path=root/'objects'/h;no_symlinks(path)
        if file_hash(path)!=h:raise ValueError('corrupt_object')
        return path
    receipt=read_json(obj('receipt.json'))
    if not receipt['safe'] or receipt['plan_hash']!=OLD_PLAN:raise ValueError('unsafe_or_wrong_snapshot')
    z,checks=storage.archive(obj('state.zip'),receipt['sha256'])
    try:
        if digest(json.loads(z.read('plan.json')))!=OLD_PLAN:raise ValueError('archive_plan_changed')
        if any(Path(n).parts[0] in FORBIDDEN or n in ('execution-preflight.json','policies.json','policy-lock.json') for n in checks):
            raise ValueError('durable_child_has_execution_artifacts')
    finally:z.close()
    return file_hash(snap/'index.json')


def apply(old_checkout,target,original,durable,proposal,output,persistent):
    old_checkout,target,original,durable,proposal,output,persistent=map(Path,
        (old_checkout,target,original,durable,proposal,output,persistent))
    for p in (old_checkout,target,original,durable,proposal,output,persistent):no_symlinks(p)
    private_path(output);private_path(persistent)
    if output.exists() or persistent.exists():raise ValueError('new_successor_destinations_required')
    if output.name!=plan.RUN or persistent.name!=plan.RUN:raise ValueError('same_logical_child_owner_required')
    if Path(plan.REPO).resolve()!=target.resolve() or code_identity(target)!=TARGET:
        raise ValueError('approved_target_checkout_required')
    if not original.is_dir():raise ValueError('original_run_missing')
    with run_lock(original):
        if file_hash(proposal/'proposal.sanitized.json')!=PROPOSAL_SHA:raise ValueError('unapproved_proposal')
        if (proposal/'COMPLETE').read_text().strip()!=file_hash(proposal/'checksums.json'):
            raise ValueError('proposal_incomplete')
        if read_json(proposal/'checksums.json')!={'proposal.sanitized.json':PROPOSAL_SHA}:
            raise ValueError('proposal_inventory_changed')
        decision=read_json(proposal/'proposal.sanitized.json')
        saved=read_json(original/'plan.json');before=file_hash(original/'plan.json')
        if digest(saved)!=OLD_PLAN or before!=decision['original_plan_file_sha256']:
            raise ValueError('original_plan_changed')
        if decision['proposed_source_code']!=TARGET or code_identity(old_checkout)!=decision['old_source_code']:
            raise ValueError('source_identity_changed')
        assert_inactive(original)
        snapshot_index=verify_durable(durable)
        env=dict(os.environ,PYTHONPATH=str(old_checkout/'src'),PYTHONDONTWRITEBYTECODE='1',
                 CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
        validation=subprocess.run([sys.executable,'-B','-c',
            'import sys; from pathlib import Path; from pact.revival.documented_execution.plan import validate; '
            'validate(Path(sys.argv[1]),sys.argv[2])',str(original),OLD_PLAN],
            env=env,cwd=old_checkout,capture_output=True)
        if validation.returncode:raise ValueError('original_validator_failed')
        p=successor(saved,TARGET,output)
        output.mkdir(parents=True,mode=0o700)
        (output/'sealed').mkdir(mode=0o700)
        for name in ('prospective.private.json','graph.private.json'):
            shutil.copyfile(original/'sealed'/name,output/'sealed'/name)
            if file_hash(original/'sealed'/name)!=file_hash(output/'sealed'/name):raise ValueError('copy_mismatch')
        write_json(output/'plan.json',p)
        new_hash=digest(p)
        plan.validate(output,new_hash)
        if file_hash(original/'plan.json')!=before:raise ValueError('original_plan_modified')
        assert_inactive(original)
        receipt={'version':'documented_checksum_source_transition_applied_v1',
            'status':'SOURCE_TRANSITION_APPLIED_EXECUTION_DISABLED',
            'approved_proposal_sha256':PROPOSAL_SHA,'user_instruction':'proceed',
            'authorization_scope':'exact_checksum_source_transition_only',
            'authorization_context':'reply to explicit proposal-bound transition approval question',
            'transition_approved':True,'transition_applied':True,'reviewer_signature':None,
            'old_plan_hash':OLD_PLAN,'new_plan_hash':new_hash,
            'changed_plan_fields':['scratch_root','source_code'],'old_source_code':saved['source_code'],
            'new_source_code':TARGET,'original_plan_preserved':True,
            'old_snapshot_index_sha256':snapshot_index,
            'freeze':p['freeze'],'conditional_limits':p['budgets'],
            'historical_spending':None,'remaining_historical_budget':None,
            'execution_authorized':False,'wallet_active':False,'gpu_preflight_authorized':False,
            'model_calls':0,'training_forwards':0,'optimizer_updates':0,
            'current_S0_tensors_rechecked':False,'helper_sha256':file_hash(Path(__file__))}
        write_json(output/'source-transition.sanitized.json',receipt)
        report.report(output,p)
        # Include transition provenance in SANITIZED output via its allowlisted summary.
        summary=read_json(output/'summary.json');summary['source_transition']=receipt
        write_json(output/'summary.json',summary)
        bundles=storage.export(output,'source-transition',persistent)
        if file_hash(original/'plan.json')!=before:raise ValueError('original_plan_modified')
        return {**receipt,'transition_receipt_sha256':file_hash(output/'source-transition.sanitized.json'),
                'bundles':bundles,'stop_for_review':True}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('old-checkout','target-checkout','original-run','old-persistent','proposal','output','persistent'):
        p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args()
    try:
        out=apply(a.old_checkout,a.target_checkout,a.original_run,a.old_persistent,a.proposal,a.output,a.persistent)
        print(canonical(out));return 0
    except Exception as e:
        import traceback
        print(canonical({'status':'stopped','exception_type':type(e).__name__,
            'locations':[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name}
                         for f in traceback.extract_tb(e.__traceback__)[-4:]],
            'action':'preserve_both_runs_no_automatic_retry'}));return 1


if __name__=='__main__':raise SystemExit(main())
