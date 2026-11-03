"""Deterministic proposed MethodSpec, bounded graph, safe CPU recovery and handoff."""
import copy
import hashlib
import json
import zipfile
from pathlib import Path
from ...util import canonical, digest, file_hash, read_json, write_json
from .. import development_amendment as proposal
from ..allocation_v3 import design
from ..gpqa_source import graph, contracts, sources
from .audit import VERSION, CHILD, LIMITATIONS

APPROVAL = {'child':CHILD,'scope':'implementation_and_CPU_validation_only',
    'accepted_proposal_digest':'ddda40a0802b5d3e8b72640e22e72722c710dc32a7fcf1968c73f1c15f07da09',
    'documented_exclusion_standard_accepted':True,'conditional_ceiling_accepted':True,
    'cohort_accepted':False,'physical_spending_authorized':False,'GPU_authorized':False}
FILES = {'source.private.json','lineage.private.json','audit.private.json','training.private.json',
         'candidate.private.json','graph.private.json','method.private.json','summary.sanitized.json','manifest.json'}


def compile_graph(source, candidate, lineage):
    inherited = graph.compile_graph(source, candidate, lineage)
    # Separate physical namespace while preserving all scientific seeds and
    # dependency semantics. Old v3 and GPQA v2 graphs remain immutable.
    binding = digest([VERSION, APPROVAL, inherited['binding_hash']])
    ids = {n['id']:digest([binding,n['id']]) for n in inherited['nodes']}
    def remap(value):
        if isinstance(value,str):return ids.get(value,value)
        if isinstance(value,list):return [remap(v) for v in value]
        if isinstance(value,dict):return {k:remap(v) for k,v in value.items()}
        return value
    result = remap(inherited)
    result.update(version=VERSION,binding_hash=binding,owner=CHILD,dispatchable=False)
    return result


def assemble(source, lineage, audit, candidate):
    if candidate is not None and not audit['fixture']:
        eligibility=audit['eligibility']
        if candidate != sources.select(eligibility['screened_rows'],eligibility['screened_labels']):
            raise ValueError('deterministic_cohort_selection_conflict')
    training = contracts.training_contract(source,lineage['S0'])
    if not audit['fixture'] and digest(training)!=proposal.TRAINING_HASH:
        raise ValueError('starting_checkpoint_or_training_contract_changed')
    compiled = compile_graph(source,candidate,lineage) if candidate else None
    method = {'version':VERSION,'child':CHILD,'status':'PROPOSED_REVIEW_REQUIRED','approval':APPROVAL,
        'training_dependency_hash':digest(training),'S0':lineage['S0'],
        'candidate_digest':digest(candidate) if candidate else None,
        'graph_digest':digest(compiled) if compiled else None,'audit_digest':digest(audit),
        'conditional_limits':design.BUDGET,'budget_reconciliation':graph.budget_reconciliation(source),
        'method_contract':graph.contract(),'evaluation_source_weights':dict.fromkeys(sources.SOURCES_EVAL,.5),
        'limitations':LIMITATIONS,'historical_spending':None,'remaining_historical_budget':None,
        'physical_wallet_active':False,'cohort_frozen':False,
        'execution_prerequisites':['explicit_artifact_bound_cohort_review','new_physical_spending_approval',
            'exact_S0_tensor_reload','exact_native_runtime_and_access','frozen_graph_and_rendered_context_caps',
            'stage_bound_execution_grant','no_unresolved_child_attempts'],
        'policy_evaluation_prerequisites':['complete_assay','five_prespecified_policies_frozen',
            'all_checkpoint_hashes_and_alias_contracts_locked','analysis_and_cohort_unchanged'],
        'readout':'pristine_R','evaluation_messages':'own_team_generated_initial_and_revised_packets',
        'evaluation_sealed_from':'training_and_allocation_inputs',
        'reporter':'pact.revival.gpqa_source.results.report',
        'code_hashes':{p.name:file_hash(p) for p in sorted(Path(__file__).parent.glob('*.py'))}}
    elig = audit.get('eligibility')
    public = {'version':VERSION,'child':CHILD,'fixture':audit['fixture'],
        'status':'PROPOSED_COHORT_REQUIRES_REVIEW' if candidate else 'SOURCE_AUDIT_BLOCKED',
        'screened_unique_groups':elig['screened_unique_groups'] if elig else None,
        'proposed_cohort_counts':dict.fromkeys(sources.SOURCES_EVAL,64) if candidate else None,
        'blockers':audit['blockers'],'candidate_digest':method['candidate_digest'],
        'graph_digest':method['graph_digest'],'compiled_counts':compiled['counts'] if compiled else None,
        'training_dependency_hash':digest(training),'conditional_limits':design.BUDGET,
        'budget_reconciliation':method['budget_reconciliation'],'limitations':LIMITATIONS,
        'semantic_decontamination':False,'project_freshness_certified':False,
        'historical_spending':None,'remaining_budget':None,'cohort_frozen':False,
        'execution_authorized':False,'wallet_active':False,'model_calls':0,'training_forwards':0}
    values = {'source.private.json':source,'lineage.private.json':lineage,'audit.private.json':audit,
              'training.private.json':training,'method.private.json':method,'summary.sanitized.json':public}
    if candidate:values.update({'candidate.private.json':candidate,'graph.private.json':compiled})
    return json.loads(canonical(values))


