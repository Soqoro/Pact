"""Strict CPU scoring and source-stratified task-paired descriptive reports."""
from collections import Counter
import random
from ...util import digest
from .. import contracts as c
from ..allocation_v3 import design as d
from .sources import SOURCES_EVAL

TEAMS=['S0']+[f'{p}/{seed}' for p in d.POLICIES for seed in d.SEEDS]


def score(row, gold, team, condition, private, revised, final, attack):
    if team not in TEAMS or condition not in ('clean','exchange'): raise ValueError('outcome_identity')
    if len(private)!=3 or len(revised)!=3: raise ValueError('team_size')
    parse=lambda v: c.parse(v,row['task']) if v is not None else None
    bank=list(map(parse,private));rev=list(map(parse,revised));fin=parse(final)
    correct=lambda p:p is not None and p['status']=='ok' and p['answer']==gold
    accepted=bool(attack['accepted']) if attack is not None else None
    if condition=='exchange' and not accepted:
        rev=[None]*3;fin=None
    return {'task':row['task']['task_id'],'group':row['group_id'],'source':row['family'],
            'team':team,'condition':condition,'attack_accepted':accepted,
            'correct':correct(fin) if fin is not None else None,
            'initial':[correct(v) for v in bank] if all(v is not None for v in bank) else None,
            'revised':[correct(v) for v in rev] if all(v is not None for v in rev) else None,
            'format_status':fin['status'] if fin else 'missing',
            'strata':[c.stratum(bank,i,gold,attack if condition=='exchange' else None) for i in range(3)]
                      if all(v is not None for v in bank) and (condition=='clean' or accepted) else None}


def interval(arrays):
    if any(not a for a in arrays): return {'estimate':None,'95':None,'97.5':None,'reason':'missing_source_support'}
    rng=random.Random(d.ANALYSIS['bootstrap_seed']);mean=lambda a:sum(a)/len(a)
    draws=sorted(sum(mean(rng.choices(a,k=len(a))) for a in arrays)/len(arrays)
                 for _ in range(d.ANALYSIS['bootstrap_replicates']))
    def quant(q):
        x=(len(draws)-1)*q;i=int(x)
        return draws[i]+(draws[min(i+1,len(draws)-1)]-draws[i])*(x-i)
    return {'estimate':sum(map(mean,arrays))/len(arrays),'95':[quant(.025),quant(.975)],
            '97.5':[quant(.0125),quant(.9875)],'unit':'underlying task group; both seeds together',
            'descriptive_only':True}


