"""receiver_supervision_v1: records, prefix masks, balanced loss and frozen study plan."""
from collections import Counter,defaultdict
import dataclasses as dc
import json,math
from pathlib import Path
from ..protocol import private_prompt,revision_prompt,deliver
from ..schemas import task_from_dict,PrivatePacket,DeliveredMessage,AttackRecord
from ..parsing import parse_answer
from ..util import canonical,digest,read_json,node_seed
from .data import read_training_data
from .feasibility import read_review
from .receiver import call_from_dict

ARMS=('frozen','task_sft','receiver_sft')
STRATA=('hold','repair')

@dc.dataclass(frozen=True)
class ReceiverSupervisionConfig:
    schema_version:int=1
    variant:str='receiver_supervision_v1'
    target_mode:str='receiver_answer_ce_v1'
    focal_agent:int=0
    selection_seed:int=20260922
    generation_seed:int=20260922
    fit_tasks:int=64
    heldout_tasks:int=32
    fit_contexts:int=64
    heldout_contexts:int=32
    fit_min_tasks_per_stratum:int=8
    heldout_min_tasks_per_stratum:int=4
    donor_draws:int=4
    smoke_tasks:int=8
    passes:int=2
    max_updates:int=32
    effective_batch:int=4
    learning_rate:float=1e-5
    anchor_coefficient:float=0.1
    lambda_rx:float=1.0
    lambda_dpo:float=0.0
    generation_cap:int=1500
    output_token_cap:int=384000
    data_manifest_hash:str='92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a'
    initialization_bundle_sha256:str='a1f5a23a14bb5420b963bbe02294345f98c17acd030b41e0686ce2085ff6d388'
    def validate(self):
        if self.schema_version!=1 or self.variant!='receiver_supervision_v1' or self.target_mode!='receiver_answer_ce_v1':raise ValueError('Unsupported supervision contract')
        for key in ('focal_agent','selection_seed','generation_seed','fit_tasks','heldout_tasks','fit_contexts','heldout_contexts','fit_min_tasks_per_stratum','heldout_min_tasks_per_stratum','donor_draws','smoke_tasks','passes','max_updates','effective_batch','generation_cap','output_token_cap'):
            if type(getattr(self,key)) is not int:raise ValueError('Integer setting required: '+key)
        if not (self.focal_agent in range(3) and self.fit_tasks==64 and self.heldout_tasks==32 and self.fit_contexts==64 and self.heldout_contexts==32
                and self.fit_min_tasks_per_stratum>=8 and self.heldout_min_tasks_per_stratum>=4 and 0<=self.donor_draws<=4
                and 1<=self.smoke_tasks<=8 and 1<=self.passes<=2 and 1<=self.max_updates<=32 and self.effective_batch==4):raise ValueError('Study exceeds first-study bounds')
        if not all(math.isfinite(v) for v in (self.learning_rate,self.anchor_coefficient,self.lambda_rx,self.lambda_dpo)):raise ValueError('Nonfinite loss configuration')
        if self.learning_rate!=1e-5 or self.anchor_coefficient!=.1 or self.lambda_rx!=1 or self.lambda_dpo!=0:raise ValueError('First study fixes LR/anchor and disables DPO; legacy DPO remains a separate explicit path')
        if not 0<=self.selection_seed<2**31 or not 0<=self.generation_seed<2**31:raise ValueError('Invalid seed')
        budget=study_budget(self)
        if self.generation_cap>1500 or self.output_token_cap>384000 or budget['generation_calls_upper_bound']>self.generation_cap or budget['generated_tokens_upper_bound']>self.output_token_cap:raise ValueError('Study generation ceiling exceeded before inference')
        return self


