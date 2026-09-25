"""Immutable scored-bank contract, deliberately distinct from validation handoffs.

This validates supplied records; producing verified neural scores and authoritative
training-source manifests remains the responsibility of the future collector.
"""
from __future__ import annotations

import dataclasses
import re
from pathlib import Path

from ..schemas import TaskLabel
from ..util import digest, read_json
from .assignment import finite, standardize_answer_nll, solve_assignment, loss_coefficients


def sha(value, name="hash", length=64):
    if not isinstance(value, str) or not re.fullmatch(rf"[0-9a-f]{{{length}}}", value):
        raise ValueError(f"Invalid {name}")


def token_ids(values, name):
    if not values or any(type(x) is not int or x < 0 for x in values):
        raise ValueError(f"{name} must contain nonnegative integer token IDs")


@dataclasses.dataclass(frozen=True)
class BankRow:
    row_id: str
    task_id: str
    split: str
    source_hash: str
    label_hash: str
    allowed_answers: tuple[str, ...]
    gold: str
    initial_correct: tuple[bool, ...]
    answer_nll: tuple[float, ...]
    delta: tuple[float | None, ...]
    private_pair_ids: tuple[str | None, ...]


@dataclasses.dataclass(frozen=True)
class Candidate:
    raw: str
    context_hash: str
    prompt_ids: tuple[int, ...]
    completion_ids: tuple[int, ...]
    stop_reason: str


@dataclasses.dataclass(frozen=True)
class ReceiverContext:
    row_id: str
    agent: int
    prompt: str
    prompt_ids: tuple[int, ...]
    has_helpful_peer: bool
    has_misleading_peer: bool
    candidates: tuple[Candidate, ...]


@dataclasses.dataclass(frozen=True)
class WarmstartReference:
    agent: int
    kind: str
    adapter_hash: str


