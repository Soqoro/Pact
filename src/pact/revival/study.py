"""Bounded Stage I collection, six-adapter training and matched receiver evaluation."""
from dataclasses import asdict
from pathlib import Path
import json
import time
from collections import Counter
from ..util import digest,read_json,write_json,canonical,node_seed
from ..schemas import task_from_dict
from ..backends import Request
from ..studies.heterogeneity import immutable
from ..environment import code_identity
from . import contracts as c,neural,runtime


def records(plan,split):return [r for r in plan['source']['records'] if r['split']==split]
def tid(r):return r['task']['task_id']
def seed(r,phase,slot=0,condition='',repeat=0):return node_seed(c.SEED,tid(r),phase,str(slot),condition,str(repeat))


def plan(root,source):
    from ..studies.forensics import private_root
    private_root(root,source['fixture'])
    if (root/'plan.json').exists():raise ValueError('Never re-plan existing run')
    from .data import validate_source
    validate_source(source)
    p={'version':c.VERSION,'run_id':c.RUN,'source':source,'source_code':code_identity(Path(__file__).resolve().parents[3]),'contract':c.budget_arithmetic()}
    p['smoke']=[min((r for r in records(p,'main_fit') if r['family']==f),key=lambda r:digest([c.SEED,'smoke',r['group_id']]))['task']['task_id'] for f in ('arc_challenge','logiqa')]
    p['peer_use']=[tid(r) for f in ('arc_challenge','logiqa') for r in sorted((x for x in records(p,'validation') if x['family']==f),key=lambda r:digest([c.SEED,'peer-use',r['group_id']]))[:32]]
    immutable(root/'plan.json',p);return {'plan_hash':digest(p),'budgets':c.BUDGETS,'source_counts':dict(Counter(r['split'] for r in source['records']))}


def guard(root,plan_hash,fixture=False):
    p=read_json(root/'plan.json')
    if digest(p)!=plan_hash or p['version']!=c.VERSION or p['source']['fixture']!=fixture:raise ValueError('Frozen plan/fixture mismatch')
    if not fixture and p['source_code']!=code_identity(Path(__file__).resolve().parents[3]):raise ValueError('Source changed; no implicit migration')
    return p


def trained(root,arm,family):return root/'training'/arm/family


def checkpoint_for(root,arm,family):
    if arm==c.ARMS[0] or family=='R':return None
    path=trained(root,arm,family);ep=read_json(path/'epoch2.json');status=read_json(path/'status.json')
    if not status['complete'] or ep['adapter_hash']!=status['adapter_hash']:raise ValueError('Fixed epoch2 checkpoint required')
    team=root/'teams'/f'{arm}.json'
    if team.exists() and read_json(team)['adapters'][family]!=ep:raise ValueError('Frozen team checkpoint changed')
    return path


def load_backend(root,family,cache,checkpoint=None,factory=None):
    if factory:return factory(family,checkpoint)
    return runtime.Backend(family,read_json(root/'access.json')[family],cache,checkpoint)


def dispatch(root,p,items,cache,factory=None,stage='I',persistent=None):
    """Items have full dependencies and are grouped by checkpoint/family; one resident model."""
    journal=runtime.Journal(root,stage);out={}
    buckets={}
    for item in items:buckets.setdefault((item['family'],str(item.get('checkpoint') or '')),[]).append(item)
    for (family,checkpoint),batch in buckets.items():
        backend=load_backend(root,family,cache,Path(checkpoint) if checkpoint else None,factory)
        try:
            immutable(root/'identities'/f"{digest(backend.identity)}.json",backend.identity)
            for x in batch:
                r=x['record'];task=task_from_dict(r['task'])
                req=Request(task,x['messages'],'base',x['phase'],x['seed'],512,family=='R')
                value=journal.request(backend,req,x['logical'],persistent);out[x['id']]=value
                if len(journal.results)%32==0:runtime.checkpoint(root,persistent)
            write_json(root/'resources'/f'{time.time_ns()}.json',backend.resource_usage())
        finally:backend.close()
    return out


def item(r,family,phase,messages,logical,*,slot=0,condition='',repeat=0,checkpoint=None):
    return {'record':r,'family':family,'phase':phase,'messages':messages,'logical':logical,'id':digest(logical),
            'seed':seed(r,phase,slot,condition,repeat),'checkpoint':checkpoint}


