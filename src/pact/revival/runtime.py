"""One native resident model, immutable dispatch accounting, recoverable private ZIPs."""
from dataclasses import asdict,replace
from pathlib import Path
import json
import zipfile
import time
import hashlib
from ..util import read_json,write_json,digest,file_hash,canonical
from ..artifacts import ShardStore,safe_relative
from ..backends.native import NativeBackend,metadata
from ..config import Limits
from ..environment import code_identity
from . import contracts as c


def preflight(root,cache):
    from ..studies.heterogeneity import immutable
    receipts={k:metadata(k,cache) for k in 'QLMR'}
    immutable(root/'access.json',receipts)
    return {'all_models_authorized':True,'weights_verified_on_load':False}


class Backend(NativeBackend):
    def __init__(self,key,receipt,cache,checkpoint=None):
        super().__init__(key,receipt,cache)
        try:
            from . import neural
            shapes={n:list(m.weight.shape) for n,m in neural.projections(self.model)} if key!='R' else {}
            self.identity={**self.identity,'native_projection_shapes':shapes}
            self.config.limits=replace(self.config.limits,context=8192)
            self.identity={**self.identity,'revival_profile':{'context':8192,'output':512,'packet_contract':c.VERSION}}
            self.identity['snapshot']=digest(self.identity)
            if checkpoint is not None:
                from . import neural
                if key=='R':raise ValueError('Readout must remain pristine')
                neural.attach(self.model, c.SEED+'QLM'.index(key))
                contract=read_json(checkpoint/'contract.json');neural.load(checkpoint/'checkpoints',contract,self.model)
                actual=neural._weights_hash(neural.parameters(self.model))
                if actual!=read_json(checkpoint/'status.json')['adapter_hash']:raise ValueError('Effective adapter identity differs from committed status')
                self.identity={**self.identity,'adapter_hash':actual,'lora':c.LORA}
                self.identity['snapshot']=digest(self.identity)
        except BaseException:
            self.close()
            raise
    def generation_parameters(self,request):return {**super().generation_parameters(request),'max_new_tokens':512}


class Journal:
    def __init__(self,root,stage='I',allow_incomplete=False):
        self.root=Path(root);self.stage=stage
        self.store=ShardStore(self.root/'calls');self.plan=read_json(self.root/'plan.json')
        self.hash=digest(self.plan);self.allow_incomplete=allow_incomplete;self.inspect()
    def inspect(self):
        self.intents={p.stem:read_json(p) for p in (self.root/'intents').glob('*.json')}
        self.results={r['work_id']:r for r in self.store.records()}
        for key,r in self.results.items():
            if key not in self.intents or r['intent']!=self.intents[key] or digest(r['intent']['identity'])!=key:raise ValueError('Journal identity mismatch')
            identity=r['intent']['identity'];req=identity['request'];call=r['call'];tokens=r['tokens']
            if identity['plan_hash']!=self.hash or call['seed']!=req['seed'] or call['messages']!=req['messages'] or call['snapshot']!=identity['model']['snapshot'] or call['phase']!=req['phase']:raise ValueError('Call provenance mismatch')
            if call['context_hash']!=digest(call['rendered_prompt']) or tokens['raw']!=r['raw'] or tokens['context_hash']!=call['context_hash']:raise ValueError('Rendered/token provenance mismatch')
            if call['input_tokens']!=len(tokens['prompt_ids']) or call['output_tokens']!=len(tokens['completion_ids']) or call['input_tokens']+512>8192 or call['output_tokens']>512:raise ValueError('Native token budget mismatch')
            if r['packet']!=c.parse(r['raw'],req['task'],call['stop_reason']):raise ValueError('Packet parse mismatch')
        if set(self.intents)-set(self.results) and not self.allow_incomplete:raise ValueError('Unresolved dispatch; do not retry or use an older snapshot')
        for stage in ('I','II'):
            n=sum(i['identity']['budget_stage']==stage for i in self.intents.values())
            if n>c.BUDGETS[stage]['generation']:raise ValueError('Generation budget exceeded')
    def request(self,backend,req,logical,persistent=None):
        if self.plan.get('version')=='revival_replacement_training_v1':raise ValueError('Replacement generation is not authorized')
        identity={'plan_hash':self.hash,'budget_stage':self.stage,'model':backend.identity,'request':asdict(req),'logical':logical}
        key=digest(identity)
        if key in self.results:return self.results[key]
        n=sum(i['identity']['budget_stage']==self.stage for i in self.intents.values())
        if n>=c.BUDGETS[self.stage]['generation'] or req.max_tokens!=512:raise ValueError('Generation budget exhausted')
        rendered=backend.render_messages(req.messages)
        if backend.count_tokens(rendered)+512>8192:raise ValueError('Context incompatibility; no task dropping')
        intent={'identity':json.loads(canonical(identity)),'work_id':key}
        write_json(self.root/'intents'/f'{key}.json',intent);self.intents[key]=intent
        if persistent is not None:
            marker={'plan_hash':self.hash,'work_id':key,'kind':'generation'}
            write_json(persistent/'INFLIGHT.json',marker)
            if read_json(persistent/'INFLIGHT.json')!=marker:raise ValueError('Durable dispatch marker failed')
        raw,call=backend.generate(req)
        if call.input_tokens+512>8192 or call.output_tokens>512 or call.snapshot!=backend.identity['snapshot']:raise ValueError('Call contract mismatch')
        result={'schema_version':1,'work_id':key,'intent':intent,'raw':raw,'call':asdict(call),'tokens':backend.last_generation,
                'packet':c.parse(raw,asdict(req.task),call.stop_reason)}
        self.store.put(key,result);self.results[key]=result
        print(f'{self.stage} generation {n+1}/{c.BUDGETS[self.stage]["generation"]}',flush=True)
        return result


