"""Inference-only heterogeneous complementarity; explicit model-major Colab stages."""
import argparse
from collections import Counter
import dataclasses as dc
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import zipfile

from ..artifacts import ShardStore,run_lock,sync_run
from ..backends import Request
from ..environment import code_identity,runtime_fingerprint,versions
from ..parsing import parse_answer
from ..protocol import private_prompt,revision_prompt,envelope,safe_json,trusted_input,READOUT_INSTRUCTION,readout_prompt
from ..schemas import Message,PrivatePacket,DeliveredMessage,task_from_dict
from ..storage import persist_bundle,storage_operation
from ..training.colab import review_bundle
from ..training.feasibility import read_review
from ..training.receiver import JournalBackend,call_from_dict
from ..util import canonical,digest,file_hash,read_json,write_json
from .heterogeneity_plan import RUN_ID,VARIANT,BUDGET,TEAMS,freeze_plan,pilot_source,schedule,load_plan


def immutable(path,value):
    if path.exists() and read_json(path)!=value:raise ValueError('Immutable heterogeneous artifact changed')
    if not path.exists():write_json(path,value)


def initialize(root,source,code,fixture=False):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    if (root/'plan.json').exists():raise ValueError('Existing run; never re-plan or reset budgets')
    p=freeze_plan(source,code,fixture)
    write_json(root/'plan.json',p);write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':True})
    write_json(root/'resolved_config.json',{k:v for k,v in p.items() if k not in ('source','team_bindings')});
    write_json(root/'model_registry.json',p['models']);write_json(root/'team_bindings.json',p['team_bindings'])
    write_json(root/'source_exposure_manifest.json',{'exposure':p['exposure'],'pilot_sha':source['archive_sha256'],
        'manifest':source['manifest'],'training_allowed':False,'untouched_final':False})
    return p


def journal_state(root,plan):
    intents={p.stem:read_json(p) for p in (root/'call-intents').glob('*.json')}
    expected={digest([r['key'],0]):r for r in schedule(plan)};results={};missing=[]
    store=ShardStore(root/'calls')
    for key,i in intents.items():
        if key not in expected or i.get('work_id')!=key or i.get('record_id')!=expected[key]['key'] or i.get('slot')!=0 or i.get('max_tokens')!=expected[key]['cap']:
            raise ValueError('Unplanned or changed dispatch intent')
        path=store.path(key)
        if not path.exists() or not path.with_suffix('.sha256').exists():missing.append(key);continue
        value=store.read(key)
        if value['intent']!=i:raise ValueError('Intent mismatch')
        results[expected[key]['key']]=value
    for p in (root/'calls/shards').glob('*'):
        if p.stem not in intents or p.suffix not in ('.json','.sha256'):raise ValueError('Unjournaled result')
    if len(intents)>2400 or sum(i['max_tokens'] for i in intents.values())>476160:raise ValueError('Attempt budget exceeded')
    return intents,results,missing


def packet(result,task,slot):
    call=call_from_dict(result['call'])
    answer,explanation,status=parse_answer(result['raw'],tuple(o.answer_id for o in task.options),
        final=call.phase=='final',stop_reason=call.stop_reason)
    return PrivatePacket(task.task_id,slot,result['raw'],answer,explanation,status,call)


def private_row(rows,tid,f,replica):
    return next(r for r in rows if r['task_id']==tid and r['stage']=='private' and r['model']==f and r['replica']==replica)


def team_packets(plan,rows,results,tid,team,revised=False):
    task=task_from_dict(next(t for t in plan['source']['tasks'] if t['task_id']==tid));out=[];refs=[]
    for b in plan['team_bindings'][tid][team]:
        row=(next(r for r in rows if r['task_id']==tid and r['stage']=='revision' and r['team']==team and r['slot']==b['slot'])
             if revised else private_row(rows,tid,b['family'],b['replica']))
        refs.append(row['key']);out.append(packet(results[row['key']],task,b['slot']))
    return tuple(out),refs


