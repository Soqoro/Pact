"""Reuse native training/replay; adapt only the child source/permission boundary."""
from pathlib import Path
from ...util import read_json, write_json, digest, file_hash
from ...studies.heterogeneity import immutable
from ..allocation_v3 import runner as native, models, design as d, storage
from .. import contracts as c
from . import guard, plan as planning


def smoke_rows(root, p, records, part):
    graph=read_json(root/'sealed/graph.private.json')
    if digest(graph)!=p['freeze']['graph_digest']:raise ValueError('graph_changed')
    ids=set(graph['smoke_manifest'][part])
    nodes=[n for n in graph['nodes'] if n['id'] in ids]
    if len(nodes)!=len(ids) or len(nodes)!={'assay':24,'policy':244}[part]:
        raise ValueError('smoke_graph_conflict')
    tasks={n['task_id'] for n in nodes}
    selected=[r for r in records if r['task']['task_id'] in tasks]
    sources=set(d.SOURCES) if part=='assay' else {'gpqa_main','logiqa'}
    if len(selected)!=2 or {r['family'] for r in selected}!=sources:
        raise ValueError('source_specific_smoke_required')
    return selected


def preflight(root, p, cache):
    """Explicit GPU/model-load opt-in, no generation or training forwards."""
    from ...environment import runtime_fingerprint
    from ...backends.native import metadata
    expected=read_json(Path(p['parent_path'])/'evidence/access.json')
    for f in 'QLMR':
        if runtime_fingerprint()!=expected[f]['runtime_fingerprint'] or metadata(f,cache)!=expected[f]:
            raise ValueError('native_runtime_or_metadata_changed')
    checked={}
    for f in 'QLMR':
        with models.opened(root,p,f,cache,None if f=='R' else 'S0') as (backend,activation):
            # No prospective question is inspected before policy lock. Dynamic
            # peer/readout prompts get the same 8192-token check in Wallet.
            for r in p['training_source']['records']:
                if backend.count_tokens(backend.render_messages(c.prompt(r['task'])))+512>8192:
                    raise ValueError('native_context_overflow_no_truncation')
            activation.check(activation.active)
            checked[f]=backend.identity
    value={'plan_hash':digest(p),'fixture':p['fixture'],'native_identities':checked,
        'gpu_runtime_checked':True,'effective_S0_loading_checked':True,'native_access_checked':True,
        'context_checks_enabled':True,'dynamic_prompts_checked_at_dispatch':True,
        'prospective_content_not_opened':True,'model_calls':0,'training_forwards':0,'optimizer_updates':0}
    immutable(root/'execution-preflight.json',value)
    return {'ready':True,'model_calls':0,'spending_authorized':False}


def collect(root,p,cache,persistent,smoke):
    if not smoke:read_json(root/'exports/assay-smoke.json')
    rows=[r for r in p['training_source']['records'] if r['split']=='allocation_probe']
    if smoke:rows=smoke_rows(root,p,rows,'assay')
    cap=24 if smoke else None
    native.attacks(root,p,rows,'assay',cache,persistent,cap)
    native.trajectory(root,p,rows,'S0',dict.fromkeys(d.FAMILIES,'S0'),'assay',cache,persistent,cap)
    immutable(root/'stages'/('assay-smoke.json' if smoke else 'collect.json'),{'complete':True})


def policy_freeze(root,p):
    # Native compiler preserves full schedule/optimizer/checkpoint alias keys.
    # Its numerical allocations are training-only; replace only its report's
    # old ARC evaluation labels, never the policy matrix or training weights.
    result=native.policy_freeze(root,p)
    summary=read_json(root/'allocation_summary.json')
    summary['evaluation_source_weights']=p['evaluation_source_weights']
    write_json(root/'allocation_summary.json',summary)
    immutable(root/'policy-freeze-receipt.json',{'sha256':file_hash(root/'policies.json')})
    return result


def evaluate(root,p,cache,persistent,smoke):
    read_json(root/'exports/policy-lock.json')
    if not smoke:read_json(root/'exports/evaluation-smoke.json')
    data=native.prospective(root,p);lock=read_json(root/'policy-lock.json')
    selected=smoke_rows(root,p,data['records'],'policy') if smoke else data['records']
    cap=244 if smoke else None
    verified={}
    for team,states in lock['teams'].items():
        actual={f:'S0' if v=='S0' else Path(v) for f,v in states.items()}
        for f,state in actual.items():
            if state!='S0' and models.checkpoint_values(state)[1]!=lock['adapter_hashes'][team][f]:
                raise ValueError('locked_checkpoint_changed')
        verified[team]=actual
    # Validate every locked team before acquiring any intervention; then freeze
    # all shared interventions before any team sees this stage's bank.
    native.attacks(root,p,selected,'policy',cache,persistent,cap)
    for team,actual in verified.items():
        native.trajectory(root,p,selected,team,actual,'policy',cache,persistent,cap)
    immutable(root/'stages'/('evaluation-smoke.json' if smoke else 'evaluate.json'),{'complete':True})


def execute(root, expected_hash, requested, approval, approval_sha, cache=None, persistent=None, resume=False):
    root=Path(root);p=planning.validate(root,expected_hash)
    guard.authorize(root,p,requested,approval,approval_sha,persistent)
    # Denied approvals never instantiate Wallet, load models or create events.
    guard.record(root,requested,approval_sha)
    stage=requested['stage']
    if stage=='preflight':
        result=preflight(root,p,cache)
        from .report import report
        report(root,p)
        return {'result':result,'bundles':storage.export(root,stage,persistent),'stop_for_review':True}
    storage.Wallet(root,p,persistent)  # complete provenance and unsafe-resume validation
    if stage in ('assay-smoke','collect'):result=collect(root,p,cache,persistent,stage=='assay-smoke')
    elif stage=='branch':result=native.branch(root,p,requested['block'],requested['family'],cache,persistent,resume)
    elif stage=='score':result=native.score(root,p,cache,persistent)
    elif stage=='policy-freeze':result=policy_freeze(root,p)
    elif stage=='continuation':result=native.continuation(root,p,requested['policy'],requested['seed'],requested['family'],cache,persistent,resume)
    elif stage=='policy-lock':
        result=native.lock_policies(root,p)
        immutable(root/'policy-lock-receipt.json',{'sha256':file_hash(root/'policy-lock.json')})
    elif stage in ('evaluation-smoke','evaluate'):result=evaluate(root,p,cache,persistent,stage=='evaluation-smoke')
    else:raise ValueError('unknown_stage')
    from .report import report
    report(root,p)
    return {'result':result,'bundles':storage.export(root,stage,persistent),'stop_for_review':True}
