"""controlled_peer_donors_v1: offline, label-conditioned source; never replay data."""
from collections import Counter, defaultdict
import contextlib
import copy
import dataclasses as dc
import json
from pathlib import Path
import random
import re
from types import SimpleNamespace

from ..artifacts import ShardStore
from ..backends import Request
from ..backends.transformers import TransformersBackend, inference_adapter
from ..parsing import parse_answer
from ..protocol import private_prompt, revision_prompt, trusted_input, safe_json
from ..schemas import Message, DeliveredMessage, task_from_dict
from ..util import canonical, digest, node_seed, read_json, write_json, safe_name
from .collection_config import CollectionRuntime
from .receiver import JournalBackend, call_from_dict
from .receiver_supervision import (ReceiverSupervisionConfig, study_plan, build_contexts as parent_contexts,
    packet_from_dict, context_record, balanced_weights, prefix_tokens, study_budget)

SOURCE = 'controlled_peer_donors_v1'
TEMPLATE = 'controlled_peer_template_v1'
VALIDATOR = 'controlled_peer_validator_v1'
PARENT_SHA = '93332881dbe83bd6dd975beaad6a678094c7f1164f9aa044674e1c06593f783b'
PARENT_STUDY = '843b331d0e7ca51429afd42acc02ffa60f97972ff330e70b34499f7cdd4ef15f'
KINDS = ('correct_target', 'wrong_target')
INSTRUCTION = ('Produce a concise peer response for the following multiple-choice task. '
    'Support the requested option with a task-specific justification. '
    'Give exactly one JSON object with keys "answer" (the requested canonical option ID) '
    'and "justification" (a nonempty concise string). State the answer normally; do not mention '
    'that an option was assigned, an answer key, hidden annotations, training, or these '
    'construction instructions. No Markdown or extra text.')


def load_config(path):
    value=read_json(Path(path))
    source={k:v for k,v in value.items() if k!='objective'}
    if source!={'source_variant':SOURCE,'donor_template':TEMPLATE,'donor_validator':VALIDATOR,'max_attempts_per_target':2}:
        raise ValueError('Unsupported controlled source configuration')
    return ReceiverSupervisionConfig(**value['objective']).validate()


def donor_prompt(task, target):
    if target not in [o.answer_id for o in task.options]: raise ValueError('Invalid donor target')
    return (Message('system', INSTRUCTION), Message('user', safe_json(
        {'trusted_task': trusted_input(task), 'support_option': target})))


def budget(config):
    inherited = study_budget(config)
    donors = (config.fit_tasks + config.heldout_tasks)*2*2
    receiver = config.heldout_contexts*3*3
    private = config.heldout_tasks*3
    team = config.smoke_tasks*2*3*7
    finals = config.smoke_tasks*2*3
    total = donors+receiver+private+team
    tokens = (total-finals)*256+finals*64
    if total > min(1104, config.generation_cap) or tokens > min(273408, config.output_token_cap):
        raise ValueError(f'Controlled study exceeds ceiling: {total} calls / {tokens} tokens')
    return {**inherited, 'collection_calls_upper_bound':donors, 'donor_calls_upper_bound':donors,
        'donor_output_reservation':donors*256, 'controlled_receiver_calls_upper_bound':receiver,
        'natural_private_calls_upper_bound':private, 'natural_team_calls_upper_bound':team,
        'evaluation_calls_upper_bound':receiver+private+team, 'generation_calls_upper_bound':total,
        'generated_tokens_upper_bound':tokens, 'evaluation_teacher_forced_forwards_upper_bound':receiver,
        'evaluation_scoring_sequence_tokens_upper_bound':receiver*4096,
        'optimizer_updates_all_arms_upper_bound':2*inherited['optimizer_updates_per_arm_upper_bound'],
        'clean_anchor_presentations_upper_bound':inherited['training_forward_backward_upper_bound']//2,
        'parent_imported_calls':672, 'parent_new_calls':0}


