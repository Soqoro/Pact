"""Task-group paired outcomes; missing infrastructure is never model failure."""
from collections import Counter,defaultdict
from ...util import digest,read_json,write_json
from ...studies.forensics import save_lines
from .. import contracts as c,study
from .engine import output


def interval(rows):
    from ...selective.diagnostics import clustered_interval
    counts=Counter(f for f,g,v in rows)
    # Existing stratified task bootstrap, scaled to equal source weight.
    scaled=[(f,g,v*len(rows)/(len(counts)*counts[f])) for f,g,v in rows] if rows else []
    return clustered_interval(scaled)


def summarize(rows):
    observed=[r for r in rows if r['final'] is not None];n=len(rows);missing=n-len(observed)
    correct=sum(r['final'] for r in observed)
    sources=sorted({r['family'] for r in rows})
    per={f:{'intended':sum(r['family']==f for r in rows),'observed':sum(r['family']==f for r in observed),'correct':sum(r['final'] for r in observed if r['family']==f)} for f in sources}
    equal=sum(v['correct']/v['observed'] for v in per.values())/len(per) if per and all(v['observed'] for v in per.values()) else None
    lowers=[v['correct']/v['intended'] for v in per.values()];uppers=[(v['correct']+v['intended']-v['observed'])/v['intended'] for v in per.values()]
    initial=[r for r in rows if r['condition']=='clean' and r['initial'] is not None]
    complete=[r for r in observed if r['initial'] is not None and r['revised'] is not None]
    with_coverage=sum(r['final'] and any(r['initial']) for r in complete);without=sum(r['final'] and not any(r['initial']) for r in complete)
    assert sum(r['final'] for r in complete)==with_coverage+without
    strata={}
    for st in ('hold_conflict','repair_available','retention','wrong_without_correct_peer'):
        cells=[(r,s) for r in complete for s,x in enumerate(r['strata']) if x==st]
        strata[st]={'support':len(cells),'correct_revision':sum(r['revised'][s] for r,s in cells),
                    'invalid_own_support':sum(r['private_status'][s]!='ok' for r,s in cells)}
    return {'intended':n,'observed':len(observed),'missing':missing,'final_correct':correct,
            'by_source':per,'equal_source_accuracy_observed':equal,
            'full_population_equal_source_bounds':[sum(lowers)/len(lowers),sum(uppers)/len(uppers)] if lowers else None,
            'paired_unit':'task group','accuracy_interval':interval([(r['family'],r['group_id'],float(r['final'])) for r in observed]),
            'status_counts':dict(Counter(r['final_status'] for r in rows)),
            'initial_correct_by_family':{f:sum(r['initial'][r['binding'].index(f)] for r in initial) for f in c.FAMILIES},
            'private_observed_tasks':len(initial),'initial_coverage':sum(any(r['initial']) for r in initial),
            'coverage_gain_over_best_member':sum(any(r['initial']) for r in initial)-max([sum(r['initial'][r['binding'].index(f)] for r in initial) for f in c.FAMILIES],default=0),
            'n0_counts':dict(Counter(sum(r['initial']) for r in complete)),
            'n1_counts':dict(Counter(sum(r['revised']) for r in complete)),
            'n0_n1':dict(Counter(f"{sum(r['initial'])}->{sum(r['revised'])}" for r in complete)),
            'harmful_revisions':sum(a and not b for r in complete for a,b in zip(r['initial'],r['revised'])),
            'newly_correct_revisions':sum(not a and b for r in complete for a,b in zip(r['initial'],r['revised'])),
            'erasure':sum(any(r['initial']) and not any(r['revised']) for r in complete),
            'utilization_support':sum(any(r['initial']) for r in complete),
            'utilized':with_coverage,
            'new_coverage':sum(not any(r['initial']) and any(r['revised']) for r in complete),
            'readout_loss':sum(any(r['revised']) and not r['final'] for r in complete),
            'final_construction':sum(not any(r['revised']) and r['final'] for r in complete),
            'final_correct_with_initial_coverage':with_coverage,'final_correct_without_initial_coverage':without,
            'on_policy_strata':strata,'conditional_populations_differ_by_arm':True}