def request_for(plan,row,rows,results):
    task=task_from_dict(next(t for t in plan['source']['tasks'] if t['task_id']==row['task_id']))
    stage=row['stage'];deps=[]
    if stage=='private':messages=private_prompt(task,'')
    elif stage=='revision':
        # Nine-packet per-task barrier, not merely the selected three.
        if any(r['key'] not in results for r in rows if r['task_id']==task.task_id and r['stage']=='private'):
            raise ValueError('Nine private packets must be frozen before revision')
        packets,deps=team_packets(plan,rows,results,task.task_id,row['team'])
        own=packets[row['slot']]
        peers=tuple(DeliveredMessage(p.agent,own.agent,p.raw,digest(p)) for p in packets if p.agent!=own.agent)
        messages=revision_prompt(task,own,peers,'')
    else:
        entries=[]
        if stage!='task_only':
            packets,deps=team_packets(plan,rows,results,task.task_id,row['team'],revised=stage=='debate')
            entries=[envelope(p.agent,p.raw) for p in packets]
        messages=readout_prompt(task,entries)
    request=Request(task,messages,'base' if row['cap']==64 else f"agent-{row['slot']}",
        'final' if row['cap']==64 else stage,row['seed'],row['cap'],row['cap']==64)
    return request,deps


class NativeJournal(JournalBackend):
    def __init__(self,backend,root,plan):
        intents,results,missing=journal_state(root,plan)
        if missing:raise ValueError('Unknown dispatch; no retry')
        self.backend,self.root,self.plan=backend,root,plan
        self.identity=backend.identity;self.budget={'generation_calls_upper_bound':2400,'generated_tokens_upper_bound':476160}
        self.intents=intents;self.results={digest([k,0]):v for k,v in results.items()}
        self.store=ShardStore(root/'calls');self.calls=[];self.seen=set();self.generation_tokens={}
        self.new_calls=0;self.stop_after=None;self.before_new=lambda:None
    def validate_request(self,r):
        if r.task.split!='validation' or r.max_tokens not in (64,256):raise ValueError('Stage/split changed')
    def _validate(self,request,intent,result):
        params=self.identity['parameters']['final' if request.deterministic else 'packet']
        if json.loads(result['call']['parameters_json'])!=params:raise ValueError('Native generation config changed')
        eos=params['eos_token_id'];ids=eos if isinstance(eos,list) else [eos]
        tokens=result['tokens']['completion_ids']
        # Existing provenance validator expects one EOS; validate native set first.
        if result['call']['stop_reason']=='eos' and (not tokens or tokens[-1] not in ids):raise ValueError('Invalid native EOT')
        original=self.backend
        self.backend=SimpleNamespace(tokenizer=SimpleNamespace(eos_token_id=tokens[-1] if tokens else ids[0]))
        try:return super()._validate(request,intent,result)
        finally:self.backend=original


def collect_stage(root,plan,stage,model,backend,*,smoke=False,stop_after=None):
    rows=schedule(plan);_,results,unknown=journal_state(root,plan)
    if unknown:raise ValueError('Unknown dispatch; no retry')
    selected=[r for r in rows if r['model']==model and (r['stage']==stage or stage=='readout' and r['cap']==64)
              and (not smoke or r['task_id'] in plan['smoke_ids'])]
    if not selected:raise ValueError('Model/stage mismatch')
    if stage=='revision' and not smoke and any(r['key'] not in results for r in rows if r['stage']=='private'):
        raise ValueError('Global private bank incomplete')
    immutable(root/'identities'/f'{model}.json',backend.identity)
    journal=NativeJournal(backend,root,plan);new=0
    for row in selected:
        if row['key'] in results:
            request,deps=request_for(plan,row,rows,results)
            journal.begin_record(row['key']);journal.generate(request);continue
        if stop_after is not None and new>=stop_after:break
        request,deps=request_for(plan,row,rows,results)
        journal.begin_record(row['key']);journal.generate(request)
        result=journal.results[digest([row['key'],0])];results[row['key']]=result
        immutable(root/'dependencies'/f"{row['key']}.json",{'request':row,'sources':deps,'identity_hash':digest(backend.identity)})
        new+=1
    return {'new_attempts':new,'committed':len(results),'cached_reuses':len(journal.calls)-new}


