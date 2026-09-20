"""One additional private draw on a pinned training-only receiver selection."""
from __future__ import annotations

from collections import Counter
import dataclasses as dc
import json
from pathlib import Path
import time

from ..artifacts import ShardStore, run_lock, sync_run
from ..backends import Request
from ..environment import code_identity, runtime_fingerprint, versions
from ..parsing import parse_answer
from ..protocol import private_prompt
from ..schemas import task_from_dict
from ..storage import persist_bundle, storage_operation
from ..util import canonical, digest, node_seed, read_json, redact, write_json
from .bank import sha
from .colab import review_bundle
from .collection_config import CollectionRuntime
from .receiver import JournalBackend, CallBoundaryStop, inspect_journal, read_receiver_review
from .receiver_plan import ReceiverFeasibilityConfig
from .scoring import CollectionBackend, verify_references

KIND = 'private_support_control'
STATUS = 'train_only_private_seed_control'


@dc.dataclass(frozen=True)
class PrivateControlConfig:
    source_bundle_sha256: str
    selection_hash: str
    generation_seed: int = 1730
    schema_version: int = 1
    purpose: str = 'one_additional_private_draw'

    def validate(self):
        sha(self.source_bundle_sha256); sha(self.selection_hash)
        if (type(self.generation_seed) is not int or self.generation_seed != 1730
                or type(self.schema_version) is not int or self.schema_version != 1
                or self.purpose != 'one_additional_private_draw'):
            raise ValueError('Private control fixes one new draw at seed 1730')
        return self


def load_private_config(path):
    return PrivateControlConfig(**read_json(Path(path))).validate()


def actor_recipe(plan):
    value = dict(plan['actor_recipe'])
    for key in ('reference_hashes','conditions'): value[key] = tuple(value[key])
    return ReceiverFeasibilityConfig(**value).validate()


def private_control_plan(config, bundle):
    config.validate()
    source = read_receiver_review(bundle,config.source_bundle_sha256)
    original = source['plan.json']; manifest = source['manifest.json']
    recipe = dict(original['config'])
    for key in ('reference_hashes','conditions'): recipe[key] = tuple(recipe[key])
    parent = ReceiverFeasibilityConfig(**recipe).validate()
    selection = original['selection']; models = source['model_identity.json']
    if (digest(selection) != config.selection_hash or original['selection_hash'] != config.selection_hash
            or digest(parent) != original['config_hash'] or parent.generation_seed != 1729
            or manifest['status'] != 'receiver_feasibility_complete_local'
            or manifest['completed_records'] != 48 or not source['report.json']['complete']
            or manifest['recipe']['plan_hash'] != digest(original)
            or manifest['recipe_hash'] != digest(manifest['recipe'])
            or manifest['recipe']['source']['dirty']
            or models['base']['snapshot'] != parent.base_snapshot
            or models['actors']['runtime_fingerprint'] != parent.runtime_fingerprint
            or [a['sha256'] for a in models['actors']['adapters']] != list(parent.reference_hashes)):
        raise ValueError('Private control requires the pinned complete receiver source')
    tasks = {t['task_id']:t for t in source['tasks.json']}
    labels = source['labels.json']
    records = [v for k,v in source.items() if k.startswith('shards/')]
    clean = {r['trajectory']['task']['task_id']:r for r in records if r['trajectory']['condition']=='clean'}
    selected = selection['selected']
    if (len(tasks) != 24 or len(selected) != 24 or len(records) != 48 or set(clean) != set(tasks)
            or Counter(t['family'] for t in tasks.values()) != {'arc_challenge':12,'logiqa':12}
            or {e['task_id'] for e in selected} != set(tasks)):
        raise ValueError('Private control requires all 24 original tasks')
    calls = {digest(v['call']):v for k,v in source.items() if k.startswith('calls/shards/')}
    requests = []
    for entry in selected:
        task = task_from_dict(tasks[entry['task_id']]); label = labels[task.task_id]
        if task.split != 'train' or digest(task) != entry['input_hash'] or digest(label) != entry['label_hash']:
            raise ValueError('Source task or separate label changed')
        trajectory = clean[task.task_id]['trajectory']
        if canonical(trajectory['task']) != canonical(task) or len(trajectory['private']) != 3:
            raise ValueError('Source private team changed')
        for agent, packet in enumerate(trajectory['private']):
            call = packet['call']; tokens = calls[digest(call)]['tokens']
            seed = node_seed(node_seed(1730,task.task_id,'trajectory'),'private',agent)
            params = json.loads(call['parameters_json'])
            if (call['actor'] != f'agent-{agent}' or call['phase'] != 'private'
                    or call['seed'] != node_seed(node_seed(1729,task.task_id,'trajectory'),'private',agent)
                    or canonical(call['messages']) != canonical(private_prompt(task,''))
                    or call['snapshot'] != models['actors']['snapshot']
                    or call['template_hash'] != models['actors']['template_hash']
                    or digest(call['rendered_prompt']) != call['context_hash']
                    or tokens['context_hash'] != call['context_hash'] or tokens['raw'] != packet['raw']
                    or call['input_tokens'] != len(tokens['prompt_ids'])
                    or call['output_tokens'] != len(tokens['completion_ids'])
                    or params['do_sample'] is not True or params['max_new_tokens'] != 256
                    or any(params.get(k) != v for k,v in (('temperature',.7),('top_p',.8),('top_k',20)))
                    or call['input_tokens']+256 > 4096):
                raise ValueError('Source private prompt, tokens, seeds or sampling changed')
            item = {'task':dc.asdict(task),'gold':label['answer_id'],'agent':agent,
                'seed':seed,'baseline_call':call,'baseline_raw':packet['raw'],
                'prompt_ids':tokens['prompt_ids'],'baseline_completion_ids':tokens['completion_ids']}
            item['work_id'] = digest(item); requests.append(item)
    return {'status':'private_support_plan_only','kind':KIND,'scientific_status':STATUS,
        'execution_implemented':True,'gpu_verified':False,'model_calls_executed':0,
        'config':dc.asdict(config),'actor_recipe':dc.asdict(parent),'selection':selection,
        'models':models,'source_bundle_sha256':config.source_bundle_sha256,
        'requests':requests,'requests_hash':digest(requests),
        'budget':{'tasks':24,'records':72,'generation_calls_upper_bound':72,
                  'generated_tokens_upper_bound':18432,'input_tokens_upper_bound':276480},
        'training_executed':False,'training_pairs_exported':False}


