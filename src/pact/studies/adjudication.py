"""Bounded frozen-bank adjudication CLI. No training, proposer calls or automatic next stage."""
import argparse
from collections import Counter
from dataclasses import asdict, replace
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from types import SimpleNamespace
import zipfile

from ..artifacts import ShardStore, run_lock, sync_run
from ..backends import Request
from ..environment import code_identity, runtime_fingerprint
from ..schemas import CallRecord
from ..storage import storage_operation, persist_bundle
from ..training.receiver import JournalBackend
from ..training.colab import review_bundle
from ..training.feasibility import read_review
from ..util import canonical, digest, node_seed, file_hash, read_json, write_json
from .breadth import BreadthJournal
from .heterogeneity import immutable
from .gpqa_data import outside_git
from .adjudication_contracts import *
from .adjudication_data import import_all, eligibility, write_lines, PARENTS

REPO = Path(__file__).resolve().parents[3]


def freeze(root):
    if (root/'adjudication_plan.json').exists():raise ValueError('Never re-plan this ID')
    bank=read_json(root/'bank.json');records=bank['records'];eligible=eligibility(records)
    if not bank['fixture']:
        outside_git(root)
        if root.name!=RUN_ID:raise ValueError('Fixed study ID required')
        if Counter(r['dataset'] for r in records)!=Counter({'mmlu-pro':140,'musr':90}):raise ValueError('Exact cohort required')
        if Counter(r['dataset'] for r in eligible)!=Counter({'mmlu-pro':42,'musr':38}):raise ValueError('Eligibility changed')
    for r in records:
        for team in ('QLM','QQQ'):from_record(r,team)
        if r['training_allowed'] or r['untouched_final']:raise ValueError('Exposure boundary changed')
    if len({r['task']['task_id'] for r in records})!=len(records):raise ValueError('Duplicate task')
    bydataset={n:budgets(sum(r['dataset']==n for r in records),sum(r['dataset']==n for r in eligible)) for n in ('mmlu-pro','musr')}
    plan={'variant':VARIANT,'attack_variant':ATTACK,'run_id':RUN_ID,'fixture':bank['fixture'],
          'bank_hash':digest(bank),'models':{k:asdict(v) for k,v in MODELS.items()},'contracts':contracts(),
          'budgets':budgets(len(records),len(eligible)),'dataset_budgets':bydataset,'eligible':eligible,
          'smoke_ids':[r['task']['task_id'] for r in records if r['dataset']=='mmlu-pro'][:2],
          'source':code_identity(REPO),'seed':SEED,'model_order':['J8','J14'],'training_allowed':False,
          'untouched_final':False,'literature_reproduction':False,'historical_readout_cap':64}
    write_json(root/'adjudication_plan.json',plan)
    write_json(root/'model_registry.json',plan['models']);write_json(root/'prompt_contracts.json',contracts())
    write_json(root/'perturbation_plan.json',{'eligible':eligible,'styles':STYLES,'attempts_per_style':1,'victims':VICTIMS,'budget':plan['budgets']['acquire']})
    write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
    write_lines(root/'clean_requests.jsonl',[{**r,'request':asdict(req)} for r,req,_ in requests(root,plan,'clean')])
    return plan


def load(root):
    p=read_json(root/'adjudication_plan.json');b=read_json(root/'bank.json')
    if not p['fixture']:outside_git(root)
    if digest(p)!=read_json(root/'state.json')['plan_hash'] or digest(b)!=p['bank_hash']:raise ValueError('Frozen plan/bank changed')
    if p['models']!={k:asdict(v) for k,v in MODELS.items()} or p['contracts']!=contracts() or p['eligible']!=eligibility(b['records']):raise ValueError('Design changed')
    if p['budgets']!=budgets(len(b['records']),len(p['eligible'])):raise ValueError('Budget changed')
    return p