def collect_fit(root,p,cache,smoke=False,factory=None,persistent=None):
    if not smoke and not (root/'source_smoke_export.json').exists():raise ValueError('Export and review included source smoke first')
    items=[]
    for r in records(p,'main_fit'):
        if smoke and tid(r) not in p['smoke']:continue
        for slot,f in enumerate(r['binding']):items.append(item(r,f,'private',c.prompt(r['task']),['fit',tid(r),slot],slot=slot))
    out=dispatch(root,p,items,cache,factory,persistent=persistent)
    for x in items:immutable(root/'fit_private'/f"{x['id']}.json",out[x['id']])
    if smoke:immutable(root/'source_smoke.json',{'requests':sorted(out),'included_calls':6})
    else:immutable(root/'fit_complete.json',{'requests':sorted(out)})
    return {'committed_fit_private':len(out)}


def attacks(root,p,cache,*,probe=False,factory=None,persistent=None):
    rows=records(p,'allocation_probe') if probe else [r for r in p['source']['records'] if r['split']!='allocation_probe']
    items=[]
    for r in rows:
        choices=[o['answer_id'] for o in r['task']['options'] if o['answer_id']!=p['source']['labels'][tid(r)]]
        wrong=min(choices,key=lambda x:digest([c.SEED,tid(r),'wrong',x]))
        from ..schemas import Message
        messages=(Message('system',c.PACKET+' Write an adversarial packet advocating the assigned option using the requested style.'),Message('user',canonical({'task':c.public(r['task']),'assigned_option':wrong,'style':r['style']})))
        x=item(r,'Q','private',messages,['attack',tid(r)],slot=9);x['wrong']=wrong;items.append(x)
    out=dispatch(root,p,items,cache,factory,'II' if probe else 'I',persistent)
    for x in items:
        v=out[x['id']];packet=v['packet'];accepted=packet['status']=='ok' and packet['answer']==x['wrong']
        immutable(root/'attacks'/f"{digest(tid(x['record']))}.json",{'accepted':accepted,'reason':None if accepted else 'schema_or_wrong_target_mismatch','packet':packet,'sender':x['record']['sender'],'request':v['work_id']})
    return {'attempts':len(out),'accepted':sum(read_json(root/'attacks'/f'{digest(tid(r))}.json')['accepted'] for r in rows)}


def attack_for(root,r):
    v=read_json(root/'attacks'/f'{digest(tid(r))}.json');return v if v['accepted'] else None


def fit_bank(root,p,*,inspect_only=False):
    read_json(root/'fit_complete.json');n=len(records(p,'main_fit'));bank={};support={}
    for f in c.FAMILIES:
        rows=[];raw=[]
        for r in records(p,'main_fit'):
            private=[read_json(root/'fit_private'/f"{digest(['fit',tid(r),slot])}.json")['packet'] for slot in range(3)]
            slot=r['binding'].index(f);gold=p['source']['labels'][tid(r)];attack=attack_for(root,r)
            for cond,a in [('clean',None)]+([('exchange',attack)] if attack else []):
                st=c.stratum(private,slot,gold,a);rows.append((tid(r),cond,st));raw.append((r,private,slot,a,cond,st))
        ws,support[f]=c.weights(rows);bank[f]=[]
        for r,private,slot,a,cond,st in raw:
            bank[f].append({'task_id':tid(r),'condition':cond,'stratum':st,'weight':ws[digest((tid(r),cond,st))],
                'gold':p['source']['labels'][tid(r)],'invalid_own':private[slot]['status']!='ok',
                'joint':[asdict(m) for m in c.prompt(r['task'],c.envelope(private[slot],slot),c.delivered(private,slot,a))],
                'independent':[asdict(m) for m in c.prompt(r['task'],c.envelope(private[slot],slot),c.delivered(private,slot,a,True))]})
    for f in c.FAMILIES:
        for cond in support[f]:
            support[f][cond]['invalid_own_tasks']=len({r['task_id'] for r in bank[f] if r['condition']==cond and r['invalid_own']})
    value={'version':c.VERSION,'plan_hash':digest(p),'bank':bank,'support':support,'tasks':n,'specialization_weight':0,'dpo':False}
    if inspect_only:return value
    immutable(root/'training_bank.json',value);return {'tasks':n,'support':support}


