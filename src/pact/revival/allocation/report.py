"""Task-cluster comparisons; no receiver-cell or seed-row pseudoreplication."""
from collections import Counter
import random
from ...util import digest, read_json, write_json
from . import design as d
from .runner import output, prospective
from .storage import safe


def intervals(values, replicates=10000):
    """values: source -> task -> paired seed-averaged difference."""
    if set(values) != set(d.SOURCES) or any(not v for v in values.values()):
        return {'estimate': None, '95': None, '97.5': None, 'reason': 'missing_source_support'}
    arrays = [list(values[s].values()) for s in d.SOURCES]
    mean = lambda a: sum(a)/len(a)
    rng = random.Random(20261027)
    draws = sorted(sum(mean([rng.choice(a) for _ in a]) for a in arrays)/2 for _ in range(replicates))
    def quantile(q):
        pos = (len(draws)-1)*q; lo = int(pos); hi = min(lo+1,len(draws)-1)
        return draws[lo]+(draws[hi]-draws[lo])*(pos-lo)
    return {'estimate': sum(map(mean,arrays))/2,
            '95': [quantile(.025),quantile(.975)], '97.5': [quantile(.0125),quantile(.9875)],
            'replicates': replicates, 'unit': 'task cluster, both seeds together',
            'descriptive_only': True}


def outcome(root, r, part, team, condition, gold):
    tid = r['task']['task_id']
    def get(logical):
        try:
            return output(root, logical)['packet']
        except FileNotFoundError:
            return None
    private = [get([part,team,tid,'private',s]) for s in range(3)]
    revised = [get([part,team,tid,condition,'revision',s]) for s in range(3)]
    final = get([part,team,tid,condition,'final'])
    correct = lambda v: v['status']=='ok' and v['answer']==gold
    initial = [correct(v) for v in private] if all(v is not None for v in private) else None
    rev = [correct(v) for v in revised] if all(v is not None for v in revised) else None
    return {'task':tid,'group':r['group_id'],'source':r['family'],'team':team,'condition':condition,
            'initial':initial,'revised':rev,'correct':correct(final) if final is not None else None,
            'initial_status':[v['status'] if v else 'missing' for v in private],
            'revision_status':[v['status'] if v else 'missing' for v in revised],
            'final_status':final['status'] if final else 'missing','binding':r['binding']}


def decompose(rows):
    observed = [r for r in rows if r['correct'] is not None and r['initial'] is not None and r['revised'] is not None]
    by = {f:[r for r in observed if r['source']==f] for f in d.SOURCES}
    n = len(observed)
    correct = sum(r['correct'] for r in observed)
    with_initial = sum(r['correct'] and any(r['initial']) for r in observed)
    without_initial = sum(r['correct'] and not any(r['initial']) for r in observed)
    if with_initial+without_initial != correct:
        raise ValueError('Outcome decomposition')
    return {'intended':len(rows),'observed':n,'missing':len(rows)-n,'correct':correct,
            'by_source':{f:{'observed':len(xs),'correct':sum(r['correct'] for r in xs)} for f,xs in by.items()},
            'equal_source_accuracy':sum(sum(r['correct'] for r in xs)/len(xs) for xs in by.values())/2 if all(by.values()) else None,
            'private_correct_by_family':{f:sum(r['initial'][r['binding'].index(f)] for r in observed) for f in d.FAMILIES},
            'initial_coverage':sum(any(r['initial']) for r in observed),
            'coverage_gain_over_best_family': (sum(any(r['initial']) for r in observed)-max(
                (sum(r['initial'][r['binding'].index(f)] for r in observed) for f in d.FAMILIES), default=0)),
            'hold_opportunities':sum(sum(r['initial']) for r in observed),
            'repair_opportunities':sum(3-sum(r['initial']) for r in observed),
            'revised_coverage':sum(any(r['revised']) for r in observed),
            'harmful_revision':sum(a and not b for r in observed for a,b in zip(r['initial'],r['revised'])),
            'newly_correct_revision':sum(not a and b for r in observed for a,b in zip(r['initial'],r['revised'])),
            'erasure':sum(any(r['initial']) and not any(r['revised']) for r in observed),
            'new_coverage':sum(not any(r['initial']) and any(r['revised']) for r in observed),
            'readout_loss':sum(any(r['revised']) and not r['correct'] for r in observed),
            'final_construction':sum(not any(r['revised']) and r['correct'] for r in observed),
            'correct_with_initial_coverage':with_initial,'correct_without_initial_coverage':without_initial,
            'format_counts':dict(Counter(r['final_status'] for r in rows)),
            'conditional_cohorts_are_on_policy':True}


