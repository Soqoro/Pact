"""Evaluator-only outcomes and aggregate allowlisted exports; no generation."""
from collections import Counter,defaultdict
from dataclasses import asdict
import math
from ..util import read_json,write_json,digest,canonical
from ..evaluation import rate
from ..studies.adjudication_metrics import paired,prefix_summary
from .contracts import Answer,ARMS,DEV_STYLES,FIT_STYLES,VERSION
from . import gates


def correct(a,gold):return a['status']=='ok' and a['answer']==gold


def fallback(raw,anchor):
    if raw['status']=='ok':return {**raw,'action':'KEEP' if raw.get('candidate_id')=='anchor' else 'SWITCH','selected_id':raw.get('candidate_id'),'fallback_reason':None}
    return {**asdict(anchor),'action':'KEEP','selected_id':'anchor','fallback_reason':'invalid_final_action'}


def evaluate_records(root,split):
    from .study import labeled_features,records,views
    tasks=labeled_features(root,split);rs={r['task']['task_id']:r for r in records(root,split)}
    baseline={r['task_id']:r for r in read_json(root/'baselines'/f'{split}.json')}
    models={arm:read_json(root/'gates'/f'{arm}.json') for arm in ARMS};thresholds=read_json(root/'threshold_selection.json');out=[]
    pool=read_json(root/'pools'/f'{split}.json')['rows'];target={(r['task_id'],r['style']):r for r in pool}
    for t in tasks:
        tid=t['task_id'];a=Answer(**t['anchor']);gold=t['gold'];T=a.status=='ok' and a.answer==gold
        _,vs,_=views(root,rs[tid]);b=baseline[tid]
        for view,rows in t['views'].items():
            peers=vs[view];O=any(p.status=='ok' and p.answer==gold for p in peers)
            outputs={};strict={};validity={}
            outputs['keep_anchor']={**asdict(a),'action':'KEEP','selected_id':'anchor','fallback_reason':None};strict['keep_anchor']=T
            for method,raw in [('anchor_inclusive_select',b['selection'][view]),('independent_reconsideration_6',b['independent_cycles'][2])]:
                outputs[method]=fallback(raw,a);strict[method]=correct(raw,gold)
                validity[method]=raw['status']=='ok'
            for arm,m in models.items():
                outputs[arm]=gates.decide(m,rows,a,thresholds[arm]['threshold'])
                # Strict policy action exists without generation; fallback parity is
                # separately reported, not a new sampled response.
                strict[arm]=correct(outputs[arm],gold)
            qualifiers=[r for r in rows if r['enabled']['restricted'] and r['restricted']['alternative_support']=='supported' and r['restricted']['baseline_support']=='contradicted']
            if len({r['answer'] for r in qualifiers})==1:
                r=min(qualifiers,key=lambda r:r['candidate_id']);outputs['restricted_rule']={'answer':r['answer'],'status':'ok','action':'SWITCH','selected_id':r['candidate_id'],'fallback_reason':None}
            else:outputs['restricted_rule']={**asdict(a),'action':'KEEP','selected_id':'anchor','fallback_reason':'no_unique_qualifying_answer'}
            strict['restricted_rule']=correct(outputs['restricted_rule'],gold)
            rewrite=target.get((tid,view));target_id=rewrite['target'] if rewrite else None
            target_answer=next((p.answer for p in peers if p.candidate_id==target_id),None)
            for method,answer in outputs.items():
                switched=answer['answer']!=a.answer and answer['status']=='ok';Y=correct(answer,gold)
                out.append({'task_id':tid,'group_id':t['group_id'],'dataset':rs[tid]['family'],'stratum':rs[tid]['stratum'], 'split':split,'view':view,'method':method,
                    'T':T,'O':O,'Y':Y,'answer':answer['answer'],'status':answer['status'],'switch':switched,'action':answer['action'],
                    'anchor_status':a.status,'strict_valid':validity.get(method,answer['status']=='ok'),'answer_equals_anchor':answer['answer']==a.answer,
                    'selected_id':answer.get('selected_id'),'strict_correct':strict[method],'fallback_reason':answer.get('fallback_reason'),
                    'anchor_hash':digest(asdict(a)),'correct_peer_hashes':[digest(asdict(p)) for p in peers if p.status=='ok' and p.answer==gold],
                    'structural_peer_only_loss':T and not O,'oracle_anchor_plus_peers':T or O,
                    'target_answer_adopted':target_answer is not None and answer['answer']==target_answer,
                    'required_checker_failure':method not in ('keep_anchor','anchor_inclusive_select','independent_reconsideration_6','metadata_augmented') and any(not r['enabled']['restricted' if method.startswith('restricted') else 'full'] for r in rows),
                    'target_candidate_adopted':target_id is not None and answer.get('selected_id')==target_id,
                    'logical_downstream_calls':0 if method in ('keep_anchor','metadata_augmented') else 1 if method=='anchor_inclusive_select' else 6 if method=='independent_reconsideration_6' else sum(1+int(r['extraction_status']=='ok') for r in rows),
                    'transition':('wrong_to_correct' if Y else 'wrong_to_wrong') if not T else 'correct_to_correct' if Y else 'correct_to_valid_wrong' if answer['status']=='ok' else 'correct_to_model_failure'})
    return out


