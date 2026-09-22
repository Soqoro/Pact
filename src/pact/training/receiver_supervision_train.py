"""Focal-only answer-field SFT, shared by real execution and tiny neural tests."""
import dataclasses as dc
from pathlib import Path
import random

from ..protocol import private_prompt
from ..schemas import task_from_dict
from ..util import digest, read_json, write_json, node_seed
from .receiver_supervision import ReceiverSupervisionConfig, prefix_tokens, torch_answer_ce
from .warmstart import (adapter_parameters, training_adapter, _weights_hash, _save_step,
                        _load_step, _restore_rng, export_references)


def training_examples(plan, contexts, tokenizer, arm):
    if arm not in ('task_sft', 'receiver_sft') or contexts['status'] != 'ready':
        raise ValueError('Training requires supported frozen contexts and a trained arm')
    partition = contexts['partitions']['fit']
    result = []
    for record in partition['records']:
        task = task_from_dict(plan['tasks'][record['task_id']])
        allowed = tuple(o.answer_id for o in task.options)
        private = [dc.asdict(m) for m in private_prompt(task, '')]
        anchor = prefix_tokens(tokenizer, private, record['target_answer'], allowed)
        primary = prefix_tokens(tokenizer, record['messages'] if arm == 'receiver_sft' else private,
                                record['target_answer'], allowed)
        result.append({'record_id': record['record_id'], 'task_id': task.task_id,
                       'primary_role': 'receiver_supervised_only' if arm=='receiver_sft' else 'task_supervised_only',
                       'anchor_role': 'clean_anchor', 'primary_coefficient':1.,
                       'anchor_coefficient':plan['config']['anchor_coefficient'],
                       'stratum': record['stratum'], 'weight': partition['weights'][record['record_id']],
                       'primary': primary, 'anchor': anchor})
    import json
    from ..util import canonical
    return json.loads(canonical(result))


def update_schedule(examples, config):
    """Same logical records, repetitions and label exposure in both trained arms."""
    result = []
    for epoch in range(config.passes):
        order = sorted(range(len(examples)), key=lambda i: digest([config.selection_seed, epoch, examples[i]['record_id']]))
        batches = [order[i:i+config.effective_batch] for i in range(0, len(order), config.effective_batch)]
        for batch in batches:
            result.append({'epoch': epoch, 'indices': batch, 'weight_scale': len(batches)})
    return result[:config.max_updates]


def token_loss(model, example):
    import torch
    device = next(model.parameters()).device
    ids = torch.tensor([example['input_ids']], device=device)
    attention = torch.tensor([example['attention_mask']], device=device)
    mask = torch.tensor([example['score_mask']], device=device)
    return torch_answer_ce(model(input_ids=ids, attention_mask=attention, use_cache=False).logits,
                           ids, attention, mask)[0]


