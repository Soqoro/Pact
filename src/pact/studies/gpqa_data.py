"""Official gated GPQA Diamond CSV, private normalization and exposure partition."""
import csv
import dataclasses as dc
import hashlib
import io
from pathlib import Path
import re
import unicodedata
from collections import Counter

from ..schemas import TaskInput, TaskLabel, Option
from ..util import canonical, digest, file_hash, read_json, write_json

REPO = 'Idavidrein/gpqa'
REVISION = '83022cefff930aea54f654c0b282e74b9eeda5c6'
FILES = {'gpqa_diamond.csv': ('7589e3e467d69a1dceb126a60c4108d6d4f1d166',1373492),
         'README.md': ('82eb4c242a2ac936d3866e4158b60e1b8ff6664d',3141),
         'license.txt': ('0f174b0a4d6f57d6661929df667516c7c77cc4fa',241)}
SEED = 20260924
DOMAINS = ('Biology','Chemistry','Physics')
FIELDS = ('Question','Correct Answer','Incorrect Answer 1','Incorrect Answer 2','Incorrect Answer 3')
ACCESS = ('dataset_access_required: sign in at https://huggingface.co/datasets/Idavidrein/gpqa, '
          'personally accept its access conditions, then provide HF_TOKEN through a runtime secret; '
          'or supply an authorized official directory containing the pinned CSV, README.md and license.txt. '
          'No mirror or remote dataset script is supported.')


def outside_git(path):
    path=Path(path).resolve()
    if any((p/'.git').exists() for p in (path,*path.parents)):
        raise ValueError('Private GPQA data must be stored outside every Git checkout')
    return path


def verified_source(directory):
    """Git blob identities resolved from the official public tree; SHA256 also logged."""
    directory=outside_git(directory); hashes={}
    for name,(oid,size) in FILES.items():
        p=directory/name
        if not p.is_file() or p.is_symlink():raise RuntimeError(ACCESS)
        raw=p.read_bytes()
        if len(raw)!=size or hashlib.sha1(b'blob '+str(size).encode()+b'\0'+raw).hexdigest()!=oid:
            raise ValueError('Official GPQA source content/revision mismatch')
        hashes[name]=file_hash(p)
    return hashes


def acquire(directory, *, download=False, token=None):
    directory=outside_git(directory)
    if not download:
        verified_source(directory);return directory
    directory.mkdir(parents=True,exist_ok=True)
    try:
        from huggingface_hub import hf_hub_download
        for name in FILES:
            # Direct pinned data files only, no datasets scripts or remote code.
            path=hf_hub_download(REPO,name,repo_type='dataset',revision=REVISION,token=token,
                                  local_dir=str(directory))
            if Path(path).resolve()!=directory/name:raise ValueError('Unexpected official download path')
    except Exception:
        raise RuntimeError(ACCESS) from None
    verified_source(directory)
    return directory


def norm(text):
    return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())


def _normalize_for_partition(row, source_hash):
    if any(not isinstance(row.get(k),str) or not row[k].strip() for k in (*FIELDS,'High-level domain')):
        raise ValueError('GPQA schema: final question/answers/domain missing or empty')
    domain=row['High-level domain'].strip()
    if domain not in DOMAINS:raise ValueError('GPQA schema: unexpected high-level domain')
    question=row['Question'].strip();answers=[row[k].strip() for k in FIELDS[1:]]
    content=digest([question,sorted(answers)])
    # Record ID when present, content-derived fallback. No subset-index identity.
    record=row.get('Record ID','').strip()
    identity=digest(['official-record',record]) if record else content
    task_id='gpqa_diamond:'+identity
    order=sorted(range(4),key=lambda i:digest([SEED,'gpqa-options-v1',task_id,answers[i]]))
    options=tuple(Option(chr(65+j),answers[i],chr(65+j)) for j,i in enumerate(order))
    task=TaskInput(task_id,'gpqa_diamond','development_diagnostic',identity,REVISION,source_hash,question,options)
    label=TaskLabel(task_id,chr(65+order.index(0)))
    private={'domain':domain,'content_hash':content,'question_group':digest(norm(question)),
             'source_to_canonical':{FIELDS[i+1]:chr(65+order.index(i)) for i in range(4)},
             'usage':'development_diagnostic','training_allowed':False,'eligible_for_untouched_final':False}
    return task,label,private


def normalize(row, source_hash):
    task,label,private=_normalize_for_partition(row,source_hash)
    if len({o.text for o in task.options})!=4:
        raise ValueError('GPQA options must be four distinguishable strings')
    return task,label,private