def study_budget(c):
    prep=(c.fit_tasks+c.heldout_tasks)*(3+c.donor_draws)
    receiver=3*c.heldout_contexts*2;private=3*c.heldout_tasks
    smoke=3*c.smoke_tasks*2*7;final=3*c.smoke_tasks*2
    updates=min(c.max_updates,c.passes*math.ceil(c.fit_contexts/c.effective_batch))
    return {'collection_calls_upper_bound':prep,'evaluation_calls_upper_bound':receiver+private+smoke,
        'generation_calls_upper_bound':prep+receiver+private+smoke,'generated_tokens_upper_bound':(prep+receiver+private+smoke-final)*256+final*64,
        'training_forward_backward_upper_bound':2*updates*c.effective_batch*2,'optimizer_updates_per_arm_upper_bound':updates,
        'evaluation_teacher_forced_forwards_upper_bound':receiver,'training_sequence_tokens_upper_bound':2*updates*c.effective_batch*2*4096,
        'evaluation_scoring_sequence_tokens_upper_bound':receiver*4096,'dpo_reference_forwards':0,'private_replay_calls':0}


def load_rx_config(path):return ReceiverSupervisionConfig(**read_json(Path(path))).validate()


def study_plan(config,data_dir,initialization_bundle,selection_path=None):
    config.validate();tasks,labels,manifest,_=read_training_data(Path(data_dir))
    if digest(manifest)!=config.data_manifest_hash:raise ValueError('Training pool mismatch')
    initial=read_review(initialization_bundle,config.initialization_bundle_sha256)
    old=initial['preparation_plan.json'];refs=initial['references/references.json']
    if refs['final_step']!=90 or initial['status.json']['completed_steps']!=90:raise ValueError('Initialization must be completed 120-task preparation')
    excluded={e['task_id'] for e in old['selection']}|{r['task']['task_id'] for r in old['private_probe_requests']}
    entries={e['task_id']:e for e in manifest['selected']}
    if not excluded<=entries.keys():raise ValueError('Exclusion provenance absent from pool')
    groups={entries[t]['group_id'] for t in excluded};content={entries[t]['content_group'] for t in excluded}
    candidates=defaultdict(list)
    for t in tasks:
        e=entries[t.task_id]
        if t.split!='train':raise ValueError('Only official training split allowed')
        if t.task_id not in excluded and e['group_id'] not in groups and e['content_group'] not in content:candidates[t.family].append(t)
    selected=[]
    for family in ('arc_challenge','logiqa'):
        ranked=sorted(candidates[family],key=lambda t:(digest([config.selection_seed,'receiver-supervision-v1',entries[t.task_id]['group_id']]),t.task_id))
        if len(ranked)<48:raise ValueError('Insufficient fresh groups')
        for i,t in enumerate(ranked[:48]):selected.append({**entries[t.task_id],'family':family,'partition':'fit' if i<32 else 'heldout'})
    selected.sort(key=lambda e:(e['partition'],e['family'],e['task_id']))
    if len({e['group_id'] for e in selected})!=96 or len({e['content_group'] for e in selected})!=96:raise ValueError('Duplicate split groups')
    if selection_path is not None and canonical(read_json(Path(selection_path)))!=canonical(selected):raise ValueError('Frozen membership changed')
    byid={t.task_id:t for t in tasks};ids={e['task_id'] for e in selected}
    return {'schema_version':1,'variant':config.variant,'config':dc.asdict(config),'config_hash':digest(config),'selection':selected,
        'selection_hash':digest(selected),'data_manifest':manifest,'tasks':{t:dc.asdict(byid[t]) for t in sorted(ids)},'labels':{t:dc.asdict(labels[t]) for t in sorted(ids)},
        'excluded_task_ids':sorted(excluded),'initialization_design':old,'initialization_references':refs,'budget':study_budget(config),
        'model':old['baseline_models']['base'],'arms':ARMS,'dpo_status':'disabled','full_pact_ready':False}


def answer_prefix(answer,allowed):
    if not isinstance(answer,str) or answer not in allowed or not answer:raise ValueError('Target outside task choices')
    quoted=json.dumps(answer,ensure_ascii=True)
    return '{"answer":'+quoted