def train_focal(model, examples, config, root, identity, *, resume=False, stop_after=None,
                before_update=lambda: None, after_update=lambda: None):
    """One scalar CE per example, microbatch one, global task/stratum weights.

    No prior preparation optimizer is consumed. Resume needs this arm's exact
    identity, tokenized examples, schedule, optimizer and RNG checkpoint.
    """
    import torch
    root = Path(root); root.mkdir(parents=True, exist_ok=True)
    schedule = update_schedule(examples, config)
    if not examples or not schedule:
        raise ValueError('Empty training schedule')
    contract = {'identity': identity, 'examples_hash': digest(examples), 'schedule': schedule,
                'config': dc.asdict(config), 'initial_weight_hash': _weights_hash(adapter_parameters(model))}
    if resume:
        if read_json(root/'run.json') != contract or read_json(root/'examples.json') != examples:
            raise ValueError('Training identity/examples/initialization/schedule changed')
    elif (root/'run.json').exists():
        raise ValueError('Existing arm requires explicit resume')
    else:
        write_json(root/'run.json', contract); write_json(root/'examples.json', examples)
    agent = f'agent{config.focal_agent}'
    selected = adapter_parameters(model, agent)
    if not selected:
        raise ValueError('Missing focal adapter')
    if any(p.dtype!=torch.float32 for p in selected.values()):raise ValueError('Focal adapter parameters must retain FP32 update precision')
    inactive = {n:p for n,p in adapter_parameters(model).items() if n not in selected}
    inactive_hash = _weights_hash(inactive)
    frozen_versions = [(n,p,p._version) for n,p in model.named_parameters() if n not in selected]
    # The full backbone can be many GiB: mutation counters plus no gradients audit it.
    step, logs, state = 0, [], None
    if resume:
        step, state = _load_step(root/'checkpoints', identity, model)
        logs = state['logs']
        # Loading actor checkpoints legitimately increments inactive tensor versions.
        if _weights_hash(inactive) != inactive_hash:
            raise ValueError('Resume changed a nonfocal adapter')
        frozen_versions = [(n,p,p._version) for n,p in model.named_parameters() if n not in selected]
    attempt = root/'update_attempt.json'
    if attempt.exists() and read_json(attempt)['step'] > step:
        raise ValueError('Unresolved optimizer attempt; no automatic replay of attempted training budget')
    with training_adapter(model, agent):
        optimizer = torch.optim.AdamW(list(selected.values()), lr=config.learning_rate,
                                     betas=(.9,.999), eps=1e-8, weight_decay=0., foreach=False)
        if state is not None:
            if state['optimizer_agent'] != agent or state['optimizer'] is None:
                raise ValueError('Wrong optimizer owner')
            optimizer.load_state_dict(state['optimizer']); _restore_rng(state['rng'])
        else:
            random.seed(config.selection_seed); torch.manual_seed(config.selection_seed)
            if torch.cuda.is_available(): torch.cuda.manual_seed_all(config.selection_seed)
            _save_step(root/'checkpoints', identity, 0, model, optimizer, agent, [])
            after_update()
        performed = 0
        for batch in schedule[step:]:
            if stop_after is not None and performed >= stop_after:
                break
            before_update()
            write_json(attempt, {'step': step+1, 'identity_hash': digest(identity), 'state':'attempted'})
            optimizer.zero_grad(set_to_none=True)
            parts = []
            for i in batch['indices']:
                example = examples[i]; weight = batch['weight_scale'] * example['weight']
                values = {}
                for role, coefficient in (('primary', 1.), ('anchor', config.anchor_coefficient)):
                    loss = token_loss(model, example[role])
                    if not torch.isfinite(loss): raise ValueError('Nonfinite supervised loss')
                    (loss * weight * coefficient).backward()
                    values[role+'_nll'] = float(loss.detach())
                    values[role+'_scored_tokens'] = sum(example[role]['score_mask'])
                    values[role+'_input_tokens'] = len(example[role]['input_ids'])
                parts.append({'record_id':example['record_id'], 'task_id':example['task_id'],
                              'stratum':example['stratum'], 'global_weight':example['weight'],
                              'update_weight':weight, **values})
            gradients = [p.grad for p in selected.values() if p.grad is not None]
            if not gradients or any(not torch.isfinite(g).all() for g in gradients):
                raise ValueError('Missing/nonfinite focal gradients')
            norm = sum(float(g.detach().float().square().sum()) for g in gradients)**.5
            if any(p.grad is not None or p._version != version for _,p,version in frozen_versions):
                raise ValueError('Backbone/nonfocal/reference mutation or gradient')
            optimizer.step(); optimizer.zero_grad(set_to_none=True)
            step += 1; performed += 1
            logs.append({'step':step, 'agent':agent, 'epoch':batch['epoch'], 'gradient_norm':norm,
                         'lambda_rx':config.lambda_rx, 'lambda_dpo':0., 'anchor_coefficient':config.anchor_coefficient,
                         'examples':parts, 'forward_backward_calls':2*len(parts)})
            _save_step(root/'checkpoints', identity, step, model, optimizer, agent, logs)
            write_json(attempt, {'step':step, 'identity_hash':digest(identity), 'state':'committed'})
            write_json(root/'status.json', {'completed_steps':step, 'planned_steps':len(schedule),
                       'training_executed':True, 'complete':step==len(schedule), 'logs':logs})
            after_update()
            print(f'Receiver SFT {identity["arm"]}: {step}/{len(schedule)} updates', flush=True)
    if _weights_hash(inactive) != inactive_hash or any(p._version != v for _,p,v in frozen_versions):
        raise ValueError('Frozen weights changed')
    result = {'completed_steps':step, 'planned_steps':len(schedule), 'training_executed':step>0,
              'complete':step==len(schedule), 'logs':logs, 'nonfocal_unchanged':True,
              'initial_weight_hash':contract['initial_weight_hash'],
              'final_weight_hash':_weights_hash(adapter_parameters(model))}
    if result['complete']:
        result['references'] = export_references(model, root, identity, step)
    write_json(root/'status.json', result)
    return result
