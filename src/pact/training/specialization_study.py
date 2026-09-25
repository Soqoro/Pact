"""Explicit stages for one fixed-bank specialization ablation; defaults are offline."""
import argparse
import dataclasses as dc
import json
from pathlib import Path
from types import SimpleNamespace
import time

from ..artifacts import ShardStore,run_lock,sync_run
from ..environment import code_identity
from ..evaluation import score,aggregate,rate,paired_bootstrap
from ..protocol import Protocol
from ..schemas import task_from_dict,TaskLabel,AttackRecord
from ..util import canonical,digest,node_seed,read_json,write_json
from ..storage import persist_bundle,storage_operation
from ..studies.gpqa_metrics import support,boundary
from ..studies.gpqa_model import load as load_initial
from .assignment_contrast import ARMS,characterize,contrast,export_contrast
from .specialization_plan import RUN_ID,SETTINGS,budgets,plan_from_sources
from .specialization_collect import collect,replay,immutable,runtime,StudyJournal
from .specialization_train import examples_for,train_team,training_audit
from .receiver import inspect_journal,CallBoundaryStop
from .colab import review_bundle


def load_plan(root,plan_hash=None):
    plan=read_json(root/'plan.json');state=read_json(root/'state.json')
    if (digest(plan)!=state['plan_hash'] or plan_hash is not None and digest(plan)!=plan_hash
        or plan['variant']!='specialization_fixed_bank_v1' or plan['budget']!=budgets() or plan['settings']!=SETTINGS):
        raise ValueError('Frozen specialization plan mismatch')
    return plan


def stage_budgets(root):
    pairs=read_json(root/'candidate_support.json')['eligible_cells'] if (root/'candidate_support.json').exists() else 192
    return {'collection':budgets()['collect'],'replay':budgets(pairs)['replay'],
            **{f'evaluation/{arm}':budgets()['evaluate_per_arm'] for arm in ('frozen',*ARMS)}}


def validate_recovery(root,plan):
    for name,budget in stage_budgets(root).items():inspect_journal(root/name,budget)
    for p in (root/'score-intents').glob('*.json'):
        if ShardStore(root/'scores').read(p.stem) is None:raise ValueError('Unresolved score intent')
    for arm in ARMS:
        r=root/'training'/arm
        if (r/'run.json').exists():
            from .checkpoints import latest_checkpoint
            _,meta=latest_checkpoint(r/'checkpoints',read_json(r/'run.json')['identity'])
            if (r/'update_attempt.json').exists() and read_json(r/'update_attempt.json')['step']>meta['step']:
                raise ValueError('Unresolved optimizer attempt')


class Recovery:
    def __init__(self,root,persistent=None):self.root=root;self.persistent=persistent
    def mark(self,safe):
        state=read_json(self.root/'state.json')
        if state['recovery_safe']==safe:return
        state['recovery_safe']=safe;write_json(self.root/'state.json',state)
        if self.persistent:sync_run(self.root,self.persistent,timeout_seconds=120)
    def before(self):self.mark(False)
    def after(self):self.mark(True)


def backend_for(plan,initial,cache,root,arm='frozen'):
    _,backend,dtypes=load_initial(plan,initial,cache)
    backend.config=dc.replace(backend.config,identity=digest(plan),seed=plan['seed'],probe=runtime(plan).probe)
    if arm!='frozen':
        from .warmstart import _load_step,_weights_hash,adapter_parameters
        from .receiver_recovery import actor_view
        r=root/'training'/arm;status=read_json(r/'status.json');run=read_json(r/'run.json')
        if not status['complete'] or status['completed_steps']!=96:raise ValueError('Final capped arm required')
        if run['identity']['plan_hash']!=digest(plan) or run['identity']['arm']!=arm:raise ValueError('Changed arm checkpoint identity')
        step,_=_load_step(r/'checkpoints',run['identity'],backend.model)
        params=adapter_parameters(backend.model)
        if step!=96 or _weights_hash(params)!=status['final_weight_hash']:raise ValueError('Final weight identity mismatch')
        hashes=[_weights_hash(actor_view(params,i)) for i in range(3)]
        backend.identity={**backend.identity,'effective_actor_tensor_hashes':hashes,
            'snapshot':digest({'base':backend.base_identity['snapshot'],'actors':hashes,'variant':'specialization_fixed_bank_v1'})}
        backend.versions=[(n,p,p._version) for n,p in backend.model.named_parameters()]
        backend.assert_unchanged()
    return backend,dtypes


