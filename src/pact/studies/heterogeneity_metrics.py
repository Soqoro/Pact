"""Task-clustered natural coverage and communication diagnostics; no outcome gates."""
from collections import Counter
from itertools import permutations
import random
import re
from ..evaluation import rate
from .gpqa_metrics import boundary as _boundary
from .heterogeneity_plan import TEAMS,SEED


def boundary(value):
    _boundary(value)
    def qualify(obj):
        if isinstance(obj,dict):
            if obj.get('boundary_uncertainty'): obj['estimation_status']='inconclusive_boundary'
            for item in list(obj.values()): qualify(item)
        elif isinstance(obj,list):
            for item in obj:qualify(item)
    qualify(value)
    return value


from ..protocol import vote_answer as vote


def summarize(rows,expected,members):
    n=len(rows);complete=[r for r in rows if r['c1'] is not None and r['debate'] is not None]
    acc={m:rate(sum(r['members'][m]['c0'] for r in rows),n) for m in members}
    covered=sum(any(r['c0']) for r in rows);best=max((v['numerator'] for v in acc.values()),default=0)
    out={'expected_tasks':expected,'observed_private_tasks':n,'missing_private_tasks':expected-n,
        'observed_communication_tasks':len(complete),'missing_communication_tasks':expected-len(complete),
        'N0':[sum(sum(r['c0'])==i for r in rows) for i in range(4)],
        'individual_accuracy':acc,'mean_accuracy':rate(sum(sum(r['c0']) for r in rows),3*n),
        'best_accuracy':rate(best,n),'coverage':rate(covered,n),'joint_failure':rate(n-covered,n),
        'gain':rate(covered-best,n),'mixed':rate(sum(r['mixed'] for r in rows),n),
        'wrong_answer_diversity':rate(sum(r['wrong_diversity'] for r in rows),n),
        'answer_disagreement':rate(sum(r['disagreement'] for r in rows),n),
        'slot_accuracy':[rate(sum(r['c0'][i] for r in rows),n) for i in range(3)],
        'unique_coverage':{m:rate(sum(r['members'][m]['c0'] and sum(r['c0'])==1 for r in rows),n) for m in members},
        'valid_peer_unique_coverage':{m:rate(sum(r['members'][m]['c0'] and sum(r['c0'])==1 and all(r['valid0']) for r in rows),sum(all(r['valid0']) for r in rows)) for m in members},
        'pairwise_rescue':[], 'terminal':{},
        'transitions':[[sum(sum(r['c0'])==i and sum(r['c1'])==j for r in complete) for j in range(4)] for i in range(4)]}
    for i,j in permutations(members,2):
        count=sum(r['members'][i]['c0'] and not r['members'][j]['c0'] for r in rows)
        out['pairwise_rescue'].append({'rescuer':i,'rescued':j,'unconditional':rate(count,n),
            'conditional_on_rescued_failure':rate(count,sum(not r['members'][j]['c0'] for r in rows))})
    for protocol in ('vote','synthesis','revised_vote','debate','task_only'):
        observed=[r for r in rows if r[protocol] is not None]
        out['terminal'][protocol]=rate(sum(r[protocol] for r in observed),len(observed))
        out.setdefault('terminal_missing',{})[protocol]=expected-len(observed)
        out.setdefault('terminal_full_cohort_lower_bound',{})[protocol]=rate(sum(r[protocol] for r in observed),expected)
    covered_rows=[r for r in complete if any(r['c0'])];uncovered=[r for r in complete if not any(r['c0'])]
    out.update(utilization=rate(sum(r['debate'] for r in covered_rows),len(covered_rows)),
        construction=rate(sum(r['debate'] for r in uncovered),len(uncovered)),
        erasure=rate(sum(not any(r['c1']) for r in covered_rows),len(covered_rows)),
        new_availability=rate(sum(any(r['c1']) for r in uncovered),len(uncovered)),
        readout_loss=rate(sum(not r['debate'] and any(r['c1']) for r in complete),len(complete)),
        readout_construction=rate(sum(r['debate'] and not any(r['c1']) for r in complete),len(complete)),
        private_readout_loss=rate(sum(not r['synthesis'] and any(r['c0']) for r in rows if r['synthesis'] is not None),sum(r['synthesis'] is not None for r in rows)))
    out['private_readout_construction']=rate(sum(r['synthesis'] and not any(r['c0']) for r in rows if r['synthesis'] is not None),sum(r['synthesis'] is not None for r in rows))
    opportunities=[]
    for r in rows:
        if r['c1'] is None:continue
        for member,v in r['members'].items():
            i=v['slot'];others=[j for j in range(3) if j!=i]
            kind=('hold' if r['c0'][i] and any(r['valid0'][j] and not r['c0'][j] for j in others)
                  else 'repair' if r['valid0'][i] and not r['c0'][i] and any(r['c0'][j] for j in others) else None)
            if kind:opportunities.append({'task':r['task_id'],'family':v['family'],'N0':sum(r['c0']),'kind':kind,'success':r['c1'][i]})
    def opp(rs):return {k:{'rate':rate(sum(v['success'] for v in rs if v['kind']==k),sum(v['kind']==k for v in rs)),
        'tasks':len({v['task'] for v in rs if v['kind']==k})} for k in ('hold','repair')}
    out['opportunities']=opp(opportunities)
    out['opportunities_by_family']={f:opp([v for v in opportunities if v['family']==f]) for f in 'QLM'}
    out['opportunities_by_N0']={str(i):opp([v for v in opportunities if v['N0']==i]) for i in range(4)}
    out['opportunities_by_family_and_N0']={f:{str(i):opp([v for v in opportunities if v['family']==f and v['N0']==i]) for i in range(4)} for f in 'QLM'}
    out['hold']=out['opportunities']['hold']['rate'];out['repair']=out['opportunities']['repair']['rate']
    out['decomposition']={'tasks':len(complete),'successes':sum(r['debate'] for r in complete),
        'covered_successes_plus_uncovered_successes':out['utilization']['numerator']+out['construction']['numerator'],
        'revised_unavailable':sum(not any(r['c1']) for r in complete),
        'uncovered_still_unavailable_plus_erased':len(uncovered)-out['new_availability']['numerator']+out['erasure']['numerator']}
    assert out['decomposition']['successes']==out['decomposition']['covered_successes_plus_uncovered_successes']
    assert out['decomposition']['revised_unavailable']==out['decomposition']['uncovered_still_unavailable_plus_erased']
    return boundary(out)


