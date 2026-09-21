"""Verified inference-only exports; never restore optimizer tensors for a probe."""
import copy
from pathlib import Path
import re
import shutil
import tempfile
from ..artifacts import safe_relative
from ..storage import storage_operation
from ..util import read_json,write_json,file_hash,digest,canonical

PRIOR_SOURCE={'git_commit':'ff349969996b2066979529b2f43d773f5a1b88e6','dirty':False,
              'source_hash':'6e0b6512f014c6f5cbda44de04b198a65c0e67b7a5f5254f69620c4812c4815a'}
MARKER='INFERENCE_ONLY.json'
SELECTED=('run.json','status.json','preparation_plan.json','references/references.json',
          'checkpoints/step-000090/state.json','checkpoints/step-000090/checksums.json',
          *(f'references/agent{i}/{name}' for i in range(3)
            for name in ('adapter_config.json','adapter_model.safetensors')))


def compatible_training_source(source,current):
    return source==current or source==PRIOR_SOURCE


def verify_inference_export(root):
    root=Path(root);proof=read_json(root/MARKER)
    index=root/'source_snapshot_index.json';completion=root/'source_snapshot_COMPLETE'
    if (proof.get('schema_version')!=1 or proof.get('kind')!='preparation_inference_only'
            or proof.get('index_sha256')!=file_hash(index)
            or completion.read_text()!=file_hash(index)):
        raise ValueError('Invalid inference-only source proof')
    inventory=read_json(index)
    if inventory.get('schema_version')!=1 or not 1<=len(inventory.get('files',{}))<=5000:
        raise ValueError('Invalid inference-only inventory')
    entries=inventory['files']
    for name in SELECTED:
        path=root/name
        if path.is_symlink() or not path.is_file() or file_hash(path)!=entries.get(name):
            raise ValueError('Changed inference-only payload: '+name)
    expected=set(SELECTED)|{MARKER,'source_snapshot_index.json','source_snapshot_COMPLETE'}
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=expected:raise ValueError('Unexpected inference-only files')
    meta=read_json(root/'run.json');status=read_json(root/'status.json')
    refs=read_json(root/'references/references.json');last=read_json(root/'checkpoints/step-000090/state.json')
    checks=read_json(root/'checkpoints/step-000090/checksums.json')
    if (set(checks)!={'state.json','tensors.safetensors'}
            or checks['state.json']!=entries['checkpoints/step-000090/state.json']
            or checks['tensors.safetensors']!=entries.get('checkpoints/step-000090/tensors.safetensors')
            or last.get('step')!=90 or last.get('identity')!=meta['identity']
            or refs.get('final_step')!=90 or refs.get('identity')!=meta['identity']
            or status.get('status')!='warmstart_updates_complete' or status.get('completed_steps')!=90
            or canonical(status.get('references'))!=canonical(refs)):
        raise ValueError('Inference export is not the completed 90-step reference set')
    return last


def _restore_preparation_references(snapshot,destination,*,progress=lambda message:None):
    snapshot=Path(snapshot);destination=Path(destination)
    if destination.exists():raise ValueError('Inference restore requires a new scratch destination')
    index=snapshot/'index.json';complete=snapshot/'COMPLETE'
    if snapshot.parent.name!='snapshots' or complete.read_text()!=file_hash(index):
        raise ValueError('Invalid source snapshot completion marker')
    inventory=read_json(index);entries=inventory.get('files',{})
    if inventory.get('schema_version')!=1 or not 1<=len(entries)<=5000:
        raise ValueError('Invalid source snapshot inventory')
    for name,sha in entries.items():
        safe_relative(name)
        if not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid source object hash')
    if not set(SELECTED)<=entries.keys():raise ValueError('Missing final preparation exports/metadata')
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix='.preparation-inference-',dir=destination.parent))
    try:
        size=0
        for i,name in enumerate(SELECTED,1):
            obj=snapshot.parent.parent/'objects'/entries[name]
            if obj.is_symlink() or not obj.is_file():raise ValueError('Missing/symlinked inference object')
            length=obj.stat().st_size;size+=length
            bound=128*1024**2 if name.endswith('.safetensors') else 8*1024**2
            if length>bound or size>512*1024**2:raise ValueError('Inference-only export size limit exceeded')
            target=staging/name;target.parent.mkdir(parents=True,exist_ok=True)
            progress(f'Restoring inference export {i}/{len(SELECTED)}: {name}')
            shutil.copyfile(obj,target)
            if file_hash(target)!=entries[name]:raise ValueError('Corrupt inference object')
        shutil.copyfile(index,staging/'source_snapshot_index.json')
        shutil.copyfile(complete,staging/'source_snapshot_COMPLETE')
        write_json(staging/MARKER,{'schema_version':1,'kind':'preparation_inference_only',
            'source_snapshot':str(snapshot),'index_sha256':file_hash(index),
            'copied_files':len(SELECTED),'copied_bytes':size,'optimizer_tensors_restored':False})
        verify_inference_export(staging)
        # Validate plan, source, final log and actual adapter/config hashes before publishing.
        from .preparation_runner import preparation_references
        preparation_references(read_json(staging/'preparation_plan.json'),staging)
        staging.rename(destination)
        return {'run_dir':str(destination),'source_snapshot':str(snapshot),'copied_files':len(SELECTED),
                'copied_bytes':size,'inference_only':True,'optimizer_tensors_restored':False}
    finally:
        if staging.exists():shutil.rmtree(staging)


def restore_preparation_references(snapshot,destination,*,timeout_seconds=600):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    return storage_operation('preparation-references-restore',Path(snapshot),destination,timeout_seconds=timeout_seconds)


def compatible_probe_resume(old,recipe):
    """One explicit storage-only source migration; scientific recipe/call IDs stay fixed."""
    if (old['recipe_hash']!=digest(old['recipe']) or old.get('identity',{}).get('recipe_hash')!=old['recipe_hash']):
        raise ValueError('Probe recipe identity is inconsistent')
    if old['recipe_hash']==digest(recipe):return old,None
    previous=old['recipe']
    if previous.get('source')!=PRIOR_SOURCE or {k:v for k,v in previous.items() if k!='source'}!={k:v for k,v in recipe.items() if k!='source'}:
        raise ValueError('Probe source/recipe mismatch; only pinned storage repair migration is supported')
    migrated=copy.deepcopy(old)
    migrated['recipe']=recipe;migrated['recipe_hash']=digest(recipe)
    migrated['identity']['recipe_hash']=digest(recipe)
    return migrated,{'kind':'storage_only_source_migration','from':previous['source'],'to':recipe['source'],
                     'previous_recipe_hash':old['recipe_hash'],'recipe_hash':digest(recipe),
                     'committed_calls':old['committed_calls'],'no_call_budget_reset':True}
