"""CPU-only private audit; existing Stage I and previous proposed children immutable."""
from pathlib import Path
import json
import zipfile
import hashlib
from ...util import digest, read_json, write_json, file_hash, canonical
from ..allocation_v3 import evidence as e, design as d
from ..evaluation_source import review as previous, sources as old
from . import sources as s, graph as g, contracts


def history_files(inventory):
    """User-controlled reviewed manifest with exact bytes; no examples printed."""
    result=[]
    if not inventory:return result,False
    if inventory.get('scope')!='both_gpqa_cohorts_all_protections_and_revisions':return result,False
    entries=inventory.get('files',[])
    roles={x.get('role') for x in entries}
    if not {'original_diamond','breadth_diamond'}<=roles:return result,False
    for entry in entries:
        path=s.private_path(entry['path'])
        if file_hash(path)!=entry['sha256']:raise ValueError('historical_manifest_digest_conflict')
        value=read_json(path)
        if value['receipt']['repository']!=s.native.REPO or value['receipt']['revision']!=s.native.REVISION:
            raise ValueError('historical_revision_reconciliation_required')
        if entry['role']=='breadth_diamond':
            m=value['manifest'];parents=m['parent_partition']
            if len(m['partitions']['characterization_dev'])!=32 or not set(m['group_by_id'])<=set(parents['protected_ids']):
                raise ValueError('breadth_parent_partition_conflict')
            # All variants, locked/reserve and excluded siblings remain unavailable.
            ids=set(m['group_by_id']);selected=set(m['partitions']['characterization_dev'])
            protected=set(m['partitions']['confirmation_locked'])|set(m['partitions']['reserve_locked'])
            value={**value,'manifest':{'selected_ids':sorted(selected),'protected_ids':sorted(protected),
                'excluded_ids':sorted(ids-selected-protected),'group_by_id':m['group_by_id']}}
        result.append(value)
    return result,inventory.get('unresolved_mappings',1)==0


def audit(root,parent,parent_bundle=None,gpqa_dir=None,data_dir=None,exposure=None,inventory=None,history_roots=(),history=None):
    source,ln=previous.lineage(Path(parent),history_roots,parent_bundle)
    # Include this child's identities as well as inherited relevant histories.
    for history_root in history_roots:
        for path in Path(history_root).glob('**/attempts/*.json'):
            if read_json(path).get('identity',{}).get('owner') in (g.ASSAY,g.POLICY,g.CHILD):
                ln['local_history_conflicts'].append(str(path))
    blockers=[];exposure=exposure or {}
    ex=old.exposure_status(exposure,source)
    blockers.extend(ex['blockers'])
    ln['external_history_reconciled']=bool(history and e.reviewed_history(history) and not ln['local_history_conflicts'])
    if not ln['external_history_reconciled']:blockers.append('relevant_external_consumption_unresolved')
    rows,raw=s.load(gpqa_dir);historical,coverage=history_files(inventory)
    if not coverage:blockers.append('gpqa_historical_partitions_unverified')
    train,val,log=old.original_sources(data_dir)
    if rows is None:blockers.append('gpqa_main_bytes_unavailable')
    if train is None:blockers.append('original_train_validation_bytes_unavailable')
    candidate=None;elig=None
    if rows is not None and train is not None:
        gp,labels,ga=s.reconcile(rows['gpqa_main.csv'],rows['gpqa_diamond.csv'],historical,raw['raw_sha256']['gpqa_main.csv'],reviewed=coverage and ex['status']=='verified')
        # Original parser/grouping/historical exclusion machinery; unchanged train/probe membership.
        lr,ll,la=old.eligibility([],train,val,source,exposure,source_reviewed={'openbookqa':False,'logiqa':True})
        # Combined lexical audit propagates cross-source aliases, including historical training groups.
        from ...schemas import task_from_dict,TaskLabel
        from ...training.data import audit_training_overlap
        exclusions={k:set(exposure.get(k,[]))|set(source.get('exposure',{}).get(k,[])) for k in old.FIELDS}
        gp=[r for r in gp if not any(v in exclusions[k] for k,v in [('task_ids',r['task']['task_id']),('group_ids',r['group_id']),('content_groups',r['content_group']),('cross_dataset_fingerprints',r['cross_dataset_fingerprint'])])]
        pairs=[(task_from_dict(r['task']),TaskLabel(r['task']['task_id'],labels[r['task']['task_id']])) for r in gp]
        reps,combined=audit_training_overlap([*train,*pairs],val)
        rejected=set()
        for group in combined['groups']:
            members={m['task_id'] for m in group['members']}
            if members&set(labels) and any(x not in labels for x in members):rejected.update(members)
        rejected.update(x['task_id'] for x in combined['exclusions'])
        permitted=[r for r in [*gp,*lr] if r['task']['task_id'] not in rejected]
        elig={'gpqa_main':ga,'logiqa':la['counts']['logiqa'],'cross_source_denied':len(rejected&{r['task']['task_id'] for r in [*gp,*lr]}),
              'permitted_counts':{f:sum(r['family']==f for r in permitted) for f in s.SOURCES_EVAL}}
        if any(n<64 for n in elig['permitted_counts'].values()):blockers.append('source_shortfall_or_unverified')
        # Relevant budget uncertainty blocks execution, not independent candidate CPU work.
        source_blockers=[b for b in blockers if b!='relevant_external_consumption_unresolved']
        if not source_blockers:candidate=s.select(permitted,{**labels,**ll})
    return save(root,source,ln,{'fixture':False,'sources':{'gpqa_main':raw,'logiqa':log},'eligibility':elig,
        'blockers':sorted(set(blockers)),'status':'candidate_selected' if candidate else 'BLOCKED'},candidate)


