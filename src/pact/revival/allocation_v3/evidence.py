"""Read-only parent resolution, source eligibility and sealed prospective selection."""
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import json
import shutil
import tempfile
from ...util import digest, file_hash, read_json, write_json
from ..stage1 import evidence as parent_evidence
from . import design as d

PARENT_SHA = '754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0'
SANITIZED_SHA = '1c4474a57bb28bd228040a32c496b6426e21531112e493b06be47dca0741047a'


def read_parent(bundle, destination):
    if destination.exists():
        raise ValueError('Absent import destination required')
    z, checks = parent_evidence.archive(bundle, PARENT_SHA)
    try:
        p = json.loads(z.read('plan.json'))
        summary = json.loads(z.read('summary.json'))
        if p['fixture'] or not all(summary['stage_status'].values()) or summary['accounting']['unresolved']:
            raise ValueError('Exact completed real Stage I required')
        if summary['accounting']['new_committed'] != 13467:
            raise ValueError('Stage I count conflict')
        destination.mkdir(parents=True, mode=0o700)
        # All paths and all checksums validated by archive(). Never execute content.
        for name in checks:
            out = destination / name
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(name) as src, out.open('wb') as dst:
                shutil.copyfileobj(src, dst)
        write_json(destination/'import-receipt.json', {'sha256': PARENT_SHA, 'files': checks})
        return p
    finally:
        z.close()


def old_assay_conflicts(roots):
    conflicts = []
    for root in roots:
        root = Path(root)
        if not root.is_dir():
            raise ValueError('History review root missing')
        for pattern in ('**/probe_training/**/status.json', '**/probe_training/**/update_attempt.json',
                        '**/probe_scores/shards/*.json', '**/score_intents/*.json'):
            conflicts.extend(str(p) for p in root.glob(pattern))
        for path in root.glob('**/attempts/*.json'):
            v=read_json(path);identity=v.get('identity',{})
            if identity.get('owner') in ('pact-update-allocation-crossed-002','pact-allocation-policy-evaluation-001'):
                conflicts.append(str(path))
        for path in root.glob('**/intents/*.json'):
            v = read_json(path)
            identity = v.get('identity', v.get('intent', {}).get('identity', {}))
            if identity.get('budget_stage') == 'II':
                conflicts.append(str(path))
    return sorted(set(conflicts))


def source_contract(source):
    blocks = source['blocks']
    rows = source['records']
    probes = {f: [r['task']['task_id'] for r in rows
                  if r['family'] == f and r['split'] == 'allocation_probe'] for f in d.SOURCES}
    counts = {f: sum(b['family'] == f for b in blocks) for f in d.SOURCES}
    blockers = []
    if counts != d.BLOCK_COUNTS:
        blockers.append('source_contract_conflict:block_membership_counts')
    if {f: len(x) for f, x in probes.items()} != d.PROBE_COUNTS:
        blockers.append('source_contract_conflict:probe_counts')
    fit = [t for b in blocks for t in b['fit']]
    if len(blocks) != 8 or any(len(b['fit']) != 64 for b in blocks) or len(set(fit)) != 512:
        blockers.append('fit_block_contract')
    if set(fit) & set(t for xs in probes.values() for t in xs):
        blockers.append('fit_probe_overlap')
    selected=[r for r in rows if r['split'] in ('main_fit','allocation_probe')]
    mapping={r['task']['task_id']:r for r in selected}
    if (len(mapping)!=576 or len({r['group_id'] for r in selected})!=576
        or any(t not in mapping or mapping[t]['split']!='main_fit'
               or mapping[t]['family']!=b['family'] for b in blocks for t in b['fit'])):
        blockers.append('fit_probe_group_or_source_identity_conflict')
    return {'status': 'blocked' if blockers else 'ready', 'blockers': blockers,
            'actual_block_counts': counts, 'actual_probe_counts': {f: len(x) for f, x in probes.items()},
            'probes': probes, 'blocks_hash': digest(blocks), 'source_sha256':digest(source),
            'record_identity_hash':digest([{'task':r['task'], 'group_id':r['group_id'],
                'content_group':r['content_group'], 'cross_dataset_fingerprint':r['cross_dataset_fingerprint'],
                'split':r['split']} for r in rows]),
            'source_revisions': {f: sorted({(r['task']['dataset_revision'],r['task']['source_hash'])
                for r in rows if r['family']==f}) for f in d.SOURCES},
            'allocation_source_weights':d.SOURCE_WEIGHTS,'model_calls':0}


