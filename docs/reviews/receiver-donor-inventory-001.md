# Retained same-task donor availability — offline audit

**Finding: no retained external packet source covers the frozen 96 receiver-study
tasks.** The stopped experiment cannot obtain the missing hold/repair support merely
by importing historical outputs. No new generation, training or final-test access
was performed. This is an availability audit, not a methodological change.

## Reproducible evidence

Run from the repository root:

```bash
PYTHONPATH=src python experiments/audits/receiver_donor_inventory.py
```

[Machine-readable inventory](receiver-donor-inventory-001.json) retains every source
ZIP name/SHA256, mapped task IDs, counts, selection hash and overlap results. The
script verifies the target review and eight explicitly selected training-generation
reviews using the existing bounded/checksummed archive reader. Imported text stays
inert. It does not extract archives, import model weights, call models or modify banks.

For each archived raw-output/call record in private or revision phase, match the
serialized `trusted_task` input to the retained training pool. Deduplicate identical
call/raw pairs across nested records and archives. Then compare exact task inputs
and known group/content-group memberships with the frozen receiver-study selection.
Do not count mentions in a plan, labels, attack payloads or unsampled requests as
available donor generations. Final-phase readout outputs are not packet donors.

| Training review | Unique private/revision call records within archive | Mapped source tasks | Current selected-task matches |
|---|---:|---:|---:|
| Initial partial bank | 18 | 1 | 0 |
| Completed bank | 192 | 2 | 0 |
| Base control | 54 | 2 | 0 |
| Receiver feasibility | 424 | 24 | 0 |
| Private-support control | 72 | 24 | 0 |
| Curated-repair diagnostic | 32 | 2 | 0 |
| Prepared actor probe | 104 | 24 | 0 |
| Prepared prompt control | 144 | 24 | 0 |

There are **950 distinct call/raw identities across these archives**, after removing
90 repeated identities. All inspected calls map to training tasks; zero unmapped
calls, zero exact selected-task matches and zero known group/content-group overlaps.
The prompt-control archive includes carried-forward baseline calls and answer-only
outputs. Including them makes this a conservative availability screen, not approval
of those outputs as normal packet donors. Counts are retained call identities, not
newly generated calls or independent statistical samples.

Earlier validation smoke/profile/pilot archives were not used as training donors.
Preparation training metadata/checkpoints are not sampled packet sources. No unknown
or final-test archive was opened for donor discovery. The conclusion is scoped to
these retained training-generation reviews, not every possible future source or
an exhaustive semantic paraphrase search.

## Consequence for the stopped study

`qwen3-receiver-supervision-001` remains at fit hold/repair 2/2 and diagnostic held-out
0/1. The 672 already collected source/donor calls are retained. No new packets were
added, thresholds reduced, tasks replaced, own states forced or old results relabeled.
DPO stays disabled; neither missing DPO pairs nor parsing primarily caused this stop.

The conservative audit included older/different model checkpoints as possible
external-source candidates and still found no same-task matches. Thus relaxing
snapshot compatibility alone cannot recover a donor from the inspected archive set.
Copying historical curated advice from another task would violate task provenance.

## Requirements before a future donor-enabled experiment

A separately identified source must actually provide same-task material; an import
interface cannot create it. Before implementing or launching another study:

1. Identify the available source and its permissions/cost. Retain actual raw outputs
   or genuinely authored reviewed messages; never invent an explanation around a
   supplied label or fabricate a wrong completion. No source has been supplied here.
2. Freeze the task/donor partition map and finite acquisition budget before observing
   donor outcomes. Preserve the distinction between fitting and diagnostic held-out
   groups. Do not supplement this closed run with retry-until-success draws.
3. For every candidate retain exact trusted task input/hash, original split/group,
   source identity, source prompt and model/checkpoint/seed/decoding when applicable,
   raw packet, strict parser outcome and immutable evidence checksum. Human-authored
   messages need an explicit authored/reviewed source category, not a fictitious model
   call. Answer correctness alone is not reasoning verification.
4. Keep external peer text explicitly curated. Keep the receiver's sampled own state
   traceable; never replace an incorrect own answer with a fabricated correct state
   to satisfy hold support. Counterbalance delivered positions without altering text.
   Do not silently weaken the current same-snapshot builder checks to import a new
   source; external provenance requires an explicit versioned extension.
5. Recompute distinct-task hold/repair support before training. Legitimate correct
   advice for a wrong receiver is necessary for repair; a correct own state plus
   legitimate misleading content is necessary for hold. A new source is not a promise
   that both minima will be reached. Missing support remains a stop.
6. Declare the new experiment identity and frozen source contract before updates.
   Preserve the normal receiver input, answer-token CE, three comparison arms, clean
   anchors, DPO-off default, focal-only updates and original deployment protocol.

No specific new acquisition procedure, donor model, human packet set or new budget
is approved or implemented by this assessment. The next concrete prerequisite is
an authentic same-task source; no further Colab command is currently warranted.
