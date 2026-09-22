"""Thin staged entry point for the bounded receiver-supervision study.

python -m pact.training.receiver_study --help
No model is loaded for planning, reporting, exporting or restoring.
"""
import argparse
from collections import Counter
import dataclasses as dc
import gc
import json
from pathlib import Path
from types import SimpleNamespace
import time

from ..artifacts import ShardStore, run_lock, sync_run
from ..attacks import fixed_attack
from ..environment import code_identity, versions, runtime_fingerprint
from ..evaluation import score, aggregate, paired_bootstrap
from ..protocol import Protocol, private_prompt, revision_prompt
from ..schemas import task_from_dict, TaskLabel, Message
from ..storage import persist_bundle, storage_operation
from ..util import canonical, digest, read_json, write_json, node_seed, redact
from .colab import review_bundle
from .collection_config import CollectionRuntime
from .preparation_runner import preparation_references
from .receiver import JournalBackend, inspect_journal
from .receiver_supervision import (ARMS, ReceiverSupervisionConfig, load_rx_config, study_plan,
                                  build_contexts, prefix_tokens, packet_from_dict)
from .receiver_supervision_train import training_examples, train_focal, token_loss
from .scoring import CollectionBackend, verify_references, scoring_adapter

STATUS = 'training_only_receiver_supervision_feasibility'


def messages(value):
    return tuple(Message(m['role'], m['content']) for m in value)


def peer_withheld(record, task):
    # Keep the exact same system instruction, trusted task and own packet.
    return revision_prompt(task, packet_from_dict(record['own_saved']), (), '')


def assert_contexts(root, plan):
    records = ShardStore(root/'contexts').records()
    expected = build_contexts(plan, records)
    if canonical(read_json(root/'contexts.json')) != canonical(expected):
        raise ValueError('Frozen contexts changed from their sampled source records')
    contracts=read_json(root/'target_masks.json')
    ids={r['record_id'] for p in expected['partitions'].values() for r in p['records']}
    if set(contracts)!=ids:raise ValueError('Incomplete target-contract preflight')
    for part in expected['partitions'].values():
        for row in part['records']:
            target=contracts[row['record_id']]
            if (target['output_prefix']!=row['output_prefix'] or target['eos_supervised'] or target['is_generated_packet']
                    or not any(target['score_mask']) or len(target['prompt_ids'])+256>4096):
                raise ValueError('Target-contract preflight mismatch')
    if expected['status'] != 'ready':
        raise ValueError('insufficient_context_support: no training or held-out inference authorized by this design')
    return json.loads(canonical(expected))


def initial_recipe(plan, initialization_root):
    recipe = preparation_references(plan['initialization_design'], initialization_root)
    if recipe.reference_manifest_hash != digest(plan['initialization_references']):
        raise ValueError('Prepared initialization differs from reviewed training bundle')
    return recipe


def arm_recipe(root, plan, arm, initial):
    if arm == 'frozen': return initial
    status = read_json(root/'training'/arm/'status.json')
    if not status.get('complete'): raise ValueError('Both trained arms must finish before held-out evaluation')
    refs = status['references']; identity = refs['identity']
    if identity['arm'] != arm or identity['study_hash'] != read_json(root/'state.json')['study_hash']:
        raise ValueError('Arm checkpoint/study mismatch')
    recipe = SimpleNamespace(reference_hashes=tuple(r['sha256'] for r in refs['references']),
                             reference_manifest_hash=digest(refs), reference_final_step=refs['final_step'],
                             base_snapshot=initial.base_snapshot, runtime_fingerprint=initial.runtime_fingerprint)
    verify_references(root/'training'/arm/'references', recipe)
    for i in range(3):
        if i != plan['config']['focal_agent'] and recipe.reference_hashes[i] != initial.reference_hashes[i]:
            raise ValueError('Nonfocal checkpoint differs between arms')
    return recipe


def load_backend(plan, references, recipe, cache):
    runtime = CollectionRuntime(digest(plan), plan['config']['generation_seed'])
    backend = CollectionBackend(runtime, cache, references, recipe)
    if (backend.base_identity['snapshot'] != plan['model']['snapshot'] or
            backend.base_identity['runtime_fingerprint'] != plan['model']['runtime_fingerprint']):
        raise ValueError('Model/runtime differs from prespecified prepared actor')
    return runtime, backend


