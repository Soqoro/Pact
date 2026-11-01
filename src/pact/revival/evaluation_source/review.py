"""Local review, immutable candidate artifacts and aggregate-only handoff."""
from pathlib import Path
from collections import Counter
from dataclasses import asdict
import hashlib
import json
import zipfile
import subprocess
from ...util import digest, file_hash, read_json, write_json, canonical
from ...schemas import task_from_dict
from ...studies.forensics import private_root
from ..allocation_v3 import evidence as e, design as d
from . import sources as s, graph as g


def lineage(parent, history_roots=(), parent_bundle=None):
    source=e.executed_source(parent)
    if parent_bundle:
        if file_hash(Path(parent_bundle))!=e.PARENT_SHA: raise ValueError('exact_parent_required')
        with zipfile.ZipFile(parent_bundle) as z:
            checks=json.loads(z.read('checksums.json'))
            for name in [*e.AUTHORITATIVE_FILES,'summary.json']:
                if file_hash(parent/name)!=checks[name]: raise ValueError('parent_archive_member_conflict')
    else:
        receipt=read_json(parent/'import-receipt.json')
        if receipt['sha256']!=e.PARENT_SHA: raise ValueError('exact_parent_required')
        if file_hash(parent/'summary.json')!=receipt['files']['summary.json']:
            raise ValueError('parent_summary_conflict')
    summary=read_json(parent/'summary.json')
    if summary['accounting']['new_committed']!=13467 or summary['accounting']['unresolved'] or not all(summary['stage_status'].values()):
        raise ValueError('completed_stage_I_required')
    inventory=read_json(parent/'checkpoint_inventory.private.json')
    conflicts=e.old_assay_conflicts([parent,*map(Path,history_roots)])
    for history_root in history_roots:
        for path in Path(history_root).glob('**/attempts/*.json'):
            owner=read_json(path).get('identity',{}).get('owner','')
            if owner in (d.ASSAY,d.POLICY,g.ASSAY,g.POLICY): conflicts.append(str(path))
    value={'parent_sha256':e.PARENT_SHA,'source_sha256':digest(source),
           'block_hash':digest(source['blocks']),'actual_counts':e.source_contract(source),
           'S0':{f:inventory['uniform_joint_sft/'+f] for f in d.FAMILIES},
           'access_hash':file_hash(parent/'evidence/access.json'),
           'historical_checkpoint_receipts_verified':True,'current_tensor_reload_verified':False,
           'parent_journal_committed':13467,'parent_v3':e.prospective_capacity(source),
           'local_history_conflicts':sorted(set(conflicts)),
           'external_history_reconciled':False}
    return source,value


def immutable_root(root, fixture=False):
    root=Path(root)
    if not fixture:
        # Existing ignored import area is private local evidence, never a Git artifact.
        resolved=root.resolve()
        imported=s.REPO/'results_import'
        if resolved.is_relative_to(imported):
            if any(p.is_symlink() for p in (root,*root.parents)):
                raise ValueError('symlink_private_destination')
            relative=str(resolved.relative_to(s.REPO))
            ignored=subprocess.run(['git','check-ignore','-q','--',relative+'/audit.private.json'],cwd=s.REPO).returncode==0
            tracked=subprocess.check_output(['git','ls-files','--',relative],cwd=s.REPO,text=True)
            if not ignored or tracked: raise ValueError('private_import_must_be_ignored_and_untracked')
        else: private_root(root)
    if root.exists() and any(root.iterdir()): raise ValueError('existing_child_collision; never overwrite or reseal')
    root.mkdir(parents=True,exist_ok=True,mode=0o700)
    return root


def acquisition_plan(spec=None):
    """Manual materialization review only. This module has no networking API."""
    blockers=['separate_source_access_approval_required','source_rights_unresolved']
    identity=None
    if spec:
        identity=s.check_spec(spec)
        if s.reviewed_documents(spec.get('rights_review'),identity): blockers.remove('source_rights_unresolved')
    else: blockers+=['immutable_revision_unresolved','raw_source_digest_unavailable','official_train_file_unreviewed']
    return {'status':'PROPOSED_ACQUISITION_ONLY','source':identity,
            'candidate':{'repository':'allenai/openbookqa','config':'main','split':'train'},
            'blockers':blockers,'maximum_files':1,'maximum_bytes':s.MAX_BYTES,
            'approved':False,'network_requests':0,'automatic_downloader_implemented':False,
            'procedure':['Review official immutable commit, exact main/train file, origin and content digest independently.',
                         'Resolve rights for this proposed closed-book project use; retain source terms and human receipt.',
                         'Obtain separate explicit user approval to acquire that single pinned file.',
                         'Manually transfer that approved file to private storage; never download validation/test/additional.',
                         'Invoke audit with the exact raw path and source-spec; local hash/schema checks precede eligibility.'],
            'no_scripts_pickle_remote_code_or_mutable_mirror':True}