def validate_parent(content, expected):
    """Reconstruct the frozen plan and every original packet's journal link, read-only."""
    old = content['plan.json']
    if canonical(old) != canonical(expected): raise ValueError('Parent frozen plan differs from reviewed population')
    if content['state.json']['study_hash'] != digest(content['recipe.json']): raise ValueError('Parent study identity mismatch')
    if canonical(content['recipe.json']['plan']) != canonical(old): raise ValueError('Parent recipe mismatch')
    records = [v for k,v in content.items() if k.startswith('contexts/shards/') and k.endswith('.json')]
    rebuilt = parent_contexts(old, records)
    if canonical(rebuilt) != canonical(content['contexts.json']): raise ValueError('Parent context audit mismatch')
    identity = content['model_identity.json']
    validator = object.__new__(JournalBackend)
    validator.identity = identity
    validator.backend = SimpleNamespace(tokenizer=SimpleNamespace(eos_token_id=151645))
    calls = {k.split('/')[-1][:-5]:v for k,v in content.items() if k.startswith('contexts/calls/shards/') and k.endswith('.json')}
    intents = {k.split('/')[-1][:-5]:v for k,v in content.items() if k.startswith('contexts/call-intents/') and k.endswith('.json')}
    if len(calls)!=672 or calls.keys()!=intents.keys(): raise ValueError('Missing parent calls or unresolved attempts')
    seen = set()
    for row in records:
        task = task_from_dict(old['tasks'][row['task_id']]); rid=digest(['source',task.task_id])
        if row['work_id']!=rid: raise ValueError('Parent source ID mismatch')
        for slot, p in enumerate(row['private']+row['alternatives']):
            agent = slot if slot<3 else 0
            seed = (node_seed(old['config']['generation_seed'],task.task_id,'source-private',agent) if slot<3
                    else node_seed(old['config']['generation_seed'],task.task_id,'donor',0,slot-3))
            request = Request(task,private_prompt(task,''),f'agent-{agent}','private',seed,256,False)
            key=digest([rid,slot]); seen.add(key)
            intent={'schema_version':1,'work_id':key,'record_id':rid,'slot':slot,'request_hash':digest(request),'max_tokens':256}
            if intents[key]!=intent or calls[key]['raw']!=p['raw'] or calls[key]['call']!=p['call']:
                raise ValueError('Parent packet/journal mismatch')
            validator.validate_request(request);validator._validate(request,intent,calls[key])
    if seen!=calls.keys(): raise ValueError('Unexpected parent journal calls')
    return records


def plan(config, data_dir, initialization_bundle, selection, parent_bundle, acquisition_id):
    from .receiver_study import read_receiver_supervision_review
    config.validate()
    if config.focal_agent!=0 or config.donor_draws!=0: raise ValueError('Controlled source fixes focal0 and forbids new natural draws')
    safe_name(acquisition_id)
    original_config=dc.replace(config,donor_draws=4,generation_cap=1500,output_token_cap=384000)
    expected=study_plan(original_config,data_dir,initialization_bundle,selection)
    content=read_receiver_supervision_review(parent_bundle,PARENT_SHA)
    if content['state.json']['study_hash']!=PARENT_STUDY: raise ValueError('Unexpected reviewed parent')
    records=validate_parent(content,expected)
    child=copy.deepcopy(content['plan.json'])
    child.update(config=dc.asdict(config),config_hash=digest(config),source_variant=SOURCE,
        budget=budget(config), parent={'run_id':'qwen3-receiver-supervision-001','sha256':PARENT_SHA,
            'study_hash':PARENT_STUDY,'source':content['recipe.json']['source'],
            'source_records_hash':digest(records)}, parent_sources=records,
        acquisition_id=acquisition_id, donor_template=TEMPLATE, donor_validator=VALIDATOR,
        donor_instruction=INSTRUCTION, generator_policy='unadapted_base_all_adapters_disabled',
        diagnostic_partition='development-heldout; parent eligibility inspected',
        generator_identity=child['model'], parent_actor_identity=content['model_identity.json'])
    child['donor_schedule']=acquisition_plan(child)
    return child


