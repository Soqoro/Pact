"""Bounded GPQA development study. No training, attacks, retries or final-test mode."""
import argparse
from collections import Counter
import dataclasses as dc
import json
from pathlib import Path
from types import SimpleNamespace
import time

from ..artifacts import ShardStore, run_lock, sync_run
from ..backends import Request
from ..environment import code_identity, versions
from ..evaluation import score
from ..protocol import Protocol, private_prompt
from ..schemas import task_from_dict, TaskLabel, AttackRecord
from ..util import canonical,digest,file_hash,read_json,write_json,node_seed
from ..training.receiver import JournalBackend,CallBoundaryStop
from ..training.collection_config import CollectionRuntime
from ..training.colab import review_bundle
from ..training.feasibility import read_review
from ..storage import persist_bundle,storage_operation
from . import gpqa_data as data
from .gpqa_model import source_contract,load as load_model
from .gpqa_metrics import summarize

RUN_ID='qwen3-gpqa-diamond-support-001'
BUDGET={'generation_calls_upper_bound':256,'generated_tokens_upper_bound':53248}
SLOTS=[('private','agent-0',256),('private','agent-1',256),('private','agent-2',256),
       ('final','base',64),('revision','agent-0',256),('revision','agent-1',256),
       ('revision','agent-2',256),('final','base',64)]


class MissingCall(Exception):pass


def request_seed(task_id,slot):
    seed=node_seed(data.SEED,task_id,'trajectory')
    if slot<3:return node_seed(seed,'private',slot)
    if slot==3:return node_seed(node_seed(seed,'independent-synthesis'),'final')
    if slot<7:return node_seed(seed,'revision',slot-4)
    return node_seed(seed,'final')


def clean(task):
    return AttackRecord(digest([task.task_id,'clean']),task.task_id,'clean','none','',None,None,0,0,
                        task.split,task.dataset_revision,task.source_hash,'gpqa clean only; no attack')


def freeze_plan(prepared,contract,source):
    selected=prepared['selected'];manifest=prepared['manifest']
    if (len(selected)!=32 or manifest['selected_ids']!=[r['task']['task_id'] for r in selected]
        or prepared['receipt']['revision']!=data.REVISION):raise ValueError('GPQA frozen selection contract changed')
    for row in selected:
        task=task_from_dict(row['task']);data.require_development(task)
        if len(task.options)!=4 or len({o.text.strip() for o in task.options})!=4:
            raise ValueError('GPQA selected options must be four distinguishable strings')
    return {'schema_version':1,'kind':'gpqa_support','run_id':RUN_ID,'seed':data.SEED,'budget':BUDGET,
        'usage':'development_diagnostic','training_allowed':False,'eligible_for_untouched_final':False,
        'source':source,'dataset_hash':digest(prepared),'dataset':prepared,'frozen_arm':contract,
        'protocol':'existing packet protocol; shared private packets; vote/synthesis/clean synchronous debate',
        'slots':SLOTS,'optimizer_steps':0,'teacher_forced_forwards':0,'donor_calls':0,
        'smoke_ids':manifest['selected_ids'][:2],'prompt_version':'pact.protocol at source hash',
        'screen':{'mixed_tasks':8,'denominator':32,'dominant_invalid_private_packets':48}}


def load_plan(root):
    plan=read_json(root/'plan.json');state=read_json(root/'state.json')
    if (digest(plan)!=state['plan_hash'] or plan['budget']!=BUDGET or plan['run_id']!=RUN_ID or
        plan['seed']!=data.SEED or len(plan['dataset']['selected'])!=32 or
        plan['dataset_hash']!=digest(plan['dataset'])):raise ValueError('Frozen GPQA plan mismatch')
    expected=freeze_plan(plan['dataset'],plan['frozen_arm'],plan['source'])
    if canonical(expected)!=canonical(plan):raise ValueError('Frozen GPQA design changed')
    return plan