def pool(root, plan):
    path=root/'pool.json'
    if not path.exists():return None
    p=read_json(path)
    if p['plan_hash']!=digest(plan) or digest(p['attempts'])!=p['pool_hash']:raise ValueError('Pool changed')
    expected=[];store=ShardStore(root/'calls')
    for row,_,_ in requests(root,plan,'acquire'):
        key=digest([row['key'],0]);result=store.read(key) if store.path(key).exists() else None
        if result is None:
            skipped=read_json(root/'nonexecuted'/f"{row['key']}.json")
            text,reason=None,skipped['status']
        else:text,reason=parse_rewrite(result['raw'],result['call']['stop_reason'])
        expected.append({**row,'accepted':text is not None,'justification':text,'validation':reason,
                         'raw':result['raw'] if result else None,'result_hash':digest(result) if result else None})
    if p['attempts']!=expected:raise ValueError('Pool differs from immutable one-attempt acquisition')
    return p


def requests(root, plan, stage):
    records=read_json(root/'bank.json')['records'];eligible={r['task_id']:r for r in plan['eligible']}
    saved=pool(root,plan) if stage=='attack' else None
    if stage=='attack' and saved is None:return []
    accepted={} if saved is None else {(r['task_id'],r['style']):r for r in saved['attempts'] if r['accepted']}
    out=[]
    for model in (('Q',) if stage=='acquire' else ('J8','J14')):
        for rec in records:
            tid=rec['task']['task_id'];e=eligible.get(tid)
            if stage!='clean' and e is None:continue
            for mode in (('rewrite',) if stage=='acquire' else MODES if stage=='clean' else VICTIMS):
                bank=from_record(rec,'QQQ' if mode=='qqq_full_select' else 'QLM')
                for style in (('clean',) if stage=='clean' else STYLES):
                    view=bank
                    if stage=='attack':
                        a=accepted.get((tid,style))
                        if a is None:continue
                        view=perturb(bank,RationalePerturbation(tid,e['target'],style,a['justification'],a['key']))
                        invariance(bank,view,e['target'],EvalSpec(rec['eval']['answer']))
                    messages=rewrite_prompt(bank,e['target'],style) if stage=='acquire' else prompt(AdjudicationInput(view,mode))
                    seed=node_seed(SEED,RUN_ID,tid,rec['group_id'],'generator',e['target'],style) if stage=='acquire' else node_seed(SEED,RUN_ID,tid,rec['group_id'],model,mode)
                    req=Request(bank.task,messages,'base','final',seed,CAP,True)
                    row={'task_id':tid,'dataset':rec['dataset'],'group_id':rec['group_id'],'stratum':rec['stratum'],
                         'model':model,'mode':mode,'style':style,'stage':stage,'seed':seed,'max_tokens':CAP,
                         'request_hash':digest(req),'bank_hash':digest(bank),
                         'perturbation_hash':digest(accepted[(tid,style)]) if stage=='attack' else None}
                    row['key']=digest([digest(plan),row]);out.append((row,req,view))
    return out


def all_requests(root,plan):
    return [x for stage in ('clean','acquire','attack') for x in requests(root,plan,stage)]


def journal(root,plan):
    planned={digest([r['key'],0]):(r,req,view) for r,req,view in all_requests(root,plan)}
    intents={p.stem:read_json(p) for p in (root/'call-intents').glob('*.json')};store=ShardStore(root/'calls')
    results={};unknown=[];counts=Counter()
    for key,intent in intents.items():
        if key not in planned:raise ValueError('Unplanned call')
        row,req,_=planned[key]
        expected={'schema_version':1,'work_id':key,'record_id':row['key'],'slot':0,'request_hash':digest(req),'max_tokens':CAP}
        if intent!=expected:raise ValueError('Attempt identity changed')
        counts[row['dataset'],row['stage']]+=1
        if not store.path(key).exists() or not store.path(key).with_suffix('.sha256').exists():unknown.append(key);continue
        value=store.read(key)
        identity=read_json(root/'identities'/f"{row['model']}.json")
        validate_identity(identity,row['model'],plan)
        if not plan['fixture']:
            access=read_json(root/'access'/f"{row['model']}.json")
            if any(identity.get(k)!=v for k,v in access.items()):raise ValueError('Access/runtime/weight receipt differs')
        validator=object.__new__(AdjudicationJournal);validator.identity=identity;validator.plan={'profile':{'context':CONTEXT}}
        validator._validate(req,intent,value)
        results[row['key']]=value
    for p in (root/'calls/shards').glob('*'):
        if p.stem not in intents or p.suffix not in ('.json','.sha256'):raise ValueError('Orphan call result')
    for (dataset,stage),n in counts.items():
        if n>plan['dataset_budgets'][dataset][stage]['calls']:raise ValueError('Dataset/stage budget exceeded')
    if len(intents)>plan['budgets']['total']['calls'] or len(intents)*CAP>plan['budgets']['total']['tokens']:raise ValueError('Total budget exceeded')
    skips={p.stem:read_json(p) for p in (root/'nonexecuted').glob('*.json')}
    expectedrows={r['key']:(r,req,view) for r,req,view in planned.values()}
    for key,s in skips.items():
        if key not in expectedrows or key in results or digest([key,0]) in intents:raise ValueError('Invalid nonexecuted record')
        row,req,view=expectedrows[key]
        if s['request_hash']!=digest(req):raise ValueError('Nonexecuted request changed')
        if s['status']=='empty_selectable':
            if not selector(row['mode']) or any(c.status=='ok' for c in view.candidates):raise ValueError('Invented empty selector')
        elif s['status']=='context_incompatible':
            if s['input_tokens']+CAP<=CONTEXT:raise ValueError('Invented overflow')
        else:raise ValueError('Unknown nonexecuted status')
    return intents,results,unknown,skips


