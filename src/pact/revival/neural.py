"""Native answer-prefix masks and audited FP32 LoRA updates; lazy torch imports."""
import json
import math
from pathlib import Path
from ..util import digest,read_json,write_json,file_hash
from ..training.checkpoints import encode_state,decode_state,commit_checkpoint,latest_checkpoint,read_checkpoint
from ..training.warmstart import _rng_state,_restore_rng,_weights_hash
from ..training.receiver_supervision import torch_answer_ce
from .contracts import LORA,OPT,SEED


def prefix_target(tokenizer,prompt,answer,allowed,limit=8192):
    if answer not in allowed or not answer:raise ValueError('Official answer outside allowed options')
    prefix='{"answer":'+json.dumps(answer,ensure_ascii=True)
    text=prompt+prefix;start=len(prompt)+len('{"answer":"');end=len(text)-1
    ids=list(tokenizer.encode(text,add_special_tokens=False));pids=list(tokenizer.encode(prompt,add_special_tokens=False))
    if not pids or ids[:len(pids)]!=pids or len(ids)>limit:raise ValueError('Native prefix/context boundary incompatibility')
    try:
        enc=tokenizer(text,add_special_tokens=False,return_offsets_mapping=True)
        offsets=[tuple(x) for x in enc['offset_mapping']]
        if list(enc['input_ids'])!=ids or len(offsets)!=len(ids):raise ValueError('Offset identity')
    except (NotImplementedError,TypeError):
        # Slow tokenizers: use cumulative exact decoding, reject nonmonotone or lossy boundaries.
        decoded=[tokenizer.decode(ids[:i],skip_special_tokens=False,clean_up_tokenization_spaces=False) for i in range(len(ids)+1)]
        if decoded[-1]!=text or any(not b.startswith(a) for a,b in zip(decoded,decoded[1:])):raise ValueError('Ambiguous slow-tokenizer offsets')
        offsets=[(len(a),len(b)) for a,b in zip(decoded,decoded[1:])]
    mask=[int(a<end and b>start) for a,b in offsets]
    covered=set()
    for i,((a,b),m) in enumerate(zip(offsets,mask)):
        if not 0<=a<=b<=len(text):raise ValueError('Invalid native offsets')
        if m:
            if i<=len(pids)-1 or a<len(prompt):raise ValueError('Gold target overlaps input')
            covered.update(range(max(a,start),min(b,end)))
    if covered!=set(range(start,end)) or not any(mask) or mask[0]:raise ValueError('Incomplete answer coverage')
    eos=tokenizer.eos_token_id
    if eos in ids[len(pids):]:raise ValueError('No EOS on incomplete answer prefix')
    return {'version':'native_answer_prefix_v1','input_ids':ids,'score_mask':mask,'output_prefix':prefix,
            'offsets':offsets,'answer_span':[start,end],'prompt_hash':digest(prompt),'eos_supervised':False}


def projections(model):
    import torch
    paths=[(n,m) for n,m in model.named_modules() if n.split('.')[-1] in LORA['targets']]
    if not paths or set(n.split('.')[-1] for n,_ in paths)!=set(LORA['targets']) or any(not isinstance(m,torch.nn.Linear) for _,m in paths):raise ValueError('Native projection modules missing/unsupported')
    return paths


def attach(model,seed=SEED):
    """A*B standard LoRA: FP32 activations/parameters on delta path, cast delta to base output dtype."""
    import torch
    from torch import nn
    class LoRALinear(nn.Module):
        def __init__(self,base):
            super().__init__();self.base=base
            self.lora_A=nn.Parameter(torch.empty(LORA['r'],base.in_features,device=base.weight.device,dtype=torch.float32))
            self.lora_B=nn.Parameter(torch.zeros(base.out_features,LORA['r'],device=base.weight.device,dtype=torch.float32))
            nn.init.kaiming_uniform_(self.lora_A,a=math.sqrt(5));self.dropout=nn.Dropout(LORA['dropout'])
        def forward(self,x):
            y=self.base(x)
            delta=torch.nn.functional.linear(torch.nn.functional.linear(self.dropout(x.float()),self.lora_A),self.lora_B)
            return y+(delta*(LORA['alpha']/LORA['r'])).to(y.dtype)
    for p in model.parameters():p.requires_grad_(False)
    paths=projections(model)
    devices=[0] if next(model.parameters()).device.type=='cuda' else []
    with torch.random.fork_rng(devices=devices):
        torch.manual_seed(seed)
        for n,m in paths:
            owner,_,name=n.rpartition('.');setattr(model.get_submodule(owner) if owner else model,name,LoRALinear(m))
    return {n:list(m.weight.shape) for n,m in paths}


def parameters(model):return {n:p for n,p in model.named_parameters() if n.endswith(('lora_A','lora_B'))}


def restore_parameters(model,values):
    import torch
    ps=parameters(model)
    if set(ps)!=set(values):raise ValueError('Adapter shape/name mismatch')
    with torch.no_grad():
        for n,p in ps.items():
            v=values[n]
            if p.dtype!=torch.float32 or v.dtype!=torch.float32 or v.shape!=p.shape or not torch.isfinite(v).all():raise ValueError('Adapter precision/shape/nonfinite mismatch')
            p.copy_(v)
    if _weights_hash(ps)!=_weights_hash(values):raise ValueError('Adapter round trip changed effective values')


def loss(model,target):
    import torch
    ids=torch.tensor([target['input_ids']],device=next(model.parameters()).device)
    mask=torch.tensor([target['score_mask']],device=ids.device)
    return torch_answer_ce(model(input_ids=ids,attention_mask=torch.ones_like(ids),use_cache=False).logits,ids,torch.ones_like(ids),mask)[0]


