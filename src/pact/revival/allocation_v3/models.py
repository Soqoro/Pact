"""Native FP32 adapters, typed checkpoint loading, real scheduled AdamW updates."""
from contextlib import contextmanager
from pathlib import Path
import time
from ...util import digest, read_json, write_json
from ...studies.heterogeneity import immutable
from .. import neural, contracts as c
from ..stage1 import weights
from . import design as d


def checkpoint_values(path):
    from safetensors.torch import load_file
    from ...training.checkpoints import read_checkpoint, decode_state
    contract = read_json(path/'contract.json')
    cp = sorted((path/'checkpoints').glob('step-*'))[-1]
    meta = read_checkpoint(cp, contract)
    state = decode_state(meta['tree'], load_file(str(cp/'tensors.safetensors')))
    status = read_json(path/'status.json')
    if not status['complete'] or meta['step'] != status['planned_steps']:
        raise ValueError('Incomplete family checkpoint')
    values = state['adapters']
    if neural._weights_hash(values) != status['adapter_hash']:
        raise ValueError('Changed adapter checkpoint')
    return values, status['adapter_hash']


@contextmanager
def opened(root, plan, family, cache, state='S0'):
    """One native backbone. R and attack Q always pristine when state=None."""
    started=time.monotonic()
    parent = Path(plan['parent_path'])
    if plan['fixture']:
        from ..mock import Backend
        backend = Backend(family)
    else:
        from ...environment import runtime_fingerprint
        access = read_json(parent/'evidence/access.json')
        if runtime_fingerprint() != access[family]['runtime_fingerprint']:
            raise ValueError('Exact recorded runtime required')
        backend = weights.backend(parent, family, cache)
        expected = read_json(parent/'inference_identity_manifest.json')['models'][family]['pristine_identity']
        if backend.identity != expected:
            backend.close()
            raise ValueError('Native base/template/precision identity changed')
    activation = None
    try:
        # Mock keys are explicit; real R key is carried by native identity.
        backend.key = family
        activation = weights.Activation(backend)
        if family == 'R' and state is not None:
            raise ValueError('R cannot activate an adapter')
        if state is not None:
            if state == 'S0':
                if plan['fixture']:
                    neural.attach(backend.model, 100+c.FAMILIES.index(family))
                    values = {n: p.detach().clone() for n, p in neural.parameters(backend.model).items()}
                    activation.base()
                    expected_hash = neural._weights_hash(values)
                else:
                    fit = 'uniform_joint_sft/'+family
                    values, inventory = weights.tensor_inventory(parent, fit)
                    expected_hash = plan['s0'][family]
                    if inventory['adapter_hash'] != expected_hash:
                        raise ValueError('Fixed S0 identity changed')
            else:
                values, expected_hash = checkpoint_values(Path(state))
            activation.use(values, expected_hash)
        yield backend, activation
    finally:
        if backend.model is not None and activation is not None:
            activation.base()
        write_json(root/'resources'/f'{time.time_ns()}.json', {
            'family': family, 'state': str(state), 'elapsed_seconds':time.monotonic()-started, 'usage': backend.resource_usage()})
        backend.close()