@dataclasses.dataclass(frozen=True)
class ScoredBank:
    schema_version: int
    kind: str
    split: str
    actor_snapshot: str
    base_snapshot: str
    data_manifest_hash: str
    tokenizer_revision: str
    template_hash: str
    precision: str
    runtime_fingerprint: str
    eos_id: int
    warmstart_references: tuple[WarmstartReference, ...]
    rows: tuple[BankRow, ...]
    receivers: tuple[ReceiverContext, ...]
    context_limit: int = 4096

    @property
    def identity(self):
        return digest(self)

    def validate(self, *, allow_synthetic=False):
        if self.schema_version != 1 or type(self.schema_version) is not int:
            raise ValueError("Unsupported scored-bank schema")
        if self.kind not in ("training", "synthetic_fixture") or self.split != "train":
            raise ValueError("Only explicit training banks are accepted; validation/test handoffs are not training data")
        if self.kind == "synthetic_fixture" and not allow_synthetic:
            raise ValueError("Synthetic training fixtures require explicit opt-in")
        for value in (self.actor_snapshot, self.base_snapshot, self.data_manifest_hash, self.template_hash, self.runtime_fingerprint):
            sha(value)
        sha(self.tokenizer_revision, "tokenizer revision", 40)
        if self.precision not in ("bfloat16", "float16", "float32"):
            raise ValueError("Unsupported precision")
        if type(self.eos_id) is not int or self.eos_id < 0 or type(self.context_limit) is not int or self.context_limit < 2:
            raise ValueError("Invalid EOS/context limit")
        if len(self.warmstart_references) != 3 or {r.agent for r in self.warmstart_references} != {0, 1, 2}:
            raise ValueError("Three explicit per-agent warm-start references required")
        for reference in self.warmstart_references:
            if type(reference.agent) is not int or reference.kind != "warm_start_adapter":
                raise ValueError("Reference must be a frozen warm-start adapter, not base/current actor")
            sha(reference.adapter_hash, "warm-start adapter hash")
        if not self.rows or len({r.row_id for r in self.rows}) != len(self.rows):
            raise ValueError("Bank rows must be nonempty and unique")
        rows = {r.row_id: r for r in self.rows}
        for row in self.rows:
            for value in (row.row_id, row.source_hash, row.label_hash):
                sha(value)
            if row.split != "train" or not row.task_id or row.task_id.startswith("gpqa_"):
                raise ValueError("Every training derivative must inherit the train split")
            if (not 2 <= len(row.allowed_answers) <= 26 or len(set(row.allowed_answers)) != len(row.allowed_answers)
                    or any(x not in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' or len(x) != 1 for x in row.allowed_answers)
                    or row.gold not in row.allowed_answers):
                raise ValueError("Invalid evaluator answer IDs")
            if digest(TaskLabel(row.task_id, row.gold)) != row.label_hash:
                raise ValueError("Evaluator label hash mismatch")
            if any(len(x) != 3 for x in (row.initial_correct, row.answer_nll, row.delta, row.private_pair_ids)):
                raise ValueError("Each bank row must have exactly three agents")
            if any(type(x) is not bool for x in row.initial_correct):
                raise ValueError("Initial correctness must be boolean")
            if any(finite(x, "answer NLL") < 0 for x in row.answer_nll):
                raise ValueError("Answer NLL must be nonnegative")
            for credit, pair_id in zip(row.delta, row.private_pair_ids):
                if credit is None:
                    if pair_id is not None:
                        raise ValueError("Missing credit must have no usable pair ID")
                else:
                    if not -1 <= finite(credit, "credit") <= 1:
                        raise ValueError("Credit outside [-1,1]")
                    sha(pair_id, "private replay pair ID")
        seen = set()
        for context in self.receivers:
            if context.row_id not in rows or type(context.agent) is not int or context.agent not in (0, 1, 2):
                raise ValueError("Receiver must belong to an existing training row/agent")
            if not isinstance(context.prompt, str) or not context.prompt:
                raise ValueError("Receiver prompt required")
            token_ids(context.prompt_ids, "prompt")
            if len(context.prompt_ids) >= self.context_limit:
                raise ValueError("Receiver prompt exceeds context budget")
            key = (context.row_id, context.agent, digest(context.prompt))
            if key in seen:
                raise ValueError("Duplicate receiver context")
            seen.add(key)
            if type(context.has_helpful_peer) is not bool or type(context.has_misleading_peer) is not bool:
                raise ValueError("Receiver strata require boolean evaluator metadata")
            if len(context.candidates) > 4:
                raise ValueError("Receiver candidate cap is four; no implicit expanded search")
            for candidate in context.candidates:
                if not isinstance(candidate.raw, str) or candidate.stop_reason not in ("eos", "length", "context_overflow"):
                    raise ValueError("Invalid candidate text/stop reason")
                if candidate.context_hash != digest(context.prompt) or candidate.prompt_ids != context.prompt_ids:
                    raise ValueError("Cross-context preference candidate: prompt bytes/token prefix differ")
                # An overflow/interruption can produce no tokens. Retain it for
                # missingness accounting; the preference parser cannot select it.
                if candidate.completion_ids or candidate.stop_reason == "eos":
                    token_ids(candidate.completion_ids, "completion")
                if len(context.prompt_ids) + len(candidate.completion_ids) > self.context_limit:
                    raise ValueError("Candidate exceeds context budget; truncation forbidden")
                if candidate.stop_reason == "eos" and (candidate.completion_ids[-1] != self.eos_id or self.eos_id in candidate.completion_ids[:-1]):
                    raise ValueError("Completed candidate must include exactly one terminal EOS")
        return self


def bank_from_dict(data, *, allow_synthetic=False):
    def construct(cls, value):
        if not isinstance(value, dict) or set(value) - {f.name for f in dataclasses.fields(cls)}:
            raise ValueError(f"Unexpected {cls.__name__} fields; no handoff-to-training conversion")
        return cls(**value)
    data = dict(data)
    for name in ("rows", "receivers", "warmstart_references"):
        if not isinstance(data.get(name), list):
            raise ValueError(f"Scored bank requires {name}; validation handoffs are not training banks")
    rows = []
    for raw in data["rows"]:
        raw = dict(raw)
        for field in ("allowed_answers", "initial_correct", "answer_nll", "delta", "private_pair_ids"):
            raw[field] = tuple(raw[field])
        rows.append(construct(BankRow, raw))
    receivers = []
    for raw in data["receivers"]:
        raw = dict(raw)
        raw["prompt_ids"] = tuple(raw["prompt_ids"])
        raw["candidates"] = tuple(construct(Candidate, {**c, "prompt_ids": tuple(c["prompt_ids"]),
                                      "completion_ids": tuple(c["completion_ids"])}) for c in raw["candidates"])
        receivers.append(construct(ReceiverContext, raw))
    data.update(rows=tuple(rows), receivers=tuple(receivers),
                warmstart_references=tuple(construct(WarmstartReference, x) for x in data["warmstart_references"]))
    return construct(ScoredBank, data).validate(allow_synthetic=allow_synthetic)


def read_bank(path: Path, *, allow_synthetic=False):
    if path.stat().st_size > 100 * 1024**2:
        raise ValueError("Scored bank exceeds local size bound")
    return bank_from_dict(read_json(path), allow_synthetic=allow_synthetic)


def assign_bank(bank, *, allow_synthetic=False, nll_mode="standardized", gamma=1.0, tau=0.2, balance=0.1):
    bank.validate(allow_synthetic=allow_synthetic)
    if finite(gamma, "gamma") < 0:
        raise ValueError("gamma must be nonnegative")
    values, stats = standardize_answer_nll([r.answer_nll for r in bank.rows], split=bank.split,
                                          snapshot=bank.actor_snapshot, bank_hash=bank.identity, mode=nll_mode)
    costs = [[nll - gamma * credit if credit is not None else None for nll, credit in zip(row, record.delta)]
             for row, record in zip(values, bank.rows)]
    solution = solve_assignment(costs, tau=tau, balance=balance)
    coefficients = loss_coefficients(solution["weights"], [r.initial_correct for r in bank.rows])
    return {"schema_version": 1, "kind": bank.kind, "bank_hash": bank.identity, "actor_snapshot": bank.actor_snapshot,
            "training_executed": False, "row_ids": [r.row_id for r in bank.rows], "normalization": stats,
            "settings": {"gamma": gamma, "tau": tau, "balance": balance}, "costs": costs,
            "solver": solution, "coefficients": coefficients,
            "base_only_rows": [r.row_id for b, r in enumerate(bank.rows) if b not in solution["eligible_rows"]]}
