"""Offline complete-case and intended-denominator metrics; cluster by source group."""
from collections import Counter,defaultdict
import random
from types import SimpleNamespace
from ..evaluation import rate
from ..protocol import vote_answer
from ..studies.heterogeneity_metrics import summarize,statistic
from .contracts import BenchmarkInput,parse
from .registry import SEED


def paired(a,b,metric_a,metric_b,ma,mb,draws=1000,macro=False):
    lookup={r['task_id']:r for r in b};pairs=[(r,lookup[r['task_id']]) for r in a if r['task_id'] in lookup]
    pairs=[(x,y) for x,y in pairs if (metric_a in ('coverage','gain') or x[metric_a] is not None) and (metric_b in ('coverage','gain') or y[metric_b] is not None)]
    if not pairs:return {'status':'missing','tasks':0,'groups':0,'difference':None,'interval':None}
    strata=defaultdict(lambda:defaultdict(list))
    for x,y in pairs:strata[x['dataset']][x['group_id']].append((x,y))
    def effect(ps):
        # Equal stratum macro is primary; same selected cohorts across all arms.
        ss=defaultdict(list)
        for x,y in ps:ss[x['dataset']].append((x,y))
        def estimate(side,metric,members):
            groups=[[p[side] for p in v] for v in ss.values()]
            weights=[1/len(groups) if macro else len(g)/len(ps) for g in groups]
            if metric=='gain':
                coverage=sum(w*statistic(g,'coverage',members) for w,g in zip(weights,groups))
                best=max(sum(w*sum(r['members'][m]['c0'] for r in g)/len(g) for w,g in zip(weights,groups)) for m in members)
                return coverage-best
            return sum(w*statistic(g,metric,members) for w,g in zip(weights,groups))
        return estimate(0,metric_a,ma)-estimate(1,metric_b,mb)
    rng=random.Random(SEED);values=[]
    for _ in range(draws):
        sample=[]
        for groups in strata.values():
            keys=sorted(groups)
            for _ in keys:sample.extend(groups[rng.choice(keys)])
        values.append(effect(sample))
    values.sort()
    return {'status':'inconclusive_boundary' if values[0]==values[-1] else 'development_diagnostic','tasks':len(pairs),'groups':sum(len(g) for g in strata.values()),
            'difference':effect(pairs),'interval':[values[int(.025*draws)],values[int(.975*draws)]],
            'method':'paired group bootstrap within strata; selected maxima recomputed', 'aggregation':'macro' if macro else 'micro',
            'boundary_uncertainty':values[0]==values[-1],
            'paired_outcomes':dict(Counter(str(int(y[metric_b]))+'->'+str(int(x[metric_a])) for x,y in pairs)) if metric_a not in ('coverage','gain') and metric_b not in ('coverage','gain') else None}


