from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from typing import Any

from .util import digest, read_json

METHODS = ("single", "single_matched", "vote", "vote_matched", "synthesis",
           "synthesis_matched", "debate", "ignore_peers", "archive", "archive_matched")
REVISION_METHODS = ("debate", "ignore_peers", "archive", "archive_matched")
EXCHANGE_METHODS = ("debate", "archive", "archive_matched")


@dataclasses.dataclass(frozen=True)
class AdapterConfig:
    identity: str
    path: str
    sha256: str  # digest of sorted relative safetensors/config filenames and file hashes


@dataclasses.dataclass(frozen=True)
class ModelConfig:
    name: str = "Qwen/Qwen3-8B"
    revision: str = "b968826d9c46dd6066d109eabc6255188de91218"
    precision: str = "bfloat16"
    device: str = "cuda"
    attention: str = "sdpa"
    enable_thinking: bool = False
    adapters: tuple[AdapterConfig, ...] = ()


@dataclasses.dataclass(frozen=True)
class Limits:
    context: int = 4096
    packet: int = 256
    final: int = 64
    payload: int = 256
    archive_context_tokens: int = 768


@dataclasses.dataclass(frozen=True)
class Sampling:
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20


@dataclasses.dataclass(frozen=True)
class ProbeConfig:
    tasks: int = 2
    candidates: int = 4
    suffix_seeds: int = 2
    length_bin: int = 32
    revision_candidates: int = 4


@dataclasses.dataclass(frozen=True)
class Config:
    schema_version: int = 1
    purpose: str = "diagnostic_pilot"
    backend: str = "mock"
    stage: str = "smoke"
    seed: int = 1729
    split: str = "validation"
    items: int = 4
    methods: tuple[str, ...] = ("debate",)
    conditions: tuple[str, ...] = ("clean", "early", "exchange")
    model: ModelConfig = ModelConfig()
    limits: Limits = Limits()
    sampling: Sampling = Sampling()
    probe: ProbeConfig = ProbeConfig()
    bootstrap_samples: int = 1000
    sync_every: int = 5

    @property
    def identity(self) -> str:
        return digest(self)

    def validate(self) -> Config:
        if type(self.schema_version) is not int or self.schema_version != 1 or self.purpose != "diagnostic_pilot":
            raise ValueError("Only schema 1 diagnostic_pilot is implemented")
        if self.backend not in ("mock", "transformers") or self.stage not in ("smoke", "profile", "pilot"):
            raise ValueError("Unsupported backend or stage")
        if self.split != "validation":
            raise ValueError("Milestones 0–2 only permit validation; final-test execution is unavailable")
        for name, value in [("items", self.items), ("seed", self.seed), ("sync_every", self.sync_every),
                            ("bootstrap_samples", self.bootstrap_samples),
                            *dataclasses.asdict(self.limits).items(),
                            *dataclasses.asdict(self.probe).items()]:
            if type(value) is not int or value < (0 if name in ("tasks", "seed") else 1):
                raise ValueError(f"Invalid integer {name}: {value}")
        if self.items % 2 or self.items > {"smoke": 8, "profile": 20, "pilot": 80}[self.stage]:
            raise ValueError("Use balanced even item counts within smoke=8, profile=20, pilot=80 caps")
        if self.items < 4 or self.probe.tasks > self.items or self.probe.candidates > 4 or self.probe.revision_candidates > 4:
            raise ValueError("Need at least 4 items; probe tasks <= items, candidates <= 4")
        if self.probe.suffix_seeds != 2:
            raise ValueError("This pilot prespecifies K=2 paired suffix seeds")
        if not self.methods or len(set(self.methods)) != len(self.methods) or set(self.methods) - set(METHODS):
            raise ValueError("Unknown, duplicate or empty methods")
        if not self.conditions or len(set(self.conditions)) != len(self.conditions) or set(self.conditions) - {"clean", "early", "exchange"}:
            raise ValueError("Unknown, duplicate or empty conditions")
        if self.probe.tasks and "debate" not in self.methods:
            raise ValueError("Probe requires the ordinary debate reference method")
        if self.limits.context <= 2 * self.limits.packet + self.limits.final:
            raise ValueError("Context cap is too small")
        if (type(self.sampling.temperature) not in (float, int) or type(self.sampling.top_p) not in (float, int)
                or not 0 < self.sampling.temperature <= 2 or not 0 < self.sampling.top_p <= 1
                or type(self.sampling.top_k) is not int or self.sampling.top_k < 1):
            raise ValueError("Invalid sampling parameters")
        if self.model.precision not in ("bfloat16", "float16", "float32") or self.model.device not in ("cuda", "cpu") or self.model.attention not in ("sdpa", "eager"):
            raise ValueError("Unsupported explicit model runtime settings")
        if type(self.model.enable_thinking) is not bool or self.model.enable_thinking:
            raise ValueError("Pilot grammar requires explicit enable_thinking=false; thinking evaluation is deferred")
        if not re.fullmatch(r"[0-9a-f]{40}", self.model.revision):
            raise ValueError("Model/tokenizer revision must be a full immutable commit SHA")
        if len(self.model.adapters) not in (0, 3):
            raise ValueError("Supply zero adapters (independent base samples) or three explicit adapters")
        if len({a.identity for a in self.model.adapters}) != len(self.model.adapters):
            raise ValueError("Adapter identities must be distinct")
        for a in self.model.adapters:
            if not re.fullmatch(r"[0-9a-f]{64}", a.sha256):
                raise ValueError("Local adapter content hash required")
        return self


