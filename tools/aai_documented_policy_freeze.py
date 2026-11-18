"""CPU-only, score-bound policy freeze; no continuation or evaluation dispatch."""
import json
import os
from pathlib import Path
import shutil

import aai_documented_remaining_batch as b
import aai_documented_score as scoring

SCORED_SHA = '33f170101b18d949054597fd8055a2072408080b9611f84d26b328ccc272f87d'


def unchanged_accounting(before, after):
    for key in ('physical_attempts', 'committed_operations', 'unresolved',
                'reserved_output_tokens', 'input_tokens', 'output_tokens',
                'format_status_counts', 'historical_spending', 'remaining_historical_budget'):
        b.require(before[key] == after[key], 'physical_or_historical_accounting_changed')
    b.require(after['recovery_safe'] is True, 'unsafe_boundary')


def check_allocation(value):
    from pact.revival.allocation_v3 import design as d
    b.require(set(value['matrices']) == set(d.POLICIES), 'policy_inventory')
    b.require(value['primary'] == 'terminal_block', 'primary_changed')
    for matrix in value['matrices'].values():
        b.require(len(matrix) == 8 and all(len(row) == 3 and sum(row) == 12
                  and all(type(n) is int and n >= 0 for n in row) for row in matrix), 'quota_contract')
    b.require(value['matrices']['uniform'] == [[4,4,4]]*8, 'uniform_changed')
    b.require(set(value['plans']) == {f'{p}/{s}' for p in d.POLICIES for s in d.SEEDS}, 'plan_inventory')
    for key, plan in value['plans'].items():
        b.require(plan['s0'] == b.S0, 'starting_checkpoint_changed')
        b.require(sum(len(v) for v in plan['schedule'].values()) == 288, 'update_schedule')
        b.require(value['plans'][value['aliases'][key]] == plan, 'alias_contract')


