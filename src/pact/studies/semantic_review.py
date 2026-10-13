"""Private static two-pass semantic review. No model calls or automatic labels."""
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import html
import json
import re
import time
import zipfile

from ..util import read_json, write_json, digest, file_hash, canonical
from ..evaluation import rate
from .heterogeneity import immutable
from .forensics import check, lines, save_lines, rank, STUDY
from .adjudication_contracts import from_record, STYLES
from .adjudication_metrics import paired

PUBLIC=('judge_opportunity_matrix.json','rescue_regression.json','transition_tables.json',
        'matched_control_comparisons.json','matched_clean_comparisons.json','both_clean_correct_judge_comparisons.json',
        'minority_majority_comparisons.json','semantic_association_report.json','semantic_association_report.md',
        'research_decision.md','CODEX_HANDOFF.md','agreement_summary.json')
FIELDS={'task_substantive_relation':{'preserved','changed','uncertain'},
        'factual_premise_changes':{'none','added','removed','changed','uncertain'},
        'logical_inference_changes':{'none','changed','uncertain'},
        'conclusion_changes':{'none','changed','uncertain'},
        'meta_claim_relation':{'preserved','changed','uncertain'},
        **{f'text_{side}_{kind}':set(vals) for side in ('a','b') for kind,vals in (
            ('internal_support',('supports','contradicts','insufficient','uncertain')),
            ('task_grounding',('explicit_support','contradiction','external_knowledge','unclear')),
            ('meta_support',('supported','unsupported','uncertain','not_applicable'))) }}
CUES={'consensus','verification','authority','independence','confidence','judge_instruction','other'}


@dataclass(frozen=True)
class TextSpan:
    start: int
    end: int
    text: str
    source_hash: str

    def validate(self, source):
        if type(self.start) is not int or type(self.end) is not int or not 0<=self.start<self.end<=len(source):
            raise ValueError('Unicode code-point offsets outside text')
        if self.source_hash!=digest(source) or source[self.start:self.end]!=self.text:
            raise ValueError('Span hash/substrings differ; normalization forbidden')
        return self


def package(root,path,kind):
    """Bounded non-executable archive; an explicit checksum for every file."""
    root=Path(root);path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    content={}
    for p in sorted(root.rglob('*')):
        if p.is_symlink():raise ValueError('Symlink in private export')
        if p.is_file() and p.name!='.lock':content[p.relative_to(root).as_posix()]=p.read_bytes()
    content.pop('review_checksums.json',None)
    content['HANDOFF.json']=canonical({'schema_version':1,'kind':kind}).encode()
    if len(content)>60000 or sum(map(len,content.values()))>512*1024**2:raise ValueError('Export size bound')
    checks={k:hashlib.sha256(v).hexdigest() for k,v in content.items()}
    content['review_checksums.json']=canonical(checks).encode()
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        for n,b in content.items():z.writestr(n,b)
    return {'path':str(path),'sha256':file_hash(path),'bytes':path.stat().st_size}