def audit(root, parent, ob_path=None, spec=None, cache=None, exposure=None, history=None, history_roots=(), parent_bundle=None):
    root=Path(root)
    source,ln=lineage(Path(parent),history_roots,parent_bundle)
    blockers=[]
    if history and e.reviewed_history(history) and not ln['local_history_conflicts']:
        ln['external_history_reconciled']=True
    else: blockers.append('external_probe_consumption_unresolved')
    if ln['local_history_conflicts']: blockers.append('historical_stage2_collision')
    exposure=exposure or {}
    exposure_report=s.exposure_status(exposure,source)
    blockers+=exposure_report['blockers']
    if spec:
        ob,ob_report=s.load_openbook(ob_path,spec)
    else:
        ob=None;ob_report={'status':'source_bytes_unavailable','raw_rows':None,
                           'source_identity_reviewed':False,'rights_reviewed':False,
                           'revision':None,'sha256':None}
    if ob is None: blockers.append('openbookqa:source_bytes_unavailable')
    if not ob_report.get('source_identity_reviewed'): blockers.append('openbookqa:source_identity_unreviewed')
    if not ob_report.get('rights_reviewed'): blockers.append('openbookqa:source_rights_unresolved')
    train,val,log_report=s.original_sources(cache)
    if train is None: blockers.append('logiqa:source_bytes_unavailable')
    log_rights=(spec or {}).get('logiqa_rights_review')
    log_identity={'family':'logiqa',**s.TRAIN_SOURCES['logiqa']}
    log_report['rights_reviewed']=s.reviewed_documents(log_rights,log_identity)
    if not log_report['rights_reviewed']: blockers.append('logiqa:source_rights_unresolved')
    candidate=None;elig=None
    if ob is not None and train is not None:
        rows,labels,elig=s.eligibility(ob,train,val,source,exposure,
            source_reviewed={'openbookqa':bool(ob_report.get('rights_reviewed') and ob_report.get('source_identity_reviewed')),
                             'logiqa':log_report['rights_reviewed']})
        if any(elig['counts'][f]['permitted_unique_groups']<64 for f in s.SOURCES_EVAL):
            blockers.append('prospective_eval_not_feasible_or_unverified')
        if not blockers: candidate=s.select(rows,labels)
    audits={'version':g.VERSION,'status':'candidate_selected' if candidate else 'BLOCKED',
            'fixture':False,'sources':{'openbookqa':ob_report,'logiqa':log_report},
            'eligibility':elig,'exposure':exposure_report,'blockers':sorted(set(blockers)),
            'cohort_approved':False,'gpu_execution_authorized':False,
            'model_calls':0,'downloads':0,'pretraining_exposure':'unknown',
            'budget_reconciliation':g.budget_reconciliation(source)}
    graph=g.compile_graph(source,candidate,ln) if candidate else None
    method=g.proposed_method(ln,audits,candidate,graph)
    immutable_root(root)
    for name,value in [('source.private.json',source),('lineage.private.json',ln),('audit.private.json',audits),
                       ('method.private.json',method),('acquisition-plan.json',acquisition_plan(spec))]:
        write_json(root/name,value)
    if candidate:
        # These are private candidate records, not a runtime training plan or approved cohort.
        write_json(root/'candidate.private.json',candidate)
        write_json(root/'graph.private.json',graph)
    write_json(root/'summary.json',sanitize(audits,method,graph))
    return read_json(root/'summary.json')


def sanitize(audit,method,graph):
    counts=None if audit['eligibility'] is None else audit['eligibility']['counts']
    # Explicit aggregate allowlist: never source-row IDs or decodable per-ID hashes.
    return {'version':g.VERSION,'status':audit['status'],'fixture':audit['fixture'],
            'blockers':audit['blockers'],'source_status':{f:{'status':v['status'],
                'raw_rows':v.get('raw_rows'),'schema_rejections':v.get('rejection_counts'),
                'rights_reviewed':v.get('rights_reviewed',False)} for f,v in audit['sources'].items()},
            'eligibility_counts':counts,'candidate_selected':method['candidate_digest'] is not None,
            'cohort_approved':False,'gpu_execution_authorized':False,'pretraining_exposure':'unknown',
            'closed_book':True,'post_stage_I_design_revision':True,
            'evaluation_source_weights':dict.fromkeys(s.SOURCES_EVAL,.5),
            'training_source_weights':d.SOURCE_WEIGHTS,'conditional_ceiling':d.BUDGET,'budget_reconciliation':audit['budget_reconciliation'],
            'compiled_graph_counts':graph['counts'] if graph else None,
            'compiled_smoke_counts':{k:len(v) for k,v in graph['smoke_manifest'].items()} if graph else None,
            'request_graph_fully_resolved':False,'new_model_calls':0,'new_training_forwards':0,
            'scientific_result':None,'native_model_behavior_verified':False}


