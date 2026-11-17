"""Approved 13-branch orchestration only; pinned scientific code is never edited."""
import collections
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import zipfile

PLAN = '024f9ef5ffccb9f90bcebab2818971964943b2892aa7ed8e1932ef02e55659f9'
COMMIT = '93b89ce38be743acd6a3aa38177237ce99a3eeeb'
RUN = 'pact-stage2-documented-execution-001'
PREFLIGHT = '1e697a75aec6dd47fe2669235b1597f2010c85b05158f773c097880dd33ea8bb'
REMAINING = [(3, 'M')] + [(b, f) for b in range(4, 8) for f in 'QLM']
COMPLETED = [(b, f) for b in range(3) for f in 'QLM'] + [(3, 'Q'), (3, 'L')]
S0 = dict(Q='eebe817dc9238d7f93e81c0152fc4c678279a5ad9840343fae5ca1ba7e66e161',
          L='d1215a90f9a91967dfd22259d688352cb3e56c3090f3d290b45fb5e1a11fcb56',
          M='a282809319d49d6d8269e6063e349129f16f9c23abb8c865d4585f31f6c4f77d')


class CheckFailed(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise CheckFailed(reason)


def canonical(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


def digest(x):
    return hashlib.sha256(canonical(x).encode()).hexdigest()


def sha(path):
    require(not path.is_symlink(), 'symlink')
    with path.open('rb') as stream:
        return stream_sha(stream)


def stream_sha(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024*1024), b''):
        h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x') as stream:
        stream.write(canonical(value) + '\n')
    return sha(path)


def archive(path, expected, root):
    require(sha(path) == expected, 'archive_hash')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        checks = json.loads(z.read('checksums.json'))
        require(len(names) == len(set(names)) and set(names) == set(checks) | {'checksums.json', 'HANDOFF.json'}, 'archive_inventory')
        require(json.loads(z.read('HANDOFF.json'))['recovery_safe'] is True, 'unsafe_archive')
        for name, h in checks.items():
            p = PurePosixPath(name)
            require(not p.is_absolute() and '..' not in p.parts, 'archive_path')
            with z.open(name) as stream:
                require(stream_sha(stream) == h, 'archive_member')
            if name != '.lock':
                require(sha(root/name) == h, 'scratch_differs_from_export')


def schedule(plan, b, f):
    block = plan['blocks'][b]
    ids = sorted(block['fit'], key=lambda t: digest([20261027, 'temporary', 17, b, f, t]))[:64]
    require(len(ids) == len(set(ids)) == 64, 'fit_size')
    records = {r['task']['task_id']: r for r in plan['training_source']['records']}
    require(all(records[t]['split'] == 'main_fit' for t in ids), 'fit_split')
    require(not set(ids) & set(plan['probes'][block['family']]), 'probe_overlap')
    return [{'tasks': ids[k:k+8], 'kind': 'base', 'block': b} for k in range(0,64,8)]


def checkpoint(root, plan, b, f):
    p = root/'branches'/f'block-{b}-{f}'
    c, s, r, e = [read(p/n) for n in ('contract.json','status.json','rollback.json','evaluated.json')]
    require(c['family'] == f and c['plan_hash'] == PLAN and c['initial'] == S0[f] and c['seed'] == 17, 'contract')
    require(c['schedule'] == schedule(plan,b,f), 'schedule')
    require(s['complete'] is True and s['completed_steps'] == 8 and s['planned_steps'] == 8 and s['forwards'] == 64, 'training_status')
    require(r['complete'] is True and r['initial_hash'] == r['restored_hash'] == S0[f] and r['probe_training_tokens'] == 0 and r['temporary_optimizer_discarded'] is True, 'rollback')
    require(e['complete'] is True and e['probe_ids'] == plan['probes'][plan['blocks'][b]['family']], 'evaluated_probes')
    cp = p/'checkpoints/step-000008'
    checks = read(cp/'checksums.json')
    require(set(checks) == {'state.json','tensors.safetensors'}, 'tensor_inventory')
    for n,h in checks.items(): require(sha(cp/n) == h, 'tensor_hash')
    state = read(cp/'state.json')
    require(state['step'] == 8 and state['identity'] == c, 'checkpoint_identity')
    return {'tensor_sha256': checks['tensors.safetensors'], 'adapter_hash_recorded': s['adapter_hash'], 'adapter_hash_recomputed': False}


def accounting(summary, done):
    require(summary['physical_attempts']['assay'] == dict(generation=3056+328*done, scores=0, training_forwards=704+64*done, updates=88+8*done), 'assay_accounting')
    require(summary['physical_attempts']['policy'] == dict(generation=0,scores=0,training_forwards=0,updates=0), 'policy_work')
    require(summary['committed_operations'] == 3144+336*done and summary['unresolved'] == 0 and summary['recovery_safe'] is True, 'unsafe_accounting')
    require(summary['reserved_output_tokens'] == 1564672+167936*done, 'token_accounting')
    require(summary['historical_spending'] is None and summary['remaining_historical_budget'] is None, 'historical_accounting')


def events(root):
    attempts = {p.stem:p for p in (root/'attempts').glob('*.json')}
    shards = {p.stem:p for p in (root/'events/shards').glob('*.json')}
    markers = {p.stem:p for p in (root/'events/shards').glob('*.sha256')}
    require(attempts.keys() == shards.keys() == markers.keys(), 'unresolved_events')
    result = {}
    for k,p in shards.items():
        h = sha(p)
        require(markers[k].read_text().strip() == h, 'event_checksum')
        result[k] = (h, sha(attempts[k]))
    return result


def delta(root, before, after, family):
    require(all(after.get(k) == v for k,v in before.items()), 'prior_events_changed')
    new = set(after)-set(before)
    require(len(new) == 336, 'unexpected_event_count')
    kinds, formats, steps = collections.Counter(), collections.Counter(), []
    for k in new:
        e = read(root/'events/shards'/f'{k}.json')
        intent = e['intent']; identity = intent['identity']
        require(identity['owner'] == RUN and identity['plan_hash'] == PLAN and identity['part'] == 'assay', 'event_owner')
        require(read(root/'attempts'/f'{k}.json') == intent and digest(identity) == k, 'intent_mismatch')
        kind = identity['kind']; kinds[kind] += 1
        if kind == 'generation':
            require(intent['cost'] == {'generation':1}, 'generation_cost')
            status = e['value']['packet']['status']
            require(status in ('ok','invalid','abstention'), 'packet_status')
            formats[status] += 1
        elif kind == 'update':
            require(intent['cost'] == {'updates':1,'training_forwards':8} and identity['dependency']['family'] == family, 'update_cost')
            steps.append(e['value']['step'])
        else:
            raise ValueError('unexpected_operation')
    require(kinds == {'generation':328,'update':8} and sorted(steps) == list(range(1,9)), 'branch_delta')
    return dict(formats)


def boundary(root, persistent, plan, completed, done):
    require(digest(read(root/'plan.json')) == PLAN and plan['s0'] == S0, 'plan_changed')
    require(not any((persistent/n).exists() for n in ('SNAPSHOT_PENDING.json','INFLIGHT.json')), 'pending_persistence')
    latest = sorted((persistent/'snapshots').iterdir())[-1]
    require((latest/'COMPLETE').read_text().strip() == sha(latest/'index.json'), 'incomplete_snapshot')
    index = read(latest/'index.json')['files']
    for h in set(index.values()):
        require(len(h)==64 and all(c in '0123456789abcdef' for c in h), 'object_address')
        require(sha(persistent/'objects'/h)==h, 'durable_object')
    receipt = read(persistent/'objects'/index['receipt.json'])
    require(receipt['safe'] is True and receipt['plan_hash']==PLAN, 'unsafe_receipt')
    require({p.name for p in (root/'branches').iterdir()} == {f'block-{b}-{f}' for b,f in completed}, 'unexpected_branch')
    allowed = [{'stage':s} for s in ('preflight','assay-smoke','collect')] + [{'stage':'branch','block':b,'family':f} for b,f in completed]
    require(all(read(p)['scope'] in allowed for p in (root/'approvals').glob('*.json')), 'unexpected_approval')
    for n in ('scores','continuations'):
        require(not any(p.is_file() for p in (root/n).rglob('*')), 'later_stage_work')
    accounting(read(root/'summary.json'),done)
    for b,f in completed: checkpoint(root,plan,b,f)
    ev = events(root)
    require(len(ev)==3144+336*done,'event_total')
    return ev


def protected_inventory(root, completed):
    paths = [root/'plan.json', root/'execution-preflight.json']
    for folder in ('outputs','attacks','approvals','sealed'):
        paths.extend(p for p in (root/folder).rglob('*') if p.is_file())
    for b,f in completed:
        branch = root/'branches'/f'block-{b}-{f}'
        paths.extend(branch/n for n in ('contract.json','status.json','rollback.json','evaluated.json'))
        paths.extend((branch/'checkpoints/step-000008').iterdir())
    return {str(p.relative_to(root)):sha(p) for p in paths if p.is_file()}


def main():
    home = Path.home(); user = os.environ['USER']
    checkout = Path(os.environ['PACT_CHECKOUT'])
    require(subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True).strip()==COMMIT, 'runtime_commit')
    require(not subprocess.check_output(['git','-C',str(checkout),'status','--porcelain'],text=True).strip(), 'runtime_dirty')
    local = Path(os.environ['PACT_LOCAL']); root = local/'runs'/RUN
    persistent = Path('/dataset')/user/'PACT/stage2-documented-execution-export-fixed-v1'/RUN
    audit = persistent/'remaining-branches-batch-v1'
    require(not audit.exists(),'batch_already_started_no_automatic_resume')
    plan = read(root/'plan.json')
    require(digest(plan)==PLAN and plan['fixture'] is False and plan['historical_spending'] is None and plan['scratch_root']==str(root),'plan_binding')
    require(sha(root/'execution-preflight.json')==PREFLIGHT,'preflight_changed')
    archive(persistent/'bundles'/f'{RUN}-PRIVATE-1794894058064977045.zip','3aa1074a336e6992ba67518381389065d81d24d6f960452219c53ef6d7d18ae9',root)
    completed = list(COMPLETED)
    before = boundary(root,persistent,plan,completed,0)
    protected = protected_inventory(root,completed)
    probes = plan['probes']['logiqa']
    require(len(probes)==len(set(probes))==40,'probe_count')
    accepted = [read(root/'attacks/assay'/f'{digest(t)}.json')['accepted'] for t in probes]
    require(all(type(v) is bool for v in accepted) and sum(accepted)==32,'attack_count')
    for b,f in REMAINING:
        require(plan['blocks'][b]['family']=='logiqa','source_changed')
        schedule(plan,b,f)
    audit.mkdir(mode=0o700)
    work = local/'remaining-branches-batch-v1'; work.mkdir(mode=0o700)
    authorization = {'plan_hash':PLAN,'branches':REMAINING,'new_generation_max':4264,'new_updates_max':104,'new_training_forwards_max':832,'new_reserved_tokens_max':2183168,'scoring_authorized':False,'later_stages_authorized':False,'historical_spending':None,'user_decision':'approve, just do a batch scope, this one job upload review cycle is taking too long.'}
    save(audit/'authorization.json',authorization)
    receipts=[]
    for i,(b,f) in enumerate(REMAINING,1):
        print(f'BATCH branch {i}/13: block-{b}-{f}; starting at {len(before)} verified events',flush=True)
        a={'version':'documented_stage2_stage_approval_v1','run_id':RUN,'plan_hash':PLAN,'freeze':plan['freeze'],'fixture':False,'scope':{'stage':'branch','block':b,'family':f},'limits':plan['budgets'],'historical_spending':None,'historical_budget_reset':False,'source_code':plan['source_code'],'preflight_sha256':PREFLIGHT,'user_decision':authorization['user_decision']+' Scope: remaining 13 branches only; per branch original S0, 8 updates, 64 training forwards, 328 generations, 167936 reserved tokens. Verify/export each branch; stop on failure. No scoring or policy work.','execution_approved':True,'spending_approved':True}
        ap=work/f'{b}-{f}.approval.json'; ah=save(ap,a)
        config={'stage':'branch','block':b,'family':f,'run_dir':str(root),'plan_hash':PLAN,'approval':str(ap),'approval_sha256':ah,'cache_dir':str(local/'cache'),'persistent':str(persistent)}
        cp=work/f'{b}-{f}.config.json'; save(cp,config)
        shutil.copy2(ap,audit/ap.name); shutil.copy2(cp,audit/cp.name)
        env=dict(os.environ,PACT_EXECUTION_CONFIG=str(cp))
        log=work/f'{b}-{f}.log'
        with log.open('x') as stream:
            process=subprocess.Popen(['bash',str(checkout/'tools/aai_documented_execution.sbatch')],env=env,stdout=stream,stderr=subprocess.STDOUT)
            while True:
                try:
                    code=process.wait(timeout=60)
                    break
                except subprocess.TimeoutExpired:
                    print(f'BATCH block-{b}-{f} still running; private log: {log}',flush=True)
        shutil.copy2(log,audit/log.name)
        require(code==0,'branch_process_failed_no_retry')
        outputs=[]
        for line in log.read_text().splitlines():
            try: v=json.loads(line)
            except ValueError: continue
            if isinstance(v,dict) and 'bundles' in v and 'result' in v:outputs.append(v)
        require(len(outputs)==1,'export_result_missing')
        out=outputs[0]
        require(out['result']=={'branch':f'block-{b}-{f}','complete':True},'wrong_completed_branch')
        require(set(out['bundles'])=={'PRIVATE','SANITIZED','RECOVERY'},'missing_export')
        for kind,info in out['bundles'].items():
            durable=persistent/'bundles'/Path(info['path']).name
            archive(durable,info['sha256'],root)
        completed.append((b,f))
        after=boundary(root,persistent,plan,completed,i)
        formats=delta(root,before,after,f)
        current_protected=protected_inventory(root,completed)
        require(all(current_protected.get(n)==h for n,h in protected.items()),'prior_artifacts_changed')
        protected=current_protected
        receipt={'branch':f'block-{b}-{f}','verified':True,'new_generations':328,'new_updates':8,'new_training_forwards':64,'formats':formats,'prior_events_unchanged':True,'checkpoint':checkpoint(root,plan,b,f),'bundles':out['bundles']}
        save(audit/f'{b}-{f}.verified.json',receipt)
        receipts.append(receipt); before=after
        print(json.dumps({'branch':receipt['branch'],'verified':True,'formats':formats,'completed_in_batch':i}),flush=True)
    final={'status':'REMAINING_13_BRANCHES_VERIFIED','plan_hash':PLAN,'completed_in_batch':13,'cumulative':read(root/'summary.json'),'last_bundles':receipts[-1]['bundles'],'scoring_started':False,'later_execution_authorized':False}
    save(audit/'summary.sanitized.json',final)
    print(json.dumps(final),flush=True)


if __name__=='__main__':
    try: main()
    except Exception as e:
        print(json.dumps({'status':'BATCH_STOPPED_NO_AUTOMATIC_RETRY','exception_type':type(e).__name__,'check':str(e) if isinstance(e,CheckFailed) else None,'preserve_scratch_and_durable_evidence':True}),flush=True)
        raise SystemExit(1)