def validate_identity(identity,key,plan):
    if identity['spec']!=plan['models'][key] or identity.get('adapters')!=[] or identity['snapshot']!=digest({k:v for k,v in identity.items() if k!='snapshot'}):raise ValueError('Model identity/isolation changed')
    if identity.get('precision')!='bfloat16' or identity.get('attention')!='sdpa':raise ValueError('Precision changed')
    if not plan['fixture']:
        if identity.get('adapter_state')!='absent' or set(identity.get('file_hashes',{}))!=set(identity['metadata_hashes'])|set(identity['weight_files']):raise ValueError('Actual weight identity missing')
        if any(identity['file_hashes'][n]!=v['etag'] for n,v in identity['weight_metadata'].items() if len(v['etag'])==64):raise ValueError('Weight hash changed')


class AdjudicationJournal(JournalBackend):
    def __init__(self,backend,root,plan,before_new):
        self.backend,self.root,self.identity=backend,root,backend.identity
        self.plan={'profile':{'context':CONTEXT}}
        self.allowed={r['key']:(r,req) for r,req,_ in all_requests(root,plan)}
        self.intents,results,unknown,_=journal(root,plan)
        if unknown:raise ValueError('Unknown dispatch; no retry')
        self.results={digest([k,0]):v for k,v in results.items()};self.store=ShardStore(root/'calls')
        self.budget={'generation_calls_upper_bound':plan['budgets']['total']['calls'],'generated_tokens_upper_bound':plan['budgets']['total']['tokens']}
        self.calls=[];self.seen=set();self.generation_tokens={};self.new_calls=0;self.stop_after=None;self.before_new=before_new
    def validate_request(self,r):
        if r.task.split!='characterization_dev' or r.max_tokens!=CAP or not r.deterministic or r.actor!='base' or r.phase!='final':raise ValueError('Outside inference-only profile')
        if hasattr(self,'allowed'):
            if self.record_key not in self.allowed:raise ValueError('Unplanned dispatch')
            row,expected=self.allowed[self.record_key]
            if r!=expected or row['model']!=self.identity['spec']['key']:raise ValueError('Stage/request/model mismatch')
    _validate=BreadthJournal._validate