def partition(rows, source_hash, *, known=None):
    if len(rows)!=198:raise ValueError('GPQA Diamond must contain exactly 198 official rows; stop preflight')
    normalized=[_normalize_for_partition(r,source_hash) for r in rows]
    byid={t.task_id:(t,l,m) for t,l,m in normalized}
    if len(byid)!=198:raise ValueError('Duplicate stable GPQA IDs; explicit source review required')
    known=known or {'exposed_content_hashes':[],'exposed_group_hashes':[],'groups':[]}
    parent={k:k for k in byid}
    def find(k):
        while parent[k]!=k:k=parent[k]
        return k
    def union(a,b):
        a,b=find(a),find(b);parent[max(a,b)]=min(a,b)
    ids=sorted(byid)
    # Outcome-free exact question and lexical near-duplicate screening.
    words={k:norm(byid[k][0].question).split() for k in ids}
    shingles={k:set(zip(w,w[1:],w[2:])) for k,w in words.items()}
    for j,a in enumerate(ids):
        for b in ids[j+1:]:
            if words[a]==words[b] or (min(len(words[a]),len(words[b]))>=12 and
                len(shingles[a]&shingles[b])/max(1,len(shingles[a]|shingles[b]))>=.9):union(a,b)
    for group in known.get('groups',[]):
        if any(k not in byid for k in group):raise ValueError('Known GPQA group has unknown IDs')
        for k in group[1:]:union(group[0],k)
    groups={}
    for k in ids:groups.setdefault(find(k),[]).append(k)
    group_hash={k:digest(sorted(byid[x][2]['question_group'] for x in members)) for k,members in groups.items()}
    malformed={k for k,(t,_,_) in byid.items() if len({o.text for o in t.options})!=4}
    excluded=set();reasons={}
    for k,members in groups.items():
        if malformed.intersection(members):
            excluded.update(members)
            for x in members:
                reasons[x]=['duplicate_option_text' if x in malformed else 'duplicate_option_group']
        if (group_hash[k] in known.get('exposed_group_hashes',[]) or
            any(byid[x][2]['content_hash'] in known.get('exposed_content_hashes',[]) for x in members)):
            excluded.update(members)
            for x in members:reasons.setdefault(x,[]).append('known_exposure')
        if len({byid[x][2]['domain'] for x in members})!=1:raise ValueError('Duplicate group crosses domains; review required')
    reps=[k for k in sorted(groups) if k not in excluded]
    counts=Counter(byid[k][2]['domain'] for k in reps)
    if set(counts)!=set(DOMAINS) or len(reps)<32:raise ValueError('Insufficient domain groups for fixed study')
    quota={d:32*counts[d]//len(reps) for d in DOMAINS}
    for d in sorted(DOMAINS,key=lambda d:(-(32*counts[d]%len(reps)),d))[:32-sum(quota.values())]:quota[d]+=1
    selected=[]
    for d in DOMAINS:
        candidates=sorted((k for k in reps if byid[k][2]['domain']==d),key=lambda k:digest([SEED,'gpqa-select-v1',group_hash[k]]))
        selected.extend(candidates[:quota[d]])
    selected=sorted(selected,key=lambda k:digest([SEED,'gpqa-order-v1',k]))
    exposed_groups={find(k) for k in selected}
    remainder=[k for k in ids if k not in excluded and find(k) not in exposed_groups]
    siblings={k for k in ids if find(k) in exposed_groups and k not in selected}
    excluded.update(siblings)
    for k in siblings:reasons.setdefault(k,[]).append('selected_group_sibling')
    manifest={'schema_version':2,'usage':'development_diagnostic','training_allowed':False,
        'eligible_for_untouched_final':False,'seed':SEED,'official_count':198,'selected_ids':selected,
        'protected_ids':remainder,'excluded_ids':sorted(excluded),
        'eligibility_policy':'gpqa-option-integrity-v2; exact stripped strings; exclude malformed groups before allocation',
        'option_identity':'case-sensitive, Unicode-preserving, outer whitespace stripped only',
        'source_integrity_excluded_ids':sorted(malformed),
        'exclusion_reasons':{k:sorted(v) for k,v in sorted(reasons.items())},
        'eligible_group_count':len(reps),
        'group_by_id':{k:group_hash[find(k)] for k in ids},
        'domain_counts':dict(sorted(counts.items())),'selected_domain_counts':quota,
        'algorithm':'largest remainder on eligible unique groups; alphabetic domain ties; SHA256 seeded group ranking',
        'duplicate_screen':'NFKC/casefold whitespace question equality or word-trigram Jaccard >=0.9 (>=12 words); known groups union',
        'semantic_paraphrase_audit':'not_run; lexical screening cannot exclude all paraphrases',
        'metadata_access':'all198 final questions/options/domain read for identity and grouping; only selected32 retained as task text; no protected generation',
        'prior_exposure_screen':known}
    return [byid[k] for k in selected],manifest


def prepare(directory, output, *, known=None):
    output=outside_git(output)
    hashes=verified_source(directory)
    with (Path(directory)/'gpqa_diamond.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not set((*FIELDS,'High-level domain'))<=set(reader.fieldnames or []):raise ValueError('Official GPQA header mismatch; access/schema review required')
        rows=list(reader)
    selected,manifest=partition(rows,hashes['gpqa_diamond.csv'],known=known)
    receipt={'schema_version':1,'repository':REPO,'revision':REVISION,'subset':'gpqa_diamond',
        'upstream_split':'train (storage label only)','source_sha256':hashes,'source_git_blobs':FILES,
        'header':reader.fieldnames,'notices':{n:(Path(directory)/n).read_text() for n in ('README.md','license.txt')},
        'canary_fields':sorted({k for row in rows for k in row if 'canary' in k.lower()}),
        'canary_values':sorted({v for row in rows for k,v in row.items() if 'canary' in k.lower() and v}),
        'redistribution':'private only; no plaintext/image examples online'}
    data={'schema_version':1,'manifest':manifest,'receipt':receipt,
          'selected':[{'task':dc.asdict(t),'label':dc.asdict(l),'private_metadata':m} for t,l,m in selected]}
    if output.exists() and canonical(read_json(output))!=canonical(data):raise ValueError('Prepared GPQA selection changed; no overwrite')
    write_json(output,data)
    return {'prepared_items':32,'protected_items':len(manifest['protected_ids']),
            'source_integrity_excluded_items':len(manifest['source_integrity_excluded_ids']),
            'excluded_items':len(manifest['excluded_ids']),'eligibility_policy':manifest['eligibility_policy'],'selected_domain_counts':manifest['selected_domain_counts'],
            'sha256':file_hash(output),'dataset_revision':REVISION}


def require_development(task):
    if task.family!='gpqa_diamond' or task.split!='development_diagnostic':raise ValueError('GPQA supports development diagnosis only; training/final export forbidden')
