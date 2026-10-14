"""Official train-only acquisition and disjoint frozen exposure allocation."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
from ..training.data import load_training_sources, audit_training_overlap, select_training, TRAIN_SOURCES
from ..datasets import content_group
from ..schemas import TaskInput, TaskLabel, Option
from ..util import digest, file_hash, read_json, write_json
from .contracts import SPLITS, SEED

REPO=Path(__file__).resolve().parents[3]
QUOTAS={'fit':64,'threshold_tuning':16,'source_development_holdout':32}
LEDGER=REPO/'docs/benchmark_exposure_ledger.md'


def prior_selections(directory):
    for path in sorted(directory.glob('*selection.json')):
        value=read_json(path)
        rows=value if isinstance(value,list) else value.get('selected',[])
        for row in rows:
            if not isinstance(row,dict) or 'task_id' not in row:raise ValueError('Malformed prior selection inventory')
            yield row


def validate_exposure(exposure):
    if exposure.get('ledger_sha256')!=file_hash(LEDGER) or exposure.get('reviewed_complete') is not True:raise ValueError('Reviewed prior/locked exposure inventory matching current ledger required')
    fields=('task_ids','group_ids','content_groups','cross_dataset_fingerprints','source_receipts')
    if any(not isinstance(exposure.get(k),list) for k in fields) or not exposure['source_receipts']:raise ValueError('Incomplete exposure inventory')
    if any(not isinstance(v,str) or not v for k in fields[:-1] for v in exposure[k]):raise ValueError('Malformed exposure identity')


def allocate(training,validation,exposure,*,fixture=False):
    if not fixture:
        validate_exposure(exposure)
        for t,_ in training:
            s=TRAIN_SOURCES.get(t.family)
            if not s or t.split!='train' or t.source_hash!=s['sha256'] or t.dataset_revision!=s['revision']:raise ValueError('Only pinned official training sources permitted')
    reps,audit=audit_training_overlap(training,validation)
    ids=set(exposure.get('task_ids',[]));groups=set(exposure.get('group_ids',[]));contents=set(exposure.get('content_groups',[]));fps=set(exposure.get('cross_dataset_fingerprints',[]))
    prior_manifest=None
    if not fixture:
        # Conservative exclusion of the ENTIRE previously prepared 1200, including
        # tasks allocated but not executed, plus prior explicit selection files.
        _,_,prior_manifest,_=select_training(training,validation,items=1200,seed=20260918)
        if digest({**prior_manifest,'sources':{'train':TRAIN_SOURCES,'validation':__import__('pact.datasets',fromlist=['SOURCES']).SOURCES}})!='92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a':
            raise ValueError('Historical 1200-source manifest changed')
        for r in prior_manifest['selected']:
            ids.add(r['task_id']);groups.add(r['group_id']);contents.add(r['content_group'])
        for r in prior_selections(REPO/'experiments'):
            ids.add(r['task_id']);groups.add(r.get('group_id'));contents.add(r.get('content_group'))
    def fingerprint(question,context,options):return digest(" ".join((context or question).split()))
    eligible=[];excluded=[]
    for (t,l),g in reps:
        # Same cross-dataset lexical fingerprint as benchmark breadth.
        fp=fingerprint(t.question,t.context,[o.text for o in t.options])
        if t.task_id in ids or g in groups or content_group(t) in contents or fp in fps:
            excluded.append({'task_id':t.task_id,'group_id':g});continue
        eligible.append((t,l,g))
    # Each complete three-task block assigns every model once to every slot.
    selected=[];labels={};perms=('QLM','LMQ','MQL','QML','MLQ','LQM')
    quotas=QUOTAS if not fixture else {s:2 for s in SPLITS}
    for family in ('arc_challenge','logiqa'):
        pool=sorted((r for r in eligible if r[0].family==family),key=lambda r:digest([SEED,'source-selection',r[2]]))
        needed=sum(quotas.values())
        if len(pool)<needed:raise ValueError(f'Insufficient fresh {family} groups: {len(pool)}/{needed}; no calls authorized')
        offset=0
        for split,n in quotas.items():
            for pos,(t,l,g) in enumerate(pool[offset:offset+n]):
                selected.append({'task':asdict(t),'group_id':g,'split':split,'family':family,'stratum':family,
                    'training_allowed':split=='fit','binding':list(perms[pos%6]),'content_group':content_group(t),'cross_dataset_fingerprint':fingerprint(t.question,t.context,[o.text for o in t.options])})
                labels[t.task_id]={'answer':l.answer_id,'split':split}
            offset+=n
    if len({r['group_id'] for r in selected})!=len(selected):raise ValueError('Cross-family duplicate group')
    selected.sort(key=lambda r:(SPLITS.index(r['split']),digest([SEED,r['task']['task_id']])))
    return {'records':selected,'labels':labels,'exposure':{'policy':'exclude previous 1200 allocation, full validation-connected groups, reviewed prior/locked IDs and fingerprints',
        'inventory':exposure,'prior_manifest_hash':digest(prior_manifest),'overlap_audit_hash':digest(audit),'excluded':excluded,
        'counts':dict(Counter(r['split'] for r in selected)),'semantic_decontamination':False},'fixture':fixture}


def prepare(cache,output,exposure_path,download=False):
    if output.exists():raise ValueError('Source output already exists; do not overwrite')
    training,validation=load_training_sources(cache,download=download)
    value=allocate(training,validation,read_json(exposure_path));write_json(output,value);return value


def fixture_data():
    training=[];validation=[]
    for family in ('arc_challenge','logiqa'):
        for i in range(10):
            tid=f'{family}:fixture-{i}';text=f'Fictional unique {family} exercise {chr(0x400+i)}. Choose the designated symbol {i}.'
            t=TaskInput(tid,family,'train',str(i),'fixture','fixture',text,tuple(Option(x,x,x) for x in 'ABC'),f'Fictional context {family} {i}')
            training.append((t,TaskLabel(tid,'B' if i%2 else 'A')))
        t=TaskInput(f'{family}:validation',family,'validation','val','fixture','fixture','Different validation problem',tuple(Option(x,x,x) for x in 'ABC'),'Validation only')
        validation.append((t,TaskLabel(t.task_id,'C')))
    return allocate(training,validation,{},fixture=True)
