"""Explicit per-dataset heterogeneous breadth stages, reusing native models and journals."""
import argparse
from collections import Counter
import dataclasses as dc
from itertools import permutations
import json
import os
from pathlib import Path
import random
import shutil
import tempfile
import time
from types import SimpleNamespace
import zipfile

from ..artifacts import ShardStore, run_lock, sync_run
from ..backends import Request
from ..backends.registry import registry as model_registry
from ..environment import code_identity, runtime_fingerprint
from ..schemas import CallRecord
from ..storage import persist_bundle
from ..training.receiver import JournalBackend, call_from_dict
from ..training.colab import review_bundle
from ..training.feasibility import read_review
from ..util import digest, canonical, node_seed, read_json, write_json, file_hash
from ..benchmarks.registry import REGISTRY, SEED, VARIANT, PARENT_MODEL_HASH, budget, registry
from ..benchmarks.contracts import BenchmarkInput, CONTRACTS, messages, parse
from ..benchmarks.scoring import score, evaluator_identity, scoring_job, import_result
from .heterogeneity import immutable

TEAMS=('QQQ','LLL','MMM','QLM')

def freeze(data,code,fixture=False):
    if digest(model_registry())!=PARENT_MODEL_HASH:raise ValueError('Completed parent model identities changed')
    name=data['dataset'];spec=REGISTRY[name];rows=data['selected']
    if not fixture and len(rows)!=spec.n:raise ValueError('Exact characterization quota required')
    parts=data['manifest']['partitions'];partition_sets=[set(parts[k]) for k in ('characterization_dev','confirmation_locked','reserve_locked')]
    if any(partition_sets[i]&partition_sets[j] for i in range(3) for j in range(i)):
        raise ValueError('Partition overlap')
    if not fixture:
        if data['receipt']['repository']!=spec.repository or data['receipt']['revision']!=spec.revision:raise ValueError('Official source identity changed')
        groups=data['manifest']['group_by_id']
        group_sets=[{groups[k] for k in ids} for ids in partition_sets]
        if any(group_sets[i]&group_sets[j] for i in range(3) for j in range(i)):raise ValueError('Group leakage')
    if any(r['task']['split']!='characterization_dev' for r in rows):raise ValueError('Locked partition cannot generate')
    if [r['task']['task_id'] for r in rows]!=data['manifest']['partitions']['characterization_dev']:raise ValueError('Selection changed')
    bindings={}
    for stratum in sorted({r['stratum'] for r in rows}):
        ids=sorted(r['task']['task_id'] for r in rows if r['stratum']==stratum)
        rng=random.Random(node_seed(SEED,name,stratum,'display'));rng.shuffle(ids)
        perms=list(permutations('QLM'));rng.shuffle(perms)
        for i,tid in enumerate(ids):
            bindings[tid]={t:[{'family':f,'replica':j,'slot':j} for j,f in enumerate(perms[i%6] if t=='QLM' else t)] for t in TEAMS}
    return {'schema_version':1,'variant':VARIANT,'run_id':'pact-breadth-'+name+'-001','dataset':name,
            'data_hash':digest(data),'data':data,'models':model_registry(),'code':code,'fixture':fixture,
            'seed':SEED,'profile':dc.asdict(spec),'budgets':budget(name,len(rows)),
            'contracts':CONTRACTS,'evaluator':evaluator_identity(spec.kind),'bindings':bindings,
            'smoke_ids':[r['task']['task_id'] for r in rows[:2]],'training_allowed':False,
            'parent_plan':'b972e06e3b8e69f8e53053d238b7fa7f04c1ddb331654b7555262021d47a506f'}


def load(root):
    p=read_json(root/'plan.json')
    if digest(p)!=read_json(root/'state.json')['plan_hash']:raise ValueError('Plan hash mismatch')
    if canonical(p)!=canonical(freeze(p['data'],p['code'],p['fixture'])):raise ValueError('Frozen design/source/evaluator changed')
    return p


def schedule(plan):
    out=[];s=plan['profile']
    for item in plan['data']['selected']:
        tid=item['task']['task_id']
        for f in 'QLM':
            for j in range(3):out.append({'task_id':tid,'stage':'private','model':f,'replica':j,'slot':j,'team':None,'phase':'A'})
        if not s['core']:continue
        for team in TEAMS:
            for b in plan['bindings'][tid][team]:out.append({'task_id':tid,'stage':'revision','model':b['family'],'replica':b['replica'],'slot':b['slot'],'team':team,'phase':'B'})
            for stage in ('synthesis','debate'):out.append({'task_id':tid,'stage':stage,'model':'R','replica':None,'slot':None,'team':team,'phase':'B'})
        out.append({'task_id':tid,'stage':'task_only','model':'R','replica':None,'slot':None,'team':None,'phase':'B'})
    for row in out:
        row['cap']=s['final'] if row['model']=='R' else s['packet']
        row['seed']=node_seed(SEED,plan['dataset'],row['task_id'],plan['models'][row['model']],row['stage'],row['replica'])
        row['key']=digest([plan['data_hash'],plan['models'],plan['contracts'],s,row])
    return out