def validate(root):
    root=Path(root)
    method=read_json(root/'method.private.json');audits=read_json(root/'audit.private.json')
    ln=read_json(root/'lineage.private.json');source=read_json(root/'source.private.json')
    if method['version']!=g.VERSION or method['child']!=g.CHILD or method['execution_enabled']:
        raise ValueError('incompatible_or_executable_method')
    if not audits['fixture'] and digest(source)!=e.EXECUTED_SOURCE_HASH: raise ValueError('source_identity_conflict')
    if audits['fixture'] and digest(source)!=digest(e.fixture_source()): raise ValueError('fixture_source_identity_conflict')
    if audits['budget_reconciliation']!=g.budget_reconciliation(source): raise ValueError('budget_conflict')
    candidate=read_json(root/'candidate.private.json') if (root/'candidate.private.json').exists() else None
    graph=read_json(root/'graph.private.json') if candidate else None
    if graph and graph!=g.compile_graph(source,candidate,ln): raise ValueError('request_graph_conflict')
    if method!=g.proposed_method(ln,audits,candidate,graph): raise ValueError('method_conflict')
    result=sanitize(audits,method,graph)
    if read_json(root/'summary.json')!=result: raise ValueError('summary_reconstruction_conflict')
    return result


def export(root):
    root=Path(root);summary=validate(root)
    destination=root/'bundles';destination.mkdir(exist_ok=True,mode=0o700)
    private={p.name:p.read_bytes() for p in sorted(root.glob('*.json'))}
    public={'summary.json':(canonical(summary)+'\n').encode()}
    if (root/'mock-summary.json').exists():
        from . import results
        expected=results.report(read_json(root/'candidate.private.json'),read_json(root/'mock-outcomes.private.json'))
        if read_json(root/'mock-summary.json')!=expected: raise ValueError('mock_summary_conflict')
        public['mock-summary.json']=(canonical(expected)+'\n').encode()
    receipts={}
    for kind,files in [('PRIVATE',private),('SANITIZED',public)]:
        checks={name:hashlib.sha256(data).hexdigest() for name,data in files.items()}
        path=destination/f'{g.CHILD}-{kind}-{digest(checks)[:16]}.zip'
        if path.exists():
            with zipfile.ZipFile(path) as z:
                if json.loads(z.read('checksums.json'))!=checks: raise ValueError('bundle_collision')
        else:
            with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED) as z:
                for name,data in files.items(): z.writestr(name,data)
                z.writestr('checksums.json',canonical(checks))
                z.writestr('HANDOFF.json',canonical({'version':g.VERSION,'kind':kind,'execution_enabled':False}))
        with zipfile.ZipFile(path) as z:
            if set(z.namelist())!=set(checks)|{'checksums.json','HANDOFF.json'} or any(hashlib.sha256(z.read(k)).hexdigest()!=v for k,v in checks.items()):
                raise ValueError('handoff_verification_failed')
        receipts[kind]={'path':str(path),'sha256':file_hash(path),'bytes':path.stat().st_size}
    return receipts


def reconstruct(bundle,sha,output):
    from ..stage1.evidence import archive
    z,checks=archive(Path(bundle),sha)
    try:
        allowed={'source.private.json','lineage.private.json','audit.private.json','method.private.json',
                 'acquisition-plan.json','summary.json','candidate.private.json','graph.private.json',
                 'mock-outcomes.private.json','mock-summary.json'}
        if not set(checks)<=allowed or 'source.private.json' not in checks: raise ValueError('private_review_bundle_required')
        fixture=json.loads(z.read('audit.private.json'))['fixture']
        if fixture and digest(json.loads(z.read('source.private.json')))!=digest(e.fixture_source()):
            raise ValueError('fixture_source_identity_conflict')
        root=immutable_root(Path(output),fixture=fixture)
        for name in checks: (root/name).write_bytes(z.read(name))
    finally: z.close()
    summary=validate(root)
    if (root/'mock-outcomes.private.json').exists():
        from . import results
        candidate=read_json(root/'candidate.private.json')
        actual=results.report(candidate,read_json(root/'mock-outcomes.private.json'))
        if actual!=read_json(root/'mock-summary.json'): raise ValueError('mock_report_reconstruction_conflict')
    return {'reconstructed':True,'status':summary['status'],'fixture':summary['fixture'],'generation_calls':0}
