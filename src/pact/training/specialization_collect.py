"""Fixed-bank acquisition and exact journal replay over the existing protocol."""
import dataclasses as dc
import json
from pathlib import Path
from types import SimpleNamespace

from ..artifacts import ShardStore
from ..backends import Request
from ..protocol import Protocol
from ..replay import probe,choose_pair
from ..schemas import task_from_dict,TaskLabel,AttackRecord
from ..util import canonical,digest,node_seed,read_json,write_json
from .collection_config import CollectionRuntime
from ..config import ProbeConfig
from .receiver import JournalBackend,inspect_journal
from .losses import answer_target
from .assignment_contrast import reconstruct_record
from .specialization_plan import budgets


def runtime(plan):
    return CollectionRuntime(digest(plan),plan['seed'],probe=ProbeConfig(tasks=32,candidates=4,suffix_seeds=2,revision_candidates=0))


def immutable(path,value):
    if path.exists() and canonical(read_json(path))!=canonical(value):raise ValueError('Immutable specialization artifact changed')
    if not path.exists():write_json(path,value)


class StudyJournal(JournalBackend):
    def __init__(self,backend,root,budget,plan,partition,*,readonly=False,**kw):
        super().__init__(backend,root,budget,**kw)
        self.plan=plan;self.partition=partition;self.readonly=readonly
        self.allowed={e['task_id'] for e in plan['selection'] if e['partition']==partition}
    def validate_request(self,r):
        super().validate_request(r)
        if r.task.task_id not in self.allowed or canonical(r.task)!=canonical(self.plan['tasks'][r.task.task_id]):
            raise ValueError('Unselected or changed task/split')
    def generate(self,r):
        if not self.readonly and hasattr(self.backend.tokenizer,'apply_chat_template'):
            rendered=self.backend.tokenizer.apply_chat_template([{'role':m.role,'content':m.content} for m in r.messages],tokenize=False,add_generation_prompt=True,enable_thinking=False)
            if self.backend.count_tokens(rendered)+r.max_tokens>4096:raise ValueError('Fixed context cap exceeded; no truncation')
        self.begin_record(digest([r,self.identity['snapshot']]))
        if self.readonly and digest([self.record_key,0]) not in self.results:raise ValueError('Missing committed generation; offline reconstruction never samples')
        return super().generate(r)
    def _validate(self,r,intent,result):
        call=super()._validate(r,intent,result)
        kind='final' if r.phase=='final' else 'packet'
        if json.loads(call.parameters_json)!=self.plan['frozen_arm']['parameters'][kind]:raise ValueError('Prespecified decoding changed')
        return call


class RoutedBackend:
    def __init__(self,backend,plan,root,stage,*,readonly=False,stop_after=None,before_new=lambda:None):
        self.backend=backend;self.identity=backend.identity;self.calls=[];self.generation_tokens={}
        self.collection=StudyJournal(backend,root/'collection',budgets()['collect'],plan,'fit',readonly=readonly or stage=='replay',
                                     stop_after=stop_after,before_new=before_new)
        pair_count=read_json(root/'candidate_support.json')['eligible_cells'] if stage=='replay' else 192
        self.replay=StudyJournal(backend,root/'replay',budgets(pair_count)['replay'],plan,'fit',readonly=readonly,
                                stop_after=stop_after,before_new=before_new) if stage=='replay' else None
    def generate(self,r):
        key=digest([digest([r,self.identity['snapshot']]),0])
        journal=self.collection if self.replay is None or key in self.collection.results else self.replay
        raw,call=journal.generate(r);self.calls.append(call)
        self.generation_tokens[digest(call)]=journal.last_generation
        return raw,call
    def count_tokens(self,text):return self.backend.count_tokens(text)
    def truncate(self,text,n):return self.backend.truncate(text,n)


def fitting_rows(plan):
    for e in plan['selection']:
        if e['partition']=='fit':
            task=task_from_dict(plan['tasks'][e['task_id']]);label=TaskLabel(e['task_id'],plan['labels'][e['task_id']]['answer_id'])
            for condition in plan['conditions']:
                raw=dict(plan['attacks'][task.task_id][condition]);raw.pop('schema_version',None)
                yield task,label,AttackRecord(**raw),digest([digest(plan),task.task_id,condition])


