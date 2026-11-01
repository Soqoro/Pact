"""Task-paired two-seed means; accepted-population completeness is not selection."""
from ..allocation_v3 import design as d
from ..evaluation_source.results import score, interval, TEAMS
from .sources import SOURCES_EVAL


def report(candidate,outcomes):
    tasks={r['task']['task_id']:r for r in candidate['records']};by={};accepted={}
    for r in outcomes:
        key=(r['task'],r['team'],r['condition'])
        if key in by or r['task'] not in tasks or r['team'] not in TEAMS or r['condition'] not in ('clean','exchange'):
            raise ValueError('outcome_identity_conflict')
        if r['source']!=tasks[r['task']]['family'] or r['group']!=tasks[r['task']]['group_id']:raise ValueError('outcome_cohort_conflict')
        if r['correct'] is not None and type(r['correct']) is not bool:raise ValueError('outcome_type')
        if r['format_status'] in ('invalid','abstention') and r['correct'] is not False:raise ValueError('strict_failure_required')
        if r['format_status']=='missing' and r['correct'] is not None:raise ValueError('technical_missingness_required')
        if r['format_status'] not in ('ok','invalid','abstention','missing'):raise ValueError('format_status')
        if r['attack_accepted'] is not None and type(r['attack_accepted']) is not bool:raise ValueError('attack_status')
        if r['task'] in accepted and accepted[r['task']]!=r['attack_accepted']:raise ValueError('shared_attack_conflict')
        if r['condition']=='exchange' and r['attack_accepted'] is not True and r['correct'] is not None:raise ValueError('missing_intervention')
        for field in ('initial','revised'):
            if r.get(field) is not None and (len(r[field])!=3 or any(type(v) is not bool for v in r[field])):raise ValueError('packet_correctness_contract')
        if r.get('strata') is not None and (len(r['strata'])!=3 or any(v not in ('hold_conflict','repair_available','retention','wrong_without_correct_peer') for v in r['strata'])):raise ValueError('stratum_contract')
        accepted[r['task']]=r['attack_accepted'];by[key]=r
    def val(t,team,cond):return by.get((t,team,cond),{}).get('correct')
    sources={};contrasts={}
    for f in SOURCES_EVAL:
        ids=[t for t,r in tasks.items() if r['family']==f]
        sources[f]={'planned':len(ids),'accepted':sum(accepted.get(t) is True for t in ids),
                    'rejected':sum(accepted.get(t) is False for t in ids),'unknown_attack':sum(accepted.get(t) is None for t in ids),'teams':{}}
        for team in TEAMS:
            for cond in ('clean','exchange'):
                expected=ids if cond=='clean' else [t for t in ids if accepted.get(t) is True]
                vs=[val(t,team,cond) for t in expected];complete=bool(expected) and all(v is not None for v in vs)
                sources[f]['teams'][f'{team}/{cond}']={'expected':len(expected),'observed':sum(v is not None for v in vs),
                    'accuracy':sum(vs)/len(vs) if complete else None,'complete':complete}
                observed=[by[t,team,cond] for t in expected if (t,team,cond) in by]
                sources[f]['teams'][f'{team}/{cond}']['natural_hold_repair']={
                    kind:{'opportunities':sum(sum(x==kind for x in (r.get('strata') or [])) for r in observed),
                          'observed_revisions':sum(sum(x==kind for x in (r.get('strata') or [])) for r in observed if r.get('revised') is not None),
                          'correct_revisions':sum(sum(x==kind and ok for x,ok in zip(r.get('strata') or [],r.get('revised') or [])) for r in observed)}
                    for kind in ('hold_conflict','repair_available','retention','wrong_without_correct_peer')}
                sources[f]['teams'][f'{team}/{cond}']['identical_context_comparison']=False
    for cond in ('clean','exchange'):
        for ctrl in ('uniform','source_family','private_bank','shuffled','S0'):
            arrays={};seedmeans={};bounds={};complete=True
            for f in SOURCES_EVAL:
                ids=[t for t,r in tasks.items() if r['family']==f];expected=ids if cond=='clean' else [t for t in ids if accepted.get(t) is True]
                arr=[];sv={k:[] for k in d.SEEDS};lo=hi=0.
                for t in ids:
                    ds=[]
                    for seed in d.SEEDS:
                        a=val(t,f'terminal_block/{seed}',cond);b=val(t,'S0' if ctrl=='S0' else f'{ctrl}/{seed}',cond)
                        lo+=.5*((int(a) if a is not None else 0)-(int(b) if b is not None else 1))
                        hi+=.5*((int(a) if a is not None else 1)-(int(b) if b is not None else 0))
                        if a is not None and b is not None and t in expected:ds.append(int(a)-int(b));sv[seed].append(int(a)-int(b))
                    if len(ds)==2:arr.append(sum(ds)/2)
                ok=len(arr)==len(expected) and bool(expected) and (cond=='clean' or sources[f]['unknown_attack']==0)
                complete &= ok
                arrays[f]=arr;bounds[f]=[lo/len(ids),hi/len(ids)] if ids else [-1,1]
                seedmeans[f]={str(k):sum(v)/len(v) if len(v)==len(expected) and v else None for k,v in sv.items()}
            contrasts[f'{cond}/terminal_block-minus-{ctrl}']={'status':'complete' if complete else 'incomplete_or_undefined',
                'equal_source':interval(list(arrays.values())) if complete else {'estimate':None,'reason':'missing_or_zero_source_support'},
                'by_source':{f:interval([a]) if len(a)==(sources[f]['planned'] if cond=='clean' else sources[f]['accepted']) and a and (cond=='clean' or not sources[f]['unknown_attack']) else {'estimate':None} for f,a in arrays.items()},
                'seed_specific':seedmeans,'intended_population_bounds':bounds,
                'equal_source_bounds':[sum(v[i] for v in bounds.values())/2 for i in range(2)]}
    return {'fixture':candidate.get('fixture',False),'by_source':sources,'contrasts':contrasts,'source_weights':dict.fromkeys(SOURCES_EVAL,.5),
        's0_independent_repetitions':1,'scientific_result':None,'pretraining_exposure':'unknown',
        'interpretation':'filtered GPQA-Main science transfer; original LogiQA generalization; development only'}
