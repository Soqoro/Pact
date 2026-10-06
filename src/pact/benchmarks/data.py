"""Official-file loaders, outcome-free grouping and immutable development partitions."""
import ast
from collections import Counter, defaultdict
import csv
import dataclasses as dc
import gzip
import json
from pathlib import Path
import re
from .registry import REGISTRY, SEED, CATEGORIES, DOMAINS, LIVE_SOURCES, LIVE_RELEASE, live_registered
from .contracts import BenchmarkInput, CONTRACTS
from ..schemas import Option
from ..util import digest, file_hash, read_json, write_json

MBPP_URL='https://github.com/evalplus/mbppplus_release/releases/download/v0.2.0/MbppPlus.jsonl.gz'
MBPP_SHA='af43697e8791c4c149bdfd6b489d8b5412507551ac20e28a439f650b8225db63'

class ReadinessError(ValueError):pass

def literal_choices(value):
    if isinstance(value,str):
        if len(value)>65536:raise ReadinessError('CSV list exceeds bound')
        try:value=ast.literal_eval(value)
        except (ValueError,SyntaxError,RecursionError):raise ReadinessError('Invalid CSV list') from None
    if not isinstance(value,list) or not 2<=len(value)<=26 or any(not isinstance(x,str) or not x.strip() for x in value):
        raise ReadinessError('Invalid options')
    return value

def normalize(name,row,source_hash,*,domain=None,index=0):
    s=REGISTRY[name];choices=[];context='';extra={}
    if name=='mmlu-pro':
        sid=str(row['question_id']);question=row['question'];choices=literal_choices(row['options']);stratum=row['category']
        ai=row['answer_index']
        if type(ai) is not int or not 0<=ai<len(choices) or row['answer']!=chr(65+ai):raise ReadinessError('MMLU index/letter mismatch')
        if stratum not in CATEGORIES:raise ReadinessError('Unexpected MMLU category')
        gold={'answer':chr(65+ai)}
    elif name=='musr':
        choices=literal_choices(row['choices']);question=row['question'];context=row['narrative'];stratum=domain
        ai=int(row['answer_index'])
        if not 0<=ai<len(choices) or choices[ai]!=row['answer_choice']:raise ReadinessError('MuSR index/choice mismatch')
        if domain not in DOMAINS:raise ReadinessError('Unexpected MuSR domain')
        sid=digest([domain,index,question,context,choices]);gold={'answer':chr(65+ai)}
    elif name=='math-500':
        sid=str(row['unique_id']);question=row['problem'];stratum=str(row['subject'])+'|'+str(row['level']);gold={'answer':row['answer']}
    elif name=='mbpp-plus':
        sid=row['task_id'];question=row['prompt'];stratum='program'
        if not re.fullmatch(r'Mbpp/\d+',sid):raise ReadinessError('MBPP official ID mismatch')
        required={'canonical_solution','base_input','plus_input','entry_point','atol'}
        if not required<=row.keys() or not (isinstance(row['plus_input'],list) or row['plus_input']=={}):raise ReadinessError('Full expanded MBPP tests required')
        # The release prompt contains its official public example and entrypoint.
        gold={'problem':row,'answer':None};extra={'release':'v0.2.0','source_population':378}
    elif name=='livebench':
        if not live_registered(row):raise ReadinessError('Native scorer registration unavailable')
        if row.get('category') not in LIVE_SOURCES or row.get('task')=='agentic_coding' or len(row.get('turns',[]))!=1:
            raise ReadinessError('Unsupported native modality/category')
        sid=str(row['question_id']);question=row['turns'][0];stratum=row['category']+'|'+row.get('subtask',row['task'])
        gold={'problem':row,'answer':None};extra={'native_task':row.get('subtask',row['task'])}
    else:raise ReadinessError('GPQA requires parent-aware official loader')
    task=BenchmarkInput(name+':'+sid,s.kind,name,'characterization_dev',s.revision,source_hash,question,
                        tuple(Option(chr(65+i),x,chr(65+i)) for i,x in enumerate(choices)),context)
    # Case/Unicode preserved. Exact public-problem fingerprint can flag copied tasks across datasets.
    fingerprint=digest(' '.join((context or question).split()))
    return {'task':dc.asdict(task),'eval':gold,'stratum':stratum,'group_id':fingerprint,
            'cross_dataset_fingerprint':fingerprint,'metadata':extra}