def journals(root,plan):
    """Read committed immutable shards and retain ambiguous attempts as missing."""
    intents={p.stem:read_json(p) for p in (root/'call-intents').glob('*.json')}
    store=ShardStore(root/'calls');results={};unresolved=[]
    allowed={digest([digest(t),i]) for t in plan['dataset']['manifest']['selected_ids'] for i in range(8)}
    for key,intent in intents.items():
        slot=intent.get('slot',-1)
        if (key not in allowed or intent.get('work_id')!=key or intent.get('schema_version')!=1 or
            not 0<=slot<8 or intent.get('max_tokens')!=SLOTS[slot][2] or
            key!=digest([intent['record_id'],slot])):raise ValueError('Invalid GPQA attempt identity/stage')
        p=store.path(key)
        if not p.exists() or not p.with_suffix('.sha256').exists():unresolved.append(key);continue
        result=store.read(key)
        if result['intent']!=intent:raise ValueError('GPQA intent/result mismatch')
        results[key]=result
    if any(p.stem not in intents or p.suffix not in ('.json','.sha256') for p in (root/'calls/shards').glob('*')):
        raise ValueError('Unjournaled GPQA result')
    if len(intents)>256 or sum(x['max_tokens'] for x in intents.values())>53248:raise ValueError('GPQA budget exceeded')
    return intents,results,unresolved


class GPQAJournal(JournalBackend):
    def __init__(self,backend,root,plan,*,readonly=False,stop_after=None,before_new=lambda:None):
        self.backend,self.root,self.plan=backend,Path(root),plan
        self.budget=BUDGET;self.identity=backend.identity
        self.intents,self.results,unresolved=journals(root,plan)
        if unresolved and not readonly:raise ValueError('Ambiguous GPQA attempt; no automatic regeneration or budget reset')
        self.readonly=readonly;self.store=ShardStore(self.root/'calls')
        self.stop_after,self.before_new=stop_after,before_new
        self.calls,self.seen,self.generation_tokens=[],set(),{}
        self.new_calls=0
        self.tasks={r['task']['task_id']:r['task'] for r in plan['dataset']['selected']}

    def validate_request(self,request):
        data.require_development(request.task)
        if request.task.task_id not in self.tasks or canonical(request.task)!=canonical(self.tasks[request.task.task_id]):
            raise ValueError('Protected/unplanned/modified GPQA input forbidden')
        if (not 0<=self.slot<8 or (request.phase,request.actor,request.max_tokens)!=SLOTS[self.slot]
            or request.deterministic!=(request.phase=='final') or self.record_key!=digest(request.task.task_id)
            or request.seed!=request_seed(request.task.task_id,self.slot)):
            raise ValueError('GPQA stage/actor/cap mismatch')

    def generate(self,request):
        self.validate_request(request)
        key=digest([self.record_key,self.slot])
        if self.readonly and key not in self.results:raise MissingCall()
        if not self.readonly and key not in self.results:
            prompt=self.backend.tokenizer.apply_chat_template([{'role':m.role,'content':m.content} for m in request.messages],
                tokenize=False,add_generation_prompt=True,enable_thinking=False)
            if self.backend.count_tokens(prompt)+request.max_tokens>4096:
                raise ValueError('GPQA context overflow before dispatch; no prompt truncation or task replacement')
        return super().generate(request)

    def _validate(self,request,intent,result):
        call=super()._validate(request,intent,result)
        kind='final' if request.phase=='final' else 'packet'
        if json.loads(call.parameters_json)!=self.plan['frozen_arm']['parameters'][kind]:
            raise ValueError('GPQA decoding differs from recorded frozen arm')
        return call


def task_private(protocol,task):
    journal=protocol.backend;journal.begin_record(digest(task.task_id))
    seed=node_seed(data.SEED,task.task_id,'trajectory')
    return tuple(protocol.private_packet(task,i,clean(task),node_seed(seed,'private',i)) for i in range(3))


