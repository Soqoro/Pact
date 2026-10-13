"""Review-gated exact-deletion mechanism test; zero default generation budget."""
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
import argparse
import json
import math
import shutil
import tempfile
import time
import zipfile

from ..util import read_json, write_json, digest, file_hash, canonical
from ..artifacts import ShardStore, run_lock, sync_run
from ..backends import Request
from ..environment import code_identity, runtime_fingerprint
from ..training.receiver import JournalBackend
from ..storage import persist_bundle, storage_operation
from ..training.feasibility import read_review
from .heterogeneity import immutable
from .forensics import CHILD, check, lines, private_root
from .semantic_review import TextSpan, display, review_state, package, normalized
from .adjudication_contracts import (MODELS, VICTIMS, CAP, CONTEXT, AdjudicationInput,
    RationalePerturbation, EvalSpec, from_record, perturb, invariance, prompt, decision)
from .adjudication import MockJudge, validate_identity
from .breadth import BreadthJournal
from .adjudication_metrics import paired

VERSIONS=('rewrite_reference_repeat','cue_deleted','sham_deleted')
REPO=Path(__file__).resolve().parents[3]
APPROVAL_FLAGS=('unsupported_isolated_cue','redundant_noncue_sham','no_task_content_removed',
                'no_answer_removed','both_coherent','no_other_cue_removed')


def deletions(source, cue, sham):
    c=TextSpan(**cue).validate(source);s=TextSpan(**sham).validate(source)
    if not (c.end<=s.start or s.end<=c.start):raise ValueError('Cue and sham overlap')
    result={'rewrite_reference_repeat':source,'cue_deleted':source[:c.start]+source[c.end:],
            'sham_deleted':source[:s.start]+source[s.end:]}
    if any(not v.strip() for v in result.values()):raise ValueError('Empty edited rationale')
    return result


def token_match(cue,sham,tokenizers):
    result={}
    for key,tok in tokenizers.items():
        c=len(tok(cue));s=len(tok(sham));limit=max(8,math.ceil(.2*c))
        result[key]={'cue_tokens':c,'sham_tokens':s,'tolerance':limit,'compatible':abs(c-s)<=limit}
    return result


def prepare(root,source,mock=False):
    root=private_root(root,mock);receipt=check(source)
    if receipt['fixture']!=mock:raise ValueError('Fixture flag differs')
    # Freeze a derivative copy for portable Colab operation. No mutation of forensics.
    target=root/'forensics'
    if target.exists():
        if read_json(root/'source.json')['receipt_hash']!=digest(receipt):raise ValueError('Source changed')
        return read_json(root/'source.json')
    if root.resolve()==Path(source).resolve() or root.resolve().is_relative_to(Path(source).resolve()) or Path(source).resolve().is_relative_to(root.resolve()):raise ValueError('Child must be separate')
    if any(p.is_symlink() for p in Path(source).rglob('*')):raise ValueError('Symlink in reviewed source')
    shutil.copytree(source,target)
    obj={'schema_version':1,'run_id':CHILD,'fixture':mock,'receipt_hash':digest(receipt),
         'files':{p.relative_to(target).as_posix():file_hash(p) for p in sorted(target.rglob('*')) if p.is_file() and p.name!='.lock'}}
    immutable(root/'source.json',obj)
    return obj


def source_check(root):
    s=read_json(root/'source.json')
    if not s['fixture']:
        from .gpqa_data import outside_git
        outside_git(root)
    for n,h in s['files'].items():
        from ..artifacts import safe_relative
        safe_relative(n);p=root/'forensics'/n
        if p.is_symlink() or file_hash(p)!=h:raise ValueError('Frozen review/source changed')
    return s


