"""Private evidence exports and latest-only child persistence; parents are read-only."""
from pathlib import Path
import shutil
import tempfile
import time
import zipfile
from ...util import file_hash,read_json,write_json,canonical,digest
from ...artifacts import safe_relative, artifact_files
from ...storage import storage_operation,persist_bundle
from ...studies.heterogeneity import immutable
from . import evidence, amendment


def safety(root):
    generation={p.stem for p in (root/'intents').glob('*.json')}=={p.stem for p in (root/'calls/shards').glob('*.sha256')}
    synthetic={p.stem for p in (root/'synthetic/intents').glob('*.json')}=={p.stem for p in (root/'synthetic/results').glob('*.json')}
    return generation and synthetic


def persist(root,destination):
    if destination is None:return
    resolution=read_json(root/'contract_resolution.json')
    if not resolution['fixture'] and destination.name!=amendment.run_id(root):raise ValueError('Wrong persistence owner')
    marker=destination/'SNAPSHOT_PENDING.json'
    inflight=destination/'INFLIGHT.json'
    if inflight.exists():
        expected=set(read_json(inflight)['attempts'])
        local={p.stem for p in (root/'intents').glob('*.json')}
        if not expected<=local:raise ValueError('Durable attempts absent from scratch; preserve marker')
    if marker.exists():raise ValueError('Pending child snapshot; no retry')
    write_json(marker,{'run_id':amendment.run_id(root),'resolution_hash':digest(read_json(root/'contract_resolution.json'))})
    write_json(root/'recovery.json',{'run_id':amendment.run_id(root),'recovery_safe':safety(root),'resolution_hash':digest(read_json(root/'contract_resolution.json'))})
    compact_snapshot(root,destination)
    marker.unlink()
    if safety(root):(destination/'INFLIGHT.json').unlink(missing_ok=True)


COMPACT_FORMAT = 'stage1_compact_snapshot_v1'


def compact_snapshot(root,destination):
    """Build on scratch; existing worker verifies only two durable objects."""
    with tempfile.TemporaryDirectory(dir=root.parent, prefix='.stage1-pack-') as tmp:
        transport=Path(tmp)
        checks={}
        print('Packing Stage I snapshot on scratch...',flush=True)
        with zipfile.ZipFile(transport/'state.zip','w',zipfile.ZIP_DEFLATED) as z:
            for f in artifact_files(root):
                if f.suffix=='.safetensors':raise ValueError('Weights must stay external')
                n=f.relative_to(root).as_posix()
                if n in ('HANDOFF.json','checksums.json'):raise ValueError('Reserved snapshot member')
                checks[n]=file_hash(f);z.write(f,n)
            z.writestr('checksums.json',canonical(checks))
            z.writestr('HANDOFF.json',canonical({'kind':'PRIVATE','format':COMPACT_FORMAT}))
        # Check the packed bytes locally before attempting persistence.
        z,_=evidence.archive(transport/'state.zip');z.close()
        receipt={'format':COMPACT_FORMAT,'sha256':file_hash(transport/'state.zip'),
                 'recovery_safe':safety(root),
                 'resolution_hash':digest(read_json(root/'contract_resolution.json'))}
        write_json(transport/'receipt.json',receipt)
        print(f'Persisting compact snapshot: {len(checks)} files in two objects',flush=True)
        return storage_operation('snapshot',transport,destination,timeout_seconds=600)


def restore_compact(obj,root):
    receipt=read_json(obj('receipt.json'))
    if receipt.get('format')!=COMPACT_FORMAT or receipt.get('recovery_safe') is not True:
        raise ValueError('Unsafe/unknown compact snapshot')
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent,prefix='.stage1-unpack-') as tmp:
        local=Path(tmp)/'state.zip'
        shutil.copyfile(obj('state.zip'),local)
        z,checks=evidence.archive(local,receipt['sha256'])
        try:
            resolution=__import__('json').loads(z.read('contract_resolution.json'))
            if digest(resolution)!=receipt['resolution_hash']:raise ValueError('Resolution mismatch')
            from ...studies.forensics import private_root
            stage=Path(tmp)/'run';private_root(stage,resolution['fixture'])
            for n in checks:
                target=stage/safe_relative(n);target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(n) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
            if not safety(stage) or not read_json(stage/'recovery.json')['recovery_safe']:
                raise ValueError('Unresolved dispatch in packed state')
            evidence.guard(stage)
            stage.rename(root)
        finally:z.close()