def task_complete(protocol,task,private):
    seed=node_seed(data.SEED,task.task_id,'trajectory');attack=clean(task)
    frozen_hash=digest(private)
    vote=protocol.suffix(task,'vote',attack,private,seed,digest([task.task_id,'vote']))
    synthesis=protocol.suffix(task,'synthesis',attack,private,node_seed(seed,'independent-synthesis'),digest([task.task_id,'synthesis']))
    debate=protocol.suffix(task,'debate',attack,private,seed,digest([task.task_id,'debate']))
    if digest(private)!=frozen_hash or synthesis.private!=debate.private:raise ValueError('Private packets changed between branches')
    return vote,synthesis,debate


class Recovery:
    """Use existing snapshots once before/after each task, not per cached call."""
    def __init__(self,root,persistent):self.root,self.persistent=Path(root),Path(persistent)
    def mark(self,safe):
        state=read_json(self.root/'state.json')
        if not safe and not state['recovery_safe']:return
        state['recovery_safe']=safe;write_json(self.root/'state.json',state)
        sync_run(self.root,self.persistent,timeout_seconds=120)
    def before(self):self.mark(False)
    def after(self):self.mark(True)


def collect(plan,root,backend,runtime,stage,*,smoke=False,recovery=None,stop_after=None):
    if stage not in ('private','complete') or (smoke and stage!='complete'):raise ValueError('GPQA stage mismatch')
    if backend.identity['snapshot']!=plan['frozen_arm']['checkpoint']['snapshot']:raise ValueError('GPQA effective adapter snapshot changed')
    recovery=recovery or SimpleNamespace(before=lambda:None,after=lambda:None)
    journal=GPQAJournal(backend,root,plan,stop_after=stop_after,before_new=recovery.before)
    protocol=Protocol(runtime,journal)
    tasks=[task_from_dict(r['task']) for r in plan['dataset']['selected']]
    # All 32 private prompts preflight before ANY model dispatch, including smoke.
    for task in tasks:
        rendered=backend.tokenizer.apply_chat_template([{'role':m.role,'content':m.content} for m in private_prompt(task,'')],
            tokenize=False,add_generation_prompt=True,enable_thinking=False)
        if backend.count_tokens(rendered)+256>4096:raise ValueError('GPQA private context overflow; fixed selection must not change')
    if smoke:tasks=tasks[:2]
    for task in tasks:
        before=journal.new_calls
        private=task_private(protocol,task)
        ShardStore(root/'private').put(digest(task.task_id),{'schema_version':1,'work_id':digest(task.task_id),'private':[dc.asdict(p) for p in private]})
        if stage=='complete':
            vote,synthesis,debate=task_complete(protocol,task,private)
            ShardStore(root/'complete').put(digest(task.task_id),{'schema_version':1,'work_id':digest(task.task_id),
                'vote':dc.asdict(vote),'synthesis':dc.asdict(synthesis),'debate':dc.asdict(debate)})
        backend.assert_unchanged()
        if journal.new_calls>before:recovery.after()
        print('GPQA task committed:',task.task_id,stage,flush=True)
    return {'committed_calls':len(journal.results),'new_calls':journal.new_calls,'stage':stage,'smoke':smoke}


