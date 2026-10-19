"""Exact-bank replacement training. No collection, scratch rerun or evaluation."""
from pathlib import Path
import argparse
import json
import shutil
import tempfile
import time
import zipfile

from ..artifacts import run_lock, safe_relative
from ..environment import code_identity, runtime_fingerprint
from ..util import canonical, digest, file_hash, read_json, write_json
from . import contracts as c, runtime, study, neural
from .replacement_review import proposal
from .retention import POLICY

VERSION = 'revival_replacement_training_v1'
RUN = 'pact-heterogeneous-receiver-training-replacement-002'
REVIEW_SHA = 'a67a7000801c4c96d19cd3b6d8521ee9d5fa9f5b2305c101eded1e11b4a066a3'
BUDGET = {'main_updates': 768, 'training_forwards': 18432, 'generation_calls': 0,
          'scratch_updates': 0, 'evaluation_calls': 0}


def source_identity():
    return code_identity(Path(__file__).resolve().parents[3])


def import_parent(bundle, root, review_sha):
    """Copy immutable parent evidence; never carry over trained optimizer state."""
    if review_sha != REVIEW_SHA:raise ValueError('Exact approved replacement review SHA required')
    if root.exists():raise ValueError('Absent child destination required; never re-import or re-plan')
    review = proposal(bundle)
    if digest_bytes(canonical(review)+'\n') != REVIEW_SHA:raise ValueError('Review proposal changed')
    from ..studies.forensics import private_root
    from .data import validate_source
    root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root.parent, prefix='.replacement-import-') as tmp:
        parent = Path(tmp)/'parent'
        parent.mkdir()
        # proposal has verified archive names, bounds, SHA and every member.
        with zipfile.ZipFile(bundle) as z:
            for name in json.loads(z.read('checksums.json')):
                target = parent/safe_relative(name)
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(name) as src, target.open('wb') as dst:shutil.copyfileobj(src,dst)
        parent_plan = read_json(parent/'plan.json')
        validate_source(parent_plan['source'])
        journal = runtime.Journal(parent)
        if len(journal.results) != review['historical_accounting']['confirmed_generation_calls']:
            raise ValueError('Parent generation accounting differs')
        rebuild_check=compare_bank(read_json(parent/'training_bank.json'), study.fit_bank(parent,parent_plan,inspect_only=True))
        if (parent/'training').exists():raise ValueError('Expected pre-main-training scratch milestone')
        child = Path(tmp)/'child'
        private_root(child, parent_plan['source']['fixture'])
        copies = {'plan.json':'parent_plan.json', 'training_bank.json':'training_bank.json',
                  'access.json':'access.json', 'sanity_complete.json':'sanity_complete.json'}
        for f in c.FAMILIES:
            copies[f'sanity/{f}/contract.json'] = f'parent_contracts/{f}.json'
            copies[f'sanity/{f}/receipt.json'] = f'parent_receipts/{f}.json'
        for src, name in copies.items():
            dst=child/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(parent/src,dst)
        shutil.copyfile(bundle, child/'parent-private.zip')
        bindings={name:file_hash(child/name) for name in [*copies.values(),'parent-private.zip']}
        p={'version':VERSION,'run_id':RUN,'source':parent_plan['source'],
           'source_code':source_identity(), 'review_sha256':REVIEW_SHA,
           'parent_plan_hash':digest(parent_plan),'imported_files':bindings,
           'budget':BUDGET,'storage_retention':POLICY,
           'historical_accounting':review['historical_accounting']}
        if not p['source']['fixture'] and (p['source_code']['dirty'] or not p['source_code']['git_commit']):
            raise ValueError('Clean pinned checkout required before real child import')
        write_json(child/'import_audit.json',rebuild_check)
        write_json(child/'plan.json',p)
        validate(child)
        child.rename(root)
    return {'run_id':RUN,'plan_hash':digest(p),'inherited_calls':len(journal.results),
            'new_model_calls':0,'new_updates':0}