def group_variants(rows):
    """Union exact/near-identical narratives independent of labels; never drop variants."""
    parent=list(range(len(rows)))
    def find(i):
        while parent[i]!=i:i=parent[i]
        return i
    def union(i,j):
        a,b=find(i),find(j);parent[max(a,b)]=min(a,b)
    exact={};shingles=[]
    for i,r in enumerate(rows):
        key=r['group_id']
        if key in exact:union(i,exact[key])
        exact[key]=i
        text=r['task']['context'] or r['task']['question'];w=text.split()
        shingles.append(set(zip(w,w[1:],w[2:])))
    # MuSR author variants may differ locally; quadratic only on its small domain pools.
    if rows and rows[0]['task']['family']=='musr':
        for i,a in enumerate(shingles):
            for j in range(i):
                b=shingles[j]
                if len(a)>10 and len(b)>10 and len(a&b)/max(1,len(a|b))>=.9:union(i,j)
    groups=defaultdict(list)
    for i in range(len(rows)):groups[find(i)].append(i)
    for members in groups.values():
        gid=digest(sorted({rows[i]['group_id'] for i in members}))
        for i in members:rows[i]['group_id']=gid
    return rows


def allocation(counts,total):
    if total>sum(counts.values()):raise ReadinessError('quota_shortfall')
    n=sum(counts.values());q={k:total*v//n for k,v in counts.items()}
    for k in sorted(q,key=lambda k:(-(total*counts[k]%n),k))[:total-sum(q.values())]:q[k]+=1
    return q


def partition(name,rows,*,n=None,known=None):
    if not rows:raise ReadinessError('Empty source')
    n=REGISTRY[name].n if n is None else n
    group_variants(rows);groups=defaultdict(list)
    for r in rows:groups[r['group_id']].append(r)
    known=known or {'exposed_groups':[],'exposed_fingerprints':[]}
    blocked=set(known.get('exposed_fingerprints',[]))|set(known.get('blocked_fingerprints',[]))
    excluded={g for g,rs in groups.items() if g in known.get('exposed_groups',[]) or any(r['cross_dataset_fingerprint'] in blocked for r in rs)}
    cross_stratum={g for g,rs in groups.items() if len({r['stratum'] for r in rs})!=1}
    excluded.update(cross_stratum)
    # Select one outcome-independent representative per group; retain every variant
    # in the source inventory and assign siblings to the same exposure partition.
    # MuSR object placements has four variants/group: splitting these would leak.
    available={g:[min(rs,key=lambda r:digest([SEED,name,'representative',r['task']['task_id']]))]
               for g,rs in groups.items() if g not in excluded}
    counts=Counter(r['stratum'] for rs in available.values() for r in rs)
    if name=='mmlu-pro' and set(counts)!=set(CATEGORIES):raise ReadinessError('MMLU category shortfall')
    if name=='musr' and set(counts)!=set(DOMAINS):raise ReadinessError('MuSR domain shortfall')
    if name in ('mmlu-pro','musr'):
        if n%len(counts):raise ReadinessError('Balanced quota cannot divide')
        quota={k:n//len(counts) for k in counts}
    elif name=='livebench':
        quota={}
        for category in LIVE_SOURCES:
            c={k:v for k,v in counts.items() if k.split('|')[0]==category}
            if not c:raise ReadinessError('LiveBench category unavailable')
            # Every scorer task represented when quota permits, then proportional remainder.
            q=n//5
            if len(c)>q:raise ReadinessError('More scorer tasks than category quota')
            extra=allocation({k:v-1 for k,v in c.items()},q-len(c)) if q>len(c) else {k:0 for k in c}
            quota.update({k:1+extra[k] for k in c})
    else:quota=allocation(counts,n)
    parts={};used=set()
    for part in ('characterization_dev','confirmation_locked'):
        ids=[]
        for stratum,q in sorted(quota.items()):
            candidates=sorted((g for g,rs in available.items() if rs[0]['stratum']==stratum and g not in used),key=lambda g:digest([SEED,name,part,stratum,g]))
            # Deterministic exact subset-sum over whole groups; never split/delete variants.
            ways={0:[]}
            for g in candidates:
                size=len(available[g])
                for x in sorted(list(ways),reverse=True):
                    if x+size<=q and x+size not in ways:ways[x+size]=ways[x]+[g]
                if q in ways:break
            if q not in ways:raise ReadinessError('quota_shortfall:'+stratum+':'+part)
            for g in ways[q]:used.add(g);ids.extend(r['task']['task_id'] for r in available[g])
        parts[part]=sorted(ids,key=lambda i:digest([SEED,name,part,'order',i]))
    parts['reserve_locked']=sorted(r['task']['task_id'] for g,rs in available.items() if g not in used for r in rs)
    manifest={'schema_version':1,'seed':SEED,'dataset':name,'training_allowed':False,'partitions':parts,
              'group_by_id':{r['task']['task_id']:r['group_id'] for r in rows},'quotas':quota,
              'source_rows':len(rows),'eligible_groups':len(available),'excluded_groups':sorted(excluded),
              'grouping':'exact whitespace public problem; MuSR word-trigram Jaccard >=0.9; no semantic guarantee',
              'prior_exposure':known,
              'cross_stratum_excluded_groups':sorted(cross_stratum),
              'representative_policy':'one SHA256-ranked source ID per group independent of labels; all siblings inherit its partition',
              'group_members':{g:[r['task']['task_id'] for r in rs] for g,rs in groups.items()},
              'variant_partition_by_id':{r['task']['task_id']:next((part for part,ids in parts.items() if any(x['task']['task_id'] in ids for x in rs)),'excluded_source_group') for rs in groups.values() for r in rs},
              'cross_dataset_fingerprints':{r['task']['task_id']:r['cross_dataset_fingerprint'] for r in rows}}
    byid={r['task']['task_id']:r for r in rows}
    if len(byid)!=len(rows):raise ReadinessError('Duplicate source ID')
    return [byid[k] for k in parts['characterization_dev']],manifest


def exposure_index(prepared):
    """Hash-only joint group flags; protect earlier locked pools as well as exposed IDs."""
    flags=defaultdict(list)
    for data in prepared:
        manifest=data['manifest']
        for tid,fingerprint in manifest['cross_dataset_fingerprints'].items():
            flags[fingerprint].append({'dataset':data['dataset'],'task_id':tid,
                'partition':manifest['variant_partition_by_id'][tid],
                'group_id':manifest['group_by_id'][tid]})
    return {'schema_version':1,'blocked_fingerprints':sorted(flags),
            'joint_groups':dict(flags),
            'cross_dataset_duplicates':sorted(k for k,v in flags.items() if len({x['dataset'] for x in v})>1),
            'policy':'Earlier characterization and locked pools unavailable to later selection; exact lexical matches only'}


def live_membership(row,release=LIVE_RELEASE):
    # Matches pinned official add-in-release-set and removal strictly-after predicate.
    releases={'2024-06-24','2024-07-26','2024-08-31','2024-11-25','2025-04-02','2025-04-25','2025-05-30','2025-11-25','2025-12-23','2026-01-08','2026-06-25'}
    added=str(row['livebench_release_date'])[:10];removed=str(row.get('livebench_removal_date') or '')[:10]
    return added in releases and added<=release and (not removed or removed>release)


def read_rows(path):
    if path.suffix=='.parquet':
        import pyarrow.parquet as pq
        return pq.read_table(path).to_pylist()
    if path.suffix=='.csv':
        with path.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
    if path.suffix=='.gz':
        with gzip.open(path,'rt') as f:return [json.loads(l) for l in f if l.strip()]
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def acquire(name,directory,*,download=False):
    from ..studies.gpqa_data import outside_git
    directory=outside_git(directory);directory.mkdir(parents=True,exist_ok=True);s=REGISTRY[name]
    if name=='gpqa':
        from ..studies.gpqa_data import acquire as gpqa_acquire
        gpqa_acquire(directory,download=download,token=__import__('os').environ.get('HF_TOKEN'))
        files=list(s.files)+['README.md','license.txt']
    elif name=='mbpp-plus':
        files=['MbppPlus.jsonl.gz','README.md']
        if download and not (directory/files[0]).exists():
            import urllib.request
            with urllib.request.urlopen(MBPP_URL,timeout=120) as response:(directory/files[0]).write_bytes(response.read(64*1024**2))
        if not (directory/files[0]).exists() or file_hash(directory/files[0])!=MBPP_SHA:raise ReadinessError('Official MBPP+ v0.2.0 checksum mismatch')
        if download:
            try:
                import shutil
                from huggingface_hub import hf_hub_download
                card=hf_hub_download(s.repository,'README.md',repo_type='dataset',revision=s.revision)
                shutil.copyfile(card,directory/'README.md')
            except Exception:raise ReadinessError('Official MBPP source notice unavailable') from None
        if not (directory/'README.md').is_file():raise ReadinessError('Official MBPP source notice missing')
    else:
        sources=[(s.repository,s.revision,f,f) for f in (*s.files,'README.md')]
        if name=='livebench':sources=[('livebench/'+c,r,f,c+'/'+f) for c,r in LIVE_SOURCES.items() for f in ('data/test-00000-of-00001.parquet','README.md')]
        files=[]
        for repo,revision,f,target in sources:
            path=directory/target;files.append(target)
            if download:
                try:
                    import os,shutil
                    from huggingface_hub import hf_hub_download
                    cached=hf_hub_download(repo,f,repo_type='dataset',revision=revision,token=os.environ.get('HF_TOKEN'))
                    path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(cached,path)
                except Exception:raise ReadinessError('official_source_access_failed:'+name) from None
            if not path.is_file():raise ReadinessError('official_source_files_missing:'+name)
            if name=='livebench' and path.suffix=='.parquet':
                inventory=read_rows(path)
                observed=sorted({str(r.get('livebench_release_date',''))[:10] for r in inventory})
                if LIVE_RELEASE not in observed:
                    write_json(directory/'readiness.json',{'status':'requested_release_unavailable',
                        'requested':LIVE_RELEASE,'checked_repository':repo,'revision':revision,
                        'source_sha256':file_hash(path),'observed_release_dates':observed,
                        'reason':'Pinned public category inventory does not establish requested release; no older fallback'})
                    raise ReadinessError('requested_release_unavailable')
        # Offline reuse requires original acquisition receipt, not self-attested revision.
        if not download:
            old=read_json(directory/'source_access_receipts.json')
            if old['revision']!=s.revision or old['files']!={f:file_hash(directory/f) for f in files}:raise ReadinessError('Source receipt mismatch')
    receipt={'repository':s.repository,'revision':s.revision,'files':{f:file_hash(directory/f) for f in files},
             'live_sources':LIVE_SOURCES if name=='livebench' else None,'license_notice_files':[f for f in files if f.endswith(('README.md','license.txt'))],
             'release':'v0.2.0' if name=='mbpp-plus' else LIVE_RELEASE if name=='livebench' else None}
    if name=='mbpp-plus':
        receipt['asset_url']=MBPP_URL
        receipt['data_authority']='Official v0.2.0 release asset and SHA256; hosted repository pin is notice/schema provenance only'
    write_json(directory/'source_access_receipts.json',receipt);return receipt


def prepare(name,directory,output,*,download=False,parent=None,known=None):
    from ..studies.gpqa_data import outside_git
    output=outside_git(output)
    if output.exists():raise ReadinessError('Prepared dataset exists; never overwrite selection')
    receipt=acquire(name,directory,download=download);s=REGISTRY[name];rows=[];parent_manifest=None
    if name=='gpqa':
        if parent is None:raise ReadinessError('GPQA parent partition required')
        pdata=read_json(parent);parent_manifest=pdata.get('manifest',pdata)
        rows=gpqa_child_rows(read_rows(directory/'gpqa_diamond.csv'),receipt['files']['gpqa_diamond.csv'],parent_manifest)
    elif name=='livebench':
        raw=[r for c in LIVE_SOURCES for r in read_rows(directory/c/'data/test-00000-of-00001.parquet')]
        # A newer leaderboard label or retained older questions is insufficient evidence.
        if not all(any(r.get('category')==c and str(r.get('livebench_release_date',''))[:10]==LIVE_RELEASE for r in raw) for c in LIVE_SOURCES):
            write_json(directory/'readiness.json',{'status':'requested_release_unavailable','requested':LIVE_RELEASE,'sources':receipt,
                'observed_release_dates':sorted({str(r.get('livebench_release_date',''))[:10] for r in raw})})
            raise ReadinessError('requested_release_unavailable')
        for row in raw:
            if not live_membership(row) or row.get('category') not in LIVE_SOURCES or row.get('task')=='agentic_coding' or len(row.get('turns',[]))!=1:continue
            rows.append(normalize(name,row,digest(receipt)))
    else:
        files=['MbppPlus.jsonl.gz'] if name=='mbpp-plus' else s.files
        for i,f in enumerate(files):
            raw=read_rows(directory/f)
            if name=='mbpp-plus' and len(raw)!=378:raise ReadinessError('MBPP+ population changed')
            if name=='math-500' and len(raw)!=500:raise ReadinessError('MATH population changed')
            rows.extend(normalize(name,r,receipt['files'][f],domain=DOMAINS[i] if name=='musr' else None,index=j) for j,r in enumerate(raw))
    selected,manifest=partition(name,rows,known=known)
    manifest['parent_partition']=parent_manifest
    data={'schema_version':1,'dataset':name,'receipt':receipt,'manifest':manifest,'selected':selected,
          'response_contract':CONTRACTS[s.kind],'scorer':s.scorer}
    write_json(output,data);return {'prepared':len(selected),'data_hash':digest(data),'partitions':{k:len(v) for k,v in manifest['partitions'].items()}}


def gpqa_child_rows(raw,source_hash,parent_manifest):
    from ..studies.gpqa_data import partition as gpqa_partition, _normalize_for_partition
    _,computed=gpqa_partition(raw,source_hash)
    if parent_manifest!=computed:raise ReadinessError('GPQA parent partition changed')
    if [len(computed[k]) for k in ('selected_ids','protected_ids','excluded_ids')]!=[32,164,2]:raise ReadinessError('GPQA parent accounting changed')
    rows=[]
    for row in raw:
        t,label,m=_normalize_for_partition(row,source_hash)
        if t.task_id not in computed['protected_ids']:continue
        task=BenchmarkInput(t.task_id,'mcq','gpqa','characterization_dev',REGISTRY['gpqa'].revision,t.source_hash,t.question,t.options)
        rows.append({'task':dc.asdict(task),'eval':{'answer':label.answer_id},'stratum':m['domain'],
                     'group_id':computed['group_by_id'][t.task_id],'cross_dataset_fingerprint':digest(' '.join(t.question.split())),'metadata':m})
    return rows