def groups_for(root,p,backend,family,arm,selected=None,private_only=False):
    from ..schemas import Message
    rs=records(p,'main_fit')
    if selected is not None and not set(selected)<={tid(r) for r in rs}:raise ValueError('Only fitting groups may supply gradients')
    rs=[r for r in rs if selected is None or tid(r) in selected];n=len(rs)
    if not n:raise ValueError('Empty fitting groups')
    bank=read_json(root/'training_bank.json')['bank'][family] if not private_only else []
    groups=[]
    for r in rs:
        allowed=[o['answer_id'] for o in r['task']['options']];gold=p['source']['labels'][tid(r)]
        def target(messages):return neural.prefix_target(backend.tokenizer,backend.render_messages(messages),gold,allowed)
        contexts=[{'role':'private','target':target(c.prompt(r['task'])),'weight':(1. if private_only else .5)/n}]
        if not private_only:
            for row in bank:
                if row['task_id']==tid(r):
                    messages=tuple(Message(m['role'],m['content']) for m in row['independent' if arm==c.ARMS[1] else 'joint'])
                    contexts.append({'role':row['condition'],'target':target(messages),'weight':.5*row['weight']})
        groups.append({'task_id':tid(r),'contexts':contexts})
    return groups


def train_agent(root,p,cache,arm,family,*,resume=False,factory=None,persistent=None,initial_check=None,stop_after=None):
    if arm not in c.ARMS[1:] or family not in c.FAMILIES:raise ValueError('Train all Q/L/M on one declared arm')
    if not (root/'sanity_complete.json').exists():raise ValueError('Bounded scratch training sanity must complete first')
    backend=load_backend(root,family,cache,None,factory)
    try:
        shapes=neural.attach(backend.model,c.SEED+c.FAMILIES.index(family))
        if hasattr(backend.model,'gradient_checkpointing_enable'):
            backend.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
        if initial_check is not None:initial_check(backend)
        gs=groups_for(root,p,backend,family,arm)
        identity={'plan':digest(p),'family':family,'arm':arm,'native':backend.identity,'shapes':shapes}
        immutable(root/'initializations'/f'{family}.json',{'hash':neural._weights_hash(neural.parameters(backend.model)),'shapes':shapes})
        started=time.monotonic()
        out=neural.train(backend.model,gs,trained(root,arm,family),identity,resume=resume,stop_after=stop_after,callback=lambda:runtime.checkpoint(root,persistent))
        write_json(trained(root,arm,family)/'resources.json',{'invocation_seconds':time.monotonic()-started,**backend.resource_usage()})
        return out
    finally:backend.close()


def freeze(root,p,arm):
    refs={f:read_json(checkpoint_for(root,arm,f)/'epoch2.json') for f in c.FAMILIES}
    immutable(root/'teams'/f'{arm}.json',{'plan':digest(p),'arm':arm,'fixed_epoch':2,'adapters':refs})
    return {'team_hash':digest(refs)}


