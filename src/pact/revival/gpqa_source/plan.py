"""CPU candidate seal; no execution approval, new wallet, or model dispatch."""
from pathlib import Path
from ...util import read_json,write_json,digest,file_hash
from ...studies.heterogeneity import immutable
from ..allocation_v3 import design as d
from . import review,graph,contracts,sources


def seal(review_root,destination,review_hash):
    """Existing explicit hash-bound review/seal pattern; prospective data separate.

    A seal freezes proposed inputs, not a scientific spending wallet. It cannot be
    passed to the old v3 CLI: that child remains blocked and version-incompatible.
    """
    root=Path(review_root);summary=review.validate(root)
    method=read_json(root/'method.private.json')
    if digest(method)!=review_hash:raise ValueError('review_hash_conflict')
    if not summary['candidate_exists']:raise ValueError('real_candidate_missing')
    if not summary['fixture'] and any(b!='relevant_external_consumption_unresolved' for b in summary['blockers']):
        raise ValueError('candidate_prerequisites_unresolved')
    candidate=read_json(root/'candidate.private.json');training=read_json(root/'training.private.json')
    contracts.allocation_inputs(training)
    destination=Path(destination)
    if not summary['fixture']:sources.private_path(destination)
    if destination.exists():raise ValueError('child_plan_collision')
    destination.mkdir(parents=True,mode=0o700)
    immutable(destination/'sealed/prospective.private.json',candidate)
    immutable(destination/'training.private.json',training)
    p={'version':graph.VERSION,'run_id':graph.ASSAY,'policy_run_id':graph.POLICY,
       'fixture':summary['fixture'],'status':'PROPOSED_SEALED','method_hash':review_hash,
       'source_review_manifest_hash':file_hash(root/'manifest.json'),
       'training_dependency_hash':digest(training),'s0':training['s0'],
       'blocks':training['blocks'],'shuffle':training['shuffle'],
       'seeds':{'root':20261027,'temporary_training':17,'probe_rollout':29,'continuation':list(d.SEEDS),'evaluation_rollout':31},
       'budgets':d.BUDGET,'analysis':d.ANALYSIS,'train':d.TRAIN,
       'prospective_hash':file_hash(destination/'sealed/prospective.private.json'),
       'graph_hash':file_hash(root/'graph.private.json'),
       'execution_enabled':False,'wallet_created':False,'remaining_owned_budget':None,
       'candidate_frozen':True,'execution_authorized':False}
    immutable(destination/'plan.json',p)
    return {'status':p['status'],'plan_hash':digest(p),'candidate_frozen':True,
            'fixture':p['fixture'],'execution_authorized':False,'wallet_created':False,'model_calls':0}
