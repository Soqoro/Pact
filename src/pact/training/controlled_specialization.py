"""Explicit controlled-private fixed-bank stages; no automatic GPU execution."""
import argparse
from pathlib import Path
import time

from ..artifacts import ShardStore, run_lock, sync_run
from ..environment import code_identity
from ..storage import storage_operation, persist_bundle
from ..util import canonical, digest, read_json, write_json
from .controlled_private_plan import (SOURCE, ESTIMATOR, VARIANT, RUN_ID, ARMS, budgets,
    plan_from_bundle, unpack_review, characterize_parent, build_plan)
from .controlled_private import (BaseGenerator, acquire, verified_pairs, build_bank, replay,
    score_bank, write_assignments, examples_for)
from .specialization_collect import immutable
from .specialization_study import (backend_for, offline_backend, evaluate, report as development_report, Recovery)
from .specialization_train import train_team, training_audit
from .receiver import inspect_journal, CallBoundaryStop
from .colab import review_bundle


def load_plan(root, expected=None):
    plan=read_json(root/'plan.json')
    if (plan.get('variant')!=VARIANT or plan.get('source_variant')!=SOURCE or plan.get('estimator')!=ESTIMATOR
        or plan['budget']!=budgets() or plan['arms']!=list(ARMS) or plan['run_id']!=RUN_ID
        or digest(plan)!=read_json(root/'state.json')['plan_hash'] or expected is not None and digest(plan)!=expected):
        raise ValueError('Controlled plan identity mismatch')
    receipt=read_json(root/'parent_import_receipt.json')
    if receipt['anchor_hashes']!=[digest(a) for a in plan['anchors']] or receipt['plan_hash']!=plan['parent']['plan_hash']:
        raise ValueError('Parent anchors or receipt changed')
    return plan


def stage_budgets():
    b=budgets()
    return {**{k:b[k] for k in ('acquire','primary','order','calibration')},
            **{'evaluation/'+a:b['evaluate_per_arm'] for a in ('frozen',*ARMS)}}


def validate_recovery(root, plan):
    for name,budget in stage_budgets().items(): inspect_journal(root/name,budget)
    intents=[read_json(p) for p in (root/'score-intents').glob('*.json')]
    for kind in ('answer','packet'):
        if sum(s['kind']==kind for s in intents)>192: raise ValueError('Score budget exceeded')
    for s in intents:
        if s['kind'] not in ('answer','packet') or ShardStore(root/'scores').read(s['work_id']) is None: raise ValueError('Unresolved/unknown scoring attempt')
    for arm in ARMS:
        r=root/'training'/arm
        if (r/'run.json').exists():
            from .checkpoints import latest_checkpoint
            identity=read_json(r/'run.json')['identity']
            if identity['plan_hash']!=digest(plan) or identity['arm']!=arm: raise ValueError('Training identity mismatch')
            _,meta=latest_checkpoint(r/'checkpoints',identity)
            if meta['step']>96 or ((r/'update_attempt.json').exists() and read_json(r/'update_attempt.json')['step']>meta['step']):
                raise ValueError('Unresolved optimizer attempt or update cap exceeded')


def accounting(root):
    by_stage={};total=reserved=0
    for name,b in stage_budgets().items():
        intents=[read_json(p) for p in (root/name/'call-intents').glob('*.json')]
        calls=ShardStore(root/name/'calls').records();tokens=sum(i['max_tokens'] for i in intents)
        if len(intents)>b['generation_calls_upper_bound'] or tokens>b['generated_tokens_upper_bound']:raise ValueError('Stage budget exceeded')
        by_stage[name]={'attempted_calls':len(intents),'committed_calls':len(calls),'unresolved':len(intents)-len(calls),
            'reserved_output_tokens':tokens,'input_tokens':sum(c['call']['input_tokens'] for c in calls),
            'output_tokens':sum(c['call']['output_tokens'] for c in calls),
            'generation_seconds':sum(c['call']['elapsed_seconds'] for c in calls)}
        logical = None
        if name in ('primary','order','calibration'):
            logical = 16*len(ShardStore(root/(name+'-cells')).records())
        elif name.startswith('evaluation/'):
            logical = 8*len(ShardStore(root/name/'records').records())
        by_stage[name]['completed_logical_call_references'] = logical
        by_stage[name]['exact_request_reuses_in_completed_records'] = max(0,logical-len(calls)) if logical is not None else 0
        total+=len(intents);reserved+=tokens
    if total>6096 or reserved>1274112:raise ValueError('Controlled global budget exceeded')
    return {'by_stage':by_stage,'attempted_calls':total,'reserved_output_tokens':reserved,
            'teacher_forced_scores':len(list((root/'score-intents').glob('*.json'))),
            'frozen_score_seconds':sum(s['score']['elapsed_seconds'] for s in ShardStore(root/'scores').records()),
            'timer_note':'Generation and scoring timers are separate; not billed GPU-hours.',
            'imported_parent_calls':1216,'parent_new_calls':0,'compute_units':None}