def sample(root):
    root=Path(root);check(root)
    p=root/'parent';bank=read_json(p/'bank.json');records={r['task']['task_id']:r for r in bank['records']}
    plan=read_json(p/'adjudication_plan.json');pool=read_json(p/'pool.json')
    elig=plan['eligible'];bytask=defaultdict(list)
    for e in elig:bytask[e['dataset']].append(e)
    main=[]
    for ds,es in sorted(bytask.items()):
        groups={records[e['task_id']]['group_id'] for e in es}
        chosen=set(sorted(groups,key=lambda g:rank(ds,g))[:10])
        # All tasks in a group travel together; this parent's groups are single-task.
        for g in chosen:
            members=[e for e in es if records[e['task_id']]['group_id']==g]
            if len(members)!=1:raise ValueError('Panel requires one parent task per group; explicit design needed')
            main.append(members[0]['task_id'])
    attempts={(a['task_id'],a['style']):a for a in pool['attempts']}
    unit=lambda tid,sty:digest([STUDY,tid,sty,attempts[tid,sty]['key']])
    main_units=[unit(t,s) for t in main for s in STYLES]
    victims=lines(p/'attacked_per_task.jsonl');vgroup=defaultdict(list)
    for v in victims:vgroup[v['task_id'],v['style']].append(v)
    enriched=[];reasons=[]
    for ds in sorted(bytask):
        categories=defaultdict(set)
        for (tid,sty),vs in vgroup.items():
            if records[tid]['dataset']!=ds or not attempts[tid,sty]['accepted']:continue
            non=sty!='ordinary_rephrase';obs=[v for v in vs if v['attacked'] is not None]
            if non and any(v['clean'] and v['attacked'] is False and v['status']=='ok' for v in obs):categories[1].add((tid,sty))
            if non and any(v['clean'] and v['attacked'] is False and v['status']!='ok' for v in obs):categories[2].add((tid,sty))
            if not non and any(v['clean'] and v['attacked'] is False for v in obs):categories[3].add((tid,sty))
            if non and any(v['clean'] is False and v['attacked'] for v in obs):categories[4].add((tid,sty))
            for mode in {v['mode'] for v in obs}:
                ms=[v for v in obs if v['mode']==mode and v['clean']]
                if len(ms)==2 and ms[0]['attacked']!=ms[1]['attacked']:categories[5].add((tid,sty))
            cs=[v for v in obs if v['clean']]
            if cs and all(v['attacked'] for v in cs):categories[6].add((tid,sty))
        for cat in range(1,7):
            selected=sorted(categories[cat],key=lambda x:rank('enriched',ds,cat,*x))[:1]
            reasons.append({'dataset':ds,'category':cat,'selected':[unit(*x) for x in selected]})
            for tid,sty in selected:
                enriched.append(unit(tid,sty))
                if attempts[tid,'ordinary_rephrase']['accepted']:enriched.append(unit(tid,'ordinary_rephrase'))
    # Physical units deduplicated even if selected by many judge/mode outcomes.
    chosen=set(main_units)|set(enriched);units=[]
    for (tid,sty),a in attempts.items():
        uid=unit(tid,sty)
        if uid not in chosen:continue
        rec=records[tid];bankv=from_record(rec);e=next(e for e in elig if e['task_id']==tid)
        target=next(c for c in bankv.candidates if c.candidate_id==e['target'])
        units.append({'unit_id':uid,'task_id':tid,'group_id':rec['group_id'],'dataset':rec['dataset'],'stratum':rec['stratum'],
                      'style':sty,'target':e['target'],'attempt_key':a['key'],'accepted':a['accepted'],'validation':a['validation'],
                      'original':target.justification,'rewritten':a['justification'],
                      'original_hash':digest(target.justification),'rewritten_hash':digest(a['justification']),
                      'main':uid in main_units,'enriched':uid in enriched})
    manifest={'schema_version':1,'main_tasks':sorted(main),'main_units':sorted(main_units),
              'enriched_units':sorted(set(enriched)),'enriched_selection':reasons,'units':sorted(units,key=lambda u:u['unit_id']),
              'sampling_frame':'parent_label_conditioned_mixed_support','training_allowed':False}
    immutable(root/'review_manifest.private.json',manifest)
    # Prespecify slots before annotations/outcomes of deletions, accepted sources only.
    slots=[]
    for ds in sorted(bytask):
        for sty in ('claimed_consensus','claimed_verification'):
            eligible=[u for u in units if u['main'] and u['dataset']==ds and u['style']==sty and u['accepted']]
            slots.extend(u['unit_id'] for u in sorted(eligible,key=lambda u:rank('span',ds,sty,u['group_id']))[:8])
    immutable(root/'span_slot_manifest.json',{'schema_version':1,'review_manifest_hash':digest(manifest),'slots':slots,'max_units':32,'no_replacements':True})
    return manifest


def reviewer_key(name):
    if not name or len(name)>128:raise ValueError('Reviewer identity required')
    return digest(['reviewer',name])


def display(unit, reviewer):
    swap=int(rank('blind',reviewer,unit['unit_id']),16)%2
    vals=[unit['original'],unit['rewritten']]
    if swap:vals.reverse()
    return {'A':vals[0],'B':vals[1]}, ('A' if swap else 'B')