def select_fresh(source, training, validation, exposure, fixture=False):
    from ...training.data import audit_training_overlap, TRAIN_SOURCES
    from ...selective.data import validate_exposure
    from ...datasets import content_group
    if not fixture:
        validate_exposure(exposure)
    exclusions = {k: set(exposure.get(k, [])) for k in
                  ('task_ids', 'group_ids', 'content_groups', 'cross_dataset_fingerprints')}
    # Preserve older exclusions even if a newer reviewed inventory omits a field.
    for key in exclusions:
        exclusions[key].update(source.get('exposure',{}).get(key,[]))
    if not fixture:
        from ...training.data import select_training
        from ...selective.data import prior_selections, REPO
        from ...datasets import SOURCES
        _,_,old,_=select_training(training,validation,items=1200,seed=20260918)
        if digest({**old,'sources':{'train':TRAIN_SOURCES,'validation':SOURCES}})!='92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a':
            raise ValueError('Historical training exclusion identity changed')
        for row in [*old['selected'],*prior_selections(REPO/'experiments')]:
            for key, field in [('task_ids','task_id'),('group_ids','group_id'),('content_groups','content_group'),('cross_dataset_fingerprints','cross_dataset_fingerprint')]:
                if row.get(field): exclusions[key].add(row[field])
    for r in source['records']:
        for key, value in [('task_ids', r['task']['task_id']), ('group_ids', r['group_id']),
                           ('content_groups', r['content_group']),
                           ('cross_dataset_fingerprints', r['cross_dataset_fingerprint'])]:
            exclusions[key].add(value)
    reps, audit = audit_training_overlap(training, validation)
    pool = {f: [] for f in d.SOURCES}
    for (t, label), group in reps:
        if t.split != 'train' or t.family not in pool:
            raise ValueError('Only authorized original train sources')
        if not fixture and (t.source_hash != TRAIN_SOURCES[t.family]['sha256'] or
                            t.dataset_revision != TRAIN_SOURCES[t.family]['revision']):
            raise ValueError('Unpinned source')
        values = {'task_ids': t.task_id, 'group_ids': group, 'content_groups': content_group(t),
                  'cross_dataset_fingerprints': digest(' '.join((t.context or t.question).split()))}
        if any(v in exclusions[k] for k, v in values.items()):
            continue
        pool[t.family].append((t, label, group, values))
    available = {f: len(v) for f, v in pool.items()}
    if any(n < 64 for n in available.values()):
        return {'status': 'prospective_eval_not_feasible', 'available': available,
                'required': dict.fromkeys(d.SOURCES, 64), 'model_calls': 0}
    rows, labels = [], {}
    for f in d.SOURCES:
        chosen = sorted(pool[f], key=lambda x: digest([20261027, 'prospective', x[2]]))[:64]
        for i, (t, label, group, values) in enumerate(chosen):
            rows.append({'task': asdict(t), 'family': f, 'group_id': group,
                         'binding': list(('QLM', 'LMQ', 'MQL', 'QML', 'MLQ', 'LQM')[i % 6]),
                         'sender': i % 3, 'style': ('claimed_consensus', 'claimed_independence')[i % 2],
                         'content_group': values['content_groups'],
                         'cross_dataset_fingerprint': values['cross_dataset_fingerprints'],
                         'split': 'prospective_development'})
            labels[t.task_id] = label.answer_id
    for key in ('group_id', 'content_group', 'cross_dataset_fingerprint'):
        if len({r[key] for r in rows}) != 128:
            raise ValueError('Prospective duplicate/cross-source group')
    return {'status': 'ready', 'available': available, 'records': rows, 'labels': labels,
            'exposure_hash': digest(exposure), 'overlap_audit_hash': digest(audit),
            'semantic_decontamination': False, 'role': 'sealed prospective source-domain development'}


