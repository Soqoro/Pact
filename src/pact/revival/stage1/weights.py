"""Inference-only reads of historical typed safetensors checkpoints."""
from pathlib import Path
import json
from dataclasses import asdict
from ...util import digest, read_json, file_hash, write_json
from ...training.checkpoints import decode_state
from ...studies.heterogeneity import immutable
from ...schemas import Message
from ...environment import runtime_fingerprint
from .. import neural, runtime, contracts as c
from .evidence import guard, SYNTHETIC, sha


def tensor_inventory(root, fit):
    import torch
    from safetensors import safe_open
    entry=read_json(root/'training_lineage_map.json')[fit]
    if not entry['tensor_path']:raise ValueError('Explicit tensor path required: '+fit)
    path=Path(entry['tensor_path'])
    if any(x.is_symlink() for x in (path,*path.parents)) or not path.is_file():raise ValueError('Missing/unsafe inference tensor file')
    actual=file_hash(path); expected=entry.get('expected_file_sha256')
    if expected is not None and actual!=sha(expected):raise ValueError('Historical tensor hash mismatch')
    contract=read_json(root/'evidence'/entry['contract']);meta=read_json(root/'evidence'/entry['metadata'])
    if meta['identity']!=contract or meta['step']!=128 or contract['lora']!=c.LORA:raise ValueError('Final contract mismatch')
    tree=dict(meta['tree']['dict'])['adapters'];refs=dict(tree['dict'])
    shapes=contract['identity']['shapes'];expected_shapes={}
    for name,(out_dim,in_dim) in shapes.items():
        expected_shapes[name+'.lora_A']=[c.LORA['r'],in_dim]
        expected_shapes[name+'.lora_B']=[out_dim,c.LORA['r']]
    if set(refs)!=set(expected_shapes):raise ValueError('Wrong adapter key set')
    values={}
    with safe_open(str(path),framework='pt',device='cpu') as stream:
        for name,ref in refs.items():
            if set(ref)!= {'tensor'} or ref['tensor'] not in stream.keys():raise ValueError('Missing inference tensor')
            v=stream.get_tensor(ref['tensor'])
            if v.dtype!=torch.float32 or list(v.shape)!=expected_shapes[name] or not torch.isfinite(v).all():raise ValueError('Nonfinite/dtype/shape mismatch')
            values[name]=v
        # Only availability is reported; optimizer/RNG are not deserialized.
        allkeys=set(stream.keys())
    content=neural._weights_hash(values)
    if content!=entry['expected_adapter_hash']:raise ValueError('Saved adapter content binding mismatch')
    def references(x):
        if isinstance(x,dict):
            if set(x)=={'tensor'}:return {x['tensor']}
            return set().union(*(references(v) for v in x.values()))
        if isinstance(x,list):return set().union(*(references(v) for v in x)) if x else set()
        return set()
    return values,{'fit':fit,'file_sha256':actual,'adapter_hash':content,'keys_shapes':expected_shapes,
        'structural_validity':True,'historical_tensor_verified':expected is not None,
        'historical_assurance':entry['assurance'],'new_content_fingerprint':content,
        'optimizer_recovery':{'all_referenced_tensors_present':references(meta['tree'])<=allkeys,'optimizer_metadata_present':'optimizer' in dict(meta['tree']['dict']),'recovery_validated':False},
        'initialization_comparison':{'historical_initial_hash':contract.get('initial'),'final_differs_from_initial_hash':content!=contract['initial'] if contract.get('initial') else None,'initial_tensor_bytes_verified':False},'saved_dtype':'float32'}


class Activation:
    """Native custom LoRA; explicit module replacement, never PEFT or merging."""
    def __init__(self,backend):
        self.backend=backend;self.model=backend.model;self.pristine=backend.identity.copy()
        self.originals=dict(neural.projections(self.model)) if getattr(backend,'key',backend.identity.get('spec',{}).get('key'))!='R' else {}
        self.versions={n:(id(p),p._version) for n,p in self.model.named_parameters()}
        self.active=None
        self.freeze()
    def freeze(self):
        self.model.eval()
        for p in self.model.parameters():p.requires_grad_(False)
    def base(self):
        for name,module in self.originals.items():
            owner,_,leaf=name.rpartition('.');setattr(self.model.get_submodule(owner) if owner else self.model,leaf,module)
        self.active=None;self.backend.identity=self.pristine.copy();self.freeze();self.check(None)
    def use(self,values,expected):
        self.base()
        if not self.originals:raise ValueError('Pristine readout cannot accept adapters')
        neural.attach(self.model);neural.restore_parameters(self.model,values)
        self.active=expected;self.freeze()
        self.adapter_versions={n:(id(p),p._version) for n,p in neural.parameters(self.model).items()}
        self.backend.identity={**self.pristine,'stage1_adapter_hash':expected,'lora':c.LORA}
        self.backend.identity['snapshot']=digest(self.backend.identity)
        self.check(expected)
    def check(self,expected,*,verify_content=True):
        import torch
        if self.active!=expected or self.model.training or any(p.requires_grad for p in self.model.parameters()):raise ValueError('Active state/eval/gradient mismatch')
        if any(isinstance(m,torch.nn.Dropout) and m.training for m in self.model.modules()):raise ValueError('Dropout active')
        ps=neural.parameters(self.model)
        if expected is None:
            if ps:raise ValueError('Pristine role contaminated')
        elif (not ps or any(p.dtype!=torch.float32 for p in ps.values())
              or {n:(id(p),p._version) for n,p in ps.items()}!=self.adapter_versions
              or (verify_content and neural._weights_hash(ps)!=expected)):raise ValueError('Effective loaded adapter values differ')
        # The underlying pristine parameter objects and version counters survive every switch.
        current={n.replace('.base.','.'):p for n,p in self.model.named_parameters() if n not in ps}
        if set(current)!=set(self.versions) or any((id(current[n]),current[n]._version)!=v for n,v in self.versions.items()):raise ValueError('Backbone changed during activation')


