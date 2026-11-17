#!/bin/bash
#SBATCH --job-name=pact-branch-3-L
#SBATCH --partition=NA100q
#SBATCH --nodelist=node01
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --gres=gpu:1
#SBATCH --mem=96G
#SBATCH --time=12:00:00
#SBATCH --no-requeue
#SBATCH --output=pact-branch-3-L-%j.out
#SBATCH --error=pact-branch-3-L-%j.err

set -euo pipefail
trap 'printf "Stopped at line %s. Preserve evidence; no automatic retry.\n" "$LINENO" >&2' ERR
umask 077

export PACT_CHECKOUT="$HOME/pact-aai-preflight/checkouts/export-fix-93b89ce38be7"
export PACT_COMMIT="93b89ce38be743acd6a3aa38177237ce99a3eeeb"
export PACT_LOCAL="/local/pact-stage2-documented-export-fixed-$USER"
export PACT_EXECUTION_CONFIG="$HOME/pact-aai-preflight/documented-branch-3-L-v1.json"

test "$(git -C "$PACT_CHECKOUT" rev-parse HEAD)" = "$PACT_COMMIT"
test -z "$(git -C "$PACT_CHECKOUT" status --porcelain)"

python3 -u - <<'PY'
import hashlib
import json
import os
import zipfile
from pathlib import Path

def canonical(value):
    return json.dumps(
        value, sort_keys=True, ensure_ascii=True,
        separators=(",", ":"), allow_nan=False,
    )

def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def read(path):
    return json.loads(path.read_text())

def save(path, value):
    data = (canonical(value) + "\n").encode()
    if path.exists():
        assert path.read_bytes() == data, (
            "Existing approval/config differs; preserve it and stop."
        )
    else:
        with path.open("xb") as stream:
            stream.write(data)
    return hashlib.sha256(data).hexdigest()

run_id = "pact-stage2-documented-execution-001"
expected = "024f9ef5ffccb9f90bcebab2818971964943b2892aa7ed8e1932ef02e55659f9"
root = Path(os.environ["PACT_LOCAL"]) / "runs" / run_id
persistent = (
    Path("/dataset") / os.environ["USER"] / "PACT"
    / "stage2-documented-execution-export-fixed-v1" / run_id
)
base = Path.home() / "pact-aai-preflight"

assert (root / "plan.json").is_file(), (
    "Scratch missing. Stop for recovery; do not recreate the plan."
)
plan = read(root / "plan.json")
assert digest(plan) == expected
assert plan["fixture"] is False
assert plan["historical_spending"] is None
assert plan["scratch_root"] == str(root)

archive = persistent / "bundles" / (
    run_id + "-PRIVATE-1794839255854220824.zip"
)
archive_sha = "3f1ba6b32582f433cc011764d36d4ed441586e59555ff2e2b7f5cf01e4d3964d"
assert file_hash(archive) == archive_sha

# Verify that the reviewed post-M evidence remains unchanged.
with zipfile.ZipFile(archive) as z:
    names = z.namelist()
    assert len(names) == len(set(names))
    checks = json.loads(z.read("checksums.json"))
    assert set(names) == set(checks) | {"checksums.json", "HANDOFF.json"}
    for name, checksum in checks.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == checksum
        if name != ".lock":
            local = root / name
            assert local.is_file() and not local.is_symlink()
            assert file_hash(local) == checksum

summary = read(root / "summary.json")
assert summary["committed_operations"] == 2808
assert summary["unresolved"] == 0
assert summary["recovery_safe"] is True
assert summary["physical_attempts"]["assay"] == {
    "generation": 2728, "scores": 0,
    "training_forwards": 640, "updates": 80,
}
assert summary["physical_attempts"]["policy"] == {
    "generation": 0, "scores": 0, "training_forwards": 0, "updates": 0,
}
assert len(list((root / "attempts").glob("*.json"))) == 2808
assert len(list((root / "events/shards").glob("*.json"))) == 2808
assert len(list((root / "events/shards").glob("*.sha256"))) == 2808

for marker in ("SNAPSHOT_PENDING.json", "INFLIGHT.json"):
    assert not (persistent / marker).exists(), (
        "Unresolved durable boundary: " + marker
    )

expected_branches = {f"block-{b}-{f}" for b in (0, 1, 2) for f in "QLM"} | {"block-3-Q"}
assert {p.name for p in (root / "branches").iterdir()} == expected_branches
assert not (root / "branches/block-3-L").exists()

allowed_scopes = [
    {"stage": "preflight"},
    {"stage": "assay-smoke"},
    {"stage": "collect"},
] + [{"stage": "branch", "block": 0, "family": f} for f in "QLM"] + [{"stage": "branch", "block": 1, "family": f} for f in "QLM"] + [{"stage": "branch", "block": 2, "family": f} for f in "QLM"] + [{"stage": "branch", "block": 3, "family": "Q"}]