def save(root,identity,step,model,optimizer,logs):
    import torch
    from safetensors.torch import save_file
    state={'adapters':{n:p.detach().cpu().clone() for n,p in parameters(model).items()},'optimizer':optimizer.state_dict(),
           'rng':_rng_state(),'logs':logs,'scheduler':{'completed_steps':step},'sampler_position':step}
    tree,ts=encode_state(state,torch.is_tensor)
    return commit_checkpoint(root,step=step,identity=identity,tree=tree,write_tensors=lambda p:save_file({k:v.detach().cpu().contiguous().clone() for k,v in ts.items()},str(p)))


def load(root,identity,model,optimizer=None):
    from safetensors.torch import load_file
    paths=sorted(root.glob('step-*'));path=paths[-1]
    meta=read_checkpoint(path,identity)
    state=decode_state(meta['tree'],load_file(str(path/'tensors.safetensors')))
    restore_parameters(model,state['adapters'])
    if optimizer is not None:optimizer.load_state_dict(state['optimizer']);_restore_rng(state['rng'])
    return meta['step'],state


def train(model,groups,root,identity,*,epochs=2,batch=8,warmup=8,resume=False,stop_after=None,callback=lambda:None):
    """Each group contains already GLOBAL coefficients. N/batch converts to unbiased minibatch loss."""
    import torch
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    schedule=[]
    for epoch in range(epochs):
        order=sorted(range(len(groups)),key=lambda i:digest([SEED,epoch,groups[i]['task_id']]))
        schedule.extend({'epoch':epoch+1,'indices':order[j:j+batch]} for j in range(0,len(order),batch))
    contract={'identity':identity,'groups_hash':digest(groups),'schedule':schedule,'initial':_weights_hash(parameters(model)), 'lora':LORA,'optimizer':OPT,'warmup':warmup}
    if (root/'contract.json').exists():
        if not resume or read_json(root/'contract.json')!=contract:raise ValueError('Explicit compatible resume required')
    else:write_json(root/'contract.json',contract)
    ps=parameters(model)
    if not ps or any(p.dtype!=torch.float32 for p in ps.values()):raise ValueError('FP32 adapters required')
    for n,p in model.named_parameters():p.requires_grad_(n in ps)
    model.train();optimizer=torch.optim.AdamW(list(ps.values()),lr=OPT['lr'],betas=tuple(OPT['betas']),eps=OPT['eps'],weight_decay=0.,foreach=False)
    step=0;logs=[]
    if resume:
        step,state=load(root/'checkpoints',contract,model,optimizer);logs=state['logs']
    else:
        torch.manual_seed(SEED);save(root/'checkpoints',contract,0,model,optimizer,[])
    intent=root/'update_attempt.json'
    if intent.exists() and read_json(intent)['step']>step:raise ValueError('Unresolved optimizer attempt; no automatic retry')
    frozen=[(p,p._version) for n,p in model.named_parameters() if n not in ps]
    for entry in schedule[step:]:
        if stop_after is not None and step>=stop_after:break
        write_json(intent,{'step':step+1,'contract_hash':digest(contract)})
        callback()  # Persist the unsafe intent before optimizer execution.
        optimizer.zero_grad(set_to_none=True);total=0.;forwards=0
        for i in entry['indices']:
            for e in groups[i]['contexts']:
                v=loss(model,e['target'])
                if not torch.isfinite(v):raise ValueError('Nonfinite supervised loss')
                weighted=v*e['weight']*len(groups)/len(entry['indices'])
                weighted.backward();total+=float(weighted.detach());forwards+=1
        grads=[p.grad for p in ps.values() if p.grad is not None]
        if not grads or any(not torch.isfinite(g).all() for g in grads):raise ValueError('Missing/nonfinite adapter gradient')
        norm=float(torch.nn.utils.clip_grad_norm_(list(ps.values()),OPT['clip']))
        if not math.isfinite(norm) or norm<=0:raise ValueError('Nonfinite/zero adapter gradient')
        if any(p.grad is not None or p._version!=v for p,v in frozen):raise ValueError('Frozen backbone mutated')
        optimizer.param_groups[0]['lr']=OPT['lr']*min(1.,(step+1)/warmup) if warmup else OPT['lr']
        optimizer.step();step+=1
        for state in optimizer.state.values():
            for key in ('exp_avg','exp_avg_sq'):
                if key in state and state[key].dtype!=torch.float32:raise ValueError('Optimizer lost FP32 state')
        logs.append({'step':step,'epoch':entry['epoch'],'loss':total,'gradient_norm':norm,'supervised_forwards':forwards,'lr':optimizer.param_groups[0]['lr']})
        save(root/'checkpoints',contract,step,model,optimizer,logs)
        if step==len(schedule) or schedule[step]['epoch']!=entry['epoch']:
            write_json(root/f"epoch{entry['epoch']}.json",{'step':step,'adapter_hash':_weights_hash(ps),'contract':contract})
        write_json(root/'status.json',{'complete':step==len(schedule),'completed_steps':step,'planned_steps':len(schedule),'forwards':sum(x['supervised_forwards'] for x in logs),'adapter_hash':_weights_hash(ps),'logs':logs})
        callback();print(f'Training {identity.get("family")} {step}/{len(schedule)} loss={total:.5f}',flush=True)
    optimizer.zero_grad(set_to_none=True);model.eval()
    return read_json(root/'status.json')