def backend(root,family,cache):
    return runtime.Backend(family,read_json(root/'evidence/access.json')[family],cache)


def verify(root,cache,factory=None,persist=lambda:None):
    r=guard(root)
    from . import amendment
    if r['version']==amendment.VERSION:raise ValueError('Inherited verification only; new synthetic forwards forbidden')
    if not r['fixture'] and (r['source_code']['dirty'] or not r['source_code']['git_commit']):raise ValueError('Reviewed clean pinned evaluation source required')
    if factory is not None and not r['fixture']:raise ValueError('No mock factory for real evidence')
    if (root/'checkpoint_verification_receipt.json').exists():raise ValueError('Verification already completed; no additional synthetic forwards')
    intents=root/'synthetic/intents';results=root/'synthetic/results'
    if list(intents.glob('*.json')):raise ValueError('Verification allowance already attempted; explicit recovery review required')
    rows={};values={};blockers=[]
    for fit in read_json(root/'training_lineage_map.json'):
        try:
            values[fit],rows[fit]=tensor_inventory(root,fit)
        except (ValueError,OSError,KeyError) as error:
            blockers.append({'fit':fit,'error_type':type(error).__name__,'reason':str(error)})
    if blockers:
        write_json(root/'checkpoint_inventory.private.json',{'valid':rows,'blockers':blockers})
        write_json(root/'checkpoint_verification_receipt.json',{'ready':False,'fixture':r['fixture'],'blockers':blockers,
            'synthetic_attempts':0,'generation_calls':0,'optimizer_updates':0})
        return read_json(root/'checkpoint_verification_receipt.json')
    immutable(root/'checkpoint_inventory.private.json',rows)
    actual_runtime=runtime_fingerprint();expected=read_json(root/'evidence/access.json')
    if not r['fixture'] and any(x['runtime_fingerprint']!=actual_runtime for x in expected.values()):raise ValueError('Exact recorded runtime required; no implicit migration')
    models={};attempt=0
    import torch
    for f in 'QLMR':
        b=factory(f) if factory else backend(root,f,cache)
        try:
            activation=Activation(b)
            messages=(Message('system','Sequence verification.'),Message('user',SYNTHETIC['text']))
            ids=b.tokenizer.encode(b.render_messages(messages),add_special_tokens=False)
            if not 0<len(ids)<=128:raise ValueError('Synthetic native input exceeds 128; no truncation')
            states=[None,c.ARMS[1],None,c.ARMS[2],None] if f!='R' else [None]
            baseline=None
            for index,arm in enumerate(states):
                if arm:
                    fit=arm+'/'+f
                    native=read_json(root/'training_lineage_map.json')[fit]['native']
                    if not r['fixture'] and activation.pristine!=native:raise ValueError('Native base/template differs from training contract')
                    activation.use(values[fit],rows[fit]['adapter_hash'])
                else:activation.base()
                if attempt>=16:raise ValueError('Synthetic allowance exhausted')
                attempt+=1
                intent={'number':attempt,'family':f,'state':arm,'input_tokens':len(ids),'input_hash':digest(ids),'policy':SYNTHETIC,'model':b.identity}
                immutable(intents/f'{attempt:02}.json',intent);persist()
                with torch.inference_mode():
                    x=torch.tensor([ids],device=next(b.model.parameters()).device)
                    logits=b.model(input_ids=x,attention_mask=torch.ones_like(x),use_cache=False).logits.detach().cpu()
                if not torch.isfinite(logits).all():raise ValueError('Nonfinite synthetic logits')
                if arm is None:
                    if baseline is None:baseline=logits
                    elif not torch.allclose(baseline,logits,atol=SYNTHETIC['atol'],rtol=SYNTHETIC['rtol']):raise ValueError('Restored base logits changed')
                activation.check(None if arm is None else rows[arm+'/'+f]['adapter_hash'])
                immutable(results/f'{attempt:02}.json',{'intent_hash':digest(intent),'finite':True,'base_restoration_checked':arm is None and index>0})
                persist()
            models[f]={'pristine_identity':activation.pristine,'resource_usage':b.resource_usage(),'active_after':None}
        finally:
            activation=None
            b.close()
    receipt={'ready':all(v['historical_tensor_verified'] for v in rows.values()),'fixture':r['fixture'],
        'inventory_hash':digest(rows),'models':models,'runtime_fingerprint':actual_runtime,
        'synthetic_attempts':attempt,'synthetic_completed':attempt,'generation_calls':0,'training_forwards':0,
        'teacher_forced_scoring_forwards':0,'optimizer_updates':0,'policy':SYNTHETIC,
        'training_runtime_fingerprint':expected['Q']['runtime_fingerprint'],
        'optimizer_recovery_validated':False,'evaluation_authorized_by_receipt':False}
    immutable(root/'checkpoint_verification_receipt.json',receipt)
    immutable(root/'inference_identity_manifest.json',{'models':models,'adapters':{k:v['adapter_hash'] for k,v in rows.items()}})
    return receipt