def main():
    from pact.revival.documented_execution import runner
    from pact.revival.allocation_v3 import design as d
    local=Path(os.environ['PACT_LOCAL']);root=local/'runs'/b.RUN
    persistent=Path('/dataset')/os.environ['USER']/'PACT/stage2-documented-execution-export-fixed-v1'/b.RUN
    audit=persistent/'policy-freeze-only-v1';work=local/'policy-freeze-only-v1'
    b.require(not audit.exists() and not work.exists(), 'already_started_no_automatic_retry')
    plan=b.read(root/'plan.json')
    b.require(b.digest(plan)==b.PLAN and plan['fixture'] is False, 'plan_binding')
    b.require(b.sha(root/'execution-preflight.json')==b.PREFLIGHT, 'preflight_changed')
    b.archive(persistent/'bundles'/f'{b.RUN}-PRIVATE-1794925020673122069.zip',SCORED_SHA,root)
    before=b.events(root);original=b.read(root/'summary.json')
    b.require(len(before)==9954 and original['physical_attempts']['assay']==
              dict(generation=7320,scores=2442,training_forwards=1536,updates=192), 'scored_boundary')
    b.require(original['unresolved']==0 and original['recovery_safe'] is True, 'unsafe_boundary')
    b.require(all(v==0 for v in original['physical_attempts']['policy'].values()), 'policy_spending')
    b.require(b.read(root/'stages/score.json')['complete'] is True, 'score_incomplete')
    completed=b.COMPLETED+b.REMAINING
    for block,family in completed:b.checkpoint(root,plan,block,family)
    protected=b.protected_inventory(root,completed)
    expected=scoring.score_keys(root,plan)
    score_events={k for k in before if b.read(root/'events/shards'/f'{k}.json')['intent']['identity']['kind']=='score'}
    pristine=b.read(Path(plan['parent_path'])/'inference_identity_manifest.json')['models']['R']['pristine_identity']
    scoring.verify_score_delta(root,{k:v for k,v in before.items() if k not in score_events},before,expected,pristine)
    for name in ('policies.json','credits.private.json','policy-lock.json','policy-freeze-receipt.json'):
        b.require(not (root/name).exists(), 'already_frozen_or_later_work')
    b.require(not any(p.is_file() for p in (root/'continuations').rglob('*')), 'continuation_work')
    audit.mkdir(mode=0o700);work.mkdir(mode=0o700)
    approval={'version':'documented_stage2_stage_approval_v1','run_id':b.RUN,'plan_hash':b.PLAN,
        'freeze':plan['freeze'],'fixture':False,'scope':{'stage':'policy-freeze'},'limits':plan['budgets'],
        'historical_spending':None,'historical_budget_reset':False,'source_code':plan['source_code'],
        'preflight_sha256':b.PREFLIGHT,'execution_approved':True,'spending_approved':True,
        'user_decision':'User replied proceed after scored assay review: freeze the five predeclared allocation policies on CPU, export and stop. Zero new generations, scoring forwards, training forwards or optimizer updates. No continuation, evaluation or historical budget reset. spending_approved is the legacy non-preflight guard field and applies only to this zero-physical-work scope.'}
    ap=work/'approval.json';ah=b.save(ap,approval);shutil.copy2(ap,audit/ap.name)
    out=runner.execute(root,b.PLAN,{'stage':'policy-freeze'},ap,ah,persistent=persistent)
    b.require(b.events(root)==before, 'events_changed')
    unchanged_accounting(original,b.read(root/'summary.json'))
    current=b.protected_inventory(root,completed)
    b.require(all(current.get(k)==v for k,v in protected.items()), 'prior_artifacts_changed')
    allocation=b.read(root/'policies.json');check_allocation(allocation)
    scores={tuple(v['logical']):v for p in (root/'scores').glob('*.json') if (v:=b.read(p))}
    accepted={t:b.read(root/'attacks/assay'/f'{b.digest(t)}.json')['accepted'] for ids in plan['probes'].values() for t in ids}
    credits=d.credits(scores,plan['blocks'],plan['probes'],accepted)
    expected_policy=d.compile_policies(plan['blocks'],credits['terminal'],credits['private_bank'],plan['shuffle'],plan['s0'],
        {'native':plan['native_contract_hashes'],'source_code':plan['source_code'],'plan_hash':b.PLAN})
    b.require(allocation==expected_policy, 'compiler_mismatch')
    b.require(b.read(root/'policy-freeze-receipt.json')['sha256']==b.sha(root/'policies.json'), 'freeze_receipt')
    b.require(not (root/'policy-lock.json').exists() and not any(p.is_file() for p in (root/'continuations').rglob('*')), 'later_work')
    for info in out['bundles'].values():b.archive(persistent/'bundles'/Path(info['path']).name,info['sha256'],root)
    b.require(set(out['bundles'])=={'PRIVATE','SANITIZED','RECOVERY'}, 'exports')
    b.require(not any((persistent/n).exists() for n in ('SNAPSHOT_PENDING.json','INFLIGHT.json')), 'pending_persistence')
    latest=sorted((persistent/'snapshots').iterdir())[-1]
    b.require((latest/'COMPLETE').read_text().strip()==b.sha(latest/'index.json'), 'snapshot_marker')
    files=b.read(latest/'index.json')['files']
    for h in set(files.values()):
        b.require(len(h)==64 and all(c in '0123456789abcdef' for c in h), 'object_address')
        b.require(b.sha(persistent/'objects'/h)==h, 'durable_object')
    receipt=b.read(persistent/'objects'/files['receipt.json'])
    b.require(receipt['safe'] is True and receipt['plan_hash']==b.PLAN, 'durable_receipt')
    final={'status':'POLICIES_FROZEN_NO_NEW_PHYSICAL_WORK','plan_hash':b.PLAN,
        'policies_sha256':b.sha(root/'policies.json'),'allocation':b.read(root/'allocation_summary.json'),
        'prior_9954_events_unchanged':True,'new_generations':0,'new_scores':0,'new_training_forwards':0,
        'new_optimizer_updates':0,'later_execution_authorized':False,'bundles':out['bundles']}
    b.save(audit/'summary.sanitized.json',final);print(json.dumps(final),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as error:
        print(json.dumps({'status':'POLICY_FREEZE_STOPPED_NO_AUTOMATIC_RETRY','exception_type':type(error).__name__,
                          'check':str(error) if isinstance(error,b.CheckFailed) else None}),flush=True)
        raise SystemExit(1)
