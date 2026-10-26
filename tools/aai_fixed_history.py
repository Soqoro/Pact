"""First AAI fixed-history dispatch only; no automatic restart or source changes."""
import argparse
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

import aai_stage1_transport as transport
from aai_stage1_restore import COMMIT
from aai_dataset_stage import no_symlinks, write_copy, TENSORS

DATASET_RECEIPT = 'f6d691e8f821bc8cd91759e27ab686bcdfa7c6bae02c83f129f356fe680103da'
FINGERPRINT = 'e4e0376b3dc5b25abcec3b0bc314936d209d519b0b862af52f5255f7bd6532b0'


def boundary(root):
    read = lambda p: json.loads((root / p).read_text())
    transport.require(transport.digest(read('plan.json')) == transport.PLAN, 'Plan changed')
    transport.require(transport.digest(read('contract_resolution.json')) == transport.RESOLUTION, 'Resolution changed')
    for stage in ('smoke', 'validation', 'source_evaluation'):
        record = read('stages/' + stage + '.json')
        transport.require(record.get('execution_complete') is True and record.get('fixture') is False
                          and record.get('plan_hash') == transport.PLAN, 'Required completed stage missing')
    transport.require(not (root / 'stages/fixed_history.json').exists(), 'Fixed history already recorded')
    transport.require(read('exports/source_evaluation.json')['complete_at_export'] is True, 'Export receipt missing')
    intents = {p.stem for p in (root / 'intents').glob('*.json')}
    calls = {p.stem for p in (root / 'calls/shards').glob('*.json')}
    transport.require(intents == calls and len(calls) == 11712, 'Unexpected initial call boundary')
    counts = {}
    for p in (root / 'intents').glob('*.json'):
        component = json.loads(p.read_text())['component']
        counts[component] = counts.get(component, 0) + 1
    transport.require(counts == {'validation': 3876, 'source_evaluation': 7836}, 'Initial components changed')


def invocation(run, persistent, cache):
    return [sys.executable, '-B', '-u', '-m', 'pact.revival.stage1', 'fixed_history',
            '--run-dir', str(run), '--persistent', str(persistent), '--cache-dir', str(cache),
            '--execute', '--plan-hash', transport.PLAN]


def load_token(path):
    no_symlinks(path)
    s = path.stat()
    transport.require(stat.S_ISREG(s.st_mode) and s.st_uid == os.getuid()
                      and stat.S_IMODE(s.st_mode) & 0o077 == 0, 'Token file must be private and user-owned')
    token = path.read_text().strip()
    transport.require(bool(token) and '\n' not in token and '\r' not in token, 'Invalid token file')
    return token


