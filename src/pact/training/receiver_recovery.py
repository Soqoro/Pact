"""Explicit evaluation-only compatibility for the audited 27889da controlled run.

Preserves the legacy loader and ALL saved tensors. No training or acquisition is
permitted through this transition. Actual loaded actors must match the certified
step-zero/final tensor states before any evaluation call.
"""
from pathlib import Path
from ..util import canonical, digest, file_hash, read_json, write_json
from .warmstart import _weights_hash

REVIEW_SHA = 'ce9f97aca8a24e7a15b890d5e557c3da7af8331f944847b8d4036feb152ae993'
STUDY = 'a858f1b22d2188b0b7be166c81d774f02a211f6cc77170e23149624a7ded99e8'
PRIOR_SOURCE = {'dirty':False,'git_commit':'27889da90d2afce934fffb1baac9acb64ec3a1e2',
                'source_hash':'bc17a6935b801d554c8fc52c7af59e07aafb1d92114b1ac8f6ff83129ee21bdb'}
POLICY = 'controlled_001_effective_initialization_v1'
ARMS = ('task_sft','receiver_sft')
RECEIPT = 'evaluation_recovery.json'


def equal_tensors(left, right, context):
    import torch
    if left.keys()!=right.keys():raise ValueError(context+': tensor keys differ')
    for key in left:
        a,b=left[key],right[key]
        if (a.dtype!=torch.float32 or b.dtype!=torch.float32 or a.shape!=b.shape
            or not torch.isfinite(a).all() or not torch.isfinite(b).all() or not torch.equal(a,b)):
            raise ValueError(context+': tensor differs: '+key)


def actor_view(parameters, agent):
    """Checkpoint named parameters -> PEFT export keys, without value conversion."""
    result={}
    for name,value in parameters.items():
        for side in ('A','B'):
            marker=f'.lora_{side}.agent{agent}.'
            if marker in name:
                key=name.replace(marker,f'.lora_{side}.')
                if key in result:raise ValueError('Duplicate actor tensor')
                result[key]=value
    if not result:raise ValueError('Missing checkpoint actor')
    return result


def certify(original, initial_states, final_states, exports):
    """Exact CPU proof: focal starts exact; nonfocal starts rounded and never moves."""
    import torch
    effective={i:{k:(v.clone() if i==0 else v.to(torch.bfloat16).float()) for k,v in original[i].items()} for i in range(3)}
    hashes={};initial_hashes={}
    for arm in ARMS:
        initial_hashes[arm]=_weights_hash(initial_states[arm])
        hashes[arm]=[]
        for i in range(3):
            equal_tensors(actor_view(initial_states[arm],i),effective[i],f'{arm}/initial/agent{i}')
            final=actor_view(final_states[arm],i)
            equal_tensors(final,exports[arm][i],f'{arm}/final/export/agent{i}')
            if i:equal_tensors(final,effective[i],f'{arm}/nonfocal/agent{i}')
            hashes[arm].append(_weights_hash(final))
    if len(set(initial_hashes.values()))!=1:raise ValueError('Arms have different effective initialization')
    return {'policy':POLICY,'original_tensor_hashes':[_weights_hash(original[i]) for i in range(3)],
        'effective_tensor_hashes':{'frozen':[_weights_hash(effective[i]) for i in range(3)],**hashes},
        'initial_weight_hash':initial_hashes[ARMS[0]],
        'focal_initialization':'exact_original_fp32',
        'nonfocal_initialization':'original_fp32_to_bf16_to_fp32; identical across arms',
        'nonfocal_optimizer_changes':False,'tensor_rewrites':False,'new_training_updates':0}


def check_transition(root, plan, source, stage, review):
    if stage not in ('evaluate','report','export'):raise ValueError('Effective initialization recovery is evaluation/report/export ONLY')
    state=read_json(root/'state.json');recipe=read_json(root/'recipe.json')
    if (state['study_hash']!=STUDY or digest(recipe)!=STUDY or recipe['source']!=PRIOR_SOURCE
        or canonical(recipe['plan'])!=canonical(plan) or canonical(review['plan.json'])!=canonical(plan)
        or review['state.json']['study_hash']!=STUDY or review['recipe.json']!=recipe):
        raise ValueError('Recovery is restricted to the audited controlled-001 study')
    path=root/RECEIPT
    if path.exists():
        receipt=read_json(path)
        if receipt.get('implementation_source')!=source or receipt.get('policy')!=POLICY or receipt.get('review_sha256')!=REVIEW_SHA:
            raise ValueError('Recovery implementation/receipt changed; no automatic transition')
    elif any((root/'evaluation').rglob('*.json')):
        raise ValueError('Recovery requires no prior evaluation evidence on first activation')