def offline_backend(plan,identity=None):
    return SimpleNamespace(identity=identity or plan['frozen_arm']['checkpoint'],
        tokenizer=SimpleNamespace(eos_token_id=plan['frozen_arm']['parameters']['final']['eos_token_id']),count_tokens=lambda text:len(text.split()))


def evaluate(plan,backend,root,arm,*,readonly=False,stop_after=None,before_new=lambda:None,after_row=lambda:None):
    if arm not in ('frozen',*ARMS):raise ValueError('Unknown arm')
    destination=root/'evaluation'/arm
    if not readonly:immutable(destination/'identity.json',backend.identity)
    journal=StudyJournal(backend,destination,budgets()['evaluate_per_arm'],plan,'development',readonly=readonly,stop_after=stop_after,before_new=before_new)
    protocol=Protocol(runtime(plan),journal);store=ShardStore(destination/'records');result=[]
    for entry in plan['selection']:
        if entry['partition']!='development':continue
        task=task_from_dict(plan['tasks'][entry['task_id']]);label=TaskLabel(task.task_id,plan['labels'][task.task_id]['answer_id'])
        for condition in plan['conditions']:
            key=digest([digest(plan),arm,task.task_id,condition]);saved=store.read(key)
            if readonly and saved is None:continue
            raw=dict(plan['attacks'][task.task_id][condition]);raw.pop('schema_version',None);attack=AttackRecord(**raw)
            count=saved['trajectory']['attack']['payload_tokens'] if readonly else backend.count_tokens(attack.payload)
            if count>256:raise ValueError('Early payload cap exceeded')
            attack=dc.replace(attack,payload_tokens=count)
            seed=node_seed(plan['seed'],task.task_id,condition,'evaluation')
            private=tuple(protocol.private_packet(task,i,attack,node_seed(seed,'private',i)) for i in range(3))
            vote=protocol.suffix(task,'vote',attack,private,seed,digest([key,'vote']))
            synth=protocol.suffix(task,'synthesis',attack,private,node_seed(seed,'independent-synthesis'),digest([key,'synthesis']))
            debate=protocol.suffix(task,'debate',attack,private,seed,digest([key,'debate']))
            c0=[p.parser_status=='ok' and p.answer_id==label.answer_id for p in private]
            row={'schema_version':1,'work_id':key,'task_id':task.task_id,'condition':condition,'family':task.family,'arm':arm,
                'c0':c0,'valid0':[p.parser_status=='ok' for p in private],'answers0':[p.answer_id for p in private],
                'c1':[p.parser_status=='ok' and p.answer_id==label.answer_id for p in debate.revised],
                'vote':vote.final.answer_id==label.answer_id,'synthesis':synth.final.answer_id==label.answer_id,'debate':debate.final.answer_id==label.answer_id,
                'evaluation':score(debate,label),'trajectory':dc.asdict(debate),'independent_synthesis':dc.asdict(synth)}
            if readonly:
                # Token-envelope lengths are derived with the real tokenizer on collection.
                # Reconstruct them from saved trajectories before exact comparison.
                for field in ('trajectory','independent_synthesis'):
                    row[field]['readout_low_trust_tokens']=saved[field]['readout_low_trust_tokens']
                row['evaluation']['readout_low_trust_tokens']=saved['trajectory']['readout_low_trust_tokens']
                if canonical(row)!=canonical(saved):raise ValueError('Evaluation reconstruction mismatch')
            else:store.put(key,row);after_row()
            result.append(row)
    if len(result)==64 and set(journal.results)!=journal.seen:raise ValueError('Unused or unplanned evaluation calls')
    return result


def accounting(root):
    result={};total_calls=total_tokens=0
    for name,budget in stage_budgets(root).items():
        intents=list((root/name/'call-intents').glob('*.json'))
        calls=ShardStore(root/name/'calls').records()
        reserved=sum(read_json(p)['max_tokens'] for p in intents)
        result[name]={'attempted_calls':len(intents),'committed_calls':len(calls),'unresolved':len(intents)-len(calls),
            'reserved_output_tokens':reserved,'input_tokens':sum(c['call']['input_tokens'] for c in calls),'output_tokens':sum(c['call']['output_tokens'] for c in calls)}
        total_calls+=len(intents);total_tokens+=reserved
    if total_calls>6336 or total_tokens>1363968:raise ValueError('Global study budget exceeded')
    return {'by_stage':result,'attempted_calls':total_calls,'reserved_output_tokens':total_tokens,
        'teacher_forced_scores':len(list((root/'score-intents').glob('*.json')))}


