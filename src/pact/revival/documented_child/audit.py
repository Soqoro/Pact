"""Actual local-source screening. No download, legacy certification or model import."""
from .lexical import audit_components
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path
from ...util import digest, file_hash
from ...datasets import content_group
from ...training.data import audit_training_overlap, select_training, TRAIN_SOURCES
from ...datasets import SOURCES
from .. import exposure_accounting as evidence, development_amendment as approval
from ..evaluation_source import sources as old
from ..gpqa_source import sources as gp, review

VERSION = 'stage2_documented_exclusions_child_v1'
CHILD = approval.PROPOSAL
MAIN_SHA = 'acdeeac8f622267f2cd727d7d474202ea08dec80f7d3c3593b3ef8644f19b8e3'
DRAFT = 'fb31284ac87bc76cc55153b98fb78715413bb54865f9a601b07c9dae3c04722f'
LIMITATIONS = sorted(approval.DISCLOSED_LIMITATIONS)
PREVIEWS = ['7-980','7-584','7-870','7-321','9-732','9-782','9-87','155','1046']


def screen(main, diamond, history, sha, training, validation, source, exposure, *, cases=(), fixture=False):
    """Screen all components before choosing representatives. Unknown cases propagate.

    Legacy GPQA reconciliation is deliberately run with reviewed=False. Its
    absence-of-scope flag is interpreted only here under the approved child policy.
    No legacy exposure flags or reviews are synthesized.
    """
    _, _, ga = gp.reconcile(main, diamond, history, sha, reviewed=False)
    gp_pairs = []
    for row in main:
        try:
            t,l,_ = gp.native._normalize_for_partition(row, sha)
            gp_pairs.append((replace(t, family='gpqa_main', split='prospective_development'), l))
        except (ValueError, TypeError, KeyError):
            pass  # Reconciliation records malformed rows; never selectable.
    original, original_audit = audit_training_overlap(training, validation)
    old_groups = {t.task_id:g for (t,l),g in original}
    pairs = [*training, *gp_pairs]
    reps, lexical = audit_components(pairs, validation)
    by_id = {t.task_id:(t,l) for t,l in pairs}
    gp_records = {r['task_id']:r for r in ga['records']}
    ex = {k:set(exposure.get(k,[])) | set(source.get('exposure',{}).get(k,[])) for k in old.FIELDS}
    previous = [] if fixture else list(old.prior_selections(old.REPO/'experiments'))
    if not fixture:
        _,_,manifest,_ = select_training(training, validation, items=1200, seed=20260918)
        if digest({**manifest,'sources':{'train':TRAIN_SOURCES,'validation':SOURCES}}) != '92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a':
            raise ValueError('historical_training_manifest_conflict')
        previous += manifest['selected']
    previous += [dict(task_id=r['task']['task_id'], **{k:r[k] for k in ('group_id','content_group','cross_dataset_fingerprint')}) for r in source['records']]
    for r in previous:
        for k,f in zip(old.FIELDS, ('task_id','group_id','content_group','cross_dataset_fingerprint')):
            if r.get(f):ex[k].add(r[f])
    reasons = {tid:set(gp_records.get(tid,{}).get('reasons',[])) for tid in by_id}
    for entry in lexical['exclusions']:
        reasons[entry['task_id']].add(entry['reason'])
    # Case receipts may exclude or hold a candidate, never silently clear it.
    for case in cases:
        if set(case) != {'task_id','reason'} or not isinstance(case['reason'],str):
            raise ValueError('candidate_case_schema')
        if case['reason'] in LIMITATIONS:
            raise ValueError('concrete_case_cannot_be_downgraded_to_blanket_limitation')
        if case['task_id'] not in by_id:
            raise ValueError('candidate_case_mapping_unresolved')
        reasons[case['task_id']].add(case['reason'])
    for tid,(t,l) in by_id.items():
        values = {'task_ids':tid, 'group_ids':old_groups.get(tid), 'content_groups':content_group(t),
                  'cross_dataset_fingerprints':digest(' '.join((t.context or t.question).split()))}
        if any(v in ex[k] for k,v in values.items()) or gp_records.get(tid,{}).get('group_id') in ex['group_ids']:
            reasons[tid].add('historical_or_protected_overlap')
    # Propagate definite exclusions and candidate-specific uncertainty over the
    # entire lexical component, including nonrepresentatives and ARC evidence.
    component_reasons = {}
    for component in lexical['groups']:
        ids = [m['task_id'] for m in component['members']]
        why = set().union(*(reasons.get(tid,set()) for tid in ids))
        if len({by_id[tid][0].family for tid in ids if tid in by_id}) > 1:
            why.add('cross_source_overlap')
        component_reasons[component['group_id']] = why
    rows, labels, decisions = [], {}, []
    for (t,l),gid in reps:
        if t.family not in gp.SOURCES_EVAL:continue
        # GPQA's full Main/Diamond component identity remains selection identity.
        group = gp_records[t.task_id]['group_id'] if t.family=='gpqa_main' else gid
        why = component_reasons[gid] | reasons[t.task_id]
        hard = why - set(LIMITATIONS)
        state = 'excluded' if hard & approval.EXCLUSIONS else ('unresolved' if hard else 'screened')
        decisions.append({'task_id':t.task_id,'family':t.family,'group_id':group,'state':state,'reasons':sorted(why)})
        if state != 'screened':continue
        rows.append({'task':asdict(t),'family':t.family,'group_id':group,'historical_group_id':old_groups.get(t.task_id),
                     'content_group':content_group(t),'cross_dataset_fingerprint':digest(' '.join((t.context or t.question).split())),
                     'split':'prospective_development'})
        labels[t.task_id] = l.answer_id
    counts = {f:len({r['group_id'] for r in rows if r['family']==f}) for f in gp.SOURCES_EVAL}
    return rows, labels, {'screened_unique_groups':counts,'decisions':decisions,'gpqa_integrity':ga,
        'lexical_audit':lexical,'original_lexical_digest':digest(original_audit),
        'documented_union_digest':digest({k:sorted(v) for k,v in ex.items()}),
        'screened_rows':rows, 'screened_labels':labels,
        'representative_status_counts':dict(Counter(r['state'] for r in decisions)),
        'known_preview_exclusions':{'source':'OpenBookQA main/train','source_ids':PREVIEWS,
            'selected_source_intersection':False,'cross_source_semantic_relationship':'not_established'},
        'semantic_decontamination':False}