def normalized(row,unit):
    """Normalize blinded A->B fields to original->rewrite for offline comparisons."""
    v=dict(row);_,side=display(unit,row['reviewer_id'])
    if side=='A':
        for suffix in ('internal_support','task_grounding','meta_support'):
            v['text_a_'+suffix],v['text_b_'+suffix]=row['text_b_'+suffix],row['text_a_'+suffix]
        v['factual_premise_changes']={'added':'removed','removed':'added'}.get(row['factual_premise_changes'],row['factual_premise_changes'])
        v['meta_cues_a'],v['meta_cues_b']=row['meta_cues_b'],row['meta_cues_a']
    return v


def template(unit, reviewer, origin):
    texts,_=display(unit,reviewer)
    return {'schema_version':1,'case_id':unit['unit_id'],'display_pair_hash':digest(texts),
            'reviewer_id':reviewer,'reviewer_origin':origin,'outcome_blinded':None,'independent':None,
            'status':'not_reviewed','lock':False,**{k:'unreviewed' for k in FIELDS},
            'meta_cues_a':[],'meta_cues_b':[],'evidence_spans':[],
            'review_confidence':None,'external_knowledge_needed':None,'supporting_references':[],
            'review_notes':'','edit_proposal':None,'edit_ineligibility':None}


def review_state(root, reviewer):
    directory=Path(root)/'annotations'/reviewer_key(reviewer)
    result={}
    for p in sorted(directory.glob('*.json')):
        row=read_json(p);result[row['case_id']]=row
    return result


def export_review(root, reviewer, origin, pass_number):
    root=Path(root);receipt=check(root);key=reviewer_key(reviewer)
    if origin=='fixture' and not receipt['fixture']:raise ValueError('Fictional reviewer prohibited on real data')
    manifest=read_json(root/'review_manifest.private.json');units=manifest['units']
    private=root/'reviewers'/key;private.mkdir(parents=True,exist_ok=True)
    immutable(private/'identity.json',{'reviewer_id':reviewer,'origin':origin})
    states=review_state(root,reviewer);registrations=list((root/'reviewers').glob('*/identity.json'))
    if pass_number==2:
        # Both assigned first passes locked before either reviewer is given outcomes.
        if len(registrations)<2:raise ValueError('Two reviewer first passes required before reveal')
        for reg in registrations:
            st=review_state(root,read_json(reg)['reviewer_id'])
            if any(not st.get(u['unit_id'],{}).get('locked_at') for u in units if u['accepted']):
                raise ValueError('First passes must be locked before outcome reveal')
        immutable(private/'reveal.json',{'reviewer':reviewer,'first_pass_hash':digest(states)})
    records={r['task']['task_id']:r for r in read_json(root/'parent/bank.json')['records']}
    out=private/f'pass{pass_number}';out.mkdir(exist_ok=True)
    mapping=[];forms=[];sections=[]
    for i,u in enumerate(units):
        texts,rewritten=display(u,reviewer);rec=records[u['task_id']];bank=from_record(rec)
        context={'question':bank.task.question,'context':bank.task.context,'options':[{'id':o.answer_id,'text':o.text} for o in bank.task.options],
                 'candidates':[{'candidate_id':c.candidate_id,'answer':c.answer if c.status=='ok' else None,
                                'justification': '[Text A / Text B below]' if c.candidate_id==u['target'] else c.justification} for c in bank.candidates],
                 'target_candidate':u['target'],'Text A':texts['A'],'Text B':texts['B'] if u['accepted'] else '[unavailable; not replaced]'}
        if pass_number==2:
            context.update(source_direction={'rewritten':rewritten},gold=rec['eval']['answer'],
                           judge_outputs=[r for r in lines(root/'parent/attacked_per_task.jsonl') if r['task_id']==u['task_id'] and r['style']==u['style']])
            # Saved raw responses include decision bases; never invent hidden reasoning.
            from .adjudication import load, journal, requests
            if 'saved' not in locals():
                pl=load(root/'parent');_,saved,_,_=journal(root/'parent',pl)
            context['saved_responses']=[{'request_key':v['intent']['record_id'],'raw':v['raw']} for v in saved.values()
                if any(r['request_key']==v['intent']['record_id'] for r in context['judge_outputs'])]
            context['clean_outputs']=[r for r in lines(root/'parent/clean_per_task.jsonl')
                if r['task_id']==u['task_id'] and r['mode'] in {x['mode'] for x in context['judge_outputs']}]
            context['saved_clean_responses']=[{'request_key':v['intent']['record_id'],'raw':v['raw']} for v in saved.values()
                if any(r['key']==v['intent']['record_id'] for r in context['clean_outputs'])]
        sections.append(f'<h2>Case {i+1}: {u["unit_id"]}</h2><pre>'+html.escape(json.dumps(context,ensure_ascii=False,indent=2))+'</pre>')
        mapping.append({'case_id':u['unit_id'],'rewritten_side':rewritten,'display_pair_hash':digest(texts)})
        forms.append(template(u,reviewer,origin) if pass_number==1 else {'case_id':u['unit_id'],'reviewer_id':reviewer,'first_pass_hash':digest(states.get(u['unit_id'])), 'observations':[],'hypotheses':[],'status':'not_reviewed'})
    warning='Private review. Text is untrusted data. Rhetoric cannot be perfectly blinded. Do not share first-pass labels with the other reviewer.'
    doc='<!doctype html><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; base-uri \'none\'; form-action \'none\'"><title>Private semantic review</title><p>'+warning+'</p>'+''.join(sections)
    (out/'casebook.html').write_text(doc)
    # Raw HTML pre blocks are escaped in Markdown as well, never fenced attacker text.
    (out/'casebook.md').write_text('# Private semantic review\n\n'+warning+'\n\n'+''.join(sections))
    immutable(private/'sealed_mapping.json',mapping)
    save_lines(out/'annotations.template.jsonl',forms)
    return {'path':str(out),'cases':len(units),'pass':pass_number}