class Recovery:
    def __init__(self, root, persistent):
        self.root, self.persistent = Path(root), Path(persistent)
    def mark(self, safe):
        state = read_json(self.root/'state.json')
        if not safe and not state['recovery_safe']: return
        state['recovery_safe'] = safe
        write_json(self.root/'state.json', state)
        # Unsafe durable marker precedes every new generation/update/scoring batch.
        # An old safe snapshot must never authorize replay after a lost runtime.
        sync_run(self.root, self.persistent, timeout_seconds=120)
    def before(self): self.mark(False)
    def after(self): self.mark(True)


def validate_local_recovery(root, plan):
    """Only scratch with every attempted operation accounted for can resume locally."""
    from .checkpoints import latest_checkpoint
    for stage in (root/'contexts', *(root/'evaluation'/a for a in ARMS)):
        inspect_journal(stage, plan['budget'])
        for intent in (stage/'ce-intents').glob('*.json'):
            if ShardStore(stage/'ce').read(intent.stem) is None:
                raise ValueError('Unresolved scoring attempt')
    for arm in ('task_sft','receiver_sft'):
        stage=root/'training'/arm
        if (stage/'run.json').exists():
            _,checkpoint=latest_checkpoint(stage/'checkpoints',read_json(stage/'run.json')['identity'])
            if (stage/'update_attempt.json').exists() and read_json(stage/'update_attempt.json')['step']>checkpoint['step']:
                raise ValueError('Unresolved optimizer attempt')


def collect(plan, backend, runtime, root, recovery, stop_after=None):
    config = ReceiverSupervisionConfig(**plan['config'])
    stage = root/'contexts'
    budget = {'generation_calls_upper_bound':plan['budget']['collection_calls_upper_bound'],
              'generated_tokens_upper_bound':plan['budget']['collection_calls_upper_bound']*256}
    journal = JournalBackend(backend, stage, budget, stop_after=stop_after, before_new=recovery.before)
    protocol = Protocol(runtime, journal); store = ShardStore(stage)
    for entry in plan['selection']:
        task = task_from_dict(plan['tasks'][entry['task_id']]); key = digest(['source', task.task_id])
        journal.begin_record(key)
        # Replay cached calls to revalidate every record against the current exact request.
        private = [protocol.packet(task, i, 'private', private_prompt(task, ''),
                    node_seed(config.generation_seed, task.task_id, 'source-private', i)) for i in range(3)]
        alternatives = [protocol.packet(task, config.focal_agent, 'private', private_prompt(task, ''),
                        node_seed(config.generation_seed, task.task_id, 'donor', config.focal_agent, j))
                        for j in range(config.donor_draws)]
        row = {'schema_version':1, 'work_id':key, 'task_id':task.task_id,
               'private':[dc.asdict(p) for p in private], 'alternatives':[dc.asdict(p) for p in alternatives],
               'donor_actor_prespecified':config.focal_agent, 'all_initials_frozen_before_delivery':True}
        store.put(key, row); recovery.after()
    result = build_contexts(plan, store.records())
    write_json(root/'contexts.json', result)
    contracts = {}
    for partition in result['partitions'].values():
        for record in partition['records']:
            task=task_from_dict(plan['tasks'][record['task_id']])
            tokens=prefix_tokens(backend.tokenizer,record['messages'],record['target_answer'],tuple(o.answer_id for o in task.options))
            if len(tokens['prompt_ids'])+256>4096: raise ValueError('Receiver context cannot fit unchanged inference limits')
            contracts[record['record_id']]=tokens
    write_json(root/'target_masks.json',contracts)
    write_json(root/'model_identity.json',backend.identity)
    backend.assert_unchanged(); recovery.after()
    return {'status':result['status'], 'support':{p:{k:v for k,v in r.items() if k!='records'}
                                                for p,r in result['partitions'].items()}}


def score_prefix(backend, tokenized, focal):
    import torch
    with scoring_adapter(backend.model, f'agent{focal}'), torch.no_grad():
        value = float(token_loss(backend.model, tokenized))
    backend.assert_unchanged()
    return value