def request_for(plan,row,rows,results):
    item=next(x for x in plan['data']['selected'] if x['task']['task_id']==row['task_id']);task=BenchmarkInput.from_dict(item['task'])
    def source(f,replica,stage='private',team=None):
        r=next(x for x in rows if x['task_id']==task.task_id and x['stage']==stage and x['model']==f and x['replica']==replica and x['team']==team)
        if r['key'] not in results:raise ValueError('Missing frozen source packet')
        return r['key'],results[r['key']]['raw']
    deps=[];peers=[];own=None
    if row['stage']!='private' and row['stage']!='task_only':
        initial=[x for x in rows if x['task_id']==task.task_id and x['stage']=='private']
        if any(x['key'] not in results for x in initial):raise ValueError('Nine-packet barrier incomplete')
        for b in plan['bindings'][task.task_id][row['team']]:
            revised=row['stage']=='debate'
            key,raw=source(b['family'],b['replica'],'revision' if revised else 'private',row['team'] if revised else None)
            deps.append(key)
            if row['stage']=='revision' and b['slot']==row['slot']:own=(b['slot'],raw)
            else:peers.append((b['slot'],raw))
    final=row['model']=='R'
    request=Request(task,messages(task,row['stage'],own,peers),'base' if final else f"agent-{row['slot']}",
                    'final' if final else row['stage'],row['seed'],row['cap'],final)
    return request,deps


def journal(root,plan):
    rows=schedule(plan);expected={digest([r['key'],0]):r for r in rows};results={};intents={};unknown=[]
    store=ShardStore(root/'calls')
    for path in (root/'call-intents').glob('*.json'):
        key=path.stem;i=read_json(path);r=expected.get(key)
        if r is None or i.get('record_id')!=r['key'] or i.get('max_tokens')!=r['cap'] or i.get('slot')!=0 or i.get('work_id')!=key:raise ValueError('Unplanned attempt')
        intents[key]=i;p=store.path(key)
        if not p.exists() or not p.with_suffix('.sha256').exists():unknown.append(key);continue
        value=store.read(key)
        if value['intent']!=i:raise ValueError('Intent/result changed')
        results[r['key']]=value
    if any(p.stem not in intents or p.suffix not in ('.json','.sha256') for p in (root/'calls/shards').glob('*')):raise ValueError('Unjournaled call artifact')
    for phase in ('A','B'):
        phase_intents=[i for k,i in intents.items() if expected[k]['phase']==phase]
        if len(phase_intents)>plan['budgets'][phase]['calls'] or sum(i['max_tokens'] for i in phase_intents)>plan['budgets'][phase]['tokens']:raise ValueError('Phase budget exceeded')
    return intents,results,unknown,rows


