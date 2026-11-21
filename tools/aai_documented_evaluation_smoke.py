"""Run and verify the two frozen policy smoke tasks with the pinned execution adapter."""
import json
import os
import shutil
import subprocess
from pathlib import Path

import aai_documented_remaining_batch as b
import aai_documented_training_batch as training
from aai_documented_policy_lock import check_evaluation_absent

LOCK = '50f2aaa21f9716eb2b85999a9b5045ab9c1a6be1ec703c4944c3da27d74fa387'
RECOVERY = '9fc6268f6d44f28f92ec2c3fbf306606d8b96f650258040847a6615ef6d342b5'
STAGE = 'evaluation-smoke'


def smoke_nodes(root, plan):
    graph = b.read(root/'sealed/graph.private.json')
    b.require(b.digest(graph) == plan['freeze']['graph_digest'], 'graph_digest')
    ids = set(graph['smoke_manifest']['policy'])
    nodes = [n for n in graph['nodes'] if n['id'] in ids]
    b.require(len(nodes) == len(ids) == 244, 'smoke_graph_size')
    b.require(all(n['kind'] == 'generation' and n['part'] == 'policy'
                  and n['reserved_output_tokens'] == 512 for n in nodes), 'smoke_graph_budget')
    tasks = {n['task_id'] for n in nodes}
    candidate = root/'sealed/prospective.private.json'
    b.require(b.sha(candidate) == plan['prospective_hash'], 'cohort_changed')
    rows = [r for r in b.read(candidate)['records'] if r['task']['task_id'] in tasks]
    b.require(len(tasks) == len(rows) == 2 and
              {r['family'] for r in rows} == {'gpqa_main', 'logiqa'}, 'source_coverage')
    return nodes


def event_key(intent):
    identity = intent['identity']
    b.require(identity['plan_hash'] == b.PLAN and identity['owner'] == b.RUN and
              identity['kind'] == 'generation' and identity['part'] == 'policy' and
              intent['cost'] == {'generation': 1}, 'operation_outside_smoke')
    dep = identity['dependency']
    req = dep['request']
    role, *scope = dep['scope']
    tid = req['task']['task_id']
    team = 'shared' if role == 'attack' else scope[0]
    phase = {'attack': 'private', 'private': 'private', 'revision': 'revision', 'readout': 'final'}[role]
    b.require(req['phase'] == phase and req['max_tokens'] == 512, 'request_contract')
    return team, tid, ('attack' if role == 'attack' else phase), dep['model']['spec']['key'], req['seed']


def verify_delta(root, nodes, before):
    after = b.events(root)
    b.require(all(after.get(k) == v for k, v in before.items()), 'previous_events_changed')
    tasks = {n['task_id'] for n in nodes}
    attacks = root/'attacks/policy'
    b.require({p.name for p in attacks.glob('*.json')} == {b.digest(t)+'.json' for t in tasks},
              'attack_inventory')
    accepted = {t: b.read(attacks/(b.digest(t)+'.json'))['accepted'] for t in tasks}
    b.require(all(type(v) is bool for v in accepted.values()), 'attack_disposition')
    expected = {(n['team'], n['task_id'], n['phase'], n['family'], n['seed']) for n in nodes
                if n['condition'] != 'exchange' or accepted[n['task_id']]}
    new = after.keys() - before.keys()
    observed = set()
    for k in new:
        intent = b.read(root/'attempts'/(k+'.json'))
        event = b.read(root/'events/shards'/(k+'.json'))
        b.require(b.digest(intent['identity']) == k and event['intent'] == intent, 'event_identity')
        observed.add(event_key(intent))
    b.require(len(new) == len(expected) == 156 + 44 * sum(accepted.values()) and
              observed == expected, 'smoke_graph_execution_mismatch')
    return len(new)


