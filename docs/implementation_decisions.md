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

## 2026-09-18: neural replay verified; receiver preference feasibility remains open

The selected check returns 13 usable private-packet pairs and 52 valid suffix
branches. Audit confirms the fixed-context substitutions, preserved other-agent
states, fixed malicious deliveries (including corrupted-sender substitutions),
paired node seeds and all recomputed credits. Mark this neural execution path
verified only on the reported unadapted L4 environment. Do not infer learned PACT
benefit from selected validation tasks, K=2, or the three length-unmatched pairs.

Hold and repair candidate sampling both execute, but 0/16 contexts yield usable
receiver preferences. Every four-candidate set contains only one correctness class;
there is no parser/pair-selector defect. Private-packet pairs cannot substitute for
same-receiver-prompt DPO pairs. Preserve missingness, no relabeled/synthetic wrong
counterparts, and no automatic increase of caps to force the desired result.

This closes the bounded replay diagnostic; no further GPU run is prescribed now.
The next proposed scope is local learning-component work plus a training-split
collection plan that explicitly handles missing receiver pairs. Selected validation
artifacts are evidence for debugging, not training data. Full revision training,
adapter/reference isolation, training memory and final-test evaluation remain
unverified or deferred. No new source/configuration change was needed for this
review. [Evidence and next gate](reviews/qwen3-replay-check-001.md).

## 2026-09-18: first local learning-foundations increment

Implement a scored training-bank contract, CPU masked assignment, same-prompt
preferences, immutable reference-score storage and numerical completion/DPO losses.
Keep neural collection/training commands explicitly unimplemented. The optional
torch wrappers and gradient test are present but unverified locally; do not equate
the synthetic CLI round trip with warm-start or PACT training.

Default answer-NLL scaling uses population statistics over all agent cells in one
frozen training bank, including base-only rows; expose raw NLL as an explicit option.
Store the transform with the bank and actor identities. One bank defines the current
assignment batch and scarcity-weight normalization. Preserve global coefficients
across future per-adapter/microbatch updates. Missing credits remain inaccessible;
all-missing rows retain ordinary supervision. The EG mirror-step cap is
`1/(tau + balance)`, with backtracking and a logged convex gap; an independent
coordinate-bisection comparison caught and resolved near-optimum oscillation from
larger steps. Solver nonconvergence cannot report CLI success.

Canonical answer supervision is mean NLL of `{"answer":"A"}` plus one EOS, with no
gold rationale. Correct sampled packet NLL is also mean completion NLL; DPO uses
completion sums. Verify the exact joint-tokenization prefix, causal shift and masks;
reject silent truncation. Pair selection prefers the same 32-token length bin,
then closest length and stable indices, retaining unmatched cases. Invalid candidates
cannot supply a negative; empty overflow completions remain in missingness accounting.
Balance hold/repair with half the global revision mass each. If either stratum is
absent, expose null coefficients and `full_revision_ready=false`; any alternative
objective must be a named ablation, not an implicit fallback.

Reference keys include masks/text/tokens, agent warm-start identity, base, tokenizer,
template, precision and runtime. Cached sums are checksummed and immutable. This
increment stores supplied reference scores; it does not yet verify real loaded
weights or compute neural scores. A scored-bank schema checks internal consistency,
not authenticity of declared sources or evaluator peer flags. The future collector
must verify manifest/replay/tokenization/peer provenance before emitting training data.

No selected validation artifact becomes a training bank. Freeze official training
manifests and train/validation overlap audits before neural collection; predeclare
budgets and report missing receiver pairs without forcing counterparts or increasing
caps until pairs appear. The proposal's full schedule remains unexecuted. Full scope,
commands and remaining gates: [training foundations](training_foundations.md).

## 2026-09-18: verified train-only sources and immutable selection manifests

Add `prepare-training-data` and `inspect-training-data` independently of the existing
validation runner/configurations. Share parser internals without broadening public
validation entry points. Training records are parsed directly from pinned official
training files, never relabeled from pilot handoffs. LogiQA train source IDs use
`train-NNNN`; existing `eval-NNNN` identities and the complete 80-item pilot manifest
reproduce exactly. Preserve option mappings and separate evaluator labels.

Verify SHA256 and complete source row counts before selection. Require all training
and validation records from both families for the official preparation command;
an 80-item validation subset is insufficient for overlap screening. Fetch missing
files only with explicit `--download`. Keep test-file URLs and execution absent.
Validate count/seed before fetching, and reject wrong cached bytes without replacing
them. Source details and their existing license status remain in each manifest.

Before selecting examples, connect equal source IDs or normalized content groups,
plus word-trigram Jaccard matches at least 9/10, using transitive components. This
fixed lexical rule groups close copies but is not a semantic paraphrase audit.
Exclude training components touching validation; quarantine inconsistent exact
duplicate labels; otherwise retain the smallest task ID. Compare correct answer
text across duplicates so option reordering does not appear as a label conflict.
Similarity itself never depends on labels or model outcomes. Audit records list
all exclusions and component-building edges, not every possible similar pair.

Use equal family quotas and deterministic hashed component rankings; fail on
insufficient availability instead of silently reallocating. Require explicit count
and seed. Current seed 20260918 selects nested 12-task and 1,200-task manifests for
engineering/data-availability review only. These do not configure or launch a neural
training schedule. Labels, tasks, full-pool identities and audit are checksummed;
publish the completion inventory only after verifying written payloads. Outputs
are immutable by default; future training must pin the reviewed manifest hash.