def output_path(root, fixture, metadata_only=False):
    root = Path(root)
    if any(p.is_symlink() for p in (root,*root.parents)):raise ValueError('symlink_output')
    if not fixture and not metadata_only:sources.private_path(root)
    if metadata_only:
        repo=Path(__file__).resolve().parents[4]
        if not root.resolve().is_relative_to(repo/"results_import"):
            sources.private_path(root)
    return root


def save(root, source, lineage, audit, candidate=None):
    metadata_only = candidate is None and audit.get('eligibility') is None and all(v.get('status')=='source_bytes_unavailable' for v in audit.get('sources',{}).values())
    root=output_path(root,audit['fixture'],metadata_only);values=assemble(source,lineage,audit,candidate)
    checks={n:hashlib.sha256((canonical(v)+'\n').encode()).hexdigest() for n,v in values.items()}
    if root.exists():
        if read_json(root/'manifest.json')!=checks:raise ValueError('incompatible_recovery_use_separate_destination')
        return validate(root)
    root.mkdir(parents=True,mode=0o700)
    for n,v in values.items():write_json(root/n,v)
    write_json(root/'manifest.json',checks)
    return validate(root)


def validate(root):
    root=Path(root);checks=read_json(root/'manifest.json')
    if not set(checks)<=FILES-{'manifest.json'}:raise ValueError('unexpected_private_member')
    for n,h in checks.items():
        if (root/n).is_symlink() or file_hash(root/n)!=h:raise ValueError('manifest_conflict')
    values={n:read_json(root/n) for n in checks}
    expected=assemble(values['source.private.json'],values['lineage.private.json'],values['audit.private.json'],values.get('candidate.private.json'))
    if values!=expected:raise ValueError('compiled_contract_conflict')
    return expected['summary.sanitized.json']