def validate(root):
    root=Path(root);source=source_check(root);f=root/'forensics'
    panel=read_json(f/'review_manifest.private.json');slots=read_json(f/'span_slot_manifest.json')
    if slots['review_manifest_hash']!=digest(panel) or len(slots['slots'])>32:raise ValueError('Panel/slot mismatch')
    units={u['unit_id']:u for u in panel['units']};regs=[read_json(p) for p in sorted((f/'reviewers').glob('*/identity.json'))]
    human=[r for r in regs if r['origin']=='human' or source['fixture'] and r['origin']=='fixture']
    states={r['reviewer_id']:review_state(f,r['reviewer_id']) for r in human}
    review_complete=len(states)==2 and all(all(st.get(u['unit_id'],{}).get('locked_at')
        for u in panel['units'] if u['accepted']) for st in states.values())
    edits=[];elig=[]
    for uid in slots['slots']:
        u=units[uid];reason='unreviewed';proposals=[];reviews=[]
        if not u['main'] or u['style'] not in ('claimed_consensus','claimed_verification') or not u['accepted']:
            raise ValueError('Intervention outside frozen main-panel source slots')
        if review_complete:
            reviews=[s.get(uid,{}) for s in states.values()]
            if all(r.get('locked_at') and r.get('independent') and r.get('outcome_blinded') for r in reviews):
                reason='no_adequate_sham'
                for r in reviews:
                    ep=r.get('edit_proposal');_,side=display(u,r.get('reviewer_id'))
                    if not ep:
                        reason=r.get('edit_ineligibility') or 'no_adequate_sham'
                        continue
                    if ep['side']!=side:raise ValueError('Deletion is not on rewritten text')
                    if r['task_substantive_relation']=='uncertain':reason='review_disputed';continue
                    if not all(ep.get(k) is True for k in APPROVAL_FLAGS):reason='substantive_edit_required';continue
                    deletions(u['rewritten'],ep['cue'],ep['sham'])
                    proposals.append({k:ep[k] for k in ('cue','sham',*APPROVAL_FLAGS)})
                if len(proposals)==2:
                    reason='eligible' if proposals[0]==proposals[1] else 'review_disputed'
                nr=[normalized(r,u) for r in reviews]
                if any(nr[0].get(k)!=nr[1].get(k) for k in ('task_substantive_relation','factual_premise_changes','logical_inference_changes')):
                    reason='review_disputed'
        if reason=='eligible':
            ep=proposals[0];versions=deletions(u['rewritten'],ep['cue'],ep['sham'])
            edits.append({'unit_id':uid,'task_id':u['task_id'],'group_id':u['group_id'],'dataset':u['dataset'],'stratum':u['stratum'],
                          'style':u['style'],'target':u['target'],'attempt_key':u['attempt_key'],
                          'source_hash':digest(u['rewritten']),'review_hashes':[digest(x) for x in reviews],
                          'edits':ep,'versions':versions,'version_hashes':{k:digest(v) for k,v in versions.items()}})
        elig.append({'unit_id':uid,'status':reason})
    out={'schema_version':1,'source_hash':digest(source),'slots_hash':digest(slots),'eligibility':elig,'edits':edits,
         'reviews_complete':review_complete,
         'status':'review_ready' if edits else 'not_testable_under_current_reviews','max_calls':len(edits)*18}
    immutable(root/'validated_edits.json',out)
    from .forensics import save_lines
    save_lines(root/'reviewed_edits.jsonl',edits)
    return out


def build_requests(root,edits):
    f=root/'forensics/parent';records={r['task']['task_id']:r for r in read_json(f/'bank.json')['records']}
    clean={(r['task_id'],r['model'],r['mode']):r for r in lines(f/'clean_per_task.jsonl')}
    old={(r['task_id'],r['model'],r['mode'],r['style']):r for r in lines(f/'attacked_per_task.jsonl')}
    out=[]
    for e in edits:
        rec=records[e['task_id']];bank=from_record(rec)
        for model in ('J8','J14'):
            for mode in VICTIMS:
                seed=clean[e['task_id'],model,mode]['seed']
                for version in VERSIONS:
                    view=perturb(bank,RationalePerturbation(e['task_id'],e['target'],e['style'],e['versions'][version],e['attempt_key']))
                    invariance(bank,view,e['target'],EvalSpec(rec['eval']['answer']))
                    req=Request(bank.task,prompt(AdjudicationInput(view,mode)),'base','final',seed,CAP,True)
                    row={k:e[k] for k in ('unit_id','task_id','group_id','dataset','stratum')}
                    row.update(model=model,mode=mode,version=version,seed=seed,edit_hash=digest(e),
                               request_hash=digest(req),historical=old[e['task_id'],model,mode,e['style']],
                               request=asdict(req),bank=asdict(view),gold=rec['eval']['answer'])
                    out.append(row)
    return out