def train_schedule(root, plan, path, family, schedule, records, labels, seed, cache, wallet,
                   part, persist=lambda: None, resume=False):
    import torch
    if any(t not in records or records[t]['split'] != 'main_fit' for e in schedule for t in e['tasks']):
        raise ValueError('Only fitting tasks may supply gradients')
    if any(len(e['tasks']) != 8 or len(set(e['tasks'])) != 8 for e in schedule):
        raise ValueError('Eight distinct fitting groups per optimizer slot')
    with opened(root, plan, family, cache, 'S0') as (backend, activation):
        model = backend.model
        initial = {n: p.detach().clone() for n, p in neural.parameters(model).items()}
        initial_hash = neural._weights_hash(initial)
        saved_rng = neural._rng_state()
        try:
            contract = {'version': d.VERSION, 'family': family, 'plan_hash': digest(plan), 'seed': seed,
                        'schedule': schedule, 'initial': initial_hash, 'native': backend.identity,
                        'train': d.TRAIN, 'lora': c.LORA, 'part': part}
            if (path/'contract.json').exists():
                if not resume or read_json(path/'contract.json') != contract:
                    raise ValueError('Explicit exact training resume required')
            else:
                immutable(path/'contract.json', contract)
            ps = neural.parameters(model)
            for n, p in model.named_parameters():
                p.requires_grad_(n in ps)
            frozen = [(p, p._version) for n, p in model.named_parameters() if n not in ps]
            if not ps or any(p.dtype != torch.float32 for p in ps.values()):
                raise ValueError('FP32 LoRA required')
            optimizer = torch.optim.AdamW(list(ps.values()), lr=5e-5, betas=(.9,.999),
                                          eps=1e-8, weight_decay=0., foreach=False)
            step, logs = 0, []
            rng_seed = int(digest([20261027, 'training', seed, family])[:8], 16)
            import random
            import numpy as np
            random.seed(rng_seed); np.random.seed(rng_seed); torch.manual_seed(rng_seed)
            if resume:
                step, state = neural.load(path/'checkpoints', contract, model, optimizer)
                logs = state['logs']
            else:
                neural.save(path/'checkpoints', contract, 0, model, optimizer, [])
            targets = {}
            for task in {t for e in schedule for t in e['tasks']}:
                r = records[task]
                targets[task] = neural.prefix_target(backend.tokenizer,
                    backend.render_messages(c.prompt(r['task'])), labels[task],
                    [o['answer_id'] for o in r['task']['options']])
            if any(len(t['input_ids']) > 8192 for t in targets.values()):
                raise ValueError('Training context exceeds inherited limit; no truncation')
            model.train()
            for entry in schedule[step:]:
                identity = {'family':family,'native_snapshot':backend.identity['snapshot'],'contract': digest(contract), 'step': step+1,
                            'path': path.relative_to(root).as_posix(), 'batch': entry}
                key, old = wallet.begin(part, 'update', identity, {'updates': 1, 'training_forwards': 8})
                if old is not None:
                    raise ValueError('Checkpoint behind committed update; do not replay')
                optimizer.zero_grad(set_to_none=True)
                total, tokens = 0., 0
                for task in entry['tasks']:
                    target = targets[task]
                    value = neural.loss(model, target)
                    if not torch.isfinite(value):
                        raise ValueError('Nonfinite supervised loss')
                    (value/8).backward()
                    total += float(value.detach())/8
                    tokens += len(target['input_ids'])
                grads = [p.grad for p in ps.values() if p.grad is not None]
                if not grads or any(not torch.isfinite(v).all() for v in grads):
                    raise ValueError('Missing/nonfinite gradients')
                norm = float(torch.nn.utils.clip_grad_norm_(list(ps.values()), 1.))
                if not __import__('math').isfinite(norm):
                    raise ValueError('Nonfinite clipped gradient')
                if any(p.grad is not None or p._version != v for p, v in frozen):
                    raise ValueError('Frozen backbone mutated')
                optimizer.step(); step += 1
                if any(v[k].dtype != torch.float32 for v in optimizer.state.values()
                       for k in ('exp_avg', 'exp_avg_sq') if k in v):
                    raise ValueError('Optimizer precision changed')
                logs.append({'step': step, 'loss': total, 'gradient_norm': norm,
                             'training_forwards': 8, 'input_tokens': tokens, 'batch': entry,
                             'lr': 5e-5})
                neural.save(path/'checkpoints', contract, step, model, optimizer, logs)
                status = {'complete': step == len(schedule), 'planned_steps': len(schedule),
                          'completed_steps': step, 'adapter_hash': neural._weights_hash(ps),
                          'forwards': step*8, 'logs': logs}
                write_json(path/'status.json', status)
                wallet.commit(key, {'step': step, 'adapter_hash': status['adapter_hash'],
                                    'input_tokens': tokens, 'loss': total})
                print(f'Allocation {part} {family} {step}/{len(schedule)} loss={total:.6f}', flush=True)
                persist()
            model.eval()
            optimizer.zero_grad(set_to_none=True)
            return read_json(path/'status.json')
        finally:
            neural.restore_parameters(model, initial)
            neural._restore_rng(saved_rng)
            activation.use(initial, initial_hash)
            activation.check(initial_hash)
            if part == 'assay':
                immutable(path/'rollback.json', {'initial_hash': initial_hash,
                          'restored_hash': neural._weights_hash(neural.parameters(model)),
                          'temporary_optimizer_discarded': True, 'probe_training_tokens': 0,
                          'complete': (path/'status.json').exists() and read_json(path/'status.json')['complete']})
