from __future__ import annotations

import contextlib
import dataclasses
import time
from pathlib import Path

from . import Request
from ..config import Config
from ..schemas import CallRecord
from ..util import canonical, digest, file_hash


def adapter_hash(path: Path) -> str:
    if not (path / "adapter_config.json").is_file() or not list(path.glob("*.safetensors")):
        raise ValueError("Adapter requires adapter_config.json and safetensors weights")
    files = sorted(p for p in path.rglob("*") if p.is_file() and p.suffix in (".json", ".safetensors"))
    return digest({p.relative_to(path).as_posix(): file_hash(p) for p in files})


@contextlib.contextmanager
def inference_adapter(model, identity: str | None, has_adapters: bool):
    """Restore active adapter even if generation raises. No adapter is trainable here."""
    previous = getattr(model, "active_adapter", None)
    try:
        if has_adapters and identity is not None:
            model.set_adapter(identity)
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        model.eval()
        with model.disable_adapter() if has_adapters and identity is None else contextlib.nullcontext():
            yield
    finally:
        if has_adapters and previous is not None:
            model.set_adapter(previous)
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        model.eval()


class TransformersBackend:
    def __init__(self, config: Config, cache_dir: Path):
        import torch
        from huggingface_hub import snapshot_download
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from ..environment import runtime_fingerprint

        self.config, self.torch = config, torch
        if config.model.device == "cuda":
            if not torch.cuda.is_available() or torch.cuda.device_count() != 1:
                raise RuntimeError("Exactly one visible CUDA GPU is required; no silent CPU/offload fallback")
            if config.model.precision == "bfloat16" and not torch.cuda.is_bf16_supported():
                raise RuntimeError("BF16 unsupported; choose a new explicit precision config and new run ID")
            torch.cuda.reset_peak_memory_stats()
        started = time.perf_counter()
        path = Path(snapshot_download(config.model.name, revision=config.model.revision,
                        cache_dir=str(cache_dir), allow_patterns=["*.json", "*.safetensors", "*.txt", "*.model"]))
        self.tokenizer = AutoTokenizer.from_pretrained(path, trust_remote_code=False)
        if not isinstance(self.tokenizer.chat_template, str) or not self.tokenizer.chat_template:
            raise ValueError("A pinned, explicit tokenizer chat template is required")
        self.model = AutoModelForCausalLM.from_pretrained(path, trust_remote_code=False,
                         torch_dtype=getattr(torch, config.model.precision),
                         attn_implementation=config.model.attention,
                         device_map={"": 0} if config.model.device == "cuda" else {"": "cpu"})
        for i, adapter in enumerate(config.model.adapters):
            if adapter_hash(Path(adapter.path)) != adapter.sha256:
                raise ValueError(f"Adapter content mismatch: {adapter.identity}")
            if i == 0:
                from peft import PeftModel
                self.model = PeftModel.from_pretrained(self.model, adapter.path,
                                        adapter_name=adapter.identity, is_trainable=False)
            else:
                self.model.load_adapter(adapter.path, adapter_name=adapter.identity, is_trainable=False)
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)
        self.load_seconds = time.perf_counter() - started
        self.load_allocated = torch.cuda.memory_allocated() if config.model.device == "cuda" else None
        files = {p.name: {"path": str(p), "sha256": file_hash(p), "bytes": p.stat().st_size}
                 for p in sorted(path.iterdir()) if p.is_file()}
        identity = {"model": config.model.name, "revision": config.model.revision,
                    "tokenizer_revision": config.model.revision,
                    "chat_template": self.tokenizer.chat_template,
                    "template_hash": digest(self.tokenizer.chat_template),
                    "precision": config.model.precision, "attention": config.model.attention,
                    "enable_thinking": config.model.enable_thinking,
                    "generation_defaults": self.model.generation_config.to_dict(),
                    "adapters": [{"identity": a.identity, "sha256": a.sha256} for a in config.model.adapters],
                    "weight_hashes": {k: v["sha256"] for k, v in files.items()}}
        self.identity = {**identity, "snapshot": digest(identity), "backend": "transformers",
                         "condition": "recorded_adapters" if config.model.adapters else "independent_samples_unadapted_base",
                         "runtime_fingerprint": runtime_fingerprint(), "external_artifacts": files,
                         "adapter_locations": [dataclasses.asdict(a) for a in config.model.adapters]}
        self.calls = []
        self.pending_call = None

    def count_tokens(self, text):
        return len(self.tokenizer.encode(text, add_special_tokens=False))

    def truncate(self, text, tokens):
        return self.tokenizer.decode(self.tokenizer.encode(text, add_special_tokens=False)[:tokens],
                                     skip_special_tokens=False)

    def generate(self, request: Request):
        torch = self.torch
        messages = [{"role": m.role, "content": m.content} for m in request.messages]
        rendered = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True,
                                                      enable_thinking=self.config.model.enable_thinking)
        inputs = self.tokenizer(rendered, return_tensors="pt", add_special_tokens=False)
        input_tokens = int(inputs["input_ids"].shape[-1])
        params = {"max_new_tokens": request.max_tokens, "do_sample": not request.deterministic,
                  "use_cache": True, "num_beams": 1, "repetition_penalty": 1.0,
                  "pad_token_id": self.tokenizer.pad_token_id, "eos_token_id": self.tokenizer.eos_token_id}
        if not request.deterministic:
            params.update(dataclasses.asdict(self.config.sampling), min_p=0.0)
        raw, output_tokens, stop = "", 0, "context_overflow"
        started = time.perf_counter()
        self.pending_call = {"request": dataclasses.asdict(request), "rendered_prompt": rendered,
                             "context_hash": digest(rendered), "input_tokens": input_tokens,
                             "output_tokens": None, "parameters": params}
        if input_tokens + request.max_tokens <= self.config.limits.context:
            actor = None
            if request.actor != "base" and self.config.model.adapters:
                actor = self.config.model.adapters[int(request.actor.split("-")[-1]) % 3].identity
            devices = [0] if self.config.model.device == "cuda" else []
            with inference_adapter(self.model, actor, bool(self.config.model.adapters)), torch.inference_mode(), torch.random.fork_rng(devices=devices):
                torch.manual_seed(request.seed)
                if devices:
                    torch.cuda.manual_seed_all(request.seed)
                generated = self.model.generate(**inputs.to(self.model.device), **params)
            output = generated[0, input_tokens:].tolist()
            output_tokens = len(output)
            eos = self.model.generation_config.eos_token_id
            eos_ids = eos if isinstance(eos, list) else [eos]
            stop = "eos" if output and output[-1] in eos_ids else "length"
            raw = self.tokenizer.decode(output, skip_special_tokens=True)
        call = CallRecord(request.actor, request.phase, self.identity["snapshot"], request.seed,
                          request.messages, rendered, digest(rendered), self.identity["template_hash"], canonical(params),
                          input_tokens, output_tokens, stop, time.perf_counter() - started)
        self.calls.append(call)
        self.pending_call = None
        return raw, call

    def resource_usage(self):
        cuda = self.config.model.device == "cuda"
        return {"peak_allocated_bytes": self.torch.cuda.max_memory_allocated() if cuda else None,
                "peak_reserved_bytes": self.torch.cuda.max_memory_reserved() if cuda else None,
                "model_load_seconds": self.load_seconds, "model_load_allocated_bytes": self.load_allocated,
                "compute_units": None, "cache_hits": 0}