def _construct(cls, data: dict[str, Any]):
    if not isinstance(data, dict) or set(data) - {f.name for f in dataclasses.fields(cls)}:
        raise ValueError(f"Unknown fields in {cls.__name__}")
    return cls(**data)


def load_config(path: str | Path) -> Config:
    # Checked-in .yaml files use the JSON subset of YAML 1.2, so CPU tools need no dependencies.
    try:
        data = read_json(Path(path))
    except json.JSONDecodeError as exc:
        raise ValueError("Config must use JSON syntax (valid YAML 1.2); see checked-in presets") from exc
    return config_from_dict(data)


def config_from_dict(data: dict) -> Config:
    data = dict(data)
    model = dict(data.get("model", {}))
    model["adapters"] = tuple(_construct(AdapterConfig, a) for a in model.get("adapters", []))
    data["model"] = _construct(ModelConfig, model)
    for field, cls in (("limits", Limits), ("sampling", Sampling), ("probe", ProbeConfig)):
        data[field] = _construct(cls, data.get(field, {}))
    for key in ("methods", "conditions"):
        if key in data:
            if not isinstance(data[key], (list, tuple)) or not all(type(x) is str for x in data[key]):
                raise ValueError(f"{key} must be a sequence of strings")
            data[key] = tuple(data[key])
    return _construct(Config, data).validate()


def budget(config: Config) -> dict:
    caps = {}
    p, f = config.limits.packet, config.limits.final
    for method in config.methods:
        if method == "single":
            n, tokens = 1, p
        elif method == "single_matched":
            n, tokens = 1, 6 * p + f
        elif method.startswith("vote"):
            n = 6 if method.endswith("matched") else 3
            tokens = n * p
        elif method.startswith("synthesis"):
            n = 7 if method.endswith("matched") else 4
            tokens = (n - 1) * p + f
        else:
            n, tokens = 7, 6 * p + f
        applicable = sum(c != "exchange" or method in EXCHANGE_METHODS for c in config.conditions)
        caps[method] = {"calls_per_trajectory": n, "max_generated_tokens": tokens,
                        "applicable_conditions": applicable,
                        "budget_view": "matched_output_cap" if "matched" in method or method == "ignore_peers" else "natural"}
    calls = config.items * sum(v["calls_per_trajectory"] * v["applicable_conditions"] for v in caps.values())
    tokens = config.items * sum(v["max_generated_tokens"] * v["applicable_conditions"] for v in caps.values())
    probe_calls = config.probe.tasks * len(config.conditions) * 3 * (
        config.probe.candidates + config.probe.revision_candidates + 2 * config.probe.suffix_seeds * 4)
    return {"methods": caps, "trajectory_calls_upper_bound": calls, "trajectory_output_tokens_upper_bound": tokens,
            "probe_calls_upper_bound": probe_calls, "probe_output_tokens_upper_bound": probe_calls * p,
            "input_tokens_note": "Actual input tokens measured; equal output caps do not imply equal FLOPs or context cost"}
