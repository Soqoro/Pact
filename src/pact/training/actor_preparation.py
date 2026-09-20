"""Frozen plan for one 120-task warm start and fixed old-context probes."""
from collections import Counter
import dataclasses as dc
from pathlib import Path

from ..util import canonical,digest,read_json
from .bank import sha
from .data import read_training_data
from .curated_repair import CuratedRepairConfig,curated_repair_plan,curated_report
from .feasibility import read_review
from .private_control import PrivateControlConfig,private_control_plan


@dc.dataclass(frozen=True)
class ActorPreparationConfig:
    data_manifest_hash: str
    warmstart_data_manifest_hash: str
    receiver_bundle_sha256: str
    private_bundle_sha256: str
    curated_bundle_sha256: str
    schema_version: int = 1
    purpose: str = 'bounded_actor_preparation_120_design'
    selection_seed: int = 20260920

    def validate(self):
        for field in ('data_manifest_hash','warmstart_data_manifest_hash','receiver_bundle_sha256',
                      'private_bundle_sha256','curated_bundle_sha256'):
            sha(getattr(self,field))
        if (type(self.schema_version) is not int or self.schema_version!=1
                or self.purpose!='bounded_actor_preparation_120_design'
                or type(self.selection_seed) is not int or self.selection_seed!=20260920):
            raise ValueError('Unsupported actor preparation design')
        return self


def load_actor_preparation_config(path):
    return ActorPreparationConfig(**read_json(Path(path))).validate()


def select_preparation_tasks(tasks,manifest,warm_manifest,probes,seed):
    """Outcome-blind expansion retaining the original twelve warm-start tasks."""
    by_id={t.task_id:t for t in tasks};entries={e['task_id']:e for e in manifest['selected']}
    if len(by_id)!=len(tasks) or len(entries)!=len(tasks) or set(by_id)!=set(entries):
        raise ValueError('Duplicate or incomplete source task inventory')
    warm={e['task_id']:e for e in warm_manifest['selected']}
    blocked={field:{e[field] for e in probes} for field in ('task_id','group_id','content_group')}
    if len(warm)!=12 or len(probes)!=24 or len(blocked['task_id'])!=24:
        raise ValueError('Require twelve old tasks and 24 distinct probe tasks')
    for tid,e in entries.items():
        if by_id[tid].split!='train' or digest(by_id[tid])!=e['input_hash']:
            raise ValueError('Training task input changed or non-training split')
    for tid,e in warm.items():
        if tid not in entries or canonical(e)!=canonical(entries[tid]):
            raise ValueError('Old warm-start task differs from parent pool')
    def eligible(e):return all(e[f] not in blocked[f] for f in blocked)
    if any(not eligible(e) for e in warm.values()):raise ValueError('Old warm-start overlaps probe group')
    selected=[]
    for family in ('arc_challenge','logiqa'):
        retained=[e for tid,e in warm.items() if by_id[tid].family==family]
        if len(retained)!=6:raise ValueError('Original warm start must be 6/6 balanced')
        candidates=[e for tid,e in entries.items() if by_id[tid].family==family and tid not in warm and eligible(e)]
        candidates.sort(key=lambda e:(digest([seed,'actor-preparation-120',e['group_id']]),e['task_id']))
        if len(candidates)<54:raise ValueError('Insufficient disjoint training groups')
        selected.extend(retained+candidates[:54])
    selected.sort(key=lambda e:e['task_id'])
    if len({e['group_id'] for e in selected})!=120 or len({e['content_group'] for e in selected})!=120:
        raise ValueError('Selected training groups are not unique')
    return selected


