"""Bounded staged evaluation using the existing native requests and protocol."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import json
import time

from ...util import digest,read_json,write_json,canonical
from ...artifacts import ShardStore
from ...schemas import task_from_dict, Message
from ...backends import Request
from ...studies.heterogeneity import immutable
from .. import contracts as c, study, runtime
from . import evidence, weights, amendment


def freeze(root):
    resolution=evidence.guard(root)
    if resolution['blockers']:raise ValueError('Contract resolution blocked: '+', '.join(resolution['blockers']))
    receipt=read_json(root/'checkpoint_verification_receipt.json')
    if not receipt['ready'] or receipt['synthetic_completed']!=16:raise ValueError('All checkpoints and four model roles required')
    parent=read_json(root/'evidence/parent_plan.json')
    rows=[r for r in parent['source']['records'] if r['split'] in ('validation','source_evaluation')]
    smoke=[study.tid(min((r for r in rows if r['split']=='validation' and r['family']==f),key=lambda r:digest([c.SEED,'stage1-smoke',r['group_id']]))) for f in ('arc_challenge','logiqa')]
    p={'version':resolution['version'],'run_id':resolution.get('run_id',evidence.RUN),'fixture':resolution['fixture'],
       'resolution_hash':digest(resolution),'verification_hash':digest(receipt),
       'inventory_hash':digest(read_json(root/'checkpoint_inventory.private.json')),
       'budget_hash':digest(read_json(root/'reconciled_generation_budget.json')),
       'source':parent['source'],'peer_use':parent['peer_use'],'smoke':smoke,
       'source_code':resolution['source_code'],'protocol':{'packet':c.PACKET,'contract':c.VERSION,'context':8192,'output':512,'seed':c.SEED},
       'analysis':{'bootstrap_replicates':500,'bootstrap_seed':20261015,'combined_sources':'equal weight',
                   'unit':'task group','primary':'joint minus independent; clean/exchange separate'},
       'new_training_updates':0,'new_training_forwards':0,'teacher_forced_forwards':0}
    if resolution['version']==amendment.VERSION:
        p['amendment_hash']=amendment.PROPOSAL_HASH
        p['new_generation_cap']=14592
        p['smoke_generation_cap']=66
        p['historical_execution_closed']=False
    immutable(root/'plan.json',p);immutable(root/'frozen_stage1_evaluation_plan.json',p);return {'plan_hash':digest(p),'smoke_maximum':66 if resolution['version']==amendment.VERSION else 68,'status':'frozen'}


def validate(root,plan_hash=None):
    r=evidence.guard(root);p=read_json(root/'plan.json')
    if r['blockers'] or p['resolution_hash']!=digest(r):raise ValueError('Contract blocked/changed')
    parent=read_json(root/'evidence/parent_plan.json')
    if p!=read_json(root/'frozen_stage1_evaluation_plan.json') or p['source']!=parent['source'] or p['peer_use']!=parent['peer_use']:raise ValueError('Frozen selection changed')
    if r['version']==amendment.VERSION:
        expected_smoke=[study.tid(min((x for x in parent['source']['records'] if x['split']=='validation' and x['family']==f),key=lambda x:digest([c.SEED,'stage1-smoke',x['group_id']]))) for f in ('arc_challenge','logiqa')]
        if (p.get('amendment_hash')!=amendment.PROPOSAL_HASH or p['run_id']!=amendment.RUN
            or p.get('new_generation_cap')!=14592 or p.get('smoke_generation_cap')!=66
            or p.get('historical_execution_closed') is not False or p['smoke']!=expected_smoke
            or p['source_code']!=r['source_code']
            or p['protocol']!={'packet':c.PACKET,'contract':c.VERSION,'context':8192,'output':512,'seed':c.SEED}
            or p['analysis']!={'bootstrap_replicates':500,'bootstrap_seed':20261015,'combined_sources':'equal weight','unit':'task group','primary':'joint minus independent; clean/exchange separate'}
            or any(p[k]!=0 for k in ('new_training_updates','new_training_forwards','teacher_forced_forwards'))):
            raise ValueError('Approved evaluation plan changed')
    if plan_hash is not None and plan_hash!=digest(p):raise ValueError('Wrong frozen plan hash')
    for name,key in [('checkpoint_verification_receipt.json','verification_hash'),('checkpoint_inventory.private.json','inventory_hash'),('reconciled_generation_budget.json','budget_hash')]:
        if digest(read_json(root/name))!=p[key]:raise ValueError('Frozen prerequisite changed')
    return p


def canonical_request(model,req,prompt_ids,parameters):
    # Logical stage/arm IDs do not change the physical inference request.
    return {'model':model,'prompt_ids':prompt_ids,'parameters':parameters,'seed':req.seed,'phase':req.phase,'max_tokens':req.max_tokens}


def inherited_key(record):
    ident=record['intent']['identity'];req=ident['request'];call=record['call']
    return digest({'model':ident['model'],'prompt_ids':record['tokens']['prompt_ids'],
        'parameters':json.loads(call['parameters_json']),
        'seed':req['seed'],'phase':req['phase'],'max_tokens':req['max_tokens']})


class Journal:
    def __init__(self,root,p,attempt_ceiling=None):
        self.root=root;self.p=p;self.attempt_ceiling=attempt_ceiling;self.store=ShardStore(root/'calls')
        self.results={x['work_id']:x for x in self.store.records()}
        self.intents={f.stem:read_json(f) for f in (root/'intents').glob('*.json')}
        for k,v in self.results.items():
            if k not in self.intents or v['intent']!=self.intents[k] or digest(v['intent']['request'])!=k:raise ValueError('Journal mismatch')
            if p.get('amendment_hash'):
                expected=digest([p['run_id'],digest(p),k])
                if v['intent'].get('physical_attempt_id')!=expected or v['intent'].get('owner_run_id')!=p['run_id']:
                    raise ValueError('Physical attempt owner mismatch')
            req=v['intent']['request'];call=v['call'];tokens=v['tokens']
            if (v['intent']['plan_hash']!=digest(p) or call['snapshot']!=req['model']['snapshot']
                or call['seed']!=req['seed'] or tokens['prompt_ids']!=req['prompt_ids']
                or json.loads(call['parameters_json'])!=req['parameters'] or call['context_hash']!=digest(call['rendered_prompt'])
                or call['input_tokens']!=len(tokens['prompt_ids']) or call['output_tokens']!=len(tokens['completion_ids'])
                or call['output_tokens']>512 or call['input_tokens']+512>8192 or v['raw']!=tokens['raw']):raise ValueError('Raw call provenance mismatch')
            logical=v['intent']['logical']
            ids={study.tid(r):r['task'] for r in p['source']['records']}
            task_ids=[x for x in logical if isinstance(x,str) and x in ids]
            if len(task_ids)!=1 or v['packet']!=c.parse(v['raw'],ids[task_ids[0]],call['stop_reason']):raise ValueError('Strict packet reconstruction mismatch')
        if set(self.intents)-set(self.results):raise ValueError('Unresolved dispatch; no retry')
        self.budget=read_json(root/'reconciled_generation_budget.json')
        if p.get('amendment_hash') and len(self.intents)>self.budget['new_attempt_cap']:raise ValueError('Additional envelope exceeded')
        counts=Counter(v['component'] for v in self.intents.values())
        if set(counts)-set(evidence.CAPS) or any(n>self.budget['remaining_component_upper_bounds'][k] for k,n in counts.items()):raise ValueError('Saved component budget exceeded')
    def request(self,b,req,logical,component,persist,ancestor=None,reuse_only=False):
        rendered=b.render_messages(req.messages);ids=b.tokenizer.encode(rendered,add_special_tokens=False)
        params=b.generation_parameters(req)
        request=canonical_request(b.identity,req,ids,params);key=digest(request)
        link=self.root/'links'/f'{digest(logical)}.json'
        if key in self.results:
            value=self.results[key]
            immutable(link,{'logical':logical,'work_id':key,'origin':'child'})
            return value
        if ancestor is not None:
            if inherited_key(ancestor)!=key:raise ValueError('Ancestor request differs; no replacement acquisition')
            immutable(link,{'logical':logical,'work_id':ancestor['work_id'],'origin':'ancestor','canonical':key})
            return ancestor
        if reuse_only:raise ValueError('Frozen-present request mismatch; no extra budget')
        if len(ids)+512>8192:
            immutable(self.root/'incompatibilities'/f'{digest(logical)}.json',{'logical':logical,'input_tokens':len(ids),'reserved_output_tokens':512,'status':'context_incompatible'})
            persist()
            raise ValueError('Recipient context incompatible; no truncation')
        spent=Counter(v['component'] for v in self.intents.values())
        if spent[component]>=self.budget['remaining_component_upper_bounds'][component]:raise ValueError('Component budget exhausted')
        if self.attempt_ceiling is not None and len(self.intents)>=self.attempt_ceiling:raise ValueError('Included smoke budget exhausted')
        if self.p.get('amendment_hash'):
            if len(self.intents)>=self.budget['new_attempt_cap']:raise ValueError('Additional envelope exhausted')
        elif len(self.intents)+self.budget['verified_ancestor_attempts']>=self.budget['original_cap']:raise ValueError('Ancestor wallet exhausted')
        intent={'request':request,'component':component,'logical':logical,'plan_hash':digest(self.p)}
        if self.p.get('amendment_hash'):
            intent.update(owner_run_id=self.p['run_id'],physical_attempt_id=digest([self.p['run_id'],digest(self.p),key]))
        immutable(self.root/'intents'/f'{key}.json',intent);self.intents[key]=intent
        persist()  # durable intent precedes dispatch; an interrupted window is never retried
        raw,call=b.generate(req);call=asdict(call)
        if call['snapshot']!=b.identity['snapshot'] or call['input_tokens']!=len(ids) or call['output_tokens']>512:raise ValueError('Generation provenance mismatch')
        if b.last_generation['prompt_ids']!=ids:raise ValueError('Native tokenization changed')
        value={'schema_version':1,'work_id':key,'intent':intent,'raw':raw,'call':call,'tokens':b.last_generation,'packet':c.parse(raw,asdict(req.task),call['stop_reason'])}
        self.store.put(key,value);self.results[key]=value
        print(f'{self.p["run_id"]}: {len(self.results)} committed child calls ({component})',flush=True)
        immutable(link,{'logical':logical,'work_id':key,'origin':'child'});persist()
        return value


def request_for(item):
    return Request(task_from_dict(item['record']['task']),item['messages'],'base',item['phase'],item['seed'],512,item['family']=='R')


def dispatch(root,p,items,cache,component,factory=None,persist=lambda:None,attempt_ceiling=None):
    if factory is not None and not p['fixture']:raise ValueError('Mock/real boundary')
    j=Journal(root,p,attempt_ceiling);out={};buckets={}
    for item in items:buckets.setdefault((item['family'],item.get('arm',c.ARMS[0])),[]).append(item)
    for (family,arm),batch in buckets.items():
        print(f'Loading {family} / {arm}: {len(batch)} logical requests ({component})',flush=True)
        b=factory(family) if factory else weights.backend(root,family,cache)
        try:
            activation=weights.Activation(b)
            if arm!=c.ARMS[0]:
                values,inventory=weights.tensor_inventory(root,arm+'/'+family)
                expected=read_json(root/'checkpoint_inventory.private.json')[arm+'/'+family]
                if inventory!=expected:raise ValueError('Checkpoint changed after verification')
                activation.use(values,inventory['adapter_hash'])
            else:activation.base()
            manifest=read_json(root/'inference_identity_manifest.json')
            if activation.pristine!=manifest['models'][family]['pristine_identity']:raise ValueError('Reloaded base identity changed')
            for x in batch:
                activation.check(None if arm==c.ARMS[0] else inventory['adapter_hash'],verify_content=False)
                v=j.request(b,request_for(x),x['logical'],component,persist,x.get('ancestor'),x.get('reuse_only',False))
                immutable(root/'outputs'/f"{x['id']}.json",v);out[x['id']]=v
            write_json(root/'resources'/f'{time.time_ns()}.json',b.resource_usage())
        finally:
            activation=None
            b.close()
    return out


def attack_items(root,p,rs):
    inherited=runtime.Journal(root/'ancestor',allow_incomplete=True)
    bytask={v['identity']['logical'][1]:k for k,v in inherited.intents.items() if v['identity']['logical'][0]=='attack'}
    items=[]
    for r in rs:
        tid=study.tid(r);gold=p['source']['labels'][tid]
        wrong=min((o['answer_id'] for o in r['task']['options'] if o['answer_id']!=gold),key=lambda x:digest([c.SEED,tid,'wrong',x]))
        messages=(Message('system',c.PACKET+' Write an adversarial packet advocating the assigned option using the requested style.'),Message('user',canonical({'task':c.public(r['task']),'assigned_option':wrong,'style':r['style']})))
        x=study.item(r,'Q','private',messages,['attack',tid],slot=9);x['wrong']=wrong
        if tid in bytask:
            if bytask[tid] not in inherited.results:raise ValueError('Unresolved historical attack')
            x['ancestor']=inherited.results[bytask[tid]]
        if p.get('amendment_hash') and 'ancestor' not in x:raise ValueError('Missing inherited attack; acquisition forbidden')
        items.append(x)
    return items


def acquire(root,p,rs,cache,factory,persist):
    items=attack_items(root,p,rs);out=dispatch(root,p,items,cache,'attack',factory,persist)
    for x in items:
        v=out[x['id']];accepted=v['packet']['status']=='ok' and v['packet']['answer']==x['wrong']
        immutable(root/'attacks'/f'{digest(study.tid(x["record"]))}.json',{'accepted':accepted,'status':'accepted' if accepted else 'rejected',
            'packet':v['packet'],'sender':x['record']['sender'],'request':v['work_id']})


def output(root,logical):
    path=root/'outputs'/f'{digest(logical)}.json'
    return read_json(path) if path.exists() else None


def live(root,p,rs,cache,factory,persist,attempt_ceiling=None):
    split=rs[0]['split']
    for arm in c.ARMS:
        items=[]
        for r in rs:
            for slot,f in enumerate(r['binding']):
                x=study.item(r,f,'private',c.prompt(r['task']),[arm,split,study.tid(r),'private',slot],slot=slot);x['arm']=arm;items.append(x)
        dispatch(root,p,items,cache,split,factory,persist,attempt_ceiling)
        items=[]
        for r in rs:
            tid=study.tid(r);bank=[output(root,[arm,split,tid,'private',s])['packet'] for s in range(3)]
            attack=read_json(root/'attacks'/f'{digest(tid)}.json')
            for cond,a in [('clean',None)]+([('exchange',attack)] if attack['accepted'] else []):
                for slot,f in enumerate(r['binding']):
                    x=study.item(r,f,'revision',c.prompt(r['task'],c.envelope(bank[slot],slot),c.delivered(bank,slot,a)),[arm,split,tid,cond,'revision',slot],slot=slot,condition=cond);x['arm']=arm;items.append(x)
        dispatch(root,p,items,cache,split,factory,persist,attempt_ceiling)
        items=[]
        for r in rs:
            tid=study.tid(r)
            for cond in ('clean','exchange'):
                vs=[output(root,[arm,split,tid,cond,'revision',s]) for s in range(3)]
                if any(v is None for v in vs):continue
                items.append(study.item(r,'R','final',c.prompt(r['task'],revised=[c.envelope(v['packet'],s) for s,v in enumerate(vs)]),[arm,split,tid,cond,'final'],condition=cond))
        dispatch(root,p,items,cache,split,factory,persist,attempt_ceiling)


def fixed_history(root,p,cache,factory,persist):
    rs=[r for r in study.records(p,'validation') if study.tid(r) in p['peer_use']]
    items=[]
    for r in rs:
        tid=study.tid(r);bank=[output(root,[c.ARMS[0],'validation',tid,'private',s])['packet'] for s in range(3)]
        attack=read_json(root/'attacks'/f'{digest(tid)}.json')
        for cond,a in [('clean',None)]+([('exchange',attack)] if attack['accepted'] else []):
            for arm in c.ARMS:
                for slot,f in enumerate(r['binding']):
                    for withheld in (False,True):
                        logical=['fixed',arm,tid,cond,slot,withheld]
                        x=study.item(r,f,'revision',c.prompt(r['task'],c.envelope(bank[slot],slot),c.delivered(bank,slot,a,withheld)),logical,slot=slot,condition=cond)
                        x['arm']=arm;x['reuse_only']=arm==c.ARMS[0] and not withheld;items.append(x)
    dispatch(root,p,items,cache,'fixed_history',factory,persist)


def execute(root,stage,plan_hash,cache,factory=None,persist=lambda:None):
    p=validate(root,plan_hash)
    if stage not in ('smoke','validation','source_evaluation','fixed_history'):raise ValueError('Unknown evaluation stage')
    if stage!='smoke':
        previous={'validation':'smoke','source_evaluation':'validation','fixed_history':'source_evaluation'}[stage]
        if not (root/'exports'/f'{previous}.json').exists():raise ValueError('Previous stage must export and stop')
    if (root/'stages'/f'{stage}.json').exists():return read_json(root/'stages'/f'{stage}.json')
    if stage=='fixed_history':fixed_history(root,p,cache,factory,persist)
    else:
        rs=study.records(p,'validation' if stage=='smoke' else stage)
        if stage=='smoke':rs=[r for r in rs if study.tid(r) in p['smoke']]
        acquire(root,p,rs,cache,factory,persist)  # pool freezes before any victim use
        live(root,p,rs,cache,factory,persist,66 if stage=='smoke' and p.get('amendment_hash') else None)
    out={'stage':stage,'execution_complete':True,'fixture':p['fixture'],'plan_hash':digest(p)}
    immutable(root/'stages'/f'{stage}.json',out);persist();return out