class MockJudge:
    def __init__(self,key):
        from ..backends.registry import generation_parameters
        tok=SimpleNamespace(eos_token_id=2,pad_token_id=2,bos_token_id=1)
        params=generation_parameters(tok,{'eos_token_id':2},final=True)
        body={'spec':asdict(MODELS[key]),'adapters':[],'precision':'bfloat16','attention':'sdpa','template_hash':digest('fictional-native'),
              'parameters':{'final':params},'fixture':True}
        self.identity={**body,'snapshot':digest(body)};self.calls=[]
    def render_messages(self,messages):return canonical(messages)
    def count_tokens(self,text):return len(text.split())
    def generate(self,req):
        body=json.loads(req.messages[1].content)
        if 'assigned_candidate' in body:obj={'justification':'Fictional rewritten rationale supporting '+body['assigned_candidate']['answer']}
        elif '"candidate_id"' in req.messages[0].content:
            choices=[c for c in body['candidates'] if c['status']=='selectable']
            obj={'decision_basis':'Fictional comparison.','candidate_id':choices[0]['candidate_id'] if choices else 'ABSTAIN'}
        else:obj={'decision_basis':'Fictional independent answer.','answer':body['trusted_task']['options'][0]['id']}
        raw=json.dumps(obj);rendered=self.render_messages(req.messages);n=self.count_tokens(rendered)
        params={**self.identity['parameters']['final'],'max_new_tokens':CAP}
        call=CallRecord('base','final',self.identity['snapshot'],req.seed,req.messages,rendered,digest(rendered),self.identity['template_hash'],canonical(params),n,2,'eos',.01)
        self.last_generation={'prompt_ids':[1]*n,'completion_ids':[1,2],'raw':raw,'context_hash':digest(rendered)}
        self.calls.append(call);return raw,call
    def resource_usage(self):return {'mock_only':True,'compute_units':None}
    def close(self):pass


def preflight(root,cache,keys):
    from ..backends.native import metadata
    from ..backends.registry import render_native
    from huggingface_hub import snapshot_download
    from transformers import AutoTokenizer
    plan=load(root)
    if plan['fixture']:raise ValueError('Real preflight not for fixtures')
    output={}
    for key in keys:
        try:
            receipt=metadata(key,cache,token=os.environ.get('HF_TOKEN'),spec=MODELS[key])
        except RuntimeError:
            write_json(root/'availability'/f'{key}.json',{'status':'model_access_unavailable','model':key});raise
        immutable(root/'access'/f'{key}.json',receipt)
        path=snapshot_download(MODELS[key].repository,revision=MODELS[key].revision,allow_patterns=list(receipt['metadata_hashes']),cache_dir=str(cache),local_files_only=True)
        tokenizer=AutoTokenizer.from_pretrained(path,trust_remote_code=False,local_files_only=True)
        checks=[]
        for row,req,_ in all_requests(root,plan):
            if row['model']!=key:continue
            n=len(tokenizer(render_native(tokenizer,req.messages,MODELS[key]),add_special_tokens=False)['input_ids'])
            checks.append({'key':row['key'],'input_tokens':n,'compatible':n+CAP<=CONTEXT})
        immutable(root/'preflight'/f'{key}-{digest(checks)}.json',{'model':key,'receipt_hash':digest(receipt),'requests':checks})
        write_json(root/'availability'/f'{key}.json',{'status':'access_verified','model':key})
        output[key]={'intended':len(checks),'compatible':sum(r['compatible'] for r in checks),'incompatible':sum(not r['compatible'] for r in checks)}
    return output


def freeze_pool(root,plan):
    _,results,unknown,skips=journal(root,plan)
    if unknown:raise ValueError('Unresolved rewrite')
    rows=requests(root,plan,'acquire')
    if any(r['key'] not in results and r['key'] not in skips for r,_,_ in rows):return None
    attempts=[]
    for r,_,_ in rows:
        value=results.get(r['key']);text,reason=parse_rewrite(value['raw'],value['call']['stop_reason']) if value else (None,skips[r['key']]['status'])
        attempts.append({**r,'accepted':text is not None,'justification':text,'validation':reason,
                         'raw':value['raw'] if value else None,'result_hash':digest(value) if value else None})
    frozen={'plan_hash':digest(plan),'pool_hash':digest(attempts),'attempts':attempts}
    immutable(root/'pool.json',frozen)
    write_lines(root/'perturbation_attempts.jsonl',attempts)
    write_lines(root/'accepted_perturbations.private.jsonl',[r for r in attempts if r['accepted']])
    return frozen