def evaluate(plan, contexts, backend, runtime, root, arm, recovery, stop_after=None):
    cfg = ReceiverSupervisionConfig(**plan['config']); stage = root/'evaluation'/arm
    rows = contexts['partitions']['heldout']['records']
    smoke_entries = sorted([e for e in plan['selection'] if e['partition']=='heldout'],
                           key=lambda e:digest([cfg.selection_seed, 'smoke', e['group_id']]))[:cfg.smoke_tasks]
    calls = len(rows)*2+cfg.heldout_tasks+cfg.smoke_tasks*14
    finals = cfg.smoke_tasks*2
    budget = {'generation_calls_upper_bound':calls, 'generated_tokens_upper_bound':(calls-finals)*256+finals*64}
    journal = JournalBackend(backend, stage, budget, stop_after=stop_after, before_new=recovery.before)
    protocol = Protocol(runtime, journal); store = ShardStore(stage); ce_store = ShardStore(stage/'ce')
    for record in rows:
        task = task_from_dict(plan['tasks'][record['task_id']]); gold = record['target_answer']
        for condition in ('full', 'peer_withheld'):
            key = digest(['receiver', record['record_id'], condition]); journal.begin_record(key)
            prompt = messages(record['messages']) if condition=='full' else peer_withheld(record, task)
            seed = node_seed(cfg.generation_seed, record['record_id'], 'heldout-receiver')
            packet = protocol.packet(task, cfg.focal_agent, 'revision', prompt, seed)
            row = {'schema_version':1, 'work_id':key, 'kind':'receiver', 'record_id':record['record_id'], 'task_id':task.task_id,
                   'family':task.family, 'source':record['source'], 'stratum':record['stratum'], 'condition':condition,
                   'arm':arm, 'packet':dc.asdict(packet), 'correct':packet.parser_status=='ok' and packet.answer_id==gold,
                   'match':{'task_id':task.task_id, 'record_id':record['record_id'], 'context_hash':digest(prompt),
                            'actor':cfg.focal_agent, 'seed':seed, 'decoding':packet.call.parameters_json},
                   'checkpoint':backend.identity}
            store.put(key, row)
            tokenized = prefix_tokens(backend.tokenizer, [dc.asdict(m) for m in prompt], gold,
                                      tuple(o.answer_id for o in task.options))
            ce_key = digest([key, backend.identity, digest(tokenized)])
            if ce_store.path(ce_key).exists():
                ce = ce_store.read(ce_key)
                if ce['tokens'] != json.loads(canonical(tokenized)): raise ValueError('Scoring cache changed')
            else:
                intent_path = stage/'ce-intents'/f'{ce_key}.json'
                if intent_path.exists(): raise ValueError('Unresolved teacher-forced attempt; no silent retry')
                recovery.before(); write_json(intent_path, {'key':ce_key, 'checkpoint':backend.identity})
                ce = {'schema_version':1, 'work_id':ce_key, 'generation_key':key, 'tokens':tokenized,
                      'answer_nll':score_prefix(backend, tokenized, cfg.focal_agent), 'checkpoint':backend.identity}
                ce_store.put(ce_key, ce)
            recovery.after()
    for entry in [e for e in plan['selection'] if e['partition']=='heldout']:
        task = task_from_dict(plan['tasks'][entry['task_id']]); key = digest(['private', task.task_id])
        journal.begin_record(key)
        packet = protocol.packet(task, cfg.focal_agent, 'private', private_prompt(task, ''),
                                 node_seed(cfg.generation_seed, task.task_id, 'heldout-private'))
        store.put(key, {'schema_version':1, 'work_id':key, 'kind':'private', 'arm':arm, 'task_id':task.task_id, 'family':task.family,
                        'packet':dc.asdict(packet), 'correct':packet.parser_status=='ok' and packet.answer_id==plan['labels'][task.task_id]['answer_id'],
                        'checkpoint':backend.identity})
        recovery.after()
    for position, entry in enumerate(smoke_entries):
        task = task_from_dict(plan['tasks'][entry['task_id']]); label = TaskLabel(task.task_id, plan['labels'][task.task_id]['answer_id'])
        for condition in ('clean', 'exchange'):
            key = digest(['natural-team', task.task_id, condition]); journal.begin_record(key)
            attack = fixed_attack(task, label, condition, position, cfg.generation_seed, journal, runtime.limits.payload)
            trajectory = protocol.run(task, 'debate', attack)
            store.put(key, {'schema_version':1, 'work_id':key, 'kind':'natural_team', 'arm':arm, 'task_id':task.task_id, 'condition':condition,
                            'trajectory':dc.asdict(trajectory), 'evaluation':score(trajectory, label), 'checkpoint':backend.identity,
                            'correct':trajectory.final.parser_status=='ok' and trajectory.final.answer_id==label.answer_id})
            recovery.after()
    backend.assert_unchanged()
    result = {'complete':True, 'arm':arm, 'checkpoint':backend.identity, 'records':len(store.records()),
              'committed_calls':len(journal.results), 'teacher_forced_forwards':len(ce_store.records())}
    write_json(stage/'status.json', result); recovery.after(); return result