def acquisition_plan(plan):
    rows={r['task_id']:r for r in plan['parent_sources']}; result=[]
    seed=plan['config']['generation_seed']
    for entry in plan['selection']:
        task=task_from_dict(plan['tasks'][entry['task_id']]); gold=plan['labels'][task.task_id]['answer_id']
        private=[packet_from_dict(p) for p in rows[task.task_id]['private']]
        # Choices depend on stable task identity, never subset position or realized outcomes.
        choice_seed=node_seed(seed,SOURCE,task.task_id,'wrong-target')
        wrong=random.Random(choice_seed).choice(sorted(o.answer_id for o in task.options if o.answer_id!=gold))
        sender=random.Random(node_seed(seed,SOURCE,task.task_id,'sender')).choice([1,2])
        reasons=[]
        if private[0].parser_status!='ok': reasons.append('original_focal_'+private[0].parser_status)
        for p in private[1:]:
            # Original builder had no parse gate for the replaced bytes; unchanged peer permits abstention.
            if p.agent!=sender and p.parser_status not in ('ok','abstention'): reasons.append('unchanged_peer_'+p.parser_status)
        targets={kind:{'option':option,'seeds':[node_seed(seed,SOURCE,task.task_id,kind,TEMPLATE,j) for j in range(2)]}
                 for kind,option in zip(KINDS,(gold,wrong))}
        result.append({**entry,'eligible':not reasons,'unsupported_reasons':reasons,'sender':sender,
            'own_correct':private[0].parser_status=='ok' and private[0].answer_id==gold,
            'wrong_target_agrees_with_wrong_own':private[0].parser_status=='ok' and private[0].answer_id!=gold and private[0].answer_id==wrong,
            'own_packet_hash':digest(private[0]),'trusted_input_hash':digest(trusted_input(task)),
            'wrong_target_seed':choice_seed,'targets':targets})
    return result


def validate_donor(raw, task, target, gold, stop_reason):
    answer, why, status=parse_answer(raw,tuple(o.answer_id for o in task.options),stop_reason=stop_reason)
    reasons=[]
    if status!='ok': reasons.append('parser_'+status)
    if status=='ok' and answer!=target: reasons.append('target_mismatch')
    if len(why)>4096: reasons.append('justification_too_long')
    if re.search(r'(?i)\b(?:the assigned target (?:is|was)|the answer key says|this is a (?:hold|repair) training example|I (?:was|am) (?:assigned|instructed) to support)\b',raw):
        reasons.append('construction_metadata_disclosure')
    if re.search(r'(?i)<\|(?:im_start|im_end|start_header_id|end_header_id)\|>|\[/?INST\]|</?(?:system|assistant|developer)>',raw):
        reasons.append('privileged_role_delimiter')
    return {'validator':VALIDATOR,'accepted':not reasons,'rejection_reasons':reasons,
        'answer_id':answer,'explanation':why,'parser_status':status,'target_match':status=='ok' and answer==target,
        'answer_correct':status=='ok' and answer==gold,'rationale_review_status':'not_reviewed',
        'reasoning_verified':False}


class DonorJournal(JournalBackend):
    def validate_request(self, request):
        if (request.task.split!='train' or request.actor!='base' or request.phase!='controlled_donor'
            or request.max_tokens!=256 or request.deterministic): raise ValueError('Donor request outside fixed design')
        user=json.loads(request.messages[1].content)
        if request.messages!=donor_prompt(request.task,user['support_option']): raise ValueError('Donor template changed')


@contextlib.contextmanager
def donor_isolation(model):
    """Use existing adapter isolation, additionally restoring incoming grad/mode state."""
    flags=[(p,p.requires_grad) for p in model.parameters()]
    modes=[(m,m.training) for m in model.modules()]
    try:
        with inference_adapter(model,None,bool(getattr(model,'peft_config',{}))): yield
    finally:
        for p,flag in flags:p.requires_grad_(flag)
        for m,mode in modes:m.training=mode