def review_contract(root, plan, review):
    files=('assignment_contrast.json','pair_quality_and_review.json','order_sensitivity.json','seed_assignment_sensitivity.json')
    wanted={f:digest(read_json(root/f)) for f in files}
    if (review.get('plan_hash')!=digest(plan) or review.get('artifact_hashes')!=wanted or
        review.get('decision')!='approve_training' or review.get('systematic_packet_defect') is not False or
        not review.get('reviewer') or not review.get('notes') or review.get('reviewed_task_ids')!=plan['review_task_ids']):
        raise ValueError('Explicit packet/seed/order review required; systematic defects stop training')
    if read_json(root/'assignment_contrast.json')['status']!='ready_for_user_review':raise ValueError('Pretraining gate failed')
    return review


def report(root):
    plan=load_plan(root)
    if (root/'controlled_pair_manifest.json').exists():
        verified_pairs(plan,root)
        build_bank(plan,root)
    if (root/'replay_complete.json').exists():
        cells=replay(plan,offline_backend(plan),root,readonly=True)
        if read_json(root/'replay_complete.json')['cells_hash']!=digest(cells):raise ValueError('Replay completion changed')
        if (root/'bank_manifest.json').exists():
            rows,records=score_bank(plan,offline_backend(plan),root,cells,readonly=True)
            write_assignments(root,rows,records,cells)
    result=development_report(root,plan=plan,arms=ARMS,accounting_fn=accounting,verify_bank=False,output_name='development_results.json')
    result.update(source_variant=SOURCE,estimator=ESTIMATOR,parent=plan['parent'],
        candidate_support=read_json(root/'controlled_support.json') if (root/'controlled_support.json').exists() else None,
        rationale_review_status='not_reviewed',controlled_effect_is_not_on_policy_credit=True,
        pretraining_review=read_json(root/'training_review.json') if (root/'training_review.json').exists() else None)
    if result['pretraining_review']: result['rationale_review_status']='human sample inspection recorded; not verified reasoning'
    write_json(root/'development_results.json',result)
    write_json(root/'training_arms.json',result['training_by_arm_and_actor'])
    return result


def export(root,persistent=None):
    try:
        result=report(root);outcome_status='review'
    except (ValueError,KeyError,FileNotFoundError,CallBoundaryStop) as exc:
        plan=load_plan(root);outcome_status='partial_requires_review'
        result={'plan_hash':digest(plan),'synthetic_fixture':plan['synthetic_fixture']}
        write_json(root/'partial_export_status.json',{'status':outcome_status,'error_type':type(exc).__name__,
                   'error_hash':digest(str(exc)),'scientific_results_verified':False})
    (root/'CODEX_HANDOFF.md').write_text('Controlled private packet insertion / synthetic-target specialization, not full PACT. Parent remains stopped. No automatic follow-up. Review ZIP is metadata only; tensors remain in full snapshots.\n')
    bundle=review_bundle(root,root.parent/'bundles'/f'{RUN_ID}-handoff-{time.time_ns()}.zip',
        {'plan_hash':result['plan_hash'],'status':outcome_status},kind=VARIANT,include_markdown=True,
        scientific_status='synthetic_fixture' if result['synthetic_fixture'] else 'controlled_training_development',max_metadata_bytes=512*1024**2)
    print('Local controlled specialization ZIP:',canonical(bundle),flush=True)
    if persistent:
        bundle['persistent_snapshot']=str(sync_run(root,persistent,timeout_seconds=120))
        dest=persistent/'bundles'/Path(bundle['path']).name
        persist_bundle(Path(bundle['path']),dest,bundle['sha256'],timeout_seconds=120)
        bundle['persistent_bundle']=str(dest)
    return bundle