def report(root):
    plan=load_plan(root);systems={};allrows={};training={}
    if (root/'bank_manifest.json').exists():
        rows,records=replay(plan,offline_backend(plan),root,readonly=True)
        if digest(records)!=read_json(root/'bank_manifest.json')['bank_hash']:raise ValueError('Bank report integrity mismatch')
        if (root/'assignment_contrast.json').exists() and canonical(contrast(rows))!=canonical(read_json(root/'assignment_contrast.json')):raise ValueError('Assignment report integrity mismatch')
    for arm in ('frozen',*ARMS):
        path=root/'evaluation'/arm/'identity.json'
        rows=evaluate(plan,offline_backend(plan,read_json(path)),root,arm,readonly=True) if path.exists() else []
        allrows[arm]={(r['task_id'],r['condition']):r for r in rows};systems[arm]={}
        for condition in plan['conditions']:
            cohort=[r for r in rows if r['condition']==condition]
            systems[arm][condition]={'support':support(cohort,32),'communication':aggregate([r['evaluation'] for r in cohort]),
                'terminal':{k:rate(sum(r[k] for r in cohort),len(cohort)) for k in ('vote','synthesis','debate')},
                'N0_to_N1':[[sum(sum(r['c0'])==i and sum(r['c1'])==j for r in cohort) for j in range(4)] for i in range(4)],
                'unique_correct_coverage':[sum(r['c0'][i] and sum(r['c0'])==1 for r in cohort) for i in range(3)],
                'all_correct_degradation':rate(sum(all(r['c0']) and not all(r['c1']) for r in cohort),sum(all(r['c0']) for r in cohort))}
        p=root/'training'/arm/'status.json'
        if p.exists():training[arm]=read_json(p)
    comparisons={}
    for arm in ARMS:
        for control in ('frozen',*ARMS):
            if control==arm:continue
            common=allrows[arm].keys()&allrows[control].keys();item={}
            for outcome in ('debate','synthesis','vote','coverage','all_correct','mixed'):
                def value(r):
                    if outcome=='coverage':return any(r['c0'])
                    if outcome=='all_correct':return all(r['c0'])
                    if outcome=='mixed':return any(r['c0']) and any(v and not c for v,c in zip(r['valid0'],r['c0']))
                    return r[outcome]
                paired={}
                for key in sorted(common):paired.setdefault(key[0],[]).append((float(value(allrows[arm][key])),float(value(allrows[control][key]))))
                item[outcome]=paired_bootstrap(paired)
                item[outcome]['by_condition']={condition:paired_bootstrap({key[0]:[(float(value(allrows[arm][key])),float(value(allrows[control][key])))] for key in sorted(common) if key[1]==condition}) for condition in plan['conditions']}
                item[outcome]['per_task_changes']=[{'task_id':key[0],'condition':key[1],'arm':value(allrows[arm][key]),'control':value(allrows[control][key])} for key in sorted(common)]
                item[outcome]['note']='task-clustered clean/early; one training seed; degenerate intervals are not equivalence'
            comparisons[arm+' vs '+control]=item
    result=boundary({'variant':plan['variant'],'plan_hash':digest(plan),'synthetic_fixture':plan['synthetic_fixture'],
        'systems':systems,'paired':comparisons,'generation_accounting':accounting(root),'training_by_arm_and_actor':training,
        'training_executed':any(s.get('training_executed') for s in training.values()),
        'evaluation_executed':any(allrows.values()),'scientific_efficacy':'not_established','full_pact_ready':False,
        'assignment':read_json(root/'assignment_contrast.json') if (root/'assignment_contrast.json').exists() else None,
        'missing_evaluation_rows':{a:64-len(v) for a,v in allrows.items()},'no_automatic_followup':True})
    write_json(root/'specialization_results.json',result)
    write_json(root/'training_by_arm_and_actor.json',training)
    write_json(root/'resource_usage.json',result['generation_accounting'])
    (root/'evaluation_per_task.jsonl').write_text(''.join(canonical({k:v for k,v in r.items() if k not in ('trajectory','independent_synthesis')})+'\n' for arm in allrows.values() for r in arm.values()))
    return result