def main():
    local = Path(os.environ['PACT_LOCAL'])
    root = local/'runs'/b.RUN
    persistent = Path('/dataset')/os.environ['USER']/'PACT/stage2-documented-step77-recovery-v1'/b.RUN
    audit = persistent/'evaluation-smoke-only-v1'
    b.require(not audit.exists(), 'already_started_no_retry')
    plan = b.read(root/'plan.json')
    b.require(b.digest(plan) == b.PLAN and plan['fixture'] is False, 'plan_changed')
    b.require(b.sha(root/'policy-lock.json') == LOCK and
              b.read(root/'policy-lock-receipt.json')['sha256'] == LOCK, 'lock_changed')
    lock_receipt = b.read(persistent/'policy-lock-only-v1/summary.sanitized.json')
    b.require(lock_receipt['status'] == 'POLICY_CHECKPOINT_LOCK_VERIFIED' and
              lock_receipt['lock_sha256'] == LOCK, 'lock_receipt')
    check_evaluation_absent(root)
    training.durable(persistent)
    print('Checking the locked recovery archive and event ledger...', flush=True)
    b.archive(persistent/'bundles'/f'{b.RUN}-RECOVERY-1795242304579084512.zip', RECOVERY, root)
    before = b.events(root)
    original = b.read(root/'summary.json')
    training.accounting(original, original, 2880)
    b.require(len(before) == 12834, 'previous_event_count')
    nodes = smoke_nodes(root, plan)
    b.require(shutil.disk_usage(root).free >= sum(v['bytes'] for v in lock_receipt['bundles'].values())
              + 1024**3, 'scratch_export_capacity')
    audit.mkdir(mode=0o700)
    approval = {'version': 'documented_stage2_stage_approval_v1', 'run_id': b.RUN,
                'plan_hash': b.PLAN, 'scope': {'stage': STAGE}, 'freeze': plan['freeze'],
                'fixture': False, 'limits': plan['budgets'], 'source_code': plan['source_code'],
                'historical_spending': None, 'historical_budget_reset': False,
                'execution_approved': True, 'spending_approved': True, 'preflight_sha256': b.PREFLIGHT,
                'lock_sha256': LOCK, 'user_decision': 'User approved the two-task evaluation smoke '
                'on this checkpoint lock. Up to 244 generations and 124928 reserved output tokens. '
                'Zero updates, training forwards or diagnostic scores. Export and stop.'}
    ap = audit/'approval.json'
    config = {'stage': STAGE, 'approval': str(ap), 'approval_sha256': b.save(ap, approval),
              'run_dir': str(root), 'plan_hash': b.PLAN, 'persistent': str(persistent),
              'cache_dir': str(local/'cache')}
    cp = audit/'config.json'
    b.save(cp, config)
    log = local/'evaluation-smoke-only-v1.log'
    print('Starting the two-task smoke. Private log:', log, flush=True)
    with log.open('x') as stream:
        subprocess.run(['bash', str(Path(os.environ['PACT_CHECKOUT'])/'tools/aai_documented_execution.sbatch')],
                       env=dict(os.environ, PACT_EXECUTION_CONFIG=str(cp)), stdout=stream,
                       stderr=subprocess.STDOUT, check=True)
    outputs = []
    for line in log.read_text().splitlines():
        try:
            value = json.loads(line)
        except ValueError:
            continue
        if isinstance(value, dict) and 'bundles' in value:
            outputs.append(value)
    b.require(len(outputs) == 1 and outputs[0]['stop_for_review'] is True, 'export_record')
    calls = verify_delta(root, nodes, before)
    summary = b.read(root/'summary.json')
    b.require(summary['physical_attempts'] == {**original['physical_attempts'], 'policy':
              {**original['physical_attempts']['policy'], 'generation': calls}} and
              summary['reserved_output_tokens'] == original['reserved_output_tokens'] + calls * 512 and
              summary['committed_operations'] == len(before) + calls and summary['unresolved'] == 0 and
              summary['recovery_safe'] is True, 'smoke_accounting')
    b.require(b.sha(root/'policy-lock.json') == LOCK and b.read(root/'stages/evaluation-smoke.json')['complete']
              is True and not (root/'stages/evaluate.json').exists(), 'final_stage')
    bundles = outputs[0]['bundles']
    b.require(set(bundles) == {'RECOVERY','PRIVATE','SANITIZED'}, 'export_inventory')
    for info in bundles.values():
        b.archive(persistent/'bundles'/Path(info['path']).name, info['sha256'], root)
    training.durable(persistent)
    final = {'status': 'EVALUATION_SMOKE_VERIFIED', 'plan_hash': b.PLAN, 'lock_sha256': LOCK,
             'new_generations': calls, 'new_reserved_output_tokens': calls*512, 'unresolved': 0,
             'new_training_forwards': 0, 'new_updates': 0, 'new_scores': 0,
             'sources': ['gpqa_main', 'logiqa'], 'teams': 11, 'full_evaluation_authorized': False,
             'bundles': bundles}
    b.save(audit/'summary.sanitized.json', final)
    print(json.dumps(final), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status': 'STOPPED_PRESERVE_EVIDENCE', 'exception_type': type(exc).__name__,
                          'check': str(exc) if isinstance(exc, b.CheckFailed) else None}), flush=True)
        raise SystemExit(1)