def summarize(rows):
    n=len(rows);T=sum(r['T'] for r in rows);Y=sum(r['Y'] for r in rows);R=sum(not r['T'] and r['Y'] for r in rows);H=sum(r['T'] and not r['Y'] for r in rows)
    assert Y==T+R-H
    opportunities=[r for r in rows if not r['T'] and r['O']];switches=[r for r in rows if r['switch']]
    return {'tasks':n,'anchor_correct':T,'final_correct':Y,'accuracy':rate(Y,n),'rescue':R,'harm':H,'net':Y-T,
       'opportunity_rescue':rate(sum(r['Y'] for r in opportunities),len(opportunities)), 'unrealized_rescue':sum(not r['Y'] for r in opportunities),
       'unconditional_harm':rate(H,n),'conditional_harm':rate(H,T),'switch_rate':rate(len(switches),n),
       'switch_precision':rate(sum(r['Y'] for r in switches),len(switches)), 'structural_peer_only_losses':sum(r['structural_peer_only_loss'] for r in rows),
       'oracle_anchor_plus_peers':sum(r['oracle_anchor_plus_peers'] for r in rows),'strict_correct':sum(r['strict_correct'] for r in rows),'tasks_with_checker_format_failure':sum(r['required_checker_failure'] for r in rows),
       'strict_valid':sum(r['strict_valid'] for r in rows),'anchor_status':dict(Counter(r['anchor_status'] for r in rows)),
       'anchor_peer_coverage_quadrants':dict(Counter(f'T{int(r["T"])}_O{int(r["O"])}' for r in rows)),
       'target_answer_adoptions':sum(r['target_answer_adopted'] for r in rows),'target_candidate_adoptions':sum(r['target_candidate_adopted'] for r in rows),
       'fallback_reasons':dict(Counter(r['fallback_reason'] for r in rows if r['fallback_reason'])), 'transitions':dict(Counter(r['transition'] for r in rows)),
       'logical_downstream_calls':sum(r['logical_downstream_calls'] for r in rows),
       'paired_vs_anchor':paired([{**r,'clean':r['T'],'attacked':r['Y']} for r in rows])}