def summarize(rows):
    tasks = sorted({r['task_id'] for r in rows})
    task_rates = [sum(r['correct'] for r in rows if r['task_id']==t)/sum(r['task_id']==t for r in rows) for t in tasks]
    counts = Counter(r['packet']['parser_status'] for r in rows if 'packet' in r)
    return {'contexts':len(rows), 'unique_tasks':len(tasks), 'correct':sum(r['correct'] for r in rows),
            'task_mean_accuracy':sum(task_rates)/len(tasks) if tasks else None, 'parser_counts':dict(counts),
            'abstentions':counts['abstention'],'malformed':counts['malformed'],'truncated':counts['length'],
            'invalid_answer':counts['invalid_answer'],'context_overflow':counts['context_overflow'],
            'wrong_valid':sum(r.get('packet',{}).get('parser_status')=='ok' and not r['correct'] for r in rows)}


def validate_receiver_match(left, right, left_checkpoint, right_checkpoint):
    if left['checkpoint'] != left_checkpoint or right['checkpoint'] != right_checkpoint:
        raise ValueError('Matched record checkpoint differs from declared arm')
    if left['match'] != right['match']:
        raise ValueError('Task/context/role/seed/decoding mismatch')


def audit_evaluation_row(plan, contexts, row, checkpoint):
    """Recompute free-generation correctness and receiver identities for reporting."""
    from ..parsing import parse_answer
    from .receiver import call_from_dict
    if row['checkpoint'] != checkpoint:
        raise ValueError('Record checkpoint differs from arm checkpoint')
    task=task_from_dict(plan['tasks'][row['task_id']]); gold=plan['labels'][task.task_id]['answer_id']
    allowed=tuple(o.answer_id for o in task.options); cfg=ReceiverSupervisionConfig(**plan['config'])
    if row['kind']=='natural_team':
        raw=row['trajectory']
        if raw['task']!=plan['tasks'][task.task_id] or raw['method']!='debate' or raw['snapshot']!=checkpoint['snapshot']:
            raise ValueError('Natural-team task/protocol/checkpoint mismatch')
        def packet(p):
            parsed=parse_answer(p['raw'],allowed,final=p['agent']==-1,stop_reason=p['call']['stop_reason'])
            if parsed!=(p['answer_id'],p['explanation'],p['parser_status']):raise ValueError('Natural-team parse mismatch')
            return SimpleNamespace(**p)
        trajectory=SimpleNamespace(**{**raw,'task':task,'private':tuple(packet(p) for p in raw['private']),
            'revised':tuple(packet(p) for p in raw['revised']),'final':packet(raw['final']),
            'delivered':tuple(SimpleNamespace(**m) for m in raw['delivered']),
            'attack':SimpleNamespace(**raw['attack']),'calls':tuple(call_from_dict(c) for c in raw['calls'])})
        if score(trajectory,TaskLabel(task.task_id,gold))!=row['evaluation'] or row['correct']!=row['evaluation']['success']:
            raise ValueError('Natural-team evaluation changed')
        return
    packet=row['packet'];call=call_from_dict(packet['call'])
    parsed=parse_answer(packet['raw'],allowed,stop_reason=call.stop_reason)
    if parsed!=(packet['answer_id'],packet['explanation'],packet['parser_status']) or row['correct']!=(parsed[2]=='ok' and parsed[0]==gold):
        raise ValueError('Generation parse/correctness mismatch')
    if row['kind']=='receiver':
        records={r['record_id']:r for r in contexts['partitions']['heldout']['records']}
        record=records[row['record_id']]
        if any(row[k]!=record[k] for k in ('task_id','source','stratum')):raise ValueError('Receiver cohort mismatch')
        prompt=messages(record['messages']) if row['condition']=='full' else peer_withheld(record,task)
        seed=node_seed(cfg.generation_seed,record['record_id'],'heldout-receiver');phase='revision'
        match={'task_id':task.task_id,'record_id':record['record_id'],'context_hash':digest(prompt),
               'actor':cfg.focal_agent,'seed':seed,'decoding':call.parameters_json}
        if row['match']!=match:raise ValueError('Receiver comparison identity changed')
    elif row['kind']=='private':
        prompt=private_prompt(task,'');seed=node_seed(cfg.generation_seed,task.task_id,'heldout-private');phase='private'
    else:raise ValueError('Unknown evaluation record kind')
    parameters=json.loads(call.parameters_json)
    if (call.messages!=prompt or call.seed!=seed or call.actor!=f'agent-{cfg.focal_agent}' or call.phase!=phase
            or call.snapshot!=checkpoint['snapshot'] or any(parameters.get(k)!=v for k,v in
                (('max_new_tokens',256),('do_sample',True),('temperature',.7),('top_p',.8),('top_k',20)))):
        raise ValueError('Evaluation prompt/seed/role/decoding/checkpoint changed')