def statistic(rows,metric,members):
    if not rows:return None
    if metric=='coverage':return sum(any(r['c0']) for r in rows)/len(rows)
    if metric=='gain':return (sum(any(r['c0']) for r in rows)-max(sum(r['members'][m]['c0'] for r in rows) for m in members))/len(rows)
    return sum(r[metric] for r in rows)/len(rows)


def paired(a,b,metric_a,metric_b,members_a,members_b,draws=1000):
    lookup={r['task_id']:r for r in b};pairs=[(r,lookup[r['task_id']]) for r in a if r['task_id'] in lookup]
    pairs=[(x,y) for x,y in pairs if (metric_a in ('coverage','gain') or x[metric_a] is not None) and (metric_b in ('coverage','gain') or y[metric_b] is not None)]
    def diff(ps):return statistic([x for x,y in ps],metric_a,members_a)-statistic([y for x,y in ps],metric_b,members_b)
    if not pairs:return {'tasks':0,'difference':None,'interval':None,'status':'missing'}
    rng=random.Random(SEED);strata=[[p for p in pairs if p[0]['dataset']==f] for f in sorted({p[0]['dataset'] for p in pairs})]
    values=sorted(diff([rng.choice(group) for group in strata for _ in group]) for _ in range(draws))
    boundary_case=values[0]==values[-1]
    out={'tasks':len(pairs),'difference':diff(pairs),'interval':[values[int(.025*draws)],values[int(.975*draws)]],
        'method':'paired task bootstrap stratified by dataset; maxima recomputed within every draw',
        'draws':draws,'status':'inconclusive_boundary' if boundary_case else 'development_diagnostic',
        'note':'Observed cohort only; missing tasks explicit. Degenerate interval does not establish equivalence; one seed schedule.'}
    if metric_a not in ('coverage','gain') and metric_b not in ('coverage','gain'):
        out['paired_outcomes']=dict(Counter(f'{int(y[metric_b])}->{int(x[metric_a])}' for x,y in pairs))
    return out


