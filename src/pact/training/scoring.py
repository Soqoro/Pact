"""Frozen warm-start reload and exact-token teacher-forced reference scoring."""
from __future__ import annotations

import contextlib
import dataclasses
from pathlib import Path
import time

from ..backends.transformers import TransformersBackend, adapter_hash
from ..config import AdapterConfig
from ..util import digest, read_json
from .losses import torch_completion_logps, tokenize_completion

ACTORS = tuple(f"agent{i}" for i in range(3))
REFERENCES = tuple(f"reference{i}" for i in range(3))


def verify_references(root, config):
    root = Path(root)
    if root.is_symlink() or (root / "references.json").is_symlink():
        raise ValueError("Reference symlinks are not allowed")
    manifest = read_json(root / "references.json")
    if (digest(manifest) != config.reference_manifest_hash or manifest.get("schema_version") != 1
            or manifest.get("final_step") != 9 or len(manifest.get("references", [])) != 3):
        raise ValueError("Frozen reference manifest mismatch")
    for i, ref in enumerate(manifest["references"]):
        path = root / ACTORS[i]
        if ref != {"agent": i, "identity": ACTORS[i], "kind": "warm_start_adapter",
                   "path": ACTORS[i], "sha256": config.reference_hashes[i]}:
            raise ValueError("Frozen reference identity mismatch")
        if path.is_symlink() or {p.name for p in path.iterdir()} != {"adapter_config.json", "adapter_model.safetensors"}:
            raise ValueError("Unexpected frozen adapter files")
        if any(p.is_symlink() or not p.is_file() or p.stat().st_size > 1024**3 for p in path.iterdir()):
            raise ValueError("Invalid frozen adapter file")
        if adapter_hash(path) != ref["sha256"]:
            raise ValueError("Frozen reference tensor/config hash mismatch")
        recipe = read_json(path / "adapter_config.json")
        if (recipe.get("peft_type") != "LORA" or recipe.get("r") != 16 or recipe.get("lora_alpha") != 32
                or set(recipe.get("target_modules", [])) != {"q_proj", "v_proj"}
                or recipe.get("lora_dropout") != 0 or recipe.get("bias") != "none"
                or recipe.get("task_type") != "CAUSAL_LM" or recipe.get("modules_to_save") is not None):
            raise ValueError("Unexpected warm-start adapter architecture")
    return manifest


def load_frozen_adapters(base, paths):
    """Explicit base already loaded; never follow the exported Colab cache path."""
    from peft import PeftModel
    model = base
    for i, name in enumerate((*ACTORS, *REFERENCES)):
        path = str(paths[i % 3])
        if i == 0:
            model = PeftModel.from_pretrained(model, path, adapter_name=name, is_trainable=False,
                                             local_files_only=True)
        else:
            model.load_adapter(path, adapter_name=name, is_trainable=False, local_files_only=True)
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    return model


@contextlib.contextmanager
def scoring_adapter(model, name):
    """PEFT set_adapter changes gradient flags; restore every flag/mode explicitly."""
    if name not in model.peft_config:
        raise ValueError("Requested adapter is not loaded")
    previous = model.active_adapter
    flags = [(p, p.requires_grad) for p in model.parameters()]
    modes = [(m, m.training) for m in model.modules()]
    try:
        model.set_adapter(name)
        model.eval()
        for p in model.parameters():
            p.requires_grad_(False)
        yield
    finally:
        model.set_adapter(previous)
        for p, flag in flags:
            p.requires_grad_(flag)
        for m, mode in modes:
            m.training = mode


