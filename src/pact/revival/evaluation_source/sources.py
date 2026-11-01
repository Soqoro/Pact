"""Bounded local source import and project-exposure audit. Never downloads."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import json
import re
import unicodedata

from ...schemas import TaskInput, TaskLabel, Option
from ...datasets import content_group, SOURCES
from ...training.data import (TRAIN_SOURCES, load_training_sources, audit_training_overlap,
                              select_training, _shingles)
from ...selective.data import validate_exposure, prior_selections, REPO
from ...util import digest, file_hash, read_json

SOURCES_EVAL = ('openbookqa', 'logiqa')
NAMESPACE = 'pact-stage2-openbookqa-logiqa-eval-amendment-v2'
SEED = 20261016
MAX_BYTES = 20 * 1024**2
MAX_ROWS = 10000
MAX_ROW_BYTES = 65536
HEX = re.compile(r'[0-9a-f]{64}\Z')
REV = re.compile(r'[0-9a-f]{40}\Z')
FIELDS = ('task_ids', 'group_ids', 'content_groups', 'cross_dataset_fingerprints')


def text(v, limit=16384):
    if not isinstance(v, str) or not v.strip() or len(v.encode('utf-8')) > limit:
        raise ValueError('missing_or_oversize_text')
    if any(unicodedata.category(c) == 'Cs' or (ord(c) < 32 and c not in '\n\r\t') for c in v):
        raise ValueError('invalid_unicode')
    return v


def openbook_row(row, revision, sha):
    """No additional fields or answer hints may enter the TaskInput."""
    if not isinstance(row, dict) or set(row) != {'id','question_stem','choices','answerKey'}:
        raise ValueError('unexpected_fields_or_additional_hints')
    if len(json.dumps(row, ensure_ascii=True).encode()) > MAX_ROW_BYTES:
        raise ValueError('oversize_serialization')
    sid = text(row['id'], 256)
    question = text(row['question_stem'])
    choices = row['choices']
    if not isinstance(choices, dict) or set(choices) != {'label','text'}:
        raise ValueError('invalid_nested_choices')
    labels, values = choices['label'], choices['text']
    if not isinstance(labels, list) or not isinstance(values, list) or len(labels) != 4 or len(values) != 4:
        raise ValueError('four_choices_required')
    norm = [unicodedata.normalize('NFKC', text(v, 16)).strip() for v in labels]
    if len(set(norm)) != 4 or set(norm) != set('ABCD'):
        raise ValueError('duplicate_or_unknown_choice_labels')
    values = [text(v) for v in values]
    if len({' '.join(unicodedata.normalize('NFKC', v).casefold().split()) for v in values}) != 4:
        raise ValueError('indistinguishable_options')
    gold = unicodedata.normalize('NFKC', text(row['answerKey'], 16)).strip()
    if gold not in norm:
        raise ValueError('invalid_gold_key')
    tid = 'openbookqa:train:' + sid
    task = TaskInput(tid, 'openbookqa', 'train', sid, revision, sha, question,
                     tuple(Option(k, v, original) for k,v,original in zip(norm,values,labels)))
    return task, TaskLabel(tid, gold)


def source_identity(spec):
    return {k:spec.get(k) for k in ('repository','config','split','revision','path','format','sha256','expected_rows')}


def check_spec(spec):
    identity = source_identity(spec)
    if (identity['repository'] != 'allenai/openbookqa' or identity['config'] != 'main'
        or identity['split'] != 'train' or not REV.fullmatch(str(identity['revision']))
        or not HEX.fullmatch(str(identity['sha256'])) or identity['format'] not in ('jsonl','parquet')):
        raise ValueError('unreviewed_source_contract')
    path = identity['path']
    if not isinstance(path,str) or not re.fullmatch(r'main/train[^/]*\.(jsonl|parquet)',path):
        raise ValueError('official_main_train_path_required')
    return identity


def rights_status(rights, identity):
    """An external review assertion, never an inferred legal approval."""
    return bool(isinstance(rights,dict) and rights.get('status') == 'approved_for_proposed_use'
        and rights.get('source_identity_sha256') == digest(identity)
        and rights.get('reviewed_by_human') is True and rights.get('item_scope_reviewed') is True
        and isinstance(rights.get('terms'),list) and rights['terms']
        and all(isinstance(x,dict) and isinstance(x.get('url'),str) and x['url'].startswith('https://')
                and HEX.fullmatch(str(x.get('sha256'))) for x in rights['terms'])
        and isinstance(rights.get('review_receipt_sha256'),str)
        and HEX.fullmatch(rights['review_receipt_sha256']))


def reviewed_documents(review, identity):
    if not rights_status(review,identity): return False
    try:
        receipt=Path(review['review_receipt_file'])
        if receipt.stat().st_size>MAX_ROW_BYTES or file_hash(receipt)!=review['review_receipt_sha256']: return False
        saved=read_json(receipt)
        if (saved.get('source_identity_sha256')!=digest(identity) or saved.get('reviewed_by_human') is not True
            or saved.get('status')!='approved_for_proposed_use' or saved.get('item_scope_reviewed') is not True
            or saved.get('terms') != [{k:x[k] for k in ('url','sha256')} for x in review['terms']]): return False
        for entry in review['terms']:
            path=Path(entry['local_file'])
            if path.stat().st_size>MAX_BYTES or file_hash(path)!=entry['sha256']: return False
        return True
    except (OSError,KeyError,ValueError,TypeError): return False


def identity_reviewed(spec):
    review=spec.get('identity_review',{})
    return bool(review.get('reviewed_by_human') is True
        and review.get('source_identity_sha256')==digest(source_identity(spec))
        and HEX.fullmatch(str(review.get('receipt_sha256')))
        and spec.get('expected_rows') == 4957 and review.get('official_origin_verified') is True
        and identity_document(spec,review))


def identity_document(spec, review):
    try:
        path=Path(review['receipt_file'])
        if path.stat().st_size>MAX_ROW_BYTES or file_hash(path)!=review['receipt_sha256']: return False
        saved=read_json(path)
        return (saved.get('source_identity_sha256')==digest(source_identity(spec))
                and saved.get('official_origin_verified') is True and saved.get('reviewed_by_human') is True)
    except (OSError,KeyError,ValueError,TypeError): return False


def load_openbook(path, spec):
    identity = check_spec(spec)
    if not path or not Path(path).is_file():
        return None, {'status':'source_bytes_unavailable','raw_rows':None,'source':identity}
    path = Path(path)
    if path.stat().st_size > MAX_BYTES or file_hash(path) != spec['sha256']:
        raise ValueError('source_byte_digest_or_size_conflict')
    if spec['format'] == 'jsonl':
        rows = []
        with path.open(encoding='utf-8', errors='strict') as f:
            for line in f:
                if len(rows) >= MAX_ROWS or len(line.encode()) > MAX_ROW_BYTES:
                    raise ValueError('source_row_bound')
                rows.append(json.loads(line))
    else:
        import pyarrow.parquet as pq
        p = pq.ParquetFile(path)
        if p.metadata.num_rows > MAX_ROWS or p.metadata.num_columns > 8 or sum(
            p.metadata.row_group(i).total_byte_size for i in range(p.metadata.num_row_groups)) > MAX_BYTES:
            raise ValueError('source_decoded_bound')
        rows = p.read().to_pylist()
    if not rows: raise ValueError('empty_source')
    if spec.get('expected_rows') is not None and (type(spec['expected_rows']) is not int or spec['expected_rows']!=len(rows)):
        raise ValueError('source_row_count_conflict')
    records, rejected = [], []
    for i,row in enumerate(rows):
        try: records.append(openbook_row(row,spec['revision'],spec['sha256']))
        except (ValueError,TypeError,UnicodeError) as e:
            rejected.append({'row':i,'reason':str(e) if isinstance(e,ValueError) else 'malformed_row'})
    # All duplicate stable IDs are denied; choosing one occurrence would hide conflicts.
    counts = Counter(t.task_id for t,l in records)
    unique=[]
    for t,l in records:
        if counts[t.task_id] != 1: rejected.append({'task_id':t.task_id,'reason':'duplicate_stable_id'})
        else: unique.append((t,l))
    return unique, {'status':'bytes_verified','source':identity,'raw_rows':len(rows),
                    'valid_rows':len(unique),'rejected':rejected,
                    'rejection_counts':dict(Counter(x['reason'] for x in rejected)),
                    'source_identity_reviewed':identity_reviewed(spec),
                    'rights_reviewed':reviewed_documents(spec.get('rights_review'),identity)}


def original_sources(cache):
    """Existing authoritative parser, all original train + validation, no test access."""
    if cache is None:
        return None,None,{'status':'source_bytes_unavailable','missing':['original_train_validation_cache'],'registered_source':TRAIN_SOURCES['logiqa'],'raw_digest_verified':False}
    missing=[s['filename'] for collection in (TRAIN_SOURCES,SOURCES) for s in collection.values()
             if not (Path(cache)/s['filename']).is_file()]
    if missing: return None,None,{'status':'source_bytes_unavailable','missing':missing,'registered_source':TRAIN_SOURCES['logiqa'],'raw_digest_verified':False}
    train,val=load_training_sources(Path(cache),download=False)
    return train,val,{'status':'bytes_verified','source':TRAIN_SOURCES['logiqa'],
                     'raw_rows':sum(t.family=='logiqa' for t,l in train)}


def exposure_status(exposure, parent_source, *, fixture=False):
    errors=[]
    if not fixture:
        try: validate_exposure(exposure)
        except (ValueError,TypeError,KeyError): errors.append('exposure_inventory_stale_or_incomplete')
        if exposure.get('experiment_ledger_sha256') != file_hash(REPO/'docs/experiment_ledger.md'):
            errors.append('experiment_history_coverage_stale')
    if exposure.get('parent_source_sha256') != digest(parent_source): errors.append('parent_exposure_lineage_conflict')
    if exposure.get('coverage') != 'all_prior_used_and_protected_project_groups': errors.append('exposure_coverage_unknown')
    if exposure.get('material_overlap_review') != 'no_unresolved_cases': errors.append('semantic_overlap_review_unresolved')
    return {'status':'verified' if not errors else 'unknown','blockers':errors,
            'pretraining_exposure':'unknown','semantic_decontamination_established':False}


def eligibility(ob, training, validation, source, exposure, *, fixture=False, source_reviewed=None):
    """Same transitive lexical rule; exact historical group identities retained as aliases."""
    es=exposure_status(exposure,source,fixture=fixture)
    source_reviewed=source_reviewed or dict.fromkeys(SOURCES_EVAL,fixture)
    ex={k:set(exposure.get(k,[])) | set(source.get('exposure',{}).get(k,[])) for k in FIELDS}
    previous=list(prior_selections(REPO/'experiments')) if not fixture else []
    if not fixture:
        _,_,old,_=select_training(training,validation,items=1200,seed=20260918)
        if digest({**old,'sources':{'train':TRAIN_SOURCES,'validation':SOURCES}}) != '92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a':
            raise ValueError('historical_training_manifest_conflict')
        previous += old['selected']
    previous += [dict(task_id=r['task']['task_id'],**{k:r[k] for k in ('group_id','content_group','cross_dataset_fingerprint')})
                 for r in source['records']]
    for row in previous:
        for key,field in zip(FIELDS,('task_id','group_id','content_group','cross_dataset_fingerprint')):
            if row.get(field): ex[key].add(row[field])
    original_reps, original_audit=audit_training_overlap(training,validation)
    old_groups={t.task_id:g for (t,l),g in original_reps}
    # Retain ARC as overlap evidence, but never select it for this child.
    reps,audit=audit_training_overlap([*training,*ob],validation)
    all_pairs={t.task_id:(t,l) for t,l in [*ob,*training]}
    candidates={tid:pair for tid,pair in all_pairs.items() if pair[0].family in SOURCES_EVAL}
    denied={x['task_id']:x['reason'] for x in audit['exclusions'] if x['task_id'] in candidates}
    allowed=[];unknown=[]
    component_excluded=set()
    # Exclusions propagate over whole lexical components, not only representatives.
    for component in audit['groups']:
        for member in component['members']:
            pair=all_pairs.get(member['task_id'])
            if pair:
                t,l=pair
                if (t.task_id in ex['task_ids'] or content_group(t) in ex['content_groups'] or
                    digest(' '.join((t.context or t.question).split())) in ex['cross_dataset_fingerprints'] or
                    old_groups.get(t.task_id) in ex['group_ids']):
                    component_excluded.add(component['group_id'])
    for (t,l),g in reps:
        if t.family not in SOURCES_EVAL: continue
        values={'task_ids':t.task_id,'group_ids':g,'content_groups':content_group(t),
                'cross_dataset_fingerprints':digest(' '.join((t.context or t.question).split()))}
        if (g in component_excluded or old_groups.get(t.task_id) in ex['group_ids']
            or any(v in ex[k] for k,v in values.items())):
            denied[t.task_id]='historical_or_protected_overlap';continue
        if es['status']!='verified' or not source_reviewed[t.family]: unknown.append(t.task_id);continue
        allowed.append({'task':asdict(t),'family':t.family,'group_id':g,
                        'historical_group_id':old_groups.get(t.task_id),
                        'content_group':values['content_groups'],
                        'cross_dataset_fingerprint':values['cross_dataset_fingerprints'],
                        'split':'prospective_development'})
    counts={}
    for f in SOURCES_EVAL:
        ids={t for t,(task,l) in candidates.items() if task.family==f}
        rows=[r for r in allowed if r['family']==f]
        counts[f]={'audited_items':len(ids),'permitted_items':len(rows),'permitted_unique_groups':len({r['group_id'] for r in rows}),
                   'denied_items':len(ids&set(denied)),'unknown_items':len(ids&set(unknown)),
                   'reasons':dict(Counter(v for k,v in denied.items() if k in ids))}
    labels={tid:l.answer_id for tid,(t,l) in candidates.items()}
    return allowed,labels,{'counts':counts,'denied':denied,'unknown':unknown,'exposure':es,
                          'overlap_audit':audit,'original_overlap_hash':digest(original_audit),
                          'semantic_overlap':'lexical_screen_only; pretraining_unknown'}


def select(rows, labels):
    """Frozen outcome-independent rule. Labels cannot affect ordering or metadata."""
    selected=[]
    for f in SOURCES_EVAL:
        pool=sorted((r for r in rows if r['family']==f),key=lambda r:(digest([SEED,NAMESPACE,r['group_id']]),r['task']['task_id']))
        if len(pool)<64: raise ValueError('prospective_eval_not_feasible')
        for i,r in enumerate(pool[:64]):
            selected.append({**r,'binding':list(('QLM','LMQ','MQL','QML','MLQ','LQM')[i%6]),
                             'sender':i%3,'style':('claimed_consensus','claimed_independence')[i%2]})
    for field in ('group_id','content_group','cross_dataset_fingerprint'):
        if len({r[field] for r in selected})!=128: raise ValueError('cross_source_selected_collision')
    return {'records':selected,'labels':{r['task']['task_id']:labels[r['task']['task_id']] for r in selected},
            'selection':{'namespace':NAMESPACE,'seed':SEED,'rule':'hash(seed,namespace,group), stable ID tie break'},
            'status':'candidate_selected','cohort_approved':False,'gpu_execution_authorized':False}
