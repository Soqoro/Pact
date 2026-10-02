"""Frozen pilot population, shared sample bindings and deterministic request schedule."""
from collections import Counter
import dataclasses as dc
from itertools import permutations
from pathlib import Path
import random
from ..backends.registry import registry
from ..schemas import task_from_dict
from ..training.feasibility import read_review
from ..util import digest,node_seed

RUN_ID='pact-heterogeneous-complementarity-001'
VARIANT='heterogeneous_natural_support_v1'
SEED=20261002
PILOT_SHA='7a2d96d48e805718d138da03f651dfbaca02adc7d95d2a02cdf5191f4c6e94f4'
TEAMS=('QQQ','LLL','MMM','QLM')
BUDGET={'calls':2400,'reserved_output_tokens':476160,'private':720,'revision':960,'synthesis':640,'task_only':80}


def pilot_source(path):
    content=read_review(Path(path),PILOT_SHA,max_members=4000,max_bytes=100*1024**2,
        checksum_name='REVIEW_EXPORT_CHECKSUMS.json',selected_names={'task_inputs.json','task_labels.json','data_manifest.json'})
    return {'tasks':content['task_inputs.json'],'labels':content['task_labels.json'],
            'manifest':content['data_manifest.json'],'archive_sha256':PILOT_SHA}


def validate_source(source,fixture=False):
    tasks=source['tasks'];labels=source['labels'];manifest=source['manifest']
    pinned={'tasks':'2f0417b03607ea2501e0c04f9784e47eeb206952e5d1a41f6e879d2e50b2f17c',
            'labels':'6badc624501d140f0bf18834dbea2dd19f411579689ee45982690ec02b09d0b5',
            'manifest':'8a8a9515244b2ded3e2eba801b99adaa107547ee02470991946d5ff7b8216495'}
    if not fixture and any(digest(source[k])!=v for k,v in pinned.items()):
        raise ValueError('Original pilot content identity changed')
    if not fixture and (source['archive_sha256']!=PILOT_SHA or len(tasks)!=80 or
            Counter(t['family'] for t in tasks)!=Counter(arc_challenge=40,logiqa=40)):
        raise ValueError('Exact original 80-task pilot required')
    if len({t['task_id'] for t in tasks})!=len(tasks):raise ValueError('Duplicate task')
    if [t['task_id'] for t in tasks]!=[s['task_id'] for s in manifest['selected']]:raise ValueError('Pilot order changed')
    if set(labels)!={t['task_id'] for t in tasks}:raise ValueError('Labels mismatch')
    for t,s in zip(tasks,manifest['selected']):
        task=task_from_dict(t);label=labels[task.task_id]
        if task.split!='validation' or task.family not in ('arc_challenge','logiqa'):raise ValueError('Forbidden split/family')
        if digest(t)!=s['input_hash'] or digest(label)!=s['label_hash']:raise ValueError('Pilot inputs/labels changed')
        if label['answer_id'] not in {o.answer_id for o in task.options}:raise ValueError('Option mapping invalid')


def freeze_plan(source,code,fixture=False):
    validate_source(source,fixture)
    mappings={}
    for family in sorted({t['family'] for t in source['tasks']}):
        ids=sorted(t['task_id'] for t in source['tasks'] if t['family']==family)
        rng=random.Random(node_seed(SEED,family,'display'));rng.shuffle(ids)
        perms=list(permutations('QLM'));rng.shuffle(perms)
        mappings.update({tid:list(perms[i%6]) for i,tid in enumerate(ids)})
    bindings={t['task_id']:{team:[{'family':f,'replica':j,'slot':j} for j,f in enumerate(mappings[t['task_id']] if team=='QLM' else team)] for team in TEAMS} for t in source['tasks']}
    return {'schema_version':1,'run_id':RUN_ID,'variant':VARIANT,'seed':SEED,'fixture':fixture,
        'source':source,'code':code,'models':registry(),'team_bindings':bindings,'budget':BUDGET,
        'exposure':'original_validation_pilot_development_exposed','final_test':False,'training':False,
        'template_policy':'native_system_user_v1','peer_order':'ascending_anonymous_slot',
        'readout_order':'ascending_anonymous_slot','context_cap':4096,
        'smoke_ids':[t['task_id'] for t in source['tasks'][:2]]}


def schedule(plan):
    rows=[]
    for task in plan['source']['tasks']:
        tid=task['task_id']
        for f in 'QLM':
            for replica in range(3):rows.append({'task_id':tid,'stage':'private','model':f,'replica':replica,'team':None,'slot':replica})
        for team in TEAMS:
            for b in plan['team_bindings'][tid][team]:rows.append({'task_id':tid,'stage':'revision','model':b['family'],'replica':b['replica'],'team':team,'slot':b['slot']})
            for stage in ('synthesis','debate'):rows.append({'task_id':tid,'stage':stage,'model':'R','replica':None,'team':team,'slot':None})
        rows.append({'task_id':tid,'stage':'task_only','model':'R','replica':None,'team':None,'slot':None})
    for row in rows:
        row['cap']=256 if row['stage'] in ('private','revision') else 64
        row['seed']=node_seed(SEED,row['task_id'],plan['models'][row['model']],
                              'revision' if row['stage']=='revision' else row['stage'],row['replica'])
        row['key']=digest(row)
    return rows


def load_plan(root):
    from ..util import read_json,canonical
    p=read_json(root/'plan.json');state=read_json(root/'state.json')
    if digest(p)!=state['plan_hash'] or canonical(freeze_plan(p['source'],p['code'],p['fixture']))!=canonical(p):
        raise ValueError('Frozen heterogeneous plan changed')
    return p
