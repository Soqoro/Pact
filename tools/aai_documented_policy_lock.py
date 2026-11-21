"""Lock the 30 completed actor checkpoints on CPU at the verified fit-30 boundary."""
import json
import os
import shutil
from pathlib import Path

import aai_documented_remaining_batch as b
import aai_documented_training_batch as training

RECOVERY = 'df931386f5eea557edb1f60f923b74df3c863f1fe680aca317ce3bf41255dc47'
SCOPE = {'stage': 'policy-lock'}


def expected_lock(root, plan, allocation):
    from pact.revival.stage1.weights import tensor_inventory

    hashes = {'S0': {}}
    teams = {'S0': dict.fromkeys('QLM', 'S0')}
    for family in 'QLM':
        _, inventory = tensor_inventory(Path(plan['parent_path']), 'uniform_joint_sft/' + family)
        hashes['S0'][family] = inventory['adapter_hash']
    b.require(hashes['S0'] == plan['s0'] == b.S0, 'S0_changed')
    for policy, seed, family, schedule in training.jobs(allocation, plan):
        team = f'{policy}/{seed}'
        path = root/'continuations'/team/family
        _, receipt = training.checkpoint(path, policy, seed, family, schedule)
        teams.setdefault(team, {})[family] = str(path)
        hashes.setdefault(team, {})[family] = receipt['adapter_hash_recorded']
    return {'teams': teams, 'adapter_hashes': hashes, 'aliases': allocation['aliases'],
            'analysis': plan['analysis'], 'prospective_hash': plan['prospective_hash'],
            'policies_hash': b.digest(allocation)}


def check_evaluation_absent(root):
    for name in ('policy_outcomes.private.json', 'policy_results.json',
                 'stages/evaluation-smoke.json', 'stages/evaluate.json'):
        b.require(not (root/name).exists(), 'evaluation_artifact_present')
    b.require(not any((root/'attacks/policy').glob('*.json')), 'policy_attack_present')


def lock(root, persistent):
    from pact.revival.documented_execution import guard, plan as planning
    from pact.revival.allocation_v3 import runner, storage
    from pact.studies.heterogeneity import immutable

    plan = planning.validate(root, b.PLAN)
    audit = persistent/'policy-lock-only-v1'
    b.require(not audit.exists() and not any((root/name).exists() for name in
              ('policy-lock.json', 'policy-lock-receipt.json', 'exports/policy-lock.json')),
              'lock_already_started')
    check_evaluation_absent(root)
    training.durable(persistent)
    print('Verifying the fit-30 recovery archive against scratch...', flush=True)
    b.archive(persistent/'bundles'/f'{b.RUN}-RECOVERY-1795225395414402843.zip', RECOVERY, root)
    summary = b.read(root/'summary.json')
    training.accounting(summary, summary, 2880)
    before = b.events(root)
    b.require(len(before) == 12834, 'fit30_ledger')
    b.require(b.sha(root/'policies.json') == training.POLICY_SHA, 'allocation_changed')
    expected = expected_lock(root, plan, b.read(root/'policies.json'))
    # Export retains the three new local ZIPs and builds snapshot metadata on scratch.
    last_export_bytes = 143181471 + 7590388634 + 8730
    b.require(shutil.disk_usage(root).free >= last_export_bytes + 1024**3,
              'insufficient_scratch_for_fit30_sized_export')
    audit.mkdir(mode=0o700)
    approval = {'version': 'documented_stage2_stage_approval_v1', 'run_id': b.RUN,
                'plan_hash': b.PLAN, 'freeze': plan['freeze'], 'fixture': False,
                'scope': SCOPE, 'limits': plan['budgets'], 'historical_spending': None,
                'historical_budget_reset': False, 'source_code': plan['source_code'],
                'preflight_sha256': b.PREFLIGHT, 'execution_approved': True,
                'spending_approved': True, 'user_decision':
                'User approved the CPU checkpoint lock after job 1124778. '
                'Zero physical model operations. Export and stop for evaluation review.'}
    ap = audit/'approval.json'
    approval_sha = b.save(ap, approval)
    guard.authorize(root, plan, SCOPE, ap, approval_sha, persistent)
    guard.record(root, SCOPE, approval_sha)
    storage.Wallet(root, plan, persistent)
    # The generic report hook starts prospective outcome analysis when a lock exists.
    result = runner.lock_policies(root, plan)
    b.require(result['locked_teams'] == 11 and b.read(root/'policy-lock.json') == expected,
              'checkpoint_lock_mismatch')
    lock_sha = b.sha(root/'policy-lock.json')
    immutable(root/'policy-lock-receipt.json', {'sha256': lock_sha})
    check_evaluation_absent(root)
    b.require(b.events(root) == before and b.read(root/'summary.json') == summary, 'ledger_changed')
    bundles = storage.export(root, 'policy-lock', persistent)
    b.require(set(bundles) == {'PRIVATE', 'RECOVERY', 'SANITIZED'}, 'bundle_set')
    for info in bundles.values():
        b.archive(persistent/'bundles'/Path(info['path']).name, info['sha256'], root)
    training.durable(persistent)
    final = {'status': 'POLICY_CHECKPOINT_LOCK_VERIFIED', 'plan_hash': b.PLAN,
             'lock_sha256': lock_sha, 'trained_adapter_hashes_verified': 30,
             'S0_adapters_verified': 3, 'locked_teams': 11, 'prior_events_verified': len(before),
             'new_generations': 0, 'new_scores': 0, 'new_updates': 0, 'new_training_forwards': 0,
             'evaluation_authorized': False, 'bundles': bundles}
    b.save(audit/'summary.sanitized.json', final)
    print(json.dumps(final), flush=True)


def main():
    from pact.artifacts import run_lock
    from pact.revival.gpqa_source.sources import private_path

    root = Path(os.environ['PACT_LOCAL'])/'runs'/b.RUN
    persistent = Path('/dataset')/os.environ['USER']/'PACT/stage2-documented-step77-recovery-v1'/b.RUN
    for path in (root, persistent):
        private_path(path)
        b.require(path.is_dir(), 'missing_existing_run')
    with run_lock(root):
        lock(root, persistent)


if __name__ == '__main__':
    main()