def prefix_tokens(tokenizer,messages,answer,allowed,context_limit=4096):
    """Score tokens overlapping answer characters, never EOS or preceding formatting."""
    prompt=tokenizer.apply_chat_template([{'role':m['role'],'content':m['content']} for m in messages],tokenize=False,add_generation_prompt=True,enable_thinking=False)
    prefix=answer_prefix(answer,allowed);text=prompt+prefix
    encoded=tokenizer(text,add_special_tokens=False,return_offsets_mapping=True)
    ids=list(encoded['input_ids']);offsets=[tuple(x) for x in encoded['offset_mapping']]
    if len(ids)!=len(offsets) or any(len(x)!=2 or not 0<=x[0]<x[1]<=len(text) for x in offsets):raise ValueError('Invalid tokenizer offsets')
    prompt_ids=list(tokenizer.encode(prompt,add_special_tokens=False))
    if ids[:len(prompt_ids)]!=prompt_ids or not prompt_ids or len(ids)>context_limit:raise ValueError('Prefix boundary/context incompatibility; no truncation')
    start=len(prompt)+len('{"answer":"');end=len(text)-1
    mask=[int(a<end and b>start) for a,b in offsets]
    if not any(mask) or any(mask[:len(prompt_ids)]) or any(m and a<len(prompt) for m,(a,b) in zip(mask,offsets)):raise ValueError('Answer span overlaps prompt or is missing')
    if tokenizer.eos_token_id in ids[len(prompt_ids):]:raise ValueError('No EOS at incomplete packet prefix')
    return {'target_mode':'receiver_answer_ce_v1','is_generated_packet':False,'prompt':prompt,'output_prefix':prefix,
        'prompt_ids':prompt_ids,'input_ids':ids,'attention_mask':[1]*len(ids),'score_mask':mask,'offsets':offsets,
        'answer_char_span':[start,end],'supervised_positions':[i for i,m in enumerate(mask) if m],
        'boundary_overlap_policy':'score indivisible tokens intersecting answer text; log offsets including any merged delimiter; no pure formatting tokens',
        'eos_supervised':False}


def torch_answer_ce(logits,ids,attention,mask):
    import torch
    import torch.nn.functional as F
    if logits.ndim!=3 or logits.shape[:2]!=ids.shape or mask.shape!=ids.shape or attention.shape!=ids.shape:raise ValueError('Mask/logit dimensions')
    if not torch.all((mask==0)|(mask==1)) or not torch.all((attention==0)|(attention==1)) or (mask>attention).any() or mask[:,0].any():raise ValueError('Invalid answer mask')
    if ((attention[:,1:]-attention[:,:-1])>0).any() or (mask.sum(1)==0).any():raise ValueError('Empty targets or non-right padding')
    b,t=mask.nonzero(as_tuple=True);selected=logits[b,t-1]
    if not torch.isfinite(selected).all():raise ValueError('Nonfinite answer logits')
    losses=F.cross_entropy(selected.float() if selected.dtype in (torch.bfloat16,torch.float16) else selected,ids[b,t],reduction='none')
    return losses.new_zeros(ids.shape[0]).index_add(0,b,losses)/mask.sum(1)


def balanced_weights(records,min_tasks):
    if type(min_tasks) is not int or min_tasks<1:raise ValueError('Positive task support minimum required')
    if len({r['record_id'] for r in records})!=len(records):raise ValueError('Duplicate supervision records')
    if any(r['stratum'] not in STRATA for r in records):raise ValueError('Unknown stratum')
    counts={s:Counter(r['task_id'] for r in records if r['stratum']==s) for s in STRATA}
    missing=[s for s in STRATA if len(counts[s])<min_tasks]
    if missing:return {'status':'insufficient_context_support','missing_strata':missing,'task_counts':{s:len(v) for s,v in counts.items()},'weights':{}}
    return {'status':'valid','missing_strata':[],'task_counts':{s:len(v) for s,v in counts.items()},
        'weights':{r['record_id']:.5/len(counts[r['stratum']])/counts[r['stratum']][r['task_id']] for r in records}}