def execute(root,persistent,stage,dataset,model,cache,*,mock=False,smoke=False,stop_after=None):
    plan=load(root)
    if plan['fixture']!=mock:raise ValueError('Fixture/real mismatch')
    if code_identity(REPO)!=plan['source']:raise ValueError('Pinned source changed')
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe dispatch window; no automatic retry')
    _,results,unknown,skips=journal(root,plan)
    if unknown:raise ValueError('Unknown dispatch')
    if stage=='attack' and pool(root,plan) is None:raise ValueError('Entire shared two-dataset pool must freeze before any victim')
    if stage=='acquire' and model!='Q' or stage!='acquire' and model not in ('J8','J14'):raise ValueError('Stage/model mismatch')
    selected=[x for x in requests(root,plan,stage) if x[0]['dataset']==dataset and x[0]['model']==model and (not smoke or x[0]['task_id'] in plan['smoke_ids'])]
    if smoke and (stage!='clean' or dataset!='mmlu-pro'):raise ValueError('Smoke is included MMLU prefix only')
    if stage=='attack':
        # Corresponding clean references must be terminal; never filter on their outcomes.
        clean=[r for r,_,_ in requests(root,plan,'clean') if r['dataset']==dataset and r['model']==model]
        if any(r['key'] not in results and r['key'] not in skips for r in clean):raise ValueError('Matched clean stage incomplete')
    pending=[x for x in selected if x[0]['key'] not in results and x[0]['key'] not in skips]
    if not pending:
        if stage=='acquire':freeze_pool(root,plan)
        return {'already_terminal':True,'intended':len(selected)}
    if not mock and (persistent is None or cache is None):raise ValueError('Real stages require scratch cache and durable root')
    receipt=None
    if not mock:
        receipt=read_json(root/'access'/f'{model}.json')
        if receipt['runtime_fingerprint']!=runtime_fingerprint():raise ValueError('Runtime differs from preflight; explicit compatible runtime required')
    backend=None;started=time.monotonic();n=0;dispatch_open=False
    try:
        if mock:backend=MockJudge(model)
        else:
            from ..backends.native import NativeBackend
            class JudgeBackend(NativeBackend):
                def generation_parameters(self,request):return {**super().generation_parameters(request),'max_new_tokens':CAP}
            print('Loading',model,'for',stage,dataset,flush=True)
            backend=JudgeBackend(model,receipt,cache,token=os.environ.get('HF_TOKEN'),spec=MODELS[model])
            backend.config.limits=replace(backend.config.limits,context=CONTEXT)
        validate_identity(backend.identity,model,plan);immutable(root/'identities'/f'{model}.json',backend.identity)
        # Entire available stage is tokenized before first dispatch; never truncate.
        checks=[]
        for row,req,view in pending:
            nt=backend.count_tokens(backend.render_messages(req.messages))
            status='empty_selectable' if stage!='acquire' and selector(row['mode']) and not any(c.status=='ok' for c in view.candidates) else 'context_incompatible' if nt+CAP>CONTEXT else 'compatible'
            checks.append({'key':row['key'],'request_hash':digest(req),'input_tokens':nt,'status':status})
            if status!='compatible':immutable(root/'nonexecuted'/f"{row['key']}.json",checks[-1])
        immutable(root/'preflight'/f'{stage}-{dataset}-{model}-{digest(checks)}.json',{'checks':checks,'identity_hash':digest(backend.identity)})
        compatible={c['key'] for c in checks if c['status']=='compatible'}
        def before():
            nonlocal dispatch_open
            if not dispatch_open:
                write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':False})
                checkpoint(root,persistent);dispatch_open=True
        wrapper=AdjudicationJournal(backend,root,plan,before)
        for row,req,view in pending:
            if row['key'] not in compatible:continue
            if stop_after is not None and n>=stop_after:break
            wrapper.begin_record(row['key']);wrapper.generate(req);n+=1
            if n%20==0:checkpoint(root,persistent)  # remains unsafe until the explicit boundary
        write_json(root/'resources'/f'{time.time_ns()}.json',{'stage':stage,'dataset':dataset,'model':model,'new_calls':n,'wall_seconds':time.monotonic()-started,**backend.resource_usage()})
    except BaseException as exc:
        write_json(root/'errors'/f'{time.time_ns()}.json',{'stage':stage,'dataset':dataset,'model':model,
                   'type':type(exc).__name__,'new_committed_calls':n,'dispatch_window_open':dispatch_open})
        if backend is not None and getattr(backend,'pending_call',None) is not None:
            write_json(root/'incomplete_request.private.json',backend.pending_call)
        raise
    finally:
        if backend is not None:backend.close()
    write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
    if stage=='acquire':freeze_pool(root,plan)
    try:checkpoint(root,persistent)
    except BaseException:
        write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':False});raise
    return {'new_calls':n,'intended':len(selected),'stage':stage,'dataset':dataset,'model':model}


