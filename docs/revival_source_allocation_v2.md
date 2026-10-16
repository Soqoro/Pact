# Source allocation revision: ARC 400 / LogiQA 560

The user authorized this revision after the original equal-source preparation
returned `source_shortfall`: ARC 74, LogiQA 0, model calls 0. Reported artifact
SHA256: `1f5efc04088adb0c273018f908bb2988eba3486269b9fbf49a2c04a923b451cc`.
This is user-returned Colab evidence; the raw file has not been independently
imported here. It establishes 406 eligible ARC groups and at least 480 LogiQA
for the old contract, not availability of 560 LogiQA groups.

The new contract is `arc400_logiqa560_v2` / `heterogeneous_dense_pact_v2`:

| Split | ARC | LogiQA | Total |
|---|---:|---:|---:|
| Main fitting | 192 | 320 | 512 |
| Allocation probes | 24 | 40 | 64 |
| Validation | 64 | 64 | 128 |
| Source evaluation | 120 | 136 | 256 |
| Total | 400 | 560 | 960 |

Three ARC and five LogiQA homogeneous blocks each contain 64 fitting and eight
probe groups. This preserves eight blocks, 24 temporary branches, per-branch
steps and every forward/call budget. Validation remains balanced for the existing
32-per-source peer-use diagnostic. The whole study is no longer equally sourced;
pooled metrics describe the declared split mixture, not equal-source performance.
The original specifications are historical v1; this addendum supersedes only
their equal quotas and four-blocks-per-source requirements.

All exclusions, official source revisions, seed, task ordering, protocols,
training targets and model identities remain unchanged. No previous exposure is
released. The existing reviewed exposure inventory remains valid because this
change allocates no new groups and does not advance the exposure ledger.

Preparation must independently establish availability of 400 ARC and 560 LogiQA.
Any shortage returns required/available counts and stops without a plan or calls.
No automatic reduction, substitution or repeat sampling. Use a fresh
`source-v2.private.json`; preserve the original shortfall JSON. Never overwrite
or migrate an existing v1 frozen plan. The run ID can be used for v2 only if no
plan was created (as in the reported source-only failure).

No real model run or scientific outcome is claimed. Push the reviewed changes,
pin the new commit in Colab, rerun source preparation on CPU, and return its
status before requesting the included six-call smoke.

## Local validation

Executed `PYTHONPATH=src /home/gnoriq/miniconda3/envs/gmats/bin/python
-m unittest discover -s tests -p test_revival.py -v`: **23 tests passed in
90.221 seconds**. This includes the full six-adapter/24-branch mock round trip,
source quota/config agreement, three/five block coverage, missing-source stopping
and rejection of v1 source and plan contracts. Log:
`/tmp/pact-revival-allocation-v2-final.log`. An initial test fixture omitted the
required validation pool; that fixture was corrected before this passing run.

Design arithmetic, notebook syntax, Python compilation, existing exposure
inventory freshness and `git diff --check` passed. No official data/model downloads
or GPU runs occurred locally. Full real-data eligibility remains unverified.