def strongest_comparison(grouped, metric, draws=1000):
    """Descriptive best homogeneous reference; reselect inside each bootstrap draw."""
    maps={t:{r['task_id']:r for r in rs} for t,rs in grouped.items()}
    ids=sorted(set.intersection(*(set(m) for m in maps.values())))
    ids=[i for i in ids if metric=='coverage' or all(m[i][metric] is not None for m in maps.values())]
    if not ids:return {'tasks':0,'difference':None,'interval':None}
    def value(sample,t):
        return sum(any(maps[t][i]['c0']) if metric=='coverage' else maps[t][i][metric] for i in sample)/len(sample)
    def difference(sample):return value(sample,'QLM')-max(value(sample,t) for t in ('QQQ','LLL','MMM'))
    strata=[[i for i in ids if maps['QLM'][i]['dataset']==d] for d in sorted({maps['QLM'][i]['dataset'] for i in ids})]
    rng=random.Random(SEED);boot=sorted(difference([rng.choice(g) for g in strata for _ in g]) for _ in range(draws))
    return {'tasks':len(ids),'difference':difference(ids),'interval':[boot[int(.025*draws)],boot[int(.975*draws)]],
        'status':'inconclusive_boundary' if boot[0]==boot[-1] else 'development_diagnostic',
        'reference':'best homogeneous on observed cohort; descriptive selection, not prespecified deployment router',
        'method':'dataset-stratified task bootstrap; homogeneous maximum reselected inside every draw'}