def report(root):
    root=Path(root);plan=load_plan(root)
    intents,calls,unresolved=journals(root,plan)
    identity=plan['frozen_arm']['checkpoint']
    # Trusted replay of stored calls through the same protocol; no inference function.
    backend=SimpleNamespace(identity=identity,tokenizer=SimpleNamespace(eos_token_id=plan['frozen_arm']['parameters']['final']['eos_token_id']),
                            count_tokens=lambda text:0)
    journal=GPQAJournal(backend,root,plan,readonly=True)
    protocol=Protocol(CollectionRuntime(digest(plan),data.SEED),journal)
    rows=[];protocol_rows=[]
    for item in plan['dataset']['selected']:
        task=task_from_dict(item['task']);label=TaskLabel(task.task_id,item['label']['answer_id'])
        try:private=task_private(protocol,task)
        except MissingCall:continue
        valid=[p.parser_status=='ok' for p in private];c0=[v and p.answer_id==label.answer_id for v,p in zip(valid,private)]
        row={'task_id':task.task_id,'domain':item['private_metadata']['domain'],'c0':c0,'answers0':[p.answer_id for p in private],
            'valid0':valid,'parser0':[p.parser_status for p in private],
            'stop0':[p.call.stop_reason for p in private],'complete':False}
        try:
            vote,synthesis,debate=task_complete(protocol,task,private)
        except MissingCall:
            rows.append(row);continue
        scored=score(debate,label)
        # Natural opportunities require valid original packets, including stop status.
        scored['helpful']=[any(c0[j] for j in range(3) if j!=i) for i in range(3)]
        scored['misleading']=[any(valid[j] and not c0[j] for j in range(3) if j!=i) for i in range(3)]
        row.update(complete=True,c1=scored['revised'],parser1=[p.parser_status for p in debate.revised],
            stop1=[p.call.stop_reason for p in debate.revised],
            final_parser={'synthesis':synthesis.final.parser_status,'debate':debate.final.parser_status},
            final_stop={'synthesis':synthesis.final.call.stop_reason,'debate':debate.final.call.stop_reason},vote=score(vote,label)['success'],
            synthesis=score(synthesis,label)['success'],debate=scored['success'])
        rows.append(row);protocol_rows.append(scored)
    costs={}
    for name,slots in {'private':(0,1,2),'independent_readout':(3,),'revision':(4,5,6),'debate_readout':(7,)}.items():
        selected=[c['call'] for c in calls.values() if c['intent']['slot'] in slots]
        costs[name]={'calls':len(selected),'input_tokens':sum(c['input_tokens'] for c in selected),
            'output_tokens':sum(c['output_tokens'] for c in selected),'generation_seconds':sum(c['elapsed_seconds'] for c in selected)}
    accounting={'attempted_calls':len(intents),'committed_calls':len(calls),'unresolved_attempts':len(unresolved),
        'reserved_output_tokens':sum(i['max_tokens'] for i in intents.values()),'budget':BUDGET,'by_stage':costs,
        'input_tokens':sum(v['input_tokens'] for v in costs.values()),'output_tokens':sum(v['output_tokens'] for v in costs.values()),
        'generation_seconds':sum(v['generation_seconds'] for v in costs.values()),'compute_units':None,
        'optimizer_steps':0,'teacher_forced_forwards':0,'donor_calls':0,'suffix_replays':0}
    result=summarize(rows,protocol_rows,accounting)
    # Option letters are unnecessary in the shareable per-task view; correctness
    # plus letters could otherwise reveal evaluator labels for identified items.
    for row in result['per_task']:row.pop('answers0',None)
    result['logical_deployment_costs']={name:{k:sum(costs[s][k] for s in stages) for k in ('calls','input_tokens','output_tokens','generation_seconds')}
        for name,stages in {'vote':('private',),'synthesis':('private','independent_readout'),
                            'debate':('private','revision','debate_readout')}.items()}
    result['completion_status_counts']={stage:dict(Counter(s for r in rows for s in r.get(field,[]))) for stage,field in [('private','parser0'),('revision','parser1')]}
    result['incomplete_justification_policy']='length-limited packets fail strict scoring even if an answer prefix is visible; raw status/tokens retained privately; no answer salvage in primary metrics'
    result['logical_cost_note']='Each protocol charged shared private use; actual study totals count private calls only once; generation seconds are not billed GPU time.'
    result['partition']={k:plan['dataset']['manifest'][k] for k in ('selected_ids','protected_ids','excluded_ids','group_by_id','selected_domain_counts','domain_counts','eligibility_policy','option_identity',
        'source_integrity_excluded_ids','exclusion_reasons','eligible_group_count')}
    result['configuration']={'run_id':RUN_ID,'selection_seed':data.SEED,'generation_seed':data.SEED,'model':'Qwen/Qwen3-8B',
        'precision':'bfloat16 backbone; recorded effective FP32 actors','thinking':False,'attention':'sdpa',
        'context_cap':4096,'packet_cap':256,'readout_cap':64,'sampling':{'temperature':.7,'top_p':.8,'top_k':20,'min_p':0.,'repetition_penalty':1.},
        'arm':'frozen','usage':'development_diagnostic','training_allowed':False,'eligible_for_untouched_final':False}
    resources=[read_json(p) for p in root.glob('resources-*.json')]
    result['invocations']={'count':len(resources),'wall_seconds':sum(r['invocation_seconds'] for r in resources),'compute_units':None}
    result['identity']={'plan_hash':digest(plan),'source':plan['source'],'dataset_revision':data.REVISION,
        'dataset_hash':plan['dataset_hash'],'effective_snapshot':identity['snapshot'],
        'effective_actor_tensor_hashes':identity['effective_actor_tensor_hashes'],
        'recovery_receipt_hash':identity['recovery_receipt_hash'],'template_hash':identity['template_hash']}
    if identity.get('backend')=='mock':result['scientific_status']='mock_only'
    write_json(root/'summary.json',result)
    return result