for path in (root / "approvals").glob("*.json"):
    assert read(path)["scope"] in allowed_scopes

for folder in ("continuations", "scores"):
    assert not any(p.is_file() for p in (root / folder).rglob("*"))

# Recheck all ten retained checkpoints and rollback records.
for completed_block, family in [(0, "Q"), (0, "L"), (0, "M"), (1, "Q"), (1, "L"), (1, "M"), (2, "Q"), (2, "L"), (2, "M"), (3, "Q")]:
    branch = root / "branches" / f"block-{completed_block}-{family}"
    status = read(branch / "status.json")
    assert status["complete"] is True
    assert status["completed_steps"] == 8
    assert read(branch / "evaluated.json")["complete"] is True

    rollback = read(branch / "rollback.json")
    assert rollback["complete"] is True
    assert (
        rollback["initial_hash"]
        == rollback["restored_hash"]
        == plan["s0"][family]
    )

    checkpoint = branch / "checkpoints/step-000008"
    inventory = read(checkpoint / "checksums.json")
    assert set(inventory) == {"state.json", "tensors.safetensors"}
    for name, checksum in inventory.items():
        assert file_hash(checkpoint / name) == checksum

assert plan["s0"]["L"] == (
    "d1215a90f9a91967dfd22259d688352cb3e56c3090f3d290b45fb5e1a11fcb56"
)

block = plan["blocks"][3]
assert block["family"] == "logiqa"
order = sorted(
    block["fit"],
    key=lambda t: digest([20261027, "temporary", 17, 3, "L", t]),
)[:64]
assert len(order) == len(set(order)) == 64

records = {r["task"]["task_id"]: r for r in plan["training_source"]["records"]}
assert all(records[t]["split"] == "main_fit" for t in order)

probes = plan["probes"]["logiqa"]
assert len(probes) == len(set(probes)) == 40
assert not set(order) & set(probes)

accepted = 0
for task_id in probes:
    attack = read(root / "attacks/assay" / (digest(task_id) + ".json"))
    assert type(attack["accepted"]) is bool
    accepted += attack["accepted"]
assert accepted == 32
assert len(probes) + 4 * (len(probes) + accepted) == 328

preflight = root / "execution-preflight.json"
assert file_hash(preflight) == (
    "1e697a75aec6dd47fe2669235b1597f2010c85b05158f773c097880dd33ea8bb"
)

approval_path = base / "documented-branch-3-L-v1.approval.json"
approval = {
    "version": "documented_stage2_stage_approval_v1",
    "run_id": run_id,
    "plan_hash": expected,
    "freeze": plan["freeze"],
    "fixture": False,
    "scope": {"stage": "branch", "block": 3, "family": "L"},
    "limits": plan["budgets"],
    "historical_spending": None,
    "historical_budget_reset": False,
    "source_code": plan["source_code"],
    "preflight_sha256": file_hash(preflight),
    "user_decision": (
        "User replied approve to the explicit block-3/L proposal. "
        "Start independently from original L S0. Authorize only "
        "8 updates, 64 supervised forwards, at most 328 new generations "
        "and 167936 reserved output tokens. Require exact S0 rollback "
        "before saved-branch probe generation. Preserve all block-0 and block-1 Q/L/M and block-2/Q,L,M and block-3/Q "
        "evidence, packets and attacks. Zero diagnostic scoring. "
        "Export and stop; no other branch, policy, evaluation or "
        "historical budget reset."
    ),
    "execution_approved": True,
    "spending_approved": True,
}
approval_sha = save(approval_path, approval)

config = {
    "stage": "branch",
    "block": 3,
    "family": "L",
    "run_dir": str(root),
    "plan_hash": expected,
    "approval": str(approval_path),
    "approval_sha256": approval_sha,
    "cache_dir": str(Path(os.environ["PACT_LOCAL"]) / "cache"),
    "persistent": str(persistent),
}
save(Path(os.environ["PACT_EXECUTION_CONFIG"]), config)

print(json.dumps({
    "stage": "branch",
    "block": 3,
    "family": "L",
    "plan_hash": expected,
    "approval_sha256": approval_sha,
    "starting_generation_calls": 2728,
    "maximum_new_generations": 328,
    "maximum_new_reserved_tokens": 167936,
    "new_optimizer_updates": 8,
    "new_supervised_forwards": 64,
    "diagnostic_scoring_forwards": 0,
    "later_stages_authorized": False,
}, indent=2), flush=True)
PY

bash "$PACT_CHECKOUT/tools/aai_documented_execution.sbatch"

echo "BRANCH_3_L_COMPLETE. Return outputs for review; no next stage."
