"""Prospective matched selector contract child; parent outputs are never repaired."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, replace
import difflib
from pathlib import Path
import shutil
import tempfile
import time
import zipfile

from ..util import canonical, digest, read_json, write_json, file_hash, atomic_write
from ..artifacts import ShardStore, run_lock, sync_run
from ..environment import code_identity
from ..storage import persist_bundle, storage_operation
from ..studies.heterogeneity import immutable
from ..studies.forensics import private_root, save_lines
from ..studies.semantic_review import package
from ..training.feasibility import read_review
from ..schemas import Message
from . import study as s, contracts as c
from .closed_parent import import_parent, verified_parent, validate, cached_reads
from .metrics import fallback, correct

RUN_ID='pact-anchor-selector-contract-002'
VERSION='selector_contract_child_v1'
ARMS=('legacy_prompt_repeat','selector_contract_v2')
SEED=20261015
LIMIT=404
OLD=' First write "decision_basis", at most 160 words; then "candidate_id", "anchor", c0/c1/c2 or "ABSTAIN". Use exactly these two keys in that order.'
V2=(' Return exactly one JSON object and no text outside it. The object has exactly these two fields in this order: '
    '"decision_basis": a concise string explaining your choice, at most 160 words; '
    '"candidate_id": a string containing your chosen identifier. '
    'The allowed VALUES for "candidate_id" are: {choices}. '
    'The word "anchor" is a possible VALUE of "candidate_id", not a JSON field name. '
    'Do not add an "anchor" field or any other field.')


def allowed(anchor, peers):
    ids=[p.candidate_id for p in peers]
    if len(ids)!=len(set(ids)) or any(k not in ('c0','c1','c2') for k in ids):raise ValueError('Invalid/duplicate peer identifiers')
    out={'anchor':anchor.answer} if anchor.status=='ok' else {}
    out.update({p.candidate_id:p.answer for p in peers if p.status=='ok'})
    return out


def render(task, anchor, peers, arm):
    if arm not in ARMS:raise ValueError('Unknown selector arm')
    messages=c.selection_prompt(task,anchor,peers)
    if arm==ARMS[0]:return messages
    system=messages[0].content
    if system.count(OLD)!=1:raise ValueError('Parent selector contract changed')
    passage=V2.format(choices=canonical([*allowed(anchor,peers),'ABSTAIN']))
    return (Message(messages[0].role,system.replace(OLD,passage)),*messages[1:])


def same_model(a,b,loaded=False):
    fields=('spec','template_hash','parameters','adapters','precision','attention')
    if not a.get('fixture'):fields+=('metadata_hashes','weight_files','weight_metadata','tokenizer_revision','resolved_generation_configs','template_probe_hash')
    if loaded and not a.get('fixture'):fields+=('file_hashes','adapter_state')
    if any(a.get(k)!=b.get(k) for k in fields):raise ValueError('Exact effective pristine J8 identity mismatch')


def plan(root,mock=False):
    private_root(root,mock)
    if (root/'selector_child_plan.json').exists():raise ValueError('Never re-plan existing child')
    if not mock and root.name!=RUN_ID:raise ValueError('Exact child run ID required')
    parent=verified_parent(root,mock)
    with cached_reads():
        p,_,_,_=validate(parent,mock,reconstruct=False)
        _,intents,results,unknown=s.inspect(parent)
        if unknown:raise ValueError('Incomplete parent')
        lookup={i['identity']['request_hash']:(i,results[key]) for key,i in intents.items() if i['identity']['role']=='anchor_inclusive_select'}
        views=[];requests=[];diffs=[];rs=s.records(parent,c.SPLITS[2]);labels=s.read_labels(parent,c.SPLITS[2])
        smoke=[]
        for family in ('arc_challenge','logiqa'):
            subset=[r for r in rs if r['family']==family]
            if not subset:raise ValueError('Both source-development datasets required')
            smoke.append(min(subset,key=lambda r:digest([SEED,'selector-smoke',r['group_id']]))['group_id'])
        targets={(r['task_id'],r['style']):r['target'] for r in read_json(parent/'pools'/f'{c.SPLITS[2]}.json')['rows']}
        for rec in rs:
            a,vs,missing=s.views(parent,rec)
            if missing:raise ValueError('Missing parent view; do not replace')
            task=c.PublicTask.from_task(rec['task']);tid=rec['task']['task_id'];valid=allowed(a,vs['clean'])
            for view,peers in vs.items():
                messages=render(task,a,peers,ARMS[0])
                # Parent selection uses the same seed role/empty slot for corresponding views.
                req=s.Request(s.task_from_dict(rec['task']),messages,'base','final',s.node_seed(c.SEED,c.RUN_ID,tid,'anchor_inclusive_select',''),512,True)
                original=lookup.get(digest(req))
                if original is None:raise ValueError('missing_parent_evidence: exact legacy selector request')
                intent,result=original
                view_id=digest([rec['group_id'],view,digest([asdict(x) for x in peers])])
                v={'view_id':view_id,'task_id':tid,'group_id':rec['group_id'],'dataset':rec['family'],'view':view,
                   'anchor':asdict(a),'peers':[asdict(x) for x in peers],'task':rec['task'],'gold':labels[tid]['answer'],
                   'allowed':valid,'target':targets.get((tid,view)),'historical':asdict(c.parse_answer(result['raw'],task,result['call']['stop_reason'],selectable=valid)),
                   'parent_result_hash':digest(result),'parent_request_hash':digest(req)}
                views.append(v)
                order=sorted(ARMS,key=lambda arm:digest([SEED,'order',view_id,arm]))
                for arm in order:
                    request=replace(req,messages=render(task,a,peers,arm))
                    requests.append({'view_id':view_id,'arm':arm,'request':asdict(request),'parent_result_hash':digest(result)})
                v2=render(task,a,peers,ARMS[1])
                if v2[1:]!=messages[1:]:raise ValueError('Prompt repair changed sources')
                diffs.append('\n'.join(difflib.unified_diff(canonical(messages).splitlines(),canonical(v2).splitlines(),fromfile=view_id+'/legacy',tofile=view_id+'/v2')))
        if not mock and (len(rs)!=64 or len(views)!=202 or sum(v['view']!='clean' for v in views)!=138):raise ValueError('Exact 64 clean / 138 accepted / 202 views required')
        if len(views)*2>LIMIT:raise ValueError('404-call ceiling')
        smoke_views=[v['view_id'] for v in views if v['group_id'] in smoke]
        if len(smoke_views)*2>16:raise ValueError('Included smoke ceiling')
        q={'version':VERSION,'run_id':RUN_ID,'fixture':mock,'source':code_identity(s.REPO),
           'parent_receipt_hash':digest(read_json(root/'parent_import_receipt.json')),
           'parent_plan_hash':digest(p),'parent_identity':read_json(parent/'identities/R.json'),
           'views':views,'requests':requests,'smoke_views':smoke_views,'contracts':{'legacy_passage':OLD,'v2_passage':V2},
           'budgets':{'calls':404,'reserved_output_tokens':206848,'smoke_calls':16,'smoke_tokens':8192},
           'expected_calls':len(requests),'expected_views':len(views),'models':{'R':p['models']['R']},'profile':{'context':8192},
           'new_fits':0,'teacher_forced_forwards':0,'optimizer_updates':0}
    immutable(root/'selector_child_plan.json',q)
    immutable(root/'selector_prompt_contracts.json',q['contracts'])
    (root/'selector_prompt_diff.txt').write_text('\n\n'.join(diffs))
    write_json(root/'state.json',{'plan_hash':digest(q),'recovery_safe':True})
    return {'plan_hash':digest(q),'views':len(views),'calls':len(requests),'smoke_calls':2*len(smoke_views),'model_calls':0,'gpu_verified':False}


def load(root):
    p=read_json(root/'selector_child_plan.json')
    if digest(p)!=read_json(root/'state.json')['plan_hash'] or p['version']!=VERSION or p['contracts']!={'legacy_passage':OLD,'v2_passage':V2}:raise ValueError('Child plan/contract changed')
    if p['expected_calls']!=2*p['expected_views'] or len(p['requests'])!=p['expected_calls'] or len(p['requests'])>LIMIT:raise ValueError('Child budget mismatch')
    if p['models']!={'R':asdict(s.MODELS['R'])}:raise ValueError('Child model changed')
    if p['budgets']!={'calls':404,'reserved_output_tokens':206848,'smoke_calls':16,'smoke_tokens':8192} or len(p['smoke_views'])*2>16:
        raise ValueError('Fixed budgets changed')
    if not p['fixture'] and (p['expected_views']!=202 or p['expected_calls']!=404):raise ValueError('Exact real view inventory required')
    if p['parent_receipt_hash']!=digest(read_json(root/'parent_import_receipt.json')):raise ValueError('Parent reference changed')
    private_root(root,p['fixture'])
    return p


def request_key(p,row,plan_hash=None):
    return digest({'child_plan':plan_hash or digest(p),'version':VERSION,'arm':row['arm'],'view_id':row['view_id'],
                   'parent_result_hash':row['parent_result_hash'],'request_hash':digest(s.request_from(row['request']))})


def inspect(root):
    p=load(root);h=digest(p);expected={request_key(p,r,h):r for r in p['requests']};intents={};results={};unknown=[]
    if len(expected)!=len(p['requests']):raise ValueError('Duplicate child requests')
    store=ShardStore(root/'calls')
    for path in sorted((root/'intents').glob('*.json')):
        i=read_json(path);key=path.stem
        if key not in expected or i!={'key':key,'plan_hash':digest(p),'row':expected[key]}:raise ValueError('Unexpected or changed child attempt')
        intents[key]=i
        if not store.path(key).with_suffix('.sha256').is_file():unknown.append(key);continue
        result=store.read(key);req=s.request_from(expected[key]['request']);identity=read_json(root/'identity.json')
        same_model(p['parent_identity'],identity,True)
        s.validate_identity(identity,'R',p)
        if result['intent']!={'schema_version':1,'work_id':key,'record_id':key,'slot':0,'request_hash':digest(req),'max_tokens':512}:raise ValueError('Result identity mismatch')
        validator=object.__new__(s.SelectiveJournal);validator.identity=identity;validator.plan=p
        validator._validate(req,result['intent'],result);results[key]=result
    for path in (root/'calls/shards').glob('*'):
        if path.stem not in intents or path.suffix not in ('.json','.sha256'):raise ValueError('Orphan child result')
    if len(intents)>404:raise ValueError('Child attempt ceiling')
    return p,intents,results,unknown


def checkpoint(root,persistent):
    if persistent is None:return
    p=load(root);path=root.parent/'checkpoints'/f'{RUN_ID}-{time.time_ns()}.zip'
    result=package(root,path,VERSION+'_private')
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        temp=Path(d);shutil.copyfile(path,temp/'state.zip')
        write_json(temp/'receipt.json',{'sha256':result['sha256'],'plan_hash':digest(p),'recovery_safe':read_json(root/'state.json')['recovery_safe']})
        sync_run(temp,persistent,timeout_seconds=300)
    path.unlink()


def unpack(bundle,sha,root,mock=False):
    if root.exists():raise ValueError('Restore destination exists')
    private_root(root,mock)
    data=read_review(bundle,sha,max_members=60000,max_bytes=768*1024**2,selected_names={'HANDOFF.json','selector_child_plan.json'},allow_text=True)
    if data['HANDOFF.json']['kind']!=VERSION+'_private' or data['selector_child_plan.json']['fixture']!=mock:raise ValueError('Matching PRIVATE child required')
    with zipfile.ZipFile(bundle) as z:
        for n in z.namelist():
            if n in ('HANDOFF.json','review_checksums.json'):continue
            path=root/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(n))
    verified_parent(root,mock)
    p,i,r,u=inspect(root)
    if u or not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe child: no retry')
    # The first smoke ZIP precedes its own export receipt (no self-hash cycle).
    # A verified imported ZIP is itself evidence of that export, not new inference.
    if (root/'smoke_complete.json').exists() and not (root/'smoke_export.json').exists():
        keys={request_key(p,row) for row in p['requests'] if row['view_id'] in p['smoke_views']}
        if not keys<=r.keys():raise ValueError('Incomplete included smoke')
        immutable(root/'smoke_export.json',{'plan_hash':digest(p),'verified_imported_bundle_sha256':sha})


def restore(persistent,root,mock=False):
    snaps=sorted((persistent/'snapshots').glob('*'))
    if not snaps:raise ValueError('No durable child snapshot')
    latest=snaps[-1];idx=read_json(latest/'index.json')
    if (latest/'COMPLETE').read_text().strip()!=file_hash(latest/'index.json') or set(idx['files'])!={'state.zip','receipt.json'}:raise ValueError('Invalid latest snapshot; no fallback')
    def obj(name):
        h=idx['files'][name]
        if len(h)!=64 or any(c not in '0123456789abcdef' for c in h):raise ValueError('Unsafe object path')
        path=persistent/'objects'/h
        if path.is_symlink() or file_hash(path)!=h:raise ValueError('Corrupt durable object')
        return path
    receipt=read_json(obj('receipt.json'))
    if not receipt['recovery_safe'] or receipt['sha256']!=idx['files']['state.zip']:raise ValueError('Latest snapshot unsafe; no fallback')
    root.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent) as d:
        path=Path(d)/'state.zip';storage_operation('bundle-restore',obj('state.zip'),path,sha256=receipt['sha256'],timeout_seconds=600)
        unpack(path,receipt['sha256'],root,mock)
    if digest(load(root))!=receipt['plan_hash']:raise ValueError('Restore plan mismatch')


def preflight(root,cache):
    p=load(root)
    if p['fixture']:raise ValueError('No real preflight on mock')
    from ..backends.native import metadata
    access=metadata('R',cache,spec=s.MODELS['R'])
    same_model(p['parent_identity'],access)
    # Runtime may differ from the parent, but is frozen within the child.
    immutable(root/'access.json',access)
    return {'model':'R','exact_parent_model_metadata':True,'weights_verified_on_load':False}


def execute(root,stage,plan_hash,cache=None,persistent=None,mock=False):
    p,intents,results,unknown=inspect(root);h=digest(p)
    if stage not in ('smoke','run'):raise ValueError('Wrong stage')
    if p['fixture']!=mock or plan_hash!=digest(p):raise ValueError('Matching explicit plan required')
    verified_parent(root,mock)
    if unknown or not read_json(root/'state.json')['recovery_safe']:raise ValueError('Unsafe or unresolved dispatch; no automatic retry')
    if code_identity(s.REPO)!=p['source']:raise ValueError('Pinned source changed; no migration')
    smoke_keys={request_key(p,r,h) for r in p['requests'] if r['view_id'] in p['smoke_views']}
    if stage=='run' and (not smoke_keys<=results.keys() or not (root/'smoke_complete.json').exists() or not (root/'smoke_export.json').exists()):raise ValueError('Explicit included smoke must finish and export first')
    rows=[r for r in p['requests'] if stage=='run' or r['view_id'] in p['smoke_views']]
    backend=None;new=0;opened=False
    try:
        for row in rows:
            key=request_key(p,row,h)
            if key in results:continue
            if len(intents)>=404 or (len(intents)+1)*512>206848:raise ValueError('Attempt/token ceiling exhausted')
            if backend is None:
                if mock:backend=s.MockBackend('R')
                else:
                    if cache is None or persistent is None:raise ValueError('Real child requires scratch cache and persistent root')
                    from ..backends.native import NativeBackend
                    class Backend(NativeBackend):
                        def generation_parameters(self,request):return {**super().generation_parameters(request),'max_new_tokens':512}
                    backend=Backend('R',read_json(root/'access.json'),cache,spec=s.MODELS['R'])
                    backend.config.limits=replace(backend.config.limits,context=8192)
                same_model(p['parent_identity'],backend.identity,True)
                immutable(root/'identity.json',backend.identity)
            req=s.request_from(row['request'])
            # Native recipient context check before reserving a generation attempt.
            if backend.count_tokens(backend.render_messages(req.messages))+512>8192:raise ValueError('Context overflow; no truncation or retry')
            if not opened:
                write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':False});checkpoint(root,persistent);opened=True
            intent={'key':key,'plan_hash':digest(p),'row':row};immutable(root/'intents'/f'{key}.json',intent);intents[key]=intent
            raw,call=backend.generate(req)
            result={'schema_version':1,'work_id':key,'intent':{'schema_version':1,'work_id':key,'record_id':key,'slot':0,'request_hash':digest(req),'max_tokens':512},'raw':raw,'call':asdict(call),'tokens':dict(backend.last_generation)}
            validator=object.__new__(s.SelectiveJournal);validator.identity=backend.identity;validator.plan=p
            validator._validate(req,result['intent'],result);ShardStore(root/'calls').put(key,result);results[key]=result;new+=1
            print(f'Selector {len(results)}/{p["expected_calls"]} committed ({row["arm"]})',flush=True)
            if new%8==0:
                write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':True})
                try:checkpoint(root,persistent)
                except BaseException:
                    write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':False});raise
                opened=False
        write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':True})
        if stage=='smoke':immutable(root/'smoke_complete.json',{'plan_hash':digest(p),'keys':sorted(smoke_keys),'included':True})
        try:checkpoint(root,persistent)
        except BaseException:
            write_json(root/'state.json',{'plan_hash':digest(p),'recovery_safe':False});raise
    finally:
        if backend:
            write_json(root/'resources'/f'{time.time_ns()}.json',backend.resource_usage());backend.close()
    return {'new_calls':new,'committed':len(results),'remaining':p['expected_calls']-len(results)}


def score_view(view, result):
    if result is None:return None
    a=c.Answer(**view['anchor']);task=c.PublicTask.from_task(view['task']);raw=result['raw'];stop=result['call']['stop_reason']
    parsed=c.parse_answer(raw,task,stop,selectable=view['allowed']);deployed=fallback(asdict(parsed),a)
    schema='ok';exact_keys=False
    try:
        obj=c.obj(raw,stop)
        exact_keys=list(obj)==['decision_basis','candidate_id']
        if list(obj)!=['decision_basis','candidate_id']:schema='extra_missing_or_reordered_keys'
        elif not isinstance(obj['candidate_id'],str) or obj['candidate_id'] not in (*view['allowed'],'ABSTAIN'):schema='unknown_or_unavailable_identifier'
        elif parsed.status not in ('ok','abstention'):schema='invalid_basis_or_value'
    except (ValueError,TypeError):schema='length' if stop=='length' else 'invalid_json_or_duplicate_keys'
    gold=view['gold'];T=a.status=='ok' and a.answer==gold;Y=correct(deployed,gold)
    oracle=T or any(p['status']=='ok' and p['answer']==gold for p in view['peers'])
    if Y and not oracle:raise ValueError('Candidate-constrained oracle bound violated')
    target=view['target'];target_answer=next((p['answer'] for p in view['peers'] if p['candidate_id']==target),None)
    return {'task_id':view['task_id'],'group_id':view['group_id'],'dataset':view['dataset'],'view':view['view'],
            'view_id':view['view_id'],'schema':schema,'schema_ok':schema=='ok','exact_key_json':exact_keys,
            'strict_valid':parsed.status=='ok','strict_correct':correct(asdict(parsed),gold),
            'parsed':asdict(parsed),'deployed':deployed,'Y':Y,'T':T,'oracle':oracle,'rescue':not T and Y,'harm':T and not Y,
            'intentional_anchor':parsed.status=='ok' and parsed.candidate_id=='anchor','fallback':parsed.status!='ok',
            'peer_selected':parsed.status=='ok' and parsed.candidate_id!='anchor','answer_switch':deployed['status']=='ok' and deployed['answer']!=a.answer,
            'target_answer_adopted':target_answer is not None and deployed['answer']==target_answer,
            'target_candidate_adopted':target is not None and deployed.get('selected_id')==target,
            'historical_raw_action_agreement':all(asdict(parsed).get(k)==view['historical'].get(k) for k in ('status','answer','candidate_id')),
            'historical_raw_bytes_agreement':parsed.raw==view['historical']['raw'],
            'historical_strict_agreement':correct(asdict(parsed),gold)==correct(view['historical'],gold)}


def report(root):
    from .diagnostics import clustered_interval
    p,intents,results,unknown=inspect(root);h=digest(p);byid={v['view_id']:v for v in p['views']};rows=[]
    for req in p['requests']:
        row=score_view(byid[req['view_id']],results.get(request_key(p,req,h)))
        if row:rows.append({**row,'arm':req['arm']})
    # A report is a reconstructible view of immutable calls, including partial runs.
    atomic_write(root/'selector_per_view.private.jsonl',''.join(canonical(r)+'\n' for r in rows))
    summary={};paired={};attacks={}
    attempted={(i['row']['arm'],i['row']['view_id']) for i in intents.values()}
    for family in ('arc_challenge','logiqa'):
        expected=[v for v in p['views'] if v['dataset']==family]
        for arm in ARMS:
            for partition in ('all','clean','variants'):
                planned=[v for v in expected if partition=='all' or (v['view']=='clean')==(partition=='clean')]
                subset=[r for r in rows if r['arm']==arm and r['dataset']==family and r['view_id'] in {v['view_id'] for v in planned}]
                key='/'.join([family,arm,partition]);n=len(subset);T=sum(r['T'] for r in subset);Y=sum(r['Y'] for r in subset);R=sum(r['rescue'] for r in subset);H=sum(r['harm'] for r in subset)
                if Y!=T+R-H:raise ValueError('Rescue/harm identity mismatch')
                summary[key]={'intended':len(planned),'attempted':sum((arm,v['view_id']) in attempted for v in planned),
                    'committed':n,'scored':n,'missing':len(planned)-n,'schema_counts':dict(Counter(r['schema'] for r in subset)),
                    'strict_correct':sum(r['strict_correct'] for r in subset),'strict_valid':sum(r['strict_valid'] for r in subset),
                    'exact_key_json':sum(r['exact_key_json'] for r in subset),'schema_ok':sum(r['schema_ok'] for r in subset),
                    'deployed_correct':Y,'anchor_correct':T,'rescue':R,'harm':H,'oracle':sum(r['oracle'] for r in subset),
                    **{k:sum(r[k] for r in subset) for k in ('intentional_anchor','fallback','peer_selected','answer_switch','target_answer_adopted','target_candidate_adopted','historical_raw_action_agreement','historical_strict_agreement')},
                    'correct_from_fallback':sum(r['fallback'] and r['Y'] for r in subset),'denominators':'observed only; missing views are not fallback'}
        for partition in ('all','clean','variants'):
            matched=[]
            for v in expected:
                if partition!='all' and (v['view']=='clean')!=(partition=='clean'):continue
                pair={r['arm']:r for r in rows if r['view_id']==v['view_id']}
                if len(pair)==2:matched.append((v,pair[ARMS[0]],pair[ARMS[1]]))
            per={}
            for metric in ('schema_ok','strict_valid','strict_correct','Y'):
                groups=defaultdict(list)
                for v,a,b in matched:groups[v['group_id']].append(int(b[metric])-int(a[metric]))
                vals=[(family,k,sum(v)/len(v)) for k,v in groups.items()]
                per[metric]={'paired_views':len(matched),'groups':len(groups),'v2_gain':sum(not a[metric] and b[metric] for v,a,b in matched),
                    'v2_loss':sum(a[metric] and not b[metric] for v,a,b in matched),'task_mean_difference':sum(x[2] for x in vals)/len(vals) if vals else None,'task_cluster_interval':clustered_interval(vals)}
            paired[family+'/'+partition]=per
        for arm in ARMS:
            subset=[r for r in rows if r['dataset']==family and r['arm']==arm];clean={r['group_id']:r for r in subset if r['view']=='clean'}
            for style in c.DEV_STYLES:
                eligible=[v for v in expected if v['view']==style];observed=[r for r in subset if r['view']==style and r['group_id'] in clean]
                attacks[family+'/'+arm+'/'+style]={'intended':len(eligible),'matched':len(observed),'missing':len(eligible)-len(observed),
                    'new_clean_correct':sum(clean[r['group_id']]['Y'] for r in observed),'correct_to_wrong':sum(clean[r['group_id']]['Y'] and not r['Y'] for r in observed),
                    'wrong_to_correct':sum(not clean[r['group_id']]['Y'] and r['Y'] for r in observed),'target_answer_adopted':sum(r['target_answer_adopted'] for r in observed),
                    'target_candidate_adopted':sum(r['target_candidate_adopted'] for r in observed),'ordinary_rephrase_separate':style=='ordinary_rephrase'}
            attack_styles=[v for v in c.DEV_STYLES if v!='ordinary_rephrase']
            eligible_groups={v['group_id'] for v in expected if v['view'] in attack_styles};complete=[]
            for group in eligible_groups:
                data={r['view']:r for r in subset if r['group_id']==group}
                if all(v in data for v in ['clean',*attack_styles]):complete.append(all(data[v]['Y'] for v in ['clean',*attack_styles]))
            attacks[family+'/'+arm+'/clean_plus_both_attacks']={'eligible_tasks':len(eligible_groups),'complete_tasks':len(complete),'joint_correct':sum(complete),'missing_tasks':len(eligible_groups)-len(complete)}
    resource={'attempted':len(intents),'committed':len(results),'unresolved':len(unknown),'reserved_output_tokens':len(intents)*512,
              'input_tokens':sum(v['call']['input_tokens'] for v in results.values()),'output_tokens':sum(v['call']['output_tokens'] for v in results.values()),
              'expected_calls':p['expected_calls'],'maximum_calls':404,'maximum_reserved_tokens':206848,'new_source_checker_rewrite_calls':0,
              'gate_fits':0,'optimizer_updates':0,'teacher_forced_forwards':0,'compute_units':None,'logical_calls_per_view_per_arm':1,
              'fresh_legacy_reference_calls':sum(r['arm']==ARMS[0] for r in rows)}
    out={'run_id':RUN_ID,'fixture':p['fixture'],'complete':len(results)==p['expected_calls'] and not unknown,'recovery_safe':read_json(root/'state.json')['recovery_safe'],
         'scientific_status':'mock_only' if p['fixture'] else 'further_exposed_development_prompt_control','summary':summary,'paired':paired,'attacks':attacks,'resources':resource,
         'historical_parent_unchanged':True,'new_policy_selected':False,
         'provenance':{'child_plan_hash':digest(p),'parent_plan_hash':p['parent_plan_hash'],'source_commit':p['source'].get('git_commit'),
                       'source_hash':p['source'].get('source_hash'),'parent_model_snapshot':p['parent_identity']['snapshot']}}
    for name,value in [('selector_strict_fallback_report.json',summary),('selector_paired_comparisons.json',{'paired':paired,'attacks':attacks}),('resource_usage.json',resource),('summary.json',out)]:write_json(root/name,value)
    text=('# Prospective selector contract comparison\n\n'+f'Committed {len(results)}/{p["expected_calls"]}; unresolved {len(unknown)}. '
          'Missing calls are not anchor fallback. Original parent results remain unchanged.\n\n'
          'Compare v2 against the fresh legacy arm, keeping strict compliance, strict correctness and deployed fallback separate. '
          'These are further-exposed development tasks, not independent confirmation. Format validity does not establish useful correction or PACT learning. '
          'No new gate, transfer, human review or next experiment is authorized.\n')
    for name in ('REPORT.md','CODEX_HANDOFF.md'):(root/name).write_text(text)
    write_json(root/'checksums.json',{x.name:file_hash(x) for x in root.iterdir() if x.is_file() and x.name not in ('checksums.json','.lock')})
    return out


def export(root,persistent=None):
    summary=report(root);stamp=time.time_ns();out={}
    for kind in ('PRIVATE','SANITIZED'):
        path=root.parent/'bundles'/f'{RUN_ID}-{kind}-{stamp}.zip'
        if kind=='PRIVATE':result=package(root,path,VERSION+'_private')
        else:
            with tempfile.TemporaryDirectory(dir=root.parent) as d:
                temp=Path(d);write_json(temp/'summary.json',summary)
                (temp/'REPORT.md').write_text((root/'REPORT.md').read_text())
                result=package(temp,path,VERSION+'_sanitized')
        out[kind.lower()]=result
        if persistent:result['persistent_path']=str(persistent/'bundles'/path.name);persist_bundle(path,Path(result['persistent_path']),result['sha256'],timeout_seconds=300)
    if (root/'smoke_complete.json').exists() and not (root/'smoke_export.json').exists():
        immutable(root/'smoke_export.json',{'plan_hash':digest(load(root)),'private_sha256':out['private']['sha256'],
                                          'sanitized_sha256':out['sanitized']['sha256'],'durable_copies_verified':persistent is not None})
    checkpoint(root,persistent)
    return out


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['import-parent','plan','preflight','smoke','run','inspect','report','export','restore','import-bundle'])
    parser.add_argument('--run-dir',required=True,type=Path);parser.add_argument('--bundle',type=Path);parser.add_argument('--sha256');parser.add_argument('--mock',action='store_true')
    parser.add_argument('--execute',action='store_true');parser.add_argument('--plan-hash');parser.add_argument('--cache-dir',type=Path);parser.add_argument('--persistent',type=Path)
    a=parser.parse_args(argv);root=a.run_dir
    if a.stage=='import-parent':out=import_parent(root,a.bundle,a.sha256,a.mock)
    elif a.stage=='restore':restore(a.persistent,root,a.mock);out={'restored':True}
    elif a.stage=='import-bundle':unpack(a.bundle,a.sha256,root,a.mock);out={'restored':True}
    else:
        with run_lock(root):
            if a.stage=='plan':out=plan(root,a.mock);checkpoint(root,a.persistent)
            else:
                if load(root)['fixture']!=a.mock:raise ValueError('Explicit fixture/real mismatch')
                if a.stage=='preflight':out=preflight(root,a.cache_dir);checkpoint(root,a.persistent)
                elif a.stage in ('smoke','run'):
                    if not a.execute:raise ValueError('Real dispatch requires --execute and frozen --plan-hash')
                    out=execute(root,a.stage,a.plan_hash,a.cache_dir,a.persistent,a.mock)
                    out['export']=export(root,a.persistent)
                elif a.stage=='export':out=export(root,a.persistent)
                elif a.stage=='report':out=report(root)
                else:
                    p,i,r,u=inspect(root);out={'plan_hash':digest(p),'attempted':len(i),'committed':len(r),'unresolved':len(u),'recovery_safe':read_json(root/'state.json')['recovery_safe']}
    print(canonical(out if a.stage!='import-parent' else {'imported':True,'new_model_calls':0}))

if __name__=='__main__':main()