def private_report(plan, records):
    indexed = {r['work_id']:r for r in records}; requests = plan['requests']
    if len(indexed) != len(records) or set(indexed)-{r['work_id'] for r in requests}:
        raise ValueError('Duplicate or unknown private control records')
    tasks = []; transitions = Counter(); by_agent = {str(i):Counter() for i in range(3)}
    for entry in plan['selection']['selected']:
        items = [i for i in requests if i['task']['task_id']==entry['task_id']]
        draws = {'baseline':[], 'control':[]}
        for item in items:
            allowed = tuple(o['answer_id'] for o in item['task']['options'])
            def outcome(raw,stop):
                answer,_,status = parse_answer(raw,allowed,stop_reason=stop)
                return {'agent':item['agent'],'answer':answer,'parser_status':status,'correct':status=='ok' and answer==item['gold']}
            old = outcome(item['baseline_raw'],item['baseline_call']['stop_reason'])
            draws['baseline'].append(old)
            if item['work_id'] in indexed:
                record = indexed[item['work_id']]
                new = outcome(record['raw'],record['call']['stop_reason']); draws['control'].append(new)
                key = f"{old['correct']}->{new['correct']}"
                transitions[key] += 1; by_agent[str(item['agent'])][key] += 1
        complete = len(draws['control'])==3
        row = {'task_id':entry['task_id'],'family':entry['family'],'complete':complete,'draws':draws}
        for name, values in draws.items():
            correct = sum(v['correct'] for v in values)
            row[name] = (None if len(values)!=3 else {'correct_agents':correct,
                'unanimous_valid_answer':all(v['parser_status']=='ok' for v in values) and len({v['answer'] for v in values})==1,
                'potential_clean_repair_contexts':3-correct if correct else 0})
        tasks.append(row)
    summary = {}
    for family in ('arc_challenge','logiqa','all'):
        cohort = [t for t in tasks if family=='all' or t['family']==family]
        summary[family] = {'selected_tasks':len(cohort),'complete_control_tasks':sum(t['complete'] for t in cohort)}
        for name in ('baseline','control'):
            available = [t[name] for t in cohort if t[name] is not None]
            summary[family][name] = {'tasks':len(available),
                'correct_agent_counts':dict(Counter(t['correct_agents'] for t in available)),
                'unanimous_valid_answer_tasks':sum(t['unanimous_valid_answer'] for t in available),
                'potential_clean_repair_contexts':sum(t['potential_clean_repair_contexts'] for t in available)}
    return {'kind':KIND,'complete':len(records)==len(requests),'completed_records':len(records),
        'expected_records':len(requests),'missing_records':len(requests)-len(records),
        'tasks':tasks,'summary':summary,'correctness_transitions':dict(transitions),
        'transitions_by_agent':{k:dict(v) for k,v in by_agent.items()},
        'training_executed':False,'training_pairs_exported':False,'full_pact_ready':False,
        'limitation':'one additional draw; potential clean repair only, no receiver outputs or preference evidence'}


