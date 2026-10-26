#!/bin/bash
#SBATCH --job-name=pact-storage-probe
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:05:00
#SBATCH --output=pact-storage-probe-%j.out
#SBATCH --error=pact-storage-probe-%j.err
set -euo pipefail
printf 'JOB: %s\nNODE: %s\n' "$SLURM_JOB_ID" "$SLURMD_NODENAME"
python3 - <<'PY'
import json
import os
from pathlib import Path
import re
import stat

# Only filesystem metadata. No directory traversal, writes or payload reads.
def unescape(value):
    return re.sub(r'\\([0-7]{3})', lambda m: chr(int(m.group(1), 8)), value)

mounts = []
for line in Path('/proc/self/mountinfo').read_text().splitlines():
    left, right = line.split(' - ', 1)
    fields, extra = left.split(), right.split()
    mounts.append({'target': unescape(fields[4]), 'filesystem': extra[0],
                   'source': unescape(extra[1]), 'options': fields[5]})

user = os.environ['USER']
roots = ['/tmp', '/var/tmp', '/scratch', '/localscratch', '/local_scratch',
         '/scratch_local', '/lscratch', '/local', '/mnt', '/data', '/work',
         '/workspace', '/srv', '/dev/shm']
for entry in mounts:
    if entry['filesystem'] in {'ext4', 'xfs', 'btrfs', 'zfs', 'nfs', 'nfs4', 'lustre', 'beegfs'}:
        p = entry['target']
        if not p.startswith(('/proc/', '/sys/', '/dev/')):
            roots.append(p)
paths = set(roots)
for root in roots:
    if root != '/':
        paths.add(str(Path(root) / user))
for name in ('TMPDIR', 'SLURM_TMPDIR', 'LOCAL_SCRATCH', 'SCRATCH'):
    value = os.environ.get(name)
    print(json.dumps({'variable': name, 'value': value}))
    if value and value.startswith('/'):
        paths.add(value)
paths.add(str(Path.home()))
paths.add(str(Path.home() / 'pact-aai-transfer/restoration-v1'))

for value in sorted(paths):
    path = Path(value)
    try:
        if not path.is_dir():
            continue
        resolved = path.resolve(strict=True)
        matching = [m for m in mounts if resolved == Path(m['target'])
                    or Path(m['target']) in resolved.parents]
        mount = max(matching, key=lambda m: len(Path(m['target']).parts))
        s, v = path.stat(), os.statvfs(path)
        print(json.dumps({
            'path': value, 'resolved': str(resolved), 'mount': mount,
            'uid': s.st_uid, 'gid': s.st_gid, 'mode': stat.filemode(s.st_mode),
            'write_search_access': os.access(path, os.W_OK | os.X_OK),
            'free_GiB': round(v.f_bavail * v.f_frsize / 1024**3, 2),
            'total_GiB': round(v.f_blocks * v.f_frsize / 1024**3, 2),
            'free_inodes': v.f_favail,
            'read_only': bool(v.f_flag & os.ST_RDONLY),
            'ram_backed': mount['filesystem'] in ('tmpfs', 'ramfs'),
        }), flush=True)
    except OSError as exc:
        print(json.dumps({'path': value, 'error': type(exc).__name__, 'errno': exc.errno}))
print('Metadata only: access/free space is not quota, reservation, or site-policy approval.')
PY
if command -v quota >/dev/null 2>&1; then
    timeout 20s quota -s || printf 'Quota query unavailable, timed out or failed.\n'
else
    printf 'quota command unavailable.\n'
fi
printf 'STORAGE_PROBE_COMPLETE; no files created by the probe, restored, moved or deleted; no GPU/model operations.\n'
