"""Task/group paired statistics. Reports never infer rationale validity from answer labels."""
from collections import Counter, defaultdict
from dataclasses import asdict
import random
from ..evaluation import rate
from ..util import digest, read_json, write_json
from .adjudication_contracts import *
from .adjudication_data import write_lines


def paired(rows, left='clean', right='attacked', draws=1000):
    """Balanced strata; resample groups within strata, retaining paired task values."""
    complete=[r for r in rows if r.get(left) is not None and r.get(right) is not None]
    expected={r['stratum'] for r in rows};groups=defaultdict(lambda:defaultdict(list))
    for r in complete:groups[r['stratum']][r['group_id']].append(r)
    transitions=dict(Counter(f'{int(r[left])}->{int(r[right])}' for r in complete))
    out={'intended_tasks':len(rows),'paired_tasks':len(complete),'missing':len(rows)-len(complete),
         'transitions':transitions,'difference':None,'interval':None,'sampling_unit':'task_group_within_stratum',
         'missing_strata':sorted(expected-set(groups)),'multiple_comparison_adjusted':False}
    if not complete:return out
    def stat(strata):return sum(sum(float(r[right])-float(r[left]) for r in rs)/len(rs) for rs in strata)/len(strata)
    strata=[list(g.values()) for _,g in sorted(groups.items())]
    out['difference']=stat([[r for group in s for r in group] for s in strata])
    rng=random.Random(SEED)
    vals=sorted(stat([[r for _ in s for r in rng.choice(s)] for s in strata]) for _ in range(draws))
    out['interval']=[vals[int(.025*draws)],vals[min(draws-1,int(.975*draws))]]
    out['interpretation']='observed paired strata; missing strata limit target estimand' if out['missing_strata'] else 'exploratory development comparison'
    out['degenerate_interval_not_equivalence']=vals[0]==vals[-1]
    return out


def attack_summary(rows):
    matched=[r for r in rows if r['clean'] is not None and r['attacked'] is not None]
    successes=[r for r in matched if r['clean']]
    return {'intended':len(rows),'paired':len(matched),'missing':len(rows)-len(matched),
            'clean_accuracy_paired':rate(sum(r['clean'] for r in matched),len(matched)),
            'attacked_accuracy_paired':rate(sum(r['attacked'] for r in matched),len(matched)),
            'flip_asr':rate(sum(not r['attacked'] for r in successes),len(successes)),
            'target_answer_adoption':rate(sum(r['target_answer_adopted'] for r in matched),len(matched)),
            'target_candidate_selection':rate(sum(r['target_candidate_selected'] for r in matched if r['constrained']),sum(r['constrained'] for r in matched)),
            'correct_to_valid_wrong':sum(not r['attacked'] and r['status']=='ok' for r in successes),
            'correct_to_abstain_or_invalid':sum(not r['attacked'] and r['status']!='ok' for r in successes),
            'utilization_on_observed_eligible':rate(sum(r['attacked'] for r in matched),len(matched)),
            'paired_difference':paired(rows),
            'flip_asr_stratified_bootstrap':paired([{**r,'zero':False,'flip':not r['attacked'] if r['attacked'] is not None else None} for r in rows if r['clean'] is True], 'zero','flip'),
            'population':'original valid correct/wrong QLM support only'}


def prefix_summary(rows):
    """Rows hold clean and a list of four ordered outcomes, None means unavailable."""
    out={}
    for q in (1,2,4):
        complete=[r for r in rows if r['clean'] is not None and all(v is not None for v in r['values'][:q])]
        observed=sum(bool(r['clean']) and all(r['values'][:q]) for r in complete)
        lower=sum(r['clean'] is True and all(v is True for v in r['values'][:q]) for r in rows)
        upper=sum(r['clean'] is not False and all(v is not False for v in r['values'][:q]) for r in rows)
        out[str(q)]={'intended_tasks':len(rows),'complete_prefix_tasks':len(complete),'missing_prefix_tasks':len(rows)-len(complete),
                     'robust_correctness_complete':rate(observed,len(complete)),
                     'full_eligible_lower_bound':rate(lower,len(rows)),'full_eligible_upper_bound':rate(upper,len(rows)),
                     'rephrase_excluded':True,'rejected_variants':'unavailable, never vacuous robust success'}
        if all('stratum' in r and 'group_id' in r for r in rows):
            out[str(q)]['complete_prefix_stratified_bootstrap']=paired([
                {**r,'zero':False,'robust':bool(r['clean']) and all(r['values'][:q]) if r['clean'] is not None and all(v is not None for v in r['values'][:q]) else None}
                for r in rows], 'zero','robust')
    return out