def run_private_control(config,bundle,references_dir,root,cache_dir,*,resume=False,
                        stop_after=None,persistent=None,timeout_seconds=120):
    root = Path(root); plan = private_control_plan(config,bundle); parent = actor_recipe(plan)
    if stop_after is not None and (type(stop_after) is not int or stop_after<1):
        raise ValueError('stop_after must be a positive number of new calls')
    if not 0 < timeout_seconds < float('inf'): raise ValueError('Invalid storage deadline')
    persistent = Path(persistent) if persistent is not None else None
    if persistent is not None and (root.absolute()==persistent.absolute()
            or root.absolute() in persistent.absolute().parents or persistent.absolute() in root.absolute().parents):
        raise ValueError('Persistent destination must be outside scratch run')
    recipe = {'config':dc.asdict(config),'plan_hash':digest(plan),
              'source':code_identity(Path(__file__).resolve().parents[3])}
    old = read_json(root/'manifest.json') if resume else None
    if root.exists() and not resume: raise ValueError('Private run exists; use compatible resume')
    if old and (old['recipe_hash']!=digest(recipe) or 'identity' not in old):
        raise ValueError('Private resume source/recipe mismatch or uninitialized model')
    if old: inspect_journal(root,plan['budget'])
    with run_lock(root):
        manifest = {'schema_version':1,'kind':KIND,'recipe':recipe,'recipe_hash':digest(recipe),
            'expected_records':72,'completed_records':0,'status':'loading','recovery_safe':True,
            'persistent_copy_verified':False}
        if old: manifest['identity'] = old['identity']
        write_json(root/'manifest.json',manifest);write_json(root/'plan.json',plan)
        write_json(root/'package_versions.json',versions())
        result = {'exit_code':0,'persistent_copy_verified':False,'persistent_snapshot':None,
                  'persistent_bundle':None,'scientific_status':STATUS}
        backend = journal = None; started = time.monotonic(); store = ShardStore(root)
        try:
            if runtime_fingerprint()!=parent.runtime_fingerprint:
                raise ValueError('Private runtime fingerprint changed; no model downloaded')
            verify_references(references_dir,parent)
            backend = CollectionBackend(CollectionRuntime(digest(config),config.generation_seed),Path(cache_dir),references_dir,parent)
            if (backend.identity['snapshot']!=plan['models']['actors']['snapshot']
                    or backend.base_identity['snapshot']!=parent.base_snapshot
                    or backend.identity['runtime_fingerprint']!=parent.runtime_fingerprint):
                raise ValueError('Private control model/runtime mismatch')
            identity = {'recipe_hash':digest(recipe),'actor':backend.identity['snapshot'],
                        'base':parent.base_snapshot,'runtime':parent.runtime_fingerprint}
            if old and old['identity']!=identity: raise ValueError('Private resume identity mismatch')
            manifest.update(identity=identity,status='collecting')
            if backend.identity.get('backend')=='mock':result['scientific_status']='synthetic_fixture'
            write_json(root/'model_identity.json',{'actors':backend.identity,'base':backend.base_identity})
            def checkpoint():
                manifest['committed_calls'] = len(journal.results) if journal else 0
                write_json(root/'manifest.json',manifest)
                if persistent is not None:
                    result['last_verified_snapshot'] = str(sync_run(root,persistent,timeout_seconds=timeout_seconds))
            def before_new():
                if manifest['recovery_safe']:
                    manifest['recovery_safe']=False;checkpoint()
            journal = JournalBackend(backend,root,plan['budget'],stop_after=stop_after,before_new=before_new)
            expected = set()
            for position,item in enumerate(plan['requests']):
                key=item['work_id'];expected.add(key);journal.begin_record(key)
                request=Request(task_from_dict(item['task']),private_prompt(task_from_dict(item['task']),''),
                                f"agent-{item['agent']}",'private',item['seed'],256,False)
                raw,call=journal.generate(request);tokens=journal.last_generation
                if (call.rendered_prompt!=item['baseline_call']['rendered_prompt']
                        or tokens['prompt_ids']!=item['prompt_ids']
                        or call.parameters_json!=item['baseline_call']['parameters_json']):
                    raise ValueError('Private control changed baseline prompt, tokens or sampling')
                record={'schema_version':1,'work_id':key,'request_hash':digest(item),
                        'raw':raw,'call':dc.asdict(call),'tokens':tokens}
                store.put(key,record);manifest['completed_records']=position+1
                if (position+1)%3==0:
                    backend.assert_unchanged()
                    if not manifest['recovery_safe']:manifest['recovery_safe']=True;checkpoint()
                print(f"Private control {position+1}/72 {item['task']['task_id']}/agent-{item['agent']}",flush=True)
            if {p.stem for p in (root/'shards').glob('*.json')}!=expected or journal.seen!=set(journal.results):
                raise ValueError('Unexpected private record or unused cached call')
            if backend.scorer.forwards:raise ValueError('Private control performed forbidden scoring')
            verify_references(references_dir,parent)
            manifest['status']='private_support_complete_local'
        except CallBoundaryStop:
            manifest['status']='interrupted_at_call_boundary'
        except (Exception,KeyboardInterrupt) as exc:
            import traceback
            manifest.update(status='failed',failure={'type':type(exc).__name__,'message':redact(str(exc))})
            write_json(root/'failure.json',{'traceback':redact(traceback.format_exc())});result['exit_code']=2
        finally:
            try:
                intents,finished=inspect_journal(root,plan['budget']);manifest['recovery_safe']=True
            except ValueError:
                intents={p.stem:read_json(p) for p in (root/'call-intents').glob('*.json')}
                finished=journal.results if journal else {};manifest['recovery_safe']=False
            records=store.records();report=private_report(plan,records)
            if result['exit_code']:report['complete']=False
            report['generation_accounting']={'attempted_calls':len(intents),'committed_calls':len(finished),
                'unresolved_attempts':len(intents)-len(finished),
                'input_tokens':sum(r['call']['input_tokens'] for r in finished.values()),
                'output_tokens':sum(r['call']['output_tokens'] for r in finished.values()),
                'reserved_output_tokens':sum(i['max_tokens'] for i in intents.values())}
            name='report.json' if report['complete'] else 'partial_report.json'
            if name=='report.json' and (root/name).exists() and canonical(read_json(root/name))!=canonical(report):
                raise ValueError('Cannot replace completed private report')
            write_json(root/name,report)
            resources={'invocation_seconds':time.monotonic()-started,'exit_code':result['exit_code'],
                'new_calls':journal.new_calls if journal else 0,'committed_calls_total':len(finished),
                'attempted_calls_total':len(intents),'training_executed':False,
                'teacher_forced_forwards':len(backend.scorer.forwards) if backend else 0}
            if backend:
                resources.update(backend.resource_usage(),generation_calls=len(backend.calls),
                    input_tokens=sum(c.input_tokens for c in backend.calls),output_tokens=sum(c.output_tokens for c in backend.calls),
                    pending_call=getattr(backend,'pending_call',None))
            resources['cache_hits']=len(journal.seen)-journal.new_calls if journal else 0
            write_json(root/'resources.json',resources);write_json(root/f'attempts/{time.time_ns()}.json',resources)
            manifest.update(scientific_status=result['scientific_status'],completed_records=len(records),committed_calls=len(finished))
            write_json(root/'manifest.json',manifest)
            output=root.parent/'bundles'/f'{root.name}-review-{time.time_ns()}.zip'
            result.update(review_bundle(root,output,{**result,'status':manifest['status']},
                          kind=KIND+'_review',scientific_status=result['scientific_status']))
            print(f"Local private-control ZIP: {output} SHA256: {result['sha256']}",flush=True)
        if persistent is not None and result['exit_code']==0:
            try:
                snapshot=sync_run(root,persistent,timeout_seconds=timeout_seconds)
                result.update(persistent_copy_verified=True,persistent_snapshot=str(snapshot))
                output=root.parent/'bundles'/f'{root.name}-handoff-{time.time_ns()}.zip'
                result.update(review_bundle(root,output,{**result,'status':manifest['status']},
                              kind=KIND+'_review',scientific_status=result['scientific_status']))
                target=persistent/'bundles'/output.name
                persist_bundle(output,target,result['sha256'],timeout_seconds=timeout_seconds)
                result['persistent_bundle']=str(target)
            except (Exception,KeyboardInterrupt) as exc:
                result.update(exit_code=2,persistence_error=redact(str(exc)))
        return {**result,'status':manifest['status'],'completed_records':manifest['completed_records'],
                'committed_calls':manifest['committed_calls'],'training_executed':False}


def restore_private_control(snapshot,destination,*,timeout_seconds=120):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    return storage_operation('private-control-restore',Path(snapshot),destination,timeout_seconds=timeout_seconds)


def copy_private_source(source,destination,config,*,timeout_seconds=120):
    destination=Path(destination)
    if destination.exists():
        private_control_plan(config,destination)
        return {'path':str(destination),'reused':True}
    destination.parent.mkdir(parents=True,exist_ok=True)
    result=storage_operation('bundle-restore',Path(source),destination,
                             timeout_seconds=timeout_seconds,sha256=config.source_bundle_sha256)
    private_control_plan(config,destination)
    return result
