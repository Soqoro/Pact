"""Sequential three-adapter optimization of one globally reduced frozen objective."""
from pathlib import Path
import random
import time

from ..util import digest,read_json,write_json,canonical
from .warmstart import adapter_parameters,training_adapter,_weights_hash,_save_step,_load_step,_restore_rng,export_references
from .losses import torch_completion_logps,answer_target
from .assignment_contrast import ARMS
from .specialization_collect import immutable


def sequence(score):
    prompt=list(score['prompt_ids']);target=list(score['completion_ids'])
    if not prompt or not target or len(prompt)+len(target)>4096:raise ValueError('Training context overflow or missing tokens')
    return {'input_ids':prompt+target,'attention_mask':[1]*(len(prompt)+len(target)),
            'completion_mask':[0]*len(prompt)+[1]*len(target)}


def examples_for(records,assignments,arm,tokenizer):
    if arm not in ARMS or assignments['status']!='ready':raise ValueError('Supported contrasted bank required; no base-only fallback')
    coefficients=assignments['coefficients'][arm];examples=[]
    for b,r in enumerate(records):
        cells=[]
        for i in range(3):
            score=r['answer_scores'][i]
            if score['adapter']!=f'agent{i}' or score['completion']!=answer_target(r['row']['gold']):raise ValueError('Base target changed')
            def validate(s,prompt):
                if (list(tokenizer.encode(prompt,add_special_tokens=False))!=s['prompt_ids'] or s['completion_ids'][-1]!=tokenizer.eos_token_id
                    or tokenizer.eos_token_id in s['completion_ids'][:-1] or tokenizer.decode(s['completion_ids'][:-1],skip_special_tokens=True)!=s['completion']):
                    raise ValueError('Training token/prompt/EOS mismatch')
            validate(score,r['trajectory']['private'][i]['call']['rendered_prompt'])
            pair=r['replays'][i];packet=None
            if pair['status']=='eligible':
                p=pair['candidates'][pair['positive_index']]
                ps=next(s for s in r['packet_scores'] if s['agent']==i)
                if ps['completion']!=p['raw'] or ps['pair_id']!=pair['pair_id']:raise ValueError('Positive target provenance mismatch')
                validate(ps,p['call']['rendered_prompt']);packet=sequence(ps)
            cells.append({'base':sequence(score),'packet':packet,'base_coefficient':coefficients['base'][b][i],
                          'packet_coefficient':coefficients['specialization'][b][i]})
        examples.append({'row_id':r['work_id'],'task_id':r['row']['task_id'],'cells':cells})
    return examples


def schedule(examples,seed):
    if len(examples)!=64:raise ValueError('Exactly64 fitting rows required')
    batches=[]
    for epoch in range(2):
        order=sorted(range(64),key=lambda i:digest([seed,epoch,examples[i]['row_id']]))
        for j in range(0,64,4):batches.append({'epoch':epoch,'indices':order[j:j+4],'scale':16.})
    return [{'agent':agent,'actor_step':j+1,**batch} for agent in range(3) for j,batch in enumerate(batches)]


def training_audit(examples,seed):
    sched=schedule(examples,seed)
    result={'optimizer_updates':96,'updates_per_actor':32,'scheduler':'none; constant LR',
        'reduction':'L=sum(baseNLL)/(3U)+sum(omega*R*packetNLL)/B; update=sum4rows(global coefficients)*U/4',
        'U':64,'lambda_spec':1.,'actor_specialization_mass':[sum(r['cells'][i]['packet_coefficient'] for r in examples) for i in range(3)],
        'base_forwards':0,'packet_forwards':0,'base_target_tokens':0,'packet_target_tokens':0,
        'base_prompt_tokens':0,'packet_prompt_tokens':0,'base_sequence_tokens':0,'packet_sequence_tokens':0,
        'exposure_scope':'full planned schedule','example_presentations':384}
    for batch in sched:
        for j in batch['indices']:
            cell=examples[j]['cells'][batch['agent']]
            for role in ('base','packet'):
                if cell[role] is not None:
                    result[role+'_forwards']+=1;result[role+'_target_tokens']+=sum(cell[role]['completion_mask'])
                    result[role+'_sequence_tokens']+=sum(cell[role]['attention_mask'])
                    result[role+'_prompt_tokens']+=sum(cell[role]['attention_mask'])-sum(cell[role]['completion_mask'])
    return result


def token_nll(model,sequence):
    import torch
    device=next(model.parameters()).device
    ids=torch.tensor([sequence['input_ids']],device=device);attention=torch.tensor([sequence['attention_mask']],device=device)
    mask=torch.tensor([sequence['completion_mask']],device=device)
    sums,counts=torch_completion_logps(model(input_ids=ids,attention_mask=attention,use_cache=False).logits,ids,attention,mask)
    return -sums[0]/counts[0]


def backward_rows(model,examples,batch,actor):
    """Production microbatch accumulator; coefficients retain global bank units."""
    import torch
    parts=[]
    for j in batch['indices']:
        cell=examples[j]['cells'][actor];item={'row_id':examples[j]['row_id']}
        for role in ('base','packet'):
            if cell[role] is None:continue
            value=token_nll(model,cell[role]);weight=cell[role+'_coefficient']*batch['scale']
            if not torch.isfinite(value):raise ValueError('Nonfinite training loss')
            # Preserve forward/token exposure even for a numerical zero R.
            if weight:(value*weight).backward()
            item[role+'_nll']=float(value.detach());item[role+'_weight']=weight
            item[role+'_target_tokens']=sum(cell[role]['completion_mask'])
            item[role+'_sequence_tokens']=sum(cell[role]['attention_mask'])
        parts.append(item)
    return parts


