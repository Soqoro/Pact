"""CPU readiness bridge for the exact sealed child. No model factory or wallet.

This module is outside the frozen audit package to preserve its bound bytes.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import tempfile
from ..util import canonical, digest, file_hash, read_json
from . import documented_freeze as freezing
from .documented_child import review
from .allocation_v3 import design, evidence
from .gpqa_source.contracts import allocation_inputs

RECEIPT_SHA='0d1530b1658bcab6216eab9c6bb8dc311a2321b9efcb09f28960e7f233ad8921'
MANIFEST_SHA='b13f9f7571cb6b8a6d6fb3a5d17020dc77976d3e76887af6e35440a80cdd45e7'
METHOD='13817d7b6ebdb6634e9028d8421c57203bf76f1d2483d297b8ddba39bfa184f7'
PACKAGES={'torch':'2.11.0+cu130','transformers':'4.57.6','peft':'0.18.1',
    'accelerate':'1.12.0','tokenizers':'0.22.2','huggingface-hub':'0.36.2',
    'jinja2':'3.1.6','numpy':'2.1.3','safetensors':'0.8.0'}
VERSION='documented_stage2_cpu_preflight_v1'


def checked_inventory(root, expected_manifest):
    """Verify bounded named files; reject links, traversal and unsealed additions."""
    root=Path(root);freezing.no_symlinks(root)
    if file_hash(root/'checksums.json')!=expected_manifest or (root/'COMPLETE').read_text().strip()!=expected_manifest:
        raise ValueError('seal_marker_or_manifest_conflict')
    checks=read_json(root/'checksums.json')
    if not isinstance(checks,dict) or len(checks)>32:raise ValueError('seal_inventory_bound')
    for n,h in checks.items():
        if not isinstance(n,str) or Path(n).is_absolute() or '..' in Path(n).parts or '\\' in n:
            raise ValueError('unsafe_seal_member')
        path=root/n;freezing.no_symlinks(path)
        if path.stat().st_size>128*1024**2 or file_hash(path)!=h:raise ValueError('seal_member_changed')
    actual=set()
    for p in root.rglob('*'):
        freezing.no_symlinks(p)
        if p.is_file():actual.add(p.relative_to(root).as_posix())
    if actual!=set(checks)|{'checksums.json','COMPLETE'}:raise ValueError('unexpected_seal_files')
    return checks


def verify_seal(root):
    root=Path(root);checked_inventory(root,MANIFEST_SHA)
    if file_hash(root/'freeze.sanitized.json')!=RECEIPT_SHA:raise ValueError('freeze_receipt_conflict')
    r=read_json(root/'freeze.sanitized.json')
    if r['fixture'] is not False or r['candidate_frozen'] is not True or r['execution_authorized'] is not False or r['wallet_active'] is not False:
        raise ValueError('freeze_scope_conflict')
    for k,v in freezing.EXPECTED.items():
        if r[k]!=v:raise ValueError('frozen_identity_conflict')
    if r['method_digest']!=METHOD:raise ValueError('method_identity_conflict')
    summary=review.validate(root/'evidence')
    training=read_json(root/'training.private.json');allocation_inputs(training)
    if digest(training)!=r['training_dependency_hash']:raise ValueError('training_identity_conflict')
    for file,key in [('prospective.private.json','candidate_digest'),('graph.private.json','graph_digest')]:
        if digest(read_json(root/'sealed'/file))!=r[key]:raise ValueError('sealed_content_identity_conflict')
    if summary['candidate_digest']!=r['candidate_digest'] or summary['graph_digest']!=r['graph_digest']:
        raise ValueError('audit_freeze_conflict')
    return r,training,read_json(root/'evidence/method.private.json')


def package_check():
    expected={'python':'3.13.15','platform':'Linux','machine':'x86_64','packages':PACKAGES}
    actual={'python':platform.python_version(),'platform':platform.system(),'machine':platform.machine(),'packages':{}}
    for n in PACKAGES:
        try:actual['packages'][n]=importlib.metadata.version(n)
        except importlib.metadata.PackageNotFoundError:actual['packages'][n]=None
    return {'expected':expected,'actual':actual,'matches':actual==expected,
            'gpu_runtime_checked':False,'model_access_checked':False}


def check_checkpoint_result(family, actual, expected):
    if actual.get('fit')!='uniform_joint_sft/'+family:raise ValueError('wrong_starting_arm_or_family')
    for k in ('file_sha256','adapter_hash','keys_shapes','saved_dtype'):
        if actual.get(k)!=expected[k]:raise ValueError('S0_identity_conflict')
    if actual.get('structural_validity') is not True or actual.get('historical_tensor_verified') is not True:
        raise ValueError('unverified_S0_tensor')
    return {k:actual[k] for k in ('fit','file_sha256','adapter_hash','saved_dtype','structural_validity','historical_tensor_verified')}


def execution_contract(receipt, training, method):
    """Build a non-dispatchable bridge to the existing native stage implementations.

    Evaluation content never enters this training/assay interface. A code pointer
    is not an execution grant; all calls remain behind a separate approval gate.
    """
    allocation_inputs(training)
    return {'version':VERSION,'child':review.CHILD,'status':'EXECUTION_DISABLED',
        'freeze_receipt_sha256':RECEIPT_SHA,'method_digest':receipt['method_digest'],
        'candidate_digest':receipt['candidate_digest'],'graph_digest':receipt['graph_digest'],
        'training_dependency_hash':receipt['training_dependency_hash'],
        's0':{f:method['S0'][f]['adapter_hash'] for f in design.FAMILIES},
        'training_source':{'records':training['records'],'labels':training['labels']},
        'blocks':training['blocks'],'shuffle':training['shuffle'],'train':design.TRAIN,
        'analysis':design.ANALYSIS,'policies':list(design.POLICIES),'seeds':list(design.SEEDS),
        'budgets':design.BUDGET,'evaluation_source_weights':{'gpqa_main':.5,'logiqa':.5},
        'stages':{'assay-smoke':'allocation_v3.runner.collect(smoke=True)',
            'collect':'allocation_v3.runner.collect','branch':'allocation_v3.runner.branch',
            'score':'allocation_v3.runner.score','policy-freeze':'documented_child.policies.freeze',
            'continuation':'allocation_v3.runner.continuation','policy-lock':'allocation_v3.runner.lock_policies',
            'policy-evaluation':'requires_child_dispatch_adapter_and_frozen_graph_smoke_ids'},
        'smoke_manifest_source':'sealed/graph.private.json; included IDs only',
        'execution_authorized':False,'wallet_active':False,'historical_spending':None,
        'remaining_budget':None,'evaluation_access':'requires_all_policies_checkpoints_analysis_lock'}


def require_execution_authority(contract):
    # No preflight or CPU report can authorize physical work. Fail closed even
    # if an imported record changes an authorization boolean.
    raise PermissionError('separate_reviewed_execution_integration_and_physical_allowance_required')


def run(seal, parent):
    receipt,training,method=verify_seal(seal)
    parent=Path(parent);freezing.no_symlinks(parent)
    source=evidence.executed_source(parent)  # Exact seven authoritative files.
    if source!=read_json(Path(seal)/'evidence/source.private.json'):
        raise ValueError('parent_source_changed')
    registry=read_json(parent/'checkpoint_inventory.private.json')
    lineage=read_json(parent/'training_lineage_map.json')
    for f in design.FAMILIES:
        expected=method['S0'][f]
        if registry['uniform_joint_sft/'+f]!=expected:raise ValueError('frozen_registry_conflict')
        entry=lineage['uniform_joint_sft/'+f]
        # The authoritative lineage map binds paths. tensor_inventory checks
        # contract/metadata structure against exact file and adapter identities.
        for name in (entry['contract'],entry['metadata']):
            if Path(name).is_absolute() or '..' in Path(name).parts:raise ValueError('unsafe_tensor_metadata_path')
            freezing.no_symlinks(parent/'evidence'/name)
    packages=package_check()
    tensors={}
    from .stage1.weights import tensor_inventory
    for f in design.FAMILIES:
        values,actual=tensor_inventory(parent,'uniform_joint_sft/'+f)
        tensors[f]=check_checkpoint_result(f,actual,method['S0'][f]);del values
    contract=execution_contract(receipt,training,method)
    public={'version':VERSION,'status':'CPU_CHECKPOINTS_VERIFIED_EXECUTION_DISABLED',
        'fixture':False,'child':review.CHILD,'freeze_receipt_sha256':RECEIPT_SHA,
        'freeze_manifest_sha256':MANIFEST_SHA,'candidate_digest':receipt['candidate_digest'],
        'graph_digest':receipt['graph_digest'],'training_dependency_hash':receipt['training_dependency_hash'],
        'current_S0_tensors_verified':True,'S0':tensors,'packages':packages,
        'execution_contract_digest':digest(contract),'gpu_runtime_checked':False,
        'effective_model_loading_checked':False,'native_tokenizer_context_checked':False,
        'remaining_prerequisites':['GPU_runtime_identity','native_access_and_context_limits',
            'effective_S0_loading','reviewed_child_dispatch_adapter','explicit_physical_spending_approval'],
        'execution_authorized':False,'wallet_active':False,'historical_spending':None,
        'remaining_budget':None,'model_calls':0,'synthetic_forwards':0,'training_forwards':0,'optimizer_updates':0}
    if not packages['matches']:public['remaining_prerequisites'].insert(0,'recorded_package_runtime_mismatch')
    return contract,public


def save(destination, contract, public):
    destination=Path(destination);freezing.no_symlinks(destination);review.sources.private_path(destination)
    if destination.exists():raise ValueError('new_preflight_destination_required')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent,prefix='.cpu-preflight-') as temp:
        stage=Path(temp)/'result';stage.mkdir(mode=0o700)
        checks={}
        for n,v in [('execution-contract.private.json',contract),('preflight.sanitized.json',public)]:
            raw=(canonical(v)+'\n').encode();p=stage/n
            with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
            checks[n]=hashlib.sha256(raw).hexdigest()
            if file_hash(p)!=checks[n]:raise ValueError('preflight_write_failed')
        (stage/'checksums.json').write_text(canonical(checks)+'\n')
        if destination.exists():raise ValueError('preflight_destination_collision')
        os.rename(stage,destination)
    return {**public,'receipt_sha256':checks['preflight.sanitized.json']}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seal',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        # This entry point is CPU-only, even if accidentally run on a GPU node.
        os.environ['CUDA_VISIBLE_DEVICES']=''
        contract,public=run(a.seal,Path(read_json(a.config)['parent_dir']))
        print(canonical(save(a.output,contract,public)));return 0
    except Exception as e:
        print(canonical({'status':'stopped','exception_type':type(e).__name__,'model_calls':0,
            'action':'preserve_evidence_and_return_sanitized_output'}));return 1

if __name__=='__main__':raise SystemExit(main())
