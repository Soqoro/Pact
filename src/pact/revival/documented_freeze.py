"""Seal the exact reviewed development cohort; never activate scientific execution.

Kept outside documented_child: that package's bytes are bound by the reviewed
MethodSpec. Changing them would implicitly migrate the candidate's audit.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import zipfile
from ..util import canonical, digest, file_hash, read_json
from .documented_child import review
from .gpqa_source.contracts import allocation_inputs

EXPECTED = {
    'archive_sha256':'1bc27e0f3d90548d54efbb22b437b6639c564ec0da7bb829832b7cdd1eadc88d',
    'candidate_digest':'66f13a4fae506c2ec944a0833fd6dab9f898375caa46bcb60d625ab131375e22',
    'graph_digest':'ddff260749cc7b9736265a258295f97e6d7c7fea36c95a6587e3bbcd8cbea9a0',
    'training_dependency_hash':'d01160bb00a9da7292a305331275139d026d4c21dc5cc274609ab272afbfaf49',
}
ARCHIVE = 'pact-stage2-documented-exclusions-amendment-001-PRIVATE-782c1c0cb8744196.zip'
VERSION = 'documented_cohort_freeze_v1'


def no_symlinks(path):
    if any(p.is_symlink() for p in (path,*path.parents)):
        raise ValueError('symlink_path')


def seal(root, archive, destination, expected, *, fixture=False):
    """Internal fixture flag is test-only; the CLI accepts only exact real identities."""
    root,archive,destination=map(Path,(root,archive,destination))
    for path in (root,archive,destination):no_symlinks(path)
    if destination.resolve()==root.resolve() or destination.resolve().is_relative_to(root.resolve()):
        raise ValueError('separate_freeze_destination_required')
    summary=review.validate(root)
    if summary['fixture'] is not fixture or summary['blockers']:
        raise ValueError('unblocked_exact_mode_required')
    for k in ('candidate_digest','graph_digest','training_dependency_hash'):
        if not expected.get(k) or summary[k]!=expected[k]:raise ValueError('reviewed_identity_conflict')
    if any(summary[k] is not False for k in ('cohort_frozen','execution_authorized','wallet_active')):
        raise ValueError('unexpected_prior_state')
    if file_hash(archive)!=expected['archive_sha256']:raise ValueError('reviewed_archive_conflict')
    for n in ('INFLIGHT.json','SNAPSHOT_PENDING.json','attempts','events'):
        if (root/n).exists():raise ValueError('unexpected_execution_state')
    # Check the whole exact PRIVATE handoff against the live audit before copying.
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        allowed=set(read_json(root/'manifest.json'))|{'manifest.json'}
        if len(names)!=len(set(names)) or set(names)!=allowed|{'checksums.json','HANDOFF.json'}:
            raise ValueError('archive_inventory_conflict')
        if sum(i.file_size for i in z.infolist())>256*1024**2:raise ValueError('archive_size_bound')
        checks=json.loads(z.read('checksums.json'))
        if set(checks)!=allowed:raise ValueError('checksum_inventory_conflict')
        handoff=json.loads(z.read('HANDOFF.json'))
        if handoff!={'version':review.VERSION,'kind':'PRIVATE','child':review.CHILD,'execution_authorized':False}:
            raise ValueError('wrong_private_handoff')
        contents={}
        for n,h in checks.items():
            raw=z.read(n)
            if hashlib.sha256(raw).hexdigest()!=h or (root/n).read_bytes()!=raw:
                raise ValueError('live_audit_archive_conflict')
            contents[n]=raw
    training=json.loads(contents['training.private.json']);allocation_inputs(training)
    method=json.loads(contents['method.private.json'])
    if digest(training)!=expected['training_dependency_hash'] or training['s0']!=method['S0']:
        raise ValueError('checkpoint_or_training_conflict')
    if not fixture:review.sources.private_path(destination)
    # Original proposal continues to report cohort_frozen=false. A separate receipt
    # records the user's later freeze instruction, not a fabricated reviewer signature.
    receipt={'version':VERSION,'child':review.CHILD,'fixture':fixture,
        'status':'COHORT_FROZEN_EXECUTION_DISABLED','candidate_frozen':True,
        **expected,'method_digest':digest(method),'original_manifest_sha256':file_hash(root/'manifest.json'),
        'instruction':'Proceed toward freezing the exact proposed cohort.',
        'scope':'cohort_and_graph_freeze_only','source_standard':'documented_exclusion_screened_development',
        'conditional_limits':summary['conditional_limits'],'limitations':summary['limitations'],
        'historical_spending':None,'remaining_budget':None,'execution_authorized':False,
        'wallet_active':False,'model_calls':0,'training_forwards':0,'optimizer_updates':0,
        'project_freshness_certified':False,'semantic_decontamination':False,
        'policies_and_trained_checkpoints_locked':False,'current_S0_tensors_verified':False}
    files={'evidence/'+n:raw for n,raw in contents.items()}
    files['sealed/prospective.private.json']=contents['candidate.private.json']
    files['sealed/graph.private.json']=contents['graph.private.json']
    files['training.private.json']=contents['training.private.json']
    files['freeze.sanitized.json']=(canonical(receipt)+'\n').encode()
    manifest={n:hashlib.sha256(raw).hexdigest() for n,raw in files.items()}
    files['checksums.json']=(canonical(manifest)+'\n').encode()
    marker=hashlib.sha256(files['checksums.json']).hexdigest()
    files['COMPLETE']=(marker+'\n').encode()
    if destination.exists():
        if any(p.is_symlink() for p in destination.rglob('*')):
            raise ValueError('symlink_in_existing_freeze')
        actual={p.relative_to(destination).as_posix() for p in destination.rglob('*') if p.is_file()}
        if actual!=set(files) or any((destination/n).read_bytes()!=v for n,v in files.items()):
            raise ValueError('incomplete_or_changed_freeze_no_overwrite')
    else:
        destination.parent.mkdir(parents=True,exist_ok=True)
        with tempfile.TemporaryDirectory(dir=destination.parent,prefix='.cohort-freeze-') as tmp:
            staged=Path(tmp)/'seal';staged.mkdir(mode=0o700)
            for n,raw in files.items():
                p=staged/n;p.parent.mkdir(parents=True,exist_ok=True)
                with p.open('xb') as f:
                    f.write(raw);f.flush();os.fsync(f.fileno())
                if file_hash(p)!=hashlib.sha256(raw).hexdigest():raise ValueError('copy_verification_failed')
            # Existing destinations, including incomplete ones, must never be replaced.
            if destination.exists():raise ValueError('concurrent_freeze_destination')
            os.rename(staged,destination)
    return {**receipt,'freeze_receipt_sha256':file_hash(destination/'freeze.sanitized.json'),
            'freeze_manifest_sha256':marker}


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',type=Path,required=True)
    p.add_argument('--freeze-output',type=Path,required=True)
    a=p.parse_args(argv)
    try:
        root=Path(read_json(a.config)['output'])
        print(canonical(seal(root,root/'bundles'/ARCHIVE,a.freeze_output,EXPECTED)))
        return 0
    except Exception as e:
        print(canonical({'status':'stopped','exception_type':type(e).__name__,
            'action':'preserve_evidence_no_automatic_retry','model_calls':0}))
        return 1

if __name__=='__main__':raise SystemExit(main())
