"""Every scientific stage is explicit, bounded and exports/stops."""
import argparse
from pathlib import Path
from ...util import read_json, write_json, digest, file_hash, canonical
from ...environment import code_identity
from ...artifacts import run_lock
from ...studies.heterogeneity import immutable
from . import design as d, evidence, runner, models, report, storage

REPO = Path(__file__).resolve().parents[4]
EXECUTE = {'checkpoint','preflight','assay-smoke','collect','branch','score','continuation',
           'policy-lock','evaluation-smoke','evaluate'}


def inspect(root, bundle, history_roots):
    parent = root/'parent'
    if not parent.exists():
        evidence.read_parent(bundle,parent)
    receipt = read_json(parent/'import-receipt.json')
    if receipt['sha256'] != evidence.PARENT_SHA:
        raise ValueError('Wrong parent')
    source = read_json(parent/'plan.json')['source']
    conflict = evidence.source_contract(source)
    conflict['old_stage2_conflicts'] = evidence.old_assay_conflicts([parent,*history_roots])
    if conflict['old_stage2_conflicts']:
        conflict['blockers'].append('older_stage2_execution_conflict')
        conflict['status']='blocked'
    conflict['history_review_scope']=[str(p) for p in history_roots]
    conflict['external_history_not_certified']=True
    write_json(root/'resolution.private.json',conflict)
    return conflict


def create_plan(root, fixture=False, data_dir=None, exposure=None, history_receipt=None):
    if (root/'plan.json').exists():
        raise ValueError('Never re-plan an existing child')
    if fixture:
        source = evidence.fixture_source()
        fresh = {'status':'ready','records':[r for r in source['records'] if r['split']=='prospective_development'],
                 'labels':{r['task']['task_id']:source['labels'][r['task']['task_id']] for r in source['records'] if r['split']=='prospective_development'}}
        s0 = dict.fromkeys(d.FAMILIES,'fixture_initialized')
        parent = root/'parent'
        parent.mkdir(parents=True,exist_ok=True)
    else:
        parent = root/'parent'
        resolution = read_json(root/'resolution.private.json')
        source = read_json(parent/'plan.json')['source']
        current = evidence.source_contract(source)
        blockers = list(current['blockers'])
        if resolution['old_stage2_conflicts']:
            blockers.append('older_stage2_execution_conflict')
        if not history_receipt:
            blockers.append('reviewed_unconsumed_probe_history_receipt_required')
        else:
            h = read_json(history_receipt)
            if (h.get('parent_sha256')!=evidence.PARENT_SHA or h.get('old_stage2_executed') is not False or
                h.get('probe_groups_consumed') is not False or h.get('reviewed') is not True):
                blockers.append('history_receipt_conflict')
        if blockers:
            return {'status':'blocked','blockers':blockers,'model_calls':0,
                    'actual':current,'new_plan_created':False}
        if not data_dir or not exposure:
            return {'status':'blocked','blockers':['official_source_and_reviewed_exposure_required'],'model_calls':0}
        from ...training.data import load_training_sources
        training, validation = load_training_sources(data_dir, download=False)
        fresh = evidence.select_fresh(source,training,validation,read_json(exposure))
        if fresh['status']!='ready':
            write_json(root/'source-shortfall.json',fresh)
            return fresh
        inventory = read_json(parent/'checkpoint_inventory.private.json')
        s0 = {f:inventory['uniform_joint_sft/'+f]['adapter_hash'] for f in d.FAMILIES}
        # Resolve executed optimizer settings; warmup=0 is the explicit new schedule.
        from .. import contracts as c
        if any(c.OPT[k]!=d.TRAIN[k] for k in ('lr','betas','eps','weight_decay','clip')):
            raise ValueError('Executed optimizer contract conflicts')
    if root.name != d.ASSAY and not fixture:
        raise ValueError('New reserved assay ID required')
    contract = evidence.source_contract(source)
    if contract['status']!='ready':
        raise ValueError('Fixture or actual source violates reviewed v2 design')
    selected = [r for r in source['records'] if r['split'] in ('main_fit','allocation_probe')]
    labels = {r['task']['task_id']:source['labels'][r['task']['task_id']] for r in selected}
    immutable(root/'sealed/prospective.private.json',fresh)
    parent_receipt = read_json(parent/'import-receipt.json') if not fixture else {'sha256':'fixture'}
    # Parent content map binds external checkpoint metadata and all imported inputs.
    p = {'version':d.VERSION,'run_id':d.ASSAY,'policy_run_id':d.POLICY,'fixture':fixture,
         'source_code':code_identity(REPO),'parent_path':str(parent.resolve()),
         'parent_sha256':parent_receipt['sha256'],'s0':s0,
         'history_review':read_json(history_receipt) if history_receipt and not fixture else None,
         'source_resolution':contract,
         'fresh_exposure_hash':fresh.get('exposure_hash'),
         'fresh_overlap_audit_hash':fresh.get('overlap_audit_hash'),
         'parent_files': parent_receipt.get('files',{}),
         'training_source':{'records':selected,'labels':labels},
         'blocks':source['blocks'],'probes':contract['probes'],'shuffle':d.derangement(source['blocks']),
         'prospective_hash':file_hash(root/'sealed/prospective.private.json'),
         'prospective_ids':[r['task']['task_id'] for r in fresh['records']],
         'budgets':d.BUDGET,'analysis':d.ANALYSIS,'train':d.TRAIN,
         'seeds':{'root':20261027,'temporary':17,'probe_rollout':29,'continuations':[113,227],'evaluation_rollout':31},
         'changes_from_old_stage2':['shared32_probes','one_rollout_seed','common_reader_private_scores',
                                   'explicit_extra_slots','five_two_seed_policies','fresh128','new_wallets'],
         'probe_role':'training-use metadata, never gradient targets',
         'evaluation_access':'sealed until full policy/checkpoint/analysis lock'}
    if not fixture and (p['source_code']['dirty'] or not p['source_code']['git_commit']):
        raise ValueError('Clean pinned scientific checkout required')
    immutable(root/'plan.json',p)
    return {'status':'planned','plan_hash':digest(p),'budgets':d.BUDGET,'fixture':fixture}