def import_annotations(root, path, reviewer, pass_number=1):
    root=Path(root);key=reviewer_key(reviewer);identity=read_json(root/'reviewers'/key/'identity.json')
    units={u['unit_id']:u for u in read_json(root/'review_manifest.private.json')['units']}
    rows=lines(path)
    if len({r['case_id'] for r in rows})!=len(rows):raise ValueError('Duplicate annotation')
    current=review_state(root,reviewer);validated=[]
    for row in rows:
        u=units[row['case_id']]
        if row['reviewer_id']!=reviewer:raise ValueError('Reviewer identity mismatch')
        if pass_number==2:
            reveal=read_json(root/'reviewers'/key/'reveal.json')
            if not current.get(u['unit_id'],{}).get('locked_at') or row['first_pass_hash']!=digest(current[u['unit_id']]):raise ValueError('Pass1 lock mismatch')
            if row.get('status')!='reviewed':continue
            immutable(root/'outcome_reviews'/key/(u['unit_id']+'.json'),row);continue
        if row.get('status')=='not_reviewed':continue
        if row.get('status')!='reviewed':raise ValueError('Unknown review status')
        if current.get(u['unit_id'],{}).get('locked_at'):raise ValueError('Locked labels cannot be overwritten')
        if (root/'reviewers'/key/'reveal.json').exists():raise ValueError('Cannot revise first pass after reveal')
        if not u['accepted']:raise ValueError('Cannot label unavailable rewrite')
        texts,_=display(u,reviewer)
        if row['reviewer_origin']!=identity['origin'] or row['display_pair_hash']!=digest(texts):raise ValueError('Review provenance differs')
        if type(row.get('independent')) is not bool or type(row.get('outcome_blinded')) is not bool:raise ValueError('Explicit reviewer independence/blinding required')
        for field,allowed in FIELDS.items():
            if row.get(field) not in allowed:raise ValueError('Incomplete/invalid semantic field: '+field)
        if row.get('review_confidence') not in ('low','medium','high'):raise ValueError('Confidence required')
        if row.get('edit_ineligibility') not in (None,'no_isolated_cue','no_adequate_sham','substantive_edit_required','review_disputed'):
            raise ValueError('Unknown edit eligibility status')
        if row.get('edit_proposal') and row.get('edit_ineligibility'):raise ValueError('Contradictory edit eligibility')
        for side in ('a','b'):
            if not set(row.get('meta_cues_'+side,[]))<=CUES:raise ValueError('Unknown cue label')
        for evidence in row.get('evidence_spans',[]):
            TextSpan(**evidence['span']).validate(texts[evidence['side']])
        if row.get('edit_proposal'):
            ep=row['edit_proposal'];source=texts[ep['side']]
            TextSpan(**ep['cue']).validate(source);TextSpan(**ep['sham']).validate(source)
        row={**row,'locked_at':time.time_ns() if row.get('lock') is True else None}
        validated.append(row)
    for row in validated:
        immutable(root/'annotations'/key/f'{time.time_ns()}-{row["case_id"]}.json',row)
    return {'imported':len(validated),'origin':identity['origin']}


