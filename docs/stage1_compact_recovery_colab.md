# Recover the audited Stage I inspection after a Colab reset

Storage only; CPU is sufficient. First review, commit and push the maintenance
changes locally. Set the full resulting commit below. Do not reuse the old
03f2319 revision for this command. No model dependencies, HF token or tensors are
needed for this recovery. Do not delete the pending marker or old object files.
The recovered inspection-recovery directory may remain; the active runs directory
must be absent. Failure stops; do not delete partially restored active state.

## Cell 1 — pinned maintenance checkout

```python
from pathlib import Path
import os, sys, subprocess, re, time, shutil, hashlib
from google.colab import drive
drive.mount('/content/drive')
GIT_REF = 'PASTE_NEW_REVIEWED_40_CHARACTER_COMMIT'
assert re.fullmatch('[0-9a-f]{40}', GIT_REF)
SCRATCH = Path('/content/pact-stage1')
CHECKOUT = SCRATCH / ('checkout-' + GIT_REF[:12])
RUN = SCRATCH / 'runs/pact-revival-stage1-evaluation-001'
PERSISTENT = Path('/content/drive/MyDrive/PACT/stage1-evaluation') / RUN.name
SCRATCH.mkdir(parents=True, exist_ok=True)
RUN.parent.mkdir(parents=True, exist_ok=True)
assert not RUN.exists(), 'Preserve existing active scratch; recovery requires review.'
url = 'https://github.com/Soqoro/Pact.git'
if not CHECKOUT.exists():
    subprocess.run(['git','clone','--filter=blob:none',url,str(CHECKOUT)],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'remote','get-url','origin'],text=True).strip() == url
assert not subprocess.check_output(['git','-C',str(CHECKOUT),'status','--porcelain'],text=True).strip()
subprocess.run(['git','-C',str(CHECKOUT),'fetch','--depth','1','origin',GIT_REF],check=True)
subprocess.run(['git','-C',str(CHECKOUT),'checkout','--detach',GIT_REF],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'rev-parse','HEAD'],text=True).strip() == GIT_REF
os.chdir(CHECKOUT)
subprocess.run([sys.executable,'-m','pip','install','-e','.'],check=True)
print('Pinned storage maintenance commit:',GIT_REF,flush=True)
```

## Cell 2 — copy the exact audited archive to scratch

```python
NAME = 'pact-revival-stage1-evaluation-001-PRIVATE-1792657561217646069.zip'
EXPECTED = '3f0d2c8b0b85a8e56b62bfd41cdd7cc8c109563d30ed69cae7f06bcc603aecc3'
LOCAL = SCRATCH / 'recovery-inputs' / NAME
LOCAL.parent.mkdir(parents=True, exist_ok=True)
if not LOCAL.exists():
    print('Copying PRIVATE archive from Drive...',flush=True)
    shutil.copyfile(PERSISTENT / 'bundles' / NAME, LOCAL)
h = hashlib.sha256()
with LOCAL.open('rb') as f:
    for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
assert h.hexdigest() == EXPECTED, 'Archive mismatch; stop without replacing evidence.'
print('Audited archive verified:',EXPECTED,flush=True)
```

## Cell 3 — recover and persist compactly, then stop

```python
RESOLUTION_HASH = '1a201309fe4b4e3d518eec18e754c294dae6b3ecf316d5865bd7aedeeae93f28'
command = [sys.executable,'-u','-m','pact.revival.stage1','recover-inspection',
           '--run-dir',str(RUN),'--persistent',str(PERSISTENT),
           '--private',str(LOCAL),'--execute','--plan-hash',RESOLUTION_HASH]
log_path = SCRATCH / f'compact-inspection-recovery-{time.time_ns()}.log'
print('Starting storage-only recovery. Log:',log_path,flush=True)
with log_path.open('w') as log:
    process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    for line in process.stdout:
        print(line,end='',flush=True)
        log.write(line);log.flush()
    code = process.wait()
assert code == 0, f'Recovery stopped ({code}); preserve files and send final lines from {log_path}. No automatic retry.'
print('STOP: return this output before any checkpoint verification.',flush=True)
```

Success reports `model_calls: 0`, `verification_resumed: false`, a verified snapshot
path and `source_transition_recorded: true`. The pending marker is cleared only
after the worker verifies both compact objects and the completion index. No new
scientific plan, resolution or quota is created. Old failed per-file objects remain.

After a later reset, the ordinary `restore` command on this SAME pinned maintenance
revision reads the compact snapshot. Final tensor files still need remapping from
the original RECOVERY archive to their recorded scratch paths before verification.
The original Cell 5 remains suitable only for a genuinely new run without a pending
marker; it is not the recovery command for this incident. Both evaluation blockers
remain. Actual Colab transport performance is unverified until returned evidence.
