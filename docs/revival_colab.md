# Revival: exact commands and execution prerequisites

**Current disposition: real Stage I is blocked by at least73 missing fresh ARC
training groups. Do not buy GPU time or run the smoke for this design yet.** The
commands below describe the implemented interfaces. Source preparation must report
`ready` under a separately reviewed feasible data contract before any real model
stage. No command below changes the960 quotas or exclusion policy.

Local prerequisite artifacts already produced from verified manifests:

- `/var/tmp/pact-revival-prerequisites-20261016/prior-exposure.json`
- `/var/tmp/pact-revival-prerequisites-20261016/revival-source-feasibility.json`

Inventory SHA256:
`3138e7a0ab7b3deb8b05d24f530a68f15f0fd92c436e0c301224242618a01849`.
Keep these metadata inventories private. They cover all prior allocations and the
224 selective tasks; no old adjudication archive or old trained weights are needed.
Do not use an empty inventory. A later ledger revision invalidates this inventory.

## Fresh Colab setup (CPU is sufficient for prerequisite checks)

Run these cells sequentially. Use a reviewed full40-character SHA after pushing.
Changing a frozen source/runtime after calls is not an exact resume.

```python
from pathlib import Path
import os, re, sys, subprocess, json, hashlib
from google.colab import drive
drive.mount('/content/drive')
GIT_REF = 'SET_FULL_REVIEWED_COMMIT_SHA'
assert re.fullmatch(r'[0-9a-fA-F]{40}', GIT_REF), 'Set the reviewed commit first.'
SCRATCH = Path('/content/pact-revival')
CHECKOUT = SCRATCH / 'checkout'
RUN = SCRATCH / 'runs' / 'pact-heterogeneous-receiver-training-001'
CACHE = SCRATCH / 'cache'
PERSISTENT = Path('/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-001')
SCRATCH.mkdir(parents=True, exist_ok=True)
if not CHECKOUT.exists():
    subprocess.run(['git','clone','https://github.com/Soqoro/Pact.git',str(CHECKOUT)],check=True)
assert not subprocess.check_output(['git','-C',str(CHECKOUT),'status','--porcelain'],text=True).strip()
subprocess.run(['git','-C',str(CHECKOUT),'fetch','origin',GIT_REF],check=True)
subprocess.run(['git','-C',str(CHECKOUT),'checkout','--detach',GIT_REF],check=True)
assert subprocess.check_output(['git','-C',str(CHECKOUT),'rev-parse','HEAD'],text=True).strip().lower()==GIT_REF.lower()
os.chdir(CHECKOUT)
subprocess.run([sys.executable,'-m','pip','install','-e','.[model]'],check=True)
sys.path.insert(0,str(CHECKOUT/'src'))
```

The existing model extra pins Transformers4.57.6, PEFT0.18.1, Accelerate1.12.0,
PyArrow22.0.0. Preserve the supplied PyTorch/CUDA stack. Package installation runs
before imports; stage commands below use fresh subprocesses. Native execution
requires one BF16 CUDA GPU. Device capacity/throughput has not been verified for
this training profile; neither L4 nor a specific A100/H100 capacity is guaranteed.

```python
from google.colab import files
uploaded = files.upload()  # choose the reviewed prior-exposure.json
EXPOSURE = SCRATCH / 'prior-exposure.json'
content = uploaded['prior-exposure.json']
assert hashlib.sha256(content).hexdigest() == '3138e7a0ab7b3deb8b05d24f530a68f15f0fd92c436e0c301224242618a01849'
EXPOSURE.write_bytes(content)
SOURCE = SCRATCH / 'source.private.json'

def command(group, stage, *options):
    cmd = [sys.executable,'-u','-m','pact',group,stage,
           '--run-dir',str(RUN),'--cache-dir',str(CACHE),
           '--persistent',str(PERSISTENT),*map(str,options)]
    print('Starting:',group,stage,flush=True)
    subprocess.run(cmd,check=True)  # streams errors; no automatic retry

def study(stage,*options): return command('revival',stage,*options)
def assay(stage,*options): return command('update-probe',stage,*options)
```

Source preparation accesses only the pinned official ARC TRAIN/original English
LogiQA TRAIN and validation files for grouping. It does not access final tests.
With the current contract this step must stop on shortage; it cannot issue calls.

```python
study('prepare-source','--source',SOURCE,'--exposure',EXPOSURE,'--download')
source = json.loads(SOURCE.read_text())
print({k:source.get(k) for k in ('status','shortfall')})
assert source['status']=='ready', 'STOP: return the shortfall; no quota/source substitutions.'
study('plan','--source',SOURCE)
from pact.util import digest
PLAN_HASH = digest(json.loads((RUN/'plan.json').read_text()))
print('PLAN_HASH:',PLAN_HASH)
```

## First six-call source smoke (only after the prerequisite is resolved)

User must already have authorized official Q/L/M/R access, including Llama's gate.
Use the runtime's configured Hugging Face authentication; never paste/log tokens.
No adapter checkpoint is required initially. Preflight checks all four official
identities before any source dispatch.

```python
study('preflight','--execute','--plan-hash',PLAN_HASH)
study('source-smoke','--execute','--plan-hash',PLAN_HASH)
study('report')
study('export')
```

Stop and return PRIVATE+SANITIZED ZIPs. These six private calls are included in the
1536-call bank. No source smoke prompts/tasks may be changed based on results.

## Explicit Stage I continuation, per-agent training and evaluation