def export(root,persistent=None):
    try:
        result=report(root);outcome_status='review'
    except (ValueError,KeyError) as exc:
        plan=load_plan(root)
        result={'plan_hash':digest(plan),'synthetic_fixture':plan['synthetic_fixture'],'status':'partial_requires_review',
                'failure_type':type(exc).__name__,'failure_hash':digest(str(exc))}
        write_json(root/'partial_export_status.json',result);outcome_status='partial_requires_review'
    (root/'CODEX_HANDOFF.md').write_text('Specialization fixed-bank ablation; not full PACT. Review ZIP omits weights/optimizer tensors. Full snapshots required for resume. No automatic follow-up.\n')
    path=root.parent/'bundles'/f'{RUN_ID}-handoff-{time.time_ns()}.zip'
    bundle=review_bundle(root,path,{'status':outcome_status,'plan_hash':result['plan_hash']},kind='specialization_fixed_bank',scientific_status='synthetic_fixture' if result['synthetic_fixture'] else 'specialization_development',include_markdown=True,max_metadata_bytes=512*1024**2)
    print('Local specialization bundle:',canonical(bundle),flush=True)
    if persistent:
        bundle['persistent_snapshot']=str(sync_run(root,persistent,timeout_seconds=120))
        dest=persistent/'bundles'/path.name;persist_bundle(path,dest,bundle['sha256'],timeout_seconds=120)
        bundle['persistent_bundle']=str(dest)
    return bundle