def preflight(root,cache,mock=False,execute=False):
    source=source_check(root)
    if mock!=source['fixture'] or not mock and not execute:raise ValueError('Explicit metadata preflight opt-in required')
    edits=read_json(root/'validated_edits.json')['edits'];tokenizers={};receipts={};renders={}
    if mock:
        for key in ('J8','J14'):
            tok=lambda s:list(s.split());tokenizers[key]=tok
            b=MockJudge(key);receipts[key]=b.identity;renders[key]=b.render_messages
    else:
        from ..backends.native import metadata
        from ..backends.registry import render_native
        from huggingface_hub import snapshot_download
        from transformers import AutoTokenizer
        for key in ('J8','J14'):
            receipt=metadata(key,cache,spec=MODELS[key]);receipts[key]=receipt
            expected=read_json(root/'forensics/parent/access'/f'{key}.json')
            for field in ('spec','metadata_hashes','weight_files','weight_metadata','template_hash','parameters','precision','attention','adapters'):
                if receipt[field]!=expected[field]:raise ValueError('Parent frozen model contract differs')
            path=snapshot_download(MODELS[key].repository,revision=MODELS[key].revision,cache_dir=str(cache),allow_patterns=list(receipt['metadata_hashes']),local_files_only=True)
            tokenizer=AutoTokenizer.from_pretrained(path,trust_remote_code=False,local_files_only=True)
            tokenizers[key]=lambda s,t=tokenizer:t(s,add_special_tokens=False)['input_ids']
            renders[key]=lambda m,t=tokenizer,k=key:render_native(t,m,MODELS[k])
    checks=[];ready=[]
    for e in edits:
        lengths=token_match(e['edits']['cue']['text'],e['edits']['sham']['text'],tokenizers)
        prompts=[]
        for row in build_requests(root,[e]):
            req=request_from(row);n=len(tokenizers[row['model']](renders[row['model']](req.messages)))
            prompts.append({'request_hash':row['request_hash'],'model':row['model'],'version':row['version'],'mode':row['mode'],'input_tokens':n,'compatible':n+CAP<=CONTEXT})
        ok=all(v['compatible'] for v in lengths.values()) and all(v['compatible'] for v in prompts)
        checks.append({'unit_id':e['unit_id'],'lengths':lengths,'prompts':prompts,'eligible':ok})
        if ok:ready.append(e['unit_id'])
    obj={'schema_version':1,'edit_hash':digest(read_json(root/'validated_edits.json')),'receipts':receipts,'checks':checks,'ready':ready,'fixture':mock}
    immutable(root/'preflight.json',obj)
    return obj


def freeze(root):
    source=source_check(root);valid=read_json(root/'validated_edits.json');pre=read_json(root/'preflight.json')
    if pre['edit_hash']!=digest(valid) or pre['fixture']!=source['fixture']:raise ValueError('Preflight differs')
    edits=[e for e in valid['edits'] if e['unit_id'] in pre['ready']];rows=build_requests(root,edits)
    if len(rows)>576 or len(edits)>32:raise ValueError('Hard budget exceeded')
    plan={'schema_version':1,'run_id':CHILD,'fixture':source['fixture'],'source':code_identity(REPO),
          'source_hash':digest(source),'reviewed_edits_hash':digest(valid),'preflight_hash':digest(pre),
          'models':{k:asdict(MODELS[k]) for k in ('J8','J14')},'requests':rows,
          'budget':{'calls':len(rows),'reserved_tokens':len(rows)*CAP,'hard_calls':576,'hard_tokens':294912},
          'smoke_units':[e['unit_id'] for e in edits[:2]],'paid_calls':0,'training_updates':0,'teacher_forced':0,
          'status':'ready_for_explicit_user_decision' if rows else 'not_testable'}
    immutable(root/'span_plan.json',plan)
    if not (root/'state.json').exists():write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
    template={'schema_version':1,'plan_hash':digest(plan),'reviewed_edits_hash':plan['reviewed_edits_hash'],
              'models_hash':digest(plan['models']),'requests_hash':digest(rows),'budget':plan['budget'],
              'approved':False,'origin':None,'approved_by':None,'decision_reference':None}
    immutable(root/'authorization.template.json',template)
    return {'plan_hash':digest(plan),'budget':plan['budget'],'status':plan['status']}