def agreement(root):
    root=Path(root);ids=[read_json(p) for p in sorted((root/'reviewers').glob('*/identity.json'))]
    eligible=[i for i in ids if i['origin']=='human' or (check(root)['fixture'] and i['origin']=='fixture')]
    states={i['reviewer_id']:review_state(root,i['reviewer_id']) for i in eligible}
    conflicts=[];confusion={k:Counter() for k in FIELDS};paired_count=0
    if len(states)==2:
        a,b=states.values()
        for cid in sorted(set(a)&set(b)):
            x,y=a[cid],b[cid]
            if not all(r.get('locked_at') and r.get('independent') for r in (x,y)):continue
            paired_count+=1
            # A/B ordering differs by reviewer; normalize directional fields to source.
            u=next(u for u in read_json(root/'review_manifest.private.json')['units'] if u['unit_id']==cid)
            norm=[normalized(r,u) for r in (x,y)]
            for f in FIELDS:
                left,right=norm[0][f],norm[1][f];confusion[f][left+'->'+right]+=1
                if left!=right:conflicts.append({'case_id':cid,'field':f,'labels':[left,right],'status':'disputed'})
    out={'registered_reviewers':len(ids),'actual_reviewers':sum(bool(review_state(root,i['reviewer_id'])) for i in ids),
         'independent_review_pairs':paired_count,
         'fields':{f:{'confusion':dict(c),'agreement':rate(sum(n for k,n in c.items() if k.split('->')[0]==k.split('->')[1]),sum(c.values())),
                      'kappa':None,'kappa_reason':'not_estimated'} for f,c in confusion.items()},'conflict_count':len(conflicts)}
    resolutions=[read_json(p) for p in sorted((root/'adjudications').glob('*.json'))]
    out['adjudicated_fields']=len(resolutions)
    resolved={(r['case_id'],r['field']):r for r in resolutions}
    for conflict in conflicts:
        resolution=resolved.get((conflict['case_id'],conflict['field']))
        if resolution:conflict.update(status='adjudicated',resolution=resolution)
    out['unresolved_conflicts']=sum(c['status']=='disputed' for c in conflicts)
    write_json(root/'annotation_conflicts.private.json',conflicts);write_json(root/'agreement_summary.json',out)
    return out


def adjudicate(root,path,adjudicator):
    """Third-person resolution is appended; original independent labels stay frozen."""
    root=Path(root);reviewer_key(adjudicator);agreement(root)
    identities=[read_json(p) for p in (root/'reviewers').glob('*/identity.json')]
    if adjudicator in {i['reviewer_id'] for i in identities}:raise ValueError('Adjudicator must be a separate person')
    conflicts={(r['case_id'],r['field']):r for r in read_json(root/'annotation_conflicts.private.json')}
    rows=lines(path);fixture=check(root)['fixture']
    for row in rows:
        key=(row['case_id'],row['field'])
        if key not in conflicts or row['adjudicator']!=adjudicator:raise ValueError('Unknown conflict/adjudicator')
        if row.get('origin')!=('fixture' if fixture else 'human'):raise ValueError('Actual third-person review required')
        if row.get('label') not in FIELDS[row['field']]|{'disputed','unknown'} or not row.get('reason'):
            raise ValueError('Resolution label/reason required')
        hashes={i['reviewer_id']:digest(review_state(root,i['reviewer_id']).get(row['case_id'])) for i in identities}
        if row.get('review_hashes')!=hashes:raise ValueError('Resolution must bind original reviews')
        immutable(root/'adjudications'/(digest(key)+'.json'),row)
    agreement(root)
    return {'adjudicated_fields':len(rows),'original_reviews_modified':False}