def paired(rows):
    out={}
    for split in ('validation','source_evaluation'):
        for cond in ('clean','exchange'):
            for a,b in ((c.ARMS[0],c.ARMS[1]),(c.ARMS[0],c.ARMS[2]),(c.ARMS[1],c.ARMS[2])):
                left={r['task_id']:r for r in rows if r['split']==split and r['condition']==cond and r['arm']==a}
                right={r['task_id']:r for r in rows if r['split']==split and r['condition']==cond and r['arm']==b}
                pairs=[(x,right[t]) for t,x in left.items() if t in right and x['final'] is not None and right[t]['final'] is not None]
                ds=[(x['family'],x['group_id'],int(y['final'])-int(x['final'])) for x,y in pairs]
                sources=sorted({r['family'] for r in left.values()})
                point=sum(sum(v for f,g,v in ds if f==s)/sum(f==s for f,g,v in ds) for s in sources)/len(sources) if sources and all(any(f==s for f,g,v in ds) for s in sources) else None
                bounds=[]
                for s in sources:
                    n=sum(r['family']==s for r in left.values());observed=[v for f,g,v in ds if f==s];m=n-len(observed)
                    bounds.append([(sum(observed)-m)/n,(sum(observed)+m)/n])
                out[f'{split}/{cond}/{b}-minus-{a}']={'paired_tasks':len(pairs),'intended':len(left),'gains':sum(not x['final'] and y['final'] for x,y in pairs),'losses':sum(x['final'] and not y['final'] for x,y in pairs),
                    'equal_source_difference':point,'interval':interval(ds),'full_population_difference_bounds':[sum(v[i] for v in bounds)/len(bounds) for i in (0,1)] if bounds else None,
                    'incomplete_intersection_selection_risk':len(pairs)!=len(left)}
    return out


def interaction(rows):
    out={}
    for cond in ('clean','exchange'):
        for family in (*c.FAMILIES,'equal_receivers'):
            selected=[r for r in rows if r['condition']==cond and (family=='equal_receivers' or r['receiver_family']==family)]
            by={(r['task_id'],r['slot'],r['arm'],r['withheld']):r for r in selected}
            cells=[]
            for t,s in sorted({(r['task_id'],r['slot']) for r in selected}):
                vals=[by.get((t,s,a,w),{}).get('correct') for a in c.ARMS[1:] for w in (False,True)]
                if any(v is None for v in vals):continue
                ip,iw,jp,jw=map(int,vals)
                ref=by[t,s,c.ARMS[1],False]
                cells.append({'family':ref['family'],'group_id':ref['group_id'],'stratum':ref['common_stratum'],
                              'ip':ip,'iw':iw,'jp':jp,'jw':jw,'interaction':(jp-jw)-(ip-iw)})
            group=defaultdict(list)
            for x in cells:group[x['family'],x['group_id']].append(x)
            task_rows=[(f,g,sum(x['interaction'] for x in xs)/len(xs)) for (f,g),xs in group.items()]
            source_groups=defaultdict(list)
            for (f,g),xs in group.items():source_groups[f].append({k:sum(x[k] for x in xs)/len(xs) for k in ('ip','iw','jp','jw','interaction')})
            mean=lambda k: sum(sum(x[k] for x in xs)/len(xs) for xs in source_groups.values())/len(source_groups) if source_groups else None
            means={k:mean(k) for k in ('ip','iw','jp','jw','interaction')}
            frozen={}
            for w in (False,True):
                xs=[r for r in selected if r['arm']==c.ARMS[0] and r['withheld']==w and r['correct'] is not None]
                fs=sorted({r['family'] for r in xs})
                frozen['withheld' if w else 'present']={'observed':len(xs),'accuracy':sum(sum(r['correct'] for r in xs if r['family']==f)/sum(r['family']==f for r in xs) for f in fs)/len(fs) if fs else None}
            out[cond+'/'+family]={'paired_receivers':len(cells),'paired_tasks':len(group),'intended_receivers':len({(r['task_id'],r['slot']) for r in selected}),
                'frozen':frozen,'accuracies':{k:means[k] for k in ('ip','iw','jp','jw')},'interaction':means['interaction'],'interval':interval(task_rows),
                'present_gain':means['jp']-means['ip'] if cells else None,'withheld_gain':means['jw']-means['iw'] if cells else None,
                'common_strata':dict(Counter(x['stratum'] for x in cells)),
                'interpretation':'Positive interaction alone may reflect worse joint withheld performance; not efficacy.'}
    return out