class DonorBackend(TransformersBackend):
    def generate(self, request):
        if request.actor!='base' or self.config.model.adapters or self.identity['adapters']:
            raise ValueError('Donors must use the pinned unadapted base')
        with donor_isolation(self.model): return super().generate(request)
    def assert_unchanged(self):
        if any(p._version!=v for p,v in self.protected): raise RuntimeError('Donor backbone changed')


def validate_generator_identity(plan, identity):
    if identity.get('backend')=='mock':return
    if identity.get('adapters')!=[]:raise ValueError('Donor identity includes learner adapters')
    for key in ('snapshot','runtime_fingerprint','revision','tokenizer_revision','template_hash','precision','attention','enable_thinking'):
        if identity[key]!=plan['model'][key]:raise ValueError('Donor base identity mismatch: '+key)


def load_backend(plan, cache):
    runtime=CollectionRuntime(digest(plan),plan['config']['generation_seed'])
    backend=DonorBackend(runtime,cache)
    validate_generator_identity(plan,backend.identity)
    backend.protected=[(p,p._version) for p in backend.model.parameters()]
    return runtime,backend


class MockTokenizer:
    """Transparent character tokenizer for software fixtures, not Qwen tokenization."""
    eos_token_id=0
    def apply_chat_template(self,messages,**kwargs):
        return ''.join('<'+m['role']+'>\n'+m['content']+'\n' for m in messages)+'<assistant>\n'
    def encode(self,text,**kwargs):return [ord(c)+1 for c in text]
    def __call__(self,text,**kwargs):
        return {'input_ids':self.encode(text),'offset_mapping':[(i,i+1) for i in range(len(text))]}


class MockDonorBackend:
    """Deterministic bounded software double. Cannot stand in for GPU evidence."""
    def __init__(self):
        self.tokenizer=MockTokenizer();self.calls=[]
        self.identity={'backend':'mock','snapshot':digest('controlled-donor-mock-v1'),
                       'template_hash':digest('character-template'),'adapters':[],'adapter_policy':'all_disabled'}
    def completion(self,request):
        target=json.loads(request.messages[1].content)['support_option']
        return canonical({'answer':target,'justification':'Synthetic software fixture supporting option '+target+'.'})
    def generate(self,request):
        from ..schemas import CallRecord
        raw=self.completion(request);rendered=self.tokenizer.apply_chat_template([dc.asdict(m) for m in request.messages])
        prompt=self.tokenizer.encode(rendered);output=self.tokenizer.encode(raw)+[0];stop='eos'
        if len(prompt)+256>4096:raw='';output=[];stop='context_overflow'
        if len(output)>256:output=output[:256];raw=''.join(chr(x-1) for x in output);stop='length'
        params=canonical({'max_new_tokens':256,'do_sample':True,'temperature':.7,'top_p':.8,'top_k':20})
        call=CallRecord(request.actor,request.phase,self.identity['snapshot'],request.seed,request.messages,
            rendered,digest(rendered),self.identity['template_hash'],params,len(prompt),len(output),stop,0.)
        self.last_generation={'prompt_ids':prompt,'completion_ids':output,'raw':raw,'context_hash':digest(rendered)}
        self.calls.append(call);return raw,call
    def assert_unchanged(self):pass
    def count_tokens(self,text):return len(self.tokenizer.encode(text))


