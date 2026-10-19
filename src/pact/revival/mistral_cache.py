"""Explicit repair for the reviewed official Mistral Git-LFS pointer discrepancy."""
import hashlib
import os
import re
from pathlib import Path

from ..util import file_hash, write_json

REVISION='c170c708c41dac9275d15a8fff4eca08d52bab71'
GIT_BLOB='029a2451811177349803d8a4789f6861a7afb0e0'
PAYLOAD_SHA='37f00374dea48658ee8f5d0f21895b9bc55cb0103939607c8185bfd1c6ca1f89'
PAYLOAD_BYTES=587404


def verify(raw, payload):
    if hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()!=GIT_BLOB:
        raise ValueError('Official raw Git identity mismatch')
    match=re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n?',raw)
    if not match or match[1].decode()!=PAYLOAD_SHA or int(match[2])!=PAYLOAD_BYTES:
        raise ValueError('Unexpected official pointer contract')
    if len(payload)!=PAYLOAD_BYTES or hashlib.sha256(payload).hexdigest()!=PAYLOAD_SHA:
        raise ValueError('Pointer payload checksum/size mismatch')


def repair(cache):
    import requests
    cache=Path(cache)
    repo=cache/'models--mistralai--Mistral-7B-Instruct-v0.3'
    target=repo/'snapshots'/REVISION/'tokenizer.model'
    if target.is_file() and file_hash(target)==PAYLOAD_SHA:
        return {'tokenizer_payload_verified':True,'already_present':True,'model_calls':0}
    if target.exists() or target.is_symlink():raise ValueError('Different cached tokenizer; preserve it and use a fresh cache')
    token=os.environ.get('HF_TOKEN')
    headers={'Authorization':f'Bearer {token}'} if token else {}
    base='https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3'
    def get(kind,limit):
        try:
            with requests.get(f'{base}/{kind}/{REVISION}/tokenizer.model',headers=headers,stream=True,timeout=60) as r:
                r.raise_for_status();parts=[];size=0
                for chunk in r.iter_content(65536):
                    size+=len(chunk)
                    if size>limit:raise ValueError('Download bound exceeded')
                    parts.append(chunk)
                return b''.join(parts)
        except Exception:
            raise RuntimeError('Official tokenizer repair download failed; no token or URL details emitted') from None
    raw=get('raw',1024);payload=get('resolve',PAYLOAD_BYTES)
    verify(raw,payload)
    blob=repo/'blobs'/PAYLOAD_SHA;blob.parent.mkdir(parents=True,exist_ok=True)
    if blob.exists() and file_hash(blob)!=PAYLOAD_SHA:raise ValueError('Existing payload blob differs')
    if not blob.exists():
        from ..util import atomic_write
        atomic_write(blob,payload)
    if file_hash(blob)!=PAYLOAD_SHA:raise ValueError('Installed payload verification failed')
    target.parent.mkdir(parents=True,exist_ok=True)
    target.symlink_to(Path('../../blobs')/PAYLOAD_SHA)
    if file_hash(target)!=PAYLOAD_SHA:raise ValueError('Snapshot link verification failed')
    receipt={'revision':REVISION,'git_blob':GIT_BLOB,'payload_sha256':PAYLOAD_SHA,
             'payload_bytes':PAYLOAD_BYTES,'tokenizer_payload_verified':True,'model_calls':0}
    write_json(cache/'mistral-tokenizer-repair.json',receipt)
    return receipt