def export(root):
    root=Path(root);public=validate(root);dest=root/'bundles';dest.mkdir(exist_ok=True,mode=0o700)
    receipt={}
    for kind in ('PRIVATE','SANITIZED'):
        names=sorted(set(read_json(root/'manifest.json'))|{'manifest.json'}) if kind=='PRIVATE' else ['summary.sanitized.json']
        data={n:(root/n).read_bytes() for n in names}
        checks={n:hashlib.sha256(v).hexdigest() for n,v in data.items()}
        handoff={'version':VERSION,'kind':kind,'child':CHILD,'execution_authorized':False}
        destfile=dest/f'{CHILD}-{kind}-{digest(checks)[:16]}.zip'
        if not destfile.exists():
            with zipfile.ZipFile(destfile,'x',zipfile.ZIP_DEFLATED) as z:
                for n,v in data.items():z.writestr(n,v)
                z.writestr('checksums.json',canonical(checks));z.writestr('HANDOFF.json',canonical(handoff))
        with zipfile.ZipFile(destfile) as z:
            if len(z.namelist())!=len(checks)+2 or set(z.namelist())!=set(checks)|{'checksums.json','HANDOFF.json'} or json.loads(z.read('HANDOFF.json'))!=handoff or any(hashlib.sha256(z.read(n)).hexdigest()!=h for n,h in checks.items()):
                raise ValueError('existing_export_conflict')
        receipt[kind]={'filename':destfile.name,'sha256':file_hash(destfile),'bytes':destfile.stat().st_size}
    return receipt


def restore(bundle, sha, root):
    """CPU audit recovery only: never restore a scientific wallet or resume work."""
    if file_hash(bundle)!=sha:raise ValueError('archive_digest_conflict')
    with zipfile.ZipFile(bundle) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or not set(names)<=FILES|{'checksums.json','HANDOFF.json'}:
            raise ValueError('archive_member_conflict')
        if sum(v.file_size for v in z.infolist())>256*1024**2:raise ValueError('archive_size_bound')
        if json.loads(z.read('HANDOFF.json'))!={'version':VERSION,'kind':'PRIVATE','child':CHILD,'execution_authorized':False}:
            raise ValueError('private_child_archive_required')
        checks=json.loads(z.read('checksums.json'))
        if set(checks)!=set(names)-{'checksums.json','HANDOFF.json'}:raise ValueError('archive_inventory_conflict')
        values={}
        for n,h in checks.items():
            raw=z.read(n)
            if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('archive_member_digest_conflict')
            values[n]=json.loads(raw)
    expected=assemble(values['source.private.json'],values['lineage.private.json'],values['audit.private.json'],values.get('candidate.private.json'))
    if {k:v for k,v in values.items() if k!='manifest.json'}!=expected:raise ValueError('recovery_contract_conflict')
    return save(root,values['source.private.json'],values['lineage.private.json'],values['audit.private.json'],values.get('candidate.private.json'))


def execution_guard(root, stage, method_hash, *, checkpoint_receipt=None, policy_lock=None):
    """Read-only guard. CPU approval cannot create or activate a spending wallet.

    This child intentionally has no bypass accepting a hand-written authorization
    boolean. A subsequent reviewed execution amendment must add the real grant
    and dispatch adapter, bound to the concrete cohort/graph returned here.
    """
    validate(root);root=Path(root);method=read_json(root/'method.private.json')
    if digest(method)!=method_hash:raise ValueError('exact_method_required')
    if stage not in ('assay-smoke','collect','branch','score','policy-freeze','continuation','policy-lock','evaluation-smoke','evaluate'):
        raise ValueError('stage_not_owned')
    if method['candidate_digest'] is None:raise ValueError('no_proposed_cohort')
    if any((root/n).exists() for n in ('INFLIGHT.json','SNAPSHOT_PENDING.json','attempts','events')):
        raise ValueError('unexpected_or_unresolved_execution_state')
    if checkpoint_receipt is None or checkpoint_receipt.get('S0')!=method['S0'] or checkpoint_receipt.get('tensors_verified') is not True:
        raise ValueError('exact_checkpoint_reload_required')
    if stage in ('evaluation-smoke','evaluate'):
        if not policy_lock or any(policy_lock.get(k)!=v for k,v in {
            'candidate_digest':method['candidate_digest'],'graph_digest':method['graph_digest'],
            'analysis_digest':digest(design.ANALYSIS),'policies':list(design.POLICIES),
            'all_checkpoint_hashes_locked':True}.items()):raise ValueError('all_policies_checkpoints_analysis_must_lock')
    raise PermissionError('CPU_approval_only_no_physical_spending_grant')
