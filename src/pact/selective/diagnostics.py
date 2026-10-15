"""Saved-gate diagnostics only: no fitting, model execution or policy selection."""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import html
import math
from pathlib import Path
import tempfile
import time

import numpy as np
from ..util import canonical, digest, read_json, write_json, file_hash, atomic_write
from ..studies.forensics import private_root, save_lines
from ..studies.semantic_review import package
from . import gates as g, contracts as c, study as s
from .closed_parent import import_parent, verified_parent, validate, cached_reads

RUN_ID = 'pact-gate-diagnostics-001'
COSTS = (0., .5, 1., 2.)
TAUS = (-2., -1., -.5, -.25, -.1, 0., .05, .1, .2, .35, .5, .75, 'KEEP_ONLY')
SEED = 20261015


def layout(model):
    return 'metadata' if model['arm']=='metadata_augmented' else 'restricted' if model['arm'].startswith('restricted') else 'full'


def scores(model, features):
    g.validate_model(model)
    if model['class_order'] != ['harm', 'neutral', 'improve']:
        raise ValueError('Class order mismatch')
    f = (np.asarray(g.encode(features, model['arm']=='metadata_augmented'))-model['mean'])/model['scale']
    z = np.asarray(model['coefficients'])@f + model['intercept']
    if not np.isfinite(z).all():
        raise ValueError('Nonfinite logits')
    exp = np.exp(z-z.max()); p = exp/exp.sum()
    if not np.allclose(p, g.probability(model, features), rtol=0, atol=1e-14):
        raise ValueError('Independent probability reconstruction mismatch')
    margin = float(z[2]-z[0]-math.log(2))
    u = float(p[2]-2*p[0])
    # Report finite precision underflow/cancellation explicitly, never change utilities.
    numeric_boundary = abs(u)<1e-14 or abs(margin)<1e-14
    if not numeric_boundary and (u>0)!=(margin>0):
        raise ValueError('Class/cost algebra mismatch')
    return {'logits':z.tolist(), 'probabilities':p.tolist(), 'u2':u,
            'log_odds_IH':float(z[2]-z[0]), 'margin_to_cost_boundary':margin,
            'numeric_boundary':numeric_boundary}


def weighted_rows(tasks, arm):
    """Same task/view/alternative reduction on each split, without relabeling splits."""
    out=[]
    for t in tasks:
        attacks=[(v,rs) for v,rs in t['views'].items() if v!='clean']
        chosen=[('clean',t['views']['clean'],1.)]
        if not arm.endswith('_clean') and attacks:
            chosen=[('clean',t['views']['clean'],.5)]+[(v,rs,.5/len(attacks)) for v,rs in attacks]
        for view, rs, mass in chosen:
            if {-1,1} <= {r['target'] for r in rs}:
                raise ValueError('Improve and harm cannot coexist under the same fixed anchor')
            for r in rs:
                out.append((t,view,r,mass/len(tasks)/len(rs)))
    return out


def rank_metrics(values, positive, weights, groups):
    """Weighted ROC with half-credit ties; AP aggregates a whole tied score block."""
    pos=sum(w for w,y in zip(weights,positive) if y);neg=sum(weights)-pos
    support={'rows':len(values),'groups':len(set(groups)), 'positive_mass':pos,'negative_mass':neg,
             'prevalence':pos/(pos+neg) if pos+neg else None}
    if not pos or not neg or len(set(groups))<2:
        return {**support,'roc_auc':None,'average_precision':None,'undefined':'both classes and >=2 distinct groups required'}
    blocks=defaultdict(lambda:[0.,0.])
    for value,y,w in zip(values,positive,weights):blocks[float(value)][0 if y else 1]+=w
    below=area=0.
    for _,(p,n) in sorted(blocks.items()):area+=p*(below+n*.5);below+=n
    tp=fp=ap=0.
    for _,(p,n) in sorted(blocks.items(),reverse=True):
        tp+=p;fp+=n;ap+=p/pos*tp/(tp+fp)
    return {**support,'roc_auc':area/(pos*neg),'average_precision':ap,'undefined':None}