def save(root,source,ln,audit,candidate=None):
    metadata_only=not candidate and audit['sources']['gpqa_main']['status']=='source_bytes_unavailable'
    root=previous.immutable_root(Path(root),fixture=audit['fixture']) if audit['fixture'] or metadata_only else s.private_path(root)
    if not audit['fixture'] and not metadata_only:
        if root.exists():raise ValueError('child_collision')
        root.mkdir(parents=True,mode=0o700)
    contract=contracts.training_contract(source,ln['S0'])
    graph=g.compile_graph(source,candidate,ln) if candidate else None
    method=g.proposed_method(ln,audit,candidate,graph)
    method['training_dependency_hash']=digest(contract)
    method['historical_budget_remaining']='unknown_until_reconciled'
    method['budget_reconciliation']=g.budget_reconciliation(source)
    values={'source.private.json':source,'lineage.private.json':ln,'audit.private.json':audit,
        'training.private.json':contract,'method.private.json':method}
    if candidate:values.update({'candidate.private.json':candidate,'graph.private.json':graph})
    for name,v in values.items():write_json(root/name,v)
    summary=sanitize(audit,method,graph)
    write_json(root/'summary.json',summary)
    write_json(root/'manifest.json',{n:file_hash(root/n) for n in values})
    return summary


def sanitize(audit,method,graph):
    elig=audit.get('eligibility')
    return {'version':g.VERSION,'status':audit['status'],'fixture':audit['fixture'],
        'blockers':audit['blockers'],'source_status':{f:v['status'] for f,v in audit['sources'].items()},
        'permitted_counts':elig.get('permitted_counts') if elig else None,
        'candidate_exists':method['candidate_digest'] is not None,'candidate_frozen':False,'execution_authorized':False,
        'training_dependency_hash':method['training_dependency_hash'],'budget_ceiling':d.BUDGET,
        'counts':graph['counts'] if graph else None,'budget_reconciliation':method['budget_reconciliation'],'remaining_budget':None,'historical_consumption':'unresolved',
        'this_task_real_generation_calls':0,'this_task_real_forwards':0,'pretraining_exposure':'unknown'}