def attempt_record(plan, spec, kind, attempt, request, raw, call, identity, plan_hash=None):
    task=request.task
    row={'schema_version':1,'source_variant':SOURCE,'acquisition_id':plan['acquisition_id'],
        'parent':plan['parent'],'task_id':task.task_id,'group_id':spec['group_id'],'partition':spec['partition'],
        'family':task.family,'trusted_input_hash':spec['trusted_input_hash'],'generator':identity,
        'adapter_policy':'all_disabled','template':TEMPLATE,'target_kind':kind,'target_option':spec['targets'][kind]['option'],
        'wrong_target_seed':spec['wrong_target_seed'],'attempt':attempt,'seed':request.seed,
        'request':dc.asdict(request),'request_hash':digest(request),'raw':raw,'raw_hash':digest(raw),
        'call':dc.asdict(call),'reserved_output_tokens':256,'attempt_status':'committed',
        **validate_donor(raw,task,spec['targets'][kind]['option'],plan['labels'][task.task_id]['answer_id'],call.stop_reason)}
    row['work_id']=digest([plan_hash or digest(plan),task.task_id,kind,attempt,TEMPLATE,VALIDATOR]);return row


def acquire(plan, backend, runtime, root, recovery, stop_after=None):
    plan_hash=digest(plan)
    stage=root/'donors'; b={'generation_calls_upper_bound':plan['budget']['donor_calls_upper_bound'],
                          'generated_tokens_upper_bound':plan['budget']['donor_output_reservation']}
    journal=DonorJournal(backend,stage,b,stop_after=stop_after,before_new=recovery.before);store=ShardStore(stage)
    for spec in plan['donor_schedule']:
        if not spec['eligible']:continue
        task=task_from_dict(plan['tasks'][spec['task_id']])
        for kind in KINDS:
            target=spec['targets'][kind]
            for attempt,seed in enumerate(target['seeds']):
                request=Request(task,donor_prompt(task,target['option']),'base','controlled_donor',seed,256,False)
                key=digest([plan_hash,task.task_id,kind,attempt,TEMPLATE,VALIDATOR]);journal.begin_record(key)
                raw,call=journal.generate(request)
                row=attempt_record(plan,spec,kind,attempt,request,raw,call,backend.identity,plan_hash)
                store.put(key,row)
                if row['accepted']:break
        recovery.after()  # persist each completed task; scratch journals retain every attempt
    backend.assert_unchanged()
    write_json(stage/'status.json',{'complete':True,'attempts':len(journal.results),'generator':backend.identity})
    result=freeze_contexts(plan,root,backend.tokenizer)
    recovery.after()
    return {'status':result['status'],'source_variant':SOURCE,'yields':result['yields']}


def verified_attempts(plan, root):
    """Replay immutable calls without a model; reject extra/missing attempts and modified validation."""
    plan_hash=digest(plan)
    stage=root/'donors';status=read_json(stage/'status.json')
    if not status['complete']:raise ValueError('Acquisition incomplete')
    validate_generator_identity(plan,status['generator'])
    fake=SimpleNamespace(identity=status['generator'],tokenizer=SimpleNamespace(eos_token_id=151645 if status['generator'].get('backend')!='mock' else 0))
    journal=DonorJournal(fake,stage,{'generation_calls_upper_bound':384,'generated_tokens_upper_bound':98304},stop_after=0)
    expected=[]
    for spec in plan['donor_schedule']:
        if not spec['eligible']:continue
        task=task_from_dict(plan['tasks'][spec['task_id']])
        for kind in KINDS:
            for attempt,seed in enumerate(spec['targets'][kind]['seeds']):
                request=Request(task,donor_prompt(task,spec['targets'][kind]['option']),'base','controlled_donor',seed,256,False)
                key=digest([plan_hash,task.task_id,kind,attempt,TEMPLATE,VALIDATOR]);journal.begin_record(key)
                raw,call=journal.generate(request)
                row=attempt_record(plan,spec,kind,attempt,request,raw,call,fake.identity,plan_hash);expected.append(row)
                if row['accepted']:break
    actual=ShardStore(stage).records()
    if (canonical(sorted(expected,key=lambda r:r['work_id']))!=canonical(sorted(actual,key=lambda r:r['work_id']))
        or journal.seen!=journal.results.keys() or status['attempts']!=len(expected)):raise ValueError('Donor bank or attempt ledger changed')
    return expected