class BreadthJournal(JournalBackend):
    def __init__(self,backend,root,plan):
        self.backend,self.root,self.plan=backend,root,plan;self.identity=backend.identity
        self.intents,results,unknown,_=journal(root,plan)
        if unknown:raise ValueError('Unresolved attempt; no regeneration')
        self.results={digest([k,0]):v for k,v in results.items()};self.store=ShardStore(root/'calls')
        self.budget={'generation_calls_upper_bound':sum(x['calls'] for x in plan['budgets'].values()),
                     'generated_tokens_upper_bound':sum(x['tokens'] for x in plan['budgets'].values())}
        self.calls=[];self.seen=set();self.generation_tokens={};self.new_calls=0;self.stop_after=None;self.before_new=lambda:None
    def validate_request(self,r):
        if r.task.split!='characterization_dev' or r.max_tokens!=(self.plan['profile']['final'] if r.deterministic else self.plan['profile']['packet']):raise ValueError('Request outside design')
    def _validate(self,request,intent,result):
        self.validate_request(request);c=call_from_dict(result['call']);t=result['tokens']
        params=dict(self.identity['parameters']['final' if request.deterministic else 'packet']);params['max_new_tokens']=request.max_tokens
        if (digest(request)!=intent['request_hash'] or result['intent']!=intent or c.messages!=request.messages or c.seed!=request.seed or
            c.actor!=request.actor or c.phase!=request.phase or c.snapshot!=self.identity['snapshot'] or c.template_hash!=self.identity['template_hash'] or
            c.context_hash!=digest(c.rendered_prompt) or t['context_hash']!=c.context_hash or t['raw']!=result['raw'] or
            c.input_tokens!=len(t['prompt_ids']) or c.output_tokens!=len(t['completion_ids']) or json.loads(c.parameters_json)!=params):raise ValueError('Request/token/model identity changed')
        if any(type(v) is not int or v<0 for v in t['prompt_ids']+t['completion_ids']):raise ValueError('Invalid token IDs')
        if not 0<=c.output_tokens<=request.max_tokens or not 0<=c.elapsed_seconds<float('inf'):raise ValueError('Invalid call accounting')
        overflow=c.input_tokens+request.max_tokens>self.plan['profile']['context']
        if (c.stop_reason=='context_overflow')!=overflow or (overflow and (c.output_tokens or result['raw'])):raise ValueError('Context boundary mismatch')
        eos=params['eos_token_id'];eos=eos if isinstance(eos,list) else [eos]
        if c.stop_reason=='eos' and (not t['completion_ids'] or t['completion_ids'][-1] not in eos):raise ValueError('Native EOS mismatch')
        if c.stop_reason not in ('eos','length','context_overflow'):raise ValueError('Unknown stop')
        return c


def reconstruct(root,plan):
    intents,results,unknown,rows=journal(root,plan)
    for r in rows:
        if r['key'] not in results:continue
        identity=read_json(root/'identities'/f"{r['model']}.json")
        if identity['spec']!=plan['models'][r['model']] or identity.get('adapters')!=[]:raise ValueError('Model isolation changed')
        if identity['snapshot']!=digest({k:v for k,v in identity.items() if k!='snapshot'}):raise ValueError('Model identity hash mismatch')
        if not plan['fixture']:
            access=read_json(root/'access_preflight.json')['models'][r['model']]
            if any(identity.get(k)!=v for k,v in access.items()):raise ValueError('Preflight/model mismatch')
        request,deps=request_for(plan,r,rows,results)
        validator=object.__new__(BreadthJournal);validator.plan=plan;validator.identity=identity
        validator._validate(request,intents[digest([r['key'],0])],results[r['key']])
        if read_json(root/'dependencies'/f"{r['key']}.json")!={'request':r,'sources':deps,'identity_hash':digest(identity)}:raise ValueError('Source dependency changed')
    return intents,results,unknown,rows


def collect(root,plan,stage,model,backend,*,smoke=False,stop_after=None):
    _,results,unknown,rows=reconstruct(root,plan)
    if unknown:raise ValueError('Unresolved call')
    selected=[r for r in rows if r['model']==model and (r['stage']==stage or stage=='readout' and r['model']=='R') and (not smoke or r['task_id'] in plan['smoke_ids'])]
    if not selected:raise ValueError('Stage/model outside plan')
    if stage!='private' and any(r['key'] not in results for r in rows if r['phase']=='A'):raise ValueError('Phase A private bank incomplete')
    for r in selected:request_for(plan,r,rows,results)
    immutable(root/'identities'/f'{model}.json',backend.identity)
    wrapper=BreadthJournal(backend,root,plan);n=0
    for r in selected:
        if r['key'] in results:continue
        if stop_after is not None and n>=stop_after:break
        req,deps=request_for(plan,r,rows,results);wrapper.begin_record(r['key']);wrapper.generate(req)
        results[r['key']]=wrapper.results[digest([r['key'],0])]
        immutable(root/'dependencies'/f"{r['key']}.json",{'request':r,'sources':deps,'identity_hash':digest(backend.identity)})
        n+=1
        if n==1 or n%5==0:print(model,stage,'new committed calls:',n,flush=True)
        if results[r['key']]['call']['stop_reason']=='context_overflow':
            write_json(root/'resource_stop.json',{'status':'context_overflow','request_key':r['key']})
            return {'new_attempts':n,'stage_complete':False,'status':'context_overflow'}
    return {'new_attempts':n,'stage_complete':all(r['key'] in results for r in selected)}