def export(root,persistent):
    root=Path(root);result=report(root)
    bundles=root.parent/'bundles';stamp=time.time_ns()
    handoff=('GPQA development-only clean support study. Private bundle: NOT FOR PUBLIC REDISTRIBUTION. '
        'Raw prompts, responses, labels and decodable IDs are private. Sanitized summary cannot audit raw prompts. '
        'No weights included; initialization requires the verified preparation snapshot. '
        'No training, attacks, final-test or automatic follow-up. Small task sample; human review required.\n')
    (root/'CODEX_HANDOFF.md').write_text(handoff)
    private=review_bundle(root,bundles/f'{RUN_ID}-PRIVATE-{stamp}.zip',{'completed_tasks':result['completed_tasks']},
        kind='gpqa_support_private',scientific_status=result['scientific_status'],include_markdown=True,max_metadata_bytes=256*1024**2)
    # Allowlisted summary built from parsed booleans/IDs/counts, never generic redaction of raw artifacts.
    import tempfile
    with tempfile.TemporaryDirectory(prefix='gpqa-sanitized-',dir=root.parent) as tmp:
        public=Path(tmp);write_json(public/'summary.json',result)
        (public/'CODEX_HANDOFF.md').write_text('Sanitized GPQA summary; insufficient for raw-prompt audit. No automatic follow-up.\n')
        sanitized=review_bundle(public,bundles/f'{RUN_ID}-SANITIZED-{stamp}.zip',{'completed_tasks':result['completed_tasks']},
            kind='gpqa_support_sanitized',scientific_status=result['scientific_status'],include_markdown=True)
    print('Local private bundle (do not publish):',canonical(private),flush=True)
    print('Local sanitized bundle:',canonical(sanitized),flush=True)
    snapshot=sync_run(root,Path(persistent),timeout_seconds=120)
    for view,bundle in (('private',private),('sanitized',sanitized)):
        target=Path(persistent)/'bundles'/Path(bundle['path']).name
        persist_bundle(Path(bundle['path']),target,bundle['sha256'],timeout_seconds=120)
        bundle['persistent_path']=str(target)
    return {'private':private,'sanitized':sanitized,'snapshot':str(snapshot)}


def read_bundle(path,sha,*,private=False):
    content=read_review(Path(path),sha,max_members=10000,max_bytes=256*1024**2,allow_text=True)
    kind='gpqa_support_private' if private else 'gpqa_support_sanitized'
    if content['HANDOFF.json']['kind']!=kind:raise ValueError('GPQA bundle view mismatch')
    return content