def report(root):
    root = Path(root); plan = read_json(root/'plan.json'); contexts = assert_contexts(root, plan)
    training={a:read_json(root/'training'/a/'status.json') for a in ('task_sft','receiver_sft')}
    if any(not s.get('complete') or not s.get('training_executed') for s in training.values()):raise ValueError('Both trained arms must complete before reporting')
    initial_hashes=[s.get('initial_weight_hash') for s in training.values()]
    if any(not isinstance(h,str) or len(h)!=64 for h in initial_hashes) or len(set(initial_hashes))!=1:
        raise ValueError('Training arms did not declare identical initial adapter bytes')
    outputs = {}; paired = {}; all_rows = {}
    for arm in ARMS:
        status = read_json(root/'evaluation'/arm/'status.json')
        if not status['complete']: raise ValueError('Incomplete arm; missing pairs remain missing')
        rows = ShardStore(root/'evaluation'/arm).records(); ce = ShardStore(root/'evaluation'/arm/'ce').records()
        ce_by_key={r['generation_key']:r for r in ce}
        if len(ce_by_key)!=len(ce) or set(ce_by_key)!={r['work_id'] for r in rows if r['kind']=='receiver'}:raise ValueError('Missing/duplicate teacher-forced diagnostics')
        all_rows[arm] = rows
        if len({r['work_id'] for r in rows}) != len(rows):raise ValueError('Duplicate evaluation record')
        for row in rows:
            audit_evaluation_row(plan,contexts,row,status['checkpoint'])
        outputs[arm] = {'checkpoint':status['checkpoint'], 'receiver':{}, 'private':summarize([r for r in rows if r['kind']=='private']),
                        'natural_team':{c:aggregate([r['evaluation'] for r in rows if r['kind']=='natural_team' and r['condition']==c]) for c in ('clean','exchange')},
                        'per_task':rows, 'teacher_forced_answer_nll':ce}
        for condition in ('full','peer_withheld'):
            for stratum in ('hold','repair'):
                for source in ('all','natural','curated'):
                    cohort = [r for r in rows if r['kind']=='receiver' and r['condition']==condition and r['stratum']==stratum and (source=='all' or r['source']==source)]
                    summary = summarize(cohort)
                    by_task={}
                    for r in cohort:by_task.setdefault(r['task_id'],[]).append(ce_by_key[r['work_id']]['answer_nll'])
                    summary['teacher_forced_answer_nll_task_mean']=(sum(sum(v)/len(v) for v in by_task.values())/len(by_task)) if by_task else None
                    summary['teacher_forced_scored_tokens']=sum(sum(ce_by_key[r['work_id']]['tokens']['score_mask']) for r in cohort)
                    if stratum=='hold': summary['task_mean_harm'] = 1-summary['task_mean_accuracy'] if cohort else None
                    outputs[arm]['receiver'][f'{condition}/{stratum}/{source}'] = summary
        paired[arm] = {r['work_id']:r for r in rows if r['kind']=='receiver'}
    contrasts = {}
    for left,right in (('frozen','task_sft'),('frozen','receiver_sft'),('task_sft','receiver_sft')):
        if paired[left].keys()!=paired[right].keys(): raise ValueError('Missing matched evaluation pairs')
        transitions = Counter()
        for key in paired[left]:
            a,b=paired[left][key],paired[right][key]
            validate_receiver_match(a,b,outputs[left]['checkpoint'],outputs[right]['checkpoint'])
            transitions[f'{a["correct"]}->{b["correct"]}']+=1
        cohorts={}
        for condition in ('full','peer_withheld'):
            for stratum in ('hold','repair'):
                pairs={}
                selected=[k for k,r in paired[left].items() if r['condition']==condition and r['stratum']==stratum]
                counts=Counter()
                for key in selected:
                    a,b=paired[left][key],paired[right][key]
                    pairs.setdefault(a['task_id'],[]).append((float(b['correct']),float(a['correct'])))
                    counts[f'{a["correct"]}->{b["correct"]}']+=1
                cohorts[f'{condition}/{stratum}']={'transitions':dict(counts),'task_cluster_difference':paired_bootstrap(pairs)}
        contrasts[f'{left}->{right}'] = {'transitions':dict(transitions),'cohorts':cohorts}
    other_contrasts={}
    for left,right in (('frozen','task_sft'),('frozen','receiver_sft'),('task_sft','receiver_sft')):
        for kind in ('private','natural_team'):
            a={r['work_id']:r for r in all_rows[left] if r['kind']==kind}
            b={r['work_id']:r for r in all_rows[right] if r['kind']==kind}
            if a.keys()!=b.keys():raise ValueError('Missing private/team comparison pair')
            transitions=Counter()
            for key,x in a.items():
                y=b[key]
                if kind=='private':
                    cx,cy=x['packet']['call'],y['packet']['call']
                    if any(cx[k]!=cy[k] for k in ('messages','seed','actor','phase','parameters_json')):raise ValueError('Unmatched private control')
                else:
                    tx,ty=x['trajectory'],y['trajectory']
                    if any(tx[k]!=ty[k] for k in ('task','method','condition','seed','attack')):raise ValueError('Unmatched natural-team attack or seed')
                    if [(c['seed'],c['actor'],c['phase'],c['parameters_json']) for c in tx['calls']]!=[(c['seed'],c['actor'],c['phase'],c['parameters_json']) for c in ty['calls']]:raise ValueError('Unmatched team node seeds or decoding')
                transitions[f'{x["correct"]}->{y["correct"]}']+=1
            other_contrasts[f'{left}->{right}/{kind}']=dict(transitions)
    peer_effects={}
    for arm in ARMS:
        controls={(r['record_id'],r['condition']):r for r in paired[arm].values()}
        peer_effects[arm]={}
        for stratum in ('hold','repair'):
            pairs={};transitions=Counter()
            for (rid,condition),row in controls.items():
                if condition!='full' or row['stratum']!=stratum:continue
                neutral=controls[(rid,'peer_withheld')]
                if any(row['match'][k]!=neutral['match'][k] for k in ('task_id','actor','seed','decoding')):raise ValueError('Unmatched peer control')
                pairs.setdefault(row['task_id'],[]).append((float(row['correct']),float(neutral['correct'])))
                transitions[f'{neutral["correct"]}->{row["correct"]}']+=1
            peer_effects[arm][stratum]={'peer_withheld_to_full':dict(transitions),'task_cluster_difference':paired_bootstrap(pairs)}
    generation = []; teacher=0
    for stage in (root/'contexts', *(root/'evaluation'/arm for arm in ARMS)):
        intents, calls = inspect_journal(stage, plan['budget']); generation.extend(calls.values())
        teacher += len(ShardStore(stage/'ce').records())
    if (len(generation)>plan['budget']['generation_calls_upper_bound'] or
        sum(r['intent']['max_tokens'] for r in generation)>plan['budget']['generated_tokens_upper_bound'] or
        teacher>plan['budget']['evaluation_teacher_forced_forwards_upper_bound']):raise ValueError('Global generation/scoring budget exceeded')
    result = {'schema_version':1, 'scientific_status':('mock_only' if all(outputs[a]['checkpoint'].get('backend')=='mock' for a in ARMS) else STATUS), 'full_pact_ready':False,
              'claim':'training-only feasibility; no final-test or PACT-improvement claim',
              'uncertainty':'One training seed; small task denominators. Descriptive, not powered efficacy evidence.',
              'history':'Receiver own packets and donors are frozen initialization histories, not updated-team trajectories.',
              'readiness':{'supervised_data_valid':True,'supervised_update_executed':True,'optional_dpo':'disabled',
                           'specialization_integration':'deferred','full_joint_training':False,'scientific_efficacy':'not_established'},
              'arms':outputs, 'paired_receiver_transitions':contrasts,'paired_peer_effects':peer_effects,'paired_private_team_transitions':other_contrasts,
              'generation_accounting':{'attempted_calls':len(generation), 'committed_calls':len(generation),
                 'input_tokens':sum(r['call']['input_tokens'] for r in generation),
                 'output_tokens':sum(r['call']['output_tokens'] for r in generation),
                 'reserved_output_tokens':sum(r['intent']['max_tokens'] for r in generation)},
              'teacher_forced_forwards':teacher, 'budget':plan['budget'],
              'training':training,
              'compute_units':None,
              'support':{p:{k:v for k,v in s.items() if k!='records'} for p,s in contexts['partitions'].items()}}
    write_json(root/'report.json', result); return result


