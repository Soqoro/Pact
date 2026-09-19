# Receiver preference feasibility: matched base control

The completed engineering bank contains no receiver preference pairs. This
increment analyzes that failure and implements one bounded diagnostic: run the
unadapted base on the **same saved actor-produced prompts and seeds**. It does not
train, refresh the bank, generate a new team, or export training preferences.
The runner is CPU tested; the actual GPU comparison has not been run.

## Findings from the returned bank

The failure is not a JSON-format or context-overflow problem. All 218 bank calls
reach EOS, and the 24 receiver candidates comprise 14 valid wrong answers and ten
abstentions. Each of the two hold contexts produces four abstentions. Four repair
contexts produce 14 wrong answers and two abstentions. No correct receiver sample
exists to pair with a wrong answer; abstention is not a preference negative.

All six eligible receiver contexts concern one LogiQA training item,
`logiqa:train-7374`. The correct initial agent abandons A in both clean and exchange
conditions; other receivers see its answer-correct packet but do not repair.
The clean private pools, including the original sample and four alternatives per
agent, contain six correct answers out of 15 (agent0: 3/5, agent1: 0/5, agent2: 3/5).
Correct private proposals therefore exist, but that observation does not show
correct receiver completions have appreciable probability under the fixed prompts.

The other task, `arc_challenge:MCAS_2004_5_13`, has no correct clean private sample
among the 15 recorded initial/alternative outputs. Its rationales repeatedly
associate removing heat with becoming gas. It supplies no eligible receiver
context. More receiver samples on these same two tasks would not establish broad
training support.

The LogiQA item also deserves a wording flag: option B's first clause explicitly
says Sichuan excludes Cantonese, while its second clause introduces a conflicting
ordering condition. Several wrong model rationales rely only on the first clause.
This is a possible item-level confound, not a label correction. Keep official gold
A and the existing failure labels; no local relabeling or task replacement occurs.

The common warm start was only three optimizer updates per agent, with answer-only
targets. Revision prompts request answer-plus-justification packets and expose peer
text. Target-format transfer, limited optimization, item difficulty/ambiguity and
communication effects are plausible explanations. None is established by the bank.
There is no pre-training model control on these exact contexts, so a warm-start
regression cannot be inferred from the wrong answers alone.

## Prespecified diagnostic

[`preference_feasibility.json`](../experiments/preference_feasibility.json) pins the
complete source ZIP SHA256 and scored-bank hash. Selection is deterministic:

| Context source | Existing actor outputs reused | Fresh base calls |
|---|---:|---:|
| Both clean tasks, all three agents: original private sample plus four alternatives | 30 | 30 |
| Every eligible original receiver: two hold and four repair contexts, four candidates each | 24 | 24 |
| Total | 54 | 54 |

The private original and four alternatives form a five-sample diagnostic group;
this does not increase the original four-alternative sampling cap or add actor
samples. Receiver groups retain the four recorded seeds exactly. No selected
suffix-replay revision is substituted for an original receiver sample.

Each base call preserves the source messages, rendered prompt and token prefix,
seed, 256-token output cap, 4,096-token context and sampling settings
(temperature 0.7, top-p 0.8, top-k 20). Qwen3-8B revision, BF16/SDPA, no-thinking
template and runtime fingerprint must match the source run. All adapters are absent
from this control. A mismatch fails; no hardware/library/precision fallback occurs.
The maximum new output is **13,824 tokens**. No teacher-forced scoring, suffix
replays, reference model, optimizer or final-test data is used. No private task,
label, peer packet, answer format or abstention rule is changed.

The selection is a retrospective diagnostic on two already-seen training tasks,
not a representative data sample or held-out evaluation. The base receives contexts
created by the actors; results are not an independent base-team accuracy estimate.
Paired seeds hold the RNG setup fixed but do not guarantee matching sampled tokens
under different model policies. Source actor generation cost and new base generation
cost are reported separately.

## Measurements and decision rules

