"""Read-only lineage resolution. No inference, training, or historical mutations."""
from collections import Counter
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile

from ...artifacts import safe_relative
from ...environment import code_identity
from ...util import digest, file_hash, read_json, write_json
from ...studies.heterogeneity import immutable
from ...studies.forensics import private_root
from .. import contracts as c, continuation, study, data, runtime

PRIVATE = '2d65cbe6bee279608ca472af081e1d1ca4305de44af7d73e859eb4581e870959'
SANITIZED = '9a34de7cb4d5602b1fa4beeaa735ca14d9418f47fc08cdc14b4b11e2dbf72d1a'
PLAN = 'bbd6decefbd9ba4808de22b31c87f02f4d19094ee1b4035383db0285000d5897'
RUN = 'pact-revival-stage1-evaluation-001'
VERSION = 'revival_stage1_evaluation_v1'
CAPS = {'validation':4224, 'source_evaluation':8448, 'fixed_history':1920, 'attack':384}
SYNTHETIC = {'attempts':16, 'input_tokens_per_attempt':128, 'atol':0., 'rtol':0.,
             'text':'Synthetic verification only. Say nothing; this is a sequence forward.'}


def sha(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('Expected a full lowercase SHA256 (64 hex characters)')
    return value


def archive(path, expected=None):
    if expected is not None and file_hash(path) != sha(expected):
        raise ValueError('Archive identity mismatch')
    z = zipfile.ZipFile(path)
    try:
        names=z.namelist()
        if len(names)!=len(set(names)) or len(names)>150000 or sum(i.file_size for i in z.infolist())>32*1024**3:
            raise ValueError('Archive bounds/duplicates')
        for i in z.infolist():
            safe_relative(i.filename)
            if (i.external_attr>>16)&0o170000==0o120000:raise ValueError('Archive symlink')
        checks=json.loads(z.read('checksums.json'))
        if set(names)!=set(checks)|{'HANDOFF.json','checksums.json'}:raise ValueError('Archive inventory')
        for name, expected_hash in checks.items():
            h=hashlib.sha256()
            with z.open(name) as f:
                for chunk in iter(lambda:f.read(8*1024**2),b''):h.update(chunk)
            if h.hexdigest()!=sha(expected_hash):raise ValueError('Archive member mismatch')
        return z, checks
    except BaseException:
        z.close();raise


def exposure_check(source, exposure, fixture=False):
    """Fresh inventory plus typed events: own evaluation exposure is not fitting."""
    if not fixture:
        from ...selective.data import validate_exposure
        validate_exposure(exposure)
    selected={study.tid(r):r for r in source['records'] if r['split'] in ('validation','source_evaluation')}
    known={r['group_id'] for r in selected.values()}
    allowed={continuation.RUN, 'pact-heterogeneous-receiver-training-001',
             'pact-heterogeneous-receiver-training-replacement-002', RUN}
    explained=set(); explained_groups=set()
    for event in exposure.get('events',[]):
        ids=set(event.get('task_ids',[]));groups=set(event.get('group_ids',[]))
        if ids & selected.keys() or groups & known:
            if event.get('run_id') not in allowed or event.get('purpose') not in ('allocation','evaluation','attack_acquisition'):
                raise ValueError('Evaluation contamination/unrelated exposure; no replacement tasks')
            explained |= ids; explained_groups |= groups
    if (set(exposure.get('task_ids',[])) & selected.keys())-explained or (set(exposure.get('group_ids',[])) & known)-explained_groups:
        raise ValueError('Unexplained prior/locked exposure')
    for field in ('content_groups','cross_dataset_fingerprints'):
        record_field={'content_groups':'content_group','cross_dataset_fingerprints':'cross_dataset_fingerprint'}[field]
        selected_values={r.get(record_field) for r in selected.values()}-{None}
        overlapping=set(exposure.get(field,[])) & selected_values
        explained_values=set()
        for event in exposure.get('events',[]):
            if event.get('run_id') in allowed and event.get('purpose') in ('allocation','evaluation','attack_acquisition'):
                explained_values.update(event.get(field,[]))
        if overlapping-explained_values:raise ValueError('Unexplained content/fingerprint exposure')
    return {'inventory_sha256':digest(exposure),'self_events_checked':True}


def resolve(root, bundle, sanitized, exposure, checkpoint_map=None, *, fixture=False):
    if root.exists():raise ValueError('New immutable child required; use inspect for existing run')
    z,checks=archive(bundle,None if fixture else PRIVATE)
    sz,_=archive(sanitized,None if fixture else SANITIZED)
    try:
        p=json.loads(z.read('plan.json'));s=json.loads(z.read('summary.json'))
        if s!=json.loads(sz.read('summary.json')):raise ValueError('Summary mismatch')
        if not fixture and (digest(p)!=PLAN or p['amendment']!=continuation.AMENDMENT or p['review_hash']!=continuation.REVIEW_HASH):raise ValueError('Completed lineage mismatch')
        if p['source']['fixture']!=fixture or not s['training_complete'] or not s['recovery_safe'] or s['combined_committed_updates']!=768:raise ValueError('Complete safe descendant required')
        data.validate_source(p['source']); exposure_check(p['source'],exposure,fixture)
        private_root(root,fixture)
        # Preserve exact metadata; never import executable archive code.
        selected=['plan.json','summary.json','parent_plan.json','parent_replacement_plan.json','access.json']
        selected += [n for n in checks if n.startswith(('training/','lineage/','parent_contracts/','parent_receipts/')) and n.endswith('.json')]
        for n in selected:
            target=root/'evidence'/safe_relative(n);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))
        parent_bytes=z.read('parent-private.zip')
        with archive(io.BytesIO(parent_bytes))[0] as parent:
            for n in json.loads(parent.read('checksums.json')):
                if n.startswith(('intents/','calls/','attacks/')) or n=='plan.json':
                    target=root/'ancestor'/safe_relative(n);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(parent.read(n))
        parent=read_json(root/'ancestor/plan.json')
        if parent['source']!=p['source']:raise ValueError('Source lineage mismatch')
        j=runtime.Journal(root/'ancestor',allow_incomplete=True)
        counts=Counter(); inherited={}
        for key,intent in j.intents.items():
            logical=intent['identity']['logical']
            component='fit_private' if logical[0]=='fit' else 'scratch' if logical[0]=='scratch' else 'attack' if logical[0]=='attack' else 'unclassified'
            counts[component]+=1
            if component=='attack':
                tid=logical[1]; inherited[tid]={'work_id':key,'status':'committed' if key in j.results else 'unresolved'}
        evaluation_ids={study.tid(r) for r in p['source']['records'] if r['split'] in ('validation','source_evaluation')}
        previous_attacks={k:v for k,v in inherited.items() if k in evaluation_ids}
        blockers=[]
        if set(j.intents)-set(j.results) or counts['unclassified']:blockers.append('unresolved_or_unclassified_ancestor_generation')
        # The exact approved v2 allocation supersedes the old balanced design;
        # expose the new brief's conflicting quota, do not silently replace IDs.
        source_counts={split:dict(Counter(r['family'] for r in study.records(parent,split))) for split in ('validation','source_evaluation')}
        if not fixture and source_counts['source_evaluation']!={'arc_challenge':128,'logiqa':128}:
            blockers.append('brief_128_128_conflicts_with_executed_120_136')
        if not fixture and read_json(root/'evidence/parent_replacement_plan.json')['historical_accounting'].get('later_execution_history'):
            blockers.append('original_later_generation_ownership_requires_closure')
        mapping={}
        for arm in c.ARMS[1:]:
            for family in c.FAMILIES:
                fit=f'{arm}/{family}';prefix=f'training/{fit}/';cp=prefix+'checkpoints/step-000128/'
                status=json.loads(z.read(prefix+'status.json'));contract=json.loads(z.read(prefix+'contract.json'));state=json.loads(z.read(cp+'state.json'));inv=json.loads(z.read(cp+'checksums.json'))
                if status['completed_steps']!=128 or not status['complete'] or state['step']!=128 or state['identity']!=contract or contract['identity']['family']!=family or contract['identity']['arm']!=arm or contract['schedule'][-1]['epoch']!=2:raise ValueError('Wrong fit/step/contract')
                if inv['state.json']!=checks[cp+'state.json']:raise ValueError('Checkpoint metadata checksum mismatch')
                ancestor='replacement-002' if arm==c.ARMS[1] else 'continuation-003'
                if arm==c.ARMS[1] and p['inherited_files'][cp+'tensors.safetensors']!=inv['tensors.safetensors']:raise ValueError('Inherited tensor receipt mismatch')
                mapping[fit]={'family':family,'arm':arm,'step':128,'ancestor':ancestor,'metadata':cp+'state.json',
                    'contract':prefix+'contract.json','status':prefix+'status.json','expected_file_sha256':sha(inv['tensors.safetensors']),
                    'expected_adapter_hash':status['adapter_hash'],'native':contract['identity']['native'],
                    'tensor_path':(checkpoint_map or {}).get(fit), 'expected_hash_source':cp+'checksums.json',
                    'assurance':'audit_archive_bound_expected_hash_not_independent_authentication'}
        nominal=dict(CAPS)
        budget={'owner_plan':digest(parent),'owner_source':'ancestor/plan.json:contract.budgets.I',
                'original_cap':parent['contract']['budgets']['I']['generation'], 'nominal_components':nominal,
                'nominal_total':sum(nominal.values()),'nominal_reserved_tokens':sum(nominal.values())*512,
                'verified_ancestor_attempts':len(j.intents),'ancestor_components':dict(counts),
                'previous_evaluation_attack_attempts':len(previous_attacks),
                'remaining_component_upper_bounds':{**nominal,'attack':nominal['attack']-len(previous_attacks)},
                'ownership_status':'blocked' if any('generation' in b for b in blockers) else 'resolved',
                'unknown_parent_optimizer_step':s['unknown_parent_update'],'physical_update_bound':769,
                'ancestor_inventory_hash':digest(j.intents),'inherited_attacks':previous_attacks}
        if any(v<0 for v in budget['remaining_component_upper_bounds'].values()):raise ValueError('Budget overflow')
        if len(j.intents)+sum(budget['remaining_component_upper_bounds'].values())>budget['original_cap']:blockers.append('owner_total_cap_exceeded')
        fields={'tasks':{'source':'evidence/parent_plan.json:source','counts':source_counts},
                'checkpoints':{'source':'training_lineage_map.json','fits':list(mapping)},
                'models':{'source':'evidence/access.json','keys':list(read_json(root/'evidence/access.json'))},
                'prompt_parser_seeds':{'source':'pact.revival.contracts/study at recorded source','contract':c.VERSION,'seed':c.SEED,'packet':c.PACKET},
                'fixed_history':{'source':'evidence/parent_plan.json:peer_use','ids':parent['peer_use']},
                'runtime':{'source':'evidence/access.json','policy':'exact_training_fingerprint'},
                'budget':{'source':'reconciled_generation_budget.json'}}
        out={'version':VERSION,'fixture':fixture,'parent_plan':digest(p),'source_code':code_identity(Path(__file__).resolve().parents[4]),
             'evidence_sha256':file_hash(bundle),'lineage_map_hash':digest(mapping),'budget_hash':digest(budget),'fields':fields,'blockers':blockers,'status':'blocked' if blockers else 'resolved',
             'synthetic_allowance':SYNTHETIC,'new_generation_calls':0,'exposure':exposure_check(p['source'],exposure,fixture)}
        immutable(root/'contract_resolution.json',out);immutable(root/'training_lineage_map.json',mapping)
        immutable(root/'reconciled_generation_budget.json',budget);immutable(root/'exposure.json',exposure)
        immutable(root/'evidence_inventory.json',{f.relative_to(root).as_posix():file_hash(f) for base in ('evidence','ancestor') for f in sorted((root/base).rglob('*')) if f.is_file()})
        return out
    finally:z.close();sz.close()


def guard(root):
    r=read_json(root/'contract_resolution.json')
    if digest(read_json(root/'training_lineage_map.json'))!=r['lineage_map_hash'] or digest(read_json(root/'reconciled_generation_budget.json'))!=r['budget_hash']:
        raise ValueError('Resolved lineage/budget changed')
    if digest(read_json(root/'exposure.json'))!=r['exposure']['inventory_sha256']:raise ValueError('Exposure inventory changed')
    for n,h in read_json(root/'evidence_inventory.json').items():
        if file_hash(root/safe_relative(n))!=h:raise ValueError('Evidence changed')
    if not r['fixture']:
        if r['source_code']!=code_identity(Path(__file__).resolve().parents[4]):raise ValueError('Pinned evaluation source changed')
        exposure_check(read_json(root/'evidence/plan.json')['source'],read_json(root/'exposure.json'))
    return r
