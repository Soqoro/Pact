"""Artifact-bound amended continuation; never resume or alter the unsafe parent."""
import argparse
import hashlib
import json
import shutil
import tempfile
import time
import zipfile
from pathlib import Path

from ..artifacts import safe_relative, run_lock
from ..environment import runtime_fingerprint
from ..training.checkpoints import read_checkpoint, decode_state
from ..util import canonical, digest, file_hash, read_json, write_json
from . import contracts as c, neural, replacement, runtime, study
from .retention import POLICY

RUN = 'pact-heterogeneous-receiver-training-continuation-003'
VERSION = 'revival_amended_continuation_v1'
FORENSIC_SHA = 'bb9d759af00b2ee7942ad25236bced0b6ebf95cbdaccf2f582a22586148d9015'
PARENT_PLAN = '0cd17021ec0b11865e2ddb5b761e086b88650d356c870494d86ec78c1d689f55'
SNAPSHOT = '1792486927348121446-eefe02888431'
JOINT = 'uniform_joint_sft'
BASELINES = {'independent_adversarial_sft/Q':128, 'independent_adversarial_sft/L':128,
             'independent_adversarial_sft/M':128, 'uniform_joint_sft/Q':93}
AMENDMENT = {'version':VERSION, 'parent_plan_hash':PARENT_PLAN, 'forensic_sha256':FORENSIC_SHA,
             'new_committed_updates':291, 'new_training_forwards_max':6984,
             'generation_calls':0, 'evaluation_calls':0,
             'unknown_parent_step':{'arm':JOINT, 'family':'Q', 'step':94},
             'unknown_step_forwards_max':24, 'unknown_step_optimizer_updates_max':1,
             'inherited_committed_updates':477, 'combined_committed_path_updates':768,
             'combined_physical_optimizer_updates_max':769,
             'original_pre_replacement_history_remains_separate':True}
REVIEW_HASH = digest(AMENDMENT)