Report all 12 groups by task, condition, original agent, phase and receiver stratum:
correct, wrong, abstention, malformed/invalid and truncation/overflow counts; matched
actor-to-base outcome transitions; and whether each base receiver pool contains
both a correct and a wrong completion. Preserve raw text and actual token IDs.
Incomplete groups cannot claim base pair availability. Never pool candidates
across prompts or across actor/base policies.

- Engineering success requires all 54 immutable results, matching source/runtime
  identities, correct resume behavior and verified persistence. Zero correct
  samples can still be a completed diagnostic.
- If the base also lacks correct receiver samples, this result does not support
  blaming the warm start. Review item/prompt/context support and predeclare a
  broader train-only selection before considering more sampling.
- If the base recovers correct receiver outputs where actors fail, inspect the
  warm-start/export path and answer-only transfer with a separately specified
  control. A single item does not establish a general degradation effect.
- If private base outputs improve but receiver outputs still fail, distinguish
  private answer availability from behavior under the communication prompts.
- If either base stratum contains a pair, that establishes only diagnostic base
  pair availability. It does not make the actor bank ready for revision training.

Every outcome ends this bounded diagnostic. There is no retry-until-pairs loop,
automatic training launch, curated positive insertion, or sampling expansion.
`report.json` has a distinct diagnostic kind, `training_pairs_exported=false`, and
`training_executed=false`. Full PACT readiness and GPU frozen-reference scoring
remain unresolved. No paper placeholder is filled.

## Local plan and tests

```bash
python -m pact preference-diagnostic \
  --config experiments/preference_feasibility.json \
  --bundle results_import/qwen3-bank-001-handoff-1789804954424856576.zip \
  --run-dir scratch/diagnostics/qwen3-base-control-001
```

This verifies the pinned ZIP/checksums, reconstructs selection and reports the cap;
it loads no model and creates no run directory. Actual-source plan and descriptive
group counts are retained under ignored `results_import/preference-feasibility-001/`.
Selection digest:
`31f2d542eb0d8cafb813d1cecb2b198ea605bc74f687b5d720d9f6b2cffe56b4`.

The default suite passes 92 tests with five neural skips; neural opt-in passes all
97. Seven new CPU fixture tests cover archive/hash/path checks, no-model planning,
matched contexts and labels outside requests, partial resume, diagnostic pair
separation, invalid candidates, runtime mismatch, failure ZIPs, timed source copy,
verified snapshot/bundle/restore, no overwrite and zero-call repeated completion.
These tests contain invented outputs and do not measure the base model. The earlier
tiny-model tests still pass. [Implementation evidence](reviews/preference-feasibility-001.md).

## Colab sequence after review and publication

Publish this increment, then pin that new full SHA in setup cell 1 from the previous
instructions. The completed bank commit `12861a1ca4dce794a1f4daaa27e02618fed2956e`
does not contain this command. Use a fresh GPU runtime matching the original L4
environment to avoid stale imported Python modules. Run only the checkout and
installation/GPU-check cells (previous cells 1–2). No warm-start or bank rerun is
needed, and no adapter/optimizer snapshot needs restoring for this base control.

Copy the small source ZIP onto scratch and validate the plan:

```python
from pathlib import Path
from pact.training.feasibility import load_feasibility_config, copy_source_bundle, prepare_feasibility

SCRATCH = Path('/content/pact-scratch')
CHECKOUT = SCRATCH / 'checkout'
CONFIG = CHECKOUT / 'experiments/preference_feasibility.json'
SOURCE = SCRATCH / 'imports/qwen3-bank-001-complete.zip'
RUN = SCRATCH / 'diagnostics/qwen3-base-control-001'
DURABLE = Path('/content/drive/MyDrive/PACT/diagnostics/qwen3-base-control-001')
TIMEOUT = 120
recipe = load_feasibility_config(CONFIG)
print(copy_source_bundle(
    '/content/drive/MyDrive/PACT/collection/qwen3-bank-001/bundles/qwen3-bank-001-handoff-1789804954424856576.zip',
    SOURCE, recipe, timeout_seconds=TIMEOUT))
print(prepare_feasibility(recipe, SOURCE)['summary'])
```