def restore(destination,root):
    if root.exists():raise ValueError('Absent local destination required')
    if (destination/'SNAPSHOT_PENDING.json').exists() or (destination/'INFLIGHT.json').exists():raise ValueError('Pending persistence/dispatch; no fallback')
    snaps=sorted((destination/'snapshots').glob('*'))
    if not snaps:raise ValueError('No child snapshot')
    snap=snaps[-1]
    if not (snap/'COMPLETE').exists() or (snap/'COMPLETE').read_text().strip()!=file_hash(snap/'index.json'):raise ValueError('Latest snapshot incomplete')
    idx=read_json(snap/'index.json')['files']
    def obj(n):
        h=evidence.sha(idx[n]);p=destination/'objects'/h
        if p.is_symlink() or file_hash(p)!=h:raise ValueError('Snapshot object missing/corrupt')
        return p
    if set(idx)=={'state.zip','receipt.json'}:
        restore_compact(obj,root)
        return {'restored':True,'snapshot':snap.name,'tensors_restored':False,'format':COMPACT_FORMAT}
    if not read_json(obj('recovery.json'))['recovery_safe']:raise ValueError('Unresolved dispatch; no restore')
    resolution=read_json(obj('contract_resolution.json'))
    from ...studies.forensics import private_root
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent) as tmp:
        stage=Path(tmp)/'run';private_root(stage,resolution['fixture'])
        for n in idx:
            target=stage/safe_relative(n);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(obj(n),target)
        if not safety(stage):raise ValueError('Receipt contradicts saved attempts')
        stage.rename(root)
    return {'restored':True,'snapshot':snap.name,'tensors_restored':False}


def export(root,stage,destination=None):
    if stage not in ('inspect','verify','freeze','smoke','validation','source_evaluation','fixed_history'):raise ValueError('Unknown export stage')
    if stage in ('smoke','validation','source_evaluation','fixed_history') and not (root/'stages'/f'{stage}.json').exists():raise ValueError('Stage incomplete; use inspect export to preserve partial evidence')
    from .metrics import report
    if (root/'plan.json').exists():report(root)
    # Sanitized allowlist excludes IDs, prompts, labels, tokens and private paths.
    public=('summary.json','paired_metrics.json','peer_access_interaction.json','runtime_and_cost_report.json')
    out={}
    for kind in ('PRIVATE','SANITIZED'):
        path=root.parent/'bundles'/f'{amendment.run_id(root)}-{kind}-{time.time_ns()}.zip';path.parent.mkdir(exist_ok=True)
        checks={}
        with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
            for f in sorted(root.rglob('*')):
                if f.is_symlink():raise ValueError('Export symlink')
                if not f.is_file() or f.name=='.lock':continue
                n=f.relative_to(root).as_posix()
                if f.suffix=='.safetensors':raise ValueError('Weights must stay outside child run')
                if kind=='SANITIZED' and n not in public:continue
                checks[n]=file_hash(f);z.write(f,n)
            meta={'version':evidence.VERSION,'kind':kind,'stage':stage,'recovery_safe':safety(root),
                  'synthetic_attempts':len(list((root/'synthetic/intents').glob('*.json'))),
                  'verification_ready':read_json(root/'checkpoint_verification_receipt.json')['ready'] if (root/'checkpoint_verification_receipt.json').exists() else False}
            if amendment.is_amended(root):meta.update(run_id=amendment.RUN,amendment_hash=amendment.PROPOSAL_HASH)
            z.writestr('HANDOFF.json',canonical(meta));z.writestr('checksums.json',canonical(checks))
        out[kind]={'path':str(path),'sha256':file_hash(path),'bytes':path.stat().st_size}
        if destination:out[kind]['persistent']=persist_bundle(path,destination/'bundles'/path.name,out[kind]['sha256'],timeout_seconds=600)
    receipt_path=root/'exports'/f'{stage}.json' if stage!='inspect' else root/'export_reviews'/f'{time.time_ns()}.json'
    immutable(receipt_path,{'stage':stage,'complete_at_export':safety(root)})
    persist(root,destination);return out


