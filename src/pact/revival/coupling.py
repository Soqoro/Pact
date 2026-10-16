"""Finite coupling orchestration; real execution needs a separately reviewed MethodSpec."""
from copy import deepcopy
from ..util import digest
MODES=('uniform','local','terminal_static','terminal_refreshed','shuffled','split')


def run(spec,team,collect,probe,assign,train,evaluate,*,fixture=False):
    required={'rounds','mode','cohorts','family_checkpoints','loss_weights','update_budget','query_budget','selection_rule','assignment_origin','refresh_policy'}
    if not required<=set(spec) or spec['mode'] not in MODES or spec['rounds']<2:raise ValueError('Finite complete MethodSpec required')
    if not fixture:raise ValueError('No real coupled execution plan authorized; supply a separately implemented reviewed preset')
    if spec['update_budget']<=0 or spec['query_budget']<=0:raise ValueError('Finite budgets required')
    original=deepcopy(team);history=[];allocation=None;used_updates=0;used_queries=0
    for r in range(spec['rounds']):
        snapshot=deepcopy(team);bank,queries=collect(deepcopy(snapshot),r);used_queries+=queries
        if allocation is None or spec['refresh_policy']=='refreshed' and spec['mode']!='terminal_static':
            scores,queries,updates=probe(deepcopy(snapshot),deepcopy(bank),r);used_queries+=queries;used_updates+=updates
            allocation=assign(deepcopy(scores),spec['mode'])
        if used_queries>spec['query_budget'] or used_updates>spec['update_budget']:raise ValueError('Coupling assay budget')
        for phase in (('specialization','receiver') if spec['mode']=='split' else ('joint',)):
            team,updates=train(deepcopy(team),deepcopy(bank),deepcopy(allocation),phase,spec['loss_weights']);used_updates+=updates
            if used_updates>spec['update_budget']:raise ValueError('Coupling update budget')
        history.append({'round':r,'before':digest(snapshot),'after':digest(team),'allocation':deepcopy(allocation),'queries':used_queries,'updates':used_updates})
    return {'initial':original,'team':team,'rounds':history,'evaluation':evaluate(deepcopy(team)),'mock_only':True}


def allocate(mode,terminal,local,sources):
    """Explicit controls on unscaled frozen scores; no per-agent normalization."""
    from ..training.assignment import solve_assignment
    if mode not in MODES or len(terminal)!=len(local) or len(sources)!=len(local):raise ValueError('Allocation contract')
    if mode=='uniform':return [[1/3]*3 for _ in terminal]
    values=local if mode=='local' else terminal
    costs=[[-v if v is not None else None for v in row] for row in values]
    weights=solve_assignment(costs,tau=.2,balance=.1)['weights']
    weights=[row if sum(row)>0 else [1/3]*3 for row in weights]
    if mode=='shuffled':
        original=deepcopy(weights)
        for family in sorted(set(sources)):
            ix=[i for i,x in enumerate(sources) if x==family]
            order=sorted(ix,key=lambda i:digest([20261016,'coupling-shuffle',i]))
            for dest,src in zip(ix,order):weights[dest]=original[src]
    return weights