def live(root,p,cache,arm,split,*,factory=None,persistent=None,repeat=0,selected=None,branch=None,stage='I'):
    if split not in ('validation','source_evaluation','allocation_probe'):raise ValueError('Not an evaluation split')
    if arm!=c.ARMS[0]:read_json(root/'teams'/f'{arm}.json')
    rs=records(p,split);rs=[r for r in rs if selected is None or tid(r) in selected]
    tag=[arm,split,repeat,branch['id'] if branch else 'baseline'];base_tag=[arm,split,repeat,'baseline']
    private={};items=[]
    for r in rs:
        for slot,f in enumerate(r['binding']):
            logical=[*tag,tid(r),'private',slot]
            if branch and f!=branch['family']:
                private[tid(r),slot]=read_json(root/'outputs'/f"{digest([*base_tag,tid(r),'private',slot])}.json")
                continue
            cp=branch['checkpoint'] if branch and f==branch['family'] else checkpoint_for(root,arm,f)
            items.append(item(r,f,'private',c.prompt(r['task']),logical,slot=slot,repeat=repeat,checkpoint=cp))
    out=dispatch(root,p,items,cache,factory,stage,persistent)
    for x in items:
        v=out[x['id']];immutable(root/'outputs'/f"{x['id']}.json",v);private[tid(x['record']),x['logical'][-1]]=v
    revisions={};items=[]
    for r in rs:
        bank=[private[tid(r),s]['packet'] for s in range(3)];attack=attack_for(root,r)
        for condition,a in [('clean',None)]+([('exchange',attack)] if attack else []):
            for slot,f in enumerate(r['binding']):
                cp=branch['checkpoint'] if branch and f==branch['family'] else checkpoint_for(root,arm,f)
                logical=[*tag,tid(r),condition,'revision',slot]
                items.append(item(r,f,'revision',c.prompt(r['task'],c.envelope(bank[slot],slot),c.delivered(bank,slot,a)),logical,slot=slot,condition=condition,repeat=repeat,checkpoint=cp))
    out=dispatch(root,p,items,cache,factory,stage,persistent)
    for x in items:
        v=out[x['id']];immutable(root/'outputs'/f"{x['id']}.json",v);revisions[tid(x['record']),x['logical'][-3],x['logical'][-1]]=v
    items=[]
    for r in rs:
        for condition in ('clean','exchange'):
            if (tid(r),condition,0) not in revisions:continue
            messages=c.prompt(r['task'],revised=[c.envelope(revisions[tid(r),condition,s]['packet'],s) for s in range(3)])
            items.append(item(r,'R','final',messages,[*tag,tid(r),condition,'final'],condition=condition,repeat=repeat))
    out=dispatch(root,p,items,cache,factory,stage,persistent)
    for x in items:immutable(root/'outputs'/f"{x['id']}.json",out[x['id']])
    result=[]
    for r in rs:
        gold=p['source']['labels'][tid(r)]
        initial=[private[tid(r),s]['packet']['answer']==gold for s in range(3)]
        for cond in ('clean','exchange'):
            key=digest([*tag,tid(r),cond,'final']);v=out.get(key)
            revised=[revisions[tid(r),cond,s]['packet']['answer']==gold for s in range(3)] if v else None
            result.append({'task_id':tid(r),'group_id':r['group_id'],'family':r['family'],'arm':arm,'split':split,'condition':cond,'repeat':repeat,
                'binding':r['binding'],'receiver_strata':[c.stratum([private[tid(r),z]['packet'] for z in range(3)],slot,gold,attack_for(root,r) if cond=='exchange' else None) for slot in range(3)] if v else None,
                'missing':v is None,'initial':initial,'revised':revised,'final':v['packet']['answer']==gold if v else None,'readout_key':v['work_id'] if v else None})
    immutable(root/'evaluations'/f'{digest(tag)}.json',{'tag':tag,'rows':result})
    return result


def sanity(root,p,cache,factory=None,persistent=None):
    """Disposable 16 steps/family, two included-source task generations; rollback always."""
    import torch
    for f in c.FAMILIES:
        path=root/'sanity'/f
        if (path/'receipt.json').exists():continue
        backend=load_backend(root,f,cache,None,factory)
        try:
            neural.attach(backend.model,c.SEED+c.FAMILIES.index(f));start={n:v.detach().clone() for n,v in neural.parameters(backend.model).items()};rng=neural._rng_state()
            gs=groups_for(root,p,backend,f,c.ARMS[2],p['smoke'],True)
            initial=neural._weights_hash(start)
            try:
                status=neural.train(backend.model,gs,path,{'family':f,'role':'scratch','plan':digest(p),'native':backend.identity},epochs=8,batch=1,warmup=0,resume=(path/'contract.json').exists(),callback=lambda:runtime.checkpoint(root,persistent))
                backend.identity={**backend.identity,'scratch_adapter':status['adapter_hash']};backend.identity['snapshot']=digest(backend.identity)
                j=runtime.Journal(root)
                outputs=[]
                for r in records(p,'main_fit'):
                    if tid(r) not in p['smoke']:continue
                    req=Request(task_from_dict(r['task']),c.prompt(r['task']),'base','private',seed(r,'private',r['binding'].index(f)),512,False)
                    outputs.append(j.request(backend,req,['scratch',f,tid(r)],persistent)['work_id'])
            finally:
                neural.restore_parameters(backend.model,start);neural._restore_rng(rng)
            immutable(path/'receipt.json',{'initial':initial,'restored':neural._weights_hash(neural.parameters(backend.model)),'outputs':outputs,'status':status})
        finally:backend.close()
    immutable(root/'sanity_complete.json',{'families':list(c.FAMILIES),'scratch_steps':48,'post_update_generations':6})
    return read_json(root/'sanity_complete.json')