def report(root):
    p=read_json(root/'plan.json');rows=[];availability=[];fixed=[]
    attempted_attacks={v['logical'][1] for path in (root/'intents').glob('*.json') if (v:=read_json(path))['component']=='attack'}
    for split in ('validation','source_evaluation'):
        for r in study.records(p,split):
            tid=study.tid(r);gold=p['source']['labels'][tid];ap=root/'attacks'/f'{digest(tid)}.json'
            attack=read_json(ap) if ap.exists() else {'status':'attempted_unresolved' if tid in attempted_attacks else 'never_attempted','accepted':False}
            availability.append({'task_id':tid,'split':split,'group_id':r['group_id'],'attack_status':attack['status']})
            for arm in c.ARMS:
                private=[output(root,[arm,split,tid,'private',s]) for s in range(3)]
                bank=[v['packet'] for v in private] if all(v is not None for v in private) else None
                for cond in ('clean','exchange'):
                    final=output(root,[arm,split,tid,cond,'final']);revs=[output(root,[arm,split,tid,cond,'revision',s]) for s in range(3)]
                    rows.append({'task_id':tid,'group_id':r['group_id'],'family':r['family'],'binding':r['binding'],'split':split,'condition':cond,'arm':arm,
                        'initial':[v['answer']==gold and v['status']=='ok' for v in bank] if bank else None,
                        'private_status':[v['status'] for v in bank] if bank else None,
                        'revised':[v['packet']['status']=='ok' and v['packet']['answer']==gold for v in revs] if all(v is not None for v in revs) else None,
                        'final':final['packet']['status']=='ok' and final['packet']['answer']==gold if final else None,
                        'final_status':final['packet']['status'] if final else ('attack_'+attack['status'] if cond=='exchange' and not attack['accepted'] else 'infrastructure_missing'),
                        'strata':[c.stratum(bank,s,gold,attack if cond=='exchange' else None) for s in range(3)] if bank and (cond=='clean' or attack['accepted']) else None})
            if split=='validation' and tid in p['peer_use']:
                private=[output(root,[c.ARMS[0],split,tid,'private',s]) for s in range(3)]
                bank=[v['packet'] for v in private] if all(v is not None for v in private) else None
                for cond in ('clean','exchange'):
                    for arm in c.ARMS:
                        for slot,f in enumerate(r['binding']):
                            for withheld in (False,True):
                                v=output(root,['fixed',arm,tid,cond,slot,withheld])
                                fixed.append({'task_id':tid,'group_id':r['group_id'],'family':r['family'],'receiver_family':f,'slot':slot,'arm':arm,'condition':cond,'withheld':withheld,
                                    'correct':v['packet']['status']=='ok' and v['packet']['answer']==gold if v else None,
                                    'common_stratum':c.stratum(bank,slot,gold,attack if cond=='exchange' else None) if bank and (cond=='clean' or attack['accepted']) else None,
                                    'invalid_own':bank[slot]['status']!='ok' if bank else None})
    # Derived views can grow after another explicitly invoked stage; raw shards stay immutable.
    def lines(name,values):
        from ...util import canonical,atomic_write
        atomic_write(root/name,''.join(canonical(v)+'\n' for v in values))
    lines('live_per_task.private.jsonl',rows);lines('fixed_history_per_receiver.private.jsonl',fixed)
    write_json(root/'source_and_attack_availability.json',availability)
    metrics={f'{split}/{arm}/{cond}':summarize([r for r in rows if r['split']==split and r['arm']==arm and r['condition']==cond]) for split in ('validation','source_evaluation') for arm in c.ARMS for cond in ('clean','exchange')}
    write_json(root/'paired_metrics.json',paired(rows));write_json(root/'peer_access_interaction.json',interaction(fixed))
    intents={f.stem:read_json(f) for f in (root/'intents').glob('*.json')}
    from ...artifacts import ShardStore
    results=ShardStore(root/'calls').records();results=list(results)
    budget=read_json(root/'reconciled_generation_budget.json')
    accounting={'new_attempts':len(intents),'new_committed':len(results),'unresolved':len(set(intents)-{r['work_id'] for r in results}),
        'component_attempts':dict(Counter(v['component'] for v in intents.values())), 'reserved_output_tokens':len(intents)*512,
        'input_tokens':sum(v['call']['input_tokens'] for v in results),'output_tokens':sum(v['call']['output_tokens'] for v in results),
        'inherited_attempts':budget['verified_ancestor_attempts'],'optimizer_updates':0,'training_forwards':0,'teacher_forced_forwards':0,
        'synthetic_attempts':len(list((root/'synthetic/intents').glob('*.json'))),'compute_units':None,
        'reuse_links':sum(read_json(f)['origin']=='ancestor' for f in (root/'links').glob('*.json'))}
    if p.get('amendment_hash'):
        accounting.update(budget_ownership='approved_additional_envelope',
            new_generation_cap=budget['new_attempt_cap'],
            historical_accounting=budget['historical_accounting'],
            inherited_verification_forwards=16,amendment_hash=p['amendment_hash'],
            possible_repeats_of_unrecoverable_history=True)
    accounting['resource_records']=[read_json(f) for f in sorted((root/'resources').glob('*.json'))]
    accounting['context_incompatibilities']=len(list((root/'incompatibilities').glob('*.json')))
    accounting['format_status_counts']=dict(Counter(v['packet']['status'] for v in results))
    accounting['logical_links']=len(list((root/'links').glob('*.json')))
    accounting['canonical_child_reuses']=accounting['logical_links']-accounting['reuse_links']-len(results)
    write_json(root/'runtime_and_cost_report.json',accounting)
    out={'scientific_status':'mock_only' if p['fixture'] else 'development_evaluation','accounting':accounting,'live':metrics,
        'stage_status':{s:(root/'stages'/f'{s}.json').exists() for s in ('smoke','validation','source_evaluation','fixed_history')},
        'all_outputs_observed':all(r['final'] is not None for r in rows) and all(r['correct'] is not None for r in fixed),
        'full_pact_executed':False,'historical_unknown_step_preserved':True}
    write_json(root/'summary.json',out);return out