def forensic(bundle):
    """Verify all members before selecting evidence; do not execute archive content."""
    if file_hash(bundle) != FORENSIC_SHA:raise ValueError('Exact forensic archive required')
    with zipfile.ZipFile(bundle) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or len(names)>500 or sum(i.file_size for i in z.infolist())>1024**3:
            raise ValueError('Forensic archive bounds/duplicates')
        for i in z.infolist():
            safe_relative(i.filename)
            if (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Archive symlink')
        manifest=json.loads(z.read('FORENSIC_MANIFEST.json'))
        if set(names)!=set(manifest['files'])|{'FORENSIC_MANIFEST.json'}:raise ValueError('Forensic inventory')
        for name,record in manifest['files'].items():
            h=hashlib.sha256();size=0
            with z.open(name) as f:
                for b in iter(lambda:f.read(8*1024**2),b''):h.update(b);size+=len(b)
            if h.hexdigest()!=record['sha256'] or size!=record['bytes']:raise ValueError('Forensic member mismatch')
        prefix=f'snapshots/{SNAPSHOT}/'
        raw=z.read(prefix+'index.json')
        if hashlib.sha256(raw).hexdigest()!=z.read(prefix+'COMPLETE').decode().strip():raise ValueError('Snapshot index mismatch')
        files=json.loads(raw)['files']
        def obj(name):
            value=z.read('objects/'+files[name])
            if hashlib.sha256(value).hexdigest()!=files[name]:raise ValueError('Object identity mismatch')
            return json.loads(value)
        receipt=obj('recovery.json');parent=obj('run/plan.json')
        if (digest(parent)!=PARENT_PLAN or receipt['plan_hash']!=PARENT_PLAN or receipt['recovery_safe']
                or files!={**receipt['files'],'recovery.json':files['recovery.json']}):
            raise ValueError('Exact unsafe parent evidence required')
        intent=obj(f'run/training/{JOINT}/Q/update_attempt.json')
        if intent['step']!=94:raise ValueError('Unexpected parent intent')
        return parent, files


def prepare(parent_bundle, evidence, root, review_hash):
    if review_hash!=REVIEW_HASH:raise ValueError('Exact amended accounting review hash required')
    if root.exists():raise ValueError('Absent continuation root required')
    parent, files=forensic(evidence)
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent,prefix='.continuation-') as tmp:
        stage=Path(tmp)/'child'
        # Existing importer independently verifies the fixed bank and original
        # initialized actors from the exact pre-main-training PRIVATE bundle.
        replacement.import_parent(parent_bundle,stage,replacement.REVIEW_SHA)
        replacement.validate_inherited(stage,parent)
        write_json(stage/'parent_replacement_plan.json',parent)
        lineage=stage/'lineage';lineage.mkdir()
        shutil.copyfile(evidence,Path(tmp)/'verified-forensic.zip')
        if file_hash(Path(tmp)/'verified-forensic.zip')!=FORENSIC_SHA:raise ValueError('Forensic changed during import')
        with zipfile.ZipFile(Path(tmp)/'verified-forensic.zip') as z:
            for fit,step in BASELINES.items():
                base=f'run/training/{fit}/';ck=base+f'checkpoints/step-{step:06d}/'
                selected=[base+'contract.json',base+'status.json']+[ck+n for n in ('state.json','checksums.json','tensors.safetensors')]
                for name in selected:
                    dest=stage/safe_relative(name[4:]);dest.parent.mkdir(parents=True,exist_ok=True)
                    with z.open('objects/'+files[name]) as src,dest.open('wb') as out:shutil.copyfileobj(src,out)
                    if file_hash(dest)!=files[name]:raise ValueError('Selected checkpoint copy mismatch')
                folder=stage/'training'/fit
                meta=read_checkpoint(folder/f'checkpoints/step-{step:06d}',read_json(folder/'contract.json'))
                if meta['step']!=step or read_json(folder/'status.json')['completed_steps']!=step:raise ValueError('Checkpoint/status mismatch')
            # Retain the original unresolved intent as evidence, not an active
            # intent in the new branch. No old file is rewritten or removed.
            pending=z.read('objects/'+files[f'run/training/{JOINT}/Q/update_attempt.json'])
            (lineage/'parent_step94_intent.json').write_bytes(pending)
            (lineage/'joint_Q_inherited_status.json').write_bytes(z.read('objects/'+files[f'run/training/{JOINT}/Q/status.json']))
            for name in ('SNAPSHOT_PENDING.json','FORENSIC_MANIFEST.json'):
                (lineage/name).write_bytes(z.read(name))
        inherited={p.relative_to(stage).as_posix():file_hash(p) for fit in BASELINES
                   for p in (stage/'training'/fit).rglob('*') if p.is_file()}
        bindings={p.relative_to(stage).as_posix():file_hash(p) for p in lineage.iterdir()}
        write_json(stage/'plan.json',{'version':VERSION,'run_id':RUN,'source':parent['source'],
            'source_code':replacement.source_identity(),'parent_plan_hash':PARENT_PLAN,
            'parent_plan_sha256':file_hash(stage/'parent_replacement_plan.json'),
            'amendment':AMENDMENT,'review_hash':REVIEW_HASH,'storage_retention':POLICY,
            'inherited_files':inherited,'lineage_files':bindings})
        validate(stage)
        report(stage)
        stage.rename(root)
    return report(root)


def validate(root, plan_hash=None, check_source=False):
    p=read_json(root/'plan.json')
    if (p['version']!=VERSION or p['run_id']!=RUN or p['amendment']!=AMENDMENT
            or p['review_hash']!=REVIEW_HASH or p['storage_retention']!=POLICY or p['parent_plan_hash']!=PARENT_PLAN):raise ValueError('Continuation contract mismatch')
    if plan_hash is not None and digest(p)!=plan_hash:raise ValueError('Continuation plan hash mismatch')
    if check_source and p['source_code']!=replacement.source_identity():raise ValueError('Pinned continuation source changed')
    parent=read_json(root/'parent_replacement_plan.json')
    if (digest(parent)!=PARENT_PLAN or file_hash(root/'parent_replacement_plan.json')!=p['parent_plan_sha256']
            or p['source']!=parent['source']):raise ValueError('Parent lineage mismatch')
    replacement.validate_inherited(root,parent)
    for name,h in p['lineage_files'].items():
        if file_hash(root/safe_relative(name))!=h:raise ValueError('Lineage evidence changed')
    # Completed independent fits are immutable; Q's imported step-93 may later
    # be pruned by the existing explicit retention policy, but never overwritten.
    for name,h in p['inherited_files'].items():
        path=root/safe_relative(name)
        if name.startswith(f'training/{JOINT}/Q/'):
            if name.endswith('status.json'):continue
            if not path.exists() and name.endswith('tensors.safetensors'):continue
        if path.is_symlink() or file_hash(path)!=h:raise ValueError('Inherited checkpoint changed')
    return p