def receiver_objective(*,base,specialization,receiver,lambda_rx=1.,lambda_spec=0.,lambda_dpo=0.,dpo=None,dpo_validated=False):
    """Integration interface. DPO data validated by legacy builder/reference path, never fabricated."""
    if any(not math.isfinite(x) or x<0 for x in (lambda_rx,lambda_spec,lambda_dpo)):raise ValueError('Invalid loss coefficients')
    if lambda_dpo and (dpo is None or not dpo_validated):raise ValueError('Enabled DPO requires validated same-prompt pairs and immutable reference scores')
    return base+lambda_spec*specialization+lambda_rx*receiver+(lambda_dpo*dpo if lambda_dpo else 0)


def packet_dict(task,agent,raw,call):
    answer,why,status=parse_answer(raw,tuple(o.answer_id for o in task.options),stop_reason=call.stop_reason)
    return dc.asdict(PrivatePacket(task.task_id,agent,raw,answer,why,status,call))


def packet_from_dict(p):
    return PrivatePacket(p['task_id'],p['agent'],p['raw'],p['answer_id'],p['explanation'],p['parser_status'],call_from_dict(p['call']))


def context_record(plan,entry,private,own,peers,stratum,origins,source):
    cfg=ReceiverSupervisionConfig(**plan['config']);task=task_from_dict(plan['tasks'][entry['task_id']]);gold=plan['labels'][task.task_id]['answer_id']
    if len(private)!=3 or [p.agent for p in private]!=[0,1,2] or own.agent!=cfg.focal_agent or any(p.task_id!=task.task_id for p in (*private,own)):raise ValueError('Context private provenance mismatch')
    correct=own.parser_status=='ok' and own.answer_id==gold
    peer_classes=[parse_answer(p.text,tuple(o.answer_id for o in task.options))[0] for p in peers]
    eligible=(correct and any(a is not None and a!=gold for a in peer_classes)) if stratum=='hold' else (own.parser_status=='ok' and not correct and gold in peer_classes)
    if stratum not in STRATA or not eligible:raise ValueError('Ineligible receiver stratum')
    messages=[dc.asdict(m) for m in revision_prompt(task,own,tuple(peers),'')]
    record={'schema_version':1,'variant':cfg.variant,'task_id':task.task_id,'group_id':entry['group_id'],'split':'train',
        'partition':entry['partition'],'actor':f'agent-{cfg.focal_agent}','source_snapshot':own.call.snapshot,
        'source':source,'stratum':stratum,'target_mode':cfg.target_mode,'messages':messages,'context_hash':digest(messages),
        'private_history':[dc.asdict(p) for p in private],'own_saved':dc.asdict(own),'delivered':[dc.asdict(p) for p in peers],
        'donor_origins':origins,'answer_correct_advice_reasoning_audited':False,'target_answer':gold,
        'output_prefix':answer_prefix(gold,tuple(o.answer_id for o in task.options)),
        'loss_role':'receiver_supervised_only','target_mask_artifact':'target_masks.json (key: record_id)',
        'baseline_completion_class':'not_required'}
    record['record_id']=digest(record);return record


