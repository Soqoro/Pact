"""Frozen design and reporting for a curated helpful-peer diagnostic."""
from __future__ import annotations
from collections import Counter
import dataclasses as dc
import json
from pathlib import Path
import random

from ..protocol import revision_prompt
from ..schemas import DeliveredMessage, PrivatePacket, task_from_dict
from ..parsing import parse_answer
from ..util import canonical, digest, node_seed, read_json
from .bank import sha
from .feasibility import read_review
from .receiver import call_from_dict, read_receiver_review
from .private_control import PrivateControlConfig, private_control_plan, private_report


@dc.dataclass(frozen=True)
class CuratedRepairConfig:
    receiver_bundle_sha256: str
    private_bundle_sha256: str
    schema_version: int = 1
    purpose: str = 'same_task_curated_helpful_peer_diagnostic'
    generation_seed: int = 20260920
    peer_order_seed: int = 1729
    samples_per_arm: int = 4

    def validate(self):
        sha(self.receiver_bundle_sha256);sha(self.private_bundle_sha256)
        if (self.schema_version != 1 or type(self.schema_version) is not int
                or self.purpose != 'same_task_curated_helpful_peer_diagnostic'
                or type(self.generation_seed) is not int or self.generation_seed != 20260920
                or type(self.peer_order_seed) is not int or self.peer_order_seed != 1729
                or type(self.samples_per_arm) is not int or self.samples_per_arm != 4):
            raise ValueError('Curated diagnostic fixes seeds and four samples per arm')
        return self


def load_curated_config(path):
    return CuratedRepairConfig(**read_json(Path(path))).validate()


def paired_contexts(task, private, donor, config):
    """One outgoing replacement; sender private state never changes."""
    config.validate()
    sender = donor['agent']
    if (task.split != 'train' or len(private)!=3 or [p.agent for p in private]!=[0,1,2]
            or any(p.task_id!=task.task_id for p in private)
            or donor['task_id']!=task.task_id or sender not in (0,1,2)):
        raise ValueError('Curated contexts require the same training task and three source identities')
    contexts=[]
    for recipient in range(3):
        if recipient==sender:continue
        for arm in ('original_peers','curated_help'):
            peers=[DeliveredMessage(i,recipient,donor['raw'] if arm=='curated_help' and i==sender else p.raw,
                                    digest(p)) for i,p in enumerate(private) if i!=recipient]
            random.Random(node_seed(config.peer_order_seed,task.task_id,recipient,'peer-order')).shuffle(peers)
            messages=revision_prompt(task,private[recipient],tuple(peers),'')
            context={'task_id':task.task_id,'family':task.family,'recipient':recipient,'sender':sender,'arm':arm,
                'messages':[dc.asdict(m) for m in messages],
                'messages_hash':digest(messages),'own_private_hash':digest(private[recipient]),
                'private_state_hash':digest(private),'delivered':[dc.asdict(p) for p in peers],
                'donor_call_hash':donor['call_hash'] if arm=='curated_help' else None,
                'seeds':[node_seed(config.generation_seed,'curated-repair-v1',task.task_id,recipient,j)
                         for j in range(config.samples_per_arm)]}
            context['context_id']=digest(context);contexts.append(context)
    return contexts


