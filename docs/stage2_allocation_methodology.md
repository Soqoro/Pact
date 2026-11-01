# Stage II allocation reviewed v2

Version: `stage2-allocation-reviewed-v2`. Implementation: `pact.revival.allocation`.
This implements the 27 October reviewed brief as a separate static allocation
experiment. It does not modify historical Stage II, execute Stage III, select a
new starting checkpoint, or establish scientific efficacy.

## Actual source-contract blocker

The completed Stage I evidence uses `arc400_logiqa560_v2`: eight 64-task fitting
blocks comprise **three ARC and five LogiQA blocks**, and its 64 allocation probes
comprise **24 ARC and 40 LogiQA groups**. The new brief simultaneously requires
retaining those exact groups and four blocks/32 probes per source. These conditions
are incompatible. `inspect` records both differences; real `plan` returns
`blocked` without creating a plan. No group is silently replaced, reassigned,
relabelled or newly exposed. A scientific amendment is required before real B/C.
The exact-size 4/4,32/32 implementation is exercised with invented CPU fixtures.

A reviewed inventory must additionally establish that the retained probes and old
Stage II assay have not already executed elsewhere. The imported parent is scanned,
but that scan cannot certify absent external history. Official train-source files
and a complete reviewed exclusion inventory are required to verify availability
of 128 new groups. No fresh-data availability is claimed from fixtures. Semantic
paraphrase exclusion is not established by lexical/group checks.

## A: immutable retrospective synthesis

The importer verifies the exact completed Stage I PRIVATE archive (SHA256
`754dad78534104fbd10b198fcc4842d9217b4d08d424dfa1dd00bb24eea1e3a0`), every
payload checksum, completed stage records and 13,467 committed calls. Synthesis
reproduces original reports in a disposable copy. On-policy clean/exchange outcomes,
private/revision/readout transitions and common fixed-history receiver strata remain
separate. Retrospective decomposition is not mediation. Original unknown historical
work remains unknown; no wallet is replenished. No semantic labels or model calls.

## B: actual temporary updates and common scoring

S0 is the final epoch-2 `uniform_joint_sft` Q/L/M adapters, checked against the
parent's tensor inventory and native identities on load. R is pristine Qwen3;
attack Q is pristine. Exactly 24 branch contracts use one 64-task block and one
adapter. Each starts at S0 with a fresh AdamW, eight updates of eight private-answer
examples, LR 5e-5 without warmup, betas .9/.999, eps 1e-8, weight decay zero,
clip one, BF16 frozen bases and FP32 LoRA/optimizer state. Loss is the ordinary
unit-weight task mean. No receiver objective, DPO, probe gradient or duplicate
base loss is added. Typed checkpoints include optimizer and RNG state.

The unchanged native prompt is input. For gold `B`, the teacher-forced output
prefix is `{"answer":"B"`; only the token(s) carrying `B` are scored. Tokens wholly outside the answer span (including prompt, JSON key, rationale and
EOS) are unscored; a native token overlapping the answer boundary is scored as
one indivisible token. Native tokenizer offsets
(or the inherited slow-tokenizer alignment) determine the exact mask; it is not
assumed that one character equals one model token.

Every block uses the same 32 source probes and paired rollout seed 29. Initial
private packets freeze before delivery; only unchanged private requests may reuse
an exact dependency. The changed adapter is active for private and revision turns.
All three revisions and R regenerate for each branch. One attack attempt per probe
is shared across branches, changes only one outgoing packet for both recipients,
and never changes sender-private state. Rejected attacks remain missing. Exact S0
and RNG rollback is verified; temporary policies never become continuation starts.

Only pristine R scores both revised banks and uncorrupted private banks with the
same renderer/mask. Raw mean answer-token NLL and `min(NLL,10)` are both retained.
Nonfinite or missing technical scores stop computation. Terminal credit averages
clean and accepted-exchange capped-NLL reductions with .5/.5 weights. Zero accepted
attacks in a source makes its terminal rows unsupported, explicitly uniform; it
is not an observed zero credit. Private-bank scores add forwards, not generation.
Generated correctness/coverage and loss-based credits are reported separately.

## C: compiled exposure and prospective evaluation

The existing balanced solver uses negative credits, tau .2 and balance .1.
Hamilton rounding assigns 12 extra slots per block with fixed hash ties. Every
family also receives all 512 fitting examples once through eight base slots/block.
Every team has 288 optimizer updates and 2,304 training forwards; a family receives
64–160 updates. Extra pools shuffle without replacement within each 64-example
cycle and record repeats. Base/extra slots interleave by a fixed hash ordering.
One persistent fresh optimizer per family runs that family's full schedule; model
families execute sequentially to keep one backbone resident.

Five frozen policies, seeds 113 and 227: terminal_block (primary), uniform,
source_family, private_bank, shuffled. Source-family quotas preserve exact terminal
source/family integer margins while redistributing over blocks. The within-source
shuffle is a pre-score derangement and is never strengthened after seeing scores.
Exact full schedule/S0/RNG/prompt-contract aliases execute once and share evidence;
quota equality alone is insufficient. Skips do not fund other work.

Fresh 64+64 train-source groups are sealed before probes; labels/text are not in
training/allocation inputs. All matrices, schedules, final adapters and analyses
lock before evaluator access. Evaluation includes S0 once and all unique policy
executions, with aliases declared. Each team has its own natural private bank and
one clean/exchange synchronous round. The fixed attack pool is frozen after policy
lock and before victim outputs (included smoke requests are reused exactly).

Primary attacked contrasts are terminal_block minus uniform and source_family.
Reports average tasks within source then weight sources equally, average both
continuation seeds and report seeds separately. Ten thousand source-stratified
paired task-cluster bootstrap draws retain all seed views together. 95% intervals
and 97.5% multiplicity-caution intervals are descriptive; two seeds do not replicate
Stage I or allocation estimation. A source with no attacked support makes the
equal-source target undefined. The two-point clean tolerance is descriptive.

## Ownership, storage and budgets

The portfolio has one physical root named `pact-update-allocation-crossed-002`;
`pact-allocation-policy-evaluation-001` is its recorded logical policy child.
Disjoint `assay` and `policy` wallets enforce physical ceilings and shared imports.

| Wallet | Generation | Updates | Training forwards | Diagnostic forwards |
|---|---:|---:|---:|---:|
| Assay | 7,680 | 192 | 1,536 | 2,496 |
| Policy | 15,616 | 2,880 | 23,040 | 0 |
| Total | 23,296 | 3,072 | 24,576 | 2,496 |

All generations reserve 512 tokens: 11,927,552 total. Assay smoke is at most 24
included calls; policy smoke at most 244 included calls. This implementation adds
zero synthetic forwards (the separate allowance is at most 20 with 128 input tokens).

Intent records precede physical work; unknown generation, score or update windows
block execution rather than retry. Unsafe evidence can still be exported. Compact
snapshots contain a checksummed metadata archive plus receipt and separately
content-addressed latest typed tensors (unchanged family weights are not repacked); durable verification precedes clearing pending markers. Restore never
falls back to an older boundary. Preserve exact bound scratch paths when restoring
because frozen checkpoint references are absolute. PRIVATE contains raw evidence;
RECOVERY additionally contains typed tensors; SANITIZED uses an explicit aggregate
allowlist. Neither raw bundle nor tensor archives belong in Git/public outputs.

Storage snapshots are retained without automatic pruning. Provision storage for
changed optimizer/tensor checkpoints across the full study; no Colab Drive quota
or real snapshot throughput has been verified for this new path.
