# Approved amended Stage I evaluation: fresh Colab

Use the NEW reviewed/pushed implementation commit. Keep the verified parent and
old pinned source unchanged. For the actual smoke, use the recorded A100-SXM4-80GB
runtime and HF_TOKEN with Q/L/M/R access. No GPU is needed for import/freeze alone.
Recorded packages: Python3.13.15, Torch2.11.0+cu130, Transformers4.57.6,
PEFT0.18.1, Accelerate1.12.0, Tokenizers0.22.2, Hub0.36.2, Jinja2 3.1.6,
NumPy2.1.3, Safetensors0.8.0. Fresh-process failures must be printed and inspected;
never modify saved fingerprints to bypass a mismatch.

The child has an explicitly approved ADDITIONAL envelope, not a reconstructed
remaining historical budget. Import/freeze does not run models. Run All leaves
RUN_SMOKE=False. First real stage is the <=66-call included smoke only; return its
PRIVATE/SANITIZED ZIPs before requesting another stage. Do not run verify,
recover-inspection, training, new attack acquisition or any all-stage loop.

## 1. Mount Drive and pin the NEW reviewed implementation revision

```python
from pathlib import Path
import os, sys, subprocess, json, time, shutil
from google.colab import drive
drive.mount('/content/drive')
GIT_REF = 'PASTE_NEW_REVIEWED_40_CHARACTER_COMMIT'
import re
assert re.fullmatch('[0-9a-f]{40}', GIT_REF)
SCRATCH = Path('/content/pact-stage1')
CHECKOUT = SCRATCH / ('checkout-' + GIT_REF[:12])
RUN = SCRATCH / 'runs/pact-revival-stage1-evaluation-amended-002'
PERSISTENT = Path('/content/drive/MyDrive/PACT/stage1-evaluation') / RUN.name
CACHE = SCRATCH / 'cache'
SCRATCH.mkdir(parents=True, exist_ok=True)
RUN.parent.mkdir(parents=True, exist_ok=True)
URL = 'https://github.com/Soqoro/Pact.git'
if not CHECKOUT.exists():
    subprocess.run(['git','clone','--filter=blob:none',URL,str(CHECKOUT)],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'remote','get-url','origin'],text=True).strip() == URL
assert not subprocess.check_output(['git','-C',str(CHECKOUT),'status','--porcelain'],text=True).strip(), 'Preserve local changes.'
subprocess.run(['git','-C',str(CHECKOUT),'fetch','--depth','1','origin',GIT_REF],check=True)
subprocess.run(['git','-C',str(CHECKOUT),'checkout','--detach',GIT_REF],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'rev-parse','HEAD'],text=True).strip() == GIT_REF
os.chdir(CHECKOUT)
print('Pinned implementation:',GIT_REF,flush=True)
```

## 2. Install recorded dependencies, load HF_TOKEN and define the helper

```python
subprocess.run([sys.executable,'-m','pip','install','-e','.[model]',
                'tokenizers==0.22.2','huggingface-hub==0.36.2'],check=True)
# Do not replace Torch/CUDA or silently change runtime versions.
sys.path.insert(0,str(CHECKOUT/'src'))
from pact.util import read_json, digest, file_hash, redact
from google.colab import userdata
secret = userdata.get('HF_TOKEN')
assert secret, 'Enable notebook access to HF_TOKEN.'
os.environ['HF_TOKEN'] = secret
secret = None

def stage(name,*options):
    command=[sys.executable,'-u','-m','pact.revival.stage1',name,
             '--run-dir',str(RUN),'--persistent',str(PERSISTENT),
             '--cache-dir',str(CACHE),*map(str,options)]
    log_path=SCRATCH/f'amended-{name}-{time.time_ns()}.log'
    print('Starting:',name,'Log:',log_path,flush=True)
    with log_path.open('w') as log:
        proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
        for line in proc.stdout:
            clean=redact(line)
            token=os.environ.get('HF_TOKEN')
            if token:clean=clean.replace(token,'[REDACTED]')
            print(clean,end='',flush=True);log.write(clean);log.flush()
        code=proc.wait()
    if code:raise RuntimeError(f'{name} stopped ({code}); preserve files and send final lines from {log_path}. No automatic retry.')
    print('Finished:',name,flush=True)
```

## 3. Import the exact verified parent or restore this child, then freeze

```python
APPROVAL_HASH = '49de20c60cb493467fb940b5f27e98280bd7ba0021d612db69c6cb86125642a6'
PARENT = Path('/content/drive/MyDrive/PACT/stage1-evaluation/pact-revival-stage1-evaluation-001/bundles/pact-revival-stage1-evaluation-001-PRIVATE-1792766354718085784.zip')
PARENT_SHA = '6836c626fbfb502c7da4f59db2f70280669db84611ef155280fcc73f8626efda'
LOCAL_PARENT = SCRATCH/'sources'/'stage1-verified-parent.zip'
LOCAL_PARENT.parent.mkdir(parents=True,exist_ok=True)
if not LOCAL_PARENT.exists():
    print('Copying verified parent to scratch...',flush=True)
    shutil.copyfile(PARENT,LOCAL_PARENT)
assert file_hash(LOCAL_PARENT)==PARENT_SHA
assert not (PERSISTENT/'SNAPSHOT_PENDING.json').exists(), 'Pending snapshot: stop for review.'
assert not (PERSISTENT/'INFLIGHT.json').exists(), 'Inflight work: stop for review.'
if RUN.exists():
    stage('inspect')
elif PERSISTENT.exists() and any(PERSISTENT.iterdir()):
    stage('restore')
    stage('inspect')
else:
    stage('init-amended','--private',LOCAL_PARENT,'--approval-hash',APPROVAL_HASH)
RESOLUTION_HASH=digest(read_json(RUN/'contract_resolution.json'))
stage('freeze')
PLAN_HASH=digest(read_json(RUN/'plan.json'))
stage('export','--export-stage','freeze')
print('RUN:',RUN.name)
print('PLAN_HASH:',PLAN_HASH)
print('Additional generation caps:',read_json(RUN/'reconciled_generation_budget.json')['remaining_component_upper_bounds'])
print('Original later-generation history remains unknown. No model calls yet.')
```

