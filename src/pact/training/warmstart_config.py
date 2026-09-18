"""Bounded clean-answer engineering recipe; separate from validation presets."""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

from ..protocol import safe_json, trusted_input
from ..schemas import Message
from ..util import digest, read_json
from .bank import sha
from .data import read_training_data


@dataclass(frozen=True)
class WarmstartConfig:
    data_manifest_hash: str
    schema_version: int = 1
    purpose: str = "clean_answer_warmstart_engineering"
    seeds: tuple[int, ...] = (1729, 1730, 1731)
    steps_per_agent: int = 3
    effective_batch: int = 4
    context_limit: int = 4096
    rank: int = 16
    alpha: int = 32
    learning_rate: float = 1e-5
    weight_decay: float = 0.0
    max_grad_norm: float = 1.0
    dropout: float = 0.0
    target_modules: tuple[str, ...] = ("q_proj", "v_proj")

    def validate(self):
        sha(self.data_manifest_hash, "training manifest hash")
        if type(self.schema_version) is not int or self.schema_version != 1 or self.purpose != "clean_answer_warmstart_engineering":
            raise ValueError("Unsupported warm-start recipe")
        if len(self.seeds) != 3 or len(set(self.seeds)) != 3 or any(type(s) is not int or not 0 <= s < 2**31 for s in self.seeds):
            raise ValueError("Three distinct integer agent seeds required")
        for name, bound in (("steps_per_agent", 16), ("effective_batch", 16), ("context_limit", 4096), ("rank", 64), ("alpha", 128)):
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= bound:
                raise ValueError(f"Invalid engineering bound: {name}")
        for name in ("learning_rate", "weight_decay", "max_grad_norm", "dropout"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"Nonfinite training setting: {name}")
        if not 0 < self.learning_rate <= 0.01 or self.weight_decay < 0 or self.max_grad_norm <= 0 or not 0 <= self.dropout < 1:
            raise ValueError("Invalid optimizer/dropout setting")
        if self.target_modules != ("q_proj", "v_proj"):
            raise ValueError("This bounded recipe supports the explicitly named q/v LoRA variant only")
        return self


def load_warmstart_config(path: Path):
    data = read_json(path)
    for field in ("seeds", "target_modules"):
        if field in data:
            data[field] = tuple(data[field])
    return WarmstartConfig(**data).validate()


def warmstart_prompt(task):
    if task.split != "train":
        raise ValueError("Warm-start prompts require training tasks")
    return (Message("system", 'Solve the trusted multiple-choice task. Return exactly one JSON object with the sole key "answer" and a canonical option ID. No Markdown or extra text.'),
            Message("user", safe_json({"trusted_task": trusted_input(task)})))


def warmstart_plan(config, data_dir):
    config.validate()
    tasks, labels, manifest, _ = read_training_data(data_dir)
    if digest(manifest) != config.data_manifest_hash:
        raise ValueError("Warm-start training manifest does not match the reviewed hash")
    used = config.steps_per_agent * config.effective_batch
    if not 2 <= len(tasks) <= 32 or used > len(tasks):
        raise ValueError("Engineering warm-start requires 2–32 tasks and at most one pass per agent")
    orders = [sorted(range(len(tasks)), key=lambda j: (digest([seed, tasks[j].task_id]), tasks[j].task_id))[:used]
              for seed in config.seeds]
    plan = {"status": "warmstart_plan_only", "training_executed": False, "config_hash": digest(config),
            "data_manifest_hash": digest(manifest), "microbatch": 1, "effective_batch": config.effective_batch,
            "optimizer": "AdamW; betas=(0.9,0.999); eps=1e-8; foreach=False; constant LR; no scheduler",
            "precision": "BF16 backbone, FP32 LoRA parameters; one CUDA GPU", "thinking": False,
            "total_optimizer_steps": 3 * config.steps_per_agent, "training_examples": 3 * used,
            "target": "clean canonical answer-only JSON plus EOS; mean completion-token NLL",
            "agent_task_ids": [[tasks[j].task_id for j in order] for order in orders],
            "gpu_training_verified": False}
    return tasks, labels, orders, plan
