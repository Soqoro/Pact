"""One approved score-only job on the fixed completed assay; no automatic next stage."""
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

import aai_documented_remaining_batch as b

EXPECTED_SCORES = 2442


def score_keys(root, plan):
    entries = [('S0', [t for ids in plan['probes'].values() for t in ids])]
    entries += [(f'block-{i}-{f}', plan['probes'][block['family']])
                for i,block in enumerate(plan['blocks']) for f in 'QLM']
    accepted = {}
    for source, count, accepted_count in [('arc_challenge',24,17),('logiqa',40,32)]:
        ids=plan['probes'][source]
        b.require(len(ids)==len(set(ids))==count,'probe_count')
        for t in ids:
            value=b.read(root/'attacks/assay'/f'{b.digest(t)}.json')['accepted']
            b.require(type(value) is bool,'attack_status')
            accepted[t]=value
        b.require(sum(accepted[t] for t in ids)==accepted_count,'attack_count')
    keys={(branch,t,kind) for branch,ids in entries for t in ids
          for kind in ['private_bank','clean']+(['exchange'] if accepted[t] else [])}
    b.require(len(keys)==EXPECTED_SCORES,'score_graph_changed')
    return keys


def check_loss(value):
    raw=value['raw_nll']
    b.require(type(raw) in (float,int) and math.isfinite(raw) and raw>=0,'invalid_nll')
    b.require(value['capped_nll']==min(float(raw),10.),'nll_cap')
    b.require(value['generated_correctness_is_separate'] is True,'score_semantics')


def verify_score_delta(root, before, after, expected, pristine):
    b.require(all(after.get(k)==v for k,v in before.items()),'prior_events_changed')
    new=set(after)-set(before)
    b.require(len(new)==EXPECTED_SCORES,'score_event_count')
    observed=set()
    for k in new:
        event=b.read(root/'events/shards'/f'{k}.json')
        intent=event['intent'];identity=intent['identity'];dep=identity['dependency']
        b.require(b.digest(identity)==k and b.read(root/'attempts'/f'{k}.json')==intent,'score_intent')
        b.require(identity['owner']==b.RUN and identity['plan_hash']==b.PLAN and identity['part']=='assay'
                  and identity['kind']=='score' and intent['cost']=={'scores':1},'non_score_operation')
        logical=(dep['branch'],dep['task'],dep['kind'])
        b.require(logical in expected and logical not in observed,'unexpected_score')
        observed.add(logical)
        b.require(dep['model']==pristine,'readout_identity')
        check_loss(event['value'])
        record=b.read(root/'scores'/f'{b.digest(list(logical))}.json')
        b.require(record=={'logical':list(logical),**event['value']},'score_record_mismatch')
    b.require(observed==expected,'incomplete_scores')
    b.require({p.name for p in (root/'scores').iterdir()}=={b.digest(list(k))+'.json' for k in expected},'score_inventory')


def post_accounting(summary, original):
    b.require(summary['physical_attempts']['assay']==dict(generation=7320,scores=2442,training_forwards=1536,updates=192),'score_accounting')
    b.require(summary['committed_operations']==9954 and summary['unresolved']==0 and summary['recovery_safe'] is True,'unsafe_score_boundary')
    for key in ('reserved_output_tokens','input_tokens','output_tokens','format_status_counts','historical_spending','remaining_historical_budget'):
        b.require(summary[key]==original[key],'generation_or_history_changed')
    b.require(summary['physical_attempts']['policy']==original['physical_attempts']['policy'],'policy_work')
    b.require(set(summary['stages'])=={'assay-smoke','collect','score'},'unexpected_stage')