def export(root, persistent, outcome):
    root=Path(root); state=read_json(root/'state.json')
    write_json(root/'CODEX_HANDOFF.json', {'variant':'receiver_supervision_v1', 'study_hash':state['study_hash'],
        'scientific_status':STATUS, 'full_pact_ready':False, 'outcome':outcome,
        'checkpoint_paths':{a:str(root/'training'/a/'references') for a in ('task_sft','receiver_sft')},
        'initialization_path':state['initialization_path'], 'persistent_root':str(persistent),
        'review_contains_tensor_weights':False, 'resume_requires_verified_full_snapshot':True})
    (root/'CODEX_HANDOFF.md').write_text(
        '# Receiver supervision review\n\nTraining-only feasibility; GPU behavior is established only by returned artifacts.\n'
        'Review ZIP omits tensors; restore the verified full snapshot to resume.\n'
        f'Full durable root: `{persistent}`. Initialization: `{state["initialization_path"]}`.\n'
        'Frozen histories are from initialization; natural-team results are separate. DPO is disabled.\n'
        'See plan.json, target_masks.json, training/*/examples.json, status.json, report.json and resource files.\n', encoding='utf-8')
    bundle=review_bundle(root, root.parent/'bundles'/f'{root.name}-{time.time_ns()}.zip', outcome,
                         kind='receiver_supervision_review', scientific_status=STATUS,max_metadata_bytes=256*1024**2,include_markdown=True)
    print('Local review ZIP:', canonical(bundle), flush=True)
    snapshot=sync_run(root, Path(persistent), timeout_seconds=120)
    handoff=read_json(root/'CODEX_HANDOFF.json');handoff['verified_full_snapshot']=str(snapshot)
    write_json(root/'CODEX_HANDOFF.json',handoff)
    with (root/'CODEX_HANDOFF.md').open('a',encoding='utf-8') as stream:
        stream.write(f'\nVerified full checkpoint snapshot: `{snapshot}`.\n')
    bundle=review_bundle(root,root.parent/'bundles'/f'{root.name}-handoff-{time.time_ns()}.zip',outcome,
                         kind='receiver_supervision_review',scientific_status=STATUS,
                         max_metadata_bytes=256*1024**2,include_markdown=True)
    durable=Path(persistent)/'bundles'/Path(bundle['path']).name
    persist_bundle(Path(bundle['path']), durable, bundle['sha256'], timeout_seconds=120)
    return {**bundle, 'persistent_snapshot':str(snapshot), 'persistent_bundle':str(durable)}


