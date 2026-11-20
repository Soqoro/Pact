"""Approved 30-fit continuation batch; frozen policies, no evaluation or retries."""
import argparse
import json
import zipfile
import os
from pathlib import Path
import shutil
import subprocess
import aai_documented_remaining_batch as b

POLICY_SHA='4a45e3ddfea573566fd31383b2530d14757640278060c30e143d25dd5b437896'
POLICIES=('terminal_block','uniform','source_family','private_bank','shuffled')
SEEDS=(113,227)


def jobs(allocation, plan):
    keys={f'{p}/{s}' for p in POLICIES for s in SEEDS}
    b.require(set(allocation['plans'])==keys and allocation['aliases']=={k:k for k in keys},'frozen_team_inventory')
    records={r['task']['task_id']:r for r in plan['training_source']['records']}
    probes={t for ids in plan['probes'].values() for t in ids}
    result=[]
    for policy in POLICIES:
        for seed in SEEDS:
            contract=allocation['plans'][f'{policy}/{seed}']
            b.require(contract['s0']==b.S0 and contract['seed']==seed,'starting_contract')
            b.require(set(contract['schedule'])==set('QLM'),'family_inventory')
            b.require(sum(len(v) for v in contract['schedule'].values())==288,'team_updates')
            for family in 'QLM':
                schedule=contract['schedule'][family]
                b.require(64<=len(schedule)<=160,'fit_limit')
                for entry in schedule:
                    tasks=entry['tasks']
                    b.require(len(tasks)==len(set(tasks))==8 and not set(tasks)&probes,'probe_training')
                    b.require(all(records[t]['split']=='main_fit' and t in plan['blocks'][entry['block']]['fit'] for t in tasks),'fit_source')
                result.append((policy,seed,family,schedule))
    b.require(len(result)==30 and sum(len(j[3]) for j in result)==2880,'batch_budget')
    return result


def accounting(value, original, updates):
    b.require(value['physical_attempts']['assay']==dict(generation=7320,scores=2442,training_forwards=1536,updates=192),'assay_changed')
    b.require(value['physical_attempts']['policy']==dict(generation=0,scores=0,training_forwards=updates*8,updates=updates),'policy_accounting')
    b.require(value['committed_operations']==9954+updates and value['unresolved']==0 and value['recovery_safe'] is True,'unsafe_accounting')
    for key in ('reserved_output_tokens','input_tokens','output_tokens','format_status_counts','historical_spending','remaining_historical_budget','stages'):
        b.require(value[key]==original[key],'generation_or_history_changed')


def delta(root,before,after,path,contract,schedule,offset=0):
    b.require(all(after.get(k)==v for k,v in before.items()),'prior_events_changed')
    new=set(after)-set(before);steps=[]
    b.require(len(new)==len(schedule)-offset,'update_count')
    for key in new:
        event=b.read(root/'events/shards'/f'{key}.json');intent=event['intent'];identity=intent['identity'];dep=identity['dependency']
        b.require(b.digest(identity)==key and b.read(root/'attempts'/f'{key}.json')==intent,'intent_identity')
        b.require(identity['owner']==b.RUN and identity['plan_hash']==b.PLAN and identity['part']=='policy' and identity['kind']=='update','unexpected_operation')
        b.require(intent['cost']=={'updates':1,'training_forwards':8},'update_cost')
        step=event['value']['step'];steps.append(step)
        b.require(type(step) is int and 1<=step<=len(schedule),'step')
        b.require(dep['path']==path.relative_to(root).as_posix() and dep['family']==contract['family'] and dep['contract']==b.digest(contract)
                  and dep['step']==step and dep['batch']==schedule[step-1],'update_contract')
    b.require(sorted(steps)==list(range(offset+1,len(schedule)+1)),'step_coverage')