def checkpoint(root,persistent):
    if persistent is None:return
    stamp=time.time_ns();bundle=review_bundle(root,root.parent/'bundles'/f'{root.name}-checkpoint-{stamp}.zip',{},kind=VARIANT+'_private',scientific_status='development_only',include_markdown=True,max_metadata_bytes=512*1024**2)
    with tempfile.TemporaryDirectory(dir=root.parent) as temp:
        compact=Path(temp);shutil.copyfile(bundle['path'],compact/'state.zip')
        write_json(compact/'receipt.json',{'sha256':bundle['sha256'],'plan_hash':digest(load(root)),'recovery_safe':read_json(root/'state.json')['recovery_safe']})
        sync_run(compact,persistent,timeout_seconds=300)


def unpack(bundle,sha,root):
    if root.exists():raise ValueError('Import destination must be absent')
    content=read_review(bundle,sha,max_members=60000,max_bytes=512*1024**2,allow_text=True)
    if content['HANDOFF.json']['kind']!=VARIANT+'_private':raise ValueError('Wrong bundle kind')
    with zipfile.ZipFile(bundle) as z:
        for name in content:
            if name=='HANDOFF.json':continue
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
            if '/shards/' in name:path.with_suffix('.sha256').write_text(file_hash(path))
    reconstruct(root,load(root))


def restore(persistent,root):
    snaps=sorted(p for p in (persistent/'snapshots').iterdir() if p.is_dir())
    if not snaps:raise ValueError('No snapshots')
    snap=snaps[-1];index=read_json(snap/'index.json')
    if (snap/'COMPLETE').read_text().strip()!=file_hash(snap/'index.json') or set(index['files'])!={'receipt.json','state.zip'}:raise ValueError('Latest snapshot invalid')
    def obj(name):
        sha=index['files'][name]
        if not __import__('re').fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid object hash')
        p=persistent/'objects'/sha
        if not p.is_file() or p.is_symlink() or file_hash(p)!=sha:raise ValueError('Snapshot checksum mismatch')
        return p
    receipt=read_json(obj('receipt.json'))
    if not receipt['recovery_safe']:raise ValueError('Unsafe latest snapshot; no fallback')
    if receipt['sha256']!=index['files']['state.zip']:raise ValueError('Receipt mismatch')
    from ..storage import storage_operation
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent) as temp:
        local=Path(temp)/'state.zip'
        storage_operation('bundle-restore',obj('state.zip'),local,sha256=receipt['sha256'],timeout_seconds=300)
        unpack(local,receipt['sha256'],root)
    if not read_json(root/'state.json')['recovery_safe'] or digest(load(root))!=receipt['plan_hash']:raise ValueError('Unsafe/mismatched restored state')


