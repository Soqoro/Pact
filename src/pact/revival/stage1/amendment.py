"""Explicitly approved additional evaluation envelope; parent history stays open."""
from collections import Counter
from pathlib import Path
import json
import shutil
import tempfile

from ...environment import code_identity
from ...artifacts import safe_relative
from ...util import digest, file_hash, read_json, write_json
from ...studies.forensics import private_root
from . import evidence

RUN = 'pact-revival-stage1-evaluation-amended-002'
VERSION = 'stage1_approved_additional_evaluation_v1'
PROPOSAL_HASH = '49de20c60cb493467fb940b5f27e98280bd7ba0021d612db69c6cb86125642a6'
PRIVATE = '6836c626fbfb502c7da4f59db2f70280669db84611ef155280fcc73f8626efda'
SANITIZED = '86b29cf813b729e3af57fe7726cecbd33c15e86a811831154c438fe1fcf7d687'
CAPS = {'validation':4224,'source_evaluation':8448,'fixed_history':1920,'attack':0}
APPROVAL = {'version':'stage1_accounting_approval_v1','proposal_hash':PROPOSAL_HASH,
            'approved':True,'authority':'user_explicit_proceed_after_artifact_bound_amendment_question',
            'scope':'implement_separate_child_with_additional_budget_and_possible_historical_repeats',
            'automatic_gpu_execution':False}
REPO = Path(__file__).resolve().parents[4]


def proposal():
    value=read_json(REPO/'docs/stage1_evaluation_accounting_amendment_proposal.json')
    if digest(value)!=PROPOSAL_HASH:raise ValueError('Approved proposal changed')
    return value


def is_amended(root):
    return read_json(root/'contract_resolution.json')['version']==VERSION


def run_id(root):
    return RUN if is_amended(root) else evidence.RUN


def validate_parent(read,checks,fixture=False):
    p=proposal();r=read('contract_resolution.json');v=read('checkpoint_verification_receipt.json')
    if bool(r['fixture'])!=fixture or bool(v['fixture'])!=fixture:raise ValueError('Fixture/real boundary')
    if not v['ready'] or v['synthetic_completed']!=16 or v['synthetic_attempts']!=16:
        raise ValueError('Completed verification required')
    if any(v[k]!=0 for k in ('generation_calls','training_forwards','optimizer_updates','teacher_forced_scoring_forwards')):
        raise ValueError('Unexpected parent work')
    if any(n.startswith(('intents/','calls/','stages/')) or n=='plan.json' for n in checks):
        raise ValueError('Parent already evaluated; exact verification-only parent required')
    inv=read('checkpoint_inventory.private.json');lineage=read('training_lineage_map.json')
    if digest(inv)!=v['inventory_hash'] or len(inv)!=6 or set(inv)!=set(lineage):raise ValueError('Inventory binding')
    for fit,row in inv.items():
        if not row['historical_tensor_verified'] or row['adapter_hash']!=lineage[fit]['expected_adapter_hash'] or row['file_sha256']!=lineage[fit]['expected_file_sha256']:
            raise ValueError('Historical adapter binding')
    for i in range(1,17):
        intent=read(f'synthetic/intents/{i:02}.json');result=read(f'synthetic/results/{i:02}.json')
        if result['intent_hash']!=digest(intent) or not result['finite']:raise ValueError('Verification links')
    if not fixture:
        bound={'contract_resolution.json':'original_resolution_hash',
               'reconciled_generation_budget.json':'original_budget_hash',
               'checkpoint_verification_receipt.json':'verification_receipt_hash',
               'inference_identity_manifest.json':'inference_identity_manifest_hash'}
        for name,key in bound.items():
            if digest(read(name))!=p[key]:raise ValueError('Approved prerequisite differs')
        parent=read('evidence/parent_plan.json')
        if digest(parent['source'])!=p['frozen_source_hash'] or digest(parent['peer_use'])!=p['peer_use_hash']:
            raise ValueError('Frozen selection differs')
        counts={s:dict(Counter(x['family'] for x in parent['source']['records'] if x['split']==s)) for s in p['allocation']}
        if counts!=p['allocation']:raise ValueError('Executed allocation differs')
    return r