def checkpoint(root,persistent):
    if persistent is None:return
    plan=load(root);stamp=time.time_ns()
    bundle=review_bundle(root,root.parent/'bundles'/f'{RUN_ID}-checkpoint-{stamp}.zip',{},kind=VARIANT+'_private',scientific_status='development_diagnostic',include_markdown=True,max_metadata_bytes=512*1024**2)
    with tempfile.TemporaryDirectory(dir=root.parent) as temp:
        compact=Path(temp);shutil.copyfile(bundle['path'],compact/'state.zip')
        write_json(compact/'receipt.json',{'sha256':bundle['sha256'],'plan_hash':digest(plan),'recovery_safe':read_json(root/'state.json')['recovery_safe']})
        sync_run(compact,persistent,timeout_seconds=300)


def unpack(bundle,sha,root):
    if root.exists():raise ValueError('Restore destination must be absent')
    content=read_review(bundle,sha,max_members=60000,max_bytes=512*1024**2,allow_text=True)
    if content['HANDOFF.json']['kind']!=VARIANT+'_private':raise ValueError('Private full bundle required')
    if not content['bank.json']['fixture']:outside_git(root)
    with zipfile.ZipFile(bundle) as archive:
        for name in content:
            if name=='HANDOFF.json':continue
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.read(name))
            if '/shards/' in name:p.with_suffix('.sha256').write_text(file_hash(p))
    plan=load(root);journal(root,plan)


def restore(persistent,root):
    snaps=sorted((persistent/'snapshots').glob('*'))
    if not snaps:raise ValueError('No durable snapshot')
    snap=snaps[-1];index=read_json(snap/'index.json')
    if (snap/'COMPLETE').read_text().strip()!=file_hash(snap/'index.json') or set(index['files'])!={'receipt.json','state.zip'}:raise ValueError('Latest snapshot invalid; no fallback')
    def obj(name):
        sha=index['files'][name]
        if not __import__('re').fullmatch('[0-9a-f]{64}',sha):raise ValueError('Invalid object hash')
        p=persistent/'objects'/sha
        if p.is_symlink() or file_hash(p)!=sha:raise ValueError('Snapshot corrupt')
        return p
    receipt=read_json(obj('receipt.json'))
    if not receipt['recovery_safe'] or receipt['sha256']!=index['files']['state.zip']:raise ValueError('Unsafe latest snapshot; preserve forensics, no fallback')
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent) as temp:
        local=Path(temp)/'state.zip';storage_operation('bundle-restore',obj('state.zip'),local,sha256=receipt['sha256'],timeout_seconds=600)
        unpack(local,receipt['sha256'],root)
    if digest(load(root))!=receipt['plan_hash'] or not read_json(root/'state.json')['recovery_safe']:raise ValueError('Restored state mismatch')


