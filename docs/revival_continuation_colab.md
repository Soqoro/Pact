# Amended continuation 003 — fresh Colab sequence

Use the SAME original GPU/runtime/package identities. Preflight rejects changes.
These cells are for a new separately pinned continuation, never replacement-002.
Review `revival_continuation_review.md` before GPU execution: Q resumes from 93,
old step 94 remains unknown, and 291 new updates are the amended budget. No new
collection, independent-arm training, evaluation or Stage II. The user reviews,
commits and pushes local changes first; paste that full reviewed commit in Cell 1.
A runtime interruption still stops on an unresolved transaction; never clear markers.

Cell 1 — paths and pinned checkout. Enable the HF_TOKEN Colab secret.

```python
from pathlib import Path
import os, sys, re, subprocess, json, shutil, time
from google.colab import drive
drive.mount('/content/drive')
GIT_REF = input('Full reviewed and pushed continuation commit SHA: ').strip()
assert re.fullmatch(r'[0-9a-fA-F]{40}', GIT_REF)
REPO_URL = 'https://github.com/Soqoro/Pact.git'
SCRATCH = Path('/content/pact-continuation')
CHECKOUT = SCRATCH / ('checkout-' + GIT_REF[:12])
RUN_ID = 'pact-heterogeneous-receiver-training-continuation-003'
RUN = SCRATCH / 'runs' / RUN_ID
CACHE = SCRATCH / 'cache'
PERSISTENT = Path('/content/drive/MyDrive/PACT/revival') / RUN_ID
PARENT = Path('/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-001/bundles/pact-heterogeneous-receiver-training-001-PRIVATE-1792171769996477145.zip')
FORENSIC = Path('/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-replacement-002/forensics/replacement-002-FORENSIC-PRIVATE-1792568005277432071.zip')
REVIEW_HASH = '2546efe226d2f6d80d0b13bb04930a482487ea7477a892ec821f763de618f0db'
SCRATCH.mkdir(parents=True, exist_ok=True)
if not CHECKOUT.exists():
    subprocess.run(['git','clone',REPO_URL,str(CHECKOUT)],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'remote','get-url','origin'],text=True).strip() == REPO_URL
assert not subprocess.check_output(['git','-C',str(CHECKOUT),'status','--porcelain'],text=True).strip(), 'Preserve local changes.'
subprocess.run(['git','-C',str(CHECKOUT),'fetch','origin',GIT_REF],check=True)
subprocess.run(['git','-C',str(CHECKOUT),'checkout','--detach',GIT_REF],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'rev-parse','HEAD'],text=True).strip().lower() == GIT_REF.lower()
os.chdir(CHECKOUT)
```

Cell 2 — dependencies and fresh-process GPU imports.

```python
subprocess.run([sys.executable,'-m','pip','install','-e','.[model]'],check=True)
from google.colab import userdata
if not os.environ.get('HF_TOKEN'):
    os.environ['HF_TOKEN'] = userdata.get('HF_TOKEN')
assert os.environ.get('HF_TOKEN')
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '0'
sys.path.insert(0,str(CHECKOUT/'src'))
subprocess.run([sys.executable,'-c',"import torch; from transformers import AutoTokenizer, AutoModelForCausalLM; assert torch.cuda.is_available() and torch.cuda.device_count()==1 and torch.cuda.is_bf16_supported(); print(torch.__version__, torch.cuda.get_device_name(0))"],check=True)
```

Cell 3 — thin subprocess runner, with local logs and progress notices.

```python
from pact.util import read_json, file_hash, digest, redact

def study(stage, *options):
    cmd = [sys.executable,'-u','-m','pact.revival.continuation',stage,
           '--run-dir',str(RUN),'--persistent',str(PERSISTENT),
           '--cache-dir',str(CACHE),*map(str,options)]
    log = SCRATCH / f'continuation-{stage}-{time.time_ns()}.log'
    print('Starting:',stage,'Log:',log,flush=True)
    with log.open('w') as output:
        proc = subprocess.Popen(cmd,stdout=output,stderr=subprocess.STDOUT)
    offset = 0
    last = time.monotonic()
    while True:
        with log.open(errors='replace') as stream:
            stream.seek(offset)
            text = stream.read()
            offset = stream.tell()
        if text:
            print(redact(text),end='',flush=True)
            last = time.monotonic()
        if proc.poll() is not None:
            with log.open(errors='replace') as stream:
                stream.seek(offset)
                print(redact(stream.read()),end='',flush=True)
            break
        if time.monotonic()-last >= 30:
            print(stage,'still running; log:',log,flush=True)
            last = time.monotonic()
        time.sleep(1)
    if proc.returncode:
        raise RuntimeError(f'{stage} failed ({proc.returncode}); preserve files and log. No automatic retry.')
    print('Finished:',stage,flush=True)
```

