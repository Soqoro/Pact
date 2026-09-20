"""Bounded 120-task execution, using the unchanged neural warm-start engine."""
import dataclasses as dc
from pathlib import Path
from types import SimpleNamespace
import time

from ..artifacts import sync_run
from ..environment import code_identity
from ..schemas import task_from_dict,TaskLabel
from ..storage import persist_bundle
from ..util import digest,canonical,read_json,write_json,redact
from .warmstart_config import WarmstartConfig
from .warmstart import _run_prepared_warmstart
from .checkpoints import latest_checkpoint
from .scoring import verify_references
from .colab import review_bundle

STATUS='train_only_actor_preparation_120'


@dc.dataclass(frozen=True)
class PreparationTrainingConfig(WarmstartConfig):
    purpose: str = 'bounded_actor_preparation_120'
    steps_per_agent: int = 30

    def validate(self):
        expected=PreparationTrainingConfig(self.data_manifest_hash)
        if canonical(self)!=canonical(expected):raise ValueError('Preparation fixes the complete 90-update recipe')
        # Reuse validation of all old scalar types without relaxing engineering bounds.
        dc.replace(WarmstartConfig(self.data_manifest_hash),seeds=self.seeds).validate()
        return self


def training_inputs(plan):
    if (plan['selection_hash']!=digest(plan['selection']) or len(plan['selection'])!=120
            or plan['training_recipe_hash']!=digest(plan['training'])):
        raise ValueError('Preparation selection or recipe mismatch')
    config=PreparationTrainingConfig(digest({'selection':plan['selection'],'design':digest(plan)})).validate()
    tasks=[task_from_dict(t) for t in plan['training_tasks']]
    labels={tid:TaskLabel(v['task_id'],v['answer_id']) for tid,v in plan['training_labels'].items()}
    index={t.task_id:i for i,t in enumerate(tasks)}
    if len(index)!=120 or any(t.split!='train' for t in tasks):raise ValueError('Preparation requires 120 training tasks')
    for e in plan['selection']:
        if digest(tasks[index[e['task_id']]])!=e['input_hash'] or digest(labels[e['task_id']])!=e['label_hash']:
            raise ValueError('Preparation task/label mismatch')
    orders=[[index[tid] for tid in order] for order in plan['training']['agent_task_ids']]
    if len(orders)!=3 or any(sorted(o)!=list(range(120)) for o in orders):raise ValueError('Not one complete pass per agent')
    for seed,order in zip(config.seeds,orders):
        if order!=sorted(range(120),key=lambda j:(digest([seed,tasks[j].task_id]),tasks[j].task_id)):
            raise ValueError('Preparation order differs from frozen seeds')
    summary={'data_manifest_hash':config.data_manifest_hash,'design_hash':digest(plan),
             'total_optimizer_steps':90,'training_examples':360,'agent_task_ids':plan['training']['agent_task_ids']}
    return config,(tasks,labels,orders,summary)