def policy_report(root, plan):
    data = prospective(root,plan); lock = read_json(root/'policy-lock.json')
    all_rows = [outcome(root,r,'policy',team,cond,data['labels'][r['task']['task_id']])
                for r in data['records'] for team in lock['teams'] for cond in ('clean','exchange')]
    write_json(root/'policy_outcomes.private.json',all_rows)
    by = {(r['task'],r['team'],r['condition']):r for r in all_rows}
    comparisons = {}
    for cond in ('clean','exchange'):
        for other in ('uniform','source_family','private_bank','shuffled','S0'):
            values = {f:{} for f in d.SOURCES}; seeds = {s:{f:{} for f in d.SOURCES} for s in d.SEEDS}
            missing = 0
            for r in data['records']:
                tid = r['task']['task_id']; diffs = []
                for seed in d.SEEDS:
                    left = lock['aliases'][f'terminal_block/{seed}']
                    right = 'S0' if other=='S0' else lock['aliases'][f'{other}/{seed}']
                    a,b = by[tid,left,cond]['correct'],by[tid,right,cond]['correct']
                    if a is None or b is None:
                        break
                    diff = int(a)-int(b); diffs.append(diff); seeds[seed][r['family']][r['group_id']]=diff
                if len(diffs)==2:
                    values[r['family']][r['group_id']]=sum(diffs)/2
                else:
                    missing += 1
            comparisons[cond+'/terminal_block-minus-'+other] = {
                **intervals(values,plan['analysis']['bootstrap_replicates']),
                'paired_tasks':sum(map(len,values.values())),'missing_tasks':missing,
                'seed_specific':{str(s):intervals(v,plan['analysis']['bootstrap_replicates']) for s,v in seeds.items()},
                'primary':cond=='exchange' and other in ('uniform','source_family')}
    for name, value in comparisons.items():
        if name.startswith('clean/'):
            value['prespecified_clean_tolerance']=plan['analysis']['clean_tolerance']
            value['point_estimate_within_tolerance']=(value['estimate'] >= -plan['analysis']['clean_tolerance']) if value['estimate'] is not None else None
            value['utility_target_not_certified_bound']=True
    aggregate = {team+'/'+cond:decompose([r for r in all_rows if r['team']==team and r['condition']==cond])
                 for team in lock['teams'] for cond in ('clean','exchange')}
    accepted = {}
    for f in d.SOURCES:
        rs = [r for r in data['records'] if r['family']==f]
        statuses = [(root/'attacks/policy'/f'{digest(r["task"]["task_id"])}.json') for r in rs]
        accepted[f] = {'intended':len(rs),'attempted':sum(p.exists() for p in statuses),
                       'accepted':sum(read_json(p)['accepted'] for p in statuses if p.exists())}
    result = {'fixture':plan['fixture'],'scientific_status':'mock_only' if plan['fixture'] else 'development_static_allocation','comparisons':comparisons,'by_team':aggregate,'attacks':accepted,'aliases':lock['aliases'],
              'primary_policy':'terminal_block','unchanged_s0_reported_once':True,
              'no_best_seed_selection':True,'static_allocation_not_full_pact':True}
    write_json(root/'policy_results.json',result)
    return result


def report(root, plan):
    intents = [read_json(p) for p in (root/'attempts').glob('*.json')]
    from ...artifacts import ShardStore
    results = list(ShardStore(root/'events').records())
    counts = {part:{kind:sum(v['cost'].get(kind,0) for v in intents if v['identity']['part']==part)
                    for kind in ('generation','scores','updates','training_forwards')}
              for part in ('assay','policy')}
    generated = [r['value'] for r in results if r['intent']['identity']['kind']=='generation']
    out = {'version':d.VERSION,'scientific_status':'mock_only' if plan['fixture'] else 'development_static_allocation',
           'physical':counts,'unresolved':len(intents)-len(results),'recovery_safe':safe(root),
           'input_tokens':sum(v['call']['input_tokens'] for v in generated),
           'output_tokens':sum(v['call']['output_tokens'] for v in generated),
           'reserved_output_tokens':sum(v['generation'] for v in counts.values())*512,
           'format_status_counts':dict(Counter(v['packet']['status'] for v in generated)),
           'training_input_tokens_committed':sum(r['value']['input_tokens'] for r in results if r['intent']['identity']['kind']=='update'),
           'diagnostic_input_tokens_committed':sum(len(r['intent']['identity']['dependency']['target']['input_ids']) for r in results if r['intent']['identity']['kind']=='score'),
           'compute_units':None,'synthetic_forwards':0,'budgets':d.BUDGET,'full_pact_executed':False,
           'assay_cost_is_incremental_to_uniform':True,
           'historical_unknown_work':'preserved separately; not zeroed or recycled',
           'stages':sorted(p.stem for p in (root/'stages').glob('*.json'))}
    logical = [read_json(p)['logical'] for p in (root/'outputs').glob('*.json')]
    out['saved_logical_generation_outputs'] = {part:sum(x[0]==part for x in logical) for part in ('assay','policy')}
    if (root/'policy-lock.json').exists():
        lock=read_json(root/'policy-lock.json')
        by_team=Counter(x[1] for x in logical if x[0]=='policy')
        out['policy_alias_expanded_logical_outputs'] = by_team['attack']+by_team['S0']+sum(
            by_team[owner] for owner in lock['aliases'].values())
        out['unique_policy_executions'] = len(set(lock['aliases'].values()))
    write_json(root/'summary.json',out)
    if (root/'stages/score.json').exists():
        assay_report(root,plan)
    if (root/'policy-lock.json').exists():
        policy_report(root,plan)
    return out


def assay_report(root, plan):
    from .runner import rows
    records=rows(plan); result={}; private=[]
    for b, block in enumerate(plan['blocks']):
        ids=plan['probes'][block['family']]
        for family in d.FAMILIES:
            branch=f'block-{b}-{family}'
            for cond in ('clean','exchange'):
                pairs=[]
                for tid in ids:
                    gold=plan['training_source']['labels'][tid]
                    before=outcome(root,records[tid],'assay','S0',cond,gold)
                    after=outcome(root,records[tid],'assay',branch,cond,gold)
                    private.append({'before':before,'after':after})
                    if before['correct'] is not None and after['correct'] is not None:
                        pairs.append((before,after))
                result[branch+'/'+cond]={'source':block['family'],'intended':len(ids),
                    'paired_tasks':len(pairs),'missing':len(ids)-len(pairs),
                    'before':decompose([a for a,b in pairs]),'after':decompose([b for a,b in pairs]),
                    'paired_correctness_change':sum(int(b['correct'])-int(a['correct']) for a,b in pairs),
                    'temporary_update_surrogate_only':True}
    write_json(root/'assay_outcomes.private.json',private)
    write_json(root/'assay_results.json',result)
    return result
