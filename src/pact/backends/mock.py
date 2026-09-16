from __future__ import annotations

import json
import re

from . import Request
from ..config import Config
from ..schemas import CallRecord
from ..util import canonical, digest


class MockBackend:
    """Synthetic scripted cases, never accepts real benchmarks or gold-label records."""
    def __init__(self, config: Config):
        self.config = config
        self.identity = {"backend": "mock", "version": "synthetic-v1", "model": "scripted-fixtures",
                         "condition": "mock_only", "snapshot": digest(["mock-v1", config.model]),
                         "template": "JSON messages", "runtime_fingerprint": "stdlib-mock-v1"}
        self.calls = []

    def count_tokens(self, text):
        return len(re.findall(r"\w+|[^\w\s]", text))

    def truncate(self, text, tokens):
        parts = list(re.finditer(r"\w+|[^\w\s]", text))
        return text if len(parts) <= tokens else text[:parts[tokens - 1].end()] if tokens else ""

    def generate(self, request: Request):
        if not request.task.family.startswith("mock_"):
            raise ValueError("The scripted mock backend accepts synthetic fixtures only")
        scenario = request.task.source_id.split("-")[-1]
        actor = int(request.actor.split("-")[-1]) if request.actor != "base" else 0
        data = json.loads(request.messages[-1].content)
        raw = ""
        if request.phase == "private":
            patterns = {"erasure": ["A", "B", "B"], "repair": ["B", "A", "B"],
                        "construction": ["B"] * 3, "readout_failure": ["A"] * 3, "missing": ["A"] * 3}
            answer = patterns.get(scenario, ["A" if request.seed % 2 else "B"] * 3)[actor % 3]
        elif request.phase == "revision":
            patterns = {"erasure": "B", "repair": "A", "construction": "A", "readout_failure": "A", "missing": "A", "zero": "B"}
            if scenario in patterns:
                answer = patterns[scenario]
            else:
                try:
                    own = json.loads(data["own_private"]["text"])["answer"]
                except (ValueError, KeyError):
                    own = "ABSTAIN"
                answer = own if scenario == "positive" else ("B" if own == "A" else "A")
        else:
            if scenario == "readout_failure":
                answer = "B"
            elif scenario in ("positive", "negative"):
                try:
                    answer = json.loads(data["packets"][0]["text"])["answer"]
                except (ValueError, KeyError):
                    answer = "ABSTAIN"
            else:
                answers = []
                for packet in data["packets"]:
                    try:
                        answers.append(json.loads(packet["text"])["answer"])
                    except (ValueError, KeyError):
                        pass
                answer = max(sorted(set(answers)), key=answers.count) if answers else "ABSTAIN"
        raw = canonical({"answer": answer} if request.phase == "final" else
                        {"answer": answer, "justification": "Deterministic synthetic fixture rationale."})
        rendered = canonical([{"role": m.role, "content": m.content} for m in request.messages])
        count = self.count_tokens(rendered)
        stop = "eos"
        if count + request.max_tokens > self.config.limits.context:
            raw, stop = "", "context_overflow"
        params = {"max_new_tokens": request.max_tokens, "do_sample": not request.deterministic,
                  "temperature": self.config.sampling.temperature, "top_p": self.config.sampling.top_p,
                  "top_k": self.config.sampling.top_k, "token_unit": "mock lexical tokens"}
        call = CallRecord(request.actor, request.phase, self.identity["snapshot"], request.seed,
                          request.messages, rendered, digest(rendered), digest("mock-json"), canonical(params),
                          count, self.count_tokens(raw), stop, 0.0)
        self.calls.append(call)
        return raw, call

    def resource_usage(self):
        return {"peak_allocated_bytes": None, "peak_reserved_bytes": None, "model_load_seconds": 0.0,
                "model_load_allocated_bytes": None, "compute_units": None, "cache_hits": 0}