def report(root):
    from .study import inspect,records
    p,intents,results,unknown=inspect(root);tables={};robust={};attacks={};comparison={};common_clean={};states={};feature_diagnostics={}
    for split in ('source_development_holdout','transfer'):
        if split=='transfer' and not (root/'transfer.json').exists():states[split]={'status':'not_invoked'};continue
        rs=records(root,split);path=root/'evaluation'/f'{split}.json'
        if not path.exists():states[split]={'status':'not_evaluated','intended_tasks':len(rs),'scored_tasks':0};continue
        evaluation=read_json(path);rows=evaluation['rows']
        if digest(rows)!=evaluation['hash'] or evaluation['policy_hash']!=digest(read_json(root/'frozen_policy_receipt.json')):raise ValueError('Evaluation/policy changed')
        states[split]={'status':'complete','intended_tasks':len(rs),'scored_tasks':len({r['task_id'] for r in rows})}
        grouped=defaultdict(list)
        lookup={(r['task_id'],r['method'],r['view']):r for r in rows}
        for r in rows:grouped[(r['dataset'],r['method'],r['view'])].append(r)
        for k,group in grouped.items():tables['/'.join((split,*k))]=summarize(group)
        pool=read_json(root/'pools'/f'{split}.json')['rows'];bytask=defaultdict(list)
        for v in pool:bytask[v['task_id']].append(v)
        for dataset in sorted({r['family'] for r in rs}):
            for method in ('keep_anchor','anchor_inclusive_select','independent_reconsideration_6','restricted_rule',*ARMS):
                entries=[];attackrows=defaultdict(list);prefixrows=[]
                for rec in rs:
                    if rec['family']!=dataset:continue
                    tid=rec['task']['task_id'];clean=lookup[tid,method,'clean'];slots=[v for v in bytask[tid] if v['style']!='ordinary_rephrase' and v['target'] is not None]
                    if not slots:continue
                    observed=[]
                    for v in bytask[tid]:
                        if v['target'] is None:continue
                        changed=lookup.get((tid,method,v['style']));attackrows[v['style']].append({'group_id':rec['group_id'],'stratum':rec['stratum'],'clean':clean['Y'],'attacked':changed['Y'] if changed else None})
                        if v['style']!='ordinary_rephrase':observed.append(changed['Y'] if changed else None)
                    complete=all(x is not None for x in observed);known_failure=not clean['Y'] or any(x is False for x in observed)
                    entries.append({'complete':complete,'lower':clean['Y'] and complete and all(observed),'upper':not known_failure,'observed_success':clean['Y'] and all(x for x in observed if x is not None)})
                    order=rec.get('attack_order',list(DEV_STYLES[:2]))
                    prefixrows.append({'group_id':rec['group_id'],'stratum':rec['stratum'],'clean':clean['Y'],
                        'values':[lookup[tid,method,v]['Y'] if (tid,method,v) in lookup else None for v in order]})
                key='/'.join((split,dataset,method));robust[key]={'eligible_tasks':len(entries),'complete_prefix_tasks':sum(x['complete'] for x in entries),
                   'complete_robust':sum(x['lower'] for x in entries),'full_eligible_lower':sum(x['lower'] for x in entries),'full_eligible_upper':sum(x['upper'] for x in entries),
                   'observed_joint_success':sum(x['observed_success'] for x in entries),'observed_joint_accuracy':rate(sum(x['observed_success'] for x in entries),len(entries)),
                   'complete_prefix_accuracy':rate(sum(x['lower'] for x in entries),sum(x['complete'] for x in entries)),
                   'bounds_are_not_confidence_intervals':True,'ordinary_rephrase_excluded':True}
                robust[key]['fixed_prefixes']={k:v for k,v in prefix_summary(prefixrows).items() if k!='4' or split=='transfer'}
                for style,ar in attackrows.items():
                    available=[x for x in ar if x['attacked'] is not None];cc=[x for x in available if x['clean']]
                    attacks[key+'/'+style]={'eligible':len(ar),'observed':len(available),'missing':len(ar)-len(available),'clean_conditional_flips':rate(sum(not x['attacked'] for x in cc),len(cc)),'paired':paired(ar)}
            for left,right in [('full_clean','restricted_clean'),('full_augmented','restricted_augmented'),('restricted_clean','restricted_augmented'),('metadata_augmented','restricted_augmented'),('anchor_inclusive_select','restricted_augmented'),('independent_reconsideration_6','restricted_augmented'),('keep_anchor','restricted_augmented')]:
                rr=[]
                for row in rows:
                    if row['dataset']!=dataset or row['method']!=left:continue
                    other=lookup[row['task_id'],right,row['view']]
                    rr.append({**row,'clean':row['Y'],'attacked':other['Y']})
                # Bootstrap groups retain all views; clean and each style also appear
                # in the tables, this aggregate is explicitly equal observed-row weight.
                comparison['/'.join((split,dataset,left,right))]=paired(rr)
                # Compare attacks on the SAME tasks clean-correct under both arms.
                for style in sorted({r['view'] for r in rows if r['view']!='clean'}):
                    shared=[];eligible=0
                    for rec in rs:
                        if rec['family']!=dataset:continue
                        tid=rec['task']['task_id']
                        if not (lookup[tid,left,'clean']['Y'] and lookup[tid,right,'clean']['Y']):continue
                        if not any(v['style']==style and v['target'] is not None for v in bytask[tid]):continue
                        eligible+=1;l=lookup.get((tid,left,style));r=lookup.get((tid,right,style))
                        if l is not None and r is not None:shared.append({'group_id':rec['group_id'],'stratum':rec['stratum'],'clean':l['Y'],'attacked':r['Y']})
                    common_clean['/'.join((split,dataset,left,right,style))]={'joint_clean_eligible':eligible,'observed':len(shared),'missing':eligible-len(shared),
                        'left_flips':sum(not r['clean'] for r in shared),'right_flips':sum(not r['attacked'] for r in shared),'paired':paired(shared)}
        f=read_json(root/'features'/f'{split}.json')['rows'];rowsf=[r for t in f for rs2 in t['views'].values() for r in rs2]
        diag={'candidate_view_rows':len(rowsf),'missing_references':sum(not r['references'] for r in rowsf),'extract_status':dict(Counter(r['extraction_status'] for r in rowsf)),
              'full_restricted_verdict_agreement':rate(sum(r['full']['comparative_verdict']==r['restricted']['comparative_verdict'] for r in rowsf),len(rowsf)),
              'disabled':{k:sum(not r['enabled'][k] for r in rowsf) for k in ('full','restricted')},
              'evidence_basis':{k:dict(Counter(r[k]['evidence_basis'] for r in rowsf)) for k in ('full','restricted')},
              'logical_collection_paths':sum(len(r['evidence']) for r in rowsf),'unique_check_calls':len({key for r in rowsf for key in r['evidence'].values()}),
              'reused_paths':sum(len(r['evidence']) for r in rowsf)-len({key for r in rowsf for key in r['evidence'].values()})}
        # Probability scoring is evaluator-only, never a threshold selection input.
        from .study import labeled_features
        labeled=labeled_features(root,split);score={};basis_outcomes=defaultdict(list)
        for t in labeled:
            for rr in t['views'].values():
                for r in rr:
                    for mode in ('full','restricted'):basis_outcomes[mode+'/'+r[mode]['evidence_basis']].append(r['target'])
        diag['replacement_targets_by_evidence_basis']={k:dict(Counter(str(t) for t in ts)) for k,ts in basis_outcomes.items()}
        diag['basis_unit']='candidate/view rows; correlated, not independent tasks'
        for arm in ARMS:
            m=read_json(root/'gates'/f'{arm}.json');layout='metadata' if arm=='metadata_augmented' else 'restricted' if arm.startswith('restricted') else 'full'
            values=[]
            for t in labeled:
                for rr in t['views'].values():
                    for r in rr:
                        probs=gates.probability(m,r[layout]);y=r['target']+1
                        values.append((-math.log(max(probs[y],1e-300)),sum((p-int(j==y))**2 for j,p in enumerate(probs))))
            score[arm]={'candidate_rows':len(values),'mean_nll':sum(v[0] for v in values)/len(values) if values else None,'mean_brier':sum(v[1] for v in values)/len(values) if values else None,'diagnostic_only':True}
        diag['probability_scoring']=score;feature_diagnostics[split]=diag
    roles=Counter(i['identity']['role'] for i in intents.values());buckets=Counter(i['split'] for i in intents.values())
    out={'version':VERSION,'fixture':p['fixture'],'scientific_status':'mock_only' if p['fixture'] else 'bounded_development_learning_study',
      'primary':'restricted_augmented','stages':states,'tables':tables,'robust_pool':robust,'attack_comparisons':attacks,'paired_gate_comparisons':comparison,'common_clean_attack_comparisons':common_clean,'feature_diagnostics':feature_diagnostics,
      'accounting':{'attempted':len(intents),'committed':len(results),'unresolved':len(unknown),'reserved_output_tokens':len(intents)*512,
        'input_tokens':sum(r['call']['input_tokens'] for r in results.values()),'output_tokens':sum(r['call']['output_tokens'] for r in results.values()),'by_role':dict(roles),'by_split':dict(buckets),
        'llm_optimizer_updates':0,'teacher_forced_forwards':0,'gate_fits_attempted':len(list((root/'fit-intents').glob('*.json'))),'compute_units':None,
        'budgets':p['budgets'],'total_call_ceiling':p['total_calls'],
        'cpu_fits':{f.stem:read_json(f) for f in (root/'fit_resources').glob('*.json')},
        'source_cost_policy':'Four new source calls/task in core; zero new source calls in transfer. Per-method downstream logical costs are separate from union collection.'},
      'recovery_safe':read_json(root/'state.json')['recovery_safe'],'formal_risk_certificate':False,'human_review_and_spans':'deferred',
      'limitations':'Development outcomes; same-model checks are unverified. Exact references are not proof. Missing variants are not safe outcomes. No full PACT efficacy or final-test claim.'}
    if (root/'fit_diagnostics.json').exists():out['fit_diagnostics']=read_json(root/'fit_diagnostics.json')
    out['fit_support']={a:{k:read_json(root/'gates'/f'{a}.json')[k] for k in ('class_rows','clean_candidate_classes','task_class_support','fit_groups')} for a in ARMS if (root/'gates'/f'{a}.json').exists()}
    resource_rows=[read_json(f) for f in (root/'resources').glob('*.json')]
    out['model_resources']={k:{'loads':sum(r['model']==k for r in resource_rows),
        **{field:sum(r.get(field,0) or 0 for r in resource_rows if r['model']==k) for field in ('model_load_seconds','download_seconds','file_hash_seconds','materialization_seconds')},
        **{field:max((r[field] for r in resource_rows if r['model']==k and r.get(field) is not None),default=None) for field in ('peak_allocated_bytes','peak_reserved_bytes','model_load_allocated_bytes')}} for k in ('Q','L','M','R')}
    if (root/'threshold_selection.json').exists():out['thresholds']={a:{k:v for k,v in t.items() if k not in ('model_hash','tuning_hash')} for a,t in read_json(root/'threshold_selection.json').items()}
    write_json(root/'summary.json',out)
    for name,value in [('rescue_harm_tables',tables),('robust_pool_results',robust),('strict_and_fallback_failures',{k:{field:v[field] for field in ('strict_correct','fallback_reasons','transitions','tasks_with_checker_format_failure')} for k,v in tables.items()}),('cost_and_reuse',{'accounting':out['accounting'],'feature_diagnostics':feature_diagnostics}),('reference_integrity',{'exact_spans_not_proof':True,'by_split':{k:{f:v[f] for f in ('candidate_view_rows','missing_references','extract_status')} for k,v in feature_diagnostics.items()}})]:write_json(root/(name+'.json'),value)
    for split in states:
        (root/f'{split}_report.md').write_text('# Selective correction — '+split+'\n\n'+out['limitations']+'\n\n```json\n'+json_safe({'status':states[split],'tables':{k:v for k,v in tables.items() if k.startswith(split+'/')}})+'\n```\n')
    (root/'CODEX_HANDOFF.md').write_text('# Selective correction handoff\n\nReturn matching PRIVATE and SANITIZED bundles with hashes. PRIVATE contains source text, labels, gates and token IDs; keep outside Git. No result authorizes another run.\n')
    return out


def json_safe(value):
    import json
    return json.dumps(value,indent=2,ensure_ascii=True).replace('<','\\u003c').replace('>','\\u003e')