Cell 4 — new child preparation or latest CHILD restore. No parent restore.

```python
study('review')
if RUN.exists():
    assert (RUN/'plan.json').is_file(), 'Partial preparation: stop and preserve it.'
    study('inspect')
elif PERSISTENT.exists() and any(PERSISTENT.iterdir()):
    study('restore')
else:
    sources = SCRATCH/'sources'
    sources.mkdir(parents=True,exist_ok=True)
    for source, name, expected in (
        (PARENT,'parent-private.zip','f9a78141d0c662c06be903b49318f0235f6253d11e42f5bb17b2dd8adf9f2793'),
        (FORENSIC,'forensic-private.zip','bb9d759af00b2ee7942ad25236bced0b6ebf95cbdaccf2f582a22586148d9015'),
    ):
        assert source.is_file(), str(source)
        target = sources/name
        shutil.copyfile(source,target)
        assert file_hash(target)==expected, f'Checksum mismatch: {name}'
    study('prepare','--parent-private',sources/'parent-private.zip',
          '--forensic',sources/'forensic-private.zip','--review-hash',REVIEW_HASH)
PLAN_HASH = digest(read_json(RUN/'plan.json'))
print('Continuation plan hash:',PLAN_HASH)
study('inspect')
```

Cell 5 — official tokenizer cache repair and real identity/restore preflight.
This uses model loads but no generation or training forwards.

```python
study('repair-tokenizer-cache','--execute','--plan-hash',PLAN_HASH)
study('preflight','--execute','--plan-hash',PLAN_HASH)
```

Cell 6 — one INCLUDED new update on the explicitly amended Q branch.
It repeats the logical position 94 from the verified step-93 state; it does not
assert that historical step 94 never executed.

```python
status = read_json(RUN/'training/uniform_joint_sft/Q/status.json')
if status['completed_steps'] == 93:
    study('train-agent','--family','Q','--resume','--stop-after','94',
          '--execute','--plan-hash',PLAN_HASH)
study('report')
assert read_json(RUN/'summary.json')['recovery_safe']
study('export')
```

Cell 7 — complete only joint Q/L/M. Completed fits are skipped.

```python
for family in ('Q','L','M'):
    folder = RUN/'training/uniform_joint_sft'/family
    status = read_json(folder/'status.json') if (folder/'status.json').exists() else {}
    if status.get('complete'):
        print('Already complete:',family,flush=True)
        continue
    options = ['--family',family,'--execute','--plan-hash',PLAN_HASH]
    if (folder/'contract.json').exists():
        options.append('--resume')
    study('train-agent',*options)
    study('report')
```

Cell 8 — completion/accounting checks and final bundles.

```python
study('report')
summary = read_json(RUN/'summary.json')
print(json.dumps(summary,indent=2))
assert summary['training_complete'] and summary['recovery_safe']
assert summary['new_work']['committed_updates']==291
assert summary['combined_committed_updates']==768
assert summary['new_work']['generation_calls']==0
study('export')
print('Return the PRIVATE and SANITIZED bundles with printed SHA256 values.')
print('Keep RECOVERY on Drive. Original step 94 remains historically unresolved.')
```

Expected artifacts: a new plan binding the amendment and imported checkpoint hashes;
unchanged parent evidence in lineage; independent final checkpoints; joint checkpoints,
optimizer/RNG state and logs; phase-bound persistence transactions; a summary with
new versus inherited updates; and PRIVATE/SANITIZED/RECOVERY bundles. These cells
never run evaluation. Full-model GPU restore/update behavior remains unverified
until actual evidence is returned. No claim of improved PACT follows from training.