def synthesize(parent, output):
    """Reproduce original reports in a disposable copy; parent files are read-only."""
    from ..stage1 import metrics, engine
    from unittest.mock import patch
    from ...studies.forensics import save_lines
    receipt = read_json(parent/'import-receipt.json')
    for name, expected in receipt['files'].items():
        if file_hash(parent/name) != parent_evidence.sha(expected):
            raise ValueError('Imported Stage I bytes changed')
    with tempfile.TemporaryDirectory(prefix='pact-stage1-synthesis-') as temp:
        target = Path(temp)/'parent'
        shutil.copytree(parent, target)
        p = read_json(target/'plan.json'); ph = digest(p); original = engine.digest
        with patch.object(engine, 'digest', side_effect=lambda v: ph if v is p else original(v)):
            engine.Journal(target, p)
        if digest(p) != ph:
            raise ValueError('Plan mutation')
        names = ('summary.json', 'paired_metrics.json', 'peer_access_interaction.json', 'runtime_and_cost_report.json')
        before = {n: read_json(target/n) for n in names}
        metrics.report(target)
        if any(read_json(target/n) != v for n, v in before.items()):
            raise ValueError('Stage I summary does not reproduce')
        # Generated status transitions, never semantic rationale labels.
        from ..stage1.engine import output as lookup
        transitions = Counter()
        derived = {}
        for line in (target/'live_per_task.private.jsonl').read_text().splitlines():
            r = json.loads(line)
            if r['final'] is not None and r['initial'] is not None and r['revised'] is not None:
                key='/'.join([r['split'],r['arm'],r['condition']])
                v=derived.setdefault(key, {'observed_tasks':0,'initial_coverage':0,
                    'private_correct_by_family':dict.fromkeys(d.FAMILIES,0),'revised_coverage':0,
                    'erasure':0,'construction':0,'readout_loss':0})
                v['observed_tasks']+=1
                v['initial_coverage']+=int(any(r['initial']))
                v['revised_coverage']+=int(any(r['revised']))
                v['erasure']+=int(any(r['initial']) and not any(r['revised']))
                v['construction']+=int(not any(r['revised']) and r['final'])
                v['readout_loss']+=int(any(r['revised']) and not r['final'])
                for slot,f in enumerate(r['binding']):
                    v['private_correct_by_family'][f]+=int(r['initial'][slot])
            for slot in range(3):
                own = lookup(target, [r['arm'], r['split'], r['task_id'], 'private', slot])
                rev = lookup(target, [r['arm'], r['split'], r['task_id'], r['condition'], 'revision', slot])
                final = lookup(target, [r['arm'], r['split'], r['task_id'], r['condition'], 'final'])
                key = '/'.join([r['split'], r['arm'], r['condition'],
                                own['packet']['status'] if own else 'missing',
                                rev['packet']['status'] if rev else 'missing',
                                final['packet']['status'] if final else 'missing'])
                transitions[key] += 1
        fixed_strata = {}
        for line in (target/'fixed_history_per_receiver.private.jsonl').read_text().splitlines():
            r = json.loads(line)
            key = '/'.join([r['arm'], r['condition'], r['receiver_family'],
                            'withheld' if r['withheld'] else 'present', str(r['common_stratum'])])
            value = fixed_strata.setdefault(key, {'intended': 0, 'observed': 0, 'correct': 0, 'invalid_own': 0})
            value['intended'] += 1
            value['observed'] += r['correct'] is not None
            value['correct'] += int(bool(r['correct']))
            value['invalid_own'] += int(bool(r['invalid_own']))
        result = {'version': d.VERSION, 'derived_observed_task_transitions':derived,
                  'historical_exchange_private_zero_fields':'historical summary did not aggregate these; use derived observed-task table, not zero accuracy', 'common_history_strata': fixed_strata, 'retrospective_only': True, 'model_calls': 0,
                  'prior_source_archive_byte_comparison': 'unavailable',
                  'on_policy': before['summary.json']['live'],
                  'paired': before['paired_metrics.json'], 'fixed_history': before['peer_access_interaction.json'],
                  'status_transition_receiver_counts': dict(transitions),
                  'historical_unknown_preserved': True, 's0_selection': 'fixed final uniform_joint_sft'}
        if output.exists():
            raise ValueError('Do not overwrite a synthesis')
        write_json(output, result)
        return result


