"""Restricted mechanical source audit. No network except explicit acquire()."""
import csv
import io
import hashlib
from collections import Counter
from dataclasses import replace, asdict
from pathlib import Path
from ...studies import gpqa_data as native
from ...util import digest, file_hash, read_json, write_json
from ...datasets import content_group
from ..evaluation_source import sources as old

SOURCES_EVAL=('gpqa_main','logiqa')
SEED=20261016
NAMESPACE='pact-stage2-gpqa-logiqa-v2'
FILES=('gpqa_main.csv','gpqa_diamond.csv','README.md','license.txt')
MAX_BYTES=20*1024*1024


def private_path(path):
    path=Path(path)
    if any(p.is_symlink() for p in (path,*path.parents)): raise ValueError('private_path_symlink')
    return native.outside_git(path)


def acquire(directory, *, approved=False):
    """USER INVOKED only. HF's existing authentication; never inspect secret values."""
    if not approved: raise ValueError('explicit_source_access_required')
    directory=private_path(directory)
    if directory.exists(): raise ValueError('acquisition_destination_must_be_absent')
    # Bound official metadata before any payload fetch. No repository scripts.
    from huggingface_hub import HfApi, hf_hub_download
    info=HfApi().dataset_info(native.REPO,revision=native.REVISION,files_metadata=True)
    if info.sha!=native.REVISION: raise ValueError('official_revision_conflict')
    siblings={s.rfilename:s for s in info.siblings}
    if any(n not in siblings or siblings[n].size is None or not 0<siblings[n].size<=MAX_BYTES for n in FILES):
        raise ValueError('official_file_inventory_or_size_conflict')
    directory.mkdir(parents=True,mode=0o700)
    receipt={'repository':native.REPO,'revision':native.REVISION,'files':{},'mechanical_import_not_model_exposure':True}
    for name in FILES:
        p=Path(hf_hub_download(native.REPO,name,repo_type='dataset',revision=native.REVISION,local_dir=str(directory)))
        if p.resolve()!=directory/name or p.stat().st_size!=siblings[name].size: raise ValueError('download_identity_conflict')
        raw=p.read_bytes(); sha=file_hash(p); blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        entry=siblings[name];lfs=getattr(entry,'lfs',None)
        expected=(lfs.get('sha256') if isinstance(lfs,dict) else getattr(lfs,'sha256',None)) if lfs else None
        if (expected and sha!=expected) or (not expected and blob!=entry.blob_id): raise ValueError('upstream_content_identity_conflict')
        receipt['files'][name]={'sha256':sha,'bytes':len(raw),'git_blob':entry.blob_id,'upstream_sha256':expected}
    native.verified_source(directory)  # preserves original Diamond + terms pins
    write_json(directory/'source-receipt.json',receipt)
    return {'acquired_files':4,'revision':native.REVISION,'receipt_sha256':file_hash(directory/'source-receipt.json'),'model_calls':0}


def parse_csv(text):
    reader=csv.DictReader(io.StringIO(text))
    if not set((*native.FIELDS,'High-level domain'))<=set(reader.fieldnames or []):raise ValueError('source_schema_conflict')
    rows=[]
    for row in reader:
        if len(rows)>=1000 or any(len(v.encode('utf-8'))>MAX_BYTES for v in row.values() if isinstance(v,str)):
            raise ValueError('source_row_bounds')
        rows.append(row)
    return rows


def load(directory):
    if directory is None:return None,{'status':'source_bytes_unavailable','raw_rows':None}
    directory=private_path(directory)
    if not directory.is_dir():return None,{'status':'source_bytes_unavailable','raw_rows':None}
    if (directory/'source-receipt.json').is_file():receipt=read_json(directory/'source-receipt.json')
    else:
        # Reuse established native/HF acquisition receipt; no new acceptance ceremony.
        existing=read_json(directory/'source_access_receipts.json')
        receipt={'repository':existing['repository'],'revision':existing['revision'],
            'files':{n:{'sha256':existing['files'][n],'bytes':(directory/n).stat().st_size} for n in FILES}}
    if receipt['repository']!=native.REPO or receipt['revision']!=native.REVISION:raise ValueError('source_pin_conflict')
    native.verified_source(directory)
    for name in FILES:
        p=directory/name;entry=receipt['files'][name]
        if p.is_symlink() or p.stat().st_size>MAX_BYTES or p.stat().st_size!=entry['bytes'] or file_hash(p)!=entry['sha256']:
            raise ValueError('source_bytes_conflict')
    rows={}
    for name in FILES[:2]:
        rows[name]=parse_csv((directory/name).read_text(encoding='utf-8-sig'))
    if len(rows['gpqa_main.csv'])!=448 or len(rows['gpqa_diamond.csv'])!=198:raise ValueError('official_row_count_conflict')
    return rows,{'status':'bytes_verified','raw_rows':448,'revision':native.REVISION,'source_receipt_sha256':digest(receipt),
                 'raw_sha256':{n:receipt['files'][n]['sha256'] for n in FILES},'access':'official_pinned_bytes_and_terms_verified; account_acceptance_not_reasserted'}