def checkpoint(path,policy,seed,family,schedule):
    contract=b.read(path/'contract.json');status=b.read(path/'status.json')
    b.require(contract['family']==family and contract['seed']==seed and contract['part']=='policy' and contract['plan_hash']==b.PLAN
              and contract['initial']==b.S0[family] and contract['schedule']==schedule,'checkpoint_contract')
    n=len(schedule)
    b.require(status['complete'] is True and status['planned_steps']==status['completed_steps']==n and status['forwards']==8*n,'checkpoint_status')
    cp=path/'checkpoints'/f'step-{n:06d}'
    b.require(sorted((path/'checkpoints').glob('step-*'))[-1]==cp,'checkpoint_step')
    checks=b.read(cp/'checksums.json')
    b.require(set(checks)=={'state.json','tensors.safetensors'},'checkpoint_files')
    for name,h in checks.items():b.require(b.sha(cp/name)==h,'checkpoint_checksum')
    state=b.read(cp/'state.json')
    b.require(state['identity']==contract and state['step']==n,'checkpoint_state')
    return contract,{'policy':policy,'seed':seed,'family':family,'updates':n,'tensor_sha256':checks['tensors.safetensors'],
                     'adapter_hash_recorded':status['adapter_hash'],'adapter_hash_recomputed':False}


def durable(persistent):
    b.require(not any((persistent/n).exists() for n in ('SNAPSHOT_PENDING.json','INFLIGHT.json')),'pending_storage')
    latest=sorted((persistent/'snapshots').iterdir())[-1]
    b.require((latest/'COMPLETE').read_text().strip()==b.sha(latest/'index.json'),'snapshot_marker')
    files=b.read(latest/'index.json')['files']
    for h in set(files.values()):
        b.require(len(h)==64 and all(c in '0123456789abcdef' for c in h),'object_address')
        b.require(b.sha(persistent/'objects'/h)==h,'durable_object')
    receipt=b.read(persistent/'objects'/files['receipt.json'])
    b.require(receipt['safe'] is True and receipt['plan_hash']==b.PLAN,'durable_receipt')


def verify_recovered_root(root, persistent, fit15=False):
    latest = max((persistent / 'snapshots').iterdir())
    expected = '1795085568012921921-215202ff7324' if fit15 else '1795063166457853918-9a7dc24d54c7'
    b.require(latest.name == expected, 'recovery_snapshot_changed')
    files = b.read(latest / 'index.json')['files']
    receipt = b.read(persistent / 'objects' / files['receipt.json'])
    with zipfile.ZipFile(persistent / 'objects' / files['state.zip']) as archive:
        checks = json.loads(archive.read('checksums.json'))
    for name, expected in {**checks, **receipt['tensors']}.items():
        b.require(b.sha(root / name) == expected, 'scratch_differs_from_recovery')
    for folder in ('attempts', 'events/shards'):
        recorded = {n for n in checks if n.startswith(folder + '/')}
        live = {p.relative_to(root).as_posix() for p in (root / folder).iterdir() if p.is_file()}
        b.require(live == recorded, 'ledger_inventory_changed')
    if fit15:
        return
    path = root / 'continuations/uniform/227/Q'
    latest_cp = max((path / 'checkpoints').glob('step-*'))
    b.require(latest_cp.name == 'step-000077' and b.sha(latest_cp / 'tensors.safetensors') ==
              'a4caba39dae124dcc548880d3e454c8c22e334e04d11cc5c5559d914e3c6379b', 'step77_checkpoint')
    status = b.read(path / 'status.json')
    b.require(status['completed_steps'] == 77 and status['adapter_hash'] ==
              '9a55f09e7728ce781bfa82fa6cd7db97545faa2b21a9822f9f812f32f5eedf19', 'step77_status')


