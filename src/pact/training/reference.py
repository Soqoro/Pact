"""Content-addressed immutable scores; this cache does not execute a reference model."""
from __future__ import annotations

import dataclasses
from pathlib import Path

from ..artifacts import run_lock
from ..util import canonical, digest, read_json, write_json
from .assignment import finite
from .bank import sha, token_ids


@dataclasses.dataclass(frozen=True)
class ReferenceRequest:
    kind: str
    agent: int
    adapter_hash: str
    base_snapshot: str
    tokenizer_revision: str
    template_hash: str
    precision: str
    runtime_fingerprint: str
    prompt: str
    prompt_ids: tuple[int, ...]
    completion: str
    completion_ids: tuple[int, ...]
    eos_id: int

    def payload(self):
        if self.kind != "warm_start_adapter" or type(self.agent) is not int or self.agent not in (0, 1, 2):
            raise ValueError("Reference must identify the agent's frozen warm-start adapter")
        for value in (self.adapter_hash, self.base_snapshot, self.template_hash, self.runtime_fingerprint):
            sha(value)
        sha(self.tokenizer_revision, "tokenizer revision", 40)
        if self.precision not in ("float32", "float16", "bfloat16"):
            raise ValueError("Invalid reference precision")
        if not isinstance(self.prompt, str) or not self.prompt or not isinstance(self.completion, str) or not self.completion:
            raise ValueError("Exact prompt and completion bytes required")
        token_ids(self.prompt_ids, "prompt"); token_ids(self.completion_ids, "completion")
        if (type(self.eos_id) is not int or self.eos_id < 0 or self.completion_ids[-1] != self.eos_id
                or self.eos_id in self.completion_ids[:-1]):
            raise ValueError("Reference completion requires exactly one terminal EOS")
        return {**dataclasses.asdict(self), "attention_mask": [1] * (len(self.prompt_ids) + len(self.completion_ids)),
                "completion_mask": [0] * len(self.prompt_ids) + [1] * len(self.completion_ids),
                "reduction": "sum", "eos_policy": "one terminal EOS included"}

    @property
    def key(self):
        return digest(self.payload())


def reference_request(bank, pair, side):
    if side not in ("positive", "negative"):
        raise ValueError("Unknown preference side")
    ref = next(r for r in bank.warmstart_references if r.agent == pair["agent"])
    if pair["reference"] != dataclasses.asdict(ref):
        raise ValueError("Preference reference differs from bank's frozen warm start")
    candidate = pair[side]
    if (candidate["context_hash"] != digest(pair["prompt"])
            or tuple(candidate["prompt_ids"]) != tuple(pair["prompt_ids"])):
        raise ValueError("Preference candidate prompt mismatch")
    return ReferenceRequest(ref.kind, ref.agent, ref.adapter_hash, bank.base_snapshot,
                            bank.tokenizer_revision, bank.template_hash, bank.precision,
                            bank.runtime_fingerprint, pair["prompt"], tuple(pair["prompt_ids"]),
                            candidate["raw"], tuple(candidate["completion_ids"]), bank.eos_id)


class ReferenceCache:
    def __init__(self, root: Path):
        self.root = root

    def get(self, request):
        value = read_json(self.root / f"{request.key}.json")  # Missing never falls back to base/current actor.
        if (value.get("schema_version") != 1 or value.get("key") != request.key
                or canonical(value.get("request")) != canonical(request.payload())
                or value.get("token_count") != len(request.completion_ids)):
            raise ValueError("Reference cache identity/mask mismatch")
        score = finite(value["sum_logp"], "reference log probability")
        if score > 0 or value.get("checksum") != digest({k: v for k, v in value.items() if k != "checksum"}):
            raise ValueError("Reference cache score/checksum mismatch")
        return score

    def put(self, request, sum_logp):
        score = finite(sum_logp, "reference log probability")
        if score > 0:
            raise ValueError("Reference log probability must be <=0")
        value = {"schema_version": 1, "key": request.key, "request": request.payload(),
                 "token_count": len(request.completion_ids), "sum_logp": score}
        value["checksum"] = digest(value)
        with run_lock(self.root):
            path = self.root / f"{request.key}.json"
            if path.exists():
                if self.get(request) != score:
                    raise ValueError("Cannot overwrite an immutable reference score")
                return
            write_json(path, value)
            self.get(request)
