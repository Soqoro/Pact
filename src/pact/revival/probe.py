"""Separately frozen actual-update assay. Temporary private updates never become team training."""
from pathlib import Path
from collections import defaultdict
from ..util import digest,read_json,write_json,file_hash
from ..studies.heterogeneity import immutable
from ..training.assignment import solve_assignment
from . import contracts as c,study as s,neural,runtime


def plan(root,p,review_sha):
    summary=s.report(root)
    if not summary['stage_i_complete'] or file_hash(root/'summary.json')!=review_sha:raise ValueError('Completed artifact-bound Stage I review required')
    immutable(root/'reviewed_stage_i_summary.json',summary)
    team=read_json(root/'teams'/f'{c.ARMS[2]}.json')
    value={'run_id':c.PROBE,'parent_plan':digest(p),'review_sha':review_sha,'fixed_joint_team':team,'blocks':p['source']['blocks'],'seeds':[0,1],'budget':c.BUDGETS['II']}
    immutable(root/'probe_plan.json',value);return {'probe_plan_hash':digest(value),'budget':c.BUDGETS['II']}


def guard(root,h):
    v=read_json(root/'probe_plan.json')
    if file_hash(root/'reviewed_stage_i_summary.json')!=v['review_sha']:raise ValueError('Reviewed Stage I summary changed')
    if digest(v)!=h or read_json(root/'teams'/f'{c.ARMS[2]}.json')!=v['fixed_joint_team']:raise ValueError('Probe plan/team changed')
    return v


def collect(root,p,cache,factory=None,persistent=None):
    s.attacks(root,p,cache,probe=True,factory=factory,persistent=persistent)
    for repeat in (0,1):s.live(root,p,cache,c.ARMS[2],'allocation_probe',factory=factory,persistent=persistent,repeat=repeat,stage='II')
    return {'base_complete':True}


def temporary(root,p,cache,block,family,factory=None,persistent=None):
    b=read_json(root/'probe_plan.json')['blocks'][block]
    if family not in c.FAMILIES:raise ValueError('Unknown actor')
    path=root/'probe_training'/f'block-{block}'/family
    if (path/'rollback.json').exists():return read_json(path/'rollback.json')
    backend=s.load_backend(root,family,cache,s.checkpoint_for(root,c.ARMS[2],family),factory)
    try:
        initial={n:t.detach().clone() for n,t in neural.parameters(backend.model).items()};h=neural._weights_hash(initial);rng=neural._rng_state()
        try:
            groups=s.groups_for(root,p,backend,family,c.ARMS[2],b['fit'],True)
            if set(b['fit'])&set(b['probe']):raise ValueError('Probe/train leakage')
            status=neural.train(backend.model,groups,path,{'family':family,'block':block,'probe_plan':digest(read_json(root/'probe_plan.json')),'native':backend.identity},epochs=1,batch=8,warmup=0,resume=(path/'contract.json').exists(),callback=lambda:runtime.checkpoint(root,persistent))
        finally:
            neural.restore_parameters(backend.model,initial);neural._restore_rng(rng)
        receipt={'initial_hash':h,'restored_hash':neural._weights_hash(neural.parameters(backend.model)),'temporary_hash':status['adapter_hash'],'temporary_steps':status['completed_steps'],'training_task_count':len(b['fit']),'probe_training_tokens':0}
        if receipt['initial_hash']!=receipt['restored_hash']:raise ValueError('Failed rollback')
        immutable(path/'rollback.json',receipt);return receipt
    finally:backend.close()


def evaluate(root,p,cache,block,family,factory=None,persistent=None):
    path=root/'probe_training'/f'block-{block}'/family;read_json(path/'rollback.json')
    ids=read_json(root/'probe_plan.json')['blocks'][block]['probe']
    branch={'id':f'block-{block}-{family}','family':family,'checkpoint':path}
    for repeat in (0,1):s.live(root,p,cache,c.ARMS[2],'allocation_probe',factory=factory,persistent=persistent,repeat=repeat,selected=ids,branch=branch,stage='II')
    return {'block':block,'family':family,'complete':True}


