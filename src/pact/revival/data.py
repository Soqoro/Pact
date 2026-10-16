"""Official train allocation; prior exposure is a mandatory reviewed prerequisite."""
from dataclasses import asdict
from ..selective.data import validate_exposure, prior_selections, REPO
from ..training.data import load_training_sources, audit_training_overlap, select_training, TRAIN_SOURCES
from ..datasets import content_group
from ..util import digest, write_json
from .contracts import SEED,SPLITS,SOURCE_QUOTAS,ALLOCATION_VERSION


def source_quotas(fixture=False):
    return ({f:{'main_fit':6 if f=='arc_challenge' else 10,
                'allocation_probe':6 if f=='arc_challenge' else 10,
                'validation':2,'source_evaluation':2}
             for f in SOURCE_QUOTAS} if fixture else SOURCE_QUOTAS)


def allocate(training,validation,exposure,fixture=False):
    if not fixture:validate_exposure(exposure)
    ids=set(exposure.get('task_ids',[]));groups=set(exposure.get('group_ids',[]))
    contents=set(exposure.get('content_groups',[]));fps=set(exposure.get('cross_dataset_fingerprints',[]))
    if not fixture:
        _,_,old,_=select_training(training,validation,items=1200,seed=20260918)
        from ..datasets import SOURCES
        if digest({**old,'sources':{'train':TRAIN_SOURCES,'validation':SOURCES}})!='92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a':raise ValueError('Historical training allocation changed')
        for r in [*old['selected'],*prior_selections(REPO/'experiments')]:
            ids.add(r['task_id']);groups.add(r.get('group_id'));contents.add(r.get('content_group'))
    reps,audit=audit_training_overlap(training,validation)
    pool=[]
    for (t,l),g in reps:
        if not fixture:
            s=TRAIN_SOURCES[t.family]
            if t.split!='train' or t.source_hash!=s['sha256'] or t.dataset_revision!=s['revision']:raise ValueError('Official training only')
        fp=digest(' '.join((t.context or t.question).split()))
        if t.task_id in ids or g in groups or content_group(t) in contents or fp in fps:continue
        pool.append((t,l,g,fp))
    by_source=source_quotas(fixture)
    available={f:sum(t.family==f for t,_,_,_ in pool) for f in by_source}
    required={f:sum(q.values()) for f,q in by_source.items()}
    shortfall={f:max(0,required[f]-available[f]) for f in by_source}
    if any(shortfall.values()):return {'status':'source_shortfall','shortfall':shortfall,'available':available,'required':required,'allocation_version':ALLOCATION_VERSION,'model_calls':0}
    records=[];labels={};perms=('QLM','LMQ','MQL','QML','MLQ','LQM')
    for family in ('arc_challenge','logiqa'):
        candidates=sorted((r for r in pool if r[0].family==family),key=lambda r:digest([SEED,'allocation',r[2]]))
        offset=0
        for split,n in by_source[family].items():
            for pos,(t,l,g,fp) in enumerate(candidates[offset:offset+n]):
                styles=('argument_pressure','claimed_verification') if split=='main_fit' else ('claimed_consensus','claimed_independence')
                records.append({'task':asdict(t),'group_id':g,'family':family,'split':split,'binding':list(perms[pos%6]),
                    'sender':pos%3,'style':styles[pos%2],'content_group':content_group(t),'cross_dataset_fingerprint':fp})
                labels[t.task_id]=l.answer_id
            offset+=n
    if len({r['group_id'] for r in records})!=len(records) or len({r['cross_dataset_fingerprint'] for r in records})!=len(records):raise ValueError('Cross-source duplicate')
    blocks=[]
    for family in ('arc_challenge','logiqa'):
        fit=[r['task']['task_id'] for r in records if r['family']==family and r['split']=='main_fit']
        probe=[r['task']['task_id'] for r in records if r['family']==family and r['split']=='allocation_probe']
        count=3 if family=='arc_challenge' else 5
        for j in range(count):blocks.append({'family':family,'fit':fit[j*len(fit)//count:(j+1)*len(fit)//count], 'probe':probe[j*len(probe)//count:(j+1)*len(probe)//count]})
    return {'status':'ready','fixture':fixture,'records':records,'labels':labels,'blocks':blocks,'exposure':exposure,
            'allocation_version':ALLOCATION_VERSION,'source_quotas':by_source,'required':required,'available':available,'source_contract':TRAIN_SOURCES,'overlap_audit_hash':digest(audit),'semantic_decontamination':False}


def fixture():
    from ..schemas import TaskInput,TaskLabel,Option
    train=[]
    for f in ('arc_challenge','logiqa'):
        for i in range(24):
            t=TaskInput(f'{f}:fake-{i}',f,'train',str(i),'fixture','fixture',f'Invented {f} question {digest([f,i,1])}',tuple(Option(x,x,x) for x in 'ABC'),f'Invented context {digest([f,i,2])}')
            train.append((t,TaskLabel(t.task_id,'ABC'[i%3])))
    val=[]
    for f in ('arc_challenge','logiqa'):
        t=TaskInput(f'{f}:val',f,'validation','v','fixture','fixture','Validation unrelated quasar ocean',tuple(Option(x,x,x) for x in 'ABC'),'Unrelated validator')
        val.append((t,TaskLabel(t.task_id,'A')))
    return allocate(train,val,{},True)


def validate_source(source):
    """Do not trust a prepared JSON's ready flag as proof of quotas or exclusions."""
    if source.get('status')!='ready':raise ValueError('Source quota shortfall')
    fixture=source.get('fixture') is True;rows=source['records'];labels=source['labels']
    by_source=source_quotas(fixture)
    if source.get('allocation_version')!=ALLOCATION_VERSION or source.get('source_quotas')!=by_source:raise ValueError('Source allocation contract changed')
    counts={split:sum(r['split']==split for r in rows) for split in SPLITS}
    expected=SPLITS if not fixture else {'main_fit':16,'allocation_probe':16,'validation':4,'source_evaluation':4}
    if counts!=expected or len(rows)!=sum(expected.values()):raise ValueError('Exact split quotas required')
    if len({r['group_id'] for r in rows})!=len(rows) or len({r['task']['task_id'] for r in rows})!=len(rows):raise ValueError('Duplicate group/task')
    if set(labels)!={r['task']['task_id'] for r in rows}:raise ValueError('Label inventory mismatch')
    if not fixture:validate_exposure(source['exposure'])
    for r in rows:
        t=r['task'];f=r['family']
        if t['split']!='train' or f not in TRAIN_SOURCES or sorted(r['binding'])!=list('LMQ') or labels[t['task_id']] not in [o['answer_id'] for o in t['options']]:raise ValueError('Source identity/label/binding mismatch')
        if sum(x['split']==r['split'] and x['family']==f for x in rows)!=by_source[f][r['split']]:raise ValueError('Source quota mismatch')
        if not fixture:
            spec=TRAIN_SOURCES[f];ex=source['exposure']
            if t['dataset_revision']!=spec['revision'] or t['source_hash']!=spec['sha256']:raise ValueError('Unofficial source')
            if t['task_id'] in ex['task_ids'] or any(r[k] in ex[z] for k,z in [('group_id','group_ids'),('content_group','content_groups'),('cross_dataset_fingerprint','cross_dataset_fingerprints')]):raise ValueError('Prior exposure overlap')
    fit={r['task']['task_id'] for r in rows if r['split']=='main_fit'};pr={r['task']['task_id'] for r in rows if r['split']=='allocation_probe'}
    blocks=source['blocks']
    if len(blocks)!=8 or set(t for b in blocks for t in b['fit'])!=fit or set(t for b in blocks for t in b['probe'])!=pr:raise ValueError('Block coverage mismatch')
    if sum(len(b['fit']) for b in blocks)!=len(fit) or sum(len(b['probe']) for b in blocks)!=len(pr):raise ValueError('Duplicate block membership')
    if [b['family'] for b in blocks]!=['arc_challenge']*3+['logiqa']*5:raise ValueError('Block source allocation')
    for b in blocks:
        if len(b['fit'])!=expected['main_fit']//8 or len(b['probe'])!=expected['allocation_probe']//8:raise ValueError('Block sizes')
        if any(r['family']!=b['family'] for r in rows if r['task']['task_id'] in b['fit']+b['probe']):raise ValueError('Cross-source block')
