"""Sequential clean-answer LoRA warm start. GPU execution requires an explicit CLI flag."""
from __future__ import annotations

import contextlib
import dataclasses
import hashlib
from pathlib import Path
import random
import shutil
import tempfile
import time

from ..artifacts import run_lock
from ..backends.transformers import adapter_hash
from ..util import digest, node_seed, read_json, write_json
from .checkpoints import commit_checkpoint, decode_state, encode_state, latest_checkpoint
from .losses import answer_target, tokenize_completion, torch_completion_logps
from .warmstart_config import warmstart_plan, warmstart_prompt


AGENTS = ("agent0", "agent1", "agent2")


def adapter_parameters(model, agent=None):
    names = AGENTS if agent is None else (agent,)
    return {n: p for n, p in model.named_parameters()
            if any(f".lora_{side}.{name}." in n for side in ("A", "B") for name in names)}


@contextlib.contextmanager
def training_adapter(model, agent):
    previous = model.active_adapter
    flags = [(p, p.requires_grad) for p in model.parameters()]
    modes = [(module, module.training) for module in model.modules()]
    try:
        model.set_adapter(agent)
        selected = adapter_parameters(model, agent)
        if not selected:
            raise ValueError("Active adapter has no q/v LoRA parameters")
        ids = {id(p) for p in selected.values()}
        for p in model.parameters():
            p.requires_grad_(id(p) in ids)
            p.grad = None
        model.train()
        yield selected
    finally:
        model.set_adapter(previous)
        for p, flag in flags:
            p.requires_grad_(flag)
            p.grad = None
        for module, training in modes:
            module.training = training


def create_adapters(base, config):
    import torch
    from peft import LoraConfig, get_peft_model
    model = base
    for i, agent in enumerate(AGENTS):
        torch.manual_seed(node_seed(config.seeds[i], "adapter-init"))
        cfg = LoraConfig(r=config.rank, lora_alpha=config.alpha, lora_dropout=config.dropout,
                         target_modules=list(config.target_modules), bias="none", task_type="CAUSAL_LM")
        if i == 0:
            model = get_peft_model(model, cfg, adapter_name=agent)
        else:
            model.add_adapter(agent, cfg)
    for p in model.parameters():
        p.requires_grad_(False)
    # Explicit FP32 adapter update policy, including subsequently added adapters.
    for p in adapter_parameters(model).values():
        p.data = p.data.float()
    model.eval()
    return model


def prepare_examples(tokenizer, tasks, labels, config):
    examples = []
    for task in tasks:
        if task.family.startswith("gpqa") or task.task_id.startswith("gpqa_"):
            raise ValueError("GPQA development/evaluation items are forbidden in warm-start training")
        messages = [dataclasses.asdict(m) for m in warmstart_prompt(task)]
        messages = [{"role": m["role"], "content": m["content"]} for m in messages]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        label = labels[task.task_id]
        if label.task_id != task.task_id or label.answer_id not in [o.answer_id for o in task.options]:
            raise ValueError("Warm-start evaluator label mismatch")
        completion = answer_target(label.answer_id)
        tokens = tokenize_completion(tokenizer, prompt, completion, eos_id=tokenizer.eos_token_id,
                                     max_length=config.context_limit)
        examples.append({"task_id": task.task_id, "prompt": prompt, "target": completion, **tokens})
    return examples


def _weights_hash(parameters):
    import torch
    result = {}
    for name, p in parameters.items():
        data = p.detach().cpu().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes()
        result[name] = {"sha256": hashlib.sha256(data).hexdigest(), "shape": list(p.shape), "dtype": str(p.dtype)}
    return digest(result)