def quantiles(values, weights=None):
    if not values:return {'n':0,'quantiles':None}
    weights = np.ones(len(values)) if weights is None else np.asarray(weights)
    ix=np.argsort(values,kind='stable');v=np.asarray(values)[ix];w=weights[ix]
    if not w.sum():return {'n':len(values),'quantiles':None}
    cumulative=np.cumsum(w)/w.sum()
    return {'n':len(values),'quantiles':{str(q):float(v[min(np.searchsorted(cumulative,q),len(v)-1)]) for q in (0,.05,.25,.5,.75,.95,1)}}


def clustered_interval(rows, replicates=500):
    """Input one descriptive scalar per task; dataset-stratified task resampling."""
    if not 0<=replicates<=2000:raise ValueError('Bootstrap cap')
    strata=defaultdict(list)
    for family,group,value in rows:strata[family].append((group,value))
    if any(len({g for g,v in rs})!=len(rs) for rs in strata.values()):raise ValueError('One row per task required')
    if sum(len(rs) for rs in strata.values())<2 or not replicates:return None
    rng=np.random.default_rng(SEED);samples=[]
    for _ in range(replicates):
        values=[]
        for rs in strata.values():values.extend(rs[i][1] for i in rng.integers(len(rs),size=len(rs)))
        samples.append(float(np.mean(values)))
    return {'lower':float(np.quantile(samples,.025)),'upper':float(np.quantile(samples,.975)),
            'unit':'task/group, all views together, stratified by dataset','seed':SEED,'replicates':replicates,'descriptive_only':True}


def select(model, rows, anchor, cost, tau, cache):
    if model['keep_only'] or tau=='KEEP_ONLY':return None
    active=[r for r in rows if layout(model)=='metadata' or r['enabled'][layout(model)]]
    ranked=[]
    for r in active:
        p=cache[digest(r[layout(model)])]['probabilities'];u=p[2]-cost*p[0]
        if u>tau:ranked.append((u,r['candidate_id'],r))
    return sorted(ranked,key=lambda x:(-x[0],x[1]))[0][2] if ranked else None


def sensitivity(model, tasks, cache):
    if any(t['split'] not in c.SPLITS[:2] for t in tasks):raise ValueError('Sensitivity forbids source-development labels')
    out=[]
    for cost in COSTS:
        for tau in TAUS:
            rescues=harms=pool_harm=switches=switched_tasks=joint=complete=missing=0
            for t in tasks:
                a=t['anchor'];T=a['status']=='ok' and a['answer']==t['gold'];ys={};actions=[]
                for view,rs in t['views'].items():
                    selected=select(model,rs,a,cost,tau,cache);actions.append(selected is not None)
                    ys[view]=selected['answer']==t['gold'] if selected else T
                rescues+=int(not T and ys['clean']);harms+=int(T and not ys['clean'])
                pool_harm+=int(T and not all(ys.values()));joint+=int(all(ys.values()))
                switches+=sum(actions);switched_tasks+=int(any(actions));complete+=int(t.get('missing_variants',0)==0);missing+=t.get('missing_variants',0)
            n=len(tasks)
            out.append({'lambda':cost,'threshold':tau,'tasks':n,'switches':switches,'switched_tasks':switched_tasks,
                        'clean_rescues':rescues,'clean_harms':harms,'R_minus_H':rescues-harms,'R_minus_lambda_H':rescues-cost*harms,
                        'observed_pool_harm':pool_harm,'joint_observed_success':joint,'complete_pool_tasks':complete,
                        'missing_variants':missing,'original_5pct_screen_reference':bool(n and harms/n<=.05 and pool_harm/n<=.05)})
    return {'diagnostic_only':True,'policy_selection_authorized':False,'grid':out}