def compare_bank(saved, rebuilt):
    """Verify semantics; never replace the SHA-bound original floating coefficients.

    Python versions use different summation algorithms. Only reconstructed weight
    and support-mass roundoff is tolerated in this supplementary offline check.
    Actual training always reads the exact original bytes whose SHA is pinned.
    """
    import math
    differences=[]
    def compare(a,b,path=()):
        if isinstance(a,dict) and isinstance(b,dict):
            if a.keys()!=b.keys():raise ValueError('Bank fields differ')
            for k in a:compare(a[k],b[k],path+(k,))
        elif isinstance(a,list) and isinstance(b,list):
            if len(a)!=len(b):raise ValueError('Bank lengths differ')
            for i,(v,w) in enumerate(zip(a,b)):compare(v,w,path+(i,))
        elif a!=b:
            numeric_weight=(len(path)==4 and path[0]=='bank' and path[-1]=='weight')
            numeric_mass=(len(path)==5 and path[0]=='support' and path[3]=='mass')
            if not ((numeric_weight or numeric_mass) and type(a) is float and type(b) is float
                    and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-15)):
                raise ValueError('Bank reconstruction changed inputs/labels/weights')
            differences.append(abs(a-b))
    compare(saved,rebuilt)
    return {'original_bank_bytes_preserved':True,'reconstruction_roundoff_fields':len(differences),
            'maximum_reconstruction_roundoff':max(differences,default=0.0)}


def digest_bytes(text):
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()


def validate(root, plan_hash=None, *, check_source=False):
    p=read_json(root/'plan.json')
    if p['version']!=VERSION or p['run_id']!=RUN or p['review_sha256']!=REVIEW_SHA or p['budget']!=BUDGET or p['storage_retention']!=POLICY:
        raise ValueError('Replacement contract mismatch')
    if plan_hash is not None and digest(p)!=plan_hash:raise ValueError('Replacement plan hash mismatch')
    if check_source and p['source_code']!=source_identity():raise ValueError('Child source changed; no implicit migration')
    for name, sha in p['imported_files'].items():
        path=root/safe_relative(name)
        if path.is_symlink() or file_hash(path)!=sha:raise ValueError('Imported parent evidence changed')
    parent=read_json(root/'parent_plan.json')
    if digest(parent)!=p['parent_plan_hash'] or parent['source']!=p['source']:
        raise ValueError('Parent source/plan changed')
    if read_json(root/'training_bank.json')['plan_hash']!=p['parent_plan_hash']:
        raise ValueError('Bank must retain original parent identity')
    if any(any(path.is_file() for path in (root/d).rglob('*')) for d in ('calls','intents','score_intents','probe_scores','evaluations')):
        raise ValueError('Replacement admits no new generation, scoring or evaluation')
    for f in c.FAMILIES:
        contract=read_json(root/f'parent_contracts/{f}.json')
        receipt=read_json(root/f'parent_receipts/{f}.json')
        if not (contract['initial']==receipt['initial']==receipt['restored']):
            raise ValueError('Parent initialization was not restored')
        if contract['identity']['family']!=f or contract['identity']['plan']!=p['parent_plan_hash']:
            raise ValueError('Parent family/plan identity changed')
        if contract['lora']!=c.LORA or contract['optimizer']!=c.OPT:
            raise ValueError('Parent training precision/objective contract changed')
    return p


def capacity(root):
    """Conservative structural bound, not a claim about account quota/throughput."""
    from .persistence import MAX_OBJECT_BYTES
    sizes={}
    for f in c.FAMILIES:
        native=read_json(root/f'parent_contracts/{f}.json')['identity']['native']
        shapes=native['native_projection_shapes']
        sizes[f]=sum(c.LORA['r']*(out+inp)*4 for out,inp in shapes.values())
    # Two arms/family: initial adapters + both epoch adapter/Adam checkpoints.
    # Six additional full checkpoints cover current/previous/incoming headroom.
    # 1 GiB metadata reserve and 25% margin also cover RNG/serialization overhead.
    bound=(14*sum(sizes.values())+18*max(sizes.values())+1024**3)*5//4
    if bound>MAX_OBJECT_BYTES:raise ValueError('Protected tensors/staging exceed object capacity; stop')
    return {'adapter_bytes':sizes,'projected_peak_object_bytes':bound,
            'max_object_bytes':MAX_OBJECT_BYTES,'drive_account_free_space_verified':False}