def _rng_state():
    import torch
    return {"python": random.getstate(), "torch": torch.get_rng_state(),
            "cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def _restore_rng(state):
    import torch
    random.setstate(state["python"])
    torch.set_rng_state(state["torch"])
    if len(state["cuda"]) != (torch.cuda.device_count() if torch.cuda.is_available() else 0):
        raise ValueError("Checkpoint CUDA RNG/device count mismatch")
    if state["cuda"]:
        torch.cuda.set_rng_state_all(state["cuda"])


def _save_step(root, identity, step, model, optimizer, optimizer_agent, logs):
    import torch
    from safetensors.torch import save_file
    state = {"adapters": {n: p.detach().cpu().clone() for n, p in adapter_parameters(model).items()},
             "optimizer": optimizer.state_dict() if optimizer is not None else None,
             "optimizer_agent": optimizer_agent, "rng": _rng_state(), "logs": logs}
    tree, tensors = encode_state(state, torch.is_tensor)
    tensors = {k: v.detach().cpu().contiguous().clone() for k, v in tensors.items()}
    return commit_checkpoint(root, step=step, identity=identity, tree=tree,
                             write_tensors=lambda path: save_file(tensors, str(path)))


def _load_step(root, identity, model):
    import torch
    from safetensors.torch import load_file
    path, metadata = latest_checkpoint(root, identity)
    state = decode_state(metadata["tree"], load_file(str(path / "tensors.safetensors")))
    parameters = adapter_parameters(model)
    if set(state["adapters"]) != set(parameters):
        raise ValueError("Checkpoint adapter parameter names differ")
    for name, p in parameters.items():
        value = state["adapters"][name]
        if value.shape != p.shape or value.dtype != p.dtype or not torch.isfinite(value).all():
            raise ValueError("Checkpoint adapter shape/dtype/value mismatch")
    with torch.no_grad():
        for name, p in parameters.items():
            p.copy_(state["adapters"][name])
    if len(state["logs"]) != metadata["step"]:
        raise ValueError("Checkpoint progress/log mismatch")
    return metadata["step"], state


def train_adapters(model, examples, orders, config, root: Path, identity, *, resume=False, stop_after=None, checkpoint_callback=None, audit_training=False):
    """Neural engine shared by real execution and opt-in tiny tests; save every step."""
    import torch
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be a positive number of newly committed updates")
    total = len(AGENTS) * config.steps_per_agent
    if len(orders) != 3 or any(len(o) != config.steps_per_agent * config.effective_batch for o in orders):
        raise ValueError("Warm-start sample order/batch mismatch")
    checkpoints = root / "checkpoints"
    if resume:
        step, saved = _load_step(checkpoints, identity, model)
        logs = saved["logs"]
        if step > total:
            raise ValueError("Checkpoint exceeds configured steps")
    else:
        step, saved, logs = 0, None, []
        _save_step(checkpoints, identity, 0, model, None, None, logs)
    start_step = step
    all_adapter_ids = {id(p) for p in adapter_parameters(model).values()}
    base = [(n, p, p._version) for n, p in model.named_parameters() if id(p) not in all_adapter_ids]
    while step < total:
        agent_index = step // config.steps_per_agent
        agent = AGENTS[agent_index]
        inactive = {n: p for n, p in adapter_parameters(model).items() if n not in adapter_parameters(model, agent)}
        inactive_hash = _weights_hash(inactive)
        with training_adapter(model, agent) as parameters:
            optimizer = torch.optim.AdamW(list(parameters.values()), lr=config.learning_rate,
                                         betas=(0.9, 0.999), eps=1e-8, weight_decay=config.weight_decay, foreach=False)
            if saved is not None and saved["optimizer_agent"] == agent:
                optimizer.load_state_dict(saved["optimizer"])
                _restore_rng(saved["rng"])
            else:
                seed = node_seed(config.seeds[agent_index], "optimization")
                random.seed(seed)
                torch.manual_seed(seed)
            saved = None
            while step < total and step // config.steps_per_agent == agent_index:
                local_step = step % config.steps_per_agent
                selected = orders[agent_index][local_step * config.effective_batch:(local_step + 1) * config.effective_batch]
                optimizer.zero_grad(set_to_none=True)
                loss_sum, completion_tokens = 0., 0
                for microbatch, index in enumerate(selected, 1):
                    ex = examples[index]
                    print(f"Warm-start update {step + 1}/{total}: {agent}, "
                          f"example {microbatch}/{len(selected)}, tokens={len(ex['input_ids'])}", flush=True)
                    ids = torch.tensor([ex["input_ids"]], dtype=torch.long, device=model.device)
                    attention = torch.tensor([ex["attention_mask"]], dtype=torch.long, device=model.device)
                    mask = torch.tensor([ex["completion_mask"]], dtype=torch.long, device=model.device)
                    attempt = None
                    if audit_training:
                        attempt = root / 'training-attempts' / f'{time.time_ns()}.json'
                        accounting = {'step':step+1,'agent':agent,'task_id':ex['task_id'],
                            'sequence_tokens':len(ex['input_ids']),'forward_backward_complete':False}
                        write_json(attempt,accounting)
                    output = model(input_ids=ids, attention_mask=attention, use_cache=False)
                    sums, counts = torch_completion_logps(output.logits, ids, attention, mask)
                    loss = -(sums / counts).sum() / config.effective_batch
                    if not torch.isfinite(loss):
                        raise ValueError("Nonfinite warm-start loss")
                    loss.backward()
                    if attempt is not None:
                        write_json(attempt,{**accounting,'forward_backward_complete':True})
                    loss_sum += loss.detach().item()
                    completion_tokens += counts.sum().item()
                    del output, loss, sums, counts
                if any(p.grad is not None or p.requires_grad or p._version != version for _, p, version in base):
                    raise RuntimeError("Backbone freeze invariant violated")
                norm = torch.nn.utils.clip_grad_norm_(list(parameters.values()), config.max_grad_norm, error_if_nonfinite=True)
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                if any(not torch.isfinite(p).all() for p in parameters.values()):
                    raise ValueError("Nonfinite adapter parameter after update")
                if _weights_hash(inactive) != inactive_hash:
                    raise RuntimeError("Inactive adapter changed during another agent's update")
                if any(p._version != version for _, p, version in base):
                    raise RuntimeError("Backbone changed during optimizer step")
                step += 1
                logs.append({"step": step, "agent": agent, "agent_step": local_step + 1,
                             "task_ids": [examples[j]["task_id"] for j in selected],
                             "mean_completion_nll": loss_sum, "gradient_norm": norm.item(),
                             "completion_tokens": completion_tokens})
                _save_step(checkpoints, identity, step, model, optimizer, agent, logs)
                if checkpoint_callback is not None: checkpoint_callback(step)
                print(f"Warm-start {step}/{total}: {agent} loss={loss_sum:.6f}; checkpoint verified", flush=True)
                if stop_after is not None and step - start_step >= stop_after and step < total:
                    return {"status": "interrupted_at_optimizer_boundary", "completed_steps": step, "logs": logs}
            del optimizer
    return {"status": "warmstart_updates_complete", "completed_steps": step, "logs": logs}


def export_references(model, root: Path, identity, final_step):
    import torch
    from peft import get_peft_model_state_dict
    from safetensors.torch import load_file
    target = root / "references"
    if not target.exists():
        staging = Path(tempfile.mkdtemp(prefix=".references-", dir=root))
        try:
            model.save_pretrained(str(staging), selected_adapters=list(AGENTS), safe_serialization=True,
                                  save_embedding_layers=False)
            refs = [{"agent": i, "identity": name, "kind": "warm_start_adapter",
                     "path": name, "sha256": adapter_hash(staging / name)} for i, name in enumerate(AGENTS)]
            import os
            for name in AGENTS:
                for path in (staging / name).iterdir():
                    if path.is_file():
                        with path.open("rb") as stream:
                            os.fsync(stream.fileno())
            write_json(staging / "references.json", {"schema_version": 1, "identity": identity,
                       "final_step": final_step, "references": refs})
            staging.rename(target)
        finally:
            if staging.exists():
                shutil.rmtree(staging)
    value = read_json(target / "references.json")
    if value["identity"] != identity or value["final_step"] != final_step or len(value["references"]) != 3:
        raise ValueError("Frozen reference metadata mismatch")
    for i, reference in enumerate(value["references"]):
        if (reference["agent"] != i or reference["identity"] != AGENTS[i]
                or reference["kind"] != "warm_start_adapter" or reference["path"] != AGENTS[i]
                or reference["sha256"] != adapter_hash(target / AGENTS[i])):
            raise ValueError("Frozen warm-start reference checksum mismatch")
        expected = get_peft_model_state_dict(model, adapter_name=AGENTS[i], save_embedding_layers=False)
        actual = load_file(str(target / AGENTS[i] / "adapter_model.safetensors"))
        if set(actual) != set(expected) or any(not torch.equal(actual[k], expected[k].detach().cpu()) for k in actual):
            raise ValueError("Frozen reference weights differ from the completed warm-start adapter")
    return value


def run_warmstart(config, data_dir, root, cache_dir, *, resume=False, stop_after=None):
    return _run_prepared_warmstart(config, warmstart_plan(config,data_dir), root, cache_dir,
                                   resume=resume,stop_after=stop_after)


def _run_prepared_warmstart(config, prepared, root, cache_dir, *, resume=False, stop_after=None,
                            expected_base=None, checkpoint_callback=None,
                            scientific_status="clean_answer_warmstart_engineering_only", allow_prepared_directory=False):
    from ..backends.transformers import TransformersBackend
    from ..config import Config
    from ..environment import code_identity, runtime_fingerprint
    tasks, labels, orders, plan = prepared
    if expected_base is not None and runtime_fingerprint()!=expected_base['runtime_fingerprint']:
        raise ValueError('Preparation runtime differs before model loading')
    if stop_after is not None and (type(stop_after) is not int or stop_after < 1):
        raise ValueError("stop_after must be a positive number of newly committed updates")
    if root.exists() and not resume and not (allow_prepared_directory and
            {p.name for p in root.iterdir()}=={'preparation_plan.json'}):
        raise ValueError("Warm-start run exists; use explicit compatible resume or a new path")
    if resume and not (root / "run.json").is_file():
        raise ValueError("Warm-start run metadata is missing")
    source = code_identity(Path(__file__).resolve().parents[3])
    recipe = {"config": dataclasses.asdict(config), "data_manifest_hash": plan["data_manifest_hash"], "source": source}
    # JSON normalizes tuples; compare canonical identities at both boundaries.
    if resume and read_json(root / "run.json")["recipe_hash"] != digest(recipe):
        raise ValueError("Warm-start resume changed code/config/data; rejected before model load")
    with run_lock(root):
        print("Loading pinned Qwen base for warm-start preflight...", flush=True)
        backend = TransformersBackend(Config(backend="transformers"), cache_dir)
        if expected_base is not None:
            for key in ('snapshot','runtime_fingerprint','template_hash'):
                if backend.identity[key]!=expected_base[key]:raise ValueError('Preparation base identity differs')
        examples = prepare_examples(backend.tokenizer, tasks, labels, config)
        torch = backend.torch
        identity = {"recipe_hash": digest(recipe), "model_snapshot": backend.identity["snapshot"],
                    "runtime_fingerprint": backend.identity["runtime_fingerprint"],
                    "examples_hash": digest(examples), "orders_hash": digest(orders),
                    "torch_flags": {"deterministic_algorithms": torch.are_deterministic_algorithms_enabled(),
                        "matmul_tf32": torch.backends.cuda.matmul.allow_tf32,
                        "cudnn_tf32": torch.backends.cudnn.allow_tf32,
                        "cudnn_benchmark": torch.backends.cudnn.benchmark,
                        "cudnn_deterministic": torch.backends.cudnn.deterministic}}
        metadata = {"recipe_hash": digest(recipe), "recipe": recipe, "identity": identity, "plan": plan,
                    "base_model": backend.identity, "examples_hash": digest(examples)}
        if resume:
            if read_json(root / "run.json")["identity"] != identity:
                raise ValueError("Warm-start model/runtime/tokenization resume mismatch")
        else:
            write_json(root / "run.json", metadata)
            write_json(root / "examples.json", examples)
        model = create_adapters(backend.model, config)
        model.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        result = train_adapters(model, examples, orders, config, root, identity, resume=resume, stop_after=stop_after, checkpoint_callback=checkpoint_callback,audit_training=expected_base is not None)
        if result["status"] == "warmstart_updates_complete":
            result["references"] = export_references(model, root, identity, result["completed_steps"])
        result.update(scientific_status=scientific_status, training_executed=True,
                      resources=backend.resource_usage(), persistent_copy_verified=False)
        write_json(root / "status.json", result)
        return result
