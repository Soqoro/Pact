"""Explicit dataset-only acquisition on AAI; never invoked by an audit/import."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys


def acquire(local, destination, approved=False):
    if not approved:
        raise ValueError('source_acquisition_approval_required')
    from pact.revival.gpqa_source import sources
    from pact.training.data import TRAIN_SOURCES, _source_file
    from pact.datasets import SOURCES
    from pact.util import file_hash, write_json
    local = sources.private_path(local)
    destination = sources.private_path(destination)
    if destination.exists() or local.exists():
        raise ValueError('existing_acquisition_preserve_and_review')
    destination.mkdir(parents=True, mode=0o700)
    write_json(destination/'ACQUISITION_PENDING.json', {'model_calls': 0, 'automatic_retry': False})
    local.mkdir(parents=True, mode=0o700)
    sources.acquire(local/'gpqa', approved=True)
    original = local/'original'; original.mkdir(mode=0o700)
    specs = [*TRAIN_SOURCES.values(), *SOURCES.values()]
    for spec in specs:
        _source_file(original, spec, download=True)
    names = [Path('gpqa')/n for n in (*sources.FILES, 'source-receipt.json')]
    names += [Path('original')/spec['filename'] for spec in specs]
    hashes = {}
    for relative in names:
        src = local/relative; dst = destination/relative
        expected = file_hash(src)
        dst.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with src.open('rb') as r, dst.open('xb') as w:
            shutil.copyfileobj(r, w, length=1024*1024)
            w.flush(); os.fsync(w.fileno())
        if file_hash(dst) != expected:
            raise ValueError('durable_source_hash_conflict')
        hashes[str(relative)] = {'sha256': expected, 'bytes': dst.stat().st_size}
    receipt = {'status': 'official_source_files_downloaded_and_verified',
               'gpqa_revision': sources.native.REVISION, 'files': hashes,
               'source_files': 8, 'receipt_files': 1,
               'model_calls': 0, 'model_downloads': 0,
               'cohort_selected': False, 'eligibility_verified': False,
               'original_sources': [{k:s[k] for k in ('filename','revision','sha256')} for s in specs]}
    write_json(destination/'VERIFIED.json', receipt)
    (destination/'ACQUISITION_PENDING.json').unlink()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--approve-source-acquisition', action='store_true')
    args = parser.parse_args()
    try:
        from huggingface_hub import constants
        if constants.HF_TOKEN_PATH != os.environ.get('HF_TOKEN_PATH'):
            raise ValueError('existing_authentication_path_not_configured')
        result = acquire(args.local, args.destination, args.approve_source_acquisition)
        print(json.dumps(result, indent=2), flush=True)
        return 0
    except Exception as error:
        # No arbitrary exception text, payloads, signed URLs or token strings.
        chain=[];seen=set()
        while error is not None and id(error) not in seen:
            seen.add(id(error))
            response=getattr(error,'response',None)
            chain.append({'type':type(error).__name__,'http_status':getattr(response,'status_code',None)})
            error=error.__cause__ if error.__cause__ is not None else error.__context__
        print(json.dumps({'status':'stopped','errors':chain,'model_calls':0,
                          'action':'preserve scratch and destination; no automatic retry'}), flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