def run_preparation_training(plan,root,cache_dir,*,persistent,resume=False,stop_after=None,timeout_seconds=120):
    root=Path(root);persistent=Path(persistent)
    if not 0<timeout_seconds<float('inf'):raise ValueError('Invalid storage timeout')
    if root.resolve()==persistent.resolve() or root.resolve() in persistent.resolve().parents or persistent.resolve() in root.resolve().parents:
        raise ValueError('Persistent destination must be outside scratch')
    config,prepared=training_inputs(plan)
    if root.exists() and not resume:raise ValueError('Preparation run exists; explicit resume required')
    if resume and canonical(read_json(root/'preparation_plan.json'))!=canonical(plan):raise ValueError('Preparation design changed')
    # Write design before engine initialization, but retain the engine new-directory guard.
    if not resume:root.mkdir(parents=True);write_json(root/'preparation_plan.json',plan)
    started=time.monotonic()
    result={'exit_code':0,'scientific_status':STATUS,'persistent_copy_verified':False}
    try:
        def checkpoint(step):
            if step%10==0:
                result['last_verified_snapshot']=str(sync_run(root,persistent,timeout_seconds=timeout_seconds))
        # Fresh root contains only the declared design, checked by the shared engine.
        status=_run_prepared_warmstart(config,prepared,root,Path(cache_dir),resume=resume,
            stop_after=stop_after,expected_base=plan['baseline_models']['base'],checkpoint_callback=checkpoint,
            scientific_status=STATUS,allow_prepared_directory=True)
        result['status']=status
    except (Exception,KeyboardInterrupt) as exc:
        result.update(exit_code=2,error=redact(str(exc)))
        write_json(root/'failure.json',{'type':type(exc).__name__,'message':redact(str(exc))})
    attempts=[read_json(p) for p in (root/'training-attempts').glob('*.json')]
    result['invocation_seconds']=time.monotonic()-started
    result['training_accounting']={'attempted_example_presentations':len(attempts),
        'completed_forward_backward':sum(a['forward_backward_complete'] for a in attempts),
        'attempted_sequence_tokens':sum(a['sequence_tokens'] for a in attempts),
        'generation_calls':0,'reference_scoring_forwards':0}
    write_json(root/f'invocations/{time.time_ns()}.json',result)
    output=root.parent/'bundles'/f'{root.name}-review-{time.time_ns()}.zip'
    result.update(review_bundle(root,output,result,kind='actor_preparation_review',scientific_status=STATUS))
    print(f"Local preparation ZIP: {output} SHA256: {result['sha256']}",flush=True)
    try:
        latest_checkpoint(root/'checkpoints',read_json(root/'run.json')['identity'])
        snapshot=sync_run(root,persistent,timeout_seconds=timeout_seconds)
        result.update(persistent_copy_verified=True,persistent_snapshot=str(snapshot))
        # Receipt is outside the snapshot so it cannot recursively assert its own hash.
        write_json(root/'durable_receipt.json',{'snapshot':str(snapshot),'identity':read_json(root/'run.json')['identity']})
        output=root.parent/'bundles'/f'{root.name}-handoff-{time.time_ns()}.zip'
        result.update(review_bundle(root,output,result,kind='actor_preparation_review',scientific_status=STATUS))
        target=persistent/'bundles'/output.name
        persist_bundle(output,target,result['sha256'],timeout_seconds=timeout_seconds)
        result['persistent_bundle']=str(target)
    except (Exception,KeyboardInterrupt) as exc:
        result.update(exit_code=2,persistence_error=redact(str(exc)))
    return result


def preparation_references(plan,root):
    """Only final, same-design exports may supply a probe checkpoint."""
    root=Path(root);config,prepared=training_inputs(plan)
    meta=read_json(root/'run.json');status=read_json(root/'status.json')
    if (canonical(read_json(root/'preparation_plan.json'))!=canonical(plan)
            or canonical(meta['recipe']['config'])!=canonical(config)
            or meta['recipe']['source']!=code_identity(Path(__file__).resolve().parents[3])
            or meta['plan']['design_hash']!=digest(plan)
            or meta['recipe_hash']!=digest(meta['recipe']) or meta['identity']['recipe_hash']!=meta['recipe_hash']
            or meta['identity']['model_snapshot']!=plan['baseline_models']['base']['snapshot']
            or meta['identity']['runtime_fingerprint']!=plan['baseline_models']['base']['runtime_fingerprint']
            or status['status']!='warmstart_updates_complete' or status['completed_steps']!=90
            or status['scientific_status']!=STATUS):
        raise ValueError('Require completed matching 90-step preparation')
    _,last=latest_checkpoint(root/'checkpoints',meta['identity'])
    refs=read_json(root/'references/references.json')
    if last['step']!=90 or refs['identity']!=meta['identity'] or refs['final_step']!=90:
        raise ValueError('Preparation checkpoint/reference mismatch')
    expected=[(agent,j+1,order[j*4:(j+1)*4]) for agent,order in enumerate(plan['training']['agent_task_ids']) for j in range(30)]
    logs=status['logs']
    if len(logs)!=90 or any((r['agent'],r['agent_step'],r['task_ids'],r['step'])!=(f'agent{a}',j,ids,i+1)
                            for i,(r,(a,j,ids)) in enumerate(zip(logs,expected))):
        raise ValueError('Preparation update log does not cover frozen schedule')
    recipe=SimpleNamespace(reference_manifest_hash=digest(refs),reference_hashes=tuple(r['sha256'] for r in refs['references']),
        reference_final_step=90,base_snapshot=plan['baseline_models']['base']['snapshot'],
        runtime_fingerprint=plan['baseline_models']['base']['runtime_fingerprint'])
    verify_references(root/'references',recipe)
    return recipe