def preflight(root, cache, *, factory=None):
    """Verify actual pristine models and initial adapters; no generation/forward."""
    p=validate(root,check_source=True)
    if factory is not None and not p['source']['fixture']:raise ValueError('No mock real child')
    out=capacity(root);out['families']={}
    access=read_json(root/'access.json')
    if any(access[f]['runtime_fingerprint']!=runtime_fingerprint() for f in c.FAMILIES):
        raise ValueError('Native runtime differs from parent; no automatic runtime migration')
    for f in c.FAMILIES:
        backend=factory(f) if factory else runtime.Backend(f,access[f],cache)
        try:
            neural.attach(backend.model,c.SEED+c.FAMILIES.index(f))
            verify_initial(root,f,backend)
            out['families'][f]={'native_snapshot':backend.identity['snapshot'],
                'initial_hash':neural._weights_hash(neural.parameters(backend.model))}
        finally:backend.close()
    out.update(plan_hash=digest(read_json(root/'plan.json')), runtime_fingerprint=runtime_fingerprint(),
               model_calls=0,training_forwards=0,optimizer_updates=0)
    write_json(root/'replacement_preflight.json',out)
    return out


def verify_initial(root, family, backend):
    contract=read_json(root/f'parent_contracts/{family}.json')
    if backend.identity!=contract['identity']['native']:
        raise ValueError('Native model identity differs from original scratch actor')
    if neural._weights_hash(neural.parameters(backend.model))!=contract['initial']:
        raise ValueError('Seeded initialization differs from original; no training')


def train(root, plan_hash, cache, arm, family, *, resume=False, stop_after=None, persistent=None, factory=None):
    p=validate(root,plan_hash,check_source=True)
    if factory is not None and not p['source']['fixture']:raise ValueError('No mock real child')
    if arm not in c.ARMS[1:] or family not in c.FAMILIES:raise ValueError('Declared training arm/family required')
    if stop_after is not None and not 1<=stop_after<=128:raise ValueError('Stop boundary outside reviewed fit')
    receipt=read_json(root/'replacement_preflight.json')
    if receipt['plan_hash']!=digest(p) or receipt['runtime_fingerprint']!=runtime_fingerprint():
        raise ValueError('Exact child preflight/runtime required')
    if not runtime.recovery_safe(root):raise ValueError('Unresolved execution; no retry')
    report(root)
    return study.train_agent(root,p,cache,arm,family,resume=resume,persistent=persistent,factory=factory,
        initial_check=lambda backend:verify_initial(root,family,backend),stop_after=stop_after)