def fixture_source():
    from ...schemas import TaskInput, Option
    rows, labels, blocks = [], {}, []
    for f in d.SOURCES:
        for split, count in [('main_fit', d.BLOCK_COUNTS[f]*64), ('allocation_probe', d.PROBE_COUNTS[f]), ('prospective_development', 64)]:
            ids = []
            for i in range(count):
                tid = f'{f}:fixture-{split}-{i}'
                task = TaskInput(tid, f, 'train', tid, 'fixture', 'fixture',
                                 'Invented '+digest(tid), tuple(Option(x, x, x) for x in 'ABC'),
                                 'Invented context '+digest([tid, 'context']))
                rows.append({'task': asdict(task), 'family': f, 'split': split, 'group_id': digest(tid),
                             'content_group': digest([tid, 'content']),
                             'cross_dataset_fingerprint': digest([tid, 'cross']),
                             'binding': list(('QLM', 'LMQ', 'MQL')[i % 3]), 'sender': i % 3,
                             'style': ('claimed_consensus', 'claimed_independence')[i % 2]})
                labels[tid] = 'ABC'[i % 3]; ids.append(tid)
            if split == 'main_fit':
                blocks += [{'family': f, 'fit': ids[j:j+64]} for j in range(0, d.BLOCK_COUNTS[f]*64, 64)]
    return {'fixture': True, 'records': rows, 'labels': labels, 'blocks': blocks}


EXECUTED_SOURCE_HASH = '85b414bb995aee54fe4b75c52e53df7261e9651b0d1598e2fbbc0774503c6c4b'
AUTHORITATIVE_FILES = {
 'plan.json':'34b85f0b064e0b00856d469335072e42cab5bde63eb4c20fec6687e87d67dd98',
 'evidence/plan.json':'dfadbd01009bbcef29a6591f4e04dbd507706feadda32c7f0491bf6db4f443e0',
 'checkpoint_inventory.private.json':'bc5ec49bf9175e38f18ce7504b457bce99b727cb8dfb284658add1fa51e6e243',
 'inference_identity_manifest.json':'26409207fc212f063fb502c73d5c2f3f1c903e16e7a612a414ffb3be4822857b',
 'evidence/access.json':'09759bd64158ccb2ba859c2bb41e0369f5f0d9ad185bc5780d1a06909baba933',
 'training_lineage_map.json':'74a940bb6b4f27d2d31747c5ebd4386b4b5886f4ec8d2031fe3bcb3dc4dcfc91',
 'checkpoint_verification_receipt.json':'4e8322bcee7e03fdac808a88ab4191155772b6af32a7b556a51ac59451beb7da',
}

def executed_source(parent):
    for name, expected in AUTHORITATIVE_FILES.items():
        if file_hash(parent/name)!=expected:
            raise ValueError('source_contract_conflict: authoritative bytes '+name)
    source=read_json(parent/'plan.json')['source']
    if digest(source)!=EXECUTED_SOURCE_HASH or source!=read_json(parent/'evidence/plan.json')['source']:
        raise ValueError('source_contract_conflict: executed source identity')
    return source


def prospective_capacity(source):
    """Monotone upper bound from the exact verified original eligibility receipt.
    This is not a fresh-source measurement and never relaxes original exclusions.
    """
    allocated={f:len({r['group_id'] for r in source['records'] if r['family']==f}) for f in d.SOURCES}
    available=source.get('available')
    if available is None:return {'status':'unverified','official_rescan_required':True}
    upper={f:available[f]-allocated[f] for f in d.SOURCES}
    if any(n<0 for n in upper.values()):raise ValueError('source_contract_conflict: eligibility receipt')
    return {'status':'prospective_eval_not_feasible' if any(n<64 for n in upper.values()) else 'rescan_required',
        'original_eligible':available,'already_allocated':allocated,'fresh_upper_bound':upper,
        'required':dict.fromkeys(d.SOURCES,64),'shortfall_at_least':{f:max(0,64-n) for f,n in upper.items()},
        'basis':'verified original eligibility minus all allocated groups; later exclusions only reduce support',
        'fresh_source_measurement':False,'model_calls':0}


def reviewed_history(h):
    import re
    receipts=h.get('external_evidence_receipts',[])
    return (h.get('parent_sha256')==PARENT_SHA and h.get('source_sha256')==EXECUTED_SOURCE_HASH
        and h.get('reviewed') is True and h.get('old_stage2_executed') is False
        and h.get('probe_groups_consumed') is False and h.get('unresolved_probe_consumption') is False
        and isinstance(receipts,list) and bool(receipts) and all(isinstance(r,dict)
        and isinstance(r.get('scope'),str) and bool(r['scope'])
        and isinstance(r.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',r['sha256']) for r in receipts))