## 4. Verify exact runtime in a fresh subprocess

```python
check=r"""
import json,sys
from pathlib import Path
import torch
from transformers import AutoTokenizer,AutoModelForCausalLM
from pact.environment import runtime_fingerprint
root=Path(sys.argv[1])
access=json.loads((root/'evidence/access.json').read_text())
assert torch.cuda.is_available() and torch.cuda.device_count()==1
print('GPU:',torch.cuda.get_device_name(0),flush=True)
actual=runtime_fingerprint()
print('Fingerprint:',actual,flush=True)
assert all(x['runtime_fingerprint']==actual for x in access.values()), 'Exact recorded runtime required; stop and report mismatch.'
print('RUNTIME_MATCHED',flush=True)
"""
result=subprocess.run([sys.executable,'-u','-c',check,str(RUN)],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
output=redact(result.stdout)
if os.environ.get('HF_TOKEN'):output=output.replace(os.environ['HF_TOKEN'],'[REDACTED]')
print(output,flush=True)
assert result.returncode==0, 'Stop and return the runtime-check output.'
```

## 5. Map the same six final tensors from the original training RECOVERY archive

```python
SOURCE=Path('/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-continuation-003/bundles')
TRAIN_PRIVATE=SOURCE/'pact-heterogeneous-receiver-training-continuation-003-PRIVATE-1792630912628874679.zip'
RECOVERY=SOURCE/'pact-heterogeneous-receiver-training-continuation-003-RECOVERY-1792630916259050432.zip'
SIDECAR=RECOVERY.with_suffix('.zip.sha256')
for path in (TRAIN_PRIVATE,RECOVERY,SIDECAR):assert path.is_file(),str(path)
TENSOR_DIR=SCRATCH/'verified-final-tensors'
MAP=TENSOR_DIR/'checkpoint-map.json'
if not MAP.exists():
    assert not TENSOR_DIR.exists(), 'Partial tensor copy: preserve and inspect.'
    stage('map-recovery','--private',TRAIN_PRIVATE,'--recovery-bundle',RECOVERY,
          '--recovery-sha',SIDECAR.read_text().strip().split()[0],'--tensor-dir',TENSOR_DIR)
mapping=read_json(MAP);lineage=read_json(RUN/'training_lineage_map.json')
assert len(mapping)==6 and set(mapping)==set(lineage)
for fit,path in mapping.items():
    assert path==lineage[fit]['tensor_path'] and Path(path).is_file(),fit
print('Six recorded tensor paths available. No repeated synthetic checks.')
```

## 6. Explicit included smoke ONLY — exports and stops

```python
# Change this to True only when explicitly invoking the included smoke.
RUN_SMOKE = False
if RUN_SMOKE:
    stage('repair-tokenizer-cache','--execute','--plan-hash',RESOLUTION_HASH)
    stage('smoke','--execute','--plan-hash',PLAN_HASH)
else:
    print('Smoke not invoked. At most 66 included live calls; zero new attacks or synthetic checks.')
```

## 7. Verify the returned bundles

```python
for kind in ('PRIVATE','SANITIZED'):
    candidates=sorted((RUN.parent/'bundles').glob(f'{RUN.name}-{kind}-*.zip'))
    assert candidates,kind
    local=candidates[-1];durable=PERSISTENT/'bundles'/local.name
    sha=file_hash(local)
    assert durable.is_file() and file_hash(durable)==sha
    print('\nZIP:',local.name,'\nSHA256:',sha,'\nVerified Drive copy:',durable)
print('STOP. Return both bundles and output; no automatic next stage.')
```

## Later stages (separately invoked after reviewing prior evidence)

Each stage requires its predecessor export and the same frozen plan hash. These
are not part of Run All. Restore the same child with the same pinned code and remap
external tensors after reset; pending/inflight markers stop, never trigger fallback.

```python
stage('validation','--execute','--plan-hash',PLAN_HASH)
```

```python
stage('source_evaluation','--execute','--plan-hash',PLAN_HASH)
```

```python
stage('fixed_history','--execute','--plan-hash',PLAN_HASH)
```

Expected artifacts: approved proposal/receipt, preserved parent resolution/budget,
lineage and inference identity manifests, new frozen plan, separate historical and
child accounting, immutable intents/results with physical-attempt IDs, attack reuse
links, live/fixed-history rows, paired metrics, compact snapshots and distinct
PRIVATE/SANITIZED exports. Archive tensors remain in the original training RECOVERY
and external scratch mapping; never delete parent snapshots or checkpoint files.