def preflight(root,cache,*,scorer_python=None,allow_pending=False):
    from ..backends.native import metadata
    from ..backends.registry import REGISTRY as MODELS,render_native
    from huggingface_hub import snapshot_download,try_to_load_from_cache
    from transformers import AutoTokenizer
    import torch
    plan=load(root)
    if plan['fixture']:raise ValueError('No real models for fixture')
    scorer_readiness={'ready':True,'mode':'strict_mcq'}
    if plan['profile']['kind']=='math_free_response':
        from ..benchmarks.scoring import math_worker
        import sys
        for item in plan['data']['selected']:
            result=math_worker({'kind':'math_free_response','eval':item['eval'],
                'prediction':item['eval']['answer'],'identity':plan['evaluator']},scorer_python or sys.executable)
            if result['availability']!='scored' or not result['full_success']:
                raise ValueError('Math scorer or gold reference unavailable; no generation')
        scorer_readiness={'ready':True,'mode':'gold_parse_checked','scorer':plan['evaluator']}
    elif plan['profile']['kind'] in ('python_program','native_livebench'):
        try:
            from ..benchmarks.isolation import Bubblewrap
            if scorer_python is None:raise ValueError('Evaluator runtime missing')
            worker=Bubblewrap(scorer_python);receipt=worker.probe()
            if plan['profile']['kind']=='python_program':
                item=plan['data']['selected'][0];problem=item['eval']['problem']
                body={'kind':'python_program','eval':item['eval'],'prediction':problem['prompt']+problem['canonical_solution'],
                      'identity':plan['evaluator'],'purpose':'official_scorer_preflight_no_model_call'}
                validation=worker.run({**body,'job_hash':digest(body)})
                if validation['score']['availability']!='scored' or not validation['score']['full_success']:
                    raise ValueError('Official expanded-test evaluator validation failed')
                scorer_readiness={'ready':True,'mode':'isolated_official_expanded_test_checked','sandbox':receipt,'validation':validation}
            else:
                scorer_readiness={'ready':False,'mode':'isolated_execution_capable_official_scorer_validation_pending','sandbox':receipt}
        except Exception:
            scorer_readiness={'ready':False,'mode':'safe_execution_unavailable'}
        if not scorer_readiness['ready'] and not allow_pending:raise ValueError('Explicit --allow-pending-scoring required until official scorer validation')
    immutable(root/'scorer_readiness.json',scorer_readiness)
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1 or not torch.cuda.is_bf16_supported():raise ValueError('One BF16 GPU required')
    cache.mkdir(parents=True,exist_ok=True)
    resolved={k:metadata(k,cache,token=os.environ.get('HF_TOKEN')) for k in 'QLMR'}
    missing=0
    for v in resolved.values():
        for n,m in v['weight_metadata'].items():
            p=try_to_load_from_cache(v['spec']['repository'],n,revision=v['spec']['revision'],cache_dir=str(cache))
            if not isinstance(p,str) or not Path(p).is_file():missing+=m['bytes']
    if shutil.disk_usage(cache).free<missing+8*1024**3:raise ValueError('Insufficient cache disk')
    if os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')<12*1024**3:raise ValueError('Insufficient host RAM')
    lengths={}
    for k in 'QLMR':
        v=resolved[k];p=snapshot_download(v['spec']['repository'],revision=v['spec']['revision'],cache_dir=str(cache),allow_patterns=list(v['metadata_hashes']),local_files_only=True)
        tokenizer=AutoTokenizer.from_pretrained(p,trust_remote_code=False,local_files_only=True)
        counts=[]
        for item in plan['data']['selected']:
            task=BenchmarkInput.from_dict(item['task']);rendered=render_native(tokenizer,messages(task,'task_only' if k=='R' else 'private'),MODELS[k])
            count=len(tokenizer(rendered,add_special_tokens=False)['input_ids']);counts.append(count)
            if count+(plan['profile']['final'] if k=='R' else plan['profile']['packet'])>plan['profile']['context']:raise ValueError('Selected public prompt context overflow; no truncation')
        lengths[k]=counts
    access={'models':resolved,'runtime':runtime_fingerprint(),'all_authorized':True,'source_prompt_lengths':lengths}
    immutable(root/'access_preflight.json',access)
    write_json(root/'environment.json',{'runtime':runtime_fingerprint(),'gpu':torch.cuda.get_device_name(0)})
    return {'all_model_access':True,'public_prompts_fit':True,'scorer':plan['evaluator']}


def execute(root,persistent,stage,model,cache,*,smoke=False,stop_after=None,mock=False):
    plan=load(root)
    if plan['fixture']!=mock:raise ValueError('Fixture/real execution mismatch')
    if plan['code']!=code_identity(Path(__file__).resolve().parents[3]):raise ValueError('Pinned source changed')
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe state; no automatic retry')
    if (root/'resource_stop.json').exists():raise ValueError('Recorded resource stop; no automatic continuation')
    _,results,unknown,rows=reconstruct(root,plan)
    if unknown:raise ValueError('Unresolved attempt')
    selected=[r for r in rows if r['model']==model and (r['stage']==stage or stage=='readout' and r['model']=='R') and (not smoke or r['task_id'] in plan['smoke_ids'])]
    if not selected:raise ValueError('Stage not planned')
    if all(r['key'] in results for r in selected):return {'already_complete':True}
    if stage!='private':
        if not plan['profile']['core'] or any(r['key'] not in results for r in rows if r['phase']=='A'):raise ValueError('Phase B requires complete core private bank')
    for r in selected:request_for(plan,r,rows,results)
    if not mock:
        access=read_json(root/'access_preflight.json')
        if not access['all_authorized'] or access['runtime']!=runtime_fingerprint():raise ValueError('All-model preflight/runtime mismatch')
    state=read_json(root/'state.json');state['recovery_safe']=False;write_json(root/'state.json',state);checkpoint(root,persistent)
    backend=None;started=time.monotonic()
    try:
        print('Loading',model,stage,flush=True)
        if mock:
            from ..benchmarks.fixtures import MockNative
            backend=MockNative(model,plan)
        else:
            from ..backends.native import NativeBackend
            class ProfileBackend(NativeBackend):
                def generation_parameters(self,request):return {**super().generation_parameters(request),'max_new_tokens':request.max_tokens}
            backend=ProfileBackend(model,access['models'][model],cache,token=os.environ.get('HF_TOKEN'))
            backend.config.limits=dc.replace(backend.config.limits,context=plan['profile']['context'])
        result=collect(root,plan,stage,model,backend,smoke=smoke,stop_after=stop_after)
        write_json(root/'resources'/f'{time.time_ns()}.json',{'model':model,'stage':stage,'wall_seconds':time.monotonic()-started,**backend.resource_usage()})
    finally:
        if backend is not None:backend.close()
    state['recovery_safe']=True;write_json(root/'state.json',state)
    try:checkpoint(root,persistent)
    except BaseException:
        state['recovery_safe']=False;write_json(root/'state.json',state);raise
    return result


