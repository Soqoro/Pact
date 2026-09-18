# Implementation decisions — Milestones 0–2

Scientific authority remains the [proposal](PACT_Conference_Proposal.tex) and the
[complete specification](<PACT_IMPLEMENTATION_SPEC (1).md>). Original supplied documents
and prompts are preserved. The canonical spec filename is a forwarding document,
because the uploaded original has a ` (1)` suffix. No scientific results are filled in.

## Scope and dependencies

- One Python package, dataclasses with explicit schema version 1, an ordinary CLI,
  standard-library CPU tests/reporting, and a thin notebook. No agent framework.
- Presets are JSON documents with `.yaml` extension (the JSON subset of YAML 1.2).
  Unknown fields, unpinned model revisions, unsupported stages and test splits fail.
- Inference releases verified against official package metadata: Transformers
  [4.57.6](https://pypi.org/project/transformers/4.57.6/), PEFT
  [0.18.1](https://github.com/huggingface/peft/releases/tag/v0.18.1), Accelerate
  [1.12.0](https://pypi.org/project/accelerate/1.12.0/), PyArrow
  [22.0.0](https://pypi.org/project/pyarrow/22.0.0/). Transitive versions are recorded
  from the actual environment. This is a proposed compatible set, not a GPU-validated lock.
- The notebook constrains torch to the existing Colab build. No source-built attention
  dependency, implicit CPU offload, quantization, CUDA replacement, or hidden model substitution.
- No training optimizer, DPO, responsibility solver, SAC, adaptive attacker, BFCL, or
  final-test command is implemented. Reserved responsibility/preference schemas are not
  claims of implemented learning. Tiny neural tests are opt-in and initialize random weights locally.

## Authoritative data and selection

Only official validation is downloaded. Source access and checksums were verified during
implementation on 2026-09-16; full source file hashes are in `src/pact/datasets.py`.

| Family | Authoritative source | Revision | Validation semantics |
|---|---|---|---|
| ARC-Challenge | [AllenAI dataset repository](https://huggingface.co/datasets/allenai/ai2_arc) | `210d026faf9955653af8916fad021475a3f00453` | `ARC-Challenge/validation-00000-of-00001.parquet`, 299 rows |
| LogiQA original English | [Original author repository](https://github.com/lgw863/LogiQA-dataset) | `ff6c4cbca47627b3ac2da94a29fa28204a167b41` | `Eval.txt`, 651 eight-line records |

ARC's dataset card declares CC-BY-SA-4.0. No explicit license grant/file was found in
the original LogiQA repository; this remains unresolved metadata. Do not assert a
license inherited from an unrelated repackaging. Full datasets are not bundled.

ARC source labels map in option order to A–Z, retaining each original label. LogiQA
options are defined by their four line positions, not by translated label prefixes.
The actual English release contains 21 option lines without the expected uppercase
`X.` prefix. Matching leading letter-plus-dot/whitespace prefixes are stripped,
case-insensitively; displaced prefixes are preserved verbatim. Blank separators,
lowercase gold IDs, seven nonseparator lines, and nonempty choices are checked strictly.
This was discovered and checked against the actual pinned validation file, not guessed.

Selection ranks normalized content groups by SHA256(seed, group), takes half the
requested count per family, and then orders selected tasks by SHA256(seed, task ID).
Representative selection is stable; duplicate labels must agree. This gives nested
**per-family selections**, not necessarily the same global positions across stage sizes.
Source hashes, canonical mappings, selected IDs, realized counts and duplicate groups
are exported. No semantic paraphrase model is used. Cross-split and semantic audits
remain required before training/extra partitioning; this validation pilot does not
download or inspect final-test examples. No additional train/validation partition is made.

## Model, packet grammar and information flow

- Primary [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B) revision:
  `b968826d9c46dd6066d109eabc6255188de91218`; tokenizer at the same revision.
  Qwen3-0.6B engineering revision: `c1899de289a04d12100db370d81485cdf75e47ca`.
  Runtime identity includes content hashes, actual template text/hash, dtype, attention,
  decoding defaults, and runtime fingerprint. All neural weights load as safetensors
  with remote code disabled. The model cache is runtime-local.
- Default condition: **independent samples from the unadapted base**. No fresh adapters
  are described as learned specialists. Three provided local adapter checkpoints may
  be selected using explicit identities and content hashes. Training provenance must
  be established separately. Readout disables all adapters and restores the previous
  active adapter, including exception paths. All inference parameters remain frozen.
- The official chat template receives `enable_thinking=False`. Private/revision sampling
  is temperature 0.7, top-p 0.8, top-k 20, min-p 0; readout is greedy. The latter is a
  declared fixed-readout choice. Thinking-mode evaluation is rejected in this pilot
  because its output grammar and budget need a separately validated design.
- Exact packet grammar: a single JSON object with **only** `answer` and `justification`.
  `answer` is a canonical ID; justification is a nonempty string. Final readout has
  **only** `answer`. Whitespace around JSON is allowed. Markdown fences, duplicate keys,
  multiple JSON objects, conflicting answer fields, unknown IDs and empty rationales fail.
  `ABSTAIN` is recorded separately and fails correctness. No evaluator repair/LLM judging.
  EOS is required: hitting the output cap counts as a length failure even if a prefix parses.
- Standard context/output caps: 4096 total tokens, 256 private/revised, 64 readout;
  total input plus requested generation is checked **before every model call**.
  Overflow returns an explicit failed packet; nothing truncates trusted task/options.
  It is not an infrastructure crash or a dropped task. Per-call messages, exact rendered
  text, hashes, seed, tokens, stop reason and decoding parameters remain auditable.
- Agents receive the same task, advisory, and neutral sender aliases, without labels,
  correctness, weights, attack IDs/types, source-model identity cues, or role specialization.
  All saved private packets are immutable. Revision sees own private state and only
  delivered initial peers. Early advisory is retained in the saved receiver context.
  Primary readout sees revised packets and the task only. Sender order is deterministically
  shuffled per task, consistently across methods. Literal `<`/`>` are escaped in JSON
  so embedded Qwen role delimiters do not become tokenizer-level privileged messages.

## Attacks, baselines and budgets

Three explicit fixed templates target a label-incorrect option. The offline attacker
may use labels to select that option; defender prompts contain only the permitted
payload, never the label or success metadata. No feedback queries or adaptive search
are performed. The fixed assignments are independent of method/private transcript,
so there is no hidden reference-transcript provenance. One shared early note or one
sender replacement is allowed, with a 256-token cap and balanced sender positions.
The sender's own packet is retained. Replay never regenerates the attack.

| Path | Natural or matched output cap | Readout / communication |
|---|---|---|
| `single` | 256 | One reasoning packet, direct answer |
| `single_matched` | 1600 | One independent reasoning completion; explicit baseline exception to 256 packet cap |
| `vote` | 768 | Three independent packets, unique plurality; ties/all-invalid abstain |
| `vote_matched` | 1536 | Six independent packets; unused 64-token readout allowance disclosed |
| `synthesis` | 832 | Three independent packets + 64-token frozen synthesis |
| `synthesis_matched` | 1600 | Six independent packets + same frozen synthesis |
| `debate` | 1600 | Three private + three synchronous revision + frozen synthesis |
| `ignore_peers` | 1600 | Three private + three own-state-only reconsiderations + synthesis |
| `archive` | 1600, larger natural readout input | Both initial and revised packets |
| `archive_matched` | 1600 | Same drafts; symmetric per-packet text clipping at readout |

Archive-matched limits serialized low-trust context to the smaller of 768 tokens and
the corresponding three revised packets' actual serialized context length. All six
texts receive the same clipping cap, logged in trajectory warnings. This is a disclosed
context-compression control and can lose useful text. Task/options are preserved.
The natural archive path gets its larger context up to the shared 4096 hard limit.
Actual input/output counts and readout context lengths accompany both. Output-cap
matching is **not a claim of equal total tokens, wall time, FLOPs, or identical prompts**.

No peer-exchange results exist for single, vote, synthesis, or ignore-peers paths;
those cells are N/A with no model calls. No boundary-corruption attack is substituted.
Natural baselines and matched variants have separate 80-item presets with the same
task selection/attack assignments. Run both for cost-control comparisons; neither
configuration auto-launches the other. All ten paths are exercised by CPU smoke.
Early-note recipient counts reflect actual independent private contexts (one, three,
or six); N/A exchange cells record zero deliveries. Delivered attack-token totals are
reported separately from total model input tokens.

## Replay and receiver eligibility

Probe uses ordinary debate on the configured first N selected tasks, across its
declared conditions. Four private alternatives are sampled per agent under precisely
the original actor context. Both must parse; correct/incorrect is label-checked only.
Pair selection first prefers a shared 32-token length bin, then shortest absolute
length difference, then sample indices. All candidates and unmatched cases remain.
Missing either class produces `missing_pair`, with null Q/delta and no suffix calls.

Both branches keep the entire frozen team snapshot, other private packets and attack
bytes/site. Every revision and final readout is rerun for each of K=2 matched suffix
seeds, with independent deterministic seeds per node. Corrupted-sender branches
still deliver the identical malicious payload in both branches. Results include
each paired outcome and difference. No confidence claim follows from K=2.

A bounded receiver probe samples up to four completions under the exact saved
receiver prompt. Hold contexts require initially correct receivers and at least one
answer-incorrect delivered peer; repair requires initially incorrect receivers and
an answer-correct peer. Only naturally delivered, same-task messages are used. No
curated insertions or gold rationales are fabricated. Contexts without either stratum
are `ineligible_context`. These records establish **eligibility**, not trained DPO pairs:
warm-start references, token masks/NLLs, reference scoring and learning are deferred.

No generation/KV cache is shared across calls or agents. A future cache-key contract
includes full input, provenance, model/template/checkpoint/runtime identity, decoding
and seed; tests check invalidation. Current cache hits are zero.

## Metrics and storage interpretation

Metrics use complete joint task records, never products of marginal error rates.
`c,u,k,d,r` and readout loss follow the spec. Undefined conditionals are null with
counts/reason; weighted impossible-event contributions are zero. Nonrevision metrics
are N/A. Harmful revision is reported both over initially correct receivers and
conditional on an incorrect peer; helpful repair conditions on incorrect receivers
with an answer-correct peer. Pairwise errors include unconditional co-failure and
Jaccard overlap (intersection / union of error events). Invalid answers remain failures.

One attack assignment per original task/channel; equal task weights within each
method/channel. Method-minus-debate comparisons use paired complete tasks and a
task-clustered percentile bootstrap. Clean-conditional ASR reports method-specific
and common-clean-correct denominators. A missing paired clean record is not treated
as a clean failure. Partial collection is labeled partial and includes missing counts;
reported observed-only rates never imply a complete benchmark. Single-seed pilot
intervals do not estimate training-seed variation or establish non-inferiority.

Local immutable shards have data plus SHA256 completion markers. An interrupted
unmarked file is quarantined and recomputed; a marked corrupt file is rejected.
Run/config/code/model/dataset/runtime identities must match on resume. A new environment
requires a new run ID; statistical continuation/imported-shard reuse is not implemented.
The Git SHA and executable-source hash distinguish dirty local implementation runs.
On Windows a pre-existing lock requires manual process inspection before removing it;
the runner never uses Windows `os.kill(pid, 0)` as a liveness probe. Windows execution
has not been tested locally; Colab and the exercised local environment are Linux.

Hot manifests/attempt logs/cache stay on scratch. At configurable completed-record
boundaries (default five), a content-addressed persistent object store verifies copies
before writing a new snapshot index and its completion marker. Earlier versions remain.
Resume ignores incomplete snapshots and can recover an earlier fully verified one.
A hard runtime loss can repeat at most the unsynced completed work; its prior cost is
unknown and is disclosed. Completion does not rely on a shutdown hook. Infrastructure
errors preserve diagnostic bundles and commands. OOM never changes settings silently.

Reports can be rebuilt offline from evaluator records in the handoff. Raw trajectories
remain in the persistent snapshot; the handoff contains a deterministic bounded sample,
all metric records, provenance and locations/hashes for omitted artifacts. ZIP import
rejects traversal, symlinks, unknown executable members, duplicate names, bad checksums
and excessive extraction size. It never unpickles or executes anything. Credentials
are not in URLs/manifests; environment dumps contain package versions, not environment
variables. Exceptions are redacted; raw model/attack text is always untrusted data.

## Remaining engineering uncertainties

Base-model inference and measured short-context memory/throughput are verified on
the returned L4 smoke/profile environment. PEFT adapter isolation and eligible replay
suffix execution remain GPU-unverified. Twenty-item profiling measures inference; a disposable training
microbatch and explicit sequence-length sensitivity are deferred and marked as such
in resource reports. There is no 8B training-memory claim. Colab's runtime/storage
constraints are documented by [Google](https://research.google.com/colaboratory/faq.html);
the target device is checked, never guaranteed. PEFT adapter operations follow
[the official API](https://huggingface.co/docs/peft/en/package_reference/peft_model).

## 2026-09-17: recovery after final Drive synchronization stalled

The returned profile raw archive contains all 60 complete, checksummed records and
finished reports, but no final snapshot receipt. The user observed a roughly 30-minute
stall after the final counter and needed a runtime restart. At the recorded commit,
the runner writes `persistence=complete` before calling the final sync. This makes a
local manifest insufficient evidence for remote durability. The precise blocked
filesystem call and underlying Drive cause were not captured; no network-performance
claim is inferred from the archive.

The repair leaves scientific configuration, prompts, sampling, tasks and scoring
unchanged. Storage writes run in a separate Python process with a 120-second wall
deadline per operation and visible progress/10-second waiting notices. On deadline
or interruption, the parent kills the worker and waits at most one extra second;
an OS-blocked child is explicitly reported rather than indefinitely awaited. No
success is claimed after timeout. This protects the notebook process from synchronous
mounted-filesystem writes; preflight/mount and restore reads are not covered by this
write deadline. There is no automatic retry after a failed periodic checkpoint.

The runner omits a redundant periodic sync at the last record, builds and prints a
local recovery ZIP before the final snapshot, and only records local persistence
success after receiving a verified snapshot path. The snapshot itself records the
pending intent; its verified index/COMPLETE marker is the durability evidence.
The local manifest then adds `verified_snapshot` and the local handoff records success.
Earlier snapshots are retained and restore still validates every referenced object.
The notebook copies/verifies its final handoff ZIP with the same deadline, and no
longer performs another full raw-run sync. Existing immutable objects are hashed
once per sync, removing the prior duplicate read without skipping verification.

On storage failure, completed model work stays complete, persistence is failed, and
the attempt logs record the storage error separately. Diagnostic bundles retain
that distinction. Existing recovered profile bytes are never rewritten; the derived
handoff explicitly marks old persistence unverified and explains the correction.

A new `storage` preset runs 12 mock records and the normal persistence/handoff path,
without model downloads or inference. Its purpose is to check actual Drive behavior
cheaply before another GPU run. Local worker timeout, checkpoint recovery, honest
status, bundle verification, and notebook failure-return tests pass. The repaired
path still needs actual Colab verification; small local tests do not establish large
pilot Drive throughput. The patch changes executable source identity and must be
published/pinned as a new commit. It is not an exact continuation of the old profile,
whose complete recovered records remain usable without regeneration.

Subsequent verification on 2026-09-17: the user returned `drive-storage-check-001`
from published commit `ede29d6931aa1d4634c2a9bd47dcdcc2a54708ea`. The final ZIP and
all member checksums match, all 12 mock records are complete, and its snapshot
receipt/ZIP-copy log establish normal small-run storage success on the reported
Colab environment. This closes the normal-path check above; timeout behavior on
an actually stalled Colab mount and large pilot throughput remain unverified.
See [the storage review](reviews/drive-storage-check-001.md). No code change followed.

## 2026-09-18: pilot evidence before further sampling or training

The completed 80-item unadapted pilot does not establish the scientific gate for
expensive specialization. Simple controls match or exceed debate's point estimates;
only three clean teams show mixed correctness; the four-task probe has no eligible
packet or receiver pair. These are diagnostic findings, not bugs or a result for
trained PACT. Missing credits stay null. A small probe cannot establish that pairs
are impossible across the task pool, and no sampling/attack change is justified
solely to force the desired mechanism.

All exported metrics reproduce, but the current six-example handoff omits every
probe trace and most paired mechanism cases. The next action is therefore a
CPU-only export of the already persisted raw run, rather than more GPU collection.
Keep the original configuration and artifacts. Inspect the candidate text, parser
outcomes and fixed-context invariants before deciding whether a bounded follow-up
is needed. Any future scientific configuration change requires a new run identity.
No automatic Milestone-3 training, final-test use, or paper-placeholder update follows.

The pilot reports a verified final snapshot at the repaired commit, so normal-path
storage verification now includes this 1,440-record run. This does not establish
that a genuinely blocked Colab filesystem has exercised the timeout fallback.
Review details and exact export instructions are in
[the pilot review](reviews/qwen3-pilot-001.md) and [the runbook](colab_runbook.md).

## 2026-09-18: raw audit closes recovery; selected feasibility check proposed

The requested raw ZIP is received and its checksum matches. All records and calls
pass local audit, including candidate contexts/seeds/pair selection. No source fix
is justified by the zero-pair result. The earlier export request is complete.
The full context census reveals 97 hold and ten repair opportunities, but the four
probe tasks sampled just two hold contexts. Missing sampled pairs therefore do not
establish that usable pairs are absent across the 80-task pool.

The next proposed local engineering increment is a fixed-budget, explicitly
selected diagnostic on the three observed mixed-initial tasks, preserving model,
decoding, original attack bytes/site and node seeds. Its purpose is to exercise
eligible replay/receiver paths before any training decision, not estimate accuracy
or claim a preservation benefit. Disclose selection and keep its results separate
from the original pilot. No new configuration/command is implemented by this review;
local tests, review/publication and a new pinned run identity must precede execution.
Do not change caps/temperature until pairs appear. Keep training/final-test deferred.
The concrete scope and upper bound are in the
[raw review](reviews/qwen3-pilot-001-raw.md#decision-and-smallest-useful-follow-up).

## 2026-09-18: implement the bounded selected feasibility check

The user approved proceeding with the proposed local extension. Add a separate
SelectedConfig serialization so existing ordinary config hashes remain unchanged;
only this explicitly named purpose permits the three-task, unbalanced selection.
The preset is fixed to debate, clean/exchange, three tasks and the original 4/4/K=2
probe cap. A generation-settings digest rejects accidental seed/model/precision/
length/sampling changes. The selected pool is rebuilt from official validation
sources and checked against the original full manifest and task/label hashes.

Retain original zero-based positions 41/61/70, not filtered positions 0/1/2, for
exchange sender assignment. Pin both clean/exchange attack IDs per task and validate
all six against generated payload/site identities before any inference; check the
original model snapshot at the same boundary. Reject reuse of the source run ID.
Regenerate these six main trajectories under the original node seeds; do not alter
or pretend to resume the completed pilot. New config identity intentionally gives
new probe seeds, while corresponding suffix branches remain paired by node.
Different runtime fingerprints are disclosed for a new run; existing strict resume
checks still prohibit silently continuing across changed runtime/code/configuration.

Mark selected engineering scope in manifests, metrics, diagnostics and handoffs.
The existing six-example export includes this entire six-record run, including its
probe candidates/suffixes. No extra raw-export workflow is necessary. Tighten the
reported probe-token upper bound to account for 64-token finals separately from
256-token packets; this changes accounting only, not generation caps or protocol.
No automatic sweep, retry-until-eligible, training or final-test command is added.
The new path is CPU-tested but GPU-unverified. Publication requires a new commit;
source-run evidence remains immutable. [Execution guide](replay_check.md).