def main(recovered=False, fit15=False):
    recovered = recovered or fit15
    prior_fits = 15 if fit15 else 9
    inherited = 1440 if fit15 else 941
    checkout=Path(os.environ['PACT_CHECKOUT']);local=Path(os.environ['PACT_LOCAL'])
    b.require(subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==b.COMMIT,'runtime_commit')
    b.require(not subprocess.check_output(['git','-C',str(checkout),'status','--porcelain'],text=True).strip(),'runtime_dirty')
    root=local/'runs'/b.RUN;persistent=Path('/dataset')/os.environ['USER']/'PACT/stage2-documented-execution-export-fixed-v1'/b.RUN
    audit=persistent/'policy-training-batch-v1';work=local/'policy-training-batch-v1'
    if recovered:
        persistent = persistent.parent.parent / 'stage2-documented-step77-recovery-v1' / b.RUN
        audit = persistent / 'training-from-step77-v1'
        work = local / 'training-from-step77-v1'
    if fit15:
        audit = persistent / 'training-from-fit15-v1'
        work = local / 'training-from-fit15-v1'
    b.require(not audit.exists() and not work.exists(),'already_started_no_automatic_retry')
    plan=b.read(root/'plan.json');allocation=b.read(root/'policies.json')
    b.require(b.digest(plan)==b.PLAN and plan['fixture'] is False and plan['scratch_root']==str(root),'plan')
    b.require(b.sha(root/'policies.json')==POLICY_SHA and b.read(root/'policy-freeze-receipt.json')['sha256']==POLICY_SHA,'frozen_policies')
    b.require(b.sha(root/'execution-preflight.json')==b.PREFLIGHT,'preflight')
    batch = jobs(allocation,plan)
    before = b.events(root)
    original = b.read(root/'summary.json')
    durable(persistent)
    if recovered:
        verify_recovered_root(root, persistent, fit15)
        accounting(original,original,1440 if fit15 else 864)  # Last report was exported at fit nine.
        b.require(len(before)==9954+inherited,'recovered_event_count')
        expected_paths = {root/'continuations'/p/str(seed)/f for p,seed,f,_ in batch[:15 if fit15 else 10]}
        b.require({p.parent for p in (root/'continuations').rglob('contract.json')}==expected_paths,'initial_fit_inventory')
        for policy,seed,family,schedule in batch[:prior_fits]:
            checkpoint(root/'continuations'/policy/str(seed)/family,policy,seed,family,schedule)
        b.require(not (root/'policy-lock.json').exists(),'later_work')
    else:
        b.archive(persistent/'bundles'/f'{b.RUN}-PRIVATE-1794977851626542544.zip','7e0f602afd38bbf0050c809500c27047d6c6cff128a46e57b98383b7d2d8a2be',root)
        b.require(not any(p.is_file() for p in (root/'continuations').rglob('*')) and not (root/'policy-lock.json').exists(),'later_work')
        accounting(original,original,0)
        b.require(len(before)==9954,'initial_events')
    protected=b.protected_inventory(root,b.COMPLETED+b.REMAINING)
    for folder in ('scores','stages'):
        protected.update({str(p.relative_to(root)):b.sha(p) for p in (root/folder).rglob('*') if p.is_file()})
    for name in ('policies.json','policy-freeze-receipt.json','credits.private.json','allocation_summary.json'):
        protected[name]=b.sha(root/name)
    audit.mkdir(mode=0o700);work.mkdir(mode=0o700)
    decision='User approved the bounded policy-training batch: five frozen policies, two seeds, three actors; 2880 optimizer updates and 23040 supervised forwards total, original S0 per fit. Zero generation or diagnostic scoring. Verify and export each fit, stop before policy lock/evaluation; no retries or historical budget reset.'
    b.save(audit/'authorization.json',{'plan_hash':b.PLAN,'policies_sha256':POLICY_SHA,'user_decision':decision,'fits':30,'updates':2880,'training_forwards':23040,'generation':0,'scores':0})
    receipts=[];updates=0;completed_paths=set()
    if recovered:
        updates=inherited
        for policy,seed,family,_ in batch[:prior_fits]:
            prior=root/'continuations'/policy/str(seed)/family
            completed_paths.add(prior)
            protected.update({str(p.relative_to(root)):b.sha(p) for p in prior.rglob('*') if p.is_file()})
    for index,(policy,seed,family,schedule) in enumerate(batch,1):
        if recovered and index<=prior_fits:
            continue
        offset=77 if recovered and not fit15 and index==10 else 0
        path=root/'continuations'/policy/str(seed)/family
        b.require(bool(offset) == path.exists(),'fit_start_boundary')
        if recovered:
            # Per-step checkpoint files and per-fit exports accumulate on scratch.
            sample = root/'continuations/terminal_block/113'/family/'checkpoints'
            tensor_size = (max(sample.glob('step-*'))/'tensors.safetensors').stat().st_size
            active_bytes = sum((max(folder.glob('step-*'))/'tensors.safetensors').stat().st_size
                               for folder in root.glob('**/checkpoints') if any(folder.glob('step-*')))
            needed = (len(schedule)-offset+2)*tensor_size + 2*active_bytes + 4*1024**3
            free = shutil.disk_usage(root).free
            print(f'Fit {index} scratch available={free} estimated_required={needed} bytes',flush=True)
            b.require(free>=needed,'scratch_capacity_before_fit')
        print(f'TRAIN fit {index}/30: {policy}/{seed}/{family}; {len(schedule)} updates',flush=True)
        scope={'stage':'continuation','policy':policy,'seed':seed,'family':family}
        approval={'version':'documented_stage2_stage_approval_v1','run_id':b.RUN,'plan_hash':b.PLAN,'freeze':plan['freeze'],
            'fixture':False,'scope':scope,'limits':plan['budgets'],'historical_spending':None,'historical_budget_reset':False,
            'source_code':plan['source_code'],'preflight_sha256':b.PREFLIGHT,'user_decision':decision,'execution_approved':True,'spending_approved':True}
        tag=f'{policy}-{seed}-{family}';ap=work/f'{tag}.approval.json';ah=b.save(ap,approval)
        config={**scope,'run_dir':str(root),'plan_hash':b.PLAN,'approval':str(ap),'approval_sha256':ah,'cache_dir':str(local/'cache'),'persistent':str(persistent)}
        if offset:
            config['resume']=True
        cp=work/f'{tag}.config.json';b.save(cp,config)
        for p in (ap,cp):shutil.copy2(p,audit/p.name)
        log=work/f'{tag}.log'
        with log.open('x') as stream:
            proc=subprocess.Popen(['bash',str(checkout/'tools/aai_documented_execution.sbatch')],env=dict(os.environ,PACT_EXECUTION_CONFIG=str(cp)),stdout=stream,stderr=subprocess.STDOUT)
            while True:
                try:code=proc.wait(timeout=60);break
                except subprocess.TimeoutExpired:print(f'TRAIN {tag} running; log: {log}',flush=True)
        shutil.copy2(log,audit/log.name);b.require(code==0,'fit_failed_no_retry')
        outputs=[]
        for line in log.read_text().splitlines():
            try:v=json.loads(line)
            except ValueError:continue
            if isinstance(v,dict) and 'bundles' in v and 'result' in v:outputs.append(v)
        b.require(len(outputs)==1,'export_result');out=outputs[0]
        contract,receipt=checkpoint(path,policy,seed,family,schedule)
        b.require(out['result']==b.read(path/'status.json'),'returned_fit_status')
        completed_paths.add(path)
        actual_paths={p.parent for p in (root/'continuations').rglob('contract.json')}
        b.require(actual_paths==completed_paths,'unexpected_continuation')
        after=b.events(root);delta(root,before,after,path,contract,schedule,offset)
        updates+=len(schedule)-offset;accounting(b.read(root/'summary.json'),original,updates)
        b.require(all(b.sha(root/n)==h for n,h in protected.items()),'protected_artifacts_changed')
        b.require(not (root/'policy-lock.json').exists(),'evaluation_gate_changed')
        b.require(set(out['bundles'])=={'PRIVATE','SANITIZED','RECOVERY'},'exports')
        for info in out['bundles'].values():b.archive(persistent/'bundles'/Path(info['path']).name,info['sha256'],root)
        durable(persistent)
        protected.update({str(p.relative_to(root)):b.sha(p) for p in path.rglob('*') if p.is_file()})
        protected.update({str(p.relative_to(root)):b.sha(p) for p in (root/'approvals').glob('*.json')})
        receipt.update(verified=True,bundles=out['bundles']);b.save(audit/f'{tag}.receipt.json',receipt);receipts.append(receipt)
        before=after
        print(f'VERIFIED {index}/30 fits; {updates}/2880 updates; durable exports complete',flush=True)
    final={'status':'POLICY_TRAINING_BATCH_COMPLETE','plan_hash':b.PLAN,'policies_sha256':POLICY_SHA,'fits':30,'new_updates':updates,
           'new_training_forwards':updates*8,'new_generations':0,'new_scores':0,'final_bundles':receipts[-1]['bundles'],
           'policy_lock_authorized':False,'evaluation_authorized':False,'historical_spending':None}
    if recovered:
        final.update(inherited_updates=inherited,cumulative_updates=updates,new_updates=updates-inherited,new_training_forwards=(updates-inherited)*8)
    b.save(audit/'summary.sanitized.json',final);print(json.dumps(final),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--from-fit15',action='store_true')
    mode.add_argument('--from-verified-step77',action='store_true')
    args=parser.parse_args()
    try:main(args.from_verified_step77,args.from_fit15)
    except Exception as error:
        print(json.dumps({'status':'TRAINING_BATCH_STOPPED_NO_AUTOMATIC_RETRY','exception_type':type(error).__name__,
            'check':str(error) if isinstance(error,b.CheckFailed) else None,'preserve_scratch_and_durable_evidence':True}),flush=True)
        raise SystemExit(1)