def load(root):
    p=read_json(root/'span_plan.json');s=source_check(root)
    if digest(p)!=read_json(root/'state.json')['plan_hash'] or p['source_hash']!=digest(s):raise ValueError('Plan/source mismatch')
    if p['reviewed_edits_hash']!=digest(read_json(root/'validated_edits.json')) or p['preflight_hash']!=digest(read_json(root/'preflight.json')):raise ValueError('Review/preflight changed')
    pre=read_json(root/'preflight.json');ed=[e for e in read_json(root/'validated_edits.json')['edits'] if e['unit_id'] in pre['ready']]
    if p['requests']!=json.loads(canonical(build_requests(root,ed))):raise ValueError('Request plan altered')
    if len(p['requests'])>576 or p['budget']['calls']!=len(p['requests']) or p['budget']['reserved_tokens']!=len(p['requests'])*CAP:raise ValueError('Budget altered')
    if p['models']!={k:asdict(MODELS[k]) for k in ('J8','J14')} or p['budget']['hard_calls']!=576 or p['budget']['hard_tokens']!=294912:
        raise ValueError('Frozen models/hard ceilings changed')
    return p


def authorize(root,path,mock=False):
    plan=load(root);auth=read_json(path);template=read_json(root/'authorization.template.json')
    for k in ('schema_version','plan_hash','reviewed_edits_hash','models_hash','requests_hash','budget'):
        if auth.get(k)!=template[k]:raise ValueError('Authorization does not bind frozen artifacts')
    if auth.get('approved') is not True or auth.get('origin')!=('fixture' if mock else 'user') or not auth.get('approved_by') or not auth.get('decision_reference'):
        raise ValueError('Separate explicit user decision required; no inferred approval')
    if mock!=plan['fixture']:raise ValueError('Mock approval cannot authorize real work')
    immutable(root/'authorization.json',auth)
    return auth


def request_from(row):
    from ..benchmarks.contracts import BenchmarkInput
    from ..schemas import Message
    r=row['request'];return Request(BenchmarkInput.from_dict(r['task']),tuple(Message(m['role'],m['content']) for m in r['messages']),r['actor'],r['phase'],r['seed'],r['max_tokens'],r['deterministic'])


def view_from(row):
    from .adjudication_contracts import FrozenCandidateBank,Candidate
    from ..benchmarks.contracts import BenchmarkInput
    b=row['bank'];return FrozenCandidateBank(BenchmarkInput.from_dict(b['task']),b['team'],tuple(Candidate(**c) for c in b['candidates']))


def rowkey(plan,row):return digest([CHILD,digest(plan),row])


def inspect(root,plan):
    allowed={digest([rowkey(plan,r),0]):r for r in plan['requests']}
    intents={p.stem:read_json(p) for p in (root/'call-intents').glob('*.json')};results={};unknown=[]
    store=ShardStore(root/'calls')
    for k,i in intents.items():
        if k not in allowed:raise ValueError('Unknown span request')
        row=allowed[k];req=request_from(row)
        expected={'schema_version':1,'work_id':k,'record_id':rowkey(plan,row),'slot':0,'request_hash':digest(req),'max_tokens':CAP}
        if i!=expected:raise ValueError('Intent changed')
        if not store.path(k).exists() or not store.path(k).with_suffix('.sha256').exists():unknown.append(k);continue
        value=store.read(k);identity=read_json(root/'identities'/f"{row['model']}.json")
        validate_identity(identity,row['model'],{'models':plan['models'],'fixture':plan['fixture']})
        if not plan['fixture']:
            receipt=read_json(root/'preflight.json')['receipts'][row['model']]
            if any(identity.get(k)!=v for k,v in receipt.items()):raise ValueError('Runtime/preflight identity changed')
        validator=object.__new__(SpanJournal);validator.identity=identity;validator.plan={'profile':{'context':CONTEXT}}
        validator.record_key=rowkey(plan,row);validator.allowed={validator.record_key:row}
        validator._validate(req,i,value);results[k]=value
    for f in (root/'calls/shards').glob('*'):
        if f.stem not in intents or f.suffix not in ('.json','.sha256'):raise ValueError('Orphan span result')
    if len(intents)>plan['budget']['calls'] or len(intents)*CAP>plan['budget']['reserved_tokens']:raise ValueError('Attempt budget exceeded')
    return intents,results,unknown


