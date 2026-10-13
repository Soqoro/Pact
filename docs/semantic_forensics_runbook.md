# Local semantic review workflow

No GPU, tokenizer, dataset download or API call is needed. Run from the repository. Private evidence must live outside **every** Git worktree; on this workstation `/tmp` is itself in a Git tree, so use `/var/tmp`. Use the existing final derivative from the audit for review; the import sequence below is for a new absent directory. Do not edit its `parent/` or reuse a partially failed import directory.

```bash
export PYTHONPATH="$PWD/src"
PACT_REVIEW_ROOT=/var/tmp/pact-semantic-review-20261014
PACT_PARENT_ZIP="$PWD/pact-adjudication-diagnostic-001-PRIVATE-1791903639856421059.zip"

python -m pact adjudication-forensics import-parent --run-dir "$PACT_REVIEW_ROOT" \
  --bundle "$PACT_PARENT_ZIP" \
  --sha256 2abda348768e65ec8289f51eee48f8f5653ee0b36d30aff8c9093a7dc9c2ae8f
python -m pact adjudication-forensics census --run-dir "$PACT_REVIEW_ROOT"
python -m pact adjudication-forensics sample-review --run-dir "$PACT_REVIEW_ROOT"
python -m pact adjudication-forensics report --run-dir "$PACT_REVIEW_ROOT"
```

Choose exactly two distinct reviewer identifiers. They should review separately; neither receives the other's first-pass labels. Generating blank templates does not assert that a person has reviewed anything.

```bash
python -m pact adjudication-forensics export-review --run-dir "$PACT_REVIEW_ROOT" --reviewer reviewer-1 --origin human --pass 1
python -m pact adjudication-forensics export-review --run-dir "$PACT_REVIEW_ROOT" --reviewer reviewer-2 --origin human --pass 1
python - <<'PY'
from pathlib import Path
from pact.studies.semantic_review import reviewer_key
root=Path('/var/tmp/pact-semantic-review-20261014')
for who in ('reviewer-1','reviewer-2'):
    print(who, root/'reviewers'/reviewer_key(who)/'pass1')
PY
```

Give each reviewer only their `pass1` directory (`casebook.html`, `casebook.md`, `annotations.template.jsonl`). Keep the sibling identity/mapping and analyst manifests private from reviewers. Copy the JSONL template to a separate returned file; do not edit generated artifacts. Unavailable cases stay `not_reviewed`. For available cases:

- Fill every categorical field using the enums in `semantic_review.FIELDS`; `text_a_*` and `text_b_*` refer to the displayed text. Added/removed premises mean **B relative to A**.
- Declare `independent` and `outcome_blinded` truthfully, `status="reviewed"`, actual `review_confidence`, qualifications and references. Claims needing unverified outside facts remain uncertain.
- `lock=false` saves an unfinished version; `lock=true` permanently locks that review. Lock all available units before outcomes are revealed.
- Evidence spans use `{side:"A"|"B", span:{start,end,text,source_hash}}`. Offsets are Unicode code points. `source_hash` is `pact.util.digest` of that exact displayed string, not the file hash. Span validation does not establish the claim's truth.
- An optional `edit_proposal` has `side`, `cue`, `sham` plus boolean `unsupported_isolated_cue`, `redundant_noncue_sham`, `no_task_content_removed`, `no_answer_removed`, `both_coherent`, `no_other_cue_removed`. It applies only to the text containing the proposed unsupported cue, without needing the hidden source direction. Never invent a span/control. Otherwise leave it null and record `edit_ineligibility` (`no_isolated_cue`, `no_adequate_sham`, `substantive_edit_required`, `review_disputed`, or null).

Import real returned files (paths below are placeholders for those files):

```bash
python -m pact adjudication-forensics import-annotations --run-dir "$PACT_REVIEW_ROOT" --reviewer reviewer-1 --pass 1 --file /var/tmp/reviewer-1-returned.jsonl
python -m pact adjudication-forensics import-annotations --run-dir "$PACT_REVIEW_ROOT" --reviewer reviewer-2 --pass 1 --file /var/tmp/reviewer-2-returned.jsonl
python -m pact adjudication-forensics agreement --run-dir "$PACT_REVIEW_ROOT"
python -m pact adjudication-forensics export-review --run-dir "$PACT_REVIEW_ROOT" --reviewer reviewer-1 --origin human --pass 2
python -m pact adjudication-forensics export-review --run-dir "$PACT_REVIEW_ROOT" --reviewer reviewer-2 --origin human --pass 2
```