def reports(plan,results,rows,scores):
    all_rows={r['key']:r for r in rows};teams={};tables={};n=len(plan['data']['selected'])
    def value(row):return scores.get(row['key'])
    for team in ('QQQ','LLL','MMM','QLM'):
        observations=[];native=[]
        for item in plan['data']['selected']:
            task=BenchmarkInput.from_dict(item['task']);tid=task.task_id;bind=plan['bindings'][tid][team]
            def get(stage,model=None,replica=None):
                return next(r for r in rows if r['task_id']==tid and r['stage']==stage and
                            (r['team']==team if stage in ('revision','synthesis','debate') else True) and
                            (r['model']==model if model else True) and (r['replica']==replica if replica is not None else True))
            initial=[get('private',b['family'],b['replica']) for b in bind]
            v=[value(r) for r in initial]
            if any(x is None or x['availability']!='scored' or x['full_success'] is None for x in v):continue
            c=[x['full_success'] for x in v];valid=[bool(x['syntactic_valid']) for x in v]
            parsed=[parse(task,results[r['key']]['raw'],stop=results[r['key']]['call']['stop_reason']) for r in initial]
            keys=[p['vote_key'] for p in parsed]
            can_vote=task.kind=='mcq' # optional math/native vote deliberately N/A
            gold=item['eval'].get('answer')
            vote=vote_answer([SimpleNamespace(answer_id=k,parser_status='ok' if ok else 'invalid') for k,ok in zip(keys,valid)]) if can_vote else None
            rec={'task_id':tid,'group_id':item['group_id'],'dataset':item['stratum'],'c0':c,'valid0':valid,'c1':None,
                 'members':{(b['family'] if team=='QLM' else b['family']+str(b['replica'])):{'family':b['family'],'slot':b['slot'],'c0':c[j]} for j,b in enumerate(bind)},
                 'mixed':any(c) and any(ok and not correct for ok,correct in zip(valid,c)),
                 'disagreement':len({k for k in keys if k is not None})>1,
                 'wrong_diversity':not any(c) and len({k for k in keys if k is not None})>1,
                 'vote':vote==gold if can_vote else None,'revised_vote':None,'synthesis':None,'debate':None,'task_only':None}
            if plan['profile']['core']:
                revisions=[get('revision',b['family'],b['replica']) for b in bind];rv=[value(r) for r in revisions]
                if all(x and x['availability']=='scored' and x['full_success'] is not None for x in rv):
                    rec['c1']=[x['full_success'] for x in rv]
                    if can_vote:
                        packets=[parse(task,results[r['key']]['raw'],stop=results[r['key']]['call']['stop_reason']) for r in revisions]
                        rec['revised_vote']=vote_answer([SimpleNamespace(answer_id=p['vote_key'],parser_status='ok' if p['status']=='ok' else 'invalid') for p in packets])==gold
                for stage in ('synthesis','debate','task_only'):
                    sv=value(get(stage))
                    if sv and sv['availability']=='scored':rec[stage]=sv['full_success']
            observations.append(rec);native.append({'stratum':item['stratum'],'mean':sum(x['native_score'] for x in v)/3,'oracle_best':max(x['native_score'] for x in v)})
        members=list(observations[0]['members']) if observations else (list('QLM') if team=='QLM' else [team[0]+str(i) for i in range(3)])
        summary=summarize(observations,n,members);summary['vote_semantics']='strict_mcq' if plan['profile']['kind']=='mcq' else 'not_applicable'
        strata=sorted({x['stratum'] for x in plan['data']['selected']})
        by={s:summarize([r for r in observations if r['dataset']==s],sum(x['stratum']==s for x in plan['data']['selected']),members) for s in strata}
        for entry in [summary,*by.values()]:
            if plan['profile']['kind']=='python_program':
                entry['answer_disagreement']=None;entry['wrong_answer_diversity']=None
            if plan['profile']['kind']!='mcq':
                for field in ('vote','revised_vote'):
                    entry['terminal'][field]=None;entry['terminal_full_cohort_lower_bound'][field]=None
                    entry['terminal_missing'][field]=None
        summary['coverage_intended_bounds']=[summary['coverage']['numerator']/n,(summary['coverage']['numerator']+n-len(observations))/n]
        macro={m:(sum(v[m]['value'] for v in by.values())/len(by) if all(v[m]['value'] is not None for v in by.values()) else None) for m in ('coverage','gain','joint_failure')}
        macro['individual_accuracy']={m:(sum(v['individual_accuracy'][m]['value'] for v in by.values())/len(by) if all(v['individual_accuracy'][m]['value'] is not None for v in by.values()) else None) for m in members}
        macro['best_accuracy']=max(macro['individual_accuracy'].values()) if all(v is not None for v in macro['individual_accuracy'].values()) else None
        macro['gain']=macro['coverage']-macro['best_accuracy'] if macro['coverage'] is not None and macro['best_accuracy'] is not None else None
        macro['terminal']={m:(sum(v['terminal'][m]['value'] for v in by.values())/len(by) if all(v['terminal'][m] and v['terminal'][m]['value'] is not None for v in by.values()) else None) for m in ('vote','synthesis','revised_vote','debate','task_only')}
        teams[team]={'complete_case':summary,'by_stratum':by,'macro':macro,'primary':'macro' if plan['dataset'] in ('mmlu-pro','musr') else 'micro_with_stratum_weights',
                     'stratum_weights':{s:sum(x['stratum']==s for x in plan['data']['selected'])/n for s in strata},
                     'native_private_mean':sum(x['mean'] for x in native)/len(native) if native else None,
                     'oracle_best_candidate_score':sum(x['oracle_best'] for x in native)/len(native) if native else None}
        def native_summary(rs):
            return {'scored_tasks':len(rs),'mean_candidate_score':sum(x['mean'] for x in rs)/len(rs) if rs else None,
                    'oracle_best_candidate_score':sum(x['oracle_best'] for x in rs)/len(rs) if rs else None}
        teams[team]['native_by_stratum']={s:native_summary([x for x in native if x['stratum']==s]) for s in strata}
        teams[team]['native_by_category']={s:native_summary([x for x in native if x['stratum'].split('|')[0]==s]) for s in sorted({s.split('|')[0] for s in strata})}
        teams[team]['disagreement_semantics']='exact_extracted_expression_only_not_math_equivalence' if plan['profile']['kind']=='math_free_response' else summary['vote_semantics']
        tables[team]=observations
    comparisons={}
    for other in ('QQQ','LLL','MMM'):
        comparisons['QLM_minus_'+other]={m:paired(tables['QLM'],tables[other],m,m,list('QLM'),[other[0]+str(i) for i in range(3)],macro=plan['dataset'] in ('mmlu-pro','musr')) for m in ('coverage','gain','synthesis','debate')}
    comparisons['synthesis_vs_debate']={t:paired(rs,rs,'debate','synthesis',list(rs[0]['members']) if rs else [],list(rs[0]['members']) if rs else [],macro=plan['dataset'] in ('mmlu-pro','musr')) for t,rs in tables.items()}
    return teams,comparisons,tables