def map_recovery(bundle,expected,review_bundle,destination):
    """Copy six exact final tensor files only; caller supplies archive and destination."""
    from ...studies.forensics import private_root
    if destination.exists():raise ValueError('Absent tensor destination required')
    z,checks=evidence.archive(bundle,expected);review,rchecks=evidence.archive(review_bundle,evidence.PRIVATE)
    try:
        if z.read('plan.json')!=review.read('plan.json'):raise ValueError('Recovery plan mismatch')
        private_root(destination)
        mapping={}
        from ..contracts import ARMS,FAMILIES
        for arm in ARMS[1:]:
            for f in FAMILIES:
                prefix=f'training/{arm}/{f}/checkpoints/step-000128/'
                for n in ('state.json','checksums.json'):
                    if z.read(prefix+n)!=review.read(prefix+n):raise ValueError('Recovery metadata mismatch')
                name=prefix+'tensors.safetensors';inv=__import__('json').loads(review.read(prefix+'checksums.json'))
                if checks[name]!=inv['tensors.safetensors']:raise ValueError('Recovery tensors differ from review receipt')
                target=destination/arm/f/'tensors.safetensors';target.parent.mkdir(parents=True)
                with z.open(name) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
                if file_hash(target)!=checks[name]:raise ValueError('Tensor copy mismatch')
                mapping[arm+'/'+f]=str(target.absolute())
        write_json(destination/'checkpoint-map.json',mapping)
        return {'checkpoint_map':str(destination/'checkpoint-map.json'),'recovery_sha256':expected,'optimizer_restored':False}
    finally:z.close();review.close()


def audit(bundle,root):
    """Reconstruct using installed trusted readers, never execute bundle code."""
    if root.exists():raise ValueError('Absent audit copy required')
    z,checks=evidence.archive(bundle)
    try:
        resolution=__import__('json').loads(z.read('contract_resolution.json'))
        from ...studies.forensics import private_root
        private_root(root,resolution['fixture'])
        for n in checks:
            if not (n.endswith(('.json','.jsonl','.sha256'))):continue
            target=root/safe_relative(n);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
        if (root/'plan.json').exists():
            from .engine import Journal
            from .metrics import report
            p=read_json(root/'plan.json');Journal(root,p)
            previous=read_json(root/'summary.json');actual=report(root)
            if digest(previous)!=digest(actual):raise ValueError('Reconstructed summary differs')
            return {'verified':True,'new_calls':0,'generation_accounting':actual['accounting']}
        return {'verified':True,'new_calls':0,'evaluation_not_started':True}
    finally:z.close()


class BatchedPersistence:
    """At most32 pending call IDs: durable intent per dispatch, periodic verified snapshot.

    A lost scratch batch is explicitly unsafe; its durable ID list reserves all
    ambiguous attempts. Never clear this marker except after a verified safe sync.
    """
    def __init__(self,root,destination):
        self.root=root;self.destination=destination;self.pending={}
        self.known={p.stem for p in (root/'intents').glob('*.json')}
        if destination and ((destination/'INFLIGHT.json').exists() or (destination/'SNAPSHOT_PENDING.json').exists()):raise ValueError('Unresolved durable work; no retry')
    def __call__(self):
        if self.destination is None:return
        for p in (self.root/'intents').glob('*.json'):
            if p.stem not in self.known:
                v=read_json(p);self.pending[p.stem]={'component':v['component'],'plan_hash':v['plan_hash']};self.known.add(p.stem)
        if not self.pending:return
        if len(self.pending)>32:raise ValueError('Pending batch bound exceeded')
        marker={'run_id':amendment.run_id(self.root),'attempts':self.pending,'reserved_output_tokens':512*len(self.pending)}
        path=self.destination/'INFLIGHT.json';write_json(path,marker)
        if read_json(path)!=marker:raise ValueError('Durable dispatch marker verification failed')
        if len(self.pending)==32 and safety(self.root):
            persist(self.root,self.destination);self.pending={}