def audit_bundle(bundle,sha):
    """Safe metadata-only round trip; no imported execution or tensor loading."""
    import tempfile
    import zipfile
    from .feasibility import read_review
    from ..util import file_hash
    content=read_review(Path(bundle),sha,max_members=40000,max_bytes=512*1024**2,allow_text=True)
    if content['HANDOFF.json']['kind']!='specialization_fixed_bank':raise ValueError('Wrong study bundle')
    if content['HANDOFF.json']['outcome']['status']=='partial_requires_review':
        return {'status':'partial_requires_review','artifact_checksums_verified':True,'scientific_results_verified':False}
    with tempfile.TemporaryDirectory(prefix='specialization-audit-') as tmp:
        root=Path(tmp)
        with zipfile.ZipFile(bundle) as archive:
            for name in content:
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.read(name))
                if '/shards/' in name:
                    if file_hash(path)!=content['HANDOFF.json']['inventory'][name]['sha256']:raise ValueError('Shard inventory mismatch')
                    path.with_suffix('.sha256').write_text(file_hash(path))
        rebuilt=report(root)
        if canonical(rebuilt)!=canonical(content['specialization_results.json']):raise ValueError('Returned report failed reconstruction')
        return rebuilt


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['audit','characterize','plan','collect','replay','assign','train','evaluate','report','export','restore'])
    parser.add_argument('--run-dir',type=Path,required=True);parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--source-bundle',type=Path);parser.add_argument('--sha256');parser.add_argument('--plan-hash')
    parser.add_argument('--initialization-root',type=Path);parser.add_argument('--cache-dir',type=Path,default=Path('/content/pact-scratch/cache'))
    parser.add_argument('--persistent',type=Path);parser.add_argument('--snapshot',type=Path)
    parser.add_argument('--arm',choices=['frozen',*ARMS]);parser.add_argument('--execute',action='store_true')
    parser.add_argument('--resume',action='store_true');parser.add_argument('--stop-after',type=int)
    args=parser.parse_args(argv);root=args.run_dir;repo=Path(__file__).resolve().parents[3]
    if args.stage=='audit':
        result=audit_bundle(args.source_bundle,args.sha256);write_json(root/'audited_specialization_results.json',result);print('Offline report reconstruction passed.');return
    if args.stage=='characterize':
        r=characterize(args.source_bundle,args.sha256,root);print(canonical({k:r[k] for k in ('status','distinct_tasks','D_credit_local')}));return
    if args.stage=='restore':
        print(canonical(storage_operation('specialization-restore',args.snapshot,root,timeout_seconds=1800)));return
    if args.stage=='plan':
        plan=plan_from_sources(args.data_dir,args.source_bundle,repo)
        with run_lock(root):
            immutable(root/'plan.json',plan)
            if not (root/'state.json').exists():write_json(root/'state.json',{'plan_hash':digest(plan),'recovery_safe':True})
            immutable(root/'source_and_exposure_manifest.json',plan['source_and_exposure_manifest'])
            immutable(root/'answer_score_definition.json',{'definition':plan['answer_score_definition'],'packet':plan['packet_score_definition']})
        if args.persistent:sync_run(root,args.persistent,timeout_seconds=120)
        print(canonical({'plan_hash':digest(plan),'budget':plan['budget'],'selection_counts':{'fit':32,'development':32},'model_calls':0}));return
    if not args.plan_hash:raise ValueError('Every study stage requires the frozen --plan-hash')
    plan=load_plan(root,args.plan_hash)
    if args.stage not in ('report','export') and plan['source']!=code_identity(repo):raise ValueError('Source changed; incompatible resume')
    if args.stop_after is not None and args.stop_after<1:raise ValueError('Positive pause bound required')
    with run_lock(root):
        recovery=Recovery(root,args.persistent)
        if args.stage in ('collect','replay','train','evaluate'):
            if not args.execute:raise ValueError('GPU stage requires explicit --execute; no automatic acquisition')
            if plan['synthetic_fixture']:raise ValueError('Synthetic plan cannot authorize pretrained execution')
            validate_recovery(root,plan)
            if args.stage in ('train','evaluate'):
                assignment=read_json(root/'assignment_contrast.json')
                if assignment['status']!='ready':raise ValueError(assignment['status'])
            if args.stage=='replay' and read_json(root/'candidate_support.json')['status']!='ready_for_replay':raise ValueError('insufficient_assignment_support')
            if args.stage=='train' and args.arm not in ARMS:raise ValueError('Choose a trained arm')
            if args.stage=='train' and (root/'training'/args.arm/'status.json').exists() and read_json(root/'training'/args.arm/'status.json').get('complete'):
                if read_json(root/'training'/args.arm/'run.json')['identity']['plan_hash']!=digest(plan):raise ValueError('Completed arm plan mismatch')
                print('Already complete:',args.arm);return
            if args.stage=='evaluate' and not args.arm:raise ValueError('Choose an evaluation arm')
            backend,dtypes=backend_for(plan,args.initialization_root,args.cache_dir,root,args.arm if args.stage=='evaluate' else 'frozen')
            immutable(root/('environment-'+(args.arm or args.stage)+'.json'),{'identity':backend.identity,'dtypes':dtypes})
            # Verify actual tokenizer payload lengths without changing the frozen bytes.
            for task_attacks in plan['attacks'].values():
                for attack in task_attacks.values():
                    if backend.count_tokens(attack['payload'])>256:raise ValueError('Frozen attack exceeds token cap')
            try:
                if args.stage=='collect':print(canonical(collect(plan,backend,root,stop_after=args.stop_after,before_new=recovery.before,after_row=recovery.after)))
                elif args.stage=='replay':replay(plan,backend,root,stop_after=args.stop_after,before_new=recovery.before,after_row=recovery.after)
                elif args.stage=='evaluate':evaluate(plan,backend,root,args.arm,stop_after=args.stop_after,before_new=recovery.before,after_row=recovery.after)
                else:
                    rows,records=replay(plan,offline_backend(plan),root,readonly=True)
                    if digest(records)!=read_json(root/'bank_manifest.json')['bank_hash'] or canonical(contrast(rows))!=canonical(assignment):raise ValueError('Frozen bank/assignment changed')
                    examples=examples_for(records,assignment,args.arm,backend.tokenizer)
                    identity={'plan_hash':digest(plan),'arm':args.arm,'bank_hash':digest(records),'assignment_hash':digest(assignment),
                        'model_snapshot':backend.base_identity['snapshot'],'initial_effective_hashes':backend.identity['effective_actor_tensor_hashes']}
                    immutable(root/'loss_reduction_and_weight_audit.json',{'by_arm':{a:training_audit(examples_for(records,assignment,a,backend.tokenizer),plan['seed']) for a in ARMS}})
                    train_team(backend.model,examples,plan,root/'training'/args.arm,identity,resume=args.resume,stop_after=args.stop_after,before_update=recovery.before,after_update=recovery.after)
            except CallBoundaryStop:print('Paused at a completed generation boundary; reuse committed calls.')
            validate_recovery(root,plan);recovery.after()
        elif args.stage=='assign':
            rows,records=replay(plan,offline_backend(plan),root,readonly=True);result=contrast(rows)
            if (root/'assignment_contrast.json').exists() and canonical(read_json(root/'assignment_contrast.json'))!=canonical(result):raise ValueError('Assignment changed')
            export_contrast(rows,result,root)
            (root/'replay_cell_records.jsonl').write_text(''.join(canonical(r)+'\n' for r in rows))
            print(canonical({'status':result['status'],'D_credit_local':result['D_credit_local']}))
        elif args.stage=='report':print(canonical({'missing':report(root)['missing_evaluation_rows']}))
        elif args.stage=='export':print(canonical(export(root,args.persistent)))


if __name__=='__main__':main()