def main(a):
    os.umask(0o077)
    require = transport.require
    source = a.dataset / 'stage1-migration-v1'
    execution = a.dataset / 'stage1-execution-v1'
    require(execution.is_dir() and not (execution / 'STARTED.json').exists(), 'Execution already started')
    # The batch script exclusively creates execution before launching this process.
    with (execution / 'STARTED.json').open('x') as started:
        json.dump({'job_id': os.environ.get('SLURM_JOB_ID'),
                   'plan_hash': transport.PLAN, 'local': str(a.local)}, started)
        started.flush()
        os.fsync(started.fileno())
    require(subprocess.check_output(['git', '-C', str(a.checkout), 'rev-parse', 'HEAD'], text=True).strip() == COMMIT,
            'Wrong pinned scientific source')
    require(not subprocess.check_output(['git', '-C', str(a.checkout), 'status', '--porcelain'], text=True).strip(),
            'Dirty scientific checkout')
    sys.path.insert(0, str(a.checkout / 'src'))
    os.environ['PYTHONPATH'] = str(a.checkout / 'src')
    from pact.util import read_json, write_json, file_hash
    from pact.environment import runtime_fingerprint
    from pact.revival.stage1 import io, evidence, weights
    import torch
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported(),
            'One BF16 CUDA GPU required')
    require(runtime_fingerprint() == FINGERPRINT, 'Exact runtime mismatch')
    require(file_hash(source / 'DATASET_COPY_VERIFIED.json') == DATASET_RECEIPT, 'Dataset receipt changed')
    receipt = read_json(source / 'DATASET_COPY_VERIFIED.json')
    require(receipt['plan_hash'] == transport.PLAN and receipt['execution_started'] is False, 'Wrong dataset boundary')
    # Read-only source validation. Only snapshot objects and tensors are staged locally.
    for i, (name, h) in enumerate(receipt['files'].items(), 1):
        transport.safe_name(name)
        no_symlinks(source / name)
        require(file_hash(source / name) == h, 'Dataset evidence checksum mismatch')
        print(f'Verified dataset file {i}/{len(receipt["files"])}', flush=True)
    tensors = Path('/content/pact-stage1/verified-final-tensors')
    for fit, h in TENSORS.items():
        relative = 'content/pact-stage1/verified-final-tensors/' + fit + '/tensors.safetensors'
        write_copy(source / relative, tensors / fit / 'tensors.safetensors', h)
    relative = 'content/pact-stage1/verified-final-tensors/checkpoint-map.json'
    write_copy(source / relative, tensors / 'checkpoint-map.json', receipt['files'][relative])
    persistent = execution / 'persistent' / transport.RUN
    persistent.mkdir(parents=True)
    for name, h in receipt['files'].items():
        prefix = 'verified-inputs/persistent/' + transport.RUN + '/'
        if name.startswith(prefix):
            write_copy(source / name, persistent / name[len(prefix):], h)
    run = Path('/content/pact-stage1/runs') / transport.RUN
    print('Restoring safe source-evaluation boundary onto /local...', flush=True)
    io.restore(persistent, run)
    boundary(run)
    evidence.guard(run)
    for fit in sorted(TENSORS):
        values, inventory = weights.tensor_inventory(run, fit)
        require(inventory == read_json(run / 'checkpoint_inventory.private.json')[fit], 'Checkpoint identity changed')
        del values
    token = load_token(a.token_file)
    os.environ['HF_TOKEN'] = token
    cache = a.local / 'model-cache'
    cache.mkdir()
    from pact.revival.mistral_cache import repair
    from pact.backends.native import metadata
    from huggingface_hub import snapshot_download
    print('Checking official pinned model access and metadata...', flush=True)
    repair(cache)  # existing official tokenizer-pointer repair, no study-stage writes
    access = read_json(run / 'evidence/access.json')
    for family in 'QLMR':
        fresh = metadata(family, cache, token=token)
        require(fresh == access[family], 'Official metadata identity mismatch for ' + family)
        print('Pinned metadata matched:', family, flush=True)
    # Fixed history revises Q/L/M packets only; R is access-checked, not dispatched.
    identities = read_json(run / 'inference_identity_manifest.json')['models']
    for family in 'QLM':
        saved = access[family]
        print('Downloading/verifying pinned weights:', family, flush=True)
        path = Path(snapshot_download(saved['spec']['repository'], revision=saved['spec']['revision'],
                                     cache_dir=str(cache), allow_patterns=[*saved['metadata_hashes'], *saved['weight_files']],
                                     token=token))
        hashes = {n: file_hash(path / n) for n in [*saved['metadata_hashes'], *saved['weight_files']]}
        require(hashes == identities[family]['pristine_identity']['file_hashes'], 'Model file identity mismatch')
    write_json(execution / 'execution-provenance.json', {
        'plan_hash': transport.PLAN, 'scientific_commit': COMMIT, 'runtime_fingerprint': FINGERPRINT,
        'dataset_receipt_sha256': DATASET_RECEIPT, 'job_id': os.environ.get('SLURM_JOB_ID'),
        'node': os.environ.get('SLURMD_NODENAME'), 'local': str(a.local), 'initial_committed': 11712,
        'stage': 'fixed_history', 'maximum_new_attempts': 1920,
        'maximum_new_reserved_tokens': 983040, 'automatic_resume': False,
        'model_weights_verified_before_dispatch': True,
    })
    # Make generation independent of network availability; no credential needs to be inherited.
    os.environ.pop('HF_TOKEN', None)
    token = None
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    print('Starting ONLY fixed_history; ceiling 1920 new generation calls.', flush=True)
    subprocess.run(invocation(run, persistent, cache), check=True)
    require(read_json(run / 'stages/fixed_history.json')['execution_complete'] is True, 'Stage incomplete')
    require(not any((persistent / n).exists() for n in ('INFLIGHT.json', 'SNAPSHOT_PENDING.json')),
            'Final durable boundary unsafe')
    result = {'status': 'fixed_history_completed_and_exported', 'persistent': str(persistent),
              'stages': {s: (run / 'stages' / (s + '.json')).exists()
                         for s in ('smoke', 'validation', 'source_evaluation', 'fixed_history')},
              'generation_accounting': read_json(run / 'summary.json')['accounting'],
              'bundles': [{ 'name': p.name, 'sha256': file_hash(p), 'bytes': p.stat().st_size}
                          for p in sorted((persistent / 'bundles').glob('*.zip'))]}
    write_json(execution / 'COMPLETED.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('dataset', 'local', 'checkout', 'token-file'):
        p.add_argument('--' + name, type=Path, required=True)
    args = p.parse_args()
    try:
        main(args)
    except Exception as exc:
        # Do not emit HTTP messages, credentials or generated benchmark content.
        print('AAI job stopped:', type(exc).__name__, flush=True)
        import traceback
        print(json.dumps({'locations': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name}
                                        for f in traceback.extract_tb(exc.__traceback__)[-6:]],
                          'http_status': getattr(getattr(exc, 'response', None), 'status_code', None)}), flush=True)
        print('Preserve /local and /dataset evidence. Do not resubmit or clear markers.', flush=True)
        raise SystemExit(1)