def train_team(model,examples,plan,root,identity,*,resume=False,stop_after=None,before_update=lambda:None,after_update=lambda:None):
    import torch
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    parameters=adapter_parameters(model)
    if any(p.dtype!=torch.float32 for p in parameters.values()):raise ValueError('Exact effective FP32 actor values required')
    schedule_rows=schedule(examples,plan['seed'])
    contract={'identity':identity,'examples_hash':digest(examples),'schedule':schedule_rows,
              'initial_weight_hash':_weights_hash(parameters),'settings':plan['settings']}
    if (root/'run.json').exists():
        if not resume or read_json(root/'run.json')!=contract:raise ValueError('Incompatible or unrequested training resume')
    else:
        if resume:raise ValueError('No training checkpoint to resume')
        immutable(root/'run.json',contract);immutable(root/'examples.json',examples)
    if (root/'status.json').exists() and read_json(root/'status.json').get('complete'):
        return read_json(root/'status.json')
    step=0;logs=[];state=None
    if resume:
        step,state=_load_step(root/'checkpoints',identity,model);logs=state['logs']
    attempt=root/'update_attempt.json'
    if attempt.exists() and read_json(attempt)['step']>step:raise ValueError('Unresolved optimizer attempt; no automatic budget reset')
    protected=[(p,p._version) for n,p in model.named_parameters() if n not in parameters]
    if state is None:
        random.seed(plan['seed']);torch.manual_seed(plan['seed'])
        if torch.cuda.is_available():torch.cuda.manual_seed_all(plan['seed'])
        _save_step(root/'checkpoints',identity,0,model,None,None,[]);after_update()
    else:_restore_rng(state['rng'])
    performed=0
    for actor in range(3):
        name=f'agent{actor}';selected=adapter_parameters(model,name)
        inactive={n:p for n,p in parameters.items() if n not in selected};before_hash=_weights_hash(inactive)
        batches=[(j,b) for j,b in enumerate(schedule_rows) if j>=step and b['agent']==actor]
        if not batches:continue
        with training_adapter(model,name):
            optimizer=torch.optim.AdamW(list(selected.values()),lr=1e-5,betas=(.9,.999),eps=1e-8,weight_decay=0.,foreach=False)
            if state and state['optimizer_agent']==name and state['optimizer'] is not None:optimizer.load_state_dict(state['optimizer'])
            for index,batch in batches:
                if stop_after is not None and performed>=stop_after:break
                before_update();write_json(attempt,{'step':step+1,'identity_hash':digest(identity),'state':'attempted'})
                started=time.monotonic()
                optimizer.zero_grad(set_to_none=True)
                parts=backward_rows(model,examples,batch,actor)
                grads=[p.grad for p in selected.values() if p.grad is not None]
                if not grads or any(not torch.isfinite(g).all() for g in grads):raise ValueError('Invalid active gradients')
                if any(p.grad is not None or p._version!=v for p,v in protected) or any(p.grad is not None for p in inactive.values()):raise ValueError('Inactive/backbone gradient or mutation')
                norm=torch.nn.utils.clip_grad_norm_(list(selected.values()),1.,error_if_nonfinite=True)
                optimizer.step();optimizer.zero_grad(set_to_none=True);step+=1;performed+=1
                if next(model.parameters()).is_cuda:torch.cuda.synchronize(next(model.parameters()).device)
                logs.append({'step':step,'agent':actor,'actor_step':batch['actor_step'],'gradient_norm':float(norm),'examples':parts,
                    'optimizer_step_seconds':time.monotonic()-started,
                    'timer_scope':'forward/backward/clip/optimizer; excludes checkpoint and persistence; not billed GPU time'})
                _save_step(root/'checkpoints',identity,step,model,optimizer,name,logs)
                write_json(attempt,{'step':step,'identity_hash':digest(identity),'state':'committed'})
                write_json(root/'status.json',{'complete':False,'completed_steps':step,'training_executed':True})
                after_update();print(f'Specialization {identity["arm"]} agent{actor}: {batch["actor_step"]}/32; team {step}/96',flush=True)
        if _weights_hash(inactive)!=before_hash:raise ValueError('Inactive adapter changed')
        state=None
        if stop_after is not None and performed>=stop_after:break
    if any(p._version!=v for p,v in protected):raise ValueError('Protected backbone/reference changed')
    result={'complete':step==96,'completed_steps':step,'planned_steps':96,'training_executed':step>0,
        'initial_weight_hash':contract['initial_weight_hash'],'final_weight_hash':_weights_hash(parameters),'logs':logs,
        'loss_audit':training_audit(examples,plan['seed']),'backbone_and_inactive_isolation':True}
    result['executed_training_tokens']={role:{
        'forwards':sum(role+'_nll' in item for log in logs for item in log['examples']),
        'target_tokens':sum(item.get(role+'_target_tokens',0) for log in logs for item in log['examples']),
        'sequence_tokens':sum(item.get(role+'_sequence_tokens',0) for log in logs for item in log['examples'])} for role in ('base','packet')}
    if result['complete']:result['references']=export_references(model,root,identity,step)
    write_json(root/'status.json',result);after_update()
    return result
