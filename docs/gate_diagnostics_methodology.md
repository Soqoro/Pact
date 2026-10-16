# Saved gate diagnostics and prospective selector contract comparison

Implements the [15 October specification](PACT_Codex_Gate_Diagnostics_and_Selector_Repair.md).
The closed selective-correction parent remains unchanged: all five gates selected
KEEP_ONLY, with 44/64 development correctness and no switches. All 202 historical
selector outputs remain malformed. Neither diagnostic arithmetic nor a prompt
clarification constitutes learned PACT improvement.

`pact-gate-diagnostics-001` imports the exact PRIVATE return through the existing
bounded archive reader. It reconstructs original sources, rewrite pools, structured
checking responses, feature joins, saved fit transforms/weights, class order,
objective/gradient, tuning curves and development decisions. There are no optimizer
calls or model forwards. Scoped read caches are confined to immutable metadata;
parent byte inventories are compared before and after reconstruction. Required
missing evidence stops analysis explicitly.

Saved-score analysis uses harm/neutral/improve order. Utilities and log-odds are
independently checked; near-zero cancellation/underflow is reported rather than
changing the saved decision rule. Class mass retains tasks with no alternatives
in the objective denominator. The no-feature comparator normalizes observed fit
class mass without smoothing. Log reports alone clip probabilities at 1e-15;
Brier scores and policy decisions are unclipped. Weighted ROC gives half credit
to ties; AP processes a tied block together. Missing classes or fewer than two
distinct groups produce null rank metrics. Uncertainty is descriptive: 500
bootstrap draws, seed 20261015, whole tasks stratified by source. The NLL interval
summarizes task loss contributions, including zero-contribution no-alternative
tasks; it is not an independent calibration certificate.

Fit and tuning alone receive the prespecified four-cost / thirteen-threshold grid.
Every point retains the original masks, candidate max and ID ties; risk-rejected
points remain visible. No winner or replacement policy receipt is produced.
`gates.validate_model` explicitly rejects diagnostic artifacts. Development is
used only to reproduce existing decisions and the explicitly retrospective casebook.
Exact feature collisions do not establish representational impossibility. Model
assessment categories and host-resolved spans remain unverified hypotheses.

The PRIVATE dossier includes all clean fitting improvements, all tuning rescue
opportunities, all development rescue opportunities, and up to 22 hash-selected
harmful fitting groups. All saved views are separated, raw E/full/restricted
responses and host references retained, and mechanical overlapping pathway labels
are defined. HTML is escaped under a no-resource content policy. No human review,
semantic truth labels, external verification or model-written explanations are added.

`pact-anchor-selector-contract-002` is a separate inference-only child. It contains
exactly 202 parent views (64 clean, 138 accepted variants), with a fresh old-prompt
repeat and a v2 contract clarification on each. Only the ambiguous output passage
changes. Public validity determines candidate choices; task text, order, trust rules,
160-word explanation bound, strict parser and original-anchor fallback are identical.
The exact rendered prompt diff is private. Extra keys remain malformed in both
arms. ABSTAIN and formatting failures retain the parent fallback; missing calls
never become successful fallback. An invalid anchor remains invalid.

Corresponding seeds come from actual parent selector requests. Arm order and one
smoke task per dataset are hash-frozen with seed 20261015 before outcomes. Child
keys contain the child plan, arm, view, parent result and full request identity;
a parent cache entry cannot satisfy a new legacy call. Only exact committed child
calls can be reused. One pristine J8/Qwen3-8B is resident; real preflight and loading
check parent tokenizer/template/weight hashes, BF16/SDPA, absent adapters, greedy
non-thinking settings, 512 output tokens and the recipient's 8192 total-token cap.
The parent runtime may differ from the new runtime; the new runtime is frozen within
the child. No cross-runtime determinism claim is made.

Budget is 404 attempts / 206,848 reserved tokens, including at most 16 smoke calls
/ 8,192 tokens. Smoke exports and stops; continuation requires the included smoke
and its export receipt. Failure consumes its recorded intent and blocks automatic
retry; latest unsafe snapshots are never skipped. Compact verified snapshots and
separate private/sanitized exports reuse existing storage primitives. Reports can
be rebuilt as new calls finish; call shards and parent evidence remain immutable.

Paired outcome differences use tasks/groups with all views together. Strict schema,
strict correctness, intentional anchor selection, fallback contribution and deployed
correctness remain separate. Attack flips use each new arm's own clean output;
rephrase is separate. Missing views are explicit. Candidate-constrained results
must satisfy the anchor-plus-peer oracle and final=anchor+rescue−harm identities.
Historical free reconsideration and KEEP_ONLY remain historical controls only.

See [exact local/Colab commands](gate_diagnostics_colab.md) and
[offline findings](audits/PACT_GATE_DIAGNOSTICS_2026-10-15.md). The [completed child audit](audits/PACT_SELECTOR_CONTRACT_COMPLETE_2026-10-15.md)
records returned GPU evidence for the frozen comparison. Human/span review, transfer
and full PACT remain deferred. No
result authorizes another design or reallocates the already exposed 224 groups.
