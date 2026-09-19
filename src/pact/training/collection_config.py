"""Fixed, train-only engineering collection; never a validation config override."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..config import Limits, ModelConfig, ProbeConfig, Sampling
from ..util import digest, read_json
from .bank import sha
from .data import read_training_data


@dataclass(frozen=True)
class CollectionConfig:
    data_manifest_hash: str
    reference_manifest_hash: str
    reference_hashes: tuple[str, ...]
    schema_version: int = 1
    purpose: str = "warmstart_training_bank_engineering"
    seed: int = 1729
    items: int = 2
    conditions: tuple[str, ...] = ("clean", "early", "exchange")

    def validate(self):
        sha(self.data_manifest_hash); sha(self.reference_manifest_hash)
        if len(self.reference_hashes) != 3:
            raise ValueError("Three ordered frozen reference hashes required")
        for h in self.reference_hashes:
            sha(h)
        if (type(self.schema_version) is not int or self.schema_version != 1
                or self.purpose != "warmstart_training_bank_engineering"
                or type(self.items) is not int or self.items != 2
                or self.conditions != ("clean", "early", "exchange")
                or type(self.seed) is not int or not 0 <= self.seed < 2**31):
            raise ValueError("Engineering collection requires two training tasks and fixed clean/early/exchange cells")
        return self


@dataclass(frozen=True)
class CollectionRuntime:
    identity: str
    seed: int
    model: ModelConfig = ModelConfig()
    limits: Limits = Limits()
    sampling: Sampling = Sampling()
    probe: ProbeConfig = ProbeConfig(tasks=2)


def load_collection_config(path):
    data = read_json(Path(path))
    for field in ("reference_hashes", "conditions"):
        if field in data:
            data[field] = tuple(data[field])
    return CollectionConfig(**data).validate()


def collection_plan(config, data_dir):
    config.validate()
    tasks, labels, manifest, _ = read_training_data(Path(data_dir))
    if digest(manifest) != config.data_manifest_hash:
        raise ValueError("Training manifest differs from collection recipe")
    families = sorted({t.family for t in tasks})
    if len(families) != 2 or any(t.split != "train" for t in tasks):
        raise ValueError("Collection requires two train-only families")
    # First occurrence in the already frozen manifest: no model-outcome selection.
    selected = [next(t for t in tasks if t.family == family) for family in families]
    runtime = CollectionRuntime(digest(config), config.seed)
    plan = {"status": "collection_plan_only", "gpu_collection_verified": False,
            "training_executed": False, "config_hash": digest(config),
            "task_ids": [t.task_id for t in selected], "data_manifest_hash": digest(manifest),
            "reference_manifest_hash": config.reference_manifest_hash,
            "reference_hashes": config.reference_hashes, "records": 6,
            "generation_calls_upper_bound": 474, "generated_tokens_upper_bound": 106368,
            "teacher_forced_forwards_upper_bound": 72,
            "selection": "first task per family in frozen training manifest; no outcome filtering",
            "protocol": "three frozen actors; debate; unadapted base readout; four candidates; K=2",
            "runtime": {"model": runtime.model, "limits": runtime.limits, "sampling": runtime.sampling,
                        "probe": runtime.probe},
            "scope": "fixed-pool engineering bank; no sparse-support sampling, refresh or optimization"}
    return selected, labels, manifest, runtime, plan
