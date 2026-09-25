# GPQA Diamond support study: completed evidence audit

Run: `qwen3-gpqa-diamond-support-001`. Status: completed inference-only
**development diagnostic**, returned GPU evidence audited locally. This is not
training, final-test evaluation, full PACT or demonstrated PACT efficacy.

## Evidence and verification

PRIVATE ZIP: `qwen3-gpqa-diamond-support-001-PRIVATE-1790329163573954562.zip`.
SHA256: `8db5120f4c25bc9bb99f6c04b3d7571a1c791a5cb13899176fb3a466169b3012`.
SANITIZED ZIP: `qwen3-gpqa-diamond-support-001-SANITIZED-1790329163573954562.zip`.
SHA256: `092483656108bb0b3a8d2534b4f27b234743b4839f53233807adf84a6a73f242`.
Both outer checksums and bounded archive inventories verified. Trusted local
`audit_private_bundle` reconstructed the report from retained call journals through
the existing protocol/parser/scorer; reconstructed private and sanitized summaries
match exactly. No imported code executed or model loaded locally.

Returned clean source: `1627abae3dd724cdbbb5358ebc6152d4c9be77d7`.
Plan hash: `6ffadabfe5127080e09793126095bce628f27cb1ee7c58f637713eec205f8e17`.
The entire frozen-arm contract was compared independently with the prior completed
controlled-study bundle (SHA256 `ba84d5a85d4dd8d301ad9bcef2d6fba7f64547a19ec3b261cf45973ede9202ea`).
Returned environment snapshot, effective actor hashes, runtime fingerprint,
model/tokenizer revisions, template, precision, attention, thinking flag and
sampling defaults match that contract. Effective actor hashes:

- agent0: `eef7b26388dabd812e7519b6cef0ececd1737bd9989c5a5715378694dcbad7ad`
- agent1: `505e04c7518134abfc38222ab7e507ee392c1913292cc387bcc2c7ddd74ce18c`
- agent2: `07ae09c5803bd2603beb88097208da3929a61b98a9f1bd691b4244a53cd79662`

The historical nonfocal FP32→BF16→FP32 load behavior is preserved, not corrected.
These are checked returned runtime receipts, not a fresh local tensor computation;
review ZIPs contain no weights. Non-thinking Qwen3-8B, BF16 backbone/SDPA, existing
packet protocol and base-only readouts were retained. Request reconstruction
checks stored request identities, stage seeds and decoding against the plan.

The PRIVATE upload was found in the repository root and moved to restricted
`/home/gnoriq/pact-private-results/` storage outside Git. No raw benchmark text,
answer keys, prompts, continuations or decodable token arrays are copied here.
The user-returned export log reports durable snapshot
`1790329165129871707-c75e87328e89` and both persisted bundles; Drive was not
independently accessed during this local audit.

## Partition and accounting

Official source revision: `83022cefff930aea54f654c0b282e74b9eeda5c6`.
Partition v2 accounts for198 source IDs:32 selected,164 protected,2 exact
repeated-option exclusions.196 eligible groups: Biology19, Chemistry91, Physics86.
Selected domains: Biology3, Chemistry15, Physics14. The approved case-sensitive,
Unicode-preserving option policy was used before deterministic stratification.
No excluded/protected task generation appears in the validated study journal.
The full198-row CSV is intentionally absent from the bundles; full-source
partition recomputation would require authorized official data. Manifest counts
and selected data are audited, not claimed independently regenerated from that CSV.

All32 tasks completed; missing0.256 attempts,256 committed calls, unresolved0.
Reserved output tokens53248. Actual input145169; output19784.
Zero optimizer steps, teacher-forced forwards, donors or counterfactual replays.

| Stage | Calls | Input tokens | Output tokens |
|---|---:|---:|---:|
| Private |96|31575|11751|
| Independent synthesis |32|23077|199|
| Clean revisions |96|71726|7635|
| Debate synthesis |32|18791|199|

Two recorded collection invocations total1671.44s; summed generation time1429.34s.
These are recorded durations, not billed compute or total notebook elapsed time.
The smoke uses the same request identities within the256-call plan.

## Natural private support

| Measure | Result |
|---|---:|
| Agent0 accuracy |9/32 (28.125%)|
| Agent1 accuracy |7/32 (21.875%)|
| Agent2 accuracy |7/32 (21.875%)|
| Mean agent accuracy |23/96 (23.958%)|
| Initial coverage |9/32 (28.125%)|
| Joint initial failure |23/32 (71.875%)|
| Coverage gain over best agent |0/32|
| Valid correct/wrong mixed support |2/32 (6.25%)|
| Answer disagreement |6/32 (18.75%)|
| All-wrong answer diversity |4/32 (12.5%)|

N0 counts for0,1,2,3 correct private actors: **23,2,0,7**.28 fully valid
teams have corresponding counts19,2,0,7. Four teams contain at least one non-ok
packet. Private parser counts:90 ok,3 abstentions,2 length failures,1 malformed.
A length-limited answer is a strict failure; no lenient salvage was applied.
All correct coverage was already present in agent0; wrong-answer disagreement
is not complementary correct coverage.

## Clean communication

N0→N1 nonzero task transitions:

| Initial correct actors | Revised correct actors | Tasks |
|---:|---:|---:|
|0|0|23|
|1|0|2|
|3|3|7|

Both mixed-support tasks lost their sole correct private packet during revision.
Natural hold retention0/2 agent-contexts across2 tasks; harmful revision2/2.
Natural repair0/4 agent-contexts across those same2 tasks. These four contexts
are not four independent task samples. Both hold opportunities involved agent0;
agent0 had no repair opportunities (undefined0/0, not a zero success estimate).
Overall originally correct packet retention21/23. Revision parsing:90 ok,
4 abstentions,1 length failure,1 malformed.

Utilization7/9; construction0/23; erasure2/9; new availability0/23.
Revised-packet readout loss0/32. Independently synthesized private packets also
failed on both mixed tasks: initial availability did not guarantee readout use.
The successful teams retained all three correct packets; there was no observed
construction on initially all-wrong teams. Both decomposition identities reproduce.

| Terminal protocol | Correct |
|---|---:|
| Independent vote |7/32 (21.875%)|
| Independent frozen synthesis |7/32 (21.875%)|
| Clean debate with frozen synthesis |7/32 (21.875%)|

Paired synthesis→debate correctness:25 wrong→wrong,7 correct→correct, no gains
or losses. Observed difference0/32. The stored empirical bootstrap interval[0,0]
is degenerate and does NOT establish equivalence. Internal answer erasure occurred
even though terminal correctness did not change relative to independent synthesis.

## Interpretation and boundary

The prespecified screen is **sparse_preliminary**:2/32 mixed-support tasks,
below the8/32 support threshold. This configuration supplied little observed
correct/wrong diversity, no coverage gain over its best agent, and no successful
repair on its four observed repair contexts. Neither communication readout improved
terminal correctness here. Do not generalize the two mixed cases into a population
hold/repair rate or interpret harder questions as more complementary.

There are32 sampling units with one draw per actor, not256 independent examples.
Boundary rates retain uncertainty; correct labels do not certify rationale validity,
and natural before/after changes do not isolate a causal peer influence. This is
not a full-Diamond leaderboard result or an untouched test cohort. Historical
ARC/LogiQA evidence remains descriptive and unpooled; completed receiver results
are unchanged. No new run, attacks, alternative sampling, training, prompt change,
or methodological change is authorized by this outcome. Stop for user review.