def reconstruct(root,plan):
    intents,results,unknown=journal_state(root,plan);rows=schedule(plan)
    identities={p.stem:read_json(p) for p in (root/'identities').glob('*.json')}
    for row in rows:
        if row['key'] not in results:continue
        request,deps=request_for(plan,row,rows,results)
        identity=identities[row['model']]
        if identity['spec']!=plan['models'][row['model']] or identity['adapters']!=[]:raise ValueError('Model/adapter identity mismatch')
        if not plan['fixture']:
            access=read_json(root/'access_preflight.json')['models'][row['model']]
            if any(identity.get(k)!=v for k,v in access.items()): raise ValueError('Loaded identity differs from preflight')
            body={k:v for k,v in identity.items() if k!='snapshot'}
            if digest(body)!=identity['snapshot']:raise ValueError('Native identity digest mismatch')
        validator=object.__new__(NativeJournal);validator.identity=identity;validator.backend=None
        result=results[row['key']]
        expected={'schema_version':1,'work_id':digest([row['key'],0]),'record_id':row['key'],
                  'slot':0,'request_hash':digest(request),'max_tokens':row['cap']}
        validator._validate(request,expected,result)
        dep=read_json(root/'dependencies'/f"{row['key']}.json")
        if dep!={'request':row,'sources':deps,'identity_hash':digest(identity)}:raise ValueError('Dependency mismatch')
    return intents,results,unknown,rows


def report(root):
    from .heterogeneity_metrics import build_report
    plan=load_plan(root);intents,results,unknown,rows=reconstruct(root,plan)
    out=build_report(plan,rows,results)
    out['accounting']={'attempted':len(intents),'committed':len(results),'unresolved':len(unknown),
        'reserved_output_tokens':sum(i['max_tokens'] for i in intents.values()),'budget':BUDGET,
        'optimizer_updates':0,'teacher_forced_forwards':0}
    out['recovery_safe']=read_json(root/'state.json')['recovery_safe']
    out['completed_tasks']=sum(all(r['key'] in results and results[r['key']]['call']['stop_reason']!='context_overflow' for r in rows if r['task_id']==t['task_id']) for t in plan['source']['tasks'])
    out['missing_tasks']=len(plan['source']['tasks'])-out['completed_tasks']
    out['complete']=len(results)==len(rows) and not unknown and out['recovery_safe'] and not out['context_overflows']
    out['model_identities']={p.stem:read_json(p) for p in (root/'identities').glob('*.json')}
    out['source_code']=plan['code']
    out['plan_hash']=digest(plan);out['scientific_status']='mock_only' if plan['fixture'] else 'development_diagnostic'
    out['resources']=[read_json(p) for p in sorted((root/'resources').glob('*.json'))]
    write_json(root/'summary.json',out)
    write_json(root/'incomplete_requests.json',{'unresolved_dispatches':unknown,
        'missing_requests':[r['key'] for r in rows if r['key'] not in results],
        'recovery_safe':out['recovery_safe']})
    for name,field in [('private_support','teams'),('paired_protocol_comparisons','comparisons'),('resource_usage','costs')]:write_json(root/f'{name}.json',out[field])
    write_json(root/'transition_tables.json',{t:v['overall']['transitions'] for t,v in out['teams'].items()})
    (root/'per_task_metrics.jsonl').write_text(''.join(canonical(r)+'\n' for r in out['per_task']))
    import csv
    with (root/'family_pairwise_rescue.csv').open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['team','rescuer','rescued','numerator','denominator'])
        for team,value in out['teams'].items():
            for pair in value['overall']['pairwise_rescue']:w.writerow([team,pair['rescuer'],pair['rescued'],pair['unconditional']['numerator'],pair['unconditional']['denominator']])
    lines=['# Heterogeneous complementarity review','',f"Status: {out['scientific_status']}; complete={out['complete']}; recovery_safe={out['recovery_safe']}",'',
           '| Team | Observed private tasks | Mean / best member | Coverage | Gain over best | Mixed | Vote | Synthesis | Debate | Erasure | Repair | Unique by member | Logical debate calls / output tokens |',
           '|---|---:|---|---|---|---|---|---|---|---|---|---|---|']
    fmt=lambda x:f"{x['numerator']}/{x['denominator']}" if x['denominator'] else 'undefined (0 support)'
    for t,v in out['teams'].items():
        a=v['overall'];lines.append('| '+ ' | '.join([t,str(a['observed_private_tasks']),fmt(a['mean_accuracy'])+' / '+fmt(a['best_accuracy']),fmt(a['coverage']),fmt(a['gain']),fmt(a['mixed']),*[fmt(a['terminal'][k]) for k in ('vote','synthesis','debate')],fmt(a['erasure']),fmt(a['repair']),', '.join(m+':'+fmt(v) for m,v in a['unique_coverage'].items()),str(out['costs']['logical_deployment'][t]['debate']['generation_calls'])+' / '+str(out['costs']['logical_deployment'][t]['debate']['output_tokens'])])+' |')
    lines+=['', 'Task-only common readout: '+fmt(out['task_only']), '',
        '80 development-exposed task groups, not independent calls. Partial observed metrics retain missingness; no support-based stop. ',
        'Coverage is oracle availability; construction may come from the readout. Equal logical calls/caps do not equal FLOPs or cross-tokenizer costs.',
        'No training, efficacy claim, or automatic follow-up. See summary.json for family/dataset breakdowns, uncertainty and costs.']
    (root/'report.md').write_text('\n'.join(lines)+'\n')
    return out