def score(root,p,cache,factory=None,persistent=None):
    """1024 terminal +768 local maximum; every NLL uses only masked answer-prefix targets."""
    items=[];probe_plan=read_json(root/'probe_plan.json');lookup={s.tid(r):r for r in s.records(p,'allocation_probe')}
    for bi,b in enumerate(probe_plan['blocks']):
        for tid in b['probe']:
            r=lookup[tid]
            for repeat in (0,1):
                for branch in ['baseline',*[f'block-{bi}-{f}' for f in c.FAMILIES]]:
                    tag=[c.ARMS[2],'allocation_probe',repeat,branch]
                    for cond in ('clean','exchange'):
                        if cond=='exchange' and s.attack_for(root,r) is None:continue
                        path=root/'outputs'/f"{digest([*tag,tid,cond,'final'])}.json"
                        result=read_json(path);messages=result['intent']['identity']['request']['messages']
                        items.append({'family':'R','checkpoint':None,'messages':messages,'record':r,'key':['terminal',bi,tid,repeat,branch,cond]})
                for f in c.FAMILIES:
                    for mode in ('before','after'):
                        cp=s.checkpoint_for(root,c.ARMS[2],f) if mode=='before' else root/'probe_training'/f'block-{bi}'/f
                        items.append({'family':f,'checkpoint':cp,'messages':[s.asdict(m) for m in c.prompt(r['task'])], 'record':r,'key':['local',bi,tid,repeat,f,mode]})
    from ..artifacts import ShardStore
    store=ShardStore(root/'probe_scores');buckets={}
    for x in items:buckets.setdefault((x['family'],str(x['checkpoint'] or '')),[]).append(x)
    for (f,cp),xs in buckets.items():
        backend=s.load_backend(root,f,cache,Path(cp) if cp else None,factory)
        try:
            backend.model.eval()
            for x in xs:
                identity={'logical':x['key'],'model':backend.identity,'messages':x['messages'],'probe_plan':digest(probe_plan)};key=digest(identity)
                if store.read(key) is not None:continue
                intent=root/'score_intents'/f'{key}.json'
                if intent.exists():raise ValueError('Unresolved scoring forward; no automatic retry')
                if len(list((root/'score_intents').glob('*.json')))>=1792:raise ValueError('Diagnostic scoring cap')
                from ..schemas import Message
                messages=tuple(Message(v['role'],v['content']) for v in x['messages']);r=x['record']
                target=neural.prefix_target(backend.tokenizer,backend.render_messages(messages),p['source']['labels'][s.tid(r)],[o['answer_id'] for o in r['task']['options']])
                write_json(intent,identity);runtime.checkpoint(root,persistent)
                import torch
                with torch.no_grad():value=float(neural.loss(backend.model,target))
                import math
                if not math.isfinite(value):raise ValueError('Nonfinite diagnostic score')
                store.put(key,{'schema_version':1,'work_id':key,'identity':identity,'nll':value,'gold_generation_input':False})
        finally:backend.close()
    return {'score_forwards':len(store.records())}


def assignments(root):
    from ..artifacts import ShardStore
    scores={tuple(r['identity']['logical']):r['nll'] for r in ShardStore(root/'probe_scores').records()}
    pp=read_json(root/'probe_plan.json');terminal=[];local=[];details=[]
    for bi,b in enumerate(pp['blocks']):
        ts=[];ls=[]
        for f in c.FAMILIES:
            diffs=[];ld=[];per_task=[]
            for tid in b['probe']:
                task=[]
                for repeat in (0,1):
                    for cond in ('clean','exchange'):
                        k=('terminal',bi,tid,repeat,'baseline',cond);z=('terminal',bi,tid,repeat,f'block-{bi}-{f}',cond)
                        if k in scores and z in scores:task.append(scores[k]-scores[z])
                    a=('local',bi,tid,repeat,f,'before');z=('local',bi,tid,repeat,f,'after')
                    if a in scores and z in scores:ld.append(scores[a]-scores[z])
                if len(task)==4:per_task.append(sum(task)/len(task))
            ts.append(sum(per_task)/len(per_task) if len(per_task)==len(b['probe']) else None)
            ls.append(sum(ld)/len(ld) if len(ld)==2*len(b['probe']) else None)
            details.append({'block':bi,'family':f,'task_gains':per_task,'observed_local_scores':len(ld)})
        terminal.append(ts);local.append(ls)
    def allocation(values):
        costs=[[-v if v is not None else None for v in row] for row in values]
        sol=solve_assignment(costs,tau=.2,balance=.1)
        return [row if sum(row)>0 else [1/3]*3 for row in sol['weights']]
    tw=allocation(terminal);lw=allocation(local);shuffled=[None]*len(tw)
    for family in ('arc_challenge','logiqa'):
        ix=[i for i,b in enumerate(pp['blocks']) if b['family']==family]
        order=sorted(ix,key=lambda i:digest([c.SEED,'allocation-shuffle',i]))
        for dest,src in zip(ix,order):shuffled[dest]=tw[src]
    agent_means=[sum(row[i] for row in terminal if row[i] is not None)/sum(row[i] is not None for row in terminal) if any(row[i] is not None for row in terminal) else None for i in range(3)]
    within=[[v-sum(x for x in row if x is not None)/sum(x is not None for x in row) if v is not None else None for v in row] for row in terminal]
    value={'mean_agent_terminal_effect':agent_means,'within_block_effects_descriptive_only':within,'terminal_gains':terminal,'local_gains':local,'uniform':[[1/3]*3 for _ in tw],'terminal':tw,'local':lw,'source_stratified_shuffled':shuffled,'private_details':details,
           'diagnostic_only':True,'policy_selected':False,'normalization':'none; raw paired gains','local_cross_family_calibration_matched':False}
    write_json(root/'allocation_analysis.private.json',value);return {k:v for k,v in value.items() if k!='private_details'}