def analyze(root, mock=False):
    private_root(root,mock)
    parent=verified_parent(root,mock)
    with cached_reads():
        # Receipt verified all bytes; repeat substantive validation without rebuilding raw features again.
        p,tasks,models,thresholds=validate(parent,mock,reconstruct=False)
        records={r['task']['task_id']:r for r in p['records']}
        cache={};reconstruction={};support={};signals={};collisions={};checks=defaultdict(Counter);grids={};decomposition={};opportunities={}
        private_scores=[]
        for arm,m in models.items():
            feature_cache={digest(r[layout(m)]):scores(m,r[layout(m)]) for ts in tasks.values() for t in ts for rs in t['views'].values() for r in rs}
            cache[arm]=feature_cache
            rows,w,_=g.fit_rows(tasks['fit'],arm)
            X=np.asarray([g.encode(r[layout(m)],arm=='metadata_augmented') for r in rows]).reshape(-1,len(m['mean']))
            X=(X-m['mean'])/m['scale'];y=np.asarray([r['target']+1 for r in rows]);theta=np.r_[np.asarray(m['coefficients']).ravel(),m['intercept']]
            if m['diagnostics'].get('trained'):
                loss,gradient=g.objective(theta,X,y,np.asarray(w),m['l2'])
                if abs(loss-m['diagnostics']['loss'])>1e-9 or abs(float(np.max(np.abs(gradient)))-m['diagnostics']['gradient_inf'])>1e-9:
                    raise ValueError('Saved objective reconstruction mismatch')
                reconstruction[arm]={'loss':loss,'gradient_inf':float(np.max(np.abs(gradient))),'model_hash':m['model_hash'],'transform_hash':digest([m['mean'],m['scale']]),'probability_rows':len(feature_cache)}
            else:reconstruction[arm]={'not_trained':True,'reason':m['diagnostics']['status']}
            mass=[sum(weight for r,weight in zip(rows,w) if r['target']==k) for k in (-1,0,1)]
            prior=[v/sum(mass) if sum(mass) else 0 for v in mass]
            support[arm]={'fit_effective_class_mass':mass,'fit_weight_sum':sum(mass),'descriptive_prior_probabilities':prior,
                          'zero_prior_classes':[k-1 for k,v in enumerate(prior) if not v], 'not_a_sixth_gate':True,'groups':{}}
            for split,ts in tasks.items():
                wr=weighted_rows(ts,arm);vectors=defaultdict(list);byclass=defaultdict(list)
                for t,view,r,weight in wr:
                    family=records[t['task_id']]['family'];active=layout(m)=='metadata' or r['enabled'][layout(m)]
                    key='/'.join([split,family,'clean' if view=='clean' else 'augmented', 'active' if active else 'disabled'])
                    support[arm]['groups'].setdefault(key,[]).append((r['target'],weight,t['group_id']))
                    v=feature_cache[digest(r[layout(m)])];byclass[r['target']].append((t,r,weight,v))
                    vectors[tuple(g.encode(r[layout(m)],arm=='metadata_augmented'))].append((r['target'],weight,t['group_id']))
                    private_scores.append({'arm':arm,'split':split,'task_id':t['task_id'],'view':view,'candidate_id':r['candidate_id'],'target':r['target'],'active':active,'weight':weight,**v})
                hit=[rs for rs in vectors.values() if len({r[0] for r in rs})>1]
                collisions[arm+'/'+split]={'exact_cross_label_vectors':len(hit),'rows':sum(len(rs) for rs in hit),
                    'weight':sum(r[1] for rs in hit for r in rs),'groups':len({r[2] for rs in hit for r in rs}),
                    'class_rows':dict(Counter(str(r[0]) for rs in hit for r in rs)), 'no_quantization':True,'representation_impossibility_claim':False}
                if split not in c.SPLITS[:2]:continue
                grids[arm+'/'+split]=sensitivity(m,ts,feature_cache)
                distributions={}
                for target,rs in byclass.items():
                    distributions[str(target)]={key:quantiles([v['probabilities'][idx] if idx is not None else v[key] for t,r,w,v in rs],[w for t,r,w,v in rs]) for key,idx in [('p_improve',2),('p_harm',0),('u2',None),('log_odds_IH',None)]}
                allrows=[x for rs in byclass.values() for x in rs];total=sum(x[2] for x in allrows)
                logscore=brier=priorlog=priorbrier=0.;rank={}
                for t,r,w,v in allrows:
                    prob=np.asarray(v['probabilities']);target=r['target']+1;one=np.eye(3)[target]
                    logscore-=w*math.log(max(prob[target],1e-15));brier+=w*float(np.sum((prob-one)**2))
                    priorlog-=w*math.log(max(prior[target],1e-15));priorbrier+=w*float(np.sum((np.asarray(prior)-one)**2))
                for label,eligible in [('improve_vs_harm',[x for x in allrows if x[1]['target']!=0]),('improve_vs_nonimprove',allrows)]:
                    rank[label]={metric:rank_metrics([v[metric] for t,r,w,v in eligible],[r['target']==1 for t,r,w,v in eligible],[w for t,r,w,v in eligible],[t['group_id'] for t,r,w,v in eligible]) for metric in ('u2','log_odds_IH')}
                top=[];task_losses=defaultdict(list)
                for t,view,rs in ((t,v,rs) for t in ts for v,rs in t['views'].items()):
                    if view!='clean' and arm.endswith('_clean'):continue
                    if any(r['target']==1 for r in rs):
                        selected=select(m,rs,t['anchor'],2.,-math.inf,feature_cache)
                        top.append({'group_id':t['group_id'],'view':view,'top_correct':bool(selected and selected['target']==1),'active_correct':any(r['target']==1 and (layout(m)=='metadata' or r['enabled'][layout(m)]) for r in rs)})
                for t,r,w,v in allrows:task_losses[t['group_id']].append((w,-math.log(max(v['probabilities'][r['target']+1],1e-15))))
                group_family={t['group_id']:records[t['task_id']]['family'] for t in ts}
                intervals=clustered_interval([(group_family[t['group_id']],t['group_id'],sum(w*v for w,v in task_losses[t['group_id']])*len(ts)) for t in ts])
                signals[arm+'/'+split]={'distributions':distributions,'weighted_nll':logscore/total if total else None,'weighted_brier':brier/total if total else None,
                    'prior_nll':priorlog/total if total else None,'prior_brier':priorbrier/total if total else None,'log_clip':1e-15,'rank':rank,
                    'wrong_anchor_top_candidate':{'opportunity_views':len(top),'opportunity_groups':len({v['group_id'] for v in top}),'correct_top_views':sum(v['top_correct'] for v in top),'active_opportunity_views':sum(v['active_correct'] for v in top),'competition':'improve versus neutral'},
                    'task_loss_contribution_interval':intervals,'in_sample':split=='fit'}
            support[arm]['groups']={key:{'raw_class_rows':dict(Counter(str(v[0]) for v in vs)), 'class_weight':{str(k):sum(v[1] for v in vs if v[0]==k) for k in (-1,0,1)}, 'class_groups':{str(k):len({v[2] for v in vs if v[0]==k}) for k in (-1,0,1)}} for key,vs in support[arm]['groups'].items()}
            # Original thresholds only on tuning; no development grid is evaluated.
            decomposition[arm]={}
            for tau in c.GRID:
                counts=Counter();active_scores=[]
                for t in tasks['threshold_tuning']:
                    rec=records[t['task_id']];a,vs,_=s.views(parent,rec)
                    for view,rs in t['views'].items():
                        if not any(peer.status=='ok' for peer in vs[view]):counts['no_valid_source_alternative']+=1
                        elif not rs:counts['all_alternatives_noops']+=1
                        active=[r for r in rs if layout(m)=='metadata' or r['enabled'][layout(m)]]
                        counts['disabled_candidates']+=len(rs)-len(active)
                        values=[feature_cache[digest(r[layout(m)])]['u2'] for r in active];active_scores+=values
                        counts['active_opportunities']+=sum(r['target']==1 for r in active)
                        counts['disabled_opportunities']+=sum(r['target']==1 for r in rs if r not in active)
                        chosen=select(m,rs,t['anchor'],2.,tau,feature_cache)
                        if active and chosen is None:counts['active_but_no_score_above_threshold' if tau!='KEEP_ONLY' else 'selected_KEEP_ONLY']+=1
                        if chosen and chosen['target']!=1 and any(r['target']==1 for r in active):counts['wrong_alternative_competition']+=1
                curve=next(x for x in thresholds[arm]['curves'] if x['threshold']==tau)
                decomposition[arm][str(tau)]={'counts':dict(counts),'active_score_summary':quantiles(active_scores),'exact_zero_scores':sum(v==0 for v in active_scores),
                    'rejected_by_original_risk_screen':not curve['eligible'],'original_curve':curve,'KEEP_ONLY_final_tie':thresholds[arm]['threshold']=='KEEP_ONLY' and curve['switched_tasks']==0}
        for split,ts in tasks.items():
            for family in sorted({records[t['task_id']]['family'] for t in ts}):
                subset=[t for t in ts if records[t['task_id']]['family']==family]
                opportunities[split+'/'+family]={'tasks':len(subset),'anchor_correct':sum(t['anchor']['status']=='ok' and t['anchor']['answer']==t['gold'] for t in subset),
                    'clean_rescue_groups':sum(any(r['target']==1 for r in t['views']['clean']) for t in subset),
                    'clean_improving_rows':sum(r['target']==1 for t in subset for r in t['views']['clean']),
                    'clean_harm_groups':sum(any(r['target']==-1 for r in t['views']['clean']) for t in subset)}
            for t in ts:
                for view,rs in t['views'].items():
                    for r in rs:
                        group=split+'/'+records[t['task_id']]['family']+'/'+('clean' if view=='clean' else 'augmented')+'/'+str(r['target'])
                        for kind in ('full','restricted'):
                            for field,value in r[kind].items():checks[group+'/'+kind+'/'+field][str(value)]+=1
                            checks[group+'/'+kind+'/enabled'][str(r['enabled'][kind])]+=1
                        for field,value in r['metadata'].items():checks[group+'/public_metadata/'+field][str(value)]+=1
                        checks[group+'/verdict_agreement'][str(r['full']['comparative_verdict']==r['restricted']['comparative_verdict'])]+=1
                        checks[group+'/references_available'][str(bool(r['references']))]+=1
        write_json(root/'score_reconstruction.json',reconstruction)
        write_json(root/'weighted_class_support.json',support)
        write_json(root/'candidate_signal_summary.json',signals)
        write_json(root/'checker_transition_tables.json',{k:dict(v) for k,v in checks.items()})
        write_json(root/'feature_collision_summary.json',collisions)
        write_json(root/'fit_tuning_sensitivity.json',{'diagnostic_only':True,'policy_selection_authorized':False,'results':grids})
        write_json(root/'original_tuning_reconstruction.json',{'thresholds':thresholds,'decomposition':decomposition})
        write_json(root/'split_opportunity_summary.json',opportunities)
        atomic_write(root/'saved_scores.private.jsonl',''.join(canonical(r)+'\n' for r in private_scores))
        dossier(root,parent,tasks,records,models,thresholds,cache)
    summary={'run_id':RUN_ID,'fixture':mock,'new_model_calls':0,'new_fits':0,'policy_selection_authorized':False,
             'parent_unchanged':True,'source':s.code_identity(s.REPO),'parent_sha256':read_json(root/'parent_import_receipt.json')['private_sha256'],'opportunities':opportunities,'signal':signals,'weighted_support':support,
             'original_thresholds':{a:v['threshold'] for a,v in thresholds.items()},'feature_collisions':collisions}
    write_json(root/'summary.json',summary)
    write_json(root/'resource_usage.json',{'new_model_calls':0,'gate_fits':0,'teacher_forced_forwards':0,'optimizer_updates':0})
    lines=['# Saved gate diagnostics','', 'Read-only reconstruction passed for all five models and original tuning choices. No refits or model calls.',
           '', '| Gate | Tuning active maximum u2 | Tuning u2 ROC improve/non-improve | Original threshold |','|---|---:|---:|---|']
    for arm in c.ARMS:
        q=decomposition[arm]['0']['active_score_summary']['quantiles']
        rank=signals[arm+'/threshold_tuning']['rank']['improve_vs_nonimprove']['u2']
        lines.append(f"| {arm} | {q['1'] if q else None} | {rank['roc_auc']} | {thresholds[arm]['threshold']} |")
    lines+=['','Fit is in-sample; tuning was already used for selection. Sensitivity is explanatory arithmetic, not an authorized policy. '
            'Model-reported evidence categories and source spans are not verified reasoning. No result establishes that another classifier cannot work.',
            '', 'Review score location together with ranking, masks and the private dossier. Preserve KEEP_ONLY. '
            'The separate prospective selector comparison can test compliance; its real model behavior remains GPU-unverified. '
            'No transfer, additional training or deferred human review is authorized.']
    text='\n'.join(lines)+'\n'
    for name in ('REPORT.md','diagnostic_decision_review.md','CODEX_HANDOFF.md'):(root/name).write_text(text)
    write_json(root/'checksums.json',{str(p.relative_to(root)):file_hash(p) for p in root.iterdir() if p.is_file() and p.name!='checksums.json'})
    return summary