def private_bundle(root,path):
    return review_bundle(root,path,{'purpose':VARIANT},kind=VARIANT+'_private',
                         scientific_status='mock_only' if load_plan(root)['fixture'] else 'development_diagnostic',
                         include_markdown=True,include_csv=True,max_metadata_bytes=256*1024**2)


def checkpoint(root,persistent):
    """Existing bounded storage over one compact ZIP, not thousands of Drive files."""
    stamp=time.time_ns();local=root.parent/'bundles'/f'{RUN_ID}-checkpoint-{stamp}.zip'
    bundle=private_bundle(root,local)
    compact=root.parent/f'.{root.name}-compact';compact.mkdir(exist_ok=True)
    # Persist the ZIP as an ordinary artifact through existing snapshot verification.
    import shutil
    shutil.copyfile(local,compact/'state.zip')
    write_json(compact/'receipt.json',{'sha256':bundle['sha256'],'plan_hash':read_json(root/'state.json')['plan_hash'],
        'recovery_safe':read_json(root/'state.json')['recovery_safe']})
    return sync_run(compact,persistent,timeout_seconds=300)


def restore(persistent,root):
    snaps=sorted(p for p in (persistent/'snapshots').iterdir() if p.is_dir())
    if not snaps:raise ValueError('No study snapshots available')
    snapshot=snaps[-1]
    index=read_json(snapshot/'index.json')
    if (snapshot/'COMPLETE').read_text().strip()!=file_hash(snapshot/'index.json'):raise ValueError('Invalid latest snapshot')
    if index.get('schema_version')!=1 or set(index['files'])!={'state.zip','receipt.json'}:raise ValueError('Wrong snapshot kind')
    objects=persistent/'objects'
    import re
    for name,sha in index['files'].items():
        if not isinstance(sha,str) or not re.fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid snapshot object identity')
        obj=objects/sha
        if obj.is_symlink() or not obj.is_file() or obj.stat().st_size>256*1024**2 or file_hash(obj)!=sha:raise ValueError('Corrupt snapshot')
    receipt=read_json(objects/index['files']['receipt.json'])
    if receipt['sha256']!=index['files']['state.zip']:raise ValueError('Snapshot receipt hash mismatch')
    if not receipt['recovery_safe']:raise ValueError('Latest snapshot unsafe; no fallback or regeneration')
    if root.exists():raise ValueError('Restore requires absent destination')
    with tempfile.TemporaryDirectory(dir=root.parent) as tmp:
        zip_path=Path(tmp)/'state.zip'
        storage_operation('bundle-restore',objects/index['files']['state.zip'],zip_path,timeout_seconds=300,sha256=receipt['sha256'])
        unpack(zip_path,receipt['sha256'],root)
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe restored state')
    plan=load_plan(root)
    if digest(plan)!=receipt['plan_hash']:raise ValueError('Snapshot plan receipt mismatch')
    reconstruct(root,plan)


def unpack(path,sha,root):
    content=read_review(path,sha,max_members=20000,max_bytes=256*1024**2,allow_text=True)
    if content['HANDOFF.json']['kind']!=VARIANT+'_private':raise ValueError('Private study bundle required')
    with zipfile.ZipFile(path) as z:
        for name in content:
            if name=='HANDOFF.json':continue
            dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
            if '/shards/' in name:dest.with_suffix('.sha256').write_text(file_hash(dest))
    return content