def guard(root,h,mock=False,allow_incomplete=False):
    p=read_json(root/'plan.json')
    if p['version']!=d.VERSION or digest(p)!=h or p['fixture']!=mock:
        raise ValueError('Exact plan hash and fixture mode required')
    if p['budgets']!=d.BUDGET or p['analysis']!=d.ANALYSIS or p['train']!=d.TRAIN:
        raise ValueError('Reviewed contract changed')
    if not mock and p['source_code']!=code_identity(REPO):
        raise ValueError('Pinned source changed; no implicit migration')
    if not mock:
        parent=Path(p['parent_path'])
        for name,hsh in p['parent_files'].items():
            if file_hash(parent/name)!=evidence.parent_evidence.sha(hsh):
                raise ValueError('Immutable imported parent changed')
    if (root/'policies.json').exists():
        frozen=read_json(root/'policy-freeze-receipt.json')
        if frozen['sha256']!=file_hash(root/'policies.json'):
            raise ValueError('Frozen policy matrices changed')
    storage.Wallet(root,p,allow_incomplete=allow_incomplete)
    return p


def checkpoint(root,p):
    if p['fixture']:
        result={'ready':True,'fixture':True,'s0':p['s0'],'model_calls':0}
    else:
        from ..stage1.weights import tensor_inventory
        entries={}
        for f in d.FAMILIES:
            values,inv=tensor_inventory(Path(p['parent_path']),'uniform_joint_sft/'+f)
            if inv['adapter_hash']!=p['s0'][f]:
                raise ValueError('S0 checkpoint changed')
            entries[f]=inv;del values
        result={'ready':True,'s0':entries,'model_calls':0,'synthetic_forwards':0}
    immutable(root/'checkpoint-receipt.json',result)
    return result