def score_run(root,*,python=None):
    plan=load(root);_,results,_,rows=reconstruct(root,plan);store=ShardStore(root/'scores');count=0
    for r in rows:
        if r['key'] not in results:continue
        item=next(x for x in plan['data']['selected'] if x['task']['task_id']==r['task_id']);task=BenchmarkInput.from_dict(item['task']);result=results[r['key']]
        key=digest([r['key'],digest(result),plan['evaluator']])
        if store.path(key).exists():continue
        job=scoring_job(task,item['eval'],result,r['key'])
        if task.kind in ('python_program','native_livebench'):
            immutable(root/'scoring-jobs'/f"{job['job_hash']}.json",job)
        intent={'schema_version':1,'job_hash':job['job_hash'],'score_key':key,'evaluator':plan['evaluator']}
        path=root/'score-intents'/f'{key}.json'
        if path.exists():raise ValueError('Unresolved scorer attempt; preserve and inspect')
        write_json(path,intent)
        if plan['fixture']:
            from ..benchmarks.fixtures import fixture_score
            out=fixture_score(task,item['eval'],result)
        else:out=score(task,item['eval'],result['raw'],final=r['model']=='R',stop=result['call']['stop_reason'],python=python)
        store.put(key,{'schema_version':1,'work_id':key,'request_key':r['key'],'job_hash':job['job_hash'],'score':out,'evaluator':plan['evaluator']});count+=1
    return {'new_score_records':count}


def import_scores(root,path):
    plan=load(root);store=ShardStore(root/'imported-scores');n=0
    payload=read_json(path)
    for result in payload['results']:
        job=read_json(root/'scoring-jobs'/f"{result['job_hash']}.json")
        expected=dict(job);expected.pop('job_hash')
        if digest(expected)!=job['job_hash'] or job['identity']!=plan['evaluator']:raise ValueError('Scorer job changed')
        out=import_result(job,result);key=job['job_hash']
        store.put(key,{'schema_version':1,'work_id':key,'request_key':job['request_key'],'score':out,'receipt':result});n+=1
    return {'imported':n,'trust_boundary':'external worker provenance is user-supplied; hashes are not remote attestation'}