def export(root,persistent=None):
    result=report(root);stamp=time.time_ns();bundles=root.parent/'bundles'
    (root/'CODEX_HANDOFF.md').write_text('Heterogeneous development diagnostic; no training or automatic follow-up.\n'
        'PRIVATE contains raw text, labels, prompts and token IDs; keep out of Git. SANITIZED cannot reconstruct prompts.\n'
        'Fresh official models; no old adapter checkpoints. State safety is independent of metric reconstruction.\n')
    inventory={p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file() and not p.name.startswith('.') and p.name not in ('raw_artifact_inventory.json','checksums.json')}
    write_json(root/'raw_artifact_inventory.json',inventory);write_json(root/'checksums.json',inventory)
    private=private_bundle(root,bundles/f'{RUN_ID}-PRIVATE-{stamp}.zip')
    with tempfile.TemporaryDirectory() as tmp:
        public=Path(tmp);write_json(public/'summary.json',result)
        write_json(public/'model_registry.json',load_plan(root)['models'])
        (public/'report.md').write_text((root/'report.md').read_text())
        sanitized=review_bundle(public,bundles/f'{RUN_ID}-SANITIZED-{stamp}.zip',{},kind=VARIANT+'_sanitized',scientific_status=result['scientific_status'],include_markdown=True)
    for b in (private,sanitized):
        print(canonical(b),flush=True)
        if persistent: persist_bundle(Path(b['path']),persistent/'bundles'/Path(b['path']).name,b['sha256'],timeout_seconds=300)
    return {'private':private,'sanitized':sanitized}


def preflight(root,cache):
    from ..backends.native import metadata
    import shutil
    plan=load_plan(root)
    if plan['fixture']:raise ValueError('Fixture cannot download official models')
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1 or not torch.cuda.is_bf16_supported():raise RuntimeError('One BF16 CUDA GPU required')
    cache.mkdir(parents=True,exist_ok=True)
    if shutil.disk_usage(cache).free<8*1024**3:raise RuntimeError('Preflight requires 8 GiB free cache reserve')
    ram=os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')
    if ram<12*1024**3:raise RuntimeError('Preflight requires at least 12 GiB host RAM')
    resolved={k:metadata(k,cache,token=os.environ.get('HF_TOKEN')) for k in 'QLMR'}
    from huggingface_hub import try_to_load_from_cache
    missing_bytes=0
    for receipt in resolved.values():
        for name, info in receipt['weight_metadata'].items():
            cached=try_to_load_from_cache(receipt['spec']['repository'],name,
                revision=receipt['spec']['revision'],cache_dir=str(cache))
            if not isinstance(cached,str) or not Path(cached).is_file():missing_bytes+=info['bytes']
    if shutil.disk_usage(cache).free < missing_bytes+8*1024**3:
        raise RuntimeError('Insufficient disk for missing official weights plus 8 GiB reserve')
    access={'models':resolved,'runtime':runtime_fingerprint(),'all_authorized':True}
    immutable(root/'access_preflight.json',access)
    immutable(root/'environment.json',{'versions':versions(),'runtime':runtime_fingerprint(),
        'gpu':torch.cuda.get_device_name(0),'vram_bytes':torch.cuda.get_device_properties(0).total_memory,
        'host_ram_bytes':ram})
    return access