def audit_private_bundle(path,sha):
    """Reconstruct metrics locally from bounded checksummed data, never imported code."""
    import tempfile
    import zipfile
    content=read_bundle(path,sha,private=True)
    with tempfile.TemporaryDirectory(prefix='gpqa-private-audit-') as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(path) as archive:
            for name in content:
                dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True)
                dest.write_bytes(archive.read(name))
                if '/shards/' in name:
                    expected=content['HANDOFF.json']['inventory'][name]['sha256']
                    if file_hash(dest)!=expected:raise ValueError('Private shard inventory mismatch')
                    dest.with_suffix('.sha256').write_text(expected)
        rebuilt=report(root)
        if 'summary.json' in content and canonical(rebuilt)!=canonical(content['summary.json']):
            raise ValueError('Private GPQA report does not reproduce')
        return rebuilt


def save_failure(root,exc):
    if not (root/'plan.json').exists() or (root/'.lock').exists():return
    write_json(root/'errors'/f'{time.time_ns()}.json',{'type':type(exc).__name__,'message':'Private operation failed; no automatic retry','detail_hash':digest(str(exc))})
    bundle=review_bundle(root,root.parent/'bundles'/f'{RUN_ID}-PRIVATE-recovery-{time.time_ns()}.zip',
        {'status':'interrupted_or_failed'},kind='gpqa_support_private',scientific_status='development_diagnostic_partial',
        include_markdown=True,max_metadata_bytes=256*1024**2)
    print('Local private recovery ZIP (do not publish):',canonical(bundle),flush=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('dataset','plan','private','complete','report','export','restore'))
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--persistent',type=Path,required=True)
    parser.add_argument('--dataset-dir',type=Path)
    parser.add_argument('--exposure-policy',type=Path,default=Path(__file__).resolve().parents[3]/'experiments/gpqa_exposure_policy.json')
    parser.add_argument('--prepared',type=Path)
    parser.add_argument('--source-bundle',type=Path)
    parser.add_argument('--initialization-root',type=Path)
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--download',action='store_true')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--stop-after',type=int)
    args=parser.parse_args(argv)
    root=data.outside_git(args.run_dir);persistent=data.outside_git(args.persistent)
    if root.name!=RUN_ID:parser.error('Use the fixed authorized GPQA run ID')
    if args.smoke and args.stage!='complete':parser.error('--smoke requires complete stage')
    if args.stop_after is not None and (args.stop_after<1 or args.stage not in ('private','complete')):parser.error('Invalid stop-after stage/count')
    if args.stage=='dataset':
        if args.dataset_dir is None or args.prepared is None:parser.error('dataset requires --dataset-dir and --prepared')
        import os
        data.acquire(args.dataset_dir,download=args.download,token=os.environ.get('HF_TOKEN'))
        print(canonical(data.prepare(args.dataset_dir,args.prepared,known=read_json(args.exposure_policy))));return
    if args.stage=='restore':
        if args.snapshot is None:parser.error('restore requires --snapshot')
        root.parent.mkdir(parents=True,exist_ok=True)
        print(canonical(storage_operation('gpqa-restore',args.snapshot,root,timeout_seconds=1800)));return
    root.mkdir(parents=True,exist_ok=True)
    with run_lock(root):
        if args.stage=='plan':
            if args.dataset_dir is None or args.prepared is None or args.source_bundle is None or args.initialization_root is None:parser.error('plan requires official dataset directory, prepared data, source review, real initialization root')
            data.prepare(args.dataset_dir,args.prepared,known=read_json(args.exposure_policy))
            prepared=read_json(data.outside_git(args.prepared));contract=source_contract(args.source_bundle)
            from ..training.receiver_study import initial_recipe
            initial_recipe(contract,args.initialization_root)
            plan=freeze_plan(prepared,contract,code_identity(Path(__file__).resolve().parents[3]))
            if (root/'plan.json').exists() and canonical(read_json(root/'plan.json'))!=canonical(plan):raise ValueError('GPQA plan changed; no overwrite')
            if not (root/'plan.json').exists():
                write_json(root/'plan.json',plan);write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
            if journals(root,plan)[2]:raise ValueError('Unresolved GPQA attempts; no automatic retry')
            Recovery(root,persistent).after()
            print(canonical({'status':'plan_frozen','items':32,'budget':BUDGET,'gpu_behavior':'unverified'}));return
        plan=load_plan(root)
        if args.stage in ('private','complete'):
            if not args.execute:parser.error('GPU inference requires --execute')
            if args.initialization_root is None or args.cache_dir is None:parser.error('inference requires initialization-root and cache-dir')
            if plan['source']!=code_identity(Path(__file__).resolve().parents[3]):raise ValueError('GPQA code changed; resume rejected')
            intents,calls,missing=journals(root,plan)
            if missing:raise ValueError('Unresolved GPQA attempts; no automatic retry')
            recovery=Recovery(root,persistent)
            if not read_json(root/'state.json')['recovery_safe']:recovery.after()
            started=time.monotonic()
            runtime,backend,dtypes=load_model(plan,args.initialization_root,args.cache_dir)
            write_json(root/'environment.json',{'packages':versions(),'identity':backend.identity,'dtypes':dtypes})
            try:collect(plan,root,backend,runtime,args.stage,smoke=args.smoke,recovery=recovery,stop_after=args.stop_after)
            except CallBoundaryStop:print('Paused at a committed call boundary; resume same plan.',flush=True);recovery.after()
            finally:
                write_json(root/f'resources-{time.time_ns()}.json',{'invocation_seconds':time.monotonic()-started,**backend.resource_usage()})
            backend.assert_unchanged()
        if args.stage=='report':
            result=report(root);print(canonical({k:result[k] for k in ('completed_tasks','missing_tasks','screen_flag')}));return
        print(canonical(export(root,persistent)))