def initialize(root,bundle,approval_hash,*,fixture=False):
    if approval_hash!=PROPOSAL_HASH:raise ValueError('Explicit approved proposal hash required')
    if root.exists():raise ValueError('Absent separate child required; no replan')
    if not fixture and root.name!=RUN:raise ValueError('Reserved amended child required')
    current=code_identity(REPO)
    if not fixture and (current['dirty'] or not current['git_commit']):raise ValueError('Clean pinned child source required')
    z,checks=evidence.archive(bundle,None if fixture else PRIVATE)
    try:
        read=lambda n:json.loads(z.read(n))
        original=validate_parent(read,checks,fixture)
        root.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=root.parent,prefix='.amended-import-') as tmp:
            stage=Path(tmp)/'run';private_root(stage,fixture)
            # Historical mutable state stays under provenance, never the new journal.
            relocate={'contract_resolution.json','reconciled_generation_budget.json','recovery.json','storage_transition.json','cache_repair_receipt.json'}
            for name in checks:
                renamed='parent_verification/'+name if name in relocate or name.startswith(('synthetic/','exports/','export_reviews/')) else name
                target=stage/safe_relative(renamed);target.parent.mkdir(parents=True,exist_ok=True)
                with z.open(name) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
            write_json(stage/'amendment_approval.json',APPROVAL)
            write_json(stage/'amendment_proposal.json',proposal())
            # Bind every imported payload (including archived verification attempts).
            imported={f.relative_to(stage).as_posix():file_hash(f) for f in sorted(stage.rglob('*')) if f.is_file()}
            write_json(stage/'amendment_parent_inventory.json',imported)
            old_budget=read('reconciled_generation_budget.json')
            budget={**old_budget,'ownership_status':'approved_additional_envelope',
                    'owner_plan':PROPOSAL_HASH,'owner_source':'amendment_approval.json',
                    'remaining_component_upper_bounds':CAPS,'new_attempt_cap':14592,
                    'new_reserved_output_token_cap':7471104,'smoke_attempt_cap':66,
                    'historical_accounting':proposal()['historical_accounting'],
                    'original_budget_hash':digest(old_budget),'inherited_synthetic_forwards':16}
            write_json(stage/'reconciled_generation_budget.json',budget)
            resolution={**original,'version':VERSION,'run_id':RUN,'source_code':current,
                        'evidence_sha256':file_hash(bundle),'budget_hash':digest(budget),
                        'blockers':[],'status':'resolved_by_explicit_amendment',
                        'original_resolution_hash':digest(original),'historical_execution_closed':False,
                        'original_blockers_preserved':original['blockers'],
                        'amendment_hash':PROPOSAL_HASH,'approval_hash':digest(APPROVAL),
                        'parent_inventory_hash':digest(imported),'new_synthetic_forwards':0}
            write_json(stage/'contract_resolution.json',resolution)
            validate(stage,resolution)
            stage.rename(root)
        return {'run_id':RUN,'resolution_hash':digest(resolution),'new_generation_cap':14592,
                'new_synthetic_forwards':0,'historical_execution_closed':False,'model_calls':0}
    finally:z.close()


def validate(root,r):
    if r['run_id']!=RUN or r['amendment_hash']!=PROPOSAL_HASH or r['blockers'] or r['historical_execution_closed'] is not False:
        raise ValueError('Amendment resolution changed')
    if read_json(root/'amendment_approval.json')!=APPROVAL or digest(APPROVAL)!=r['approval_hash']:
        raise ValueError('Explicit approval changed')
    if digest(read_json(root/'amendment_proposal.json'))!=PROPOSAL_HASH:raise ValueError('Proposal changed')
    inv=read_json(root/'amendment_parent_inventory.json')
    if digest(inv)!=r['parent_inventory_hash']:raise ValueError('Parent inventory changed')
    for name,h in inv.items():
        if file_hash(root/safe_relative(name))!=h:raise ValueError('Imported verification evidence changed')
    budget=read_json(root/'reconciled_generation_budget.json')
    if (budget['remaining_component_upper_bounds']!=CAPS or budget['new_attempt_cap']!=14592
        or budget['new_reserved_output_token_cap']!=7471104 or budget['smoke_attempt_cap']!=66
        or budget['ownership_status']!='approved_additional_envelope'
        or budget['historical_accounting']!=proposal()['historical_accounting']):raise ValueError('Amended budget changed')
    if any((root/'synthetic').rglob('*.json')):raise ValueError('New synthetic forwards forbidden')
    if not r['fixture'] and code_identity(REPO)!=r['source_code']:raise ValueError('Pinned amended source changed')