def execute(root,persistent,stage,model,cache,*,smoke=False,stop_after=None):
    from ..backends.native import NativeBackend
    plan=load_plan(root)
    if plan['fixture']:raise ValueError('No official inference for fixtures')
    if plan['code']!=code_identity(Path(__file__).resolve().parents[3]):raise ValueError('Pinned source changed')
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe run; no automatic resume')
    access=read_json(root/'access_preflight.json')
    if not access['all_authorized'] or set(access['models'])!=set('QLMR') or access['runtime']!=runtime_fingerprint():raise ValueError('All-model access/runtime preflight required')
    _, existing, unknown, _ = reconstruct(root,plan)
    if unknown: raise ValueError('Unknown dispatch; no retry')
    planned = schedule(plan)
    selected = [r for r in planned if r['model']==model and
        (r['stage']==stage or stage=='readout' and r['cap']==64) and
        (not smoke or r['task_id'] in plan['smoke_ids'])]
    if not selected: raise ValueError('Model/stage mismatch')
    if all(r['key'] in existing for r in selected): return {'new_attempts':0,'status':'already_complete'}
    if stage=='revision' and not smoke and any(r['key'] not in existing for r in planned if r['stage']=='private'):
        raise ValueError('Global private bank incomplete')
    # Prove all dependencies available before loading or marking a new dispatch window.
    for row in selected: request_for(plan,row,planned,existing)
    state=read_json(root/'state.json');state['recovery_safe']=False;write_json(root/'state.json',state)
    checkpoint(root,persistent) # verified BEFORE any possible dispatch
    started=time.monotonic();backend=None;usage={};completed=False
    try:
        print('Loading',model,'for',stage,flush=True)
        backend=NativeBackend(model,access['models'][model],cache,token=os.environ.get('HF_TOKEN'))
        result=collect_stage(root,plan,stage,model,backend,smoke=smoke,stop_after=stop_after)
        usage={**backend.resource_usage(),'cache_hits':result['cached_reuses']};completed=True
    finally:
        if backend is not None:backend.close()
        write_json(root/'resources'/f'{time.time_ns()}.json',{'model':model,'stage':stage,
            'load_started':True,'released':backend is not None,'completed':completed,
            'wall_seconds':time.monotonic()-started,**usage})
        print('Released',model,flush=True)
    state['recovery_safe']=True;write_json(root/'state.json',state)
    try:checkpoint(root,persistent)
    except BaseException:
        state['recovery_safe']=False;write_json(root/'state.json',state);raise
    return result


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['plan','preflight','private','revisions','readout','smoke','report','export','restore','audit'])
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--persistent',type=Path)
    p.add_argument('--pilot-bundle',type=Path);p.add_argument('--cache-dir',type=Path)
    p.add_argument('--model',choices=list('QLM'));p.add_argument('--execute',action='store_true')
    p.add_argument('--plan-hash');p.add_argument('--stop-after',type=int)
    p.add_argument('--bundle',type=Path);p.add_argument('--sha256')
    a=p.parse_args(argv);root=a.run_dir
    if a.stage=='audit':
        if root.exists():p.error('Audit requires absent output directory')
        original=unpack(a.bundle,a.sha256,root);out=report(root)
        if 'summary.json' in original and original['summary.json']!=out:raise ValueError('Report mismatch')
        print(canonical({'audit':'passed','complete':out['complete']}));return
    if root.name!=RUN_ID:p.error('Use the fixed new study ID')
    root.parent.mkdir(parents=True,exist_ok=True)
    if a.stage=='restore':restore(a.persistent,root);return
    with run_lock(root):
        if a.stage=='plan':
            if not a.pilot_bundle:p.error('--pilot-bundle required')
            plan=initialize(root,pilot_source(a.pilot_bundle),code_identity(Path(__file__).resolve().parents[3]))
            if a.persistent:checkpoint(root,a.persistent)
            print(canonical({'plan_hash':digest(plan),'budget':BUDGET,'status':'planned_gpu_unverified'}));return
        plan=load_plan(root)
        if a.stage=='report':out=report(root);print(canonical({'complete':out['complete'],'accounting':out['accounting']}));return
        if a.stage=='export':print(canonical(export(root,a.persistent)));return
        if a.plan_hash!=digest(plan):p.error('--plan-hash must match the frozen plan')
        if a.stage=='preflight':
            if not a.execute or not a.cache_dir:p.error('Explicit --execute --cache-dir required for metadata/access preflight')
            preflight(root,a.cache_dir)
            if a.persistent:checkpoint(root,a.persistent)
            print('All model access checks passed; no benchmark calls.');return
        if not a.execute or not a.cache_dir or not a.persistent:p.error('Inference requires --execute --cache-dir --persistent')
        if a.stop_after is not None and a.stop_after<1:p.error('Positive stop-after required')
        if a.stage=='smoke':
            if a.stop_after:p.error('Smoke uses the exact two-task plan without stop-after')
            phases=[(s,k) for s in ('private','revision') for k in 'QLM']+[('readout','R')]
            for stage,model in phases:execute(root,a.persistent,stage,model,a.cache_dir,smoke=True)
        else:
            stage='revision' if a.stage=='revisions' else a.stage
            model='R' if stage=='readout' else a.model
            if not model:p.error('--model required')
            print(canonical(execute(root,a.persistent,stage,model,a.cache_dir,stop_after=a.stop_after)))

def cli(argv=None):
    try:main(argv)
    except Exception as exc:
        # No credential-bearing Hub/backend traceback in notebook output.
        import sys
        safe = {'Pinned source changed','Unsafe run; no automatic resume','Unknown dispatch; no retry',
                'Global private bank incomplete','Model/stage mismatch','Latest snapshot unsafe; no fallback or regeneration',
                'Preflight requires 8 GiB free cache reserve','Insufficient disk for missing official weights plus 8 GiB reserve','Preflight requires at least 12 GiB host RAM',
                'One BF16 CUDA GPU required','All-model access/runtime preflight required'}
        message = str(exc) if str(exc) in safe or str(exc).startswith('Official model access/template preflight failed for ') else type(exc).__name__
        print('Heterogeneity stopped: '+message+'. Preserve scratch; inspect state and incomplete requests. No automatic retry.',file=sys.stderr)
        raise SystemExit(1) from None


if __name__=='__main__':cli()
