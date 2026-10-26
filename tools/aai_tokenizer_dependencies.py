"""Add two missing optional dependencies; check recorded tokenizer identity on CPU."""
import argparse
import importlib.metadata as md
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

PINS = {'sentencepiece': '0.2.1', 'protobuf': '6.33.0'}


def inventory():
    return {d.metadata['Name'].lower().replace('_', '-'): d.version
            for d in md.distributions() if d.metadata['Name']}


def validate_additions(before, after):
    if any(name in before for name in PINS):
        raise ValueError('Expected both optional dependencies absent; preserve existing installation')
    if after != {**before, **PINS}:
        raise ValueError('Package changes exceeded the two pinned additions')


def main(a):
    os.umask(0o077)
    before = inventory()
    if any(name in before for name in PINS):
        raise ValueError('Optional packages already present; inspect before rerunning')
    with (a.record / 'before.json').open('x') as f:
        json.dump(before, f, indent=2, sort_keys=True)
    # --no-deps forbids resolver upgrades; wheels only, no unreviewed source build.
    subprocess.run([str(a.uv), 'pip', 'install', '--python', sys.executable,
                    '--index-url', 'https://pypi.org/simple', '--no-deps', '--only-binary', ':all:',
                    *[name + '==' + version for name, version in PINS.items()]], check=True)
    subprocess.run([str(a.uv), 'pip', 'check', '--python', sys.executable], check=True)
    after = inventory()
    validate_additions(before, after)
    with (a.record / 'after.json').open('x') as f:
        json.dump(after, f, indent=2, sort_keys=True)
    # All tokenizer imports happen after install, in this otherwise stdlib-only process.
    import sentencepiece
    from google.protobuf.message import DecodeError
    sys.path.insert(0, str(a.checkout / 'src'))
    from pact.backends.native import metadata
    from pact.util import read_json, digest
    token_file = Path.home() / '.config/pact/hf-token'
    s = token_file.stat()
    if (any(p.is_symlink() for p in (token_file, *token_file.parents))
        or not stat.S_ISREG(s.st_mode) or s.st_uid != os.getuid() or stat.S_IMODE(s.st_mode) & 0o077):
        raise ValueError('Private user-owned token file required')
    os.environ['HF_TOKEN'] = token_file.read_text().strip()
    try:
        fresh = metadata('M', a.local / 'model-cache')
    finally:
        os.environ.pop('HF_TOKEN', None)
    run = a.local / 'content/pact-stage1/runs/pact-revival-stage1-evaluation-amended-002'
    expected = read_json(run / 'evidence/access.json')['M']
    # CPU has no GPU fingerprint. Every other metadata field must match exactly.
    omit_runtime = lambda v: {k: value for k, value in v.items() if k != 'runtime_fingerprint'}
    if omit_runtime(fresh) != omit_runtime(expected):
        raise ValueError('Saved Mistral metadata/tokenizer identity mismatch')
    result = {'status': 'tokenizer_dependencies_added_and_metadata_matched',
              'added': PINS, 'all_preexisting_package_versions_unchanged': True,
              'metadata_excluding_runtime_sha256': digest(omit_runtime(fresh)),
              'template_hash': fresh['template_hash'], 'template_probe_hash': fresh['template_probe_hash'],
              'gpu_runtime_rechecked': False, 'generation_calls': 0, 'study_state_changed': False}
    with (a.record / 'VERIFIED.json').open('x') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('record', 'uv', 'checkout', 'local'):
        p.add_argument('--' + name, type=Path, required=True)
    try:
        main(p.parse_args())
    except Exception as exc:
        import traceback
        print(json.dumps({'status': 'stopped', 'exception': type(exc).__name__,
                          'locations': [{'file': Path(f.filename).name, 'line': f.lineno, 'function': f.name}
                                        for f in traceback.extract_tb(exc.__traceback__)[-5:]]}), flush=True)
        print('Preserve installation and receipts; do not automatically retry.', flush=True)
        raise SystemExit(1)