def preflight(root,p,cache):
    read_json(root/'checkpoint-receipt.json')
    if not p['fixture']:
        from ...backends.native import metadata
        from ...environment import runtime_fingerprint
        expected=read_json(Path(p['parent_path'])/'evidence/access.json')
        for f in 'QLMR':
            if metadata(f,cache)!=expected[f] or runtime_fingerprint()!=expected[f]['runtime_fingerprint']:
                raise ValueError('Pinned native runtime/tokenizer mismatch')
    immutable(root/'preflight.json',{'ready':True,'fixture':p['fixture'],'model_calls':0,'synthetic_forwards':0})
    return {'ready':True,'weights_verified_on_load':False,'model_calls':0}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['inspect','synthesis','plan','checkpoint','preflight','assay-smoke',
        'collect','branch','score','policy-freeze','continuation','policy-lock','evaluation-smoke',
        'evaluate','report','export','restore','audit'])
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--parent-bundle',type=Path)
    parser.add_argument('--history-root',action='append',type=Path,default=[])
    parser.add_argument('--history-receipt',type=Path)
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--exposure',type=Path)
    parser.add_argument('--persistent',type=Path)
    parser.add_argument('--cache-dir',type=Path)
    parser.add_argument('--plan-hash')
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--mock',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--block',type=int)
    parser.add_argument('--family',choices=d.FAMILIES)
    parser.add_argument('--policy',choices=d.POLICIES)
    parser.add_argument('--seed',type=int,choices=d.SEEDS)
    a=parser.parse_args(argv);root=a.run_dir
    if a.stage in EXECUTE and not a.execute:
        print(canonical({'status':'offline_plan_only','stage':a.stage,'budgets':d.BUDGET,'model_calls':0}))
        return 0
    from ...studies.forensics import private_root, outside_git
    if not a.mock:
        outside_git(root)
        if a.persistent is not None: outside_git(a.persistent)
    if any(x.is_symlink() for x in (root,*root.parents)):
        raise ValueError('Symlink private destination')
    if a.stage=='restore':
        print(canonical(storage.restore(a.persistent,root)));return 0
    private_root(root,a.mock)
    with run_lock(root):
        if a.stage=='inspect':
            out=inspect(root,a.parent_bundle,a.history_root)
            out={k:v for k,v in out.items() if k!='probes'}
        elif a.stage=='synthesis':
            out=evidence.synthesize(root/'parent',root/'mechanism_synthesis.json')
            out={'status':'retrospective_synthesis_complete','model_calls':0}
        elif a.stage=='plan':
            out=create_plan(root,a.mock,a.data_dir,a.exposure,a.history_receipt)
        elif a.stage=='export' and not (root/'plan.json').exists():
            out=storage.export(root,'review-only',a.persistent)
        else:
            p=guard(root,a.plan_hash,a.mock,a.stage in ('report','export','audit'))
            if a.stage in EXECUTE and a.stage not in ('checkpoint','preflight'):
                read_json(root/'preflight.json')
            if a.stage=='checkpoint':out=checkpoint(root,p)
            elif a.stage=='preflight':out=preflight(root,p,a.cache_dir)
            elif a.stage in ('assay-smoke','collect'):
                runner.collect(root,p,a.cache_dir,a.persistent,a.stage=='assay-smoke');out={'complete':True}
            elif a.stage=='branch':
                out=runner.branch(root,p,a.block,a.family,a.cache_dir,a.persistent,a.resume)
            elif a.stage=='score':
                runner.score(root,p,a.cache_dir,a.persistent);out={'complete':True}
            elif a.stage=='policy-freeze':
                out=runner.policy_freeze(root,p)
                immutable(root/'policy-freeze-receipt.json',{'sha256':file_hash(root/'policies.json')})
            elif a.stage=='continuation':
                if a.policy is None or a.seed is None or a.family is None:
                    raise ValueError('Explicit policy/seed/family required')
                out=runner.continuation(root,p,a.policy,a.seed,a.family,a.cache_dir,a.persistent,a.resume)
            elif a.stage=='policy-lock':out=runner.lock_policies(root,p)
            elif a.stage in ('evaluation-smoke','evaluate'):
                runner.evaluate(root,p,a.cache_dir,a.persistent,a.stage=='evaluation-smoke');out={'complete':True}
            elif a.stage in ('report','audit'):
                out=report.report(root,p)
            elif a.stage=='export':
                report.report(root,p);out=storage.export(root,'manual',a.persistent)
            if a.stage not in ('report','export','audit'):
                report.report(root,p)
                out={'result':out,'bundles':storage.export(root,a.stage,a.persistent)}
        if a.stage in ('inspect','synthesis','plan'):
            out={'result':out,'bundles':storage.export(root,a.stage,a.persistent)}
        print(canonical(out))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