def main():
    checkout=Path(os.environ['PACT_CHECKOUT']);local=Path(os.environ['PACT_LOCAL'])
    b.require(subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==b.COMMIT,'runtime_commit')
    b.require(not subprocess.check_output(['git','-C',str(checkout),'status','--porcelain'],text=True).strip(),'runtime_dirty')
    root=local/'runs'/b.RUN
    persistent=Path('/dataset')/os.environ['USER']/'PACT/stage2-documented-execution-export-fixed-v1'/b.RUN
    audit=persistent/'score-only-v1';work=local/'score-only-v1'
    b.require(not audit.exists() and not work.exists(),'score_already_started_no_automatic_retry')
    plan=b.read(root/'plan.json')
    b.require(b.digest(plan)==b.PLAN and plan['fixture'] is False and plan['scratch_root']==str(root),'plan_binding')
    b.require(b.sha(root/'execution-preflight.json')==b.PREFLIGHT,'preflight_changed')
    b.archive(persistent/'bundles'/f'{b.RUN}-PRIVATE-1794916846506389838.zip',
              '8331213b321fc94dfd68f8bc3b291b3ec680da03c4e3c068bd56db388230874c',root)
    completed=b.COMPLETED+b.REMAINING
    before=b.boundary(root,persistent,plan,completed,13)
    protected=b.protected_inventory(root,completed)
    expected=score_keys(root,plan)
    pristine=b.read(Path(plan['parent_path'])/'inference_identity_manifest.json')['models']['R']['pristine_identity']
    original=b.read(root/'summary.json')
    b.require(not (root/'stages/score.json').exists(),'score_already_recorded')
    for name in ('policies.json','policy-lock.json','credits.private.json'):
        b.require(not (root/name).exists(),'later_stage_artifact')
    audit.mkdir(mode=0o700);work.mkdir(mode=0o700)
    approval={'version':'documented_stage2_stage_approval_v1','run_id':b.RUN,'plan_hash':b.PLAN,
        'freeze':plan['freeze'],'fixture':False,'scope':{'stage':'score'},'limits':plan['budgets'],
        'historical_spending':None,'historical_budget_reset':False,'source_code':plan['source_code'],
        'preflight_sha256':b.PREFLIGHT,'execution_approved':True,'spending_approved':True,
        'user_decision':'User replied approve to scoring stage only: 2442 expected diagnostic forwards within frozen 2640 ceiling; pristine R, zero new generations, training forwards or updates. Export and stop. No policy freeze, training, evaluation or historical budget reset.'}
    ap=work/'approval.json';ah=b.save(ap,approval)
    config={'stage':'score','run_dir':str(root),'plan_hash':b.PLAN,'approval':str(ap),'approval_sha256':ah,
            'cache_dir':str(local/'cache'),'persistent':str(persistent)}
    cp=work/'config.json';b.save(cp,config)
    shutil.copy2(ap,audit/ap.name);shutil.copy2(cp,audit/cp.name)
    print(json.dumps({'stage':'score','expected_diagnostic_forwards':2442,'new_generations':0,'new_training_forwards':0,'new_updates':0,'approval_sha256':ah}),flush=True)
    log=work/'score.log'
    with log.open('x') as stream:
        process=subprocess.Popen(['bash',str(checkout/'tools/aai_documented_execution.sbatch')],
            env=dict(os.environ,PACT_EXECUTION_CONFIG=str(cp)),stdout=stream,stderr=subprocess.STDOUT)
        while True:
            try:code=process.wait(timeout=60);break
            except subprocess.TimeoutExpired:print(f'Score job still running; private log: {log}',flush=True)
    shutil.copy2(log,audit/log.name)
    b.require(code==0,'score_process_failed_no_retry')
    outputs=[]
    for line in log.read_text().splitlines():
        try:value=json.loads(line)
        except ValueError:continue
        if isinstance(value,dict) and 'bundles' in value and 'result' in value:outputs.append(value)
    b.require(len(outputs)==1,'export_result_missing')
    out=outputs[0]
    b.require(set(out['bundles'])=={'PRIVATE','SANITIZED','RECOVERY'},'missing_exports')
    for info in out['bundles'].values():
        b.archive(persistent/'bundles'/Path(info['path']).name,info['sha256'],root)
    after=b.events(root)
    verify_score_delta(root,before,after,expected,pristine)
    current=b.protected_inventory(root,completed)
    b.require(all(current.get(n)==h for n,h in protected.items()),'prior_artifacts_changed')
    b.require(b.read(root/'stages/score.json')['complete'] is True,'incomplete_stage')
    summary=b.read(root/'summary.json');post_accounting(summary,original)
    # Verify the final durable snapshot and reject any later-stage work.
    b.require(not any((persistent/n).exists() for n in ('SNAPSHOT_PENDING.json','INFLIGHT.json')),'pending_persistence')
    latest=sorted((persistent/'snapshots').iterdir())[-1]
    b.require((latest/'COMPLETE').read_text().strip()==b.sha(latest/'index.json'),'incomplete_snapshot')
    index=b.read(latest/'index.json')['files']
    for h in set(index.values()):
        b.require(len(h)==64 and all(c in '0123456789abcdef' for c in h),'object_address')
        b.require(b.sha(persistent/'objects'/h)==h,'durable_object')
    receipt=b.read(persistent/'objects'/index['receipt.json'])
    b.require(receipt['safe'] is True and receipt['plan_hash']==b.PLAN,'unsafe_receipt')
    b.require({p.name for p in (root/'branches').iterdir()}=={f'block-{i}-{f}' for i,f in completed},'unexpected_branch')
    allowed=[{'stage':s} for s in ('preflight','assay-smoke','collect','score')]+[{'stage':'branch','block':i,'family':f} for i,f in completed]
    b.require(all(b.read(p)['scope'] in allowed for p in (root/'approvals').glob('*.json')),'unexpected_approval')
    b.require(not any(p.is_file() for p in (root/'continuations').rglob('*')),'policy_work')
    for name in ('policies.json','policy-lock.json','credits.private.json'):
        b.require(not (root/name).exists(),'later_stage_artifact')
    final={'status':'SCORING_COMPLETE_VERIFIED','plan_hash':b.PLAN,'diagnostic_forwards':2442,
           'prior_7512_events_unchanged':True,'new_generations':0,'new_training_forwards':0,'new_updates':0,
           'bundles':out['bundles'],'cumulative':summary,'later_execution_authorized':False}
    b.save(audit/'summary.sanitized.json',final)
    print(json.dumps(final),flush=True)


if __name__=='__main__':
    try:main()
    except Exception as e:
        print(json.dumps({'status':'SCORING_STOPPED_NO_AUTOMATIC_RETRY','exception_type':type(e).__name__,
            'check':str(e) if isinstance(e,b.CheckFailed) else None,'preserve_scratch_and_durable_evidence':True}),flush=True)
        raise SystemExit(1)
