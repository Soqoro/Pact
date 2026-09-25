"""Text-free task-level GPQA support/communication diagnostics."""
from collections import Counter
from itertools import combinations
from ..evaluation import rate, aggregate, paired_bootstrap


def boundary(value):
    if isinstance(value,dict):
        if set(('numerator','denominator','value'))<=value.keys():
            value['boundary_uncertainty']=bool(value['denominator'] and value['numerator'] in (0,value['denominator']))
            value['interval_note']='Small diagnostic; a boundary estimate does not establish a population zero/one rate.'
        for v in list(value.values()):boundary(v)
    elif isinstance(value,list):
        for v in value:boundary(v)
    return value


def support(rows,expected=32):
    n=len(rows);valid=[r for r in rows if all(r['valid0'])]
    hist=lambda rs:[sum(sum(r['c0'])==k for r in rs) for k in range(4)]
    individual=[rate(sum(r['c0'][i] for r in rows),n) for i in range(3)]
    covered=sum(any(r['c0']) for r in rows)
    mixed=[r for r in rows if any(r['c0']) and any(v and not c for v,c in zip(r['valid0'],r['c0']))]
    opportunities={}
    for kind in ('hold','repair'):
        eligible=lambda r,i:(r['c0'][i] and any(r['valid0'][j] and not r['c0'][j] for j in range(3) if j!=i)) if kind=='hold' else (r['valid0'][i] and not r['c0'][i] and any(r['c0'][j] for j in range(3) if j!=i))
        opportunities[kind]={'task_ids':[r['task_id'] for r in rows if any(eligible(r,i) for i in range(3))],
            'agent_contexts':sum(eligible(r,i) for r in rows for i in range(3)),
            'agent0_contexts':sum(eligible(r,0) for r in rows)}
        opportunities[kind]['distinct_tasks']=len(opportunities[kind]['task_ids'])
    return {'completed_private_tasks':n,'expected_tasks':expected,'missing_tasks':expected-n,
        'N0_complete_observed':hist(rows),'N0_complete_valid_teams':hist(valid),'complete_valid_teams':len(valid),
        'N0_conservative_full_cohort':[hist(rows)[0]+expected-n,*hist(rows)[1:]],
        'conservative_note':'Missing private teams assigned zero ONLY in this sensitivity; observed view excludes missing teams.',
        'individual_accuracy':individual,'mean_agent_accuracy':rate(sum(sum(r['c0']) for r in rows),3*n),
        'best_agent_accuracy':max(individual,key=lambda v:v['numerator']),
        'coverage':rate(covered,n),'joint_initial_failure':rate(n-covered,n),
        'oracle_coverage_gain_over_best':{'numerator':covered-max(v['numerator'] for v in individual),'denominator':n,
            'value':(covered-max(v['numerator'] for v in individual))/n if n else None,'deployable_accuracy':False},
        'mixed_support':rate(len(mixed),n),'mixed_task_ids':[r['task_id'] for r in mixed],
        'answer_disagreement':rate(sum(len({a for a,v in zip(r['answers0'],r['valid0']) if v})>1 for r in rows),n),
        'all_wrong_diverse':rate(sum(not any(r['c0']) and len({a for a,v in zip(r['answers0'],r['valid0']) if v})>1 for r in rows),n),
        'no_valid_option_teams':rate(sum(not any(r['valid0']) for r in rows),n),
        'partly_invalid_teams':rate(sum(not all(r['valid0']) for r in rows),n),
        'pairwise':[{'agents':[i,j],
            'valid_option_disagreement':rate(sum(r['valid0'][i] and r['valid0'][j] and r['answers0'][i]!=r['answers0'][j] for r in rows),sum(r['valid0'][i] and r['valid0'][j] for r in rows)),
            'joint_error':rate(sum(not r['c0'][i] and not r['c0'][j] for r in rows),n)} for i,j in combinations(range(3),2)],
        'opportunities':opportunities}


def summarize(rows,protocol_rows,accounting,expected=32):
    private=support(rows,expected);complete=[r for r in rows if r.get('complete')]
    matrix=[[sum(sum(r['c0'])==i and sum(r['c1'])==j for r in complete) for j in range(4)] for i in range(4)]
    mixed=private['mixed_support']['numerator']
    bad=sum(not v for r in rows for v in r['valid0'])
    trunc=sum(s=='length' for r in rows for s in r['parser0'])
    qualification=(len(complete)!=expected or accounting['unresolved_attempts']>0 or bad>=48 or trunc>=48)
    flag='qualified_incomplete_or_invalid' if qualification else 'sufficient_to_design_followup' if mixed>=8 else 'sparse_preliminary' if mixed else 'no_observed_mixed_support'
    pairs={r['task_id']:[(float(r['debate']),float(r['synthesis']))] for r in complete}
    paired=paired_bootstrap(pairs)
    paired['training_seeds']=0
    paired['sampling_unit']='task_id; one draw per actor'
    paired['boundary_note']='Degenerate empirical intervals do not establish equivalence.'
    opportunities={}
    for kind in ('hold','repair'):
        values=[]
        for r in complete:
            for i in range(3):
                eligible=(r['c0'][i] and any(r['valid0'][j] and not r['c0'][j] for j in range(3) if j!=i)) if kind=='hold' else (r['valid0'][i] and not r['c0'][i] and any(r['c0'][j] for j in range(3) if j!=i))
                if eligible:values.append((r['task_id'],i,r['c1'][i]))
        opportunities[kind]={'retention' if kind=='hold' else 'repair_success':rate(sum(v[2] for v in values),len(values)),
            'task_count':len({v[0] for v in values}),'agent0':rate(sum(v[2] for v in values if v[1]==0),sum(v[1]==0 for v in values))}
        if kind=='hold':opportunities[kind]['harmful_revision']=rate(sum(not v[2] for v in values),len(values))
    result={'schema_version':1,'study':'gpqa_diamond_natural_support_v1','scientific_status':'development_diagnostic',
        'training_executed':False,'full_pact_ready':False,'expected_tasks':expected,'completed_tasks':len(complete),
        'missing_tasks':expected-len(complete),'support':private,'N0_to_N1_counts':matrix,
        'N0_to_N1_row_rates':[[rate(v,sum(row)) for v in row] for row in matrix],
        'communication':aggregate(protocol_rows),'natural_opportunity_outcomes':opportunities,
        'terminal':{k:rate(sum(r[k] for r in complete),len(complete)) for k in ('vote','synthesis','debate')},
        'paired_synthesis_to_debate':dict(Counter(f'{r["synthesis"]}->{r["debate"]}' for r in complete)),
        'paired_debate_minus_synthesis':paired,'per_task':rows,'accounting':accounting,
        'screen_flag':flag,'screen_threshold':'at least8/32 mixed tasks; invalid-dominated >=48/96 private packets qualifies flag',
        'no_automatic_followup':True,'rationale_verification':'not_run; correct option is not a verified rationale',
        'historical_context':{'status':'not_pooled','reason':'ARC/LogiQA cohorts are unpaired and descriptive; no historical regeneration'},
        'uncertainty':'32 prespecified tasks, one draw/actor; no efficacy, equivalence, difficulty-causality or within-actor support claim'}
    return boundary(result)