def build_contexts(plan,source_records):
    """Natural records first, then one traceable substitution per stratum/task; no new calls."""
    cfg=ReceiverSupervisionConfig(**plan['config']);index={r['task_id']:r for r in source_records};pool=[];unsupported=[]
    if len(index)!=len(source_records) or set(index)!={e['task_id'] for e in plan['selection']}:raise ValueError('Missing/duplicate/unselected source task')
    for pos,e in enumerate(plan['selection']):
        row=index[e['task_id']];private=tuple(packet_from_dict(p) for p in row['private']);own=private[cfg.focal_agent]
        alternatives=[packet_from_dict(p) for p in row['alternatives']]
        task=task_from_dict(plan['tasks'][e['task_id']]);gold=plan['labels'][task.task_id]['answer_id']
        if len(private)!=3 or len(alternatives)!=cfg.donor_draws or any(p.agent!=cfg.focal_agent for p in alternatives):raise ValueError('Donor schedule changed')
        for packet in (*private,*alternatives):
            parsed=parse_answer(packet.raw,tuple(o.answer_id for o in task.options),stop_reason=packet.call.stop_reason)
            if parsed!=(packet.answer_id,packet.explanation,packet.parser_status) or packet.call.messages!=private_prompt(task,''):
                raise ValueError('Donor parse/prompt provenance mismatch')
        if any(p.task_id!=task.task_id or p.call.snapshot!=own.call.snapshot for p in (*private,*alternatives)):raise ValueError('Cross-task/snapshot donor')
        peers=[DeliveredMessage(p.agent,cfg.focal_agent,p.raw,digest(p)) for p in private if p.agent!=cfg.focal_agent]
        for stratum in STRATA:
            try:r=context_record(plan,e,private,own,peers,stratum,[],'natural')
            except ValueError:
                own_pool=[p for p in (own,*alternatives) if p.agent==cfg.focal_agent and p.parser_status=='ok' and (p.answer_id==gold)==(stratum=='hold')]
                donor_pool=[p for p in (*private,*alternatives) if p.parser_status=='ok' and (p.answer_id==gold)==(stratum=='repair')]
                if not own_pool or not donor_pool:
                    unsupported.append({'task_id':task.task_id,'stratum':stratum,'partition':e['partition'],'reason':'missing_valid_own_or_same_task_donor'});continue
                chosen=own_pool[0];donor=donor_pool[0];sender=[i for i in range(3) if i!=cfg.focal_agent][pos%2]
                changed=[dc.replace(p,text=donor.raw) if p.sender==sender else p for p in peers]
                origins=[{'source':'curated','kind':'same_task_sampled_packet','source_record':row['work_id'],'packet_hash':digest(donor),
                    'packet':dc.asdict(donor),'original_sender':donor.agent,'delivered_sender':sender,'own_substitution':digest(chosen)!=digest(own),
                    'own_packet_hash':digest(chosen),'outgoing_replacement_identical_for_recipients':donor.raw}]
                r=context_record(plan,e,private,chosen,changed,stratum,origins,'curated')
            pool.append(r)
    selected={}
    for partition,cap,minimum in (('fit',cfg.fit_contexts,cfg.fit_min_tasks_per_stratum),('heldout',cfg.heldout_contexts,cfg.heldout_min_tasks_per_stratum)):
        records=[]
        for s in STRATA:
            candidates=[r for r in pool if r['partition']==partition and r['stratum']==s]
            candidates.sort(key=lambda r:(r['source']!='natural',digest([cfg.selection_seed,r['record_id']])))
            retained=candidates[:cap//2]
            curated_position=0
            for record in retained:
                if record['source']=='curated':
                    # Counterbalance the retained curated examples, without new samples.
                    sender=[i for i in range(3) if i!=cfg.focal_agent][curated_position%2];curated_position+=1
                    history=tuple(packet_from_dict(p) for p in record['private_history'])
                    own_saved=packet_from_dict(record['own_saved']);origins=[dict(o) for o in record['donor_origins']]
                    origins[0]['delivered_sender']=sender
                    original_peers=[DeliveredMessage(p.agent,cfg.focal_agent,p.raw,digest(p)) for p in history if p.agent!=cfg.focal_agent]
                    changed=[dc.replace(p,text=origins[0]['packet']['raw']) if p.sender==sender else p for p in original_peers]
                    entry=next(e for e in plan['selection'] if e['task_id']==record['task_id'])
                    record=context_record(plan,entry,history,own_saved,changed,s,origins,'curated')
                records.append(record)
        selected[partition]={'records':records,**balanced_weights(records,minimum)}
    return {'schema_version':1,'kind':'receiver_supervision_contexts','plan_hash':digest(plan),'partitions':selected,'unsupported':unsupported,
        'status':'ready' if all(v['status']=='valid' for v in selected.values()) else 'insufficient_context_support',
        'dpo_status':'disabled','dpo_pairs_required':False,'full_pact_ready':False}
