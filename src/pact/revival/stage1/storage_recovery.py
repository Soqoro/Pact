"""One audited, zero-attempt inspection recovery; never an inference retry."""
from pathlib import Path
import json
import shutil
import tempfile

from ...artifacts import safe_relative, run_lock
from ...environment import code_identity
from ...util import digest, file_hash, read_json, write_json
from . import evidence, io

BUNDLE = '3f0d2c8b0b85a8e56b62bfd41cdd7cc8c109563d30ed69cae7f06bcc603aecc3'
RESOLUTION = '1a201309fe4b4e3d518eec18e754c294dae6b3ecf316d5865bd7aedeeae93f28'
ORIGINAL = {'git_commit':'03f2319cb2fc2a962f728e18064ed507d48c9c29','dirty':False,
            'source_hash':'d6b679b5b9180ad8f2718076137769b44a26ab1597530fa50ae16d9906aefda3'}
PROTECTED = '113d850070e6565bfc4553d8f6b3f9ffc2b65923ef01e29e329c57289b0b3f88'
EDITABLE = {'src/pact/revival/stage1/'+n for n in
            ('io.py','evidence.py','__main__.py','storage_recovery.py')}


def transition(resolution,current):
    repo=Path(__file__).resolve().parents[4]
    files=[p for folder in ('src','configs','experiments') for p in (repo/folder).rglob('*')
           if p.is_file() and '__pycache__' not in p.parts
           and not any(x.endswith('.egg-info') for x in p.parts)]
    files.append(repo/'pyproject.toml')
    protected=digest({p.relative_to(repo).as_posix():file_hash(p) for p in sorted(files)
                      if p.relative_to(repo).as_posix() not in EDITABLE})
    if protected!=PROTECTED:raise ValueError('Non-storage execution code changed')
    if current.get('dirty') or not current.get('git_commit'):raise ValueError('Clean pinned recovery source required')
    if digest(resolution)!=RESOLUTION or resolution['source_code']!=ORIGINAL:
        raise ValueError('Recovery is restricted to the audited inspection resolution')
    return {'version':'stage1_storage_transition_v1','inspection_sha256':BUNDLE,
            'original_source':ORIGINAL,'execution_source':current,
            'resolution_hash':RESOLUTION,'protected_code_hash':protected,
            'model_calls_at_transition':0,'scientific_contract_changed':False}


def validate_transition(root,resolution,current):
    expected=transition(resolution,current)
    if read_json(root/'storage_transition.json')!=expected:
        raise ValueError('Pinned storage transition changed')


def recover(root,destination,bundle,resolution_hash):
    if resolution_hash!=RESOLUTION:raise ValueError('Exact reviewed resolution hash required')
    if destination is None or destination.name!=evidence.RUN or root.name!=evidence.RUN:
        raise ValueError('Reserved child directories required')
    if root.exists():raise ValueError('Absent active scratch run required; preserve existing files')
    marker=destination/'SNAPSHOT_PENDING.json'
    pending={'run_id':evidence.RUN,'resolution_hash':RESOLUTION}
    if read_json(marker)!=pending:raise ValueError('Pending marker mismatch')
    if (destination/'INFLIGHT.json').exists() or any((destination/'snapshots').glob('*')):
        raise ValueError('Later durable work exists; no fallback to inspection')
    print('Verifying exact audited inspection archive...',flush=True)
    z,checks=evidence.archive(bundle,BUNDLE)
    try:
        handoff=json.loads(z.read('HANDOFF.json'))
        if (len(checks)!=8845 or handoff.get('stage')!='inspect'
            or handoff.get('recovery_safe') is not True
            or handoff.get('synthetic_attempts')!=0 or handoff.get('verification_ready') is not False
            or any(n.startswith(('synthetic/','intents/','calls/')) for n in checks)):
            raise ValueError('Not the zero-attempt inspection')
        resolution=json.loads(z.read('contract_resolution.json'))
        receipt=transition(resolution,code_identity(Path(__file__).resolve().parents[4]))
        root.parent.mkdir(parents=True,exist_ok=True)
        # Serialize recovery separately from normal run locking; never reset a stale lock.
        lockdir=root.parent/'.stage1-inspection-recovery-lock'
        lockdir.mkdir()
        try:
            with tempfile.TemporaryDirectory(dir=root.parent,prefix='.inspection-recover-') as tmp:
                stage=Path(tmp)/'run'
                from ...studies.forensics import private_root
                private_root(stage,False)
                for n in checks:
                    target=stage/safe_relative(n);target.parent.mkdir(parents=True,exist_ok=True)
                    with z.open(n) as src,target.open('wb') as dst:shutil.copyfileobj(src,dst)
                write_json(stage/'storage_transition.json',receipt)
                evidence.guard(stage)
                stage.rename(root)
            with run_lock(root):
                write_json(root/'recovery.json',{'run_id':evidence.RUN,'recovery_safe':True,
                                                'resolution_hash':RESOLUTION})
                result=io.compact_snapshot(root,destination)
                if read_json(marker)!=pending or (destination/'INFLIGHT.json').exists():
                    raise ValueError('Durable markers changed during recovery')
                marker.unlink()  # Only after worker verifies archive, receipt, index and COMPLETE.
            return {'restored':True,'snapshot':result['snapshot'],'model_calls':0,
                    'verification_resumed':False,'source_transition_recorded':True}
        finally:lockdir.rmdir()
    finally:z.close()