def report(root):
    from ..benchmarks.metrics import reports
    plan=load(root);intents,results,unknown,rows=reconstruct(root,plan);scores={}
    for folder in ('scores','imported-scores'):
        store=ShardStore(root/folder)
        for path in (root/folder/'shards').glob('*.json'):
            v=store.read(path.stem)
            if folder=='scores' and v['evaluator']!=plan['evaluator']:raise ValueError('Scorer identity changed')
            if v['request_key'] not in results:raise ValueError('Score without generation')
            row=next(r for r in rows if r['key']==v['request_key'])
            item=next(x for x in plan['data']['selected'] if x['task']['task_id']==row['task_id'])
            expected_job=scoring_job(BenchmarkInput.from_dict(item['task']),item['eval'],results[row['key']],row['key'])
            if folder=='scores':
                expected_key=digest([row['key'],digest(results[row['key']]),plan['evaluator']])
                if path.stem!=expected_key or v['job_hash']!=expected_job['job_hash']:raise ValueError('Score/request identity mismatch')
            else:
                if path.stem!=expected_job['job_hash'] or v['score']!=import_result(expected_job,v['receipt']):raise ValueError('Imported scoring receipt mismatch')
            scores[v['request_key']]=v['score']
    teams,comparisons,tables=reports(plan,results,rows,scores)
    phases={}
    for phase in ('A','B'):
        selected=[r for r in rows if r['phase']==phase];keys={r['key'] for r in selected};present=keys&results.keys()
        scored=[scores[k] for k in present if k in scores and scores[k]['availability']=='scored']
        executed=bool(present);complete=bool(keys) and len(present)==len(keys) and len(scored)==len(keys) and not unknown and read_json(root/'state.json')['recovery_safe']
        phases[phase]={'intended':len(keys),'generated':len(present),'scored':len(scored),
                       'status':'complete' if complete else 'partial' if executed else 'not_executed' if keys else 'not_authorized',
                       'scientific_result':'mock_only' if plan['fixture'] else 'development_diagnostic' if complete else None}
    out={'schema_version':1,'dataset':plan['dataset'],'plan_hash':digest(plan),'source_code':plan['code'],
         'fixture':plan['fixture'],'models':plan['models'],'source':plan['data']['receipt'],'evaluator':plan['evaluator'],
         'phases':phases,'teams':teams,'comparisons':comparisons,
         'recovery_safe':read_json(root/'state.json')['recovery_safe'],
         'accounting':{'attempted':len(intents),'committed':len(results),'unresolved':len(unknown),
                       'reserved_tokens':sum(i['max_tokens'] for i in intents.values()),'budgets':plan['budgets'],
                       'input_tokens':sum(v['call']['input_tokens'] for v in results.values()),
                       'output_tokens':sum(v['call']['output_tokens'] for v in results.values()),
                       'scoring_attempts':len(list((root/'score-intents').glob('*.json'))),'optimizer_updates':0,'compute_units':None},
         'scoring_status':dict(Counter(v['availability'] for v in scores.values())),
         'stop_reasons':dict(Counter(v['call']['stop_reason'] for v in results.values())),
         'readiness':{'schema_compatible':True,'partition_locked':True,'response_contract_ready':True,
                      'access_ready':(root/'access_preflight.json').exists(),'runtime_ready':(root/'access_preflight.json').exists(),
                      'scorer_ready':read_json(root/'scorer_readiness.json')['ready'] if (root/'scorer_readiness.json').exists() else None,
                      'generation_completed':phases['A']['generated']==phases['A']['intended'],
                      'communication_completed':phases['B']['generated']==phases['B']['intended'] if phases['B']['intended'] else None,
                      'scoring_completed':all(v['generated']==v['scored'] for v in phases.values()) and bool(results)},
         'interpretation':'Development subsets, not official leaderboards. Phase A measures availability only. No automatic follow-up.'}
    # Phase-A summaries must not masquerade as measured zero communication effects.
    if phases['B']['status'] in ('not_executed','not_authorized'):
        for t in teams.values():
            for summary in [t['complete_case'],*t['by_stratum'].values()]:
                for k in ('transitions','utilization','construction','erasure','new_availability','readout_loss','readout_construction','private_readout_loss','private_readout_construction','hold','repair','decomposition','opportunities','opportunities_by_family','opportunities_by_N0','opportunities_by_family_and_N0'):
                    summary[k]=None
                summary['communication_status']=phases['B']['status']
                for protocol in ('synthesis','debate','revised_vote','task_only'):
                    summary['terminal'][protocol]=None
                    summary['terminal_full_cohort_lower_bound'][protocol]=None
    write_json(root/'summary.json',out);write_json(root/'per_task_metrics.json',tables)
    lines=['# Benchmark breadth review','',f"Dataset: {plan['dataset']}; Phase A: {phases['A']['status']}; Phase B: {phases['B']['status']}",'',out['interpretation'],'',
           '| Team | Scored private tasks | Coverage | Gain over best member |','|---|---:|---:|---:|']
    for team,v in teams.items():
        t=v['complete_case'];lines.append(f"| {team} | {t['observed_private_tasks']} | {t['coverage']['numerator']}/{t['coverage']['denominator']} | {t['gain']['numerator']}/{t['gain']['denominator']} |")
    (root/'report.md').write_text('\n'.join(lines)+'\n');return out