def export(root,persistent):
    from .adjudication_metrics import report
    summary=report(root);stamp=time.time_ns();dest=root.parent/'bundles'
    write_json(root/'checksums.json',{p.relative_to(root).as_posix():file_hash(p) for p in sorted(root.rglob('*')) if p.is_file() and p.name not in ('.lock','checksums.json')})
    private=review_bundle(root,dest/f'{RUN_ID}-PRIVATE-{stamp}.zip',{},kind=VARIANT+'_private',scientific_status=summary['scientific_status'],include_markdown=True,max_metadata_bytes=512*1024**2)
    # Explicit allowlist of aggregate-only artifacts, never arbitrary logs/manifests.
    with tempfile.TemporaryDirectory(dir=root.parent) as temp:
        public=Path(temp)
        for name in ('summary.json','REPORT.md','CODEX_HANDOFF.md','joint_failure_map.json','clean_comparisons.json','q_prefix_robustness.json','rationale_tradeoff_report.json','resource_usage.json','missingness.json','model_registry.json','prompt_contracts.json'):
            shutil.copyfile(root/name,public/name)
        sanitized=review_bundle(public,dest/f'{RUN_ID}-SANITIZED-{stamp}.zip',{},kind=VARIANT+'_sanitized',scientific_status=summary['scientific_status'],include_markdown=True,max_metadata_bytes=512*1024**2)
    for b in (private,sanitized):
        print(canonical(b),flush=True)
        if persistent:persist_bundle(Path(b['path']),persistent/'bundles'/Path(b['path']).name,b['sha256'],timeout_seconds=300)
    return {'private':private,'sanitized':sanitized}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['import','analyze','plan','preflight','smoke','clean','acquire-perturbations','evaluate-perturbations','report','export','restore','audit'])
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--persistent',type=Path);p.add_argument('--cache-dir',type=Path)
    p.add_argument('--mmlu-bundle',type=Path);p.add_argument('--musr-bundle',type=Path);p.add_argument('--math-bundle',type=Path)
    p.add_argument('--dataset',choices=['mmlu-pro','musr']);p.add_argument('--judge',choices=['J8','J14']);p.add_argument('--model',choices=['J8','J14','Q'])
    p.add_argument('--plan-hash');p.add_argument('--execute',action='store_true');p.add_argument('--mock',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--stop-after',type=int)
    p.add_argument('--bundle',type=Path);p.add_argument('--sha256')
    a=p.parse_args(argv);root=a.run_dir
    if not a.mock:outside_git(root)
    if a.stage=='restore':restore(a.persistent,root);return
    if a.stage=='audit':unpack(a.bundle,a.sha256,root);print(canonical({'audit':'integrity_reconstructed','recovery_safe':read_json(root/'state.json')['recovery_safe']}));return
    with run_lock(root):
        if a.stage=='import':
            b=import_all(root,{'mmlu-pro':a.mmlu_bundle,'musr':a.musr_bundle,'math-500':a.math_bundle},a.mock)
            print(canonical({'imported_tasks':len(b['records']),'eligible':len(eligibility(b['records']))}));return
        if a.stage=='analyze':
            b=read_json(root/'bank.json');print(canonical(b['offline']));return
        if a.stage=='plan':
            plan=freeze(root);checkpoint(root,a.persistent);print(canonical({'plan_hash':digest(plan),'budgets':plan['budgets']}));return
        plan=load(root)
        if plan['fixture']!=a.mock:p.error('Fixture flag must match the frozen plan')
        if a.stage in ('report','export'):
            from .adjudication_metrics import report
            out=report(root) if a.stage=='report' else export(root,a.persistent)
            print(canonical(out));return
        if a.plan_hash!=digest(plan):p.error('Exact --plan-hash required')
        if not a.execute:p.error('Explicit --execute required')
        if a.stage=='preflight':
            if not a.cache_dir:p.error('--cache-dir required')
            print(canonical(preflight(root,a.cache_dir,[a.model] if a.model else ['J8','J14','Q'])));checkpoint(root,a.persistent);return
        stage={'smoke':'clean','clean':'clean','acquire-perturbations':'acquire','evaluate-perturbations':'attack'}[a.stage]
        if not a.dataset or (stage!='acquire' and not a.judge):p.error('--dataset and judge (except acquisition) required')
        if a.stop_after is not None and a.stop_after<1:p.error('Positive stop-after required')
        if a.stage=='smoke' and a.stop_after:p.error('Smoke is the exact included prefix')
        if any((root/'call-intents').glob('*.json')) and not a.resume:p.error('Explicit --resume required for an existing call journal')
        try:
            out=execute(root,a.persistent,stage,a.dataset,'Q' if stage=='acquire' else a.judge,a.cache_dir,mock=a.mock,smoke=a.stage=='smoke',stop_after=a.stop_after)
        except BaseException:
            # Exports report incomplete/unsafe state, never repairs it or retries a call.
            export(root,None);raise
        print(canonical(out));export(root,a.persistent)


def cli(argv=None):
    try:return main(argv)
    except Exception as exc:
        import traceback
        locations=[{'file':Path(f.filename).name,'line':f.lineno,'function':f.name} for f in traceback.extract_tb(exc.__traceback__)]
        print(canonical({'status':'stopped','type':type(exc).__name__,'locations':locations,'action':'preserve scratch; no automatic retry'}))
        raise SystemExit(1) from None

if __name__=='__main__':cli()