def read_receiver_supervision_review(bundle, expected_sha):
    from .feasibility import read_review
    content=read_review(bundle,expected_sha,max_members=10000,max_bytes=256*1024**2,allow_text=True)
    if content['HANDOFF.json']['kind']!='receiver_supervision_review':raise ValueError('Wrong study review kind')
    if content['plan.json']['variant']!='receiver_supervision_v1':raise ValueError('Wrong study variant')
    return content


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('plan','contexts','train','evaluate','report','export','restore'))
    for name in ('config','data-dir','initialization-bundle','initialization-root','run-dir','persistent'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path, default=Path('/content/pact-scratch/cache'))
    parser.add_argument('--selection', type=Path)
    parser.add_argument('--arm', choices=ARMS)
    parser.add_argument('--snapshot', type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--stop-after', type=int)
    args=parser.parse_args(argv); root=args.run_dir
    if args.stop_after is not None and args.stop_after<1: parser.error('--stop-after must be positive')
    if args.stage=='restore':
        if args.snapshot is None: parser.error('--snapshot is required')
        root.parent.mkdir(parents=True, exist_ok=True)
        print(canonical(storage_operation('receiver-supervision-restore',args.snapshot,root,timeout_seconds=600)));return
    config=load_rx_config(args.config)
    plan=study_plan(config,args.data_dir,args.initialization_bundle,args.selection)
    # Serialize dataclass/tuple values once, so disk comparisons have identical types.
    plan=json.loads(canonical(plan))
    recipe={'plan':plan, 'source':code_identity(Path(__file__).resolve().parents[3])}
    identity=digest(recipe)
    if args.stage=='plan' and not args.execute:
        print(canonical({'status':'plan_only','study_hash':identity,'budget':plan['budget'],
                         'selection_hash':plan['selection_hash'], 'training_executed':False}));return
    if args.stage in ('contexts','train','evaluate') and not args.execute:
        parser.error('GPU stages require --execute; plan first')
    root.mkdir(parents=True, exist_ok=True)
    with run_lock(root):
        if (root/'state.json').exists():
            state=read_json(root/'state.json')
            if state['study_hash']!=identity or read_json(root/'plan.json')!=plan:
                raise ValueError('Source/config/data/split/initialization changed; resume rejected')
            if not state['recovery_safe']:
                # Local journals/checkpoints can establish a boundary; runtime restore cannot.
                validate_local_recovery(root, plan)
                Recovery(root,args.persistent).after()
        else:
            if args.stage!='plan': raise ValueError('Run plan --execute to freeze the study before collection')
            write_json(root/'plan.json',plan);write_json(root/'recipe.json',recipe)
            write_json(root/'state.json',{'study_hash':identity,'recovery_safe':True,
                       'initialization_path':str(args.initialization_root)})
        recovery=Recovery(root,args.persistent); outcome={}
        try:
            if args.stage=='plan':
                recovery.after();outcome={'status':'plan_frozen','study_hash':identity,'budget':plan['budget']}
            elif args.stage=='report': outcome={'status':'report_complete','summary_path':str(root/'report.json'),'accounting':report(root)['generation_accounting']}
            elif args.stage=='export': outcome={'status':'review_export','recovery_safe':True}
            else:
                initial=initial_recipe(plan,args.initialization_root)
                if args.stage in ('train','evaluate'): contexts=assert_contexts(root,plan)
                if args.stage=='train' and args.arm not in ('task_sft','receiver_sft'):parser.error('train requires --arm task_sft or receiver_sft')
                if args.stage=='evaluate':
                    if args.arm not in ARMS:parser.error('evaluate requires --arm')
                    for arm in ('task_sft','receiver_sft'):arm_recipe(root,plan,arm,initial)
                recipe_arm=arm_recipe(root,plan,args.arm,initial) if args.stage=='evaluate' else initial
                references=(root/'training'/args.arm/'references') if args.stage=='evaluate' and args.arm!='frozen' else args.initialization_root/'references'
                write_json(root/'environment.json',{'packages':versions(),'runtime_fingerprint':runtime_fingerprint(),'compute_units':None})
                runtime,backend=load_backend(plan,references,recipe_arm,args.cache_dir)
                try:
                    if args.stage=='contexts': outcome=collect(plan,backend,runtime,root,recovery,args.stop_after)
                    elif args.stage=='evaluate': outcome=evaluate(plan,contexts,backend,runtime,root,args.arm,recovery,args.stop_after)
                    else:
                        examples=training_examples(plan,contexts,backend.tokenizer,args.arm)
                        if args.arm=='receiver_sft':
                            masks=read_json(root/'target_masks.json')
                            if any(e['primary']!=masks[e['record_id']] for e in examples):raise ValueError('Training tokenizer/prefix differs from frozen context preflight')
                        arm_identity={'study_hash':identity,'arm':args.arm,'model_snapshot':initial.base_snapshot,
                                      'runtime_fingerprint':initial.runtime_fingerprint,'context_hash':digest(contexts),
                                      'initialization_hashes':initial.reference_hashes,'target_mode':config.target_mode}
                        arm_identity=json.loads(canonical(arm_identity))
                        backend.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
                        backend.model.config.use_cache=False
                        outcome=train_focal(backend.model,examples,config,root/'training'/args.arm,arm_identity,
                                            resume=args.resume,stop_after=args.stop_after,before_update=recovery.before,after_update=recovery.after)
                        recovery.after()
                finally:
                    write_json(root/f'resources-{args.stage}-{args.arm or "source"}-{time.time_ns()}.json',backend.resource_usage())
                    del backend;gc.collect()
            print(canonical(export(root,args.persistent,outcome)))
        except BaseException as exc:
            write_json(root/'errors'/f'{time.time_ns()}.json',{'stage':args.stage,'arm':args.arm,
                       'type':type(exc).__name__,'message':redact(str(exc))})
            # Always create a local metadata review before a potentially stalled Drive write.
            bundle=review_bundle(root,root.parent/'bundles'/f'{root.name}-recovery-{time.time_ns()}.zip',
                {'status':'interrupted_or_failed','error_type':type(exc).__name__},kind='receiver_supervision_review',scientific_status=STATUS,max_metadata_bytes=256*1024**2,include_markdown=True)
            print('Local recovery ZIP:',canonical(bundle),flush=True)
            raise


if __name__=='__main__':main()