def actor_preparation_plan(config,data_dir,warmstart_data_dir,receiver_bundle,private_bundle,curated_bundle):
    config.validate()
    tasks,labels,manifest,_=read_training_data(Path(data_dir))
    _,_,warm_manifest,_=read_training_data(Path(warmstart_data_dir))
    if digest(manifest)!=config.data_manifest_hash or digest(warm_manifest)!=config.warmstart_data_manifest_hash:
        raise ValueError('Actor preparation source manifest changed')
    for field in ('training_pool_hash','validation_pool_hash','overlap_audit_hash','sources'):
        if canonical(manifest[field])!=canonical(warm_manifest[field]):raise ValueError('Different source audits')
    curated=curated_repair_plan(CuratedRepairConfig(config.receiver_bundle_sha256,config.private_bundle_sha256),
                                receiver_bundle,private_bundle)
    private=read_review(private_bundle,config.private_bundle_sha256)
    parent=private_control_plan(PrivateControlConfig(**private['plan.json']['config']),receiver_bundle)
    if (parent['actor_recipe']['data_manifest_hash']!=config.data_manifest_hash
            or parent['actor_recipe']['warmstart_data_manifest_hash']!=config.warmstart_data_manifest_hash):
        raise ValueError('Probe source pool differs')
    completed=read_review(curated_bundle,config.curated_bundle_sha256)
    m=completed['manifest.json']
    if (canonical(completed['plan.json'])!=canonical(curated)
            or m['status']!='curated_repair_complete_local' or m['completed_records']!=32
            or m['recipe']['source']['dirty'] or m['recipe_hash']!=digest(m['recipe'])
            or m['recipe']['plan_hash']!=digest(curated)):
        raise ValueError('Require completed pinned curated baseline')
    report=curated_report(curated,[v for k,v in completed.items() if k.startswith('shards/')])
    saved=dict(completed['report.json']);saved.pop('generation_accounting',None)
    if canonical(report)!=canonical(saved) or not report['complete']:raise ValueError('Curated report mismatch')
    selection=select_preparation_tasks(tasks,manifest,warm_manifest,parent['selection']['selected'],config.selection_seed)
    ids=[e['task_id'] for e in selection];by_id={t.task_id:t for t in tasks}
    training={'initialization':'fresh adapters on pinned base; no continuation from old exports',
        'seeds':[1729,1730,1731],'steps_per_agent':30,'effective_batch':4,'microbatch':1,
        'epochs_per_agent':1,'rank':16,'alpha':32,'target_modules':['q_proj','v_proj'],
        'learning_rate':1e-5,'weight_decay':0.,'max_grad_norm':1.,'dropout':0.,
        'optimizer':'AdamW; betas=(0.9,0.999); eps=1e-8; foreach=False; constant LR; no scheduler',
        'precision':'BF16 backbone, FP32 LoRA parameters; one CUDA GPU','context_limit':4096,'thinking':False,
        'target':'clean canonical answer-only JSON plus EOS; mean completion-token NLL',
        'agent_task_ids':[sorted(ids,key=lambda tid:(digest([seed,tid]),tid)) for seed in (1729,1730,1731)]}
    return {'status':'actor_preparation_plan_only','execution_implemented':True,'gpu_verified':False,
        'config':dc.asdict(config),'config_hash':digest(config),'selection':selection,'selection_hash':digest(selection),
        'family_counts':dict(Counter(by_id[tid].family for tid in ids)),
        'retained_warmstart_tasks':12,'additional_tasks':108,'excluded_probe_tasks':24,
        'training':training,'training_recipe_hash':digest(training),
        'training_tasks':[dc.asdict(by_id[tid]) for tid in ids],
        'training_labels':{tid:dc.asdict(labels[tid]) for tid in ids},
        'private_probe_requests':parent['requests'],'private_probe_requests_hash':parent['requests_hash'],
        'receiver_contexts':curated['contexts'],'receiver_contexts_hash':curated['contexts_hash'],
        'receiver_prefixes':completed['prefixes.json'],
        'baseline_models':curated['models'],'baseline_private_summary':private['report.json']['summary'],
        'baseline_receiver_report':report,
        'budget':{'training_tasks':120,'training_example_presentations':360,'optimizer_steps':90,
                  'private_calls':72,'revision_calls':32,'generation_calls_upper_bound':104,
                  'generated_tokens_upper_bound':26624,'input_tokens_upper_bound':399360,
                  'training_sequence_tokens_upper_bound':1474560,'reference_scoring_forwards':0},
        'training_executed':False,'model_calls_executed':0,'training_pairs_exported':False,'full_pact_ready':False,
        'scope':'larger clean-answer preparation bundle; fixed training probes, no generalization or full PACT claim'}