The source-copy worker keeps control files on scratch and uses a deadline. It
verifies the exact ZIP checksum before plan construction. Existing verified bytes
are reused; a mismatching existing file is not overwritten silently. The old
completed bank and its Drive object store remain intact.

Then run this explicitly gated cell. Set `EXECUTE=True` for the reviewed diagnostic;
the default shows only its plan. No other recipe value needs changing.

```python
import json, subprocess, sys
EXECUTE = False
RESUME = False
args = [sys.executable, '-u', '-m', 'pact', 'preference-diagnostic',
    '--config', str(CONFIG), '--bundle', str(SOURCE), '--run-dir', str(RUN),
    '--cache-dir', str(SCRATCH / 'cache/models'), '--persistent', str(DURABLE),
    '--storage-timeout', str(TIMEOUT)]
if EXECUTE:
    args += ['--execute']
    if RESUME:
        args += ['--resume']

DIAGNOSTIC_RESULT = None
with subprocess.Popen(args, cwd=CHECKOUT, stdout=subprocess.PIPE,
                      stderr=subprocess.STDOUT, text=True, bufsize=1) as process:
    for line in process.stdout:
        print(line, end='', flush=True)
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and 'exit_code' in value and 'path' in value:
            DIAGNOSTIC_RESULT = value
    exit_code = process.wait()
if DIAGNOSTIC_RESULT:
    print('Local ZIP:', DIAGNOSTIC_RESULT['path'])
    print('Drive ZIP:', DIAGNOSTIC_RESULT.get('persistent_bundle'))
    print('SHA256:', DIAGNOSTIC_RESULT['sha256'])
    print('Snapshot:', DIAGNOSTIC_RESULT.get('persistent_snapshot'))
if exit_code:
    raise RuntimeError('Preserve scratch and inspect the diagnostic ZIP.')
if EXECUTE:
    assert DIAGNOSTIC_RESULT is not None, 'No diagnostic receipt found.'
```

Expected completion: `diagnostic_complete_local`, `completed_records=54`, exit zero,
and enclosing `persistent_copy_verified=true`. Download the new ZIP:

```python
from google.colab import files
assert DIAGNOSTIC_RESULT is not None, 'Run the explicit diagnostic first.'
files.download(DIAGNOSTIC_RESULT['path'])
```

Return that ZIP plus its SHA256. The local bundle is under
`/content/pact-scratch/diagnostics/bundles/`; the persisted bundle is under
`/content/drive/MyDrive/PACT/diagnostics/qwen3-base-control-001/bundles/`.

## Resume and limitations

Completed calls use immutable, checksummed shards; periodic snapshots occur at
six-call boundaries and finalization first writes a local ZIP. Each Drive operation
has a separate deadline. Resource attempts record fresh calls and pending work;
abrupt runtime loss can leave unmeasured partial-call cost. Final copy time is
outside the recorded invocation timer. Compute units remain unknown unless measured.

For an intact interrupted scratch run, set `RESUME=True` and `EXECUTE=True` using
the same clean commit and environment. After reset, repeat setup and source copying,
then restore the exact snapshot printed by that diagnostic (not the bank snapshot)
into the absent diagnostic run directory before resuming:

```python
from pact.training.feasibility import restore_feasibility
DIAGNOSTIC_SNAPSHOT = ''  # Copy the exact previously verified diagnostic snapshot.
assert DIAGNOSTIC_SNAPSHOT, 'Set the explicit diagnostic snapshot path.'
print(restore_feasibility(DIAGNOSTIC_SNAPSHOT, RUN, timeout_seconds=TIMEOUT))
```

Completed results are reused without generation. Source/model/runtime mismatch
fails; a failure before model identity initialization requires a new run path.
Local storage tests do not verify this new GPU path or post-reset Drive behavior.