def anchor_candidates(protocol,task,label,attack):
    trajectory=protocol.run(task,'debate',attack)
    pools=[];support=[]
    for i in range(3):
        pool=tuple(protocol.private_packet(task,i,attack,node_seed(protocol.config.seed,trajectory.trajectory_id,i,'alternative',j)) for j in range(4))
        if any(p.call.messages!=trajectory.private[i].call.messages for p in pool):raise ValueError('Alternative context changed')
        pools.append(pool);support.append(choose_pair(pool,label.answer_id,32)[3] is None)
    return trajectory,pools,support


def collect(plan,backend,root,*,readonly=False,stop_after=None,before_new=lambda:None,after_row=lambda:None):
    journal=RoutedBackend(backend,plan,root,'collect',readonly=readonly,stop_after=stop_after,before_new=before_new)
    protocol=Protocol(runtime(plan),journal);rows=[]
    for task,label,attack,key in fitting_rows(plan):
        journal.generation_tokens.clear()
        saved=ShardStore(root/'anchors').read(key) if readonly else None
        count=saved['trajectory']['attack']['payload_tokens'] if saved else backend.count_tokens(attack.payload)
        if count>256:raise ValueError('Early payload cap exceeded')
        attack=dc.replace(attack,payload_tokens=count)
        tr,pools,mask=anchor_candidates(protocol,task,label,attack)
        value={'schema_version':1,'work_id':key,'trajectory':dc.asdict(tr),'candidates':[[dc.asdict(p) for p in pool] for pool in pools],'mask':mask}
        store=ShardStore(root/'anchors')
        if readonly:
            saved=store.read(key)
            if saved is None:raise ValueError('Missing anchor')
            value['trajectory']['readout_low_trust_tokens']=saved['trajectory']['readout_low_trust_tokens']
            if canonical(saved)!=canonical(value):raise ValueError('Anchor reconstruction mismatch')
        else:store.put(key,value)
        rows.append({'row_id':key,'task_id':task.task_id,'mask':mask})
        if not readonly:after_row()
    if set(journal.collection.results)!=journal.collection.seen:raise ValueError('Unused or unplanned collection calls')
    supported={r['task_id'] for r in rows if any(r['mask'])};multi={r['task_id'] for r in rows if sum(r['mask'])>=2}
    result={'rows':rows,'eligible_cells':sum(sum(r['mask']) for r in rows),'supported_tasks':len(supported),'multi_tasks':len(multi),
            'status':'ready_for_replay' if len(supported)>=8 and len(multi)>=8 else 'insufficient_assignment_support',
            'plan_hash':digest(plan)}
    if not readonly:immutable(root/'candidate_support.json',result)
    return result


def score_once(root,key,kind,request,callback,limit,*,readonly=False):
    intents=root/'score-intents';store=ShardStore(root/'scores');path=intents/f'{key}.json'
    contract={'work_id':key,'kind':kind,'request_hash':digest(request)}
    if path.exists():
        if read_json(path)!=contract:raise ValueError('Score identity changed')
        result=store.read(key)
        if result is None:raise ValueError('Unresolved scoring attempt')
        return result['score']
    if readonly:raise ValueError('Missing recorded NLL; no offline model forward')
    count=sum(read_json(p)['kind']==kind for p in intents.glob('*.json'))
    if count>=limit:raise ValueError('Scoring budget exhausted')
    write_json(path,contract)
    score=callback();store.put(key,{'schema_version':1,'work_id':key,'score':score})
    return score


