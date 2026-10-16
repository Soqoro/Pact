# Selector contract child: four-call GPU smoke audit

Return pair `1792068326092771454` passed local offline verification. The two
prespecified development tasks each have one clean view, evaluated under both
fresh arms. This is an included smoke, not a new cohort or completed study.

| Arm | Valid responses | Strict correct | Deployed correct | Rescue / harm | Fallbacks |
|---|---:|---:|---:|---:|---:|
| Fresh legacy prompt | 0/2 | 0/2 | 1/2 | 0 / 0 | 2 |
| Selector contract v2 | 2/2 | 2/2 | 2/2 | 1 / 0 | 0 |

V2 intentionally retains the correct ARC anchor and selects a correct peer on the
wrong-anchor LogiQA task. Both legacy responses fail the original key contract and
use unchanged anchor fallback. No output is salvaged. Two task groups cannot
establish general efficacy, risk, or a universal cause of the historical formatting
failure. There are no attack views in this smoke; robustness remains unmeasured.
The completed parent's 202 malformed outputs and KEEP_ONLY result stay unchanged.

## Artifact and execution evidence

- PRIVATE SHA256: `06c502d0f8d65d04269f54430f1e99f4cf3214eb3051d969f93bf86c304a3ead`.
- SANITIZED SHA256: `e41c1d8e2123537eebef70a7c455d81dc048b56ed8fb2be66ac9c457f7c6c7f3`.
- Clean source commit: `58e7bf3e6ed7b9defdc231298133b4a1b2dd6c8e`.
- Frozen child plan: `d704f2c4e10ed509547773cbabecd214890a23d8f69004ba2cbdb6d9d958d09f`.
- Four attempts/commits, zero unresolved; 2,048 reserved output tokens,
  2,345 actual input tokens and 419 actual output tokens. Two fresh legacy calls.
- Zero fits, LLM updates, teacher-forced forwards or new source/checker/rewrite calls.
- Recovery safe; all four exact frozen smoke keys present. 400 planned calls remain
  within the unchanged 404-call / 206,848-token ceiling.

The returned identity verifies pristine parent-matching J8 weight files, tokenizer,
template, BF16/SDPA and absent adapters. User-reported accelerator is NVIDIA L4.
The archived CPU-to-GPU preflight transition records zero preceding attempts and
no loaded-model identity. Old/new metadata match except runtime fingerprint; the
loaded identity matches the new fingerprint. This is an explicit pre-dispatch
runtime correction, not a precision/model/prompt migration after observations.

## Local audit

Both supplied ZIP hashes and trusted internal archive checks passed. Imported
parent files match their immutable receipt. All 404 planned prompts reproduce the
frozen renderer, legacy requests match parent requests exactly under canonical
serialization, and corresponding seeds and parent result hashes match. Actual
call identities, native token/accounting checks and loaded weight identity passed.
Reconstructed private report equals both the saved private and sanitized reports.
Sanitized content excludes selected task IDs/questions and decodable token arrays.

Private derivative and audit receipt:
`/var/tmp/pact-selector-smoke-1792068326092771454/local_smoke_audit.json`.
No imported script was executed. Local work performed zero generation/fitting and
made no implementation, dependency, commit or push changes. Artifact reconstruction
was executed; the unit suite was not rerun for this documentation-only audit.

## Disposition

The technical smoke is verified on the returned environment. Full-study behavior
remains unverified. The next existing stage is separately invoked continuation of
all 400 remaining requests on the same pinned source, model/runtime and plan.
It reuses the four committed smoke calls; there is no prompt tuning, task
replacement or favorable-outcome gate. No new study, policy, transfer or deferred
human/span review is authorized by these results.