def recovery_files(root):
    """One selection contract for file snapshots and explicit recovery exports."""
    for f in sorted(root.rglob('*')):
        if f.is_symlink():raise ValueError('Symlink in run')
        if not f.is_file() or f.name=='.lock' or 'bundles' in f.relative_to(root).parts:continue
        if f.suffix=='.safetensors':
            base=f.parent.parent;keep={sorted(base.glob('step-*'))[-1].name,'step-000000'}
            for ep in base.parent.glob('epoch*.json'):keep.add(f"step-{read_json(ep)['step']:06d}")
            if f.parent.name not in keep:continue
        yield f


def package(root,path,*,weights=False,sanitized=False):
    """Streaming explicit exports; routine snapshots do not create recovery ZIPs."""
    path.parent.mkdir(parents=True,exist_ok=True);checks={}
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for f in recovery_files(root):
            rel=f.relative_to(root).as_posix()
            if sanitized and rel not in ('summary.json','probe_summary.json','reviewed_stage_i_summary.json'):continue
            if not weights and f.suffix=='.safetensors':continue
            checks[rel]=file_hash(f);z.write(f,rel)
        meta={'kind':'sanitized' if sanitized else 'recovery' if weights else 'private_review','version':c.VERSION}
        z.writestr('HANDOFF.json',canonical(meta));z.writestr('checksums.json',canonical(checks))
    return {'path':str(path),'sha256':file_hash(path),'bytes':path.stat().st_size}


def unpack(bundle,sha,root):
    if root.exists() or file_hash(bundle)!=sha:raise ValueError('Absent destination and exact archive hash required')
    with zipfile.ZipFile(bundle) as z:
        if len(z.infolist())>150000 or sum(x.file_size for x in z.infolist())>32*1024**3:raise ValueError('Archive bound')
        names=z.namelist()
        if len(set(names))!=len(names):raise ValueError('Duplicate archive names')
        for i in z.infolist():
            safe_relative(i.filename)
            if (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Symlink')
        meta=json.loads(z.read('HANDOFF.json'));checks=json.loads(z.read('checksums.json'))
        if meta!={'kind':'recovery','version':c.VERSION} or set(names)!=set(checks)|{'HANDOFF.json','checksums.json'}:raise ValueError('Full recovery bundle required')
        for name,expected in checks.items():
            h=hashlib.sha256()
            with z.open(name) as src:
                while data:=src.read(1024**2):h.update(data)
            if h.hexdigest()!=expected:raise ValueError('Archive member checksum')
        from ..studies.forensics import private_root
        restored_plan=json.loads(z.read('plan.json'))
        private_root(root,restored_plan['source']['fixture'])
        for name in checks:
            out=root/name;out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(name) as src,out.open('wb') as dst:
                import shutil
                shutil.copyfileobj(src,dst)
    Journal(root)


def recovery_safe(root):
    """An optimizer intent is as binding as a generation or scoring intent."""
    safe={p.stem for p in (root/'intents').glob('*.json')}=={p.stem for p in (root/'calls/shards').glob('*.sha256')}
    safe &= {p.stem for p in (root/'score_intents').glob('*.json')}=={p.stem for p in (root/'probe_scores/shards').glob('*.sha256')}
    for p in root.rglob('update_attempt.json'):
        steps=sorted((p.parent/'checkpoints').glob('step-*'))
        if steps:
            from ..training.checkpoints import read_checkpoint
            meta=read_checkpoint(steps[-1],read_json(p.parent/'contract.json'))
            safe &= meta['step']>=read_json(p)['step']
        else:safe=False
    return bool(safe)


def checkpoint(root,persistent):
    if persistent is None:return
    from ..storage import storage_operation
    # Worker writes a durable pending marker before any snapshot mutation. Failure
    # or deadline leaves it in place, including a failed post-optimizer snapshot.
    storage_operation('revival-snapshot',root,persistent,timeout_seconds=600)
    from .retention import prune_scratch
    prune_scratch(root)


def restore_latest(persistent,root):
    """No older snapshot fallback; unfinished durable dispatch stays unsafe."""
    if (persistent/'SNAPSHOT_PENDING.json').exists():raise ValueError('Unfinished snapshot; no older fallback')
    if (persistent/'INFLIGHT.json').exists():raise ValueError('Latest durable dispatch unresolved; forensic export required, no older fallback')
    snaps=sorted((persistent/'snapshots').glob('*'))
    if not snaps:raise ValueError('No durable snapshot')
    latest=snaps[-1];idx=read_json(latest/'index.json')
    if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json') :raise ValueError('Invalid latest snapshot')
    def obj(name):
        h=idx['files'][name]
        if len(h)!=64 or any(x not in '0123456789abcdef' for x in h):raise ValueError('Bad object identifier')
        path=persistent/'objects'/h
        if path.is_symlink() or file_hash(path)!=h:raise ValueError('Corrupt snapshot object')
        return path
    if 'recovery.json' in idx['files']:
        from .persistence import restore_files
        return restore_files(persistent,root,idx,obj)
    if set(idx['files'])!={'receipt.json','state.zip'}:raise ValueError('Invalid legacy snapshot')
    receipt=read_json(obj('receipt.json'))
    if not receipt['recovery_safe'] or receipt['sha256']!=idx['files']['state.zip']:raise ValueError('Latest snapshot unsafe')
    unpack(obj('state.zip'),receipt['sha256'],root)
    if digest(read_json(root/'plan.json'))!=receipt['plan_hash']:raise ValueError('Recovered plan differs')