def prepare(root, plan, source, stage, review_path, initial_root):
    """Verify retained metadata and actual step-zero/final tensors, then add a receipt."""
    import torch
    from safetensors.torch import load_file
    from .receiver_study import read_receiver_supervision_review, initial_recipe
    from .checkpoints import read_checkpoint, decode_state
    root=Path(root);initial_root=Path(initial_root)
    review=read_receiver_supervision_review(review_path,REVIEW_SHA)
    check_transition(root,plan,source,stage,review)
    initial=initial_recipe(plan,initial_root)  # verifies original tensor/config files
    inventory=review['HANDOFF.json']['inventory']
    protected={'plan.json','recipe.json','contexts.json','target_masks.json','training_schedule.json','donor_review.json'}
    def selected(name):return name in protected or name.startswith(('training/','donors/'))
    # Metadata and exported adapters must remain byte-identical to the reviewed run.
    # Intermediate optimizer tensors are not used by evaluation; step 0/24 are checked below.
    for name,entry in inventory.items():
        if not selected(name):continue
        if '/checkpoints/' in name and name.endswith('tensors.safetensors') and not any(f'/step-{s:06d}/' in name for s in (0,24)):continue
        path=root/name
        if path.is_symlink() or not path.is_file() or file_hash(path)!=entry['sha256']:
            raise ValueError('Recovery artifact differs from reviewed bytes: '+name)
    # Do not allow extra source attempts or optimizer steps to appear after the audit.
    for prefix in ('training','donors'):
        extra={p.relative_to(root).as_posix() for p in (root/prefix).rglob('*') if p.is_file() and not any(x.startswith('.') for x in p.relative_to(root).parts)}-inventory.keys()
        if extra:raise ValueError('Unexpected recovery artifacts: '+str(sorted(extra)[:3]))
    original={i:load_file(str(initial_root/'references'/f'agent{i}'/'adapter_model.safetensors'),device='cpu') for i in range(3)}
    starts={};ends={};exports={};reference_hashes={}
    for arm in ARMS:
        stage_root=root/'training'/arm;run=read_json(stage_root/'run.json');status=read_json(stage_root/'status.json')
        if not status['complete'] or status['completed_steps']!=24 or status['planned_steps']!=24 or not status['training_executed']:
            raise ValueError('Recovery requires the completed 24-update arms')
        if status['references']!=read_json(stage_root/'references/references.json'):raise ValueError('Reference status mismatch')
        for step,destination in ((0,starts),(24,ends)):
            checkpoint=stage_root/'checkpoints'/f'step-{step:06d}'
            meta=read_checkpoint(checkpoint,run['identity'])
            state=decode_state(meta['tree'],load_file(str(checkpoint/'tensors.safetensors'),device='cpu'))
            destination[arm]=state['adapters']
        if _weights_hash(starts[arm])!=run['initial_weight_hash'] or run['initial_weight_hash']!=status['initial_weight_hash']:
            raise ValueError('Initial checkpoint/hash mismatch')
        if _weights_hash(ends[arm])!=status['final_weight_hash']:raise ValueError('Final checkpoint/hash mismatch')
        exports[arm]={i:load_file(str(stage_root/'references'/f'agent{i}'/'adapter_model.safetensors'),device='cpu') for i in range(3)}
        for i in range(3):
            if read_json(stage_root/'references'/f'agent{i}'/'adapter_config.json')!=read_json(initial_root/'references'/f'agent{i}'/'adapter_config.json'):
                raise ValueError('Adapter configuration changed')
        reference_hashes[arm]=[r['sha256'] for r in status['references']['references']]
    # Small CPU tensors; avoid oversubscribed thread pools on Colab.
    threads=torch.get_num_threads()
    try:
        torch.set_num_threads(1)
        proof=certify(original,starts,ends,exports)
    finally:torch.set_num_threads(threads)
    receipt={**proof,'schema_version':1,'study_hash':STUDY,'review_sha256':REVIEW_SHA,
        'prior_source':PRIOR_SOURCE,'implementation_source':source,
        'original_reference_hashes':list(initial.reference_hashes),'reference_hashes':reference_hashes,
        'claim':'Compatibility with the effective initialization actually used; not exact preservation of all original export values.'}
    path=root/RECEIPT
    if path.exists() and read_json(path)!=receipt:raise ValueError('Recovery proof changed')
    if not path.exists():write_json(path,receipt)
    print('Verified effective initialization; completed training and all tensor files retained.',flush=True)
    return receipt


def permits_nonfocal(receipt, arm, i, initial_hash, exported_hash):
    return (receipt is not None and receipt.get('policy')==POLICY and i in (1,2)
            and receipt['original_reference_hashes'][i]==initial_hash
            and receipt['reference_hashes'][arm][i]==exported_hash)


def verify_loaded(backend, arm, receipt):
    """No post-load correction: reject any model that differs from certified states."""
    from peft import get_peft_model_state_dict
    actual=[_weights_hash(get_peft_model_state_dict(backend.model,adapter_name=f'agent{i}')) for i in range(3)]
    if actual!=receipt['effective_tensor_hashes'][arm]:raise ValueError('Actual loaded actors differ from certified effective checkpoint')
    backend.assert_unchanged()
    advertised=backend.identity['snapshot']
    backend.identity={**backend.identity,'export_snapshot':advertised,'effective_initialization_policy':POLICY,
        'effective_actor_tensor_hashes':actual,'recovery_receipt_hash':digest(receipt),
        'snapshot':digest({'base':backend.base_identity['snapshot'],'effective_actors':actual,'policy':POLICY})}
    print('Verified actual loaded actor tensors:',arm,flush=True)