class SpanJournal(JournalBackend):
    _validate=BreadthJournal._validate
    def __init__(self,backend,root,plan,before):
        self.backend,self.root,self.identity=backend,root,backend.identity
        self.plan={'profile':{'context':CONTEXT}}
        self.intents,self.results,unknown=inspect(root,plan)
        if unknown:raise ValueError('Ambiguous dispatch: no retry')
        self.allowed={rowkey(plan,r):r for r in plan['requests']};self.store=ShardStore(root/'calls')
        self.budget={'generation_calls_upper_bound':plan['budget']['calls'],'generated_tokens_upper_bound':plan['budget']['reserved_tokens']}
        self.calls=[];self.seen=set();self.generation_tokens={};self.new_calls=0;self.stop_after=None;self.before_new=before
    def validate_request(self,req):
        row=self.allowed.get(self.record_key)
        if row is None or req!=request_from(row) or row['model']!=self.identity['spec']['key']:raise ValueError('Wrong judge/stage/request')


def checkpoint(root,persistent):
    if persistent is None:return
    result=package(root,root.parent/'bundles'/f'{CHILD}-checkpoint-{time.time_ns()}.zip',CHILD+'_private')
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        p=Path(d);shutil.copyfile(result['path'],p/'state.zip')
        write_json(p/'receipt.json',{'sha256':result['sha256'],**read_json(root/'state.json')})
        sync_run(p,persistent,timeout_seconds=300)


def evaluate(root,judge,cache,persistent,mock=False,smoke=False,resume=False):
    plan=load(root)
    if plan['fixture']!=mock:raise ValueError('Mock/real mismatch')
    authorize(root,root/'authorization.json',mock)
    if code_identity(REPO)!=plan['source']:raise ValueError('Pinned child source changed')
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe dispatch window; preserve forensics')
    intents,results,unknown=inspect(root,plan)
    if unknown or intents and not resume:raise ValueError('Unknown dispatch or explicit resume missing')
    rows=[r for r in plan['requests'] if r['model']==judge and (not smoke or r['unit_id'] in plan['smoke_units'])]
    pending=[r for r in rows if digest([rowkey(plan,r),0]) not in results]
    if not pending:return {'new_calls':0}
    if not mock and (persistent is None or cache is None):raise ValueError('Durable root/cache required')
    pre=read_json(root/'preflight.json');backend=None;started=time.monotonic();new=0;dispatch=False
    try:
        if mock:backend=MockJudge(judge)
        else:
            from ..backends.native import NativeBackend
            backend=NativeBackend(judge,pre['receipts'][judge],cache,spec=MODELS[judge])
        validate_identity(backend.identity,judge,{'fixture':mock,'models':plan['models']})
        immutable(root/'identities'/f'{judge}.json',backend.identity)
        def before():
            nonlocal dispatch
            write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':False})
            if not dispatch:checkpoint(root,persistent)
            dispatch=True
        wrapper=SpanJournal(backend,root,plan,before)
        for row in pending:
            req=request_from(row)
            actual_tokens=backend.count_tokens(backend.render_messages(req.messages))
            expected=next(p['input_tokens'] for check in pre['checks'] for p in check['prompts']
                          if p['model']==judge and p['request_hash']==row['request_hash'])
            if actual_tokens!=expected or actual_tokens+CAP>CONTEXT:raise ValueError('Recipient context changed')
            wrapper.begin_record(rowkey(plan,row));wrapper.generate(req);new+=1
            if new%20==0:checkpoint(root,persistent)
        write_json(root/'resources'/f'{time.time_ns()}.json',{'model':judge,'calls':new,'wall_seconds':time.monotonic()-started,**backend.resource_usage()})
    finally:
        if backend is not None:backend.close()
    write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
    try:checkpoint(root,persistent)
    except BaseException:
        write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':False});raise
    return {'new_calls':new}


