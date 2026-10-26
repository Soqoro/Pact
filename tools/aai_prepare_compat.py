"""Fetch one official compatibility package, verify bytes, extract without installing."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

BASE = 'https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/'
PACKAGE = 'cuda-compat-13-0'
VERSION = '580.82.07-0ubuntu1'
FILENAME = f'{PACKAGE}_{VERSION}_amd64.deb'


def select_record(text):
    matches = []
    for block in text.split('\n\n'):
        fields = dict(line.split(': ', 1) for line in block.splitlines()
                      if ': ' in line and not line.startswith(' '))
        if fields.get('Package') == PACKAGE and fields.get('Version') == VERSION and fields.get('Architecture') == 'amd64':
            matches.append(fields)
    if len(matches) != 1:
        raise ValueError('Exact official package metadata missing/ambiguous; no substitution')
    row = matches[0]
    if row['Filename'] not in (FILENAME, './' + FILENAME):
        raise ValueError('Unexpected package filename')
    if len(row['SHA256']) != 64 or any(c not in '0123456789abcdef' for c in row['SHA256']):
        raise ValueError('Invalid package checksum')
    if not 0 < int(row['Size']) < 150 * 1024**2:
        raise ValueError('Unexpected package size')
    return row


def file_hash(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024**2), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    root = Path(sys.argv[1]).resolve()
    root.mkdir(parents=True, exist_ok=True)
    receipt = root / 'compat-receipt.json'
    dest = root / 'compat'
    if receipt.exists() or dest.exists():
        raise RuntimeError('Compatibility preparation already exists; preserve and inspect before repeating')
    with urllib.request.urlopen(BASE + 'Packages.gz', timeout=60) as response:
        compressed = response.read(16 * 1024**2 + 1)
    if len(compressed) > 16 * 1024**2:
        raise ValueError('Repository metadata too large')
    row = select_record(gzip.decompress(compressed).decode())
    package = root / FILENAME
    if not package.exists():
        partial = package.with_suffix('.partial')
        with urllib.request.urlopen(BASE + FILENAME, timeout=120) as response, partial.open('xb') as out:
            count = 0
            for chunk in iter(lambda: response.read(1024**2), b''):
                count += len(chunk)
                if count > int(row['Size']):
                    raise ValueError('Download larger than official metadata')
                out.write(chunk)
        if partial.stat().st_size != int(row['Size']) or file_hash(partial) != row['SHA256']:
            raise ValueError('Official package checksum/size mismatch')
        partial.rename(package)
    if package.stat().st_size != int(row['Size']) or file_hash(package) != row['SHA256']:
        raise ValueError('Existing package checksum/size mismatch')
    subprocess.run(['dpkg-deb', '--extract', str(package), str(dest)], check=True)
    library = dest / 'usr/local/cuda-13.0/compat/libcuda.so.1'
    if not library.is_file():
        raise ValueError('Expected compatibility library missing')
    value = {'official_url': BASE + FILENAME, 'version': VERSION,
             'package_sha256': row['SHA256'], 'package_bytes': int(row['Size']),
             'repository_metadata_sha256': hashlib.sha256(compressed).hexdigest(),
             'libcuda_sha256': file_hash(library), 'system_driver_modified': False}
    receipt.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value, indent=2), flush=True)


if __name__ == '__main__':
    main()
