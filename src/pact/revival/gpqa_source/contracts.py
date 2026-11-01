"""Scientific identity excludes prospective evaluation and scheduler metadata."""
from ...util import digest, node_seed
from ..allocation_v3 import design as d, evidence as e
from .. import contracts as c


def training_contract(source,s0):
    if e.source_contract(source)['status']!='ready':raise ValueError('training_source_conflict')
    rows=[r for r in source['records'] if r['split'] in ('main_fit','allocation_probe')]
    ids={r['task']['task_id'] for r in rows}
    return {'s0':s0,'blocks':source['blocks'],'records':rows,'labels':{k:v for k,v in source['labels'].items() if k in ids},
        'train':d.TRAIN,'analysis':d.ANALYSIS,'policies':d.POLICIES,'continuation_seeds':d.SEEDS,
        'temporary_seed':17,'assay_rollout':29,'policy_rollout':31,'root_seed':20261027,
        'rng':{f:{str(seed):int(digest([20261027,'training',seed,f])[:8],16) for seed in (17,*d.SEEDS)} for f in d.FAMILIES},
        'shuffle':d.derangement(source['blocks']),
        'temporary_order':{f'{b}/{f}':d.ordered(block['fit'],'temporary',17,b,f) for b,block in enumerate(source['blocks']) for f in d.FAMILIES},
        'probe_seeds':{r['task']['task_id']:[node_seed(20261027,'29',r['task']['task_id'],'private',str(i),'') for i in range(3)] for r in rows if r['split']=='allocation_probe'}}


def allocation_inputs(contract):
    """Allowlist; reject prospective payload even if caller supplies a combined plan."""
    if any(r['split'] not in ('main_fit','allocation_probe') or r['family'] not in d.SOURCES for r in contract['records']):
        raise ValueError('prospective_data_embargo')
    if set(contract['labels'])!={r['task']['task_id'] for r in contract['records']}:raise ValueError('prospective_label_embargo')
    return contract


def context_check(messages,backend):
    rendered=backend.render_messages(messages)
    n=len(backend.tokenizer.encode(rendered,add_special_tokens=False))
    if n+512>8192:raise ValueError('context_incompatible_no_truncation')
    return {'input_tokens':n,'reserved_output_tokens':512,'static_only':True,'dynamic_runtime_check_required':True}