def peer_use(root,p,cache,arm,factory=None,persistent=None):
    rs=[r for r in records(p,'validation') if tid(r) in p['peer_use']];items=[];rows=[]
    for r in rs:
        base=[c.ARMS[0],'validation',0,'baseline'];bank=[read_json(root/'outputs'/f"{digest([*base,tid(r),'private',s])}.json")['packet'] for s in range(3)]
        attack=attack_for(root,r)
        for cond,a in [('clean',None)]+([('exchange',attack)] if attack else []):
            for slot,f in enumerate(r['binding']):
                for withheld in (False,True):
                    logical=['peer_use',arm,tid(r),cond,slot,withheld]
                    if arm==c.ARMS[0] and not withheld:
                        v=read_json(root/'outputs'/f"{digest([*base,tid(r),cond,'revision',slot])}.json")
                        rows.append({'task_id':tid(r),'group_id':r['group_id'],'condition':cond,'slot':slot,'withheld':withheld,'correct':v['packet']['answer']==p['source']['labels'][tid(r)],'reused':True})
                    else:items.append(item(r,f,'revision',c.prompt(r['task'],c.envelope(bank[slot],slot),c.delivered(bank,slot,a,withheld)),logical,slot=slot,condition=cond,checkpoint=checkpoint_for(root,arm,f)))
    out=dispatch(root,p,items,cache,factory,persistent=persistent)
    for x in items:
        v=out[x['id']];r=x['record'];rows.append({'task_id':tid(r),'group_id':r['group_id'],'condition':x['logical'][3],'slot':x['logical'][4],'withheld':x['logical'][5], 'correct':v['packet']['answer']==p['source']['labels'][tid(r)],'reused':False,'key':v['work_id']})
    immutable(root/'peer_use'/f'{arm}.json',rows);return {'arm':arm,'views':len(rows),'new_calls':len(items)}


