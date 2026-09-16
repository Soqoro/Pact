from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..config import Config
from ..schemas import Message, TaskInput, CallRecord
from ..util import digest, canonical


@dataclass(frozen=True)
class Request:
    task: TaskInput
    messages: tuple[Message, ...]
    actor: str
    phase: str
    seed: int
    max_tokens: int
    deterministic: bool = False


def cache_key(request: Request, identity: dict, config: Config, rendered: str) -> str:
    # No generation cache is enabled yet; this contract prevents future unsafe reuse.
    return digest({"request": canonical(request), "identity": identity, "config": canonical(config), "rendered": rendered})


class Backend(Protocol):
    identity: dict
    calls: list[CallRecord]

    def generate(self, request: Request) -> tuple[str, CallRecord]: ...
    def count_tokens(self, text: str) -> int: ...
    def truncate(self, text: str, tokens: int) -> str: ...
    def resource_usage(self) -> dict: ...


def create_backend(config: Config, cache_dir):
    if config.backend == "mock":
        from .mock import MockBackend
        return MockBackend(config)
    from .transformers import TransformersBackend
    return TransformersBackend(config, cache_dir)