def preflight(root,cache,factory=None):
    p=validate(root,check_source=True)
    if factory is not None and not p['source']['fixture']:raise ValueError('No mock real continuation')
    access=read_json(root/'access.json');out=replacement.capacity(root);out['families']={}
    for f in c.FAMILIES:
        if access[f]['runtime_fingerprint']!=runtime_fingerprint():raise ValueError('Original runtime required')
        backend=factory(f) if factory else runtime.Backend(f,access[f],cache)
        try:
            neural.attach(backend.model,c.SEED+c.FAMILIES.index(f))
            replacement.verify_initial(root,f,backend)
            if f=='Q':
                folder=root/'training'/JOINT/f
                neural.load(folder/'checkpoints',read_json(folder/'contract.json'),backend.model)
                if neural._weights_hash(neural.parameters(backend.model))!=read_json(folder/'status.json')['adapter_hash']:
                    raise ValueError('Restored Q adapter identity mismatch')
            out['families'][f]={'native_identity_verified':True,'initial_identity_verified':True}
        finally:backend.close()
    out.update(plan_hash=digest(p),runtime_fingerprint=runtime_fingerprint(),generation_calls=0,training_forwards=0)
    write_json(root/'continuation_preflight.json',out)
    return out


def report(root):
    p=validate(root);statuses={};new=0;forwards=0
    for arm in c.ARMS[1:]:
        for f in c.FAMILIES:
            fit=f'{arm}/{f}';folder=root/'training'/fit;status=folder/'status.json'
            if not status.exists():continue
            s=read_json(status);steps=sorted((folder/'checkpoints').glob('step-*'))
            meta=read_checkpoint(steps[-1],read_json(folder/'contract.json'))
            if meta['step']!=s['completed_steps'] or not BASELINES.get(fit,0)<=meta['step']<=128:raise ValueError('Progress inconsistent')
            if s['complete'] != (meta['step']==s['planned_steps']) or (not p['source']['fixture'] and s['planned_steps']!=128):
                raise ValueError('Completion status or schedule mismatch')
            checkpoint_logs=dict(meta['tree']['dict'])['logs']
            if (decode_state(checkpoint_logs,{})!=s['logs']
                    or len(s['logs'])!=meta['step']
                    or [x['step'] for x in s['logs']]!=list(range(1,meta['step']+1))
                    or s['forwards']!=sum(x['supervised_forwards'] for x in s['logs'])):
                raise ValueError('Training logs or forward accounting differ from checkpoint')
            statuses[fit]={k:s[k] for k in ('complete','completed_steps','planned_steps','forwards')}
            if arm==JOINT:
                new+=meta['step']-BASELINES.get(fit,0)
                base_forwards=0
                if f=='Q':
                    # Inherited log entries remain unchanged; exclude them from new work.
                    inherited=read_json(root/'lineage/joint_Q_inherited_status.json')
                    if s['logs'][:BASELINES[f'{JOINT}/Q']]!=inherited['logs']:raise ValueError('Inherited Q logs changed')
                    base_forwards=inherited['forwards']
                forwards+=s['forwards']-base_forwards
    if new>291 or forwards>6984:raise ValueError('Continuation budget exceeded')
    unresolved=[]
    for f in c.FAMILIES:
        fit=f'{JOINT}/{f}';intent=root/'training'/fit/'update_attempt.json'
        if intent.exists() and read_json(intent)['step']>statuses.get(fit,{}).get('completed_steps',0):
            unresolved.append({'family':f,'step':read_json(intent)['step']})
    out={'run_id':RUN,'plan_hash':digest(p),'scientific_status':'mock_only' if p['source']['fixture'] else 'amended_training_continuation_no_evaluation',
         'new_work':{'committed_updates':new,'training_forwards':forwards,'generation_calls':0,
                     'forward_accounting':'committed updates only; interrupted-attempt forwards unknown',
                     'unresolved_optimizer_attempts':unresolved},
         'inherited_committed_updates':477,'combined_committed_updates':477+new,
         'unknown_parent_update':AMENDMENT['unknown_parent_step'],
         'unknown_parent_step_execution':'unresolved; not counted as zero',
         'amended_budget':AMENDMENT,
         'prior_original_history':read_json(root/'parent_replacement_plan.json')['historical_accounting'],
         'training':statuses,'recovery_safe':runtime.recovery_safe(root),
         'training_complete':len(statuses)==6 and all(x['complete'] for x in statuses.values()),
         'full_pact_executed':False,'efficacy_established':False}
    write_json(root/'summary.json',out);return out