def report(root):
    from ..selective.diagnostics import clustered_interval
    p=read_json(root/'plan.json');j=runtime.Journal(root,allow_incomplete=True);metrics={}
    for path in (root/'evaluations').glob('*.json'):
        ev=read_json(path);tag=ev['tag']
        if tag[1]=='allocation_probe':continue
        for cond in ('clean','exchange'):
            rows=[r for r in ev['rows'] if r['condition']==cond];ok=[r for r in rows if not r['missing']]
            initial=[sum(r['initial']) for r in ok];revised=[sum(r['revised']) for r in ok]
            metrics['/'.join(map(str,tag+[cond]))]={'intended':len(rows),'observed':len(ok),'missing':len(rows)-len(ok),
                'final_correct':sum(r['final'] for r in ok),'accuracy_interval':clustered_interval([(r['family'],r['group_id'],float(r['final'])) for r in ok]),
                'accuracy_bounds':[sum(r['final'] for r in ok)/len(rows),(sum(r['final'] for r in ok)+len(rows)-len(ok))/len(rows)] if rows else None,
                'private_correct':[sum(r['initial'][s] for r in ok) for s in range(3)],'initial_coverage':sum(n>0 for n in initial),
                'transitions':dict(Counter(f'{a}->{b}' for a,b in zip(initial,revised))),
                'erasure':sum(a>0 and b==0 for a,b in zip(initial,revised)), 'construction':sum(not any(r['revised']) and r['final'] for r in ok),
                'readout_loss':sum(any(r['revised']) and not r['final'] for r in ok),
                'hold_opportunities':sum(st=='hold_conflict' for r in ok for st in r['receiver_strata']),
                'held':sum(st=='hold_conflict' and y for r in ok for st,y in zip(r['receiver_strata'],r['revised'])),
                'repair_opportunities':sum(st=='repair_available' for r in ok for st in r['receiver_strata']),
                'repaired':sum(st=='repair_available' and y for r in ok for st,y in zip(r['receiver_strata'],r['revised'])),
                'private_by_family':{f:sum(r['initial'][r['binding'].index(f)] for r in ok) for f in c.FAMILIES},
                'coverage_beyond_best_family':sum(n>0 for n in initial)-max((sum(r['initial'][r['binding'].index(f)] for r in ok) for f in c.FAMILIES),default=0)}
    peer={}
    for path in (root/'peer_use').glob('*.json'):
        rows=read_json(path);peer[path.stem]={}
        for cond in ('clean','exchange'):
            by={(r['task_id'],r['slot'],r['withheld']):r for r in rows if r['condition']==cond}
            diffs=[int(r['correct'])-int(by[t,s,True]['correct']) for (t,s,w),r in by.items() if not w and (t,s,True) in by]
            peer[path.stem][cond]={'paired_receivers':len(diffs),'present_minus_withheld':sum(diffs)/len(diffs) if diffs else None}
    interaction={cond:(peer.get(c.ARMS[2],{}).get(cond,{}).get('present_minus_withheld'),peer.get(c.ARMS[1],{}).get(cond,{}).get('present_minus_withheld')) for cond in ('clean','exchange')}
    interaction={k:(a-b if a is not None and b is not None else None) for k,(a,b) in interaction.items()}
    paired={}
    evs={tuple(v['tag']):v['rows'] for path in (root/'evaluations').glob('*.json') if (v:=read_json(path))['tag'][1]!='allocation_probe'}
    for split in ('validation','source_evaluation'):
        for a,b in ((c.ARMS[0],c.ARMS[1]),(c.ARMS[0],c.ARMS[2]),(c.ARMS[1],c.ARMS[2])):
            before={(r['task_id'],r['condition']):r for r in evs.get((a,split,0,'baseline'),[])}
            after={(r['task_id'],r['condition']):r for r in evs.get((b,split,0,'baseline'),[])}
            for cond in ('clean','exchange'):
                pairs=[(x,after[k]) for k,x in before.items() if k in after and k[1]==cond and not x['missing'] and not after[k]['missing']]
                diffs=[(x['family'],x['group_id'],int(y['final'])-int(x['final'])) for x,y in pairs]
                paired[f'{split}/{a}->{b}/{cond}']={'paired_tasks':len(pairs),'gain':sum(not x['final'] and y['final'] for x,y in pairs),'loss':sum(x['final'] and not y['final'] for x,y in pairs),'interval':clustered_interval(diffs)}
    formats={}
    for r in j.results.values():
        ident=r['intent']['identity'];key=ident['budget_stage']+'/'+ident['model'].get('family',ident['model'].get('spec',{}).get('key','unknown'))+'/'+r['call']['phase']
        x=formats.setdefault(key,{'calls':0,'valid':0,'abstain':0,'invalid':0,'length_stops':0,'justification_characters':0})
        x['calls']+=1;x['valid']+=r['packet']['status']=='ok';x['abstain']+=r['packet']['status']=='abstention';x['invalid']+=r['packet']['status']=='invalid';x['length_stops']+=r['call']['stop_reason']=='length';x['justification_characters']+=len(r['packet']['justification'])
    training={f'{arm}/{f}':read_json(trained(root,arm,f)/'status.json') for arm in c.ARMS[1:] for f in c.FAMILIES if (trained(root,arm,f)/'status.json').exists()}
    summary={'run_id':c.RUN,'fixture':p['source']['fixture'],'plan_hash':digest(p),'scientific_status':'mock_only' if p['source']['fixture'] else 'development_training_study',
             'generation':{'attempted':len(j.intents),'committed':len(j.results),'unresolved':len(set(j.intents)-set(j.results)),'reserved_tokens':512*len(j.intents),'input_tokens':sum(r['call']['input_tokens'] for r in j.results.values()),'output_tokens':sum(r['call']['output_tokens'] for r in j.results.values())},
             'training':{k:{s:v[s] for s in ('complete','completed_steps','forwards')} for k,v in training.items()},'live':metrics,'paired_team_outcomes':paired,'format_and_length':formats,'off_policy_peer_use':peer,'joint_minus_independent_peer_interaction':interaction,'compute_units':None,'full_pact_executed':False}
    summary['stage_i_complete']=not summary['generation']['unresolved'] and len(training)==6 and all(v['complete'] for v in training.values()) and len(metrics)==12 and len(peer)==3
    write_json(root/'summary.json',summary);return summary
