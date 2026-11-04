"""Bind the reviewed seal to a new, initially inactive native execution owner."""
from pathlib import Path
from ...util import digest, file_hash, read_json
from ...environment import code_identity
from ...studies.heterogeneity import immutable
from .. import documented_preflight as cpu
from ..allocation_v3 import design as d, evidence
from ..gpqa_source.contracts import allocation_inputs

VERSION = 'documented_stage2_execution_v1'
RUN = 'pact-stage2-documented-execution-001'
CPU_RECEIPT = 'b4c6d7433ed7fa1a2fa367027268b39cb26aabc5d08a7ba8a38ab3b54e74e7e8'
REPO = Path(__file__).resolve().parents[4]


def assemble(training, candidate, graph, receipt, parent, source_code, fixture=False):
    allocation_inputs(training)
    if graph['counts'] != {p:d.BUDGET[p] for p in ('assay','policy')}:
        raise ValueError('compiled_budget_changed')
    if graph['reserved_output_tokens'] != d.BUDGET['reserved_tokens']:
        raise ValueError('compiled_token_budget_changed')
    for obj, key in ((training,'training_dependency_hash'),(candidate,'candidate_digest'),(graph,'graph_digest')):
        if digest(obj) != receipt[key]:raise ValueError('frozen_identity_changed')
    return {'version':VERSION,'run_id':RUN,'policy_run_id':RUN,'fixture':fixture,
        'source_code':source_code,'parent_path':str(Path(parent).resolve()),
        's0':{f:training['s0'][f]['adapter_hash'] for f in d.FAMILIES},
        'training_source':{'records':training['records'],'labels':training['labels']},
        'blocks':training['blocks'],'shuffle':training['shuffle'],
        'probes':{f:[r['task']['task_id'] for r in training['records']
                    if r['split']=='allocation_probe' and r['family']==f] for f in d.SOURCES},
        'native_contract_hashes':evidence.AUTHORITATIVE_FILES,
        'budgets':d.BUDGET,'analysis':d.ANALYSIS,'train':d.TRAIN,
        'freeze':{k:receipt[k] for k in ('candidate_digest','graph_digest','training_dependency_hash','method_digest')},
        'cpu_receipt_sha256':CPU_RECEIPT,'historical_spending':None,'remaining_historical_budget':None,
        'execution_authorized_by_plan':False,'evaluation_source_weights':{'gpqa_main':.5,'logiqa':.5},
        'source_standard':'documented_exclusion_screened_development',
        'limitations':receipt.get('limitations',[])}


def prepare(root, seal, preflight, parent):
    root,seal,preflight,parent=map(Path,(root,seal,preflight,parent))
    from ..gpqa_source.sources import private_path
    from ..documented_freeze import no_symlinks
    private_path(root);no_symlinks(root)
    if root.exists() or root.name!=RUN:raise ValueError('new_exact_child_destination_required')
    receipt,training,method=cpu.verify_seal(seal)
    if file_hash(preflight/'preflight.sanitized.json')!=CPU_RECEIPT:
        raise ValueError('exact_CPU_receipt_required')
    public=read_json(preflight/'preflight.sanitized.json')
    if not public['current_S0_tensors_verified'] or not public['packages']['matches']:
        raise ValueError('CPU_prerequisite_failed')
    if evidence.executed_source(parent)!=read_json(seal/'evidence/source.private.json'):
        raise ValueError('parent_source_changed')
    identity=code_identity(REPO)
    if identity['dirty'] or not identity['git_commit']:raise ValueError('clean_pinned_checkout_required')
    candidate=read_json(seal/'sealed/prospective.private.json');graph=read_json(seal/'sealed/graph.private.json')
    p=assemble(training,candidate,graph,receipt,parent,identity)
    p['scratch_root']=str(root.resolve())
    p['seal_path']=str(seal.resolve())
    p['parent_files']={n:file_hash(parent/n) for n in (
        'checkpoint_inventory.private.json','training_lineage_map.json','inference_identity_manifest.json','evidence/access.json')}
    root.mkdir(parents=True,mode=0o700)
    immutable(root/'sealed/prospective.private.json',candidate)
    immutable(root/'sealed/graph.private.json',graph)
    p['prospective_hash']=file_hash(root/'sealed/prospective.private.json')
    p['graph_file_hash']=file_hash(root/'sealed/graph.private.json')
    immutable(root/'plan.json',p)
    return {'status':'EXECUTION_PLAN_INACTIVE','plan_hash':digest(p),'model_calls':0,
            'wallet_active':False,'historical_spending':None,'conditional_limits':d.BUDGET}


def validate(root, expected_hash):
    root=Path(root);p=read_json(root/'plan.json')
    from ..documented_freeze import no_symlinks
    no_symlinks(root)
    if p['version']!=VERSION or p['run_id']!=RUN or digest(p)!=expected_hash:
        raise ValueError('exact_child_plan_required')
    if p['budgets']!=d.BUDGET or p['analysis']!=d.ANALYSIS or p['train']!=d.TRAIN:
        raise ValueError('scientific_contract_changed')
    for name,key in (('prospective.private.json','prospective_hash'),('graph.private.json','graph_file_hash')):
        if file_hash(root/'sealed'/name)!=p[key]:raise ValueError('sealed_payload_changed')
    if not p['fixture']:
        if root.name!=RUN or str(root.resolve())!=p['scratch_root'] or p['source_code']!=code_identity(REPO):
            raise ValueError('pinned_checkout_or_owner_changed')
        receipt,training,_=cpu.verify_seal(Path(p['seal_path']))
        if p['freeze']!={k:receipt[k] for k in p['freeze']}:raise ValueError('freeze_changed')
        for n,h in p['parent_files'].items():
            if file_hash(Path(p['parent_path'])/n)!=h:raise ValueError('parent_changed')
        if p['training_source']!={'records':training['records'],'labels':training['labels']}:
            raise ValueError('training_source_changed')
    if (root/'policies.json').exists():
        if read_json(root/'policy-freeze-receipt.json')['sha256']!=file_hash(root/'policies.json'):
            raise ValueError('frozen_policies_changed')
    if (root/'policy-lock.json').exists():
        if read_json(root/'policy-lock-receipt.json')['sha256']!=file_hash(root/'policy-lock.json'):
            raise ValueError('policy_checkpoint_lock_changed')
        lock=read_json(root/'policy-lock.json');allocation=read_json(root/'policies.json')
        if lock['aliases']!=allocation['aliases'] or set(lock['teams'])!={'S0',*lock['aliases'].values()}:
            raise ValueError('policy_alias_lock_changed')
    return p
