# Revival storage incident — 19 October 2026

## Evidence boundary

User-returned Colab inspection, not locally imported weight archives. Latest
runtime was reset and scratch lost. Drive inventory reports 243 snapshot directories,
480 objects occupying 345.90 GiB, and exported bundles occupying 3.23 GiB. Latest
exported recovery remains the completed scratch milestone (1792171769996477145).

Latest two directories have neither index nor completion marker:
`1792325381948137221-1b99c7e2ccd6`, `1792324899978463252-4fa0ab893374`.
Three subsequent indexed snapshots reference missing state archives:

| Snapshot | Receipt safe | Missing state object |
|---|---|---|
| 1792324413409247972-f845d4499f38 | false | 97946816342fd02a21da40fe394aa3f2962fa2e924ef3a68ad8c32525c175013 |
| 1792324069653484611-6cd98c8865ed | true | 529ddd24abb8395919db6574e90d9ebc10cdeb800fab6c8022a2593e06577458 |
| 1792323775514045724-8b327bd72c9c | false | 69e4c8f8648c3ad92a77a81451e2be10e54fe164576ef80a5576be2631ecdfae |

## Surviving inspected evidence

Snapshot `1792323528940308589-1fa2b5b6d9f1` references object
`8371bafc49022ae2d8e344696be465fcb8410a39712e348a0715530a0a455e4c`,
3,569,263,304 bytes. Its receipt is safe; individually checked status members show
independent-adversarial Q at 28/128 updates, latest intent 28, no epoch2 marker.
Other five fits have no saved status in this archive. This does NOT establish that
no later work occurred. Whole-archive SHA256 has not yet been independently checked.

Two preceding inspected archives retain step27 safe and intent28 unsafe states.
Later missing/empty snapshots mean the latest actual optimizer boundary is unknown.
The old safe receipt is not authorization to roll back and replay updates.
No INFLIGHT marker does not certify optimizer safety: optimizer attempts are
represented inside the archived update-attempt/checkpoint state.

## Implementation finding

Pinned `neural.train` calls persistence before and after every optimizer step.
`runtime.checkpoint` packages the run into a full recovery ZIP, and content-addressed
storage retains each changed ZIP as a distinct large object. Each archive also
includes retained scratch checkpoint tensors and optimizer state. This duplicates
large payloads across steps and explains the measured storage accumulation and
substantial I/O. It does not alone establish why particular Drive objects are
missing despite completed indexes; quota/visibility/deletion causes remain unproven.

## Disposition

Main training completion is not established. No automatic restore of an older safe
snapshot, re-plan, regeneration or retry of ambiguous optimizer work. Preserve
latest surviving weight archives, all metadata/receipts and missing-object evidence.
First verify full hashes of retained archives, then produce an explicit reference-
aware retention/deletion manifest before removing any historical objects. Retain
unknown/unreferenced objects until examined; deleting empty latest directories
must never make an older snapshot appear to be the authorized latest state.

The persistence design needs a separately tested bounded-storage correction before
further training. Any runtime/code migration must be explicit and preserve recorded
scientific budgets and the unresolved execution history. No correction or cleanup
has yet been executed. This audit changes documentation only and does not invalidate
or replace the completed source/scratch evidence.

## Returned full-hash verification

The user subsequently streamed and verified these three complete Drive objects:

- `8371bafc49022ae2d8e344696be465fcb8410a39712e348a0715530a0a455e4c`, 3,569,263,304 bytes (recorded-safe step28).
- `d5cbe37a620d7ab9cd1d78c90e9faa022bc1b32af1fc0ce3e3822d0f4108bb50`, 3,569,254,755 bytes (pending step28).
- `404aa7c4697221e5125be68ceda4ad1605449022e5eb98b60dbe2552308e9c55`, 3,569,254,754 bytes (recorded-safe step27).

All returned SHA256 values match their object names. No deletion or restore was
performed. This authenticates the retained archive bytes but does not resolve
later missing updates or authorize old-checkpoint resume. Next action is a
metadata-preserving cleanup dry run: candidates must be older state objects bound
to this plan by valid indexes/receipts; protect every newer/unknown reference, all
receipt objects, the three verified objects and all exported bundles.

## Cleanup manifest review

Reviewed canonical JSON SHA256:
`0b0fbf80752d486f694e239311961aedc1c4a4814656d7242853d46e7e302ac5`.
Recomputed all index and verified-receipt hashes, object references and eligibility.
All 235 candidates are exclusively old state archives before retained step27,
bound to the exact plan by valid indexes/receipts. No protected reference intersects.
Candidates total 360,703,851,680 bytes (335.9316 GiB); deleting only these leaves
245 object files / 9.9724 GiB, plus unchanged exports and metadata. All three
verified archives, every receipt/index, newer/unknown objects and bundles are kept.
Only a dry-run manifest has been reviewed locally; remote deletion remains
unexecuted/unverified. Cleanup must preserve an audit manifest and deletion journal,
check unchanged remote inventory before mutation, and leave latest incomplete
snapshots untouched. It does not authorize recovery or replay.

## Returned cleanup execution result

The user reports successful execution of the reviewed manifest:
235 objects removed, 360,703,851,680 bytes (335.93 GiB); 245 objects remain
(9.97 GiB). All three retained archives remain present. No snapshot directories
or exported bundles were deleted. The cell checked the unchanged pre-deletion
inventory, preserved the manifest/deletion journal, and checked the final inventory
against exactly the reviewed deletion set. This is returned Colab evidence, not
a fresh local inspection of Drive or proof of account-quota refresh.

Durable audit directory:
`/content/drive/MyDrive/PACT/revival/pact-heterogeneous-receiver-training-001/cleanup-audit/0b0fbf80752d486f694e239311961aedc1c4a4814656d7242853d46e7e302ac5`.

`resume_authorized` remains false. Deliberately pruned old snapshot references are
documented in that manifest and must not be confused with the pre-existing missing
latest archives. Latest incomplete directories remain intact so cleanup cannot
silently promote an older safe checkpoint. The storage implementation is not yet
corrected; no training, rollback, plan migration or new run was performed.

## Subsequent local engineering correction

Implemented `revival_files_v1` member-addressed persistence with a 32 GiB object
admission limit, verified pending marker and fail-closed latest-only restore.
Explicit recovery exports stay ZIPs. No automatic pruning or legacy migration.
29 revival tests passed, three optional neural classes skipped; five storage and
five artifact tests passed. GPU/Drive performance remains unverified. This local
patch does not resolve the missing later execution history or authorize step28
resume; changing tensor history can still reach the new capacity stop. Details:
[storage correction](../revival_storage_recovery.md).

## Reviewed separate replacement implementation

After the user reviewed the replacement proposal, a separate child runner was
implemented and CPU-tested. It reuses the exact completed scratch-era bank and
original initialization; no step28 weights, missing later state or historical
journal identity is rewritten. Original incident recovery remains blocked.
The new attempt has its own ID, source pin and additional budget; pending historical
compute stays unknown. See [replacement plan](../revival_replacement_plan.md) and
[Colab sequence](../revival_replacement_colab.md). Final CPU evidence is 57 revival
plus ten storage/artifact tests passed; GPU/Drive behavior remains unverified.
