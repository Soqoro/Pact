"""Independent 72-call answer-only diagnostic; no training or receiver calls."""
import dataclasses as dc
from pathlib import Path
import time
from ..artifacts import ShardStore,run_lock,sync_run
from ..backends import Request
from ..environment import code_identity,runtime_fingerprint,versions
from ..schemas import Message,task_from_dict
from ..storage import persist_bundle,storage_operation
from ..util import canonical,digest,read_json,redact,write_json
from .colab import review_bundle
from .collection_config import CollectionRuntime
from .receiver import JournalBackend,CallBoundaryStop,inspect_journal
from .scoring import CollectionBackend,verify_references
from .curated_repair import curated_requests
from .prompt_control import prompt_report
from .curated_runner import preflight_contexts
from .preparation_runner import preparation_references

KIND='preparation_prompt_control'
STATUS='train_only_preparation_prompt_control'


def run_prompt_control(config,plan,training_root,root,cache_dir,*,resume=False,
                          stop_after=None,persistent=None,timeout_seconds=120):
    training_root=Path(training_root);root=Path(root)
    parent=preparation_references(plan['training_design'],training_root)
    if canonical(plan['config'])!=canonical(config):raise ValueError('Prompt-control config mismatch')
    if parent.reference_manifest_hash!=plan['reference_manifest_hash']:raise ValueError('Prompt-control reference mismatch')
    if persistent is None:raise ValueError('Prompt control requires durable storage')
    # Verify a durable final-training copy before any inference can start.
    inference_only=(training_root/'INFERENCE_ONLY.json').exists()
    if not inference_only:raise ValueError('Prompt control requires compact verified inference export')
    target=Path(persistent).parent/'inference'
    training_snapshot=sync_run(training_root,target,timeout_seconds=timeout_seconds)
    references_dir=training_root/'references'
    if stop_after is not None and (type(stop_after) is not int or stop_after<1):
        raise ValueError('stop_after must be a positive number of new calls')
    if not 0 < timeout_seconds < float('inf'): raise ValueError('Invalid storage deadline')
    persistent = Path(persistent) if persistent is not None else None
    if persistent is not None and (root.absolute()==persistent.absolute()
            or root.absolute() in persistent.absolute().parents or persistent.absolute() in root.absolute().parents):
        raise ValueError('Persistent destination must be outside scratch run')
    recipe = {'config':config,'plan_hash':digest(plan),
              'source':code_identity(Path(__file__).resolve().parents[3])}
    old = read_json(root/'manifest.json') if resume else None
    if root.exists() and not resume: raise ValueError('Prompt control run exists; use compatible resume')
    if old:
        if old['recipe_hash']!=digest(recipe) or 'identity' not in old:
            raise ValueError('Prompt-control resume source/recipe mismatch')
        inspect_journal(root,plan['budget'])
    with run_lock(root):
        manifest = {'schema_version':1,'kind':KIND,'recipe':recipe,'recipe_hash':digest(recipe),
            'expected_records':72,'completed_records':0,'status':'loading','recovery_safe':True,
            'persistent_copy_verified':False}
        if old: manifest['identity'] = old['identity']
        write_json(root/'manifest.json',manifest);write_json(root/'plan.json',plan)
        write_json(root/'package_versions.json',versions())
        result = {'exit_code':0,'persistent_copy_verified':False,'persistent_snapshot':None,
                  'persistent_bundle':None,'scientific_status':STATUS,'training_snapshot':str(training_snapshot)}
        backend = journal = None; started = time.monotonic(); store = ShardStore(root)
        try:
            if runtime_fingerprint()!=parent.runtime_fingerprint:
                raise ValueError('Prompt control runtime fingerprint changed; no model downloaded')
            verify_references(references_dir,parent)
            backend = CollectionBackend(CollectionRuntime(digest(config),20260920),Path(cache_dir),references_dir,parent)
            if (backend.identity['snapshot']!=plan['models']['actors']['snapshot']
                    or backend.identity['template_hash']!=plan['models']['actors']['template_hash']
                    or backend.base_identity['snapshot']!=parent.base_snapshot
                    or backend.identity['runtime_fingerprint']!=parent.runtime_fingerprint):
                raise ValueError('Prompt control model/runtime mismatch')
            for mode,actual in (('actors',backend.identity),('base',backend.base_identity)):
                for key in ('model','revision','tokenizer_revision','precision','attention','enable_thinking',
                            'template_hash','weight_hashes','generation_defaults','adapters'):
                    if key in plan['models'][mode] and actual.get(key)!=plan['models'][mode][key]:
                        raise ValueError('Prompt control pinned model field changed: '+mode+'/'+key)
            identity = {'recipe_hash':digest(recipe),'actor':backend.identity['snapshot'],
                        'base':parent.base_snapshot,'runtime':parent.runtime_fingerprint}
            if old and old['identity']!=identity: raise ValueError('Prompt control resume identity mismatch')
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
            prefixes = preflight_contexts(backend,plan)
            if old and journal.results and not (root/'prefixes.json').exists():
                raise ValueError('Prompt control resume missing tokenized preflight')
            if old and (root/'prefixes.json').exists() and canonical(read_json(root/'prefixes.json'))!=canonical(prefixes):
                raise ValueError('Prompt control resume tokenized contexts changed')
            write_json(root/'prefixes.json',prefixes)
            expected = set()
            for position,item in enumerate(curated_requests(plan)):
                key=item['work_id'];expected.add(key);journal.begin_record(key)
                context=item['context'];prefix=prefixes[context['context_id']]
                request=Request(task_from_dict(plan['tasks'][context['task_id']]),
                    tuple(Message(m['role'],m['content']) for m in context['messages']),
                    f"agent-{context['recipient']}",context.get('phase','revision'),item['seed'],256,False)
                raw,call=journal.generate(request);tokens=journal.last_generation
                if (call.rendered_prompt!=prefix['rendered_prompt'] or tokens['prompt_ids']!=prefix['prompt_ids']):
                    raise ValueError('Prompt control prompt or token prefix changed after preflight')
                record={'schema_version':1,'work_id':key,'request_hash':digest(item),
                        'context_id':context['context_id'],'sample_index':item['sample_index'],
                        'raw':raw,'call':dc.asdict(call),'tokens':tokens}
                store.put(key,record);manifest['completed_records']=position+1
                if (position+1)%8==0:
                    backend.assert_unchanged()
                    if not manifest['recovery_safe']:manifest['recovery_safe']=True;checkpoint()
                print(f"Prompt control {position+1}/72 {context['task_id']}/agent-{context['recipient']}/{context['arm']}",flush=True)
            if {p.stem for p in (root/'shards').glob('*.json')}!=expected or journal.seen!=set(journal.results):
                raise ValueError('Unexpected prompt-control record or unused cached call')
            if backend.scorer.forwards:raise ValueError('Prompt control performed forbidden scoring')
            verify_references(references_dir,parent)
            manifest['status']='prompt_control_complete_local'
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
            records=store.records();report=prompt_report(plan,records)
            if result['exit_code']:report.update(complete=False,decision='incomplete')
            report['generation_accounting']={'attempted_calls':len(intents),'committed_calls':len(finished),
                'unresolved_attempts':len(intents)-len(finished),
                'input_tokens':sum(r['call']['input_tokens'] for r in finished.values()),
                'output_tokens':sum(r['call']['output_tokens'] for r in finished.values()),
                'reserved_output_tokens':sum(i['max_tokens'] for i in intents.values())}
            name='report.json' if report['complete'] else 'partial_report.json'
            if name=='report.json' and (root/name).exists() and canonical(read_json(root/name))!=canonical(report):
                raise ValueError('Cannot replace completed prompt-control report')
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
            print(f"Local prompt-control ZIP: {output} SHA256: {result['sha256']}",flush=True)
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




def restore_prompt_control(snapshot,destination,*,timeout_seconds=120):
    destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
    return storage_operation('prompt-control-restore',Path(snapshot),destination,timeout_seconds=timeout_seconds)
