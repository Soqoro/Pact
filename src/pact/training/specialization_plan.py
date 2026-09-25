"""Frozen, opt-in specialization-only design. No model or GPQA data access."""
import dataclasses as dc
from pathlib import Path
from collections import Counter
from types import SimpleNamespace

from ..attacks import fixed_attack
from ..util import digest, read_json, canonical
from ..environment import code_identity
from .data import read_training_data
from .assignment_contrast import ARMS
from ..studies.gpqa_model import source_contract

RUN_ID='qwen3-specialization-contrast-001'
SEED=20260925
CONDITIONS=('clean','early')
SETTINGS={'gamma':1.,'tau':.2,'lambda_balance':.1,'lambda_spec':1.,'lambda_rx':0.,'lambda_dpo':0.,
          'transform':'eligible_cells_global_standardized','effective_batch':4,'passes':2,'max_updates_per_actor':32,
          'learning_rate':1e-5,'max_grad_norm':1.,'microbatch':1,'minimum_supported_tasks':8,'minimum_multi_tasks':8,
          'contrast_tolerance':1e-6,'candidates':4,'suffix_seeds':2}


def budgets(pairs=192):
    if type(pairs) is not int or not 0<=pairs<=192:raise ValueError('Invalid pair budget')
    return {'collect':{'generation_calls_upper_bound':1216,'generated_tokens_upper_bound':299008},
            'replay':{'generation_calls_upper_bound':pairs*16,'generated_tokens_upper_bound':pairs*3328},
            'evaluate_per_arm':{'generation_calls_upper_bound':512,'generated_tokens_upper_bound':106496},
            'total':{'generation_calls_upper_bound':1216+pairs*16+2048,'generated_tokens_upper_bound':299008+pairs*3328+425984},
            'answer_scoring_forwards':192,'packet_scoring_forwards':pairs,'updates_per_actor':32,'updates_per_arm':96,'total_updates':288}


def build_plan(tasks,labels,manifest,exposures,contract,source, *, synthetic=False):
    entries={e['task_id']:e for e in manifest['selected']};byid={t.task_id:t for t in tasks}
    if len(byid)!=len(tasks) or set(entries)!=set(byid):raise ValueError('Pool identity mismatch')
    if any(t.split!='train' or t.family not in ('arc_challenge','logiqa') for t in tasks):raise ValueError('Only ARC/LogiQA train sources allowed')
    excluded=set(exposures['task_ids'])
    if not excluded<=entries.keys():raise ValueError('Exposure IDs missing from source pool')
    groups={entries[k]['group_id'] for k in excluded};content={entries[k]['content_group'] for k in excluded}
    available=[t for t in tasks if t.task_id not in excluded and entries[t.task_id]['group_id'] not in groups and entries[t.task_id]['content_group'] not in content]
    selection=[]
    for family in ('arc_challenge','logiqa'):
        ranked=sorted((t for t in available if t.family==family),key=lambda t:(digest([SEED,'specialization-v1',entries[t.task_id]['group_id']]),t.task_id))
        if len(ranked)<32:raise ValueError(f'Insufficient fresh {family} groups: {len(ranked)}; need32')
        for i,t in enumerate(ranked[:32]):selection.append({**entries[t.task_id],'family':family,'partition':'fit' if i<16 else 'development'})
    if len({e['group_id'] for e in selection})!=64 or len({e['content_group'] for e in selection})!=64:raise ValueError('Repeated source groups')
    selection.sort(key=lambda e:(e['partition'],digest([SEED,e['task_id']])))
    # Freeze registry bytes without loading a model. Actual tokenizer count/cap is
    # checked before dispatch; token count is not used to choose payload or ID.
    counter=SimpleNamespace(count_tokens=lambda _:0)
    attacks={}
    for pos,e in enumerate(selection):
        task=byid[e['task_id']]
        attacks[task.task_id]={c:dc.asdict(fixed_attack(task,labels[task.task_id],c,pos,SEED,counter,256)) for c in CONDITIONS}
    return {'schema_version':1,'variant':'specialization_fixed_bank_v1','run_id':RUN_ID,'seed':SEED,
        'source':source,'settings':SETTINGS,'budget':budgets(),'selection':selection,'source_manifest':manifest,
        'source_and_exposure_manifest':exposures,'tasks':{e['task_id']:dc.asdict(byid[e['task_id']]) for e in selection},
        'labels':{e['task_id']:dc.asdict(labels[e['task_id']]) for e in selection},'attacks':attacks,
        'attack_policy':'fixed-pool-v1; node_seed(seed,task_id,fixed-pool); cap256; token counts verified on load',
        'frozen_arm':contract,'synthetic_fixture':synthetic,'arms':list(ARMS),'conditions':list(CONDITIONS),
        'answer_score_definition':'mean completion NLL of canonical answer JSON plus one EOS under original private prompt; no rationale prefix',
        'packet_score_definition':'mean full sampled correct completion NLL including sampled terminal EOS; prompt/padding masked',
        'reduction':'base=sum/(3*64); spec=sum(omega*R*packet_loss)/B; microbatch global coefficient *16; four rows/update',
        'receiver_loss':False,'dpo':False,'outer_refreshes':0,'final_test':False,'gpqa':False}


def plan_from_sources(data_dir,source_bundle,repo):
    tasks,labels,manifest,_=read_training_data(Path(data_dir))
    contract=source_contract(source_bundle)
    # Preparation/probe and receiver selections cover all intervening diagnostics;
    # warmstart tasks are retained inside the preparation selection.
    files=('actor_preparation_selection.json','receiver_feasibility_selection.json','receiver_supervision_selection.json')
    ids=set();receipts={}
    def visit(value):
        if isinstance(value,dict):
            if isinstance(value.get('task_id'),str):ids.add(value['task_id'])
            for v in value.values():visit(v)
        elif isinstance(value,list):
            for v in value:visit(v)
    for name in files:
        value=read_json(Path(repo)/'experiments'/name);visit(value);receipts[name]=digest(value)
    visit(contract['initialization_design']['selection']);visit(contract['initialization_design']['private_probe_requests'])
    exposure={'task_ids':sorted(ids),'selection_file_hashes':receipts,
        'ledger_review':'preparation120 includes engineering12; feasibility24 covers base/private/curated/preparation/prompt probes; receiver96 covers natural/controlled contexts',
        'limitation':'known IDs/group/content and existing lexical overlap audit; semantic paraphrases not certified'}
    return build_plan(tasks,labels,manifest,exposure,contract,code_identity(Path(repo)))