def build_contexts(plan, attempts):
    sources={r['task_id']:r for r in plan['parent_sources']};accepted={}
    for row in attempts:
        if row['accepted']:
            key=(row['task_id'],row['target_kind'])
            if key in accepted:raise ValueError('Multiple accepted targets')
            accepted[key]=row
    pool=[];variants={};unsupported=[]
    for spec in plan['donor_schedule']:
        tid=spec['task_id'];source=sources[tid];private=tuple(packet_from_dict(p) for p in source['private'])
        own=private[0];task=task_from_dict(plan['tasks'][tid]);stratum='hold' if spec['own_correct'] else 'repair'
        primary='wrong_target' if spec['own_correct'] else 'correct_target'
        if not spec['eligible']:
            unsupported.append({'task_id':tid,'partition':spec['partition'],'reasons':spec['unsupported_reasons']});continue
        versions={}
        for kind in KINDS:
            donor=accepted.get((tid,kind))
            if donor is None:continue
            peers=[DeliveredMessage(p.agent,0,donor['raw'] if p.agent==spec['sender'] else p.raw,digest(p)) for p in private[1:]]
            prompt=[dc.asdict(m) for m in revision_prompt(task,own,tuple(peers),'')]
            versions[kind]={'messages':prompt,'context_hash':digest(prompt),'donor_id':donor['work_id'],
                            'delivered':[dc.asdict(p) for p in peers]}
        variants[tid]=versions
        if primary not in versions:
            unsupported.append({'task_id':tid,'partition':spec['partition'],'reasons':['missing_primary_'+primary]});continue
        donor=accepted[(tid,primary)]
        origins=[{'source_variant':SOURCE,'donor_id':donor['work_id'],'delivered_sender':spec['sender'],
            'own_substitution':False,'original_replaced_packet':source['private'][spec['sender']],
            'rationale_review_status':'not_reviewed','not_same_actor_replay':True}]
        peers=[DeliveredMessage(**{k:v for k,v in p.items() if k!='schema_version'}) for p in versions[primary]['delivered']]
        record=context_record(plan,spec,private,own,peers,stratum,origins,SOURCE)
        record.update(source_variant=SOURCE,primary_condition=primary,donor_variants=versions,
            same_prompt_dpo_pair=False,original_own_packet_hash=digest(own))
        record.pop('record_id');record['record_id']=digest(record);pool.append(record)
    partitions={}
    for partition,cap,minimum in (('fit',64,plan['config']['fit_min_tasks_per_stratum']),('heldout',32,plan['config']['heldout_min_tasks_per_stratum'])):
        selected=[]
        for stratum in ('hold','repair'):
            candidates=[r for r in pool if r['partition']==partition and r['stratum']==stratum]
            candidates.sort(key=lambda r:(digest([plan['config']['selection_seed'],SOURCE,'context-order',r['group_id']]),r['task_id']))
            selected.extend(candidates[:cap//2])
        partitions[partition]={'records':selected,**balanced_weights(selected,minimum),
            'paired_control_tasks':sum(len(r['donor_variants'])==2 for r in selected),
            'missing_opposite_controls':sum(len(r['donor_variants'])<2 for r in selected)}
    yields=[]
    for partition in ('fit','heldout'):
        for family in ('arc_challenge','logiqa'):
            specs=[s for s in plan['donor_schedule'] if s['partition']==partition and s['family']==family];ids={s['task_id'] for s in specs}
            cohort=[r for r in pool if r['task_id'] in ids];calls=[r for r in attempts if r['task_id'] in ids]
            yields.append({'partition':partition,'family':family,'source_tasks':len(specs),
                'valid_original_focal_states':sum(sources[s['task_id']]['private'][0]['parser_status']=='ok' for s in specs),
                'eligible_source_tasks':sum(s['eligible'] for s in specs),
                'wrong_target_agrees_with_wrong_own':sum(s['wrong_target_agrees_with_wrong_own'] for s in specs if s['eligible']),
                'donor_attempts':len(calls),
                'accepted_targets':dict(Counter(r['target_kind'] for r in calls if r['accepted'])),
                'rejection_reasons':dict(Counter(x for r in calls for x in r['rejection_reasons'])),
                'primary_tasks':dict(Counter(r['stratum'] for r in cohort)),
                'selected_primary_tasks':dict(Counter(r['stratum'] for r in partitions[partition]['records'] if r['task_id'] in ids)),
                'paired_control_tasks':sum(len(r['donor_variants'])==2 for r in cohort),
                'sender_positions':dict(Counter(str(s['sender']) for s in specs if s['eligible']))})
    return {'schema_version':1,'kind':'receiver_supervision_contexts','source_variant':SOURCE,
        'plan_hash':digest(plan),'partitions':partitions,'unsupported':unsupported,'yields':yields,
        'status':'ready' if all(p['status']=='valid' for p in partitions.values()) else 'insufficient_context_support',
        'dpo_status':'disabled','dpo_pairs_required':False,'full_pact_ready':False}


def freeze_contexts(plan, root, tokenizer):
    attempts=verified_attempts(plan,root);contexts=build_contexts(plan,attempts);contracts={}
    for part in contexts['partitions'].values():
        for row in part['records']:
            task=task_from_dict(plan['tasks'][row['task_id']]);allowed=tuple(o.answer_id for o in task.options)
            for version in row['donor_variants'].values():
                tokens=prefix_tokens(tokenizer,version['messages'],row['target_answer'],allowed)
                if len(tokens['prompt_ids'])+256>4096:raise ValueError('Controlled receiver context overflow; no truncation')
            contracts[row['record_id']]=prefix_tokens(tokenizer,row['messages'],row['target_answer'],allowed)
    write_json(root/'contexts.json',contexts);write_json(root/'target_masks.json',contracts)
    if contexts['status']=='ready':
        from .receiver_supervision_train import training_examples, update_schedule
        cfg=ReceiverSupervisionConfig(**plan['config'])
        schedules={}
        for arm in ('task_sft','receiver_sft'):
            examples=training_examples(plan,contexts,tokenizer,arm)
            schedules[arm]={'schedule':update_schedule(examples,cfg),'examples_hash':digest(examples),
                'tasks':[e['task_id'] for e in examples],'anchor_hashes':[digest(e['anchor']) for e in examples]}
        if any(schedules['task_sft'][k]!=schedules['receiver_sft'][k] for k in ('schedule','tasks','anchor_hashes')):
            raise ValueError('Comparison arms have unmatched exposure')
        write_json(root/'training_schedule.json',schedules)
    groups=defaultdict(list)
    for row in attempts:
        if row['accepted']:groups[(row['family'],row['partition'],row['target_kind'])].append(row)
    sample=[]
    for group in sorted(groups):sample.extend(sorted(groups[group],key=lambda r:digest([SOURCE,'review',r['work_id']]))[:2])
    write_json(root/'donor_review.json',{'rationale_review_status':'not_reviewed','structural_acceptance_is_not_reasoning_verification':True,
        'accepted':[{'task':plan['tasks'][r['task_id']],'donor':r} for r in sample[:16]],
        'rejections':sorted([r for r in attempts if not r['accepted']],key=lambda r:digest(r))[:16]})
    return contexts


def main(argv=None):
    from .receiver_study import main as study_main
    return study_main(argv, controlled=True)



def progress_report(plan, root):
    """Partial/failure reports count intents too; never infer learning from passed tests."""
    intents=[read_json(p) for p in (root/'donors/call-intents').glob('*.json')]
    call_store=ShardStore(root/'donors/calls')
    calls=[call_store.read(i['work_id']) for i in intents if call_store.path(i['work_id']).exists() and call_store.path(i['work_id']).with_suffix('.sha256').exists()]
    attempts=ShardStore(root/'donors').records()
    contexts=read_json(root/'contexts.json') if (root/'contexts.json').exists() else None
    training={a:read_json(root/'training'/a/'status.json') if (root/'training'/a/'status.json').exists() else {'status':'not_executed','training_executed':False}
              for a in ('task_sft','receiver_sft')}
    result={'source_variant':SOURCE,'objective':plan['variant'],'parent':plan['parent'],
        'status':contexts['status'] if contexts else 'acquisition_incomplete','budget':plan['budget'],
        'readiness':{'acquisition_complete':(root/'donors/status.json').exists(),
            'structurally_accepted_donors':sum(r['accepted'] for r in attempts),'rationale_review_status':'not_reviewed',
            'context_support':contexts['status'] if contexts else 'not_built','training':training,
            'evaluation_complete':all((root/'evaluation'/a/'status.json').exists() for a in ('frozen','task_sft','receiver_sft')),
            'optional_dpo':'disabled','specialization_integration':'deferred','full_pact_efficacy':'unestablished'},
        'acquisition_accounting':{'attempted_calls':len(intents),'committed_calls':len(calls),'unresolved_attempts':len(intents)-len(calls),
            'reserved_output_tokens':sum(i['max_tokens'] for i in intents),
            'input_tokens':sum(r['call']['input_tokens'] for r in calls),
            'output_tokens':sum(r['call']['output_tokens'] for r in calls)},
        'yields':contexts['yields'] if contexts else [],'unsupported':contexts['unsupported'] if contexts else [],
        'compute_units':None,'full_pact_ready':False}
    write_json(root/'source_report.json',result);return result


def augment_report(plan, contexts, result):
    from .receiver_study import summarize
    result.update(source_variant=SOURCE,donor_rationale_review_status='not_reviewed',
        history='Own histories are original prepared focal packets; donors are newly constructed offline base-model interventions, not natural initialization or updated-team trajectories.',
        context_diagnostic='label-conditioned controlled intervention; not natural robustness or a final test',
        yields=contexts['yields'])
    result['readiness'].update(acquisition_complete=True,structural_donor_validity='accepted under '+VALIDATOR,
        rationale_review_status='not_reviewed',context_support='passed',evaluation_complete=True)
    contrasts={}
    for arm,value in result['arms'].items():
        rows=[r for r in value['per_task'] if r['kind']=='receiver']
        lookup={(r['task_id'],r['condition']):r for r in rows}
        pairs=[];transitions=Counter()
        for tid in sorted({r['task_id'] for r in rows}):
            correct=lookup.get((tid,'correct_target'));wrong=lookup.get((tid,'wrong_target'))
            if correct is None or wrong is None:continue
            if any(correct['match'][k]!=wrong['match'][k] for k in ('task_id','actor','seed','decoding')):
                raise ValueError('Unmatched correct/wrong donor comparison')
            pairs.append({'task_id':tid,'correct_target':correct['correct'],'wrong_target':wrong['correct'],
                          'correct_context_hash':correct['match']['context_hash'],'wrong_context_hash':wrong['match']['context_hash']})
            transitions[f'{wrong["correct"]}->{correct["correct"]}']+=1
        contrasts[arm]={'paired_tasks':len(pairs),'pairs':pairs,'wrong_to_correct_advice_transitions':dict(transitions),
            'missing_opposite_controls':contexts['partitions']['heldout']['missing_opposite_controls']}
        value['behavior']={name:summarize([r for r in rows if r['stratum']==stratum and r['condition']==condition])
            for name,stratum,condition in (('hold_retention','hold','wrong_target'),('repair_success','repair','correct_target'),
                ('agreement','hold','correct_target'),('misleading_advice','repair','wrong_target'))}
        held=[r for r in rows if r['stratum']=='hold' and r['condition']=='wrong_target']
        value['behavior']['hold_harmful_revision']={'failures':sum(not r['correct'] for r in held),'denominator':len(held)}
    result['controlled_donor_comparisons']=contrasts


if __name__=='__main__':main()
