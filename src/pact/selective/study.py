"""Bounded source/check acquisition, frozen CPU policies and separate transfer."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
import json
import os
import shutil
import tempfile
import time
import zipfile
from ..util import digest,canonical,read_json,write_json,file_hash,node_seed
from ..schemas import task_from_dict,Message,CallRecord
from ..backends import Request
from ..backends.registry import REGISTRY,generation_parameters
from ..environment import code_identity
from ..artifacts import ShardStore,run_lock,sync_run
from ..storage import persist_bundle,storage_operation
from ..studies.heterogeneity import immutable
from ..studies.forensics import private_root
from ..studies.semantic_review import package
from ..training.feasibility import read_review
from ..studies.breadth import BreadthJournal
from ..studies.adjudication import validate_identity
from .contracts import *
from . import gates

REPO=Path(__file__).resolve().parents[3]
MODELS={k:REGISTRY[k] for k in ('Q','L','M','R')}
LIMITS={'fit_tuning':3360,'source_development_holdout':2240,'transfer':5156}


class SelectiveJournal(BreadthJournal):
    def validate_request(self,r):
        if r.task.split not in ('train','characterization_dev') or r.max_tokens!=CAP or r.actor!='base' or r.phase!='final':raise ValueError('Request outside selective profile')


def check_budget(counts,split):
    b=bucket(split)
    if b not in LIMITS or counts.get(b,0)+1>LIMITS[b] or sum(counts.values())+1>10756:raise ValueError('Stage or portfolio attempt budget exhausted')


def bucket(split):return 'fit_tuning' if split in SPLITS[:2] else split


def plan(root,source):
    if (root/'plan.json').exists():raise ValueError('Never re-plan an existing run')
    fixture=source['fixture'];private_root(root,fixture)
    records=source['records'];labels=source['labels']
    if set(labels)!={r['task']['task_id'] for r in records}:raise ValueError('Label inventory differs from selected tasks')
    if len({r['group_id'] for r in records})!=len(records) or len({r['task']['task_id'] for r in records})!=len(records):raise ValueError('Duplicate task/group')
    for r in records:
        t=r['task'];label=labels[t['task_id']]
        if r['split'] not in SPLITS or t['split']!='train' or r['family'] not in ('arc_challenge','logiqa') or label['split']!=r['split']:raise ValueError('Forbidden source/split')
        if r['training_allowed']!=(r['split']=='fit') or sorted(r['binding'])!=['L','M','Q']:raise ValueError('Training or model binding mismatch')
        if label['answer'] not in dict(PublicTask.from_task(t).options):raise ValueError('Label mapping mismatch')
    if not fixture:
        if root.name!=RUN_ID:raise ValueError('Exact run ID required')
        from .data import QUOTAS,TRAIN_SOURCES,validate_exposure
        for r in records:
            spec=TRAIN_SOURCES[r['family']]
            if r['task']['source_hash']!=spec['sha256'] or r['task']['dataset_revision']!=spec['revision']:raise ValueError('Prepared source is not pinned official training data')
        inventory=source['exposure']['inventory'];validate_exposure(inventory)
        for r in records:
            if any(r[field] in inventory[key] for field,key in [('group_id','group_ids'),('content_group','content_groups'),('cross_dataset_fingerprint','cross_dataset_fingerprints')]) or r['task']['task_id'] in inventory['task_ids']:raise ValueError('Selected task overlaps prior/locked inventory')
        if Counter((r['split'],r['family']) for r in records)!=Counter({(s,f):n for s,n in QUOTAS.items() for f in ('arc_challenge','logiqa')}):raise ValueError('Exact 224-group quotas required')
    p={'version':VERSION,'run_id':RUN_ID,'fixture':fixture,'source':code_identity(REPO),'records':records,
       'labels_hash':{split:digest({tid:v for tid,v in labels.items() if v['split']==split}) for split in SPLITS},'exposure_hash':digest(source['exposure']),'models':{k:asdict(v) for k,v in MODELS.items()},
       'contracts':contracts(),'budgets':LIMITS,'total_calls':10756,'reserved_output_tokens':5507072,
       'smoke_ids':[r['task']['task_id'] for r in records if r['split']=='fit'][:2]}
    for split in SPLITS:immutable(root/'labels'/f'{split}.json',{tid:v for tid,v in labels.items() if v['split']==split})
    immutable(root/'source_exposure_manifest.json',source['exposure']);immutable(root/'plan.json',p)
    immutable(root/'model_and_prompt_contracts.json',{'models':p['models'],'contracts':p['contracts']})
    write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':True});return p


def load(root):
    p=read_json(root/'plan.json')
    if digest(p)!=read_json(root/'state.json')['plan_hash'] or digest(p['contracts'])!=digest(contracts()) or p['models']!={k:asdict(v) for k,v in MODELS.items()} or p['budgets']!=LIMITS:raise ValueError('Frozen plan/contracts changed')
    if digest(read_json(root/'source_exposure_manifest.json'))!=p['exposure_hash']:raise ValueError('Source exposure changed')
    if not p['fixture']:private_root(root)
    return p


def inspect(root):
    p=load(root);results={};counts=Counter();unknown=[];store=ShardStore(root/'calls');intents={}
    for f in sorted((root/'intents').glob('*.json')):
        i=read_json(f);key=f.stem
        if i['work_id']!=key or digest(i['identity'])!=key or i['identity']['plan_hash']!=digest(p):raise ValueError('Attempt identity changed')
        req=request_from(i['request']);model=i['identity']['model'];split=i['split']
        if digest(req)!=i['identity']['request_hash'] or model not in MODELS or req.max_tokens!=CAP or split not in (*SPLITS,'transfer'):raise ValueError('Request/stage mismatch')
        if req.deterministic!=(model=='R'):raise ValueError('Decoding role mismatch')
        if i['identity']['model_spec']!=p['models'][model]:raise ValueError('Attempt model specification changed')
        planned=[r for r in records(root,split) if r['task']['task_id']==req.task.task_id]
        if len(planned)!=1 or planned[0]['task']!=i['request']['task']:raise ValueError('Attempt task/split differs from frozen record')
        counts[bucket(split)]+=1;intents[key]=i
        if not store.path(key).with_suffix('.sha256').exists():unknown.append(key);continue
        result=store.read(key);identity=read_json(root/'identities'/f'{model}.json');validate_identity(identity,model,p)
        if not p['fixture']:
            access=read_json(root/'access'/f'{model}.json')
            if any(identity.get(k)!=v for k,v in access.items()):raise ValueError('Model/access mismatch')
        validator=object.__new__(SelectiveJournal);validator.identity=identity;validator.plan={'profile':{'context':CONTEXT}}
        validator._validate(req,result['intent'],result)
        if result['intent']!={'schema_version':1,'work_id':key,'record_id':key,'slot':0,'request_hash':digest(req),'max_tokens':CAP}:raise ValueError('Stored intent differs')
        results[key]=result
    for i in intents.values():
        deps=i['identity'].get('dependencies',{})
        if deps:
            e=results.get(deps.get('extractor'))
            if e is None or digest(e)!=deps.get('extractor_result'):raise ValueError('Changed/missing extractor dependency')
    for f in (root/'calls/shards').glob('*'):
        if f.stem not in intents or f.suffix not in ('.json','.sha256'):raise ValueError('Orphan result')
    if any(counts[k]>LIMITS[k] for k in counts) or sum(counts.values())>10756:raise ValueError('Attempt budget exceeded')
    return p,intents,results,unknown


def request_from(d):
    task=d['task']
    if 'kind' in task:
        from ..benchmarks.contracts import BenchmarkInput
        t=BenchmarkInput.from_dict(task)
    else:t=task_from_dict(task)
    return Request(t,tuple(Message(m['role'],m['content']) for m in d['messages']),d['actor'],d['phase'],d['seed'],d['max_tokens'],d['deterministic'])


def checkpoint(root,persistent):
    if persistent is None:return
    p=load(root)
    path=root.parent/'checkpoints'/f'{RUN_ID}-{time.time_ns()}.zip';result=package(root,path,VERSION+'_private')
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        temp=Path(d);shutil.copyfile(path,temp/'state.zip')
        write_json(temp/'receipt.json',{'sha256':result['sha256'],'plan_hash':digest(p),'recovery_safe':read_json(root/'state.json')['recovery_safe']})
        sync_run(temp,persistent,timeout_seconds=300)
    # Compact snapshots are durable; do not retain every full local checkpoint.
    path.unlink()


class Session:
    def __init__(self,root,*,execute=False,cache=None,persistent=None,mock=False):
        self.root=root;self.p,self.intents,self.results,unknown=inspect(root);self.execute=execute;self.cache=cache;self.persistent=persistent;self.mock=mock
        self.backend=None;self.model=None;self.new=0;self.reused=0;self.open=False
        if mock!=self.p['fixture']:raise ValueError('Fixture/real mismatch')
        if unknown or not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe or unresolved dispatch: no automatic retry')
        if execute and code_identity(REPO)!=self.p['source']:raise ValueError('Pinned source changed; no implicit migration')
        if execute and not mock:
            if cache is None or persistent is None:raise ValueError('Real inference requires scratch cache and durable storage')
            access=read_json(root/'preflight.json')
            if access['plan_hash']!=digest(self.p) or set(access['models'])!=set(MODELS):raise ValueError('Matching all-model access preflight required')
            if any(access['models'][k]!=read_json(root/'access'/f'{k}.json') for k in MODELS):raise ValueError('Preflight/access mismatch')
    def close_model(self):
        if self.backend:
            write_json(self.root/'resources'/f'{time.time_ns()}.json',{'model':self.model,**self.backend.resource_usage()})
            self.backend.close();self.backend=None
    def finish(self):
        self.close_model()
        if self.open:
            write_json(self.root/'state.json',{'plan_hash':digest(self.p),'recovery_safe':True})
            try:checkpoint(self.root,self.persistent)
            except BaseException:
                write_json(self.root/'state.json',{'plan_hash':digest(self.p),'recovery_safe':False});raise
            self.open=False
    def call(self,rec,model,messages,role,slot='',seed_role=None,dependencies=None):
        permitted={'private':('Q','L','M'),'anchor':('R',),'rewrite':('Q',),'extract':('R',),
                   'verify_full':('R',),'verify_restricted':('R',),'anchor_inclusive_select':('R',),
                   'independent_critique':('R',),'independent_reconsider':('R',)}
        if role not in permitted or model not in permitted[role]:raise ValueError('Stage/model mismatch')
        if rec['split']=='transfer' and role in ('private','anchor','rewrite'):raise ValueError('Transfer source regeneration forbidden')
        if rec['split'] in SPLITS[:2] and role in ('anchor_inclusive_select','independent_critique','independent_reconsider'):raise ValueError('Evaluation controls forbidden in fit/tuning')
        if rec not in records(self.root,rec['split']):raise ValueError('Unplanned task/source record')
        task=rec['task']
        if 'kind' in task:
            from ..benchmarks.contracts import BenchmarkInput
            t=BenchmarkInput.from_dict(task)
        else:t=task_from_dict(task)
        seed=node_seed(SEED,RUN_ID,t.task_id,seed_role or role,slot)
        req=Request(t,messages,'base','final',seed,CAP,model=='R')
        identity={'plan_hash':digest(self.p),'model':model,'model_spec':self.p['models'][model],'request_hash':digest(req),'role':role,'dependencies':dependencies or {}}
        key=digest(identity)
        if key in self.results:self.reused+=1;return self.results[key]
        if not self.execute:raise ValueError(f'Missing {role} evidence; complete the explicit acquisition stage first')
        split=rec['split'];b=bucket(split)
        if split in ('source_development_holdout','transfer'):frozen(self.root)
        check_budget(Counter(bucket(i['split']) for i in self.intents.values()),split)
        if self.model!=model or self.backend is None:
            self.close_model();self.model=model
            if self.mock:self.backend=MockBackend(model)
            else:
                from ..backends.native import NativeBackend
                class Backend(NativeBackend):
                    def generation_parameters(self,request):return {**super().generation_parameters(request),'max_new_tokens':CAP}
                self.backend=Backend(model,read_json(self.root/'access'/f'{model}.json'),self.cache,spec=MODELS[model])
                self.backend.config.limits=replace(self.backend.config.limits,context=CONTEXT)
            validate_identity(self.backend.identity,model,self.p);immutable(self.root/'identities'/f'{model}.json',self.backend.identity)
        if not self.open:
            write_json(self.root/'state.json',{'plan_hash':digest(self.p),'recovery_safe':False});checkpoint(self.root,self.persistent);self.open=True
        intent={'schema_version':1,'work_id':key,'identity':identity,'request':asdict(req),'split':split}
        immutable(self.root/'intents'/f'{key}.json',intent);self.intents[key]=intent
        raw,call=self.backend.generate(req)
        result={'schema_version':1,'work_id':key,'intent':{'schema_version':1,'work_id':key,'record_id':key,'slot':0,'request_hash':digest(req),'max_tokens':CAP},'raw':raw,'call':asdict(call),'tokens':dict(self.backend.last_generation)}
        validator=object.__new__(SelectiveJournal);validator.identity=self.backend.identity;validator.plan={'profile':{'context':CONTEXT}}
        validator._validate(req,result['intent'],result);ShardStore(self.root/'calls').put(key,result);self.results[key]=result;self.new+=1
        print(f'{role}: {len(self.intents)}/10756 committed; split={split}',flush=True)
        if self.new%20==0:
            write_json(self.root/'state.json',{'plan_hash':digest(self.p),'recovery_safe':True});checkpoint(self.root,self.persistent);self.open=False
        return result


def records(root,split):
    if split=='transfer':return read_json(root/'transfer.json')['records']
    if split not in SPLITS:raise ValueError('Unknown split')
    return [r for r in load(root)['records'] if r['split']==split]


def source_file(root,tid):return root/'sources'/f'{digest(tid)}.json'


def read_labels(root,split):
    if split=='transfer':
        value=read_json(root/'transfer-labels.json');expected=read_json(root/'transfer.json')['labels_hash']
    else:
        value=read_json(root/'labels'/f'{split}.json');expected=load(root)['labels_hash'][split]
    if digest(value)!=expected or any(v['split']!=split for v in value.values()):raise ValueError('Split label identity changed')
    return value


def source_bank(root,rec):
    saved=read_json(source_file(root,rec['task']['task_id']))
    if saved['record_hash']!=digest(rec):raise ValueError('Source bank changed')
    if rec['split']=='transfer':
        transfer=read_json(root/'transfer.json')
        if digest(transfer['records'])!=transfer['source_hash'] or digest(saved)!=transfer['bank_hashes'][rec['task']['task_id']]:raise ValueError('Transfer source changed')
    else:
        p=load(root);task=PublicTask.from_task(rec['task']);parsed={}
        for model in ('Q','L','M','R'):
            slot='anchor' if model=='R' else 'c'+str(rec['binding'].index(model));role='anchor' if model=='R' else 'private'
            req=Request(task_from_dict(rec['task']),source_prompt(task,model=='R'),'base','final',node_seed(SEED,RUN_ID,rec['task']['task_id'],role,slot),CAP,model=='R')
            key=digest({'plan_hash':digest(p),'model':model,'model_spec':p['models'][model],'request_hash':digest(req),'role':role,'dependencies':{}})
            v=ShardStore(root/'calls').read(key)
            parsed[slot]=asdict(parse_answer(v['raw'],task,v['call']['stop_reason'],slot,packet=model!='R'))
        if saved!={'record_hash':digest(rec),'anchor':parsed['anchor'],'peers':[parsed['c'+str(i)] for i in range(3)]}:raise ValueError('Source differs from frozen natural generations')
    return Answer(**saved['anchor']),[Answer(**p) for p in saved['peers']]


def collect_source(s,split,smoke=False):
    if split=='transfer':raise ValueError('Transfer never regenerates sources')
    if split==SPLITS[2]:frozen(s.root)
    rs=records(s.root,split)
    if smoke:
        if split!='fit':raise ValueError('Smoke only two frozen FIT tasks')
        rs=[r for r in rs if r['task']['task_id'] in s.p['smoke_ids']]
    collected={}
    for model in ('R','Q','L','M'):
        for rec in rs:
            task=PublicTask.from_task(rec['task']);tid=rec['task']['task_id'];slot='anchor' if model=='R' else 'c'+str(rec['binding'].index(model))
            v=s.call(rec,model,source_prompt(task,model=='R'),'anchor' if model=='R' else 'private',slot)
            parsed=parse_answer(v['raw'],task,v['call']['stop_reason'],slot,packet=model!='R')
            collected.setdefault(tid,{})[slot]=asdict(parsed)
    for rec in rs:
        tid=rec['task']['task_id'];r=collected[tid]
        immutable(source_file(s.root,tid),{'record_hash':digest(rec),'anchor':r['anchor'],'peers':[r['c'+str(i)] for i in range(3)]})
    return {'source_tasks':len(rs),'new_calls':s.new}


def pool_file(root,split):return root/'pools'/f'{split}.json'


def acquire(s,split):
    if split=='transfer':raise ValueError('No new transfer rewrites')
    if split==SPLITS[2]:frozen(s.root)
    rs=records(s.root,split);styles=FIT_STYLES if split in SPLITS[:2] else DEV_STYLES;labels=read_labels(s.root,split);pool=[]
    # Targets depend on natural peer correctness only, never anchor/judge success.
    targets={}
    for rec in rs:
        a,peers=source_bank(s.root,rec);tid=rec['task']['task_id'];wrong=[p for p in peers if p.status=='ok' and p.answer!=labels[tid]['answer']]
        targets[tid]=min(wrong,key=lambda p:digest([SEED,'rewrite-target',tid,p.candidate_id])).candidate_id if wrong else None
    immutable(s.root/'targets'/f'{split}.json',targets)
    for rec in rs:
        tid=rec['task']['task_id'];a,peers=source_bank(s.root,rec);target=targets[tid]
        for style in styles:
            row={'task_id':tid,'style':style,'target':target,'accepted':False,'justification':None,'status':'inapplicable_no_valid_wrong_peer'}
            if target is not None:
                peer=next(p for p in peers if p.candidate_id==target);v=s.call(rec,'Q',rewrite_prompt(PublicTask.from_task(rec['task']),peer,style),'rewrite',style)
                from ..studies.adjudication_contracts import parse_rewrite
                text,status=parse_rewrite(v['raw'],v['call']['stop_reason']);row.update(accepted=text is not None,justification=text,status=status,result_hash=digest(v))
            pool.append(row)
    immutable(pool_file(s.root,split),{'rows':pool,'hash':digest(pool)});return {'attempt_slots':len(pool),'accepted':sum(r['accepted'] for r in pool)}


def views(root,rec):
    a,peers=source_bank(root,rec);pool=read_json(pool_file(root,rec['split']))
    if digest(pool['rows'])!=pool['hash']:raise ValueError('Perturbation pool changed')
    out={'clean':peers};missing=0
    for r in pool['rows']:
        if r['task_id']!=rec['task']['task_id']:continue
        if r['accepted']:
            out[r['style']]=[replace(p,basis=r['justification'],raw=canonical({'answer':p.answer,'justification':r['justification']})) if p.candidate_id==r['target'] else p for p in peers]
        elif r['target'] is not None:missing+=1
    return a,out,missing


def build_checks(s,split):
    # Full pool must exist BEFORE any victim extraction. Every accepted view retains
    # all alternatives; unaffected prompts/seeds reuse exact call identities.
    if split in (SPLITS[2],'transfer'):frozen(s.root)
    rs=records(s.root,split);read_json(pool_file(s.root,split));output=[]
    # Reconstruct the frozen pool from already committed rewrite evidence before
    # victims. Missing rewrite evidence cannot trigger an implicit new attempt.
    if split!='transfer':
        execute=s.execute;s.execute=False
        try:acquire(s,split)
        finally:s.execute=execute
    else:
        transfer=read_json(s.root/'transfer.json')
        if digest(read_json(pool_file(s.root,split)))!=transfer['pool_hash']:raise ValueError('Transfer rewrite pool changed')
    for rec in rs:
        a,vs,missing=views(s.root,rec);task=PublicTask.from_task(rec['task']);byview={}
        for view,peers in vs.items():
            rows=[]
            for peer in alternatives(a,peers):
                e=s.call(rec,'R',pair_prompt(task,a,peer),'extract',peer.candidate_id)
                extraction=parse_challenge(e['raw'],task,e['call']['stop_reason']);verifiers={};row={'candidate_id':peer.candidate_id,'answer':peer.answer,'raw':peer.raw,'enabled':{},'metadata':features(a,peers,peer,metadata=True),'references':extraction['references'],'extraction_status':extraction['status'],'evidence':{'extract':e['work_id']}}
                for kind in ('full','restricted'):
                    if extraction['status']=='ok':
                        v=s.call(rec,'R',pair_prompt(task,a,peer,extraction,kind=='restricted'),'verify_'+kind,peer.candidate_id,seed_role='verify',dependencies={'extractor':e['work_id'],'extractor_result':digest(e)})
                        verifiers[kind]=parse_verifier(v['raw'],v['call']['stop_reason']);row['evidence'][kind]=v['work_id']
                    else:verifiers[kind]={'status':'missing','value':None}
                    row[kind]=features(a,peers,peer,extraction,verifiers[kind]);row['enabled'][kind]=extraction['status']=='ok' and verifiers[kind]['status']=='ok'
                rows.append(row)
            byview[view]=rows
        output.append({'task_id':rec['task']['task_id'],'group_id':rec['group_id'],'split':split,'training_allowed':rec['training_allowed'],
             'anchor':asdict(a),'views':byview,'missing_variants':missing})
    value={'rows':output,'hash':digest(output)};immutable(s.root/'features'/f'{split}.json',value)
    immutable(s.root/'feature_schema.json',{'checker':feature_spec(),'metadata':feature_spec(True)})
    immutable(s.root/'feature_bank_identity'/f'{split}.json',{'hash':digest(output),'plan_hash':digest(s.p)})
    return value


def labeled_features(root,split):
    f=read_json(root/'features'/f'{split}.json')
    if digest(f['rows'])!=f['hash']:raise ValueError('Feature bank changed')
    labels=read_labels(root,split);out=[]
    for t in f['rows']:
        if t['split']!=split:raise ValueError('Feature split mismatch')
        gold=labels[t['task_id']];
        if gold['split']!=split:raise ValueError('Label split mismatch')
        a=Answer(**t['anchor']);t={**t,'gold':gold['answer'],'views':{v:[{**r,'target':int(r['answer']==gold['answer'])-int(a.status=='ok' and a.answer==gold['answer'])} for r in rs] for v,rs in t['views'].items()}}
        out.append(t)
    if {t['task_id'] for t in out}!={r['task']['task_id'] for r in records(root,split)}:raise ValueError('Incomplete feature split')
    return out


def audit_checks(root,split):
    p=load(root);session=Session(root,mock=p['fixture'])
    if split!='transfer':acquire(session,split)
    build_checks(session,split)


def fit_gates(root):
    audit_checks(root,'fit');tasks=labeled_features(root,'fit');out={}
    for arm in ARMS:
        path=root/'gates'/f'{arm}.json';intent=root/'fit-intents'/f'{arm}.json'
        if path.exists():
            m=read_json(path);gates.validate_model(m)
            if m['fit_hash']!=digest(tasks):raise ValueError('Fit data changed')
        else:
            if intent.exists():raise ValueError('Prior failed/interrupted fit; no sixth fit or automatic retry')
            immutable(intent,{'arm':arm,'fit_hash':digest(tasks),'max_iterations':500})
            started=time.monotonic()
            try:m=gates.fit(tasks,arm)
            except Exception as e:
                write_json(root/'fit-errors'/f'{arm}.json',{'type':type(e).__name__,'message':str(e)});raise
            immutable(path,m)
            import numpy
            immutable(root/'fit_resources'/f'{arm}.json',{'wall_seconds':time.monotonic()-started,'numpy_version':numpy.__version__,'solver':'deterministic_full_bfgs','device':'cpu'})
        out[arm]=m['diagnostics']
    immutable(root/'fit_diagnostics.json',out)
    immutable(root/'fitting_weights.json',{a:read_json(root/'gates'/f'{a}.json')['weights'] for a in ARMS})
    immutable(root/'fit_class_and_task_support.json',{a:{k:read_json(root/'gates'/f'{a}.json')[k] for k in ('class_rows','fit_groups','weight_support')} for a in ARMS})
    return out


def tune_thresholds(root):
    audit_checks(root,'threshold_tuning');tasks=labeled_features(root,'threshold_tuning');out={arm:gates.tune(read_json(root/'gates'/f'{arm}.json'),tasks) for arm in ARMS}
    immutable(root/'threshold_selection.json',out);return out


def freeze_policies(root):
    thresholds=read_json(root/'threshold_selection.json');models={a:read_json(root/'gates'/f'{a}.json') for a in ARMS}
    for a,m in models.items():
        gates.validate_model(m)
        if thresholds[a]['model_hash']!=m['model_hash']:raise ValueError('Threshold/gate mismatch')
    receipt={'plan_hash':digest(load(root)),'models':{a:m['model_hash'] for a,m in models.items()},'threshold_hash':digest(thresholds),
             'fit_features':read_json(root/'features/fit.json')['hash'],'tuning_features':read_json(root/'features/threshold_tuning.json')['hash'],
             'primary':'restricted_augmented','formal_risk_certificate':False}
    immutable(root/'frozen_policy_receipt.json',receipt);return receipt


def frozen(root):
    r=read_json(root/'frozen_policy_receipt.json')
    if r!=freeze_policies(root):raise ValueError('Frozen policy mismatch')
    return r


def baselines(s,split):
    out=[]
    for rec in records(s.root,split):
        a,vs,missing=views(s.root,rec);task=PublicTask.from_task(rec['task']);selected={}
        for view,peers in vs.items():
            v=s.call(rec,'R',selection_prompt(task,a,peers),'anchor_inclusive_select')
            allowed={p.candidate_id:p.answer for p in peers if p.status=='ok'}
            if a.status=='ok':allowed['anchor']=a.answer
            selected[view]=asdict(parse_answer(v['raw'],task,v['call']['stop_reason'],selectable=allowed))
        current=a;cycles=[]
        for cycle in range(3):
            v=s.call(rec,'R',reconsider_prompt(task,current),'independent_critique',str(cycle))
            try:
                x=obj(v['raw'],v['call']['stop_reason'])
                if set(x)!={'critique'} or type(x['critique']) is not str or not 0<len(x['critique'])<=600:raise ValueError()
                critique={'status':'ok','text':x['critique']}
            except (ValueError,TypeError):critique={'status':'malformed','text':''}
            v=s.call(rec,'R',reconsider_prompt(task,current,critique),'independent_reconsider',str(cycle))
            current=parse_answer(v['raw'],task,v['call']['stop_reason']);cycles.append(asdict(current))
        out.append({'task_id':rec['task']['task_id'],'selection':selected,'independent_cycles':cycles})
    immutable(s.root/'baselines'/f'{split}.json',out);return out


def import_transfer(root,bundle,sha,mock=False):
    frozen(root)
    from ..studies import forensics as f,adjudication as parent
    from ..studies.adjudication_contracts import from_record,STYLES
    dest=root/'transfer-parent';receipt=f.import_parent(dest,bundle,sha,mock)
    p=parent.load(dest/'parent');_,saved,unknown,_=parent.journal(dest/'parent',p)
    if unknown:raise ValueError('Incomplete parent')
    # Require the identical pristine Qwen3 backbone, not J14 or old short readouts.
    spec=p['models']['J8'].copy();spec['key']='R'
    if spec!=asdict(MODELS['R']):raise ValueError('Transfer anchor model mismatch')
    clean={r['task_id']:r for r in f.lines(dest/'parent/clean_per_task.jsonl') if r['model']=='J8' and r['mode']=='task_only_free'}
    rows=[];labels={};banks={r['task']['task_id']:r for r in read_json(dest/'parent/bank.json')['records']}
    attack_orders={r['task_id']:r['attack_order'] for r in p['eligible']}
    for tid,rec in banks.items():
        bank=from_record(rec);c=clean[tid];v=saved.get(c['key'])
        if v is None:raise ValueError('Raw exact J8 anchor missing')
        anchor=parse_answer(v['raw'],PublicTask.from_task(rec['task']),v['call']['stop_reason'])
        peers=[Answer(x.answer,x.justification,x.status,x.raw,x.candidate_id) for x in bank.candidates]
        row={'task':rec['task'],'group_id':rec['group_id'],'split':'transfer','family':rec['dataset'],'stratum':rec['stratum'],
             'training_allowed':False,'parent_bank_hash':digest(bank),'anchor_result_hash':digest(v),'attack_order':attack_orders.get(tid,[])}
        rows.append(row);labels[tid]={'answer':rec['eval']['answer'],'split':'transfer'}
        immutable(source_file(root,tid),{'record_hash':digest(row),'anchor':asdict(anchor),'peers':[asdict(x) for x in peers]})
    attempts=read_json(dest/'parent/pool.json')['attempts'];pool=[]
    eligible={r['task_id']:r['target'] for r in p['eligible']}
    for a in attempts:pool.append({'task_id':a['task_id'],'style':a['style'],'target':eligible[a['task_id']],'accepted':a['accepted'],'justification':a['justification'],'status':a['validation'],'parent_attempt_hash':digest(a)})
    # Completed parent reader validates all 230 tasks /369 accepted/31 rejected.
    immutable(root/'transfer.json',{'records':rows,'parent_receipt':receipt,'styles':list(STYLES),'source_hash':digest(rows),'labels_hash':digest(labels),'pool_hash':digest({'rows':pool,'hash':digest(pool)}),'bank_hashes':{r['task']['task_id']:digest(read_json(source_file(root,r['task']['task_id']))) for r in rows}})
    immutable(root/'transfer-labels.json',labels);immutable(pool_file(root,'transfer'),{'rows':pool,'hash':digest(pool)})
    return {'tasks':len(rows),'accepted_rewrites':sum(a['accepted'] for a in pool),'training_allowed':False}


def evaluate(s,split):
    if split not in ('source_development_holdout','transfer'):raise ValueError('Evaluation split only')
    receipt=frozen(s.root);build_checks(s,split);baselines(s,split)
    from .metrics import evaluate_records
    out=evaluate_records(s.root,split)
    immutable(s.root/'evaluation'/f'{split}.json',{'policy_hash':digest(receipt),'rows':out,'hash':digest(out)})
    from ..studies.forensics import save_lines
    save_lines(s.root/f'per_task_{split}_results.jsonl',out)
    return {'evaluated_tasks':len(records(s.root,split)),'rows':len(out),'fixture':s.mock}


def preflight(root,cache):
    p=load(root)
    if p['fixture']:raise ValueError('Real preflight cannot use fixtures')
    from ..backends.native import metadata
    receipts={}
    for key in MODELS:
        r=metadata(key,cache,spec=MODELS[key]);immutable(root/'access'/f'{key}.json',r);receipts[key]=r
    immutable(root/'preflight.json',{'models':receipts,'plan_hash':digest(p)});return {'all_models_authorized':True}


class MockBackend:
    """Fictional public-text behavior only; never used on real task records."""
    def __init__(self,key):
        from types import SimpleNamespace
        self.key=key;self.calls=[]
        tok=SimpleNamespace(eos_token_id=2,pad_token_id=2,bos_token_id=1)
        body={'spec':asdict(MODELS[key]),'adapters':[],'precision':'bfloat16','attention':'sdpa','template_hash':digest('fictional-selective-native'),
              'parameters':{k:generation_parameters(tok,{'eos_token_id':2},final=k=='final') for k in ('packet','final')},'fixture':True}
        self.identity={**body,'snapshot':digest(body)}
    def render_messages(self,m):return canonical(m)
    def count_tokens(self,t):return len(t.split())
    def generate(self,req):
        import re
        body=json.loads(req.messages[1].content);system=req.messages[0].content
        if 'Formulate a specific potential error' in system:
            x={'challenge_kind':'inference','alleged_error':'Fictional possible mistake.','check_question':'Which fictional symbol is designated?', 'task_refs':[],'requires_external_knowledge':False}
        elif 'Check the proposed challenge' in system:
            numbers=re.findall(r'symbol (\d+)',body['trusted_task']['question']);expected='B' if numbers and int(numbers[0])%2 else 'A'
            good=body['alternative']['answer']==expected
            x={'baseline_support':'contradicted' if good else 'supported','alternative_support':'supported' if good else 'contradicted',
               'comparative_verdict':'favor_alternative' if good else 'favor_baseline','evidence_basis':'explicit_task','reason':'Fictional assessment, not evidence.'}
        elif 'Rewrite only' in system:x={'justification':'Fictional alternative argument; not a real semantic claim.'}
        elif 'Critically check' in system:x={'critique':'Fictional independent check.'}
        elif 'Choose the anchor' in system:x={'decision_basis':'Fictional selection.','candidate_id':'anchor'}
        elif self.key!='R':x={'answer':{'Q':'B','L':'A','M':'C'}[self.key],'justification':'Fictional natural packet.'}
        else:x={'decision_basis':'Fictional independent answer.','answer':'A'}
        raw=json.dumps(x);rendered=self.render_messages(req.messages);n=self.count_tokens(rendered)
        params={**self.identity['parameters']['final' if req.deterministic else 'packet'],'max_new_tokens':CAP}
        call=CallRecord('base','final',self.identity['snapshot'],req.seed,req.messages,rendered,digest(rendered),self.identity['template_hash'],canonical(params),n,2,'eos',.001)
        self.last_generation={'prompt_ids':[1]*n,'completion_ids':[1,2],'raw':raw,'context_hash':digest(rendered)};self.calls.append(call)
        return raw,call
    def resource_usage(self):return {'mock_only':True,'calls':len(self.calls),'compute_units':None}
    def close(self):pass


def export(root,persistent=None):
    from .metrics import report
    summary=report(root);stamp=time.time_ns();out={}
    for kind in ('PRIVATE','SANITIZED'):
        path=root.parent/'bundles'/f'{RUN_ID}-{kind}-{stamp}.zip'
        if kind=='PRIVATE':r=package(root,path,VERSION+'_private')
        else:
            with tempfile.TemporaryDirectory(dir=root.parent) as d:
                t=Path(d);write_json(t/'summary.json',summary)
                (t/'README.md').write_text('Aggregate development results only. No raw prompts, labels, IDs or learned coefficients. Not full PACT or a risk certificate.\n')
                r=package(t,path,VERSION+'_sanitized')
        out[kind.lower()]=r
        if persistent:persist_bundle(path,persistent/'bundles'/path.name,r['sha256'],timeout_seconds=300)
    checkpoint(root,persistent);return out


def unpack(bundle,sha,root,mock=False):
    if root.exists():raise ValueError('Restore destination must be absent')
    content=read_review(bundle,sha,max_members=60000,max_bytes=512*1024**2,selected_names={'HANDOFF.json','plan.json'},allow_text=True)
    if content['HANDOFF.json']['kind']!=VERSION+'_private' or content['plan.json']['fixture']!=mock:raise ValueError('Matching PRIVATE study bundle required')
    private_root(root,mock)
    with zipfile.ZipFile(bundle) as z:
        for n in z.namelist():
            if n in ('HANDOFF.json','review_checksums.json'):continue
            path=root/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(n))
    inspect(root)
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe restored state; no retry')


def restore(persistent,root,mock=False):
    snaps=sorted((persistent/'snapshots').glob('*'))
    if not snaps:raise ValueError('No durable snapshot')
    latest=snaps[-1];idx=read_json(latest/'index.json')
    if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json') or set(idx['files'])!={'receipt.json','state.zip'}:raise ValueError('Invalid latest snapshot; no fallback')
    def source(n):
        h=idx['files'][n]
        if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Unsafe object identity')
        p=persistent/'objects'/h
        if p.is_symlink() or file_hash(p)!=h:raise ValueError('Corrupt durable object')
        return p
    r=read_json(source('receipt.json'))
    if not r['recovery_safe'] or r['sha256']!=idx['files']['state.zip']:raise ValueError('Latest snapshot unsafe; no fallback')
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        path=Path(d)/'state.zip';storage_operation('bundle-restore',source('state.zip'),path,sha256=r['sha256'],timeout_seconds=600)
        unpack(path,r['sha256'],root,mock)
    if digest(load(root))!=r['plan_hash']:raise ValueError('Receipt differs from restored plan')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',nargs='?',default='inspect',choices=['prepare-source','plan','inspect','preflight','collect-source','acquire-rewrites','build-check-bank','fit-gates','tune-thresholds','freeze-policies','evaluate-core','import-transfer','evaluate-transfer','report','export','restore','import-bundle'])
    p.add_argument('--run-dir',required=True,type=Path);p.add_argument('--source',type=Path);p.add_argument('--exposure',type=Path)
    p.add_argument('--cache-dir',type=Path);p.add_argument('--persistent',type=Path);p.add_argument('--bundle',type=Path);p.add_argument('--sha256')
    p.add_argument('--split',choices=SPLITS);p.add_argument('--mock',action='store_true');p.add_argument('--execute',action='store_true');p.add_argument('--download',action='store_true');p.add_argument('--smoke',action='store_true');p.add_argument('--plan-hash')
    a=p.parse_args(argv);root=a.run_dir
    if a.stage in ('restore','import-bundle'):
        if a.stage=='restore':restore(a.persistent,root,a.mock)
        else:unpack(a.bundle,a.sha256,root,a.mock)
        print(canonical({'restored':True}));return
    with run_lock(root):
        if a.stage=='prepare-source':
            from .data import prepare,fixture_data
            if a.source is None:raise ValueError('--source output path required')
            if a.mock:
                if a.source.exists():raise ValueError('Source exists')
                out=fixture_data();write_json(a.source,out)
            else:
                if a.exposure is None or a.cache_dir is None:raise ValueError('Pinned source cache and reviewed --exposure required')
                private_root(a.source.parent);out=prepare(a.cache_dir,a.source,a.exposure,a.download)
            print(canonical({'source_ready':True,'groups':len(out['records']),'fixture':a.mock}));return
        if a.stage=='plan':
            if a.source is None:raise ValueError('--source prepared file required')
            out=plan(root,read_json(a.source));checkpoint(root,a.persistent);print(canonical({'plan_hash':digest(out),'budgets':LIMITS,'model_calls':0}));return
        q=load(root)
        if q['fixture']!=a.mock:raise ValueError('Explicit fixture/real mismatch')
        if a.stage=='preflight':out=preflight(root,a.cache_dir)
        elif a.stage=='inspect':
            _,i,r,u=inspect(root);out={'attempted':len(i),'committed':len(r),'unresolved':len(u),'recovery_safe':read_json(root/'state.json')['recovery_safe'],'plan_hash':digest(q),'budgets':LIMITS}
        elif a.stage=='fit-gates':
            if code_identity(REPO)!=q['source']:raise ValueError('Pinned source changed')
            out=fit_gates(root)
        elif a.stage=='tune-thresholds':
            if code_identity(REPO)!=q['source']:raise ValueError('Pinned source changed')
            out=tune_thresholds(root)
        elif a.stage=='freeze-policies':
            if code_identity(REPO)!=q['source']:raise ValueError('Pinned source changed')
            out=freeze_policies(root)
        elif a.stage=='import-transfer':out=import_transfer(root,a.bundle,a.sha256,a.mock)
        elif a.stage=='report':
            from .metrics import report
            out=report(root)
        elif a.stage=='export':out=export(root,a.persistent)
        else:
            if not a.execute or a.plan_hash!=digest(q):raise ValueError('Inference requires --execute and exact --plan-hash; offline is default')
            split='source_development_holdout' if a.stage=='evaluate-core' else 'transfer' if a.stage=='evaluate-transfer' else a.split
            if split is None:raise ValueError('--split required')
            if a.smoke and a.stage!='collect-source':raise ValueError('First smoke is source-only')
            if split in ('source_development_holdout','transfer'):frozen(root)
            s=Session(root,execute=True,cache=a.cache_dir,persistent=a.persistent,mock=a.mock)
            try:
                if a.stage=='collect-source':out=collect_source(s,split,a.smoke)
                elif a.stage=='acquire-rewrites':out=acquire(s,split)
                elif a.stage=='build-check-bank':out=build_checks(s,split);out={'feature_tasks':len(out['rows'])}
                else:out=evaluate(s,split)
                s.finish()
            finally:s.close_model()
        if a.stage not in ('export','inspect'):checkpoint(root,a.persistent)
        print(canonical(out))

if __name__=='__main__':main()