def curated_repair_plan(config,receiver_bundle,private_bundle):
    config.validate()
    receiver=read_receiver_review(receiver_bundle,config.receiver_bundle_sha256)
    control=read_review(private_bundle,config.private_bundle_sha256)
    pcfg=PrivateControlConfig(**control['plan.json']['config']).validate()
    if pcfg.source_bundle_sha256!=config.receiver_bundle_sha256:
        raise ValueError('Private control has a different parent')
    parent=private_control_plan(pcfg,receiver_bundle)
    manifest=control['manifest.json']
    if (canonical(parent)!=canonical(control['plan.json'])
            or manifest['status']!='private_support_complete_local'
            or manifest['completed_records']!=72 or manifest['recipe']['source']['dirty']
            or manifest['recipe']['plan_hash']!=digest(parent)
            or manifest['recipe_hash']!=digest(manifest['recipe'])):
        raise ValueError('Curated design requires the pinned completed private control')
    for mode in ('actors','base'):
        for key in ('snapshot','runtime_fingerprint','template_hash'):
            if control['model_identity.json'][mode][key]!=parent['models'][mode][key]:
                raise ValueError('Source model identities differ')
    records={r['work_id']:r for k,r in control.items() if k.startswith('shards/')}
    recomputed=private_report(parent,list(records.values()))
    reported=dict(control['report.json']);reported.pop('generation_accounting',None)
    if canonical(recomputed)!=canonical(reported) or not recomputed['complete']:
        raise ValueError('Private outcome report mismatch')
    tasks={}; private={}
    for item in parent['requests']:
        r=records[item['work_id']];task=task_from_dict(item['task']);call=call_from_dict(r['call'])
        if (r['request_hash']!=digest(item) or call.actor!=f"agent-{item['agent']}" or call.phase!='private'
                or call.seed!=item['seed'] or call.rendered_prompt!=item['baseline_call']['rendered_prompt']
                or r['tokens']['prompt_ids']!=item['prompt_ids'] or r['tokens']['raw']!=r['raw']):
            raise ValueError('Private source request differs')
        answer,explanation,status=parse_answer(r['raw'],tuple(o.answer_id for o in task.options),stop_reason=call.stop_reason)
        tasks[task.task_id]=(task,item['gold'])
        private.setdefault(task.task_id,[]).append(PrivatePacket(task.task_id,item['agent'],r['raw'],answer,explanation,status,call))
    donors={};inventory=[];contexts=[]
    for entry in parent['selection']['selected']:
        tid=entry['task_id'];task,gold=tasks[tid];packets=private[tid]
        if any(p.parser_status=='ok' and p.answer_id==gold for p in packets):continue
        candidates=[]
        for name,row in receiver.items():
            if not name.startswith('shards/'):continue
            t=row['trajectory']
            if t['task']['task_id']!=tid:continue
            if canonical(t['task'])!=canonical(task):raise ValueError('Donor source task mismatch')
            for phase,field in (('private','private'),('revision','revised')):
                for packet in t[field]:
                    answer,_,status=parse_answer(packet['raw'],tuple(o.answer_id for o in task.options),
                                                 stop_reason=packet['call']['stop_reason'])
                    if answer!=gold or status!='ok':continue
                    if packet['call']['actor']!=f"agent-{packet['agent']}" or packet['call']['snapshot']!=parent['models']['actors']['snapshot']:
                        raise ValueError('Donor actor identity mismatch')
                    donor={'task_id':tid,'agent':packet['agent'],'phase':phase,'condition':t['condition'],
                        'call_hash':digest(packet['call']),'packet_hash':digest(packet),'raw':packet['raw'],
                        'source_record':row['work_id'],'source_bundle_sha256':config.receiver_bundle_sha256}
                    rank=(phase!='private',t['condition']!='clean',packet['agent'],donor['call_hash'])
                    candidates.append((rank,donor))
        donor=min(candidates,key=lambda pair:pair[0])[1] if candidates else None
        inventory.append({'task_id':tid,'family':task.family,'correct_donor_candidates':len(candidates),
                          'status':'selected' if donor else 'missing_same_task_correct_packet'})
        if donor:
            if any(p.parser_status!='ok' for p in packets):raise ValueError('Design requires valid-wrong saved private packets')
            donors[tid]=donor;contexts.extend(paired_contexts(task,packets,donor,config))
    # This recipe pins the reviewed inventory; no expansion or substitution.
    if (len(inventory)!=9 or set(donors)!={'arc_challenge:Mercury_406916','arc_challenge:Mercury_7210613'}
            or len(contexts)!=8):
        raise ValueError('Source support differs from the fixed two-task curated design')
    return {'status':'curated_repair_plan_only','execution_implemented':True,'gpu_verified':False,
        'config':dc.asdict(config),'config_hash':digest(config),'models':parent['models'],
        'actor_recipe':parent['actor_recipe'],
        'tasks':{tid:dc.asdict(tasks[tid][0]) for tid in donors},
        'labels':{tid:tasks[tid][1] for tid in donors},
        'inventory':inventory,'donors':donors,'contexts':contexts,'contexts_hash':digest(contexts),
        'budget':{'tasks':2,'families':1,'recipients':4,'arms':2,'pools':8,'samples_per_pool':4,
                  'generation_calls_upper_bound':32,'generated_tokens_upper_bound':8192,
                  'input_tokens_upper_bound':122880,'teacher_forced_forwards':0,'optimizer_steps':0},
        'model_calls_executed':0,'training_executed':False,'training_pairs_exported':False,
        'full_pact_ready':False,'scope':'post-selected ARC-only curated context intervention; no natural-team efficacy claim'}