def report(root):
    plan=load(root);intents,results,unknown=inspect(root,plan);rows=[]
    for r in plan['requests']:
        v=results.get(digest([rowkey(plan,r),0]));d=decision(v['raw'],v['call']['stop_reason'],AdjudicationInput(view_from(r),r['mode'])) if v else None
        rows.append({k:r[k] for k in ('unit_id','task_id','group_id','stratum','dataset','model','mode','version')}|{
            'status':d.status if d else 'missing','answer':d.answer if d else None,'candidate_id':d.candidate_id if d else None,
            'correct':d.status=='ok' and d.answer==r['gold'] if d else None,
            'historical_correct':r['historical']['attacked'],'historical_answer':r['historical']['answer']})
    from .forensics import save_lines
    # Results grow on resume; report files are mutable, dispatch artifacts are not.
    (root/'span_results.private.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
    grouped=defaultdict(dict)
    for r in rows:grouped[r['unit_id'],r['model'],r['mode']][r['version']]=r
    comparisons=defaultdict(list);conditional=defaultdict(list);reference=defaultdict(list)
    changes=defaultdict(list);old_failures=defaultdict(list);distributions=defaultdict(list)
    for row in rows:
        distributions['/'.join(row[k] for k in ('dataset','model','mode','version'))].append(row)
    for vs in grouped.values():
        ref,cue,sham=[vs[v] for v in VERSIONS];k='/'.join(ref[x] for x in ('dataset','model','mode'))
        comparisons[k].append({**ref,'clean':sham['correct'],'attacked':cue['correct']})
        reference[k].append({**ref,'clean':ref['historical_correct'],'attacked':ref['correct']})
        if ref['correct'] is False:conditional[k].append({**ref,'clean':sham['correct'],'attacked':cue['correct']})
        if ref['historical_correct'] is False:old_failures[k].append({**ref,'clean':sham['correct'],'attacked':cue['correct']})
        for version in ('cue_deleted','sham_deleted'):
            changes[k+'/'+version].append({**ref,'clean':ref['correct'],'attacked':vs[version]['correct']})
    def compare(vs):
        v=paired(vs)
        v['intended_units']=v.pop('intended_tasks');v['paired_units']=v.pop('paired_tasks')
        v['unique_task_groups']=len({x['group_id'] for x in vs})
        return v
    out={'schema_version':1,'status':('not_testable' if not plan['requests'] else 'complete' if len(results)==len(plan['requests']) else 'partial'),
         'fixture':plan['fixture'],'planned_calls':len(plan['requests']),'attempted':len(intents),'committed':len(results),'unresolved':len(unknown),
         'reserved_output_tokens':len(intents)*CAP,'input_tokens':sum(v['call']['input_tokens'] for v in results.values()),
         'output_tokens':sum(v['call']['output_tokens'] for v in results.values()),
         'cue_minus_sham':{k:compare(v) for k,v in comparisons.items()},'reference_repeat_vs_historical':{k:compare(v) for k,v in reference.items()},
         'deletion_vs_new_reference':{k:compare(v) for k,v in changes.items()},
         'secondary_old_reference_failures':{k:compare(v) for k,v in old_failures.items()},
         'secondary_new_reference_failures':{k:compare(v) for k,v in conditional.items()},
         'distributions':{k:{'answers':dict(Counter(x['answer'] for x in v if x['answer'] is not None)),
                            'candidate_ids':dict(Counter(x['candidate_id'] for x in v if x['candidate_id'] is not None)),
                            'statuses':dict(Counter(x['status'] for x in v))} for k,v in distributions.items()},
         'plan_hash':digest(plan),'reviewed_edits_hash':plan['reviewed_edits_hash'],
         'statuses':dict(Counter(r['status'] for r in rows)), 'resources':[read_json(p) for p in (root/'resources').glob('*.json')],
         'interpretation':'Human-assisted local span test, not a deployable defense. Task-grouped paired units; no automatic next experiment.'}
    write_json(root/'span_summary.json',out);return out


def export(root,persistent=None):
    report(root);stamp=time.time_ns();out={}
    for kind in ('PRIVATE','SANITIZED'):
        path=root.parent/'bundles'/f'{CHILD}-{kind}-{stamp}.zip'
        if kind=='PRIVATE':result=package(root,path,CHILD+'_private')
        else:
            with tempfile.TemporaryDirectory(dir=root.parent) as d:
                p=Path(d);shutil.copyfile(root/'span_summary.json',p/'span_summary.json');result=package(p,path,CHILD+'_sanitized')
        out[kind.lower()]=result
        if persistent:persist_bundle(Path(result['path']),persistent/'bundles'/path.name,result['sha256'],timeout_seconds=300)
    return out


def unpack(bundle,sha,root,mock=False):
    if root.exists():raise ValueError('Destination must be absent')
    content=read_review(bundle,sha,max_members=60000,max_bytes=512*1024**2,allow_text=True,selected_names={'HANDOFF.json','source.json'})
    if content['HANDOFF.json']['kind']!=CHILD+'_private' or content['source.json']['fixture']!=mock:raise ValueError('Private matching child bundle required')
    private_root(root,mock)
    with zipfile.ZipFile(bundle) as z:
        for n in z.namelist():
            if n in ('HANDOFF.json','review_checksums.json'):continue
            p=root/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read(n))
    plan=load(root);inspect(root,plan)
    if not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe restored child; no retry')