def validate(root):
    root=Path(root);manifest=read_json(root/'manifest.json')
    for n,h in manifest.items():
        if Path(n).name!=n or file_hash(root/n)!=h:raise ValueError('review_manifest_conflict')
    source=read_json(root/'source.private.json');ln=read_json(root/'lineage.private.json');a=read_json(root/'audit.private.json')
    if not a['fixture'] and digest(source)!=e.EXECUTED_SOURCE_HASH:raise ValueError('executed_source_conflict')
    if read_json(root/'training.private.json')!=json.loads(canonical(contracts.training_contract(source,ln['S0']))):raise ValueError('scientific_dependency_conflict')
    candidate=read_json(root/'candidate.private.json') if (root/'candidate.private.json').exists() else None
    graph=g.compile_graph(source,candidate,ln) if candidate else None
    if graph and read_json(root/'graph.private.json')!=graph:raise ValueError('graph_conflict')
    m=g.proposed_method(ln,a,candidate,graph);m['training_dependency_hash']=digest(contracts.training_contract(source,ln['S0']));m['historical_budget_remaining']='unknown_until_reconciled';m['budget_reconciliation']=g.budget_reconciliation(source)
    if read_json(root/'method.private.json')!=json.loads(canonical(m)):raise ValueError('method_conflict')
    summary=sanitize(a,m,graph)
    if read_json(root/'summary.json')!=summary:raise ValueError('summary_conflict')
    return summary


def export(root):
    root=Path(root);summary=validate(root);dest=root/'bundles';dest.mkdir(exist_ok=True,mode=0o700)
    files={p.name:p.read_bytes() for p in root.glob('*.json') if p.name!='local-audit-receipt.json'}
    public={'summary.json':(canonical(summary)+'\n').encode()}
    if (root/'mock-outcomes.private.json').exists():
        from .results import report
        public['mock-summary.json']=(canonical(report(read_json(root/'candidate.private.json'),read_json(root/'mock-outcomes.private.json')))+'\n').encode()
    receipt={}
    for kind,values in [('PRIVATE',files),('SANITIZED',public)]:
        checks={n:hashlib.sha256(v).hexdigest() for n,v in values.items()};path=dest/f'{g.CHILD}-{kind}-{digest(checks)[:16]}.zip'
        if not path.exists():
            with zipfile.ZipFile(path,'x',zipfile.ZIP_DEFLATED) as z:
                for n,v in values.items():z.writestr(n,v)
                z.writestr('checksums.json',canonical(checks))
                z.writestr('HANDOFF.json',canonical({'version':g.VERSION,'kind':kind,'execution_enabled':False}))
        with zipfile.ZipFile(path) as z:
            if set(z.namelist())!=set(checks)|{'checksums.json','HANDOFF.json'} or any(hashlib.sha256(z.read(n)).hexdigest()!=h for n,h in checks.items()):raise ValueError('export_conflict')
        receipt[kind]={'sha256':file_hash(path),'bytes':path.stat().st_size,'filename':path.name}
    write_json(root/'local-audit-receipt.json',{'version':g.VERSION,'bundles':receipt,'validated':True,'raw_examples_return_allowed':False,'generation_calls':0})
    return receipt


def reconstruct(bundle,sha,root):
    from ..stage1.evidence import archive
    z,checks=archive(Path(bundle),sha)
    try:
        a=json.loads(z.read('audit.private.json'))
        root=previous.immutable_root(Path(root),fixture=True) if a['fixture'] else s.private_path(root)
        if not a['fixture']:root.mkdir(parents=True,exist_ok=False,mode=0o700)
        allowed={'source.private.json','lineage.private.json','audit.private.json','training.private.json','method.private.json','candidate.private.json','graph.private.json','summary.json','manifest.json','mock-outcomes.private.json','local-audit-receipt.json','audit-input.json','mock-assay.private.json'}
        if not set(checks)<=allowed:raise ValueError('unexpected_review_member')
        for n in checks:(root/n).write_bytes(z.read(n))
    finally:z.close()
    return validate(root)