def export(root,persistent):
    out=report(root);stamp=time.time_ns();bundles=root.parent/'bundles'
    (root/'CODEX_HANDOFF.md').write_text('Private benchmark development evidence. No weights. Pending code scores are not failures. Locked cohorts must not generate. No automatic next experiment.\n')
    private=review_bundle(root,bundles/f'{root.name}-PRIVATE-{stamp}.zip',{},kind=VARIANT+'_private',scientific_status='mock_only' if out['fixture'] else 'development_only',include_markdown=True,max_metadata_bytes=512*1024**2)
    with tempfile.TemporaryDirectory() as temp:
        public=Path(temp);write_json(public/'summary.json',out);(public/'report.md').write_text((root/'report.md').read_text())
        sanitized=review_bundle(public,bundles/f'{root.name}-SANITIZED-{stamp}.zip',{},kind=VARIANT+'_sanitized',scientific_status='development_only',include_markdown=True,max_metadata_bytes=512*1024**2)
    for b in (private,sanitized):
        print(canonical(b),flush=True)
        if persistent:persist_bundle(Path(b['path']),persistent/'bundles'/Path(b['path']).name,b['sha256'],timeout_seconds=300)
    return {'private':private,'sanitized':sanitized}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['plan','preflight','smoke','private','revisions','readout','score','report','export','restore','audit','export-jobs','import-scores'])
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--persistent',type=Path)
    p.add_argument('--data',type=Path);p.add_argument('--cache-dir',type=Path);p.add_argument('--plan-hash')
    p.add_argument('--phase',choices=['A','B'],default='A');p.add_argument('--model',choices=list('QLM'))
    p.add_argument('--execute',action='store_true');p.add_argument('--mock',action='store_true');p.add_argument('--stop-after',type=int)
    p.add_argument('--allow-pending-scoring',action='store_true');p.add_argument('--bundle',type=Path);p.add_argument('--sha256');p.add_argument('--scores',type=Path);p.add_argument('--scorer-python',type=Path)
    a=p.parse_args(argv);root=a.run_dir
    if not a.mock:
        from .gpqa_data import outside_git
        outside_git(root)
    if a.stage=='audit':
        unpack(a.bundle,a.sha256,root);old=read_json(root/'summary.json');new=report(root)
        if old!=new:raise ValueError('Report mismatch')
        print(canonical({'audit':'passed','phases':new['phases']}));return
    if a.stage=='restore':restore(a.persistent,root);return
    with run_lock(root):
        if a.stage=='plan':
            if (root/'plan.json').exists():raise ValueError('Never re-plan an existing run')
            if a.data is None:p.error('--data required')
            data=read_json(a.data)
            if bool(data.get('fixture'))!=a.mock:raise ValueError('Fixture flag mismatch')
            plan=freeze(data,code_identity(Path(__file__).resolve().parents[3]),a.mock)
            if root.name!=plan['run_id']:raise ValueError('Fixed per-dataset run ID required')
            write_json(root/'plan.json',plan);write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
            for name,value in [('benchmark_registry',registry()),('budget_plan',plan['budgets']),('dataset_group_exposure_manifest',data['manifest']),('response_contracts',CONTRACTS),('source_access_receipts',data['receipt'])]:write_json(root/(name+'.json'),value)
            checkpoint(root,a.persistent);print(canonical({'plan_hash':digest(plan),'budget':plan['budgets']}));return
        plan=load(root)
        if a.stage in ('report','export'):
            out=report(root) if a.stage=='report' else export(root,a.persistent)
            print(canonical(out if a.stage=='export' else {'phases':out['phases'],'accounting':out['accounting']}));return
        if a.stage=='export-jobs':
            jobs=[read_json(f) for f in (root/'scoring-jobs').glob('*.json')]
            write_json(root/'scoring_jobs.json',{'jobs':jobs,'plan_hash':digest(plan)});print(canonical({'jobs':len(jobs),'path':str(root/'scoring_jobs.json')}));return
        if a.plan_hash!=digest(plan):p.error('Exact --plan-hash required')
        if a.stage=='import-scores':print(canonical(import_scores(root,a.scores)));checkpoint(root,a.persistent);return
        if a.stage=='score':print(canonical(score_run(root,python=a.scorer_python)));checkpoint(root,a.persistent);return
        if not a.execute:p.error('--execute required for access or inference')
        if a.stage=='preflight':print(canonical(preflight(root,a.cache_dir,scorer_python=a.scorer_python,allow_pending=a.allow_pending_scoring)));checkpoint(root,a.persistent);return
        if not a.mock and (a.persistent is None or a.cache_dir is None):p.error('Real stages require --persistent and --cache-dir')
        if a.stop_after is not None and a.stop_after<=0:p.error('Positive stop-after required')
        expected='B' if a.stage in ('revisions','readout') else 'A'
        if a.phase!=expected:p.error('Stage/phase mismatch')
        if a.stage=='smoke':
            if a.stop_after:p.error('Smoke is the included two-task prefix')
            for k in 'QLM':
                result=execute(root,a.persistent,'private',k,a.cache_dir,smoke=True,mock=a.mock)
                if result.get('status')=='context_overflow':raise ValueError('Resource stop; preserve completed evidence')
        else:
            if a.stage in ('private','revisions') and not a.model:p.error('--model required')
            print(canonical(execute(root,a.persistent,'revision' if a.stage=='revisions' else a.stage,'R' if a.stage=='readout' else a.model,a.cache_dir,stop_after=a.stop_after,mock=a.mock)))


def cli(argv=None):
    try:main(argv)
    except Exception as exc:
        # Never print Hub credentials, benchmark text or hidden tests on errors.
        import traceback
        frames=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]
        print(canonical({'status':'stopped','error_type':type(exc).__name__,'locations':frames,'action':'preserve state; no automatic retry'}))
        raise SystemExit(1) from None

if __name__=='__main__':cli()