if __name__=='__main__':
    try:main()
    except (Exception,KeyboardInterrupt) as exc:
        # Never print raw gated benchmark text or arbitrary backend exception strings.
        import sys
        safe_errors=('GPQA context overflow before dispatch; no prompt truncation or task replacement',
            'GPQA private context overflow; fixed selection must not change',
            'GPQA runtime mismatch before model loading','GPQA code changed; resume rejected',
            'Unresolved GPQA attempts; no automatic retry','Ambiguous GPQA attempt; no automatic regeneration or budget reset',
            'GPQA operation requires review',
            'Official GPQA source content/revision mismatch',
            'GPQA schema: final question/answers/domain missing or empty',
            'GPQA schema: unexpected high-level domain',
            'Official GPQA header mismatch; access/schema review required',
            'GPQA Diamond must contain exactly 198 official rows; stop preflight',
            'Duplicate stable GPQA IDs; explicit source review required',
            'GPQA options must be four distinguishable strings',
            'Duplicate group crosses domains; review required',
            'Prepared GPQA selection changed; no overwrite',
            'Unsafe GPQA snapshot; no rollback or invisible retry',
            'GPQA frozen selection contract changed')
        message=str(exc) if str(exc)==data.ACCESS or str(exc) in safe_errors else 'GPQA operation stopped; '+type(exc).__name__+'. Preserve private scratch artifacts for local audit; no automatic retry.'
        try:
            if '--run-dir' in sys.argv:
                recovery_root=data.outside_git(Path(sys.argv[sys.argv.index('--run-dir')+1]))
                if recovery_root.name==RUN_ID:save_failure(recovery_root,exc)
        except Exception:pass
        print(message,file=sys.stderr,flush=True)
        raise SystemExit(1) from None