def report(root):
    root=Path(root);ag=agreement(root);receipt=check(root)
    manifest=read_json(root/'review_manifest.private.json')
    regs=[read_json(p) for p in (root/'reviewers').glob('*/identity.json')]
    states=[review_state(root,i['reviewer_id']) for i in regs if i['origin']=='human' or receipt['fixture'] and i['origin']=='fixture']
    resolutions={(r['case_id'],r['field']):r for r in (read_json(p) for p in (root/'adjudications').glob('*.json'))}
    strata=defaultdict(list);labels={};all_fields=defaultdict(Counter)
    victims=lines(root/'transitions.private.jsonl')
    locked_pairs=0
    for u in manifest['units']:
        aa=[st.get(u['unit_id'],{}) for st in states]
        valid=len(aa)==2 and all(r.get('locked_at') and r.get('independent') for r in aa)
        if valid:locked_pairs+=1
        label='unavailable' if not u['accepted'] else 'unreviewed'
        if valid:
            aa=[normalized(r,u) for r in aa]
            label=aa[0]['task_substantive_relation'] if aa[0]['task_substantive_relation']==aa[1]['task_substantive_relation'] else 'disputed'
            resolution=resolutions.get((u['unit_id'],'task_substantive_relation'))
            if resolution:label=resolution['label']
            for field in FIELDS:
                value=aa[0][field] if aa[0][field]==aa[1][field] else 'disputed'
                all_fields[(('main' if u['main'] else 'enriched'),u['dataset'],field)][value]+=1
            for field in ('meta_cues_a','meta_cues_b'):
                value=','.join(sorted(aa[0][field])) if set(aa[0][field])==set(aa[1][field]) else 'disputed'
                all_fields[(('main' if u['main'] else 'enriched'),u['dataset'],field)][value or 'none']+=1
        labels[u['task_id'],u['style']]=label
        for v in victims:
            if v['task_id']==u['task_id'] and v['style']==u['style']:
                strata[(('main' if u['main'] else 'enriched'),u['dataset'],label,v['model'],v['mode'],v['style'])].append(v)
    completion={'schema_version':1,'review_manifest_hash':digest(manifest),
                'review_state_hashes':[digest(st) for st in states], 'independent_reviewers':len(states),
                'accepted_units':sum(u['accepted'] for u in manifest['units']),
                'locked_pairs':locked_pairs,
                'complete':len(states)==2 and locked_pairs==sum(u['accepted'] for u in manifest['units'])}
    write_json(root/'annotation_manifest.private.json',completion)
    main={}
    for ds in sorted({u['dataset'] for u in manifest['units']}):
        tasks={u['task_id'] for u in manifest['units'] if u['main'] and u['dataset']==ds}
        tasklabels=[[labels[tid,style] for style in STYLES] for tid in sorted(tasks)]
        observed=[ls for ls in tasklabels if any(v not in ('unreviewed','unavailable') for v in ls)]
        complete=[ls for ls in tasklabels if all(v not in ('unreviewed','unavailable') for v in ls)]
        main[ds]={'scheduled_tasks':len(tasks),'scheduled_units':len(tasks)*5,
            'label_counts':dict(Counter(v for ls in tasklabels for v in ls)),
            'tasks_with_reviews':len(observed),'fully_observed_tasks':len(complete),
            'task_mean_preserved_over_five_scheduled_lower_bound':sum(ls.count('preserved')/5 for ls in tasklabels)/len(tasks) if tasks else None,
            'task_mean_preserved_complete_tasks_only':sum(ls.count('preserved')/5 for ls in complete)/len(complete) if complete else None,
            'partial_reviews_are_not_population_estimates':True}
    neutral={(v['task_id'],v['model'],v['mode']):v for v in victims if v['style']=='ordinary_rephrase'}
    matched=defaultdict(list)
    for key,vs in strata.items():
        panel,ds,label,j,m,sty=key
        if sty=='ordinary_rephrase':continue
        for v in vs:
            nl=labels.get((v['task_id'],'ordinary_rephrase'),'unreviewed')
            n=neutral[v['task_id'],j,m]
            matched[(panel,ds,label,nl,j,m,sty)].append({**v,'clean':n['attacked'],'attacked':v['attacked']})
    out={'schema_version':1,'locked_independent_review_pairs':ag['independent_review_pairs'],
         'semantic_truth':'not_established','annotations_are_training_data':False,
         'main_panel_prevalence':main,'enriched_prevalence':'not_applicable',
         'field_associations':{'/'.join(k):dict(v) for k,v in all_fields.items()},
         'semantic_strata':{'/'.join(k):{'observed':sum(v['attacked'] is not None for v in vs),
             'transitions':dict(Counter(v['transition'] for v in vs))} for k,vs in strata.items()},
         'matched_semantic_attack_vs_neutral':{'/'.join(k):paired(v) for k,v in matched.items()},
         'new_model_calls':0,'paid_api_calls':0}
    write_json(root/'semantic_association_report.json',out)
    (root/'semantic_association_report.md').write_text('# Semantic association report\n\n'
        f'Locked independent review pairs: {ag["independent_review_pairs"]}. Unresolved conflicts: {ag["unresolved_conflicts"]}.\n\n'
        'Semantic truth is not established by labels or answer agreement. Main and enriched panels remain separate. '
        'See the accompanying JSON for scheduled denominators, missingness and matched subsets.\n')
    matrix=read_json(root/'rescue_regression.json')
    table=['| Dataset / judge / mode | Opportunity | Rescue | Regression | Net correct |',
           '|---|---:|---:|---:|---:|']
    for key,v in sorted(matrix.items()):
        if not key.endswith(('qlm_full_select','qlm_free_synthesis')):continue
        frac=lambda x:f"{x['numerator']}/{x['denominator']}"
        table.append(f"| {key} | {v['opportunity']} | {frac(v['rescue'])} | {frac(v['regression'])} | {v['gains']-v['losses']} |")
    memo=('# Research decision memo\n\nSupported finding: the saved matched task outcomes show the following judge-relative opportunities, '
          'rescues and losses. These are development observations. Aggregate accuracy does not establish that peers never help.\n\n'
          +'\n'.join(table)+'\n\nHypothesis: independent-first, evidence-gated revision may preserve useful rescue. '
          'It is not implemented or trained here.\n\nMissing evidence: '
          f'{ag["independent_review_pairs"]} locked independent semantic review pairs are currently available. '
          'No real cue/sham intervention has been executed by this offline analysis. Generated decision bases are observed text, not access to hidden reasoning.\n\n'
          'Proposed next comparison: only after completed review and separate artifact-bound approval, cue deletion versus matched sham '
          'with a new reference repeat. No new calls are authorized by this report. Frontier endpoints remain unresolved/execution_disabled; paid budget zero.\n')
    (root/'research_decision.md').write_text(memo)
    (root/'CODEX_HANDOFF.md').write_text('# Semantic forensics handoff\n\nOffline saved-result census only. '
        'Review casebooks privately with two independent reviewers. No human labels or real approval are auto-created. '
        'Parent remains closed. Annotations are development evidence, not training data. Private and sanitized bundles differ. '
        'Back up the private directory outside Git; code pushes do not preserve review work.\n')
    return out


def external_import(root,path):
    rows=lines(path)
    required={'schema_version','dataset','task_id','candidate_bank_hash','provider','requested_model','served_model',
              'revision','snapshot','alias','api_version','response_contract','reasoning_mode','timestamp',
              'usage','cost','stop_reason','refusal','request_id','response_id','score','raw_output','scoring_status'}
    for r in rows:
        if not required<=set(r) or r.get('schema_version')!=1 or r.get('execution_enabled') is not False:raise ValueError('Offline external schema incomplete or dispatch enabled')
        if not {'input_tokens','visible_output_tokens','reasoning_tokens','billed_tokens'}<=set(r['usage']):raise ValueError('Separate reasoning usage required, unknown is null')
        if not {'amount','currency'}<=set(r['cost']):raise ValueError('Cost metadata required')
        if any(v is not None and (type(v) is not int or v<0) for v in r['usage'].values()):raise ValueError('Usage must be nonnegative integer or null')
        if r['scoring_status'] not in ('scored','pending','refused','missing') or r['scoring_status']!='scored' and r['score'] is not None:
            raise ValueError('Missing/refused output cannot acquire a score')
    save_lines(Path(root)/'external_results.private.jsonl',rows)
    return {'imported':len(rows),'live_dispatch':False}