def dossier(root,parent,tasks,records,models,thresholds,cache):
    harmful=sorted([t for t in tasks['fit'] if any(r['target']==-1 for r in t['views']['clean'])],key=lambda t:digest([SEED,'harm-comparison',t['group_id']]))[:22]
    chosen={t['group_id'] for t in harmful};out=[]
    for split,ts in tasks.items():
        for t in ts:
            improving=any(r['target']==1 for r in t['views']['clean'])
            if not improving and t['group_id'] not in chosen:continue
            rec=records[t['task_id']];a,vs,_=s.views(parent,rec);detail=[]
            for view,rs in t['views'].items():
                for r in rs:
                    derived={}
                    for arm,m in models.items():
                        val=cache[arm][digest(r[layout(m)])];active=layout(m)=='metadata' or r['enabled'][layout(m)]
                        top=select(m,rs,t['anchor'],2.,-math.inf,cache[arm]);labels=[]
                        if not any(peer.status=='ok' and peer.answer==t['gold'] for peer in vs[view]):labels.append('no_correct_peer')
                        if r['target']==1:
                            if not active:labels.append('correct_peer_disabled')
                            if layout(m)!='metadata':
                                favored=r[layout(m)]['comparative_verdict']=='favor_alternative'
                                if not favored:labels.append('checker_did_not_favor_correct_peer')
                                if favored and val['u2']<=0:labels.append('checker_favored_but_gate_score_nonpositive')
                            if val['u2']>0 and thresholds[arm]['threshold']!='KEEP_ONLY' and val['u2']<=thresholds[arm]['threshold']:labels.append('positive_score_below_threshold')
                            if top and top['target']!=1:labels.append('wrong_alternative_ranked_above_correct')
                            if thresholds[arm]['threshold']=='KEEP_ONLY':labels.append('retained_by_KEEP_ONLY')
                        derived[arm]={**val,'active':active,'disable_reason':None if active else 'extractor_or_checker_invalid',
                            'top_alternative':top['candidate_id'] if top else None,'threshold':thresholds[arm]['threshold'],
                            'final_parent_decision':g.decide(m,rs,a,thresholds[arm]['threshold']),'mechanical_pathways':labels}
                    evidence={k:read_json(parent/'calls/shards'/f'{key}.json') for k,key in r['evidence'].items()}
                    detail.append({'view':view,'row':r,'raw_evidence':evidence,'scores':derived})
            out.append({'task':rec,'anchor':asdict(a),'views':{v:[asdict(p) for p in ps] for v,ps in vs.items()},'split':split,
                        'panel':'rescue_opportunity' if improving else 'hash_selected_harm_comparison_not_prevalence','detail':detail})
    atomic_write(root/'opportunity_dossier.private.jsonl',''.join(canonical(r)+'\n' for r in out))
    definitions='Mechanical labels may overlap. Disabled means the original extractor/checker mask is false. Favor means comparative_verdict=favor_alternative. Nonpositive means u2<=0. Wrong rank means the active argmax is not correct. KEEP_ONLY refers to the selected policy, not finite-score behavior. No semantic truth or human review is asserted.'
    (root/'opportunity_dossier.private.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'"><title>PRIVATE opportunity dossier</title><p>'+html.escape(definitions)+'</p>'+''.join('<details><summary>Case '+str(i+1)+'</summary><pre>'+html.escape(canonical(r))+'</pre></details>' for i,r in enumerate(out)))


def export(root):
    summary=read_json(root/'summary.json');stamp=time.time_ns();out={}
    for kind in ('PRIVATE','SANITIZED'):
        path=root.parent/'bundles'/f'{RUN_ID}-{kind}-{stamp}.zip'
        if kind=='PRIVATE':out[kind.lower()]=package(root,path,'gate_diagnostics_private_v1')
        else:
            with tempfile.TemporaryDirectory(dir=root.parent) as d:
                temp=Path(d);write_json(temp/'summary.json',summary)
                (temp/'REPORT.md').write_text((root/'REPORT.md').read_text())
                out[kind.lower()]=package(temp,path,'gate_diagnostics_sanitized_v1')
    return out


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=['import-parent','analyze','report','export'])
    p.add_argument('--run-dir',type=Path,required=True);p.add_argument('--bundle',type=Path);p.add_argument('--sha256');p.add_argument('--mock',action='store_true')
    a=p.parse_args(argv)
    if a.stage=='import-parent':out=import_parent(a.run_dir,a.bundle,a.sha256,a.mock)
    elif a.stage=='analyze':out=analyze(a.run_dir,a.mock)
    elif a.stage=='report':out=read_json(a.run_dir/'summary.json')
    else:out=export(a.run_dir)
    print(canonical(out if a.stage in ('report','export') else {'status':'complete','stage':a.stage,'new_model_calls':0,'new_fits':0}))

if __name__=='__main__':main()