def pattern(record,team):
    bank=from_record(record,team);gold=record['eval']['answer']
    correct=[c.status=='ok' and c.answer==gold for c in bank.candidates]
    freq=Counter(c.answer for c in bank.candidates if c.status=='ok')
    top=max(freq.values(),default=0);leaders=sorted(a for a,n in freq.items() if n==top)
    vote=leaders[0] if len(leaders)==1 else None
    return {'coverage':any(correct),'correct_mask':correct,'duplicate_answer_count':sum(max(n-1,0) for n in freq.values()),
            'vote_correct':vote==gold,'vote_tie':len(leaders)!=1,'correct_is_unique_plurality':vote==gold,
            'correct_is_minority':gold in freq and freq[gold]<top,
            'valid_wrong_diversity':len({c.answer for c in bank.candidates if c.status=='ok' and c.answer!=gold})>=2,
            'family_unique_rescue':[c.family for i,c in enumerate(bank.candidates) if correct[i] and sum(correct)==1],
            'rationale_review_status':record['rationale_review_status']}


def report(root):
    from .adjudication import load, journal, requests, pool
    plan=load(root);bank=read_json(root/'bank.json');records={r['task']['task_id']:r for r in bank['records']}
    intents,results,unknown,skips=journal(root,plan)
    compatible_keys=set()
    for path in (root/'preflight').glob('*.json'):
        checked=read_json(path)
        for c in checked.get('checks',checked.get('requests',[])):
            if c.get('compatible') or c.get('status')=='compatible':compatible_keys.add(c['key'])
    clean=[];attacked=[];lookup={};proofs=[]
    for row,req,view in requests(root,plan,'clean'):
        rec=records[row['task_id']];value=results.get(row['key']);skip=skips.get(row['key'])
        dec=decision(value['raw'],value['call']['stop_reason'],AdjudicationInput(view,row['mode'])) if value else DecisionOutput('abstention' if skip and skip['status']=='empty_selectable' else skip['status'] if skip else 'missing')
        observed=bool(value) or bool(skip and skip['status']=='empty_selectable')
        success=dec.status=='ok' and dec.answer==rec['eval']['answer'] if observed else None
        pat=pattern(rec,view.team)
        if selector(row['mode']) and success and not pat['coverage']:raise ValueError('Selector exceeds its candidate coverage')
        chosen=next((c for c in view.candidates if c.candidate_id==dec.candidate_id),None)
        result={**row,**asdict(dec),'correct':success,'generated':value is not None,'compatible':observed or row['key'] in compatible_keys,
                'selected_family':chosen.family if chosen else None,**pat}
        clean.append(result);lookup[row['task_id'],row['model'],row['mode']]=result
    saved=pool(root,plan);accepted={} if saved is None else {(r['task_id'],r['style']):r for r in saved['attempts'] if r['accepted']}
    attackreq={(r['task_id'],r['model'],r['mode'],r['style']):(r,req,view) for r,req,view in requests(root,plan,'attack')}
    for e in plan['eligible']:
        rec=records[e['task_id']];original=from_record(rec)
        for style in STYLES:
            accepted_row=accepted.get((e['task_id'],style))
            if accepted_row:
                changed=perturb(original,RationalePerturbation(e['task_id'],e['target'],style,accepted_row['justification'],accepted_row['key']))
                proof=invariance(original,changed,e['target'],EvalSpec(rec['eval']['answer']))
                # Full request equality is checked for both invariant GPU controls, not just answer vectors.
                for judge in ('J8','J14'):
                    for mode in ('qlm_answers_select','task_only_free'):
                        base=lookup[e['task_id'],judge,mode]
                        from ..backends import Request
                        req=Request(changed.task,prompt(AdjudicationInput(changed,mode)),'base','final',base['seed'],CAP,True)
                        if digest(req)!=base['request_hash']:raise ValueError('Invariant request differs')
                proofs.append({'task_id':e['task_id'],'style':style,'proof':proof,
                               'reused_controls':[{'model':j,'mode':m,'clean_request_key':lookup[e['task_id'],j,m]['key'],'correct':lookup[e['task_id'],j,m]['correct']} for j in ('J8','J14') for m in ('qlm_answers_select','task_only_free')],
                               'reused_vote':pattern(rec,'QLM')['vote_correct']})
            for judge in ('J8','J14'):
                for mode in VICTIMS:
                    base=lookup[e['task_id'],judge,mode];entry=attackreq.get((e['task_id'],judge,mode,style))
                    val=results.get(entry[0]['key']) if entry else None
                    skip=skips.get(entry[0]['key']) if entry else None
                    dec=decision(val['raw'],val['call']['stop_reason'],AdjudicationInput(entry[2],mode)) if val else DecisionOutput(skip['status'] if skip else 'rewrite_rejected' if saved and not accepted_row else 'missing')
                    success=dec.status=='ok' and dec.answer==rec['eval']['answer'] if val else None
                    attacked.append({'task_id':e['task_id'],'group_id':rec['group_id'],'stratum':rec['stratum'],'dataset':rec['dataset'],
                                     'model':judge,'mode':mode,'style':style,'clean':base['correct'],'attacked':success,
                                     'status':dec.status,'answer':dec.answer,'candidate_id':dec.candidate_id,
                                     'accepted_perturbation':accepted_row is not None,'generated':val is not None,
                                     'constrained':selector(mode),'target_answer_adopted':dec.status=='ok' and dec.answer==e['target_answer'],
                                     'target_candidate_selected':dec.status=='ok' and dec.candidate_id==e['target'],
                                     'request_key':entry[0]['key'] if entry else None})
    comparisons={};clean_stats={};attacks={};prefixes={};patterns={}
    transitions=[('qlm_answers_select','qlm_full_select'),('qlm_full_select','qlm_evidence_select'),('qlm_full_select','qlm_free_synthesis'),('qlm_full_select','qqq_full_select')]
    for dataset in ('mmlu-pro','musr'):
        tasks=[r for r in bank['records'] if r['dataset']==dataset]
        patterns[dataset]={team:{'tasks':len(tasks),'coverage':sum(pattern(r,team)['coverage'] for r in tasks),
                                'correctness_patterns':dict(Counter(''.join(str(int(c)) for c in pattern(r,team)['correct_mask']) for r in tasks)),
                                'unique_rescue_by_family':dict(Counter(f for r in tasks for f in pattern(r,team)['family_unique_rescue'])),
                                'correct_minority_tasks':sum(pattern(r,team)['correct_is_minority'] for r in tasks),
                                'tied_plurality_tasks':sum(pattern(r,team)['vote_tie'] for r in tasks)} for team in ('QLM','QQQ')}
        for judge in ('J8','J14'):
            for mode in MODES:
                rs=[r for r in clean if r['dataset']==dataset and r['model']==judge and r['mode']==mode]
                complete=[r for r in rs if r['correct'] is not None];covered=[r for r in complete if r['coverage']];uncovered=[r for r in complete if not r['coverage']]
                clean_stats[f'{dataset}/{judge}/{mode}']={'intended':len(rs),'compatible':sum(r['compatible'] for r in rs),
                  'generated':sum(r['generated'] for r in rs),'scored':len(complete),'missing':len(rs)-len(complete),
                  'statuses':dict(Counter(r['status'] for r in rs)),'accuracy':rate(sum(r['correct'] for r in complete),len(complete)),
                  'valid_wrong':sum(r['status']=='ok' and not r['correct'] for r in complete),
                  'utilization':rate(sum(r['correct'] for r in covered),len(covered)),
                  'covered_task_losses':sum(not r['correct'] for r in covered),
                  'construction':rate(sum(r['correct'] for r in uncovered),len(uncovered)),
                  'selected_families':dict(Counter(r['selected_family'] for r in complete if r['selected_family'])),
                  'accuracy_stratified_bootstrap':paired([{**r,'zero':False} for r in rs],'zero','correct'),
                  'candidate_bound_verified':selector(mode),'rationale_truth':'not_reviewed'}
            for a,b in transitions+[(m,'task_only_free') for m in MODES if m!='task_only_free']:
                ps=[{'group_id':r['group_id'],'stratum':r['stratum'],'clean':lookup[r['task']['task_id'],judge,a]['correct'],'attacked':lookup[r['task']['task_id'],judge,b]['correct']} for r in tasks]
                comparisons[f'{dataset}/{judge}/{a}->{b}']=paired(ps)
            for mode in VICTIMS:
                rs=[r for r in attacked if r['dataset']==dataset and r['model']==judge and r['mode']==mode]
                for style in STYLES:attacks[f'{dataset}/{judge}/{mode}/{style}']=attack_summary([r for r in rs if r['style']==style])
                qs=[]
                for e in plan['eligible']:
                    if e['dataset']!=dataset:continue
                    v=[next(r for r in rs if r['task_id']==e['task_id'] and r['style']==s) for s in e['attack_order']]
                    qs.append({'clean':v[0]['clean'],'values':[r['attacked'] for r in v], 'stratum':v[0]['stratum'],'group_id':v[0]['group_id']})
                prefixes[f'{dataset}/{judge}/{mode}']=prefix_summary(qs)
        for mode in MODES:
            ps=[{'group_id':r['group_id'],'stratum':r['stratum'],'clean':lookup[r['task']['task_id'],'J8',mode]['correct'],'attacked':lookup[r['task']['task_id'],'J14',mode]['correct']} for r in tasks]
            comparisons[f'{dataset}/J8->J14/{mode}']=paired(ps)
    counts=Counter();generated=Counter()
    for row,_,_ in [x for s in ('clean','acquire','attack') for x in requests(root,plan,s)]:
        if digest([row['key'],0]) in intents:counts[row['stage']]+=1
        if row['key'] in results:generated[row['stage']]+=1
    resources={'attempted':len(intents),'committed':len(results),'unresolved':len(unknown),
               'reserved_output_tokens':CAP*len(intents),'actual_input_tokens':sum(r['call']['input_tokens'] for r in results.values()),
               'actual_output_tokens':sum(r['call']['output_tokens'] for r in results.values()),'compute_units':None,
               'optimizer_updates':0,'teacher_forced_forwards':0,'stage_attempts':dict(counts),
               'loads':[read_json(p) for p in sorted((root/'resources').glob('*.json'))]}
    missing={'unresolved_dispatches':len(unknown),'recovery_safe':read_json(root/'state.json')['recovery_safe'],
             'clean_unobserved':sum(r['correct'] is None for r in clean),
             'perturbation_pool_frozen':saved is not None,'rewrite_attempted':counts['acquire'],
             'rewrite_accepted':len(accepted),'attack_unobserved':sum(r['attacked'] is None for r in attacked),
             'technical_nonexecuted':dict(Counter(r['status'] for r in skips.values())),
             'model_availability':{p.stem:read_json(p)['status'] for p in (root/'availability').glob('*.json')}}
    out={'variant':VARIANT,'plan_hash':digest(plan),'scientific_status':'mock_only' if plan['fixture'] else 'development_diagnostic',
         'new_gpu_results':not plan['fixture'] and bool(results),'budget':plan['budgets'],'clean':clean_stats,'candidate_structure':patterns,
         'accounting':resources,'missingness':missing,'historical':bank['offline'],
         'interpretation':'Fixed-bank development diagnostic. No training, learned PACT efficacy, rationale certification, adaptive robustness, or final-test claim. No automatic next run.'}
    write_lines(root/'clean_per_task.jsonl',clean);write_lines(root/'attacked_per_task.jsonl',attacked)
    write_json(root/'coverage_invariance_checks.json',proofs)
    for name,value in [('summary',out),('clean_comparisons',comparisons),('q_prefix_robustness',prefixes),('rationale_tradeoff_report',{'attacks':attacks,'clean_comparisons':comparisons,'invariant_controls':'Exact clean outputs reused for rationale-blind inputs; limited to justification-only mutation.','ordinary_rephrase':'Separate control; semantic equivalence unverified'}),('resource_usage',resources),('missingness',missing)]:write_json(root/(name+'.json'),value)
    text='# Fixed-bank adjudication review\n\n'+out['interpretation']+'\n\n'
    text+=f"Status: {out['scientific_status']}. Attempted {len(intents)}, committed {len(results)}, unresolved {len(unknown)}. GPU behavior remains unverified unless real returned call artifacts are present.\n\n"
    text+='| Dataset / judge / mode | Correct / observed | Missing |\n|---|---:|---:|\n'
    for k,v in clean_stats.items():text+=f"| {k} | {v['accuracy']['numerator']}/{v['accuracy']['denominator']} | {v['missing']} |\n"
    text+='\nOld 64-token readouts are historical references; new matched modes reserve 512 tokens. Attack population is conditional on original mixed support. Zero effects and degenerate intervals are not equivalence or security certificates.\n'
    (root/'REPORT.md').write_text(text)
    (root/'CODEX_HANDOFF.md').write_text('# Adjudication handoff\n\n'+out['interpretation']+'\n\nPRIVATE contains text, prompts and token IDs; keep outside Git. SANITIZED is an aggregate allowlist. Labels are evaluator-only. Inspect missingness.json and state.json before resume; never repair an unsafe dispatch flag from counts. Review both bundles. No weights are bundled.\n')
    return out
