"""CPU-only proposal for one exact export checksum repair. Never changes a plan."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from pact.environment import code_identity
from pact.util import digest, file_hash, read_json, write_json, canonical

OLD_COMMIT = '995e814e0883414b1ed56c590faad2e240cdf9b1'
PLAN_HASH = '5ff472604f74ed80cdbdecb574dc83c9306e6a912f0159249b1861a689fdd025'
STORAGE = 'src/pact/revival/allocation_v3/storage.py'
BEFORE = b"persist_bundle(path, destination/'bundles'/path.name, timeout_seconds=600)"
AFTER = b"persist_bundle(path, destination/'bundles'/path.name, out[kind]['sha256'], timeout_seconds=600)"


def git(root, *args):
    return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.PIPE)


def included(name):
    parts=Path(name).parts
    return ((parts[0] in ('src','configs','experiments') and
             '__pycache__' not in parts and not any(p.endswith('.egg-info') for p in parts))
            or name=='pyproject.toml')


def compare(old, new):
    """Byte-for-byte allowlist, including additions/deletions; no semantic guesses."""
    if set(old)!=set(new):raise ValueError('source_inventory_changed')
    changed=sorted(n for n in old if old[n]!=new[n])
    if changed!=[STORAGE]:raise ValueError('only_storage_checksum_repair_permitted')
    if old[STORAGE].count(BEFORE)!=1 or old[STORAGE].replace(BEFORE,AFTER)!=new[STORAGE]:
        raise ValueError('checksum_patch_not_exact')
    hashes=lambda values:{n:__import__('hashlib').sha256(v).hexdigest() for n,v in values.items()}
    a,b=hashes(old),hashes(new)
    return {'changed_source_files':changed,'old_source_hash':digest(a),'new_source_hash':digest(b),
            'old_storage_sha256':a[STORAGE],'new_storage_sha256':b[STORAGE],
            'unchanged_source_files':len(old)-1,'scientific_source_bytes_unchanged_except_export_call':True}


def code_review(checkout):
    checkout=Path(checkout)
    paths=git(checkout,'ls-tree','-r','--name-only',OLD_COMMIT).decode().splitlines()
    old={n:git(checkout,'show',OLD_COMMIT+':'+n) for n in paths if included(n)}
    files=[p for folder in ('src','configs','experiments') for p in (checkout/folder).rglob('*')
           if p.is_file() and included(p.relative_to(checkout).as_posix())]
    files.append(checkout/'pyproject.toml')
    if any(p.is_symlink() for p in files):raise ValueError('source_symlink')
    new={p.relative_to(checkout).as_posix():p.read_bytes() for p in files}
    result=compare(old,new);identity=code_identity(checkout)
    if identity['source_hash']!=result['new_source_hash']:raise ValueError('source_changed_during_audit')
    return {**result,'old_commit':OLD_COMMIT,'proposed_source_code':identity,
            'status':'CODE_REVIEW_ONLY','execution_authorized':False,'plan_modified':False}


def inactive(root):
    # Absence is checked only for this exact recovered inactive child. It is not
    # a claim about the missing historical execution interval or other studies.
    for name in ('attempts','events','outputs','scores','resources','branches',
                 'continuations','approvals','stages'):
        if (root/name).is_symlink() or (root/name).is_file():raise ValueError('invalid_artifact_directory')
        if any(p.is_file() or p.is_symlink() for p in (root/name).rglob('*')):
            raise ValueError('child_not_inactive')
    for name in ('execution-preflight.json','policy-lock.json','policies.json'):
        if (root/name).exists():raise ValueError('child_not_inactive')


def propose(old_checkout,new_checkout,root,output):
    old_checkout,new_checkout,root,output=map(Path,(old_checkout,new_checkout,root,output))
    from pact.revival.documented_freeze import no_symlinks
    from pact.revival.gpqa_source.sources import private_path
    for path in (old_checkout,new_checkout,root,output):no_symlinks(path)
    private_path(output)
    if output.exists():raise ValueError('new_proposal_destination_required')
    audit=code_review(new_checkout)
    if audit['proposed_source_code']['dirty'] or not audit['proposed_source_code']['git_commit']:
        raise ValueError('clean_committed_candidate_required')
    old_identity=code_identity(old_checkout)
    if old_identity!={'git_commit':OLD_COMMIT,'dirty':False,'source_hash':audit['old_source_hash']}:
        raise ValueError('old_checkout_identity_conflict')
    saved=read_json(root/'plan.json');before=file_hash(root/'plan.json')
    if digest(saved)!=PLAN_HASH or saved['source_code']!=old_identity:
        raise ValueError('wrong_original_plan')
    inactive(root)
    # Validate through the old validator in a fresh process. No import swapping,
    # monkeypatch, activation, model factory, wallet or changed source guard.
    env=dict(os.environ,PYTHONPATH=str(old_checkout/'src'),PYTHONDONTWRITEBYTECODE='1',
             CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    check=subprocess.run([sys.executable,'-B','-c',
        'from pathlib import Path; import sys; from pact.revival.documented_execution.plan import validate; '
        'p=validate(Path(sys.argv[1]),sys.argv[2]); assert p["fixture"] is False; '
        'assert p["execution_authorized_by_plan"] is False',str(root),PLAN_HASH],
        env=env,cwd=old_checkout,capture_output=True)
    if check.returncode:raise ValueError('original_validator_failed')
    if file_hash(root/'plan.json')!=before:raise ValueError('original_plan_changed')
    inactive(root)
    summary={**audit,'version':'documented_export_source_transition_proposal_v1',
        'status':'SOURCE_TRANSITION_PROPOSED_NOT_APPLIED','original_plan_hash':PLAN_HASH,
        'original_plan_file_sha256':before,'old_source_code':old_identity,
        'freeze':saved['freeze'],'s0':saved['s0'],'conditional_limits':saved['budgets'],
        'analysis_digest':digest(saved['analysis']),'training_source_digest':digest(saved['training_source']),
        'existing_plan_validated_under_original_checkout':True,
        'current_S0_tensors_rechecked':False,'gpu_runtime_checked':False,
        'transition_approved':False,'transition_applied':False,'reviewer_signature':None,
        'wallet_active':False,'historical_spending':None,'remaining_historical_budget':None,
        'model_calls':0,'training_forwards':0,'optimizer_updates':0,
        'limitations':saved['limitations'],'tool_sha256':file_hash(Path(__file__)),
        'next_gate':'explicit_review_of_exact_proposal_before_any_source_transition'}
    output.mkdir(parents=True,mode=0o700)
    write_json(output/'proposal.sanitized.json',summary)
    h=file_hash(output/'proposal.sanitized.json')
    write_json(output/'checksums.json',{'proposal.sanitized.json':h})
    (output/'COMPLETE').write_text(file_hash(output/'checksums.json')+'\n')
    if file_hash(root/'plan.json')!=before:raise ValueError('original_plan_changed')
    return {**summary,'proposal_sha256':h}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage',choices=('code-review','propose'))
    p.add_argument('--new-checkout',type=Path,required=True)
    p.add_argument('--old-checkout',type=Path);p.add_argument('--run-dir',type=Path)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    try:
        value=code_review(a.new_checkout) if a.stage=='code-review' else propose(
            a.old_checkout,a.new_checkout,a.run_dir,a.output)
        print(canonical(value));return 0
    except Exception as e:
        print(canonical({'status':'stopped','exception_type':type(e).__name__,
                         'action':'preserve_evidence_no_automatic_retry'}));return 1


if __name__=='__main__':raise SystemExit(main())