def audit(bundle,sha):
    import tempfile
    with tempfile.TemporaryDirectory(prefix='controlled-audit-') as tmp:
        root=Path(tmp);content=unpack_review(bundle,sha,root)
        if content['HANDOFF.json']['kind']!=VARIANT:raise ValueError('Wrong child bundle kind')
        if content['HANDOFF.json']['outcome']['status']=='partial_requires_review':
            return {'status':'partial_requires_review','artifact_checksums_verified':True,'scientific_results_verified':False}
        plan=load_plan(root)
        parent,anchors,calibration,missing=characterize_parent(root/'parent_metadata',fixture=plan['synthetic_fixture'])
        rebuilt_plan=build_plan(parent,anchors,calibration,plan['development_exposure_review'],plan['source'],parent_sha=plan['parent']['bundle_sha256'])
        if canonical(rebuilt_plan)!=canonical(plan) or canonical(missing)!=canonical(read_json(root/'natural_candidate_missingness.json')):
            raise ValueError('Child import/selection changed')
        validate_recovery(root,plan)
        result=report(root)
        if canonical(content['development_results.json'])!=canonical(result):raise ValueError('Child report reconstruction failed')
        return result


def record_environment(root, stage, arm, identity, dtypes):
    # Training records its initialization; evaluation records its final trained
    # checkpoint. They must not contend for the same immutable arm receipt.
    path=root/f'environment-{stage}-{arm or "initial"}.json'
    immutable(path,{'identity':identity,'dtypes':dtypes})
    return path


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=('plan','acquire','build-bank','replay','score-assign','train','evaluate','report','export','restore','audit'))
    parser.add_argument('--run-dir',type=Path,required=True)
    for name in ('parent-bundle','exposure-review','initialization-root','cache-dir','persistent','snapshot','review','source-bundle'):
        parser.add_argument('--'+name,type=Path)
    parser.add_argument('--sha256');parser.add_argument('--plan-hash');parser.add_argument('--arm',choices=('frozen',*ARMS))
    parser.add_argument('--execute',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--stop-after',type=int)
    args=parser.parse_args(argv);root=args.run_dir;repo=Path(__file__).resolve().parents[3]
    if args.stage=='audit':
        result=audit(args.source_bundle,args.sha256);write_json(root/'audited_controlled_results.json',result);print('Controlled audit passed.');return
    if args.stage=='restore':
        root.parent.mkdir(parents=True,exist_ok=True)
        print(canonical(storage_operation('controlled-specialization-restore',args.snapshot,root,timeout_seconds=1800)));return
    with run_lock(root):
        if args.stage=='plan':
            if args.parent_bundle is None or args.exposure_review is None:raise ValueError('Parent ZIP and later-development-use review required')
            plan=plan_from_bundle(args.parent_bundle,root,read_json(args.exposure_review),repo)
            immutable(root/'answer_score_definition.json',{'answer':plan['answer_score_definition'],'packet':plan['packet_score_definition'],
                      'transform':'eligible-cell global population standardization; zero std scale1; frozen across sensitivities'})
            if args.persistent:sync_run(root,args.persistent,timeout_seconds=120)
            print(canonical({'plan_hash':digest(plan),'budget':plan['budget'],'model_calls':0}));return
        if not args.plan_hash:raise ValueError('Frozen plan hash required')
        plan=load_plan(root,args.plan_hash)
        if args.stage not in ('report','export') and code_identity(repo)!=plan['source']:raise ValueError('Source changed; incompatible resume')
        if args.stop_after is not None and args.stop_after<1:raise ValueError('Positive pause bound required')
        if args.stage=='build-bank':
            print(canonical(build_bank(plan,root)))
            if args.persistent:sync_run(root,args.persistent,timeout_seconds=120)
            return
        if args.stage=='report':print(canonical(report(root)));return
        if args.stage=='export':print(canonical(export(root,args.persistent)));return
        if not args.execute or plan['synthetic_fixture']:raise ValueError('Explicit real GPU stage required; fixtures cannot authorize it')
        if args.review and read_json(args.review).get('systematic_packet_defect') is True:
            immutable(root/'packet_defect_review.json',read_json(args.review))
            raise ValueError('Systematic packet defect: stop; a revised generator requires a new source version')
        if (root/'packet_defect_review.json').exists():raise ValueError('Recorded systematic packet defect; study stopped')
        validate_recovery(root,plan)
        if args.stage in ('replay','score-assign') and build_bank(plan,root)['status']!='ready_for_replay':raise ValueError('insufficient_controlled_support')
        if args.stage in ('train','evaluate'):
            if args.arm is None or args.stage=='train' and args.arm not in ARMS:raise ValueError('Choose an explicit arm')
            review=read_json(args.review) if args.review else read_json(root/'training_review.json') if (root/'training_review.json').exists() else {}
            review_contract(root,plan,review);immutable(root/'training_review.json',review)
            if args.stage=='train' and (root/'training'/args.arm/'status.json').exists() and read_json(root/'training'/args.arm/'status.json').get('complete'):
                print('Already complete:',args.arm);return
        backend,dtypes=backend_for(plan,args.initialization_root,args.cache_dir or root.parent/'cache',root,args.arm if args.stage=='evaluate' else 'frozen')
        record_environment(root,args.stage,args.arm,backend.identity,dtypes)
        recovery=Recovery(root,args.persistent)
        try:
            if args.stage=='acquire':
                acquire(plan,BaseGenerator(backend),root,stop_after=args.stop_after,before_new=recovery.before,after_task=recovery.after)
                print(canonical(build_bank(plan,root)))
            elif args.stage=='replay':
                replay(plan,backend,root,stop_after=args.stop_after,before_new=recovery.before,after_cell=recovery.after)
            elif args.stage in ('score-assign','train'):
                if not (root/'replay_complete.json').exists():raise ValueError('Complete primary/control/calibration replay required')
                cells=replay(plan,offline_backend(plan),root,readonly=True)
                rows,records=score_bank(plan,backend if args.stage=='score-assign' else offline_backend(plan),root,cells,
                    readonly=args.stage=='train',before_new=recovery.before,after_row=recovery.after)
                assignments=write_assignments(root,rows,records,cells)
                if args.stage=='score-assign':
                    print(canonical({'status':assignments['status'],'practical_screen':assignments['practical_screen'],'next':'stop for user review; no automatic training'}))
                else:
                    examples=examples_for(records,assignments,args.arm,backend.tokenizer)
                    exposures={a:training_audit(examples_for(records,assignments,a,backend.tokenizer),plan['seed']) for a in ARMS}
                    immutable(root/'loss_weight_audit.json',exposures)
                    print(canonical({'arm':args.arm,'planned_exposure':exposures[args.arm]}),flush=True)
                    identity={'plan_hash':digest(plan),'arm':args.arm,'source_variant':SOURCE,'estimator':ESTIMATOR,
                              'bank_hash':digest(records),'assignment_hash':digest(assignments),'review_hash':digest(read_json(root/'training_review.json')),
                              'initial_effective_hashes':backend.identity['effective_actor_tensor_hashes']}
                    trained=train_team(backend.model,examples,plan,root/'training'/args.arm,identity,resume=args.resume,
                               stop_after=args.stop_after,before_update=recovery.before,after_update=recovery.after)
                    print(canonical({k:trained[k] for k in ('complete','completed_steps','executed_training_tokens')}),flush=True)
            elif args.stage=='evaluate':
                evaluate(plan,backend,root,args.arm,arms=ARMS,stop_after=args.stop_after,before_new=recovery.before,after_row=recovery.after)
        except CallBoundaryStop:print('Paused at committed generation boundary; resume reuses recorded requests.')
        validate_recovery(root,plan);recovery.after()


if __name__=='__main__':main()