def report(root):
    p=validate(root)
    from ..training.checkpoints import read_checkpoint
    statuses={};pending_updates=[]
    for arm in c.ARMS[1:]:
        for f in c.FAMILIES:
            folder=study.trained(root,arm,f)
            if (folder/'update_attempt.json').exists():
                attempted=read_json(folder/'update_attempt.json')['step']
                committed=read_json(folder/'status.json')['completed_steps'] if (folder/'status.json').exists() else 0
                if attempted>committed:pending_updates.append({'arm':arm,'family':f,'step':attempted})
            if not (folder/'status.json').exists():continue
            status=read_json(folder/'status.json')
            latest=sorted((folder/'checkpoints').glob('step-*'))[-1]
            meta=read_checkpoint(latest,read_json(folder/'contract.json'))
            if meta['step']!=status['completed_steps'] or not 0<=meta['step']<=128:
                raise ValueError('Training status/checkpoint mismatch')
            statuses[f'{arm}/{f}']={k:status[k] for k in ('complete','completed_steps','planned_steps','forwards','adapter_hash')}
    updates=sum(s['completed_steps'] for s in statuses.values())
    forwards=sum(s['forwards'] for s in statuses.values())
    if updates>BUDGET['main_updates'] or forwards>BUDGET['training_forwards']:raise ValueError('Replacement budget exceeded')
    out={'run_id':RUN,'plan_hash':digest(p),'scientific_status':'mock_only' if p['source']['fixture'] else 'replacement_training_only_no_evaluation',
         'parent_history':p['historical_accounting'],'new_work':{'committed_updates':updates,
         'training_forwards':forwards,'forward_accounting':'committed updates only; partial-attempt forwards unknown',
         'unresolved_optimizer_attempts':pending_updates,'generation_calls':0},'budget':BUDGET,'training':statuses,
         'recovery_safe':runtime.recovery_safe(root),
         'training_complete':len(statuses)==6 and all(s['complete'] for s in statuses.values()),
         'full_pact_executed':False,'efficacy_established':False}
    write_json(root/'summary.json',out)
    return out


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['import-parent','inspect','preflight','repair-tokenizer-cache','train-agent','report','export','restore'])
    parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--persistent',type=Path)
    parser.add_argument('--parent-private',type=Path)
    parser.add_argument('--review-sha256')
    parser.add_argument('--plan-hash')
    parser.add_argument('--cache-dir',type=Path,default=Path('/content/pact-replacement/cache'))
    parser.add_argument('--execute',action='store_true')
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--stop-after',type=int)
    parser.add_argument('--arm',choices=c.ARMS[1:]);parser.add_argument('--family',choices=c.FAMILIES)
    a=parser.parse_args(argv);root=a.run_dir
    if root.name!=RUN or (a.persistent is not None and a.persistent.name!=RUN):
        raise ValueError('Separate replacement run ID/root required')
    if a.stage=='import-parent':
        if a.persistent is not None and a.persistent.exists() and any(a.persistent.iterdir()):
            raise ValueError('Existing persistent history: restore latest, never re-import')
        if a.parent_private is None:raise ValueError('Exact parent PRIVATE bundle required')
        out=import_parent(a.parent_private,root,a.review_sha256)
        runtime.checkpoint(root,a.persistent)
    elif a.stage=='restore':
        if a.persistent is None:raise ValueError('Latest child store required')
        runtime.restore_latest(a.persistent,root);validate(root)
        out={'restored':True,'plan_hash':digest(read_json(root/'plan.json'))}
    else:
        with run_lock(root):
            p=validate(root)
            if a.persistent is not None and (a.persistent/'SNAPSHOT_PENDING.json').exists():
                raise ValueError('Pending persistence; no automatic retry')
            if a.stage=='inspect':out={'plan_hash':digest(p),'budget':BUDGET,'capacity':capacity(root)}
            elif a.stage in ('preflight','repair-tokenizer-cache','train-agent'):
                if not a.execute or a.plan_hash is None:raise ValueError('--execute and exact --plan-hash required')
                validate(root,a.plan_hash,check_source=True)
                if a.stage=='repair-tokenizer-cache':
                    from .mistral_cache import repair
                    out=repair(a.cache_dir)
                elif a.stage=='preflight':out=preflight(root,a.cache_dir)
                else:out=train(root,a.plan_hash,a.cache_dir,a.arm,a.family,resume=a.resume,
                               stop_after=a.stop_after,persistent=a.persistent)
                runtime.checkpoint(root,a.persistent)
            elif a.stage=='report':out=report(root)
            else:
                from ..storage import persist_bundle
                report(root);runtime.checkpoint(root,a.persistent)
                out={};stamp=time.time_ns()
                for name,weights,sanitized in [('PRIVATE',False,False),('SANITIZED',False,True),('RECOVERY',True,False)]:
                    path=root.parent/'bundles'/f'{RUN}-{name}-{stamp}.zip'
                    out[name]=runtime.package(root,path,weights=weights,sanitized=sanitized)
                    if a.persistent:
                        dest=a.persistent/'bundles'/path.name
                        persist_bundle(path,dest,out[name]['sha256'],timeout_seconds=600)
                        out[name]['persistent_path']=str(dest)
    print(canonical(out))

if __name__=='__main__':main()