Pass2 templates require `observations` and `hypotheses` separately. Keep the bound `first_pass_hash`; set status reviewed only after actual review. Import with the same command and `--pass 2`. Do not quote unsaved reasoning.

An optional third reviewer can submit JSONL resolutions using `adjudicate --reviewer third-person --file ...`. Each row requires `case_id`, `field`, `adjudicator`, `origin="human"`, `label` (field enum or disputed/unknown), `reason`, and `review_hashes`: reviewer-ID → `digest(review_state(root,id)[case_id])` for both original reviewers. Resolutions append; they do not overwrite first-pass labels or supply missing edit approvals.

```bash
python -m pact adjudication-forensics report --run-dir "$PACT_REVIEW_ROOT"
python -m pact adjudication-forensics export --run-dir "$PACT_REVIEW_ROOT"
```

Back up the PRIVATE ZIP outside Git (e.g. private Drive folder). Keep the matching SANITIZED ZIP and both printed hashes. The reviewed private bundle is the Colab prerequisite. Do not prepare the real span child with incomplete reviews: it freezes its source copy. With no valid cue/sham pairs, stop as not testable. No completed review or favorable statistic automatically authorizes inference.

## Fictional contract example

Suppose a fictional task has official answer B, independent judge answer A, and valid candidates B/A/A. Then `T=0,O=1`; a peer answer B is a rescue. A different task with independent B but candidates A/A/C has `T=1,O=0`: a constrained selector cannot retain the independent correct answer, whereas free synthesis can.

For an explicitly fictional reviewed source:

```python
from pact.util import digest
from pact.studies.rationale_spans import deletions
source = "The claim follows. Everyone agrees. In brief."
cue = {"start":19,"end":35,"text":"Everyone agrees.","source_hash":digest(source)}
sham = {"start":36,"end":45,"text":"In brief.","source_hash":digest(source)}
# Compute offsets from the actual string when entering a real review; no normalization.
# This example illustrates validation only, not human eligibility or tokenizer approval.
print(deletions(source, cue, sham))
```

The three exact strings are `The claim follows. Everyone agrees. In brief.`,
`The claim follows.  In brief.`, and `The claim follows. Everyone agrees. `.
The double space and trailing space are retained. A blank blinded review presents
this pair as randomized A/B; it does not assign a semantic label from the shared answer.

Use `source.index(...)` and `start+len(exact_text)` to avoid copying incorrect offsets; the validator rejects mismatches. Cue and sham produce different exact bytes but leave the task, options, answers, ordering and other candidates unchanged. All three requests use the same parent seed for a judge/mode, yet distinct child version/plan keys. The fictional fixture test executes all three; real execution remains gated.

## Optional child, after review

Use [the exact Colab sequence](rationale_spans_colab.md) and [notebook 21](../notebooks/21_rationale_spans_colab.ipynb). It imports the reviewed private bundle, prepares/validates edits, explicitly preflights native tokenizers, freezes a plan, and exports a review bundle **before** asking for a separate user authorization JSON. The template binds all artifacts and starts `approved=false`; do not have code turn it into approval.

Once the user decides, their file supplies `approved=true`, `origin="user"`, `approved_by`, and a `decision_reference`, retaining all template hashes/budgets exactly. Authorization is an auditable user assertion, not a cryptographic signature. Run only the intended smoke/judge cell; each invocation persists and exports. Restore only the safe latest compact snapshot after a reset, with the same code/runtime; any mismatch or ambiguous dispatch stops rather than retrying.

Return `pact-rationale-span-intervention-001-PRIVATE-<timestamp>.zip` and `...-SANITIZED-<same timestamp>.zip`, with both SHA256 values. The private bundle includes frozen review/source evidence, edits, tokenizer/model receipts, approval, plan, intents/results/resources and per-task outcomes. The sanitized bundle contains aggregate outcomes/provenance only. No API key, adapter checkpoint, task selection file or new benchmark download is needed.