def replay(plan,backend,root,*,readonly=False,stop_after=None,before_new=lambda:None,after_row=lambda:None):
    support=collect(plan,backend,root,readonly=True)
    if support['status']!='ready_for_replay':raise ValueError('insufficient_assignment_support: candidates stop before replay')
    journal=RoutedBackend(backend,plan,root,'replay',readonly=readonly,stop_after=stop_after,before_new=before_new)
    protocol=Protocol(runtime(plan),journal);records=[];rows=[]
    identity={'snapshot':backend.identity['snapshot'],'precision':backend.identity['precision'],
              'runtime_fingerprint':backend.identity['runtime_fingerprint'],'template_hash':backend.identity['template_hash'],
              'tokenizer_revision':backend.identity['tokenizer_revision'],'data_manifest_hash':digest(plan['source_manifest'])}
    for task,label,attack,key in fitting_rows(plan):
        journal.generation_tokens.clear()
        attack=dc.replace(attack,payload_tokens=ShardStore(root/'anchors').read(key)['trajectory']['attack']['payload_tokens'])
        tr=protocol.run(task,'debate',attack);pairs,_=probe(protocol,tr,label)
        # receiver_candidates is zero; probe must never dispatch receiver sampling.
        answer=[];packet=[]
        if not readonly:before_new()
        for i,private in enumerate(tr.private):
            request=[backend.identity,private.call.rendered_prompt,answer_target(label.answer_id),i]
            answer.append(score_once(root,digest([key,'answer',i]),'answer',request,
                lambda i=i,p=private:backend.scorer.answer_score(i,p.call.rendered_prompt,answer_target(label.answer_id)),192,readonly=readonly))
        for pair in pairs:
            if pair.status=='eligible':
                p=pair.candidates[pair.positive_index];tokens=journal.generation_tokens[digest(p.call)]
                s=score_once(root,digest([key,'packet',pair.agent]),'packet',[backend.identity,p,tokens],
                    lambda p=p,tokens=tokens,pair=pair:backend.scorer.token_score(f'agent{pair.agent}',p.call.rendered_prompt,tokens['prompt_ids'],p.raw,tokens['completion_ids']),
                    support['eligible_cells'],readonly=readonly)
                packet.append({'agent':pair.agent,'pair_id':pair.pair_id,**s})
        row={'row_id':key,'task_id':task.task_id,'split':'train','source_hash':task.source_hash,'label_hash':digest(label),
            'allowed_answers':[o.answer_id for o in task.options],'gold':label.answer_id,
            'initial_correct':[p.answer_id==label.answer_id and p.parser_status=='ok' for p in tr.private],
            'answer_nll':[s['mean_nll'] for s in answer],'delta':[p.delta for p in pairs],
            'private_pair_ids':[p.pair_id if p.status=='eligible' else None for p in pairs]}
        record={'schema_version':1,'work_id':key,'trajectory':dc.asdict(tr),'replays':[dc.asdict(p) for p in pairs],'row':row,
                'answer_scores':answer,'packet_scores':packet,'generation_tokens':dict(journal.generation_tokens)}
        normalized=reconstruct_record(record,identity)
        if readonly:
            saved=ShardStore(root/'bank').read(key)
            if saved is None:raise ValueError('Missing replay bank row')
            record['trajectory']['readout_low_trust_tokens']=saved['trajectory']['readout_low_trust_tokens']
            for actual_pair,saved_pair in zip(record['replays'],saved['replays']):
                for field in ('positive_suffixes','negative_suffixes'):
                    for actual_branch,saved_branch in zip(actual_pair[field],saved_pair[field]):
                        actual_branch['readout_low_trust_tokens']=saved_branch['readout_low_trust_tokens']
            if canonical(saved)!=canonical(record):raise ValueError('Replay bank reconstruction mismatch')
        else:ShardStore(root/'bank').put(key,record);after_row()
        records.append(record);rows.append(normalized)
    if set(journal.replay.results)!=journal.replay.seen or set(journal.collection.results)!=journal.collection.seen:
        raise ValueError('Unused or unplanned replay calls')
    if not readonly:
        immutable(root/'bank_manifest.json',{'plan_hash':digest(plan),'bank_hash':digest(records),'row_ids':[r['work_id'] for r in records],
                 'identity':identity,'pair_count':support['eligible_cells'],'natural_private_only':True})
    return rows,records