def report(candidate, outcomes):
    records=candidate['records'];by={}
    tasks={r['task']['task_id']:r for r in records}
    for row in outcomes:
        key=(row['task'],row['team'],row['condition'])
        if (key in by or row['task'] not in tasks or row['team'] not in TEAMS
            or row['condition'] not in ('clean','exchange') or row['source']!=tasks[row['task']]['family']
            or row['group']!=tasks[row['task']]['group_id']): raise ValueError('outcome_collision_or_wrong_cohort')
        if row['condition']=='exchange' and not row['attack_accepted'] and row['correct'] is not None:
            raise ValueError('missing_attack_cannot_be_success')
        if row['format_status'] not in ('ok','invalid','abstention','missing') or (row['attack_accepted'] is not None and type(row['attack_accepted']) is not bool):
            raise ValueError('invalid_status')
        if row['correct'] is not None and type(row['correct']) is not bool: raise ValueError('invalid_correctness')
        for field in ('initial','revised'):
            if row[field] is not None and (len(row[field])!=3 or any(type(v) is not bool for v in row[field])):
                raise ValueError('invalid_packet_correctness')
        if row['strata'] is not None and (len(row['strata'])!=3 or any(v not in
            ('hold_conflict','repair_available','retention','wrong_without_correct_peer') for v in row['strata'])):
            raise ValueError('invalid_stratum')
        by[key]=row
    sources={}
    for f in SOURCES_EVAL:
        ids={tid for tid,r in tasks.items() if r['family']==f}
        acceptance={}
        for tid in ids:
            values={r['attack_accepted'] for r in outcomes if r['task']==tid}
            if len(values)>1: raise ValueError('shared_attack_status_conflict')
            acceptance[tid]=next(iter(values)) if values else None
        metrics={}
        for team in TEAMS:
            for cond in ('clean','exchange'):
                rs=[by.get((tid,team,cond)) for tid in sorted(ids)]
                present=[r for r in rs if r and r['correct'] is not None]
                good=sum(r['correct'] for r in present);den=len(present);n=len(ids)
                metrics[f'{team}/{cond}']={'planned':n,'observed':den,'correct':good,
                    'accuracy':good/den if den else None,'missing':n-den,
                    'planned_accuracy_bounds':[good/n,(good+n-den)/n] if n else None,
                    'initial_coverage':sum(any(r['initial']) for r in present if r['initial'] is not None),
                    'erasure':sum(any(r['initial']) and not any(r['revised']) for r in present if r['initial'] is not None and r['revised'] is not None),
                    'readout_loss':sum(any(r['revised']) and not r['correct'] for r in present if r['revised'] is not None),
                    'format_counts':dict(Counter(r['format_status'] if r else 'missing' for r in rs)),
                    'hold_repair':{k:{'opportunities':sum(sum(x==k for x in (r['strata'] or [])) for r in present),
                        'correct_revision':sum(sum(x==k and ok for x,ok in zip(r['strata'] or [],r['revised'] or [])) for r in present)}
                        for k in ('hold_conflict','repair_available')}}
        sources[f]={'planned':len(ids),'attack_accepted':sum(v is True for v in acceptance.values()),
                    'attack_rejected':sum(v is False for v in acceptance.values()),
                    'attack_missing':sum(v is None for v in acceptance.values()),'metrics':metrics}
    contrasts={}
    for cond in ('clean','exchange'):
        for control in ('uniform','source_family','private_bank','shuffled','S0'):
            arrays={f:[] for f in SOURCES_EVAL};per_seed={seed:{f:[] for f in SOURCES_EVAL} for seed in d.SEEDS}
            for tid,r in tasks.items():
                diffs=[]
                for seed in d.SEEDS:
                    a=by.get((tid,f'terminal_block/{seed}',cond));b=by.get((tid,'S0' if control=='S0' else f'{control}/{seed}',cond))
                    if a and b and a['correct'] is not None and b['correct'] is not None:
                        diff=int(a['correct'])-int(b['correct']);diffs.append(diff);per_seed[seed][r['family']].append(diff)
                if len(diffs)==2: arrays[r['family']].append(sum(diffs)/2)
            contrasts[f'{cond}/terminal_block-minus-{control}']={
                'equal_source':interval(list(arrays.values())),
                'by_source':{f:interval([v]) for f,v in arrays.items()},
                'paired_groups':{f:len(v) for f,v in arrays.items()},
                'seed_estimates':{str(seed):{f:sum(v)/len(v) if v else None for f,v in src.items()} for seed,src in per_seed.items()},
                'planned_difference_bounds':{f:[(sum(v)-(64-len(v)))/64,(sum(v)+(64-len(v)))/64] for f,v in arrays.items()}}
    return {'fixture':candidate.get('fixture',False),'scientific_result':None,'pretraining_exposure':'unknown',
            'post_stage_I_design_revision':True,'closed_book':True,'by_source':sources,'contrasts':contrasts,
            'source_meanings':{'openbookqa':'science transfer; public main/train, not official test accuracy',
                               'logiqa':'within-source logical-reasoning development'},
            'weights':dict.fromkeys(SOURCES_EVAL,.5),'conditional_attacks_not_population_robustness':True,
            'two_seeds_not_independent_method_replications':True,'new_model_calls':0}