def curated_requests(plan):
    """Stable work identities; labels remain outside generation requests."""
    requests=[]
    for context in plan['contexts']:
        for index,seed in enumerate(context['seeds']):
            item={'context':context,'sample_index':index,'seed':seed}
            item['work_id']=digest(item);requests.append(item)
    return requests


def curated_report(plan,records):
    requests=curated_requests(plan);expected={r['work_id']:r for r in requests}
    indexed={r['work_id']:r for r in records}
    if len(indexed)!=len(records) or set(indexed)-expected.keys():
        raise ValueError('Duplicate or unknown curated records')
    pools=[];outcomes={}
    for context in plan['contexts']:
        candidates=[];prefix=None;params=None
        tid=context['task_id'];task=plan['tasks'][tid]
        allowed=tuple(o['answer_id'] for o in task['options'])
        for item in requests:
            if item['context']['context_id']!=context['context_id'] or item['work_id'] not in indexed:continue
            record=indexed[item['work_id']];call=record['call'];tokens=record['tokens']
            sampling=json.loads(call['parameters_json'])
            if (sampling.get('max_new_tokens')!=256 or sampling.get('do_sample') is not True
                    or any(sampling.get(k)!=v for k,v in (('temperature',.7),('top_p',.8),('top_k',20)))):
                raise ValueError('Curated sampling recipe changed')
            if (record['request_hash']!=digest(item) or record['context_id']!=context['context_id']
                    or record['sample_index']!=item['sample_index'] or call['seed']!=item['seed']
                    or call['phase']!='revision' or call['actor']!=f"agent-{context['recipient']}"
                    or canonical(call['messages'])!=canonical(context['messages'])
                    or call['snapshot']!=plan['models']['actors']['snapshot']
                    or call['template_hash']!=plan['models']['actors']['template_hash']
                    or tokens['raw']!=record['raw'] or call['context_hash']!=digest(call['rendered_prompt'])
                    or tokens['context_hash']!=call['context_hash']
                    or call['input_tokens']!=len(tokens['prompt_ids'])
                    or call['output_tokens']!=len(tokens['completion_ids'])):
                raise ValueError('Curated record differs from frozen request')
            current=(call['rendered_prompt'],tokens['prompt_ids'])
            if prefix is not None and (current!=prefix or params!=call['parameters_json']):
                raise ValueError('Within-arm prompt prefix or sampling mismatch')
            prefix=current;params=call['parameters_json']
            answer,_,status=parse_answer(record['raw'],allowed,stop_reason=call['stop_reason'])
            category=('correct' if answer==plan['labels'][tid] else 'wrong') if status=='ok' else status
            value={'sample_index':item['sample_index'],'seed':item['seed'],'answer':answer,
                   'parser_status':status,'outcome':category,'correct':category=='correct',
                   'output_tokens':len(tokens['completion_ids'])}
            candidates.append(value);outcomes[(tid,context['recipient'],context['arm'],item['sample_index'])]=value
        counts=Counter(v['outcome'] for v in candidates)
        positive=[v for v in candidates if v['outcome']=='correct']
        negative=[v for v in candidates if v['outcome']=='wrong']
        full=len(candidates)==4
        reason=('incomplete_pool' if not full else 'missing_both' if not positive and not negative else
                'missing_correct' if not positive else 'missing_incorrect' if not negative else None)
        pair=None
        if reason is None:
            def rank(pair):
                a,b=pair
                return (a['output_tokens']//32!=b['output_tokens']//32,
                        abs(a['output_tokens']-b['output_tokens']),a['sample_index'],b['sample_index'])
            p,n=min(((p,n) for p in positive for n in negative),key=rank)
            pair={'positive_index':p['sample_index'],'negative_index':n['sample_index'],
                  'length_matched':not rank((p,n))[0]}
        pools.append({k:context[k] for k in ('context_id','task_id','family','recipient','arm')} | {
            'fully_sampled':full,'candidate_count':len(candidates),'candidates':candidates,
            'counts':dict(counts),'invalid_count':sum(v for k,v in counts.items() if k not in ('correct','wrong','abstention','length')),
            'abstention_count':counts['abstention'],'length_failure_count':counts['length'],
            'missing_reason':reason,'pair':pair})
    comparisons=[]
    for context in plan['contexts']:
        if context['arm']!='original_peers':continue
        tid=context['task_id'];agent=context['recipient'];pairs=[];transitions=Counter()
        for index in range(4):
            a=outcomes.get((tid,agent,'original_peers',index));b=outcomes.get((tid,agent,'curated_help',index))
            if a is None or b is None:continue
            if a['seed']!=b['seed']:raise ValueError('Unmatched curated seed')
            transitions[f"{a['correct']}->{b['correct']}"]+=1
            pairs.append({'sample_index':index,'seed':a['seed'],'original_outcome':a['outcome'],
                          'curated_outcome':b['outcome'],'correctness_delta':int(b['correct'])-int(a['correct'])})
        comparisons.append({'task_id':tid,'recipient':agent,'paired_samples':len(pairs),'missing_pairs':4-len(pairs),
            'original_correct_count':sum(p['original_outcome']=='correct' for p in pairs),
            'curated_correct_count':sum(p['curated_outcome']=='correct' for p in pairs),
            'correctness_transitions':dict(transitions),'correct_count_delta':sum(p['correctness_delta'] for p in pairs),
            'pairs':pairs})
    complete=len(records)==len(requests)
    by_task=[]
    for tid in plan['tasks']:
        values=[v for v in comparisons if v['task_id']==tid]
        by_task.append({'task_id':tid,'paired_samples':sum(v['paired_samples'] for v in values),
                       'original_correct_count':sum(v['original_correct_count'] for v in values),
                       'curated_correct_count':sum(v['curated_correct_count'] for v in values),
                       'correct_count_delta':sum(v['correct_count_delta'] for v in values)})
    total_delta=sum(v['correct_count_delta'] for v in comparisons)
    curated_pairs=sum(p['pair'] is not None for p in pools if p['arm']=='curated_help')
    all_correct=complete and all(p['counts'].get('correct',0)==4 for p in pools)
    decision=('incomplete' if not complete else 'local_curated_pair_support' if curated_pairs else
              'both_arms_correct' if all_correct else 'curated_help_without_pairs' if total_delta>0 else
              'no_aggregate_help_or_harm')
    return {'kind':'curated_repair_diagnostic','complete':complete,'completed_records':len(records),
        'expected_records':len(requests),'missing_records':len(requests)-len(records),
        'pools':pools,'paired_comparisons':comparisons,'by_task':by_task,'decision':decision,
        'paired_samples':sum(v['paired_samples'] for v in comparisons),'correct_count_delta':total_delta,
        'within_arm_pairs':sum(p['pair'] is not None for p in pools),'curated_repair_pairs':curated_pairs,
        'training_executed':False,'training_pairs_exported':False,'full_pact_ready':False,
        'scope':plan['scope'],'limitation':'two post-selected ARC tasks; no hold, LogiQA, natural-team or terminal efficacy evidence'}