def report(root):
    """Task-level paired effects, before/after accuracy and separate condition NLL."""
    from ..artifacts import ShardStore
    from ..selective.diagnostics import clustered_interval
    pp=read_json(root/'probe_plan.json');p=read_json(root/'plan.json')
    scores={tuple(r['identity']['logical']):r['nll'] for r in ShardStore(root/'probe_scores').records()}
    evaluations={tuple(v['tag']):v['rows'] for f in (root/'evaluations').glob('*.json') if (v:=read_json(f))['tag'][1]=='allocation_probe'}
    rows=[]
    for bi,b in enumerate(pp['blocks']):
        for f in c.FAMILIES:
            for cond in ('clean','exchange'):
                tasks=[];accuracies=[];private_delta=[];coverage_delta=[];receiver_error_delta=[];readout_loss_delta=[];missing=0
                for tid in b['probe']:
                    gains=[];acc=[];priv=[];cov=[];rx=[];ro=[]
                    for seed in (0,1):
                        a=('terminal',bi,tid,seed,'baseline',cond);z=('terminal',bi,tid,seed,f'block-{bi}-{f}',cond)
                        if a not in scores or z not in scores:continue
                        gains.append(scores[a]-scores[z])
                        base=evaluations.get((c.ARMS[2],'allocation_probe',seed,'baseline'),[])
                        updated=evaluations.get((c.ARMS[2],'allocation_probe',seed,f'block-{bi}-{f}'),[])
                        before=next((r for r in base if r['task_id']==tid and r['condition']==cond and not r['missing']),None)
                        after=next((r for r in updated if r['task_id']==tid and r['condition']==cond and not r['missing']),None)
                        if before and after:
                            acc.append(int(after['final'])-int(before['final']))
                            slot=next(r for r in p['source']['records'] if s.tid(r)==tid)['binding'].index(f)
                            priv.append(int(after['initial'][slot])-int(before['initial'][slot]))
                            cov.append(int(any(after['initial']))-int(any(before['initial'])))
                            rx.append(sum(not x for x in after['revised'])-sum(not x for x in before['revised']))
                            ro.append(int(any(after['revised']) and not after['final'])-int(any(before['revised']) and not before['final']))
                    if len(gains)==2 and len(acc)==2:
                        tasks.append((b['family'],tid,sum(gains)/2));accuracies.append(sum(acc)/2);private_delta.append(sum(priv)/2);coverage_delta.append(sum(cov)/2);receiver_error_delta.append(sum(rx)/2);readout_loss_delta.append(sum(ro)/2)
                    else:missing+=1
                rows.append({'block':bi,'family':f,'condition':cond,'independent_tasks':len(tasks),'missing_tasks':missing,
                    'terminal_nll_gain':sum(x[2] for x in tasks)/len(tasks) if tasks else None,
                    'terminal_interval':clustered_interval(tasks),'accuracy_delta':sum(accuracies)/len(accuracies) if accuracies else None,
                    'private_accuracy_delta':sum(private_delta)/len(private_delta) if private_delta else None,
                    'coverage_delta':sum(coverage_delta)/len(coverage_delta) if coverage_delta else None,
                    'receiver_error_count_delta':sum(receiver_error_delta)/len(receiver_error_delta) if receiver_error_delta else None,
                    'readout_loss_delta':sum(readout_loss_delta)/len(readout_loss_delta) if readout_loss_delta else None})
    probe_rows=s.records(p,'allocation_probe')
    attacks_ready=all((root/'attacks'/f'{digest(s.tid(r))}.json').exists() for r in probe_rows)
    expected_scores=sum(12+8*(1+int(s.attack_for(root,r) is not None)) for r in probe_rows) if attacks_ready else None
    branches_ready=all((root/'probe_training'/f'block-{b}'/f/'rollback.json').exists() for b in range(8) for f in c.FAMILIES)
    j=runtime.Journal(root,allow_incomplete=True)
    attempted_scores=len(list((root/'score_intents').glob('*.json')))
    value={'rows':rows,'complete':branches_ready and len(scores)==expected_scores and len(scores)==attempted_scores and set(j.intents)==set(j.results),
           'expected_score_forwards':expected_scores,'attempted_score_forwards':attempted_scores,
           'score_forwards':len(scores),'diagnostic_only':True,'common_readout':True,'local_nll_cross_family_matched':False,'seeds_are_independent_tasks':False,
           'generation':{stage:sum(v['intent']['identity']['budget_stage']==stage for v in j.results.values()) for stage in ('I','II')}}
    if (root/'allocation_analysis.private.json').exists():value['allocation_analysis']={k:v for k,v in read_json(root/'allocation_analysis.private.json').items() if k!='private_details'}
    write_json(root/'probe_summary.json',value);return value