Real-file audit excludes 59 redundant training rows, leaving 1,118 ARC and 7,318
LogiQA candidates. No exact/lexical train–validation matches or exact-duplicate label
conflicts were found. Do not infer absence of semantic paraphrases or test overlap.
No final-test file or model was accessed. Warm-start optimization, scored-bank
collection, real reference scoring and optimizer resume remain to implement.
[Commands, source pins and evidence](training_data.md).

## 2026-09-18: bounded warm-start engine, neural verification pending

Implement a separate clean-answer warm-start engineering recipe, defaulting to
plan-only CLI behavior. Actual loading/training requires `--execute`; do not invoke
it while implementing this increment. Pin the 12-task training manifest; accept only
2–32 tasks and at most one pass per agent. No proposal-size training sweep is enabled.
The default plan is three adapters, three updates each, effective batch four and
microbatch one. Distinct seeds define deterministic task orders, LoRA initialization
and optimization RNGs; all three agents see the same complete 12 tasks in this recipe.

Use a dedicated answer-only prompt and canonical gold answer plus EOS, with no
invented rationale. This realizes clean supervised warm-starting without teaching an
incomplete response to the private-packet justification instruction. The prompt-format
choice needs later packet-behavior validation; warm-start loss alone supports no
robustness/complementarity claim. Labels construct supervised targets only after
rendering. Prefix mismatch and overflow fail rather than truncate.

Choose q_proj/v_proj LoRA only, rank 16 / alpha 32, as a named engineering variant.
Keep the pinned BF16/SDPA Qwen base; explicitly train FP32 adapter parameters and
use non-reentrant gradient checkpointing. AdamW uses LR 1e-5, zero weight decay,
betas (0.9,0.999), eps 1e-8, clipping at one, foreach=False and no scheduler.
Only one optimizer is resident; inactive adapter values are hashed each update.
Backbone requires_grad/grad/version guards operate at runtime. The optional tiny
test additionally compares actual backbone values and tests dropout-sensitive resume;
it has not executed, so these neural guarantees remain unverified.

Save step zero and every completed update using immutable safetensors/typed JSON
checkpoints, never pickle. Preserve adapters, optimizer, Python/torch CPU/CUDA RNGs,
step position and logs. Restart interrupted accumulation from the last saved boundary.
Reject changed code/config/data before model load and changed model/runtime/tokens
or torch execution flags before restoring state. Missing/corrupt checkpoints fail;
no silent fallback to earlier progress. Do not promise cross-hardware bitwise replay.

Export three separate frozen warm-start adapters only after all updates finish;
verify their saved tensor values against the final actors. Do not export base or
embedding weights, automatically sync Drive, populate reference-score caches, or
claim full PACT training. Local completion explicitly leaves persistence unverified.
Real frozen-reference scoring and joint replay/preference training remain outstanding.
Seven control-path CPU tests and the nine-step dry-run plan pass; the tiny model
test requires the explicit opt-in specified by AGENTS.md and remains pending.
[Implementation, commands and limits](warmstart.md).

## 2026-09-18: user-authorized tiny CPU neural checks pass

After explicit opt-in, install CPU-only PyTorch and the pinned Transformers/PEFT/
Accelerate packages in an isolated `/tmp` virtual environment. Run the full suite
with all model tests enabled and model-hub access disabled. All 76 tests pass with
zero skips; no executable patch or methodology change is required.

Promote only the executed paths to tiny CPU neural verification: distinct adapter
and disabled-base readout, completion/DPO gradients and reference detachment,
sequential warm-start update isolation, fresh-object checkpoint/resume with nonzero
dropout, and immutable export/reload. Resume matches all final parameters and logs
exactly on this CPU environment. The warm-start fixture uses rank-2 adapters and
four synthetic token sequences, not the 12-task engineering data or real Qwen weights.

Keep BF16 CUDA training, non-reentrant activation checkpointing, real-tokenizer
training preflight, GPU resume/memory fit and durable training handoff unverified.
The CPU test exercises the shared optimizer engine, not the complete real-model
launcher. No benchmark result or full PACT training claim follows. Default tests
retain their explicit neural opt-in. [Evidence](reviews/neural-cpu-check-001.md).


## 2026-09-18: bounded warm-start notebook and durable recovery

Keep warm-start artifacts separate from validation manifests and bundle schemas.
Add a thin second notebook with `EXECUTE=False` and `STOP_AFTER=1` defaults. An
explicit first GPU invocation performs only one four-example optimizer update;
return and review its handoff before finishing the nine-update recipe. Preserve
the exact training manifest, model, precision, seeds and resume identity checks.

Run the training CLI in a child process to release GPU allocations before storage;
stream redacted logs and report microbatch positions/token counts. Keep a small
local review ZIP before any Drive operation, including hashes of excluded tensor
files. Persist the complete checkpoint tree through the existing verified immutable
object store. The review ZIP is diagnostic metadata, not a resume archive. Store
verification in the handoff receipt rather than rewriting the CLI's local-only
completion statement. A persistence-only retry never calls the training engine.

Restore only an explicitly selected complete snapshot, in a timed subprocess
whose control files stay on scratch. Verify all restored file hashes and the
complete optimizer-boundary sequence before publishing a new scratch directory.
Never fall back to another snapshot or overwrite an existing run. Keep the default
120-second deadline configurable because optimizer snapshots exceed validation
bundle sizes. Runtime loss before persistence can lose unsynced updates; retain
scratch until durable verification succeeds.

Enable non-reentrant activation checkpointing in the already authorized tiny CPU
resume test. Full suite passes 81/81 with neural opt-in; default passes 78/81 with
three expected skips. Snapshot tests use local fixture bytes, not actual Drive or
trained model weights. Real BF16 GPU memory fit/training/resume remain unverified.
[Evidence and boundaries](reviews/warmstart-colab-check-001.md).