def reconcile(main,diamond,history,raw_hash,*,reviewed=False):
    """All Diamond content is reserved; no protected release. Labels used only for conflicts."""
    pairs=[];reasons={};meta=[]
    for subset,rows in [('main',main),('diamond',diamond)]:
        for i,row in enumerate(rows):
            key=(subset,i)
            try:
                t,l,m=native._normalize_for_partition(row,raw_hash)
                # Keep original option ordering namespace/identity, even when family changes.
                t=replace(t,family='gpqa_main',split='prospective_development')
                why=[] if len({o.text for o in t.options})==4 else ['option_integrity']
                pairs.append((t,l));meta.append((key,m,row['Correct Answer'].strip(),subset))
                reasons[key]=why+(['diamond_protected'] if subset=='diamond' else [])
            except (ValueError,TypeError,KeyError):
                reasons[key]=['schema_integrity'];pairs.append(None);meta.append((key,None,None,subset))
    parent=list(range(len(pairs)))
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    def union(i,j):
        a,b=find(i),find(j);parent[max(a,b)]=min(a,b)
    for i,a in enumerate(pairs):
        if not a:continue
        wa=native.norm(a[0].question).split();sa=set(zip(wa,wa[1:],wa[2:]))
        for j in range(i):
            b=pairs[j]
            if not b:continue
            wb=native.norm(b[0].question).split();sb=set(zip(wb,wb[1:],wb[2:]))
            if a[0].source_id==b[0].source_id or wa==wb or (min(len(wa),len(wb))>=12 and len(sa&sb)/max(1,len(sa|sb))>=.9):union(i,j)
    # Historical full partition manifests, not merely exposed ID totals.
    historical=set();unresolved=[]
    for h in history:
        manifest=h['manifest']
        for field in ('selected_ids','protected_ids','excluded_ids'):
            historical.update(manifest[field])
        if set(manifest['group_by_id'])!=set(manifest['selected_ids'])|set(manifest['protected_ids'])|set(manifest['excluded_ids']):
            raise ValueError('historical_partition_incomplete')
    known={p[0].task_id for p in pairs if p}
    unresolved=sorted(historical-known)
    groups={}
    for i,p in enumerate(pairs):
        if p:groups.setdefault(find(i),[]).append(i)
    allowed=[];labels={};audit=[]
    for members in groups.values():
        rs=set();answer_sets={};qcontents=set()
        for i in members:
            t,l=pairs[i];key,m,gold,subset=meta[i];rs.update(reasons[key])
            qcontents.add(m['content_hash'])
            answer_sets.setdefault(m['content_hash'],set()).add(gold)
            if t.task_id in historical:rs.add('historical_partition')
        if any(len(v)>1 for v in answer_sets.values()):rs.add('conflicting_answer_keys')
        if len(qcontents)>1:rs.add('unresolved_revision_or_content_mapping')
        mainmembers=[i for i in members if meta[i][3]=='main']
        if len(mainmembers)>1:rs.add('duplicate_alias')
        if unresolved:rs.add('unresolved_historical_mapping')
        if not reviewed:rs.add('exposure_scope_unverified')
        for i in mainmembers:
            t,l=pairs[i];g=digest(sorted({meta[j][1]['question_group'] for j in members}))
            audit.append({'task_id':t.task_id,'group_id':g,'reasons':sorted(rs)})
            if not rs:
                allowed.append({'task':asdict(t),'family':'gpqa_main','group_id':g,'content_group':content_group(t),
                    'cross_dataset_fingerprint':digest(' '.join(t.question.split())),'split':'prospective_development'})
                labels[t.task_id]=l.answer_id
    invalid=sum(pairs[i] is None for i in range(len(main)))
    unknown=sum(bool(set(r['reasons'])&{'exposure_scope_unverified','unresolved_historical_mapping'}) for r in audit)
    return allowed,labels,{'raw_items':len(main),'permitted_unique_groups':len(allowed),'not_permitted_items':len(main)-len(allowed),
        'unknown_items':unknown,'invalid_schema_items':invalid,'reason_counts':dict(Counter(v for r in audit for v in r['reasons'])),
        'unresolved_mapping_count':len(unresolved),'selected_non_diamond':True,'records':audit}


def select(rows,labels):
    chosen=[]
    for f in SOURCES_EVAL:
        pool=sorted((r for r in rows if r['family']==f),key=lambda r:(digest([SEED,NAMESPACE,r['group_id']]),r['task']['task_id']))
        if len(pool)<64:raise ValueError('source_shortfall_or_unverified')
        for i,r in enumerate(pool[:64]):
            chosen.append({**r,'binding':list(('QLM','LMQ','MQL','QML','MLQ','LQM')[i%6]),'sender':i%3,
                           'style':('claimed_consensus','claimed_independence')[i%2]})
    if any(len({r[k] for r in chosen})!=128 for k in ('group_id','content_group','cross_dataset_fingerprint')):raise ValueError('cross_source_overlap')
    return {'records':chosen,'labels':{r['task']['task_id']:labels[r['task']['task_id']] for r in chosen},
            'status':'candidate_selected','selection_seed':SEED,'namespace':NAMESPACE,'cohort_approved':False}