def run(config):
    source, lineage, _, exposure, refs, _ = evidence.read_inputs(config)
    blockers = []
    # Exact returned union is mandatory on real inputs, not a hand-written empty substitute.
    if not config.get('exposure_draft'):
        blockers.append('documented_exclusion_union_unavailable')
    else:
        draft, ref = evidence.bounded_json(config['exposure_draft'], DRAFT, 'canonical_json')
        exposure = {**exposure, **draft['exclusion_union']}
        refs['documented_union'] = ref
    cases = []
    if config.get('cases'):
        cases, refs['candidate_cases'] = evidence.bounded_json(config['cases'], config['cases_sha256'])
    rows, raw = gp.load(config.get('gpqa_dir'))
    training, validation, original = old.original_sources(config.get('data_dir'))
    inventory = None
    if config.get('inventory'):
        inventory, refs['historical_inventory'] = evidence.bounded_json(config['inventory'])
    historical, covered = review.history_files(inventory)
    if not covered:blockers.append('historical_partitions_unverified')
    if rows is None:blockers.append('gpqa_bytes_unavailable')
    elif raw['raw_sha256']['gpqa_main.csv'] != MAIN_SHA:raise ValueError('official_main_pin_conflict')
    if training is None:blockers.append('original_bytes_unavailable')
    candidate = None; eligibility = None
    if not blockers:
        permitted, labels, eligibility = screen(rows['gpqa_main.csv'], rows['gpqa_diamond.csv'], historical,
            MAIN_SHA, training, validation, source, exposure, cases=cases)
        if all(n>=64 for n in eligibility['screened_unique_groups'].values()):
            candidate = gp.select(permitted, labels)
        else:blockers.append('screened_unique_group_shortfall')
    audit = {'version':VERSION,'fixture':False,'sources':{'gpqa_main':raw,'logiqa':original},
             'eligibility':eligibility,'blockers':blockers,'bindings':refs,
             'candidate_case_inventory':'supplied' if config.get('cases') else 'no_additional_case_file_supplied; documented_inputs_only',
             'limitations':LIMITATIONS}
    return source, lineage, audit, candidate