After reviewing the smoke, invoke collection and fixed context construction:

```python
study('collect-fit','--execute','--plan-hash',PLAN_HASH)
study('acquire-attacks','--execute','--plan-hash',PLAN_HASH)
study('build-training-bank','--plan-hash',PLAN_HASH)
study('train-sanity','--execute','--plan-hash',PLAN_HASH)
study('report')
study('export')
```

The scratch check makes48 disposable updates and six additional generations;
no successful-answer filter or extra epochs follows it. Each command below trains
exactly one family and one arm. Repeat the cell with the six listed pairs, preserving
artifacts. `--resume` is allowed only for an existing compatible optimizer run.

```python
ARM = 'independent_adversarial_sft'   # then uniform_joint_sft
FAMILY = 'Q'                        # Q, L, M for each arm
options = ['--arm',ARM,'--family',FAMILY,'--execute','--plan-hash',PLAN_HASH]
if (RUN/'training'/ARM/FAMILY/'contract.json').exists(): options += ['--resume']
study('train-agent',*options)
```

Required six pairs: independent/Q, independent/L, independent/M, joint/Q, joint/L,
joint/M, using the exact full arm strings above. Each has128 updates. Same family
initialization, independent optimizer states; main total768 updates. Once all six
complete, freeze fixed epoch2 teams:

```python
study('freeze-team','--arm','independent_adversarial_sft','--plan-hash',PLAN_HASH)
study('freeze-team','--arm','uniform_joint_sft','--plan-hash',PLAN_HASH)
```

Required recovery weights reside in
`RUN/training/<arm>/<Q|L|M>/checkpoints/step-000128/tensors.safetensors`, with the
matching state/checksum files, `contract.json` and `epoch2.json`. The three native
backbones and frozen R are separately fetched from their pinned official revisions.

Explicit evaluation cell: execute for each arm and each split (six invocations).
Use frozen validation first so the common-history diagnostic can reuse it.

```python
ARM = 'frozen_qlm'   # frozen_qlm, independent_adversarial_sft, uniform_joint_sft
SPLIT = 'validation' # then source_evaluation; retain all tasks
study('evaluate','--arm',ARM,'--split',SPLIT,'--execute','--plan-hash',PLAN_HASH)
```

Then run the following for each of the same three arms:

```python
study('evaluate-peer-use','--arm',ARM,'--execute','--plan-hash',PLAN_HASH)
study('report')
study('export')
```

Stage I ceiling17,030 attempts/8,719,360 reserved output tokens, including scratch.
All adverse/flat scientific outcomes are retained. Return PRIVATE and SANITIZED
results; keep the separate RECOVERY bundle with real weights on Drive.

## Stage II: separate review and invocation

Do not run this as a continuation cell in Run All. After a completed Stage I report
is reviewed, freeze against its exact SHA256. The start is fixed joint epoch2,
regardless of which arm had higher accuracy.

```python
REVIEWED_STAGE_I_SHA = 'SET_SHA256_OF_REVIEWED_SUMMARY_JSON'
assay('plan','--stage-i-review-sha',REVIEWED_STAGE_I_SHA)
PROBE_PLAN_HASH = digest(json.loads((RUN/'probe_plan.json').read_text()))
PROBE = ['--execute','--plan-hash',PLAN_HASH,'--probe-plan-hash',PROBE_PLAN_HASH]
assay('collect-base',*PROBE)
```

One branch at a time; choose blocks0..7 and each Q/L/M (24 branches). Its optimizer
is temporary and fresh; resume only its own compatible boundary, never another
branch. Each real branch gets eight steps on64 fitting groups.

```python
BLOCK = 0
FAMILY = 'Q'
assay('temporary-update','--block',BLOCK,'--family',FAMILY,*PROBE)
assay('evaluate-branches','--block',BLOCK,'--family',FAMILY,*PROBE)
```

Once all branches finish:

```python
assay('score',*PROBE)
assay('assign','--plan-hash',PLAN_HASH,'--probe-plan-hash',PROBE_PLAN_HASH)
assay('report')
assay('export')
```

Stage II is separately capped at4928 generations,192 temporary updates,1536
supervised forwards and1792 diagnostic scoring forwards. No output authorizes
coupled training. Stage III has CPU fixture hooks only and rejects real execution.

## Reset and recovery

Repeat only setup/definitions after a runtime reset, then restore the latest
verified snapshot. Do not rerun plan, reset budgets or use an older safe snapshot.

```python
study('restore')  # --persistent supplied by wrapper; destination RUN must be absent
PLAN_HASH = digest(json.loads((RUN/'plan.json').read_text()))
study('inspect')
```

An INFLIGHT marker or incomplete optimizer/scoring attempt stops recovery for
forensic review. When recovering from an explicitly selected RECOVERY ZIP instead,
use `python -m pact revival restore --run-dir <absent-private-path> --bundle <zip>
--sha256 <verified-sha>` without `--persistent`. PRIVATE review ZIPs cannot restore
weights. No archive scripts or pickle execute.

Bundles live at `SCRATCH/runs/bundles/` and durable copies at
`PERSISTENT/bundles/`. Expected artifacts include plan/source/block/exposure
identities, frozen private bank and attack inventory, weighted training bank,
per-family native identity and initialization hashes, actual adapter/optimizer
checkpoints, update logs, live and peer-use metrics, Stage II rollback receipts,
paired scores, allocation analyses and separate private/sanitized/recovery exports.