def build_report(plan,rows,results):
    from .heterogeneity import packet,team_packets,private_row
    from ..schemas import task_from_dict
    task_metrics=[];family_scores={f:[] for f in 'QLM'};task_only=[]
    for td in plan['source']['tasks']:
        task=task_from_dict(td);tid=task.task_id;gold=plan['source']['labels'][tid]['answer_id']
        correct=lambda p:p.parser_status=='ok' and p.answer_id==gold
        def final(stage,team):
            row=next(r for r in rows if r['task_id']==tid and r['stage']==stage and r['team']==team)
            result=results.get(row['key'])
            return correct(packet(result,task,-1)) if result and result['call']['stop_reason']!='context_overflow' else None
        alone=final('task_only',None)
        if alone is not None:task_only.append(alone)
        for f in 'QLM':
            vals=[]
            for i in range(3):
                result=results.get(private_row(rows,tid,f,i)['key'])
                vals.append(correct(packet(result,task,i)) if result and result['call']['stop_reason']!='context_overflow' else None)
            family_scores[f].append({'task_id':tid,'dataset':task.family,'replicas':vals})
        for team in TEAMS:
            try:private,_=team_packets(plan,rows,results,tid,team)
            except KeyError:continue
            if any(p.call.stop_reason=='context_overflow' for p in private):continue
            valid=[p.parser_status=='ok' for p in private];c0=[correct(p) for p in private]
            try:
                revised,_=team_packets(plan,rows,results,tid,team,True)
                if any(p.call.stop_reason=='context_overflow' for p in revised):revised=None
            except KeyError:revised=None
            bindings=plan['team_bindings'][tid][team]
            member_names=[b['family'] if team=='QLM' else f"{b['family']}{b['replica']}" for b in bindings]
            task_metrics.append({'task_id':tid,'dataset':task.family,'team':team,'c0':c0,'valid0':valid,
                'c1':[correct(p) for p in revised] if revised else None,
                'members':{m:{'c0':c0[i],'slot':i,'family':bindings[i]['family']} for i,m in enumerate(member_names)},
                'mixed':any(c0) and any(v and not c for v,c in zip(valid,c0)),
                'disagreement':len({p.answer_id for p in private if p.parser_status=='ok'})>1,
                'wrong_diversity':not any(c0) and len({p.answer_id for p in private if p.parser_status=='ok'})>1,
                'vote':vote(private)==gold,'revised_vote':vote(revised)==gold if revised else None,
                'synthesis':final('synthesis',team),'debate':final('debate',team),'task_only':alone})
    grouped={t:[r for r in task_metrics if r['team']==t] for t in TEAMS}
    members={t:list('QLM') if t=='QLM' else [f'{t[0]}{i}' for i in range(3)] for t in TEAMS}
    teams={t:{'overall':summarize(rs,len(plan['source']['tasks']),members[t]),
        'complete_valid_sensitivity':summarize([r for r in rs if all(r['valid0'])],len(plan['source']['tasks']),members[t]),
        'by_dataset':{d:summarize([r for r in rs if r['dataset']==d],sum(x['family']==d for x in plan['source']['tasks']),members[t]) for d in ('arc_challenge','logiqa')}} for t,rs in grouped.items()}
    comparisons={'QLM_minus_'+t:{m:paired(grouped['QLM'],grouped[t],m,m,members['QLM'],members[t]) for m in ('coverage','gain','vote','synthesis','debate')} for t in ('QQQ','LLL','MMM')}
    comparisons['QLM_minus_best_observed_homogeneous']={m:strongest_comparison(grouped,m) for m in ('coverage','vote','synthesis','debate')}
    for t in TEAMS:
        comparisons[t+'_protocols']={a+'_minus_'+b:paired(grouped[t],grouped[t],a,b,members[t],members[t]) for a,b in [('debate','synthesis'),('synthesis','vote'),('debate','vote'),('debate','task_only'),('synthesis','task_only'),('revised_vote','vote')]}
    def costs(rs):
        calls=[results[r['key']]['call'] for r in rs if r['key'] in results]
        return {'committed_requests':len(calls),'generation_calls':sum(c['stop_reason']!='context_overflow' for c in calls),
            'input_tokens':sum(c['input_tokens'] for c in calls),'output_tokens':sum(c['output_tokens'] for c in calls),
            'generation_seconds':sum(c['elapsed_seconds'] for c in calls)}
    logical={}
    for t in TEAMS:
        refs={private_row(rows,td['task_id'],b['family'],b['replica'])['key'] for td in plan['source']['tasks'] for b in plan['team_bindings'][td['task_id']][t]}
        logical[t]={mode:costs([r for r in rows if r['key'] in refs or r['team']==t and r['stage'] in stages]) for mode,stages in [('vote',()),('synthesis',('synthesis',)),('debate',('revision','debate'))]}
    family={}
    for f,rs in family_scores.items():
        family[f]={'per_replica':[rate(sum(r['replicas'][i] is True for r in rs),sum(r['replicas'][i] is not None for r in rs)) for i in range(3)],
            'pooled_three_draw':rate(sum(v is True for r in rs for v in r['replicas']),sum(v is not None for r in rs for v in r['replicas'])),
            'designated_single':teams['QLM']['overall']['individual_accuracy'][f],
            'task_groups':len(rs),'uncertainty':'Replicas remain grouped by task; pooled draw count is not independent sample size.', 'note':'Repeated draws within tasks; no best-replica selection'}
    statuses={f:{s:dict(Counter(packet(results[r['key']],task_from_dict(next(t for t in plan['source']['tasks'] if t['task_id']==r['task_id'])),r['slot'] or 0).parser_status for r in rows if r['model']==f and r['stage']==s and r['key'] in results)) for s in ('private','revision','synthesis','debate','task_only')} for f in 'QLMR'}
    result = {'schema_version':1,'study':plan['variant'],'expected_tasks':len(plan['source']['tasks']),
        'teams':teams,'families':family,'draw_level_private':family_scores,'per_task':task_metrics,
        'task_only':rate(sum(task_only),len(task_only)),'task_only_missing':len(plan['source']['tasks'])-len(task_only),
        'comparisons':comparisons,'parser_counts':statuses,
        'context_overflows':[r['key'] for r in rows if r['key'] in results and results[r['key']]['call']['stop_reason']=='context_overflow'],
        'self_identification_mentions':{f:sum(bool(re.search(r'\b(qwen|llama|mistral|alibaba|meta ai)\b',results[r['key']]['raw'],re.I)) for r in rows if r['model']==f and r['key'] in results) for f in 'QLMR'},
        'costs':{'actual':costs(rows),'by_model':{f:costs([r for r in rows if r['model']==f]) for f in 'QLMR'},
            'by_stage':{s:costs([r for r in rows if r['stage']==s]) for s in ('private','revision','synthesis','debate','task_only')},
            'logical_deployment':logical,'compute_units':None,'note':'Shared private calls charged once in actual totals; logical costs reuse them. Cross-tokenizer counts and FLOPs differ.'},
        'uncertainty':'80 task groups when complete; paired stratified bootstrap; no equivalence from boundary outcomes; no automatic next run.',
        'training_executed':False,'gpu_behavior':'unverified_until_returned_evidence','historical_results':'not_pooled'}

    return boundary(result)