def restore(persistent,root,mock=False):
    snaps=sorted((persistent/'snapshots').glob('*'))
    if not snaps:raise ValueError('No snapshot')
    latest=snaps[-1];idx=read_json(latest/'index.json')
    if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json') or set(idx['files'])!={'receipt.json','state.zip'}:raise ValueError('Invalid latest snapshot; no fallback')
    def obj(n):
        h=idx['files'][n]
        if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Invalid object hash')
        p=persistent/'objects'/h
        if p.is_symlink() or file_hash(p)!=h:raise ValueError('Corrupt durable object')
        return p
    receipt=read_json(obj('receipt.json'))
    if not receipt['recovery_safe'] or receipt['sha256']!=idx['files']['state.zip']:raise ValueError('Unsafe latest; no fallback')
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        local=Path(d)/'state.zip';storage_operation('bundle-restore',obj('state.zip'),local,sha256=receipt['sha256'],timeout_seconds=600)
        unpack(local,receipt['sha256'],root,mock)
    if digest(load(root))!=receipt['plan_hash']:raise ValueError('Restored receipt/plan mismatch')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['prepare','validate','preflight','plan','authorize','evaluate','smoke','report','export','restore','import-bundle'])
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--forensics',type=Path);p.add_argument('--cache-dir',type=Path);p.add_argument('--persistent',type=Path)
    p.add_argument('--file',type=Path);p.add_argument('--bundle',type=Path);p.add_argument('--sha256');p.add_argument('--judge',choices=['J8','J14'])
    p.add_argument('--plan-hash');p.add_argument('--execute',action='store_true');p.add_argument('--mock',action='store_true');p.add_argument('--resume',action='store_true')
    a=p.parse_args(argv);root=a.run_dir
    if a.stage in ('restore','import-bundle'):
        root.parent.mkdir(parents=True,exist_ok=True)
        if a.stage=='restore':restore(a.persistent,root,a.mock)
        else:unpack(a.bundle,a.sha256,root,a.mock)
        return 0
    private_root(root,a.mock)
    with run_lock(root):
        if a.stage=='prepare':out=prepare(root,a.forensics,a.mock)
        elif a.stage=='validate':out=validate(root)
        elif a.stage=='preflight':out=preflight(root,a.cache_dir,a.mock,a.execute)
        elif a.stage=='plan':out=freeze(root)
        elif a.stage=='authorize':out=authorize(root,a.file,a.mock)
        elif a.stage=='report':out=report(root)
        elif a.stage=='export':out=export(root,a.persistent)
        else:
            if not a.execute or not a.judge or a.plan_hash!=digest(load(root)):raise ValueError('Explicit execute, judge and frozen plan hash required')
            try:out=evaluate(root,a.judge,a.cache_dir,a.persistent,a.mock,a.stage=='smoke',a.resume)
            except BaseException:
                export(root,None);raise
            export(root,a.persistent)
    print(canonical(out if a.stage in ('plan','export') else {'stage':a.stage,'status':'finished'}))
    return 0