class FrozenScorer:
    def __init__(self, model, tokenizer, base_identity, reference_hashes, *, context_limit=4096):
        if not set((*ACTORS, *REFERENCES)) <= set(model.peft_config) or len(reference_hashes) != 3:
            raise ValueError("Three separate actors and frozen references must be loaded")
        self.model, self.tokenizer = model, tokenizer
        self.identity, self.reference_hashes = dict(base_identity), tuple(reference_hashes)
        self.context_limit = context_limit
        self.forwards = []
        # Actor parameters may be updated by a future optimizer; references/base may not.
        self.protected = [(n, p, p._version) for n, p in model.named_parameters()
                          if not any(f".{name}." in n for name in ACTORS)]

    def assert_frozen(self):
        current = dict(self.model.named_parameters())
        if any(current.get(n) is not p or p._version != version for n, p, version in self.protected):
            raise RuntimeError("Frozen backbone/reference changed")

    def token_score(self, adapter, prompt, prompt_ids, completion, completion_ids):
        import torch
        self.assert_frozen()
        tokenizer = self.tokenizer
        if tuple(tokenizer.encode(prompt, add_special_tokens=False)) != tuple(prompt_ids):
            raise ValueError("Scoring prompt bytes/token prefix mismatch")
        if (not completion_ids or completion_ids[-1] != tokenizer.eos_token_id
                or tokenizer.eos_token_id in completion_ids[:-1]
                or tokenizer.decode(list(completion_ids[:-1]), skip_special_tokens=True) != completion):
            raise ValueError("Scoring completion bytes/tokens/EOS mismatch")
        ids = list(prompt_ids) + list(completion_ids)
        if not prompt_ids or len(ids) > self.context_limit:
            raise ValueError("Scoring context overflow; truncation forbidden")
        started = time.monotonic()
        with scoring_adapter(self.model, adapter), torch.inference_mode():
            tokens = torch.tensor([ids], dtype=torch.long, device=self.model.device)
            attention = torch.ones_like(tokens)
            mask = torch.tensor([[0]*len(prompt_ids)+[1]*len(completion_ids)], device=self.model.device)
            output = self.model(input_ids=tokens, attention_mask=attention, use_cache=False)
            sums, counts = torch_completion_logps(output.logits, tokens, attention, mask)
            value, count = sums.item(), counts.item()
        self.assert_frozen()
        record = {"adapter": adapter, "prompt_hash": digest(prompt), "prompt_ids": list(prompt_ids),
                  "completion": completion, "completion_ids": list(completion_ids),
                  "sum_logp": value, "token_count": count, "mean_nll": -value/count,
                  "elapsed_seconds": time.monotonic()-started}
        self.forwards.append(record)
        return record

    def reference_score(self, request):
        request.payload()  # Validate IDs, EOS, hashes and role before any forward.
        if (request.adapter_hash != self.reference_hashes[request.agent]
                or request.base_snapshot != self.identity["snapshot"]
                or request.tokenizer_revision != self.identity["tokenizer_revision"]
                or request.template_hash != self.identity["template_hash"]
                or request.precision != self.identity["precision"]
                or request.runtime_fingerprint != self.identity["runtime_fingerprint"]
                or request.eos_id != self.tokenizer.eos_token_id):
            raise ValueError("Reference scoring identity differs from loaded frozen policy")
        return self.token_score(REFERENCES[request.agent], request.prompt, request.prompt_ids,
                                request.completion, request.completion_ids)["sum_logp"]

    def answer_score(self, agent, prompt, completion):
        tokens = tokenize_completion(self.tokenizer, prompt, completion,
                                     eos_id=self.tokenizer.eos_token_id, max_length=self.context_limit)
        return self.token_score(ACTORS[agent], prompt, tokens["prompt_ids"], completion, tokens["completion_ids"])


class CollectionBackend(TransformersBackend):
    def __init__(self, runtime, cache_dir, reference_dir, recipe):
        manifest = verify_references(reference_dir, recipe)
        super().__init__(runtime, cache_dir)  # Pinned bare base, no adapter path auto-loading.
        self.base_identity = dict(self.identity)
        if self.base_identity["snapshot"] != manifest["identity"]["model_snapshot"]:
            raise ValueError("Frozen references belong to a different base snapshot")
        paths = [Path(reference_dir) / name for name in ACTORS]
        self.model = load_frozen_adapters(self.model, paths)
        verify_references(reference_dir, recipe)
        adapters = tuple(AdapterConfig(name, str(path), sha) for name, path, sha in zip(ACTORS, paths, recipe.reference_hashes))
        self.config = dataclasses.replace(runtime, model=dataclasses.replace(runtime.model, adapters=adapters))
        self.identity = {**self.base_identity, "snapshot": digest({"base": self.base_identity["snapshot"],
                          "actors": recipe.reference_hashes}), "condition": "frozen_warmstart_actors",
                         "adapters": [{"identity": a.identity, "sha256": a.sha256} for a in adapters]}
        self.scorer = FrozenScorer(self.model, self.tokenizer, self.base_identity, recipe.reference_hashes)
        self.generation_tokens = {}
        self.versions = [(n, p, p._version) for n, p in self.model.named_parameters()]

    def assert_unchanged(self):
        current = dict(self.model.named_parameters())
        if any(current.get(n) is not p or p._version != v or p.requires_grad for n, p, v in self.versions):
            raise RuntimeError("Whole-team collection snapshot changed")
        self.scorer.assert_frozen()

    def generate(self, request):
        self.assert_unchanged()
        print(f"Bank generation {len(self.calls) + 1}: {request.actor}/{request.phase}", flush=True)
        raw, call = super().generate(request)
        self.generation_tokens[digest(call)] = dict(self.last_generation)
        self.assert_unchanged()
        return raw, call