def train(root,plan_hash,cache,family,*,resume=False,stop_after=None,persistent=None,factory=None):
    p=validate(root,plan_hash,check_source=True)
    if family not in c.FAMILIES:raise ValueError('Only joint Q/L/M allowed')
    if stop_after is not None and not 1<=stop_after<=128:raise ValueError('Invalid stop boundary')
    if factory is not None and not p['source']['fixture']:raise ValueError('No mock real continuation')
    pre=read_json(root/'continuation_preflight.json')
    if pre['plan_hash']!=digest(p) or pre['runtime_fingerprint']!=runtime_fingerprint():raise ValueError('Exact continuation preflight required')
    if not runtime.recovery_safe(root):raise ValueError('Unresolved new attempt; no retry')
    report(root)
    backend=factory(family) if factory else runtime.Backend(family,read_json(root/'access.json')[family],cache)
    try:
        shapes=neural.attach(backend.model,c.SEED+c.FAMILIES.index(family))
        replacement.verify_initial(root,family,backend)
        if hasattr(backend.model,'gradient_checkpointing_enable'):
            backend.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        gs=study.groups_for(root,p,backend,family,JOINT)
        identity={'plan':PARENT_PLAN,'family':family,'arm':JOINT,'native':backend.identity,'shapes':shapes}
        # Explicit inherited identity keeps the exact checkpoint contract; the
        # new outer plan separately binds amended accounting and current code.
        return neural.train(backend.model,gs,root/'training'/JOINT/family,identity,
            resume=resume,stop_after=stop_after,
            boundary_callback=lambda phase,step:runtime.checkpoint(root,persistent,
                boundary={'phase':phase,'step':step,'arm':JOINT,'family':family}))
    finally:backend.close()


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('stage',choices=['review','prepare','inspect','preflight','repair-tokenizer-cache','train-agent','report','export','restore'])
    ap.add_argument('--run-dir',type=Path);ap.add_argument('--persistent',type=Path)
    ap.add_argument('--parent-private',type=Path);ap.add_argument('--forensic',type=Path)
    ap.add_argument('--review-hash');ap.add_argument('--plan-hash');ap.add_argument('--cache-dir',type=Path)
    ap.add_argument('--family',choices=list(c.FAMILIES));ap.add_argument('--resume',action='store_true')
    ap.add_argument('--execute',action='store_true');ap.add_argument('--stop-after',type=int)
    a=ap.parse_args(argv)
    if a.stage=='review':print(canonical({'amendment':AMENDMENT,'review_hash':REVIEW_HASH}));return
    root=a.run_dir
    if root is None or root.name!=RUN or (a.persistent is not None and a.persistent.name!=RUN):raise ValueError('Separate continuation directory required')
    if a.stage=='prepare':
        if a.persistent is not None and a.persistent.exists() and any(a.persistent.iterdir()):raise ValueError('Existing child history; restore only')
        out=prepare(a.parent_private,a.forensic,root,a.review_hash);runtime.checkpoint(root,a.persistent)
    elif a.stage=='restore':
        if a.persistent is None:raise ValueError('Persistent child required')
        runtime.restore_latest(a.persistent,root);out=report(root)
    else:
        validate(root,a.plan_hash,check_source=True)
        with run_lock(root):
            if a.persistent is not None and (a.persistent/'SNAPSHOT_PENDING.json').exists():raise ValueError('Pending transaction; no retry')
            if a.stage in ('preflight','repair-tokenizer-cache','train-agent'):
                if not a.execute or not a.plan_hash:raise ValueError('Explicit execution and frozen plan hash required')
                if a.stage=='repair-tokenizer-cache':
                    from .mistral_cache import repair
                    out=repair(a.cache_dir)
                elif a.stage=='preflight':out=preflight(root,a.cache_dir)
                else:out=train(root,a.plan_hash,a.cache_dir,a.family,resume=a.resume,stop_after=a.stop_after,persistent=a.persistent)
                runtime.checkpoint(root,a.persistent)
            elif a.stage in ('inspect','report'):out=report(root)
            else:
                report(root);runtime.checkpoint(root,a.persistent);out={}
                for kind in ('PRIVATE','SANITIZED','RECOVERY'):
                    path=root.parent/'bundles'/f'{RUN}-{kind}-{time.time_ns()}.zip'
                    out[kind]=runtime.package(root,path,weights=kind=='RECOVERY',sanitized=kind=='SANITIZED')
                    if a.persistent:
                        from ..storage import persist_bundle
                        dest=a.persistent/'bundles'/path.name
                        persist_bundle(path,dest,out[kind]['sha256'],timeout_seconds=600)
                        out[kind]['persistent_path']=str(dest)
    print(canonical(out))

if __name__=='__main__':main()
