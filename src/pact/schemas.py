from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, kw_only=True)
class Record:
    schema_version: int = field(default=1, init=False)


@dataclass(frozen=True)
class Option(Record):
    answer_id: str
    text: str
    source_label: str


@dataclass(frozen=True)
class TaskInput(Record):
    task_id: str
    family: str
    split: str
    source_id: str
    dataset_revision: str
    source_hash: str
    question: str
    options: tuple[Option, ...]
    context: str = ""


@dataclass(frozen=True)
class TaskLabel(Record):
    task_id: str
    answer_id: str


@dataclass(frozen=True)
class Message(Record):
    role: str
    content: str


@dataclass(frozen=True)
class CallRecord(Record):
    actor: str
    phase: str
    snapshot: str
    seed: int
    messages: tuple[Message, ...]
    rendered_prompt: str
    context_hash: str
    template_hash: str
    parameters_json: str
    input_tokens: int
    output_tokens: int
    stop_reason: str
    elapsed_seconds: float


@dataclass(frozen=True)
class PrivatePacket(Record):
    task_id: str
    agent: int
    raw: str
    answer_id: str | None
    explanation: str
    parser_status: str
    call: CallRecord


@dataclass(frozen=True)
class RevisionPacket(PrivatePacket):
    pass


@dataclass(frozen=True)
class DeliveredMessage(Record):
    sender: int
    recipient: int
    text: str
    source_packet_hash: str


@dataclass(frozen=True)
class AttackRecord(Record):
    attack_id: str
    task_id: str
    channel: str
    template: str
    payload: str
    sender: int | None
    target_answer: str | None
    recipient_count: int
    payload_tokens: int
    split: str
    dataset_revision: str
    source_hash: str
    provenance: str = "fixed_pool_v1; label-aware incorrect target; no feedback queries"


@dataclass(frozen=True)
class Trajectory(Record):
    trajectory_id: str
    task: TaskInput
    method: str
    condition: str
    status: str
    snapshot: str
    seed: int
    attack: AttackRecord
    private: tuple[PrivatePacket, ...]
    delivered: tuple[DeliveredMessage, ...]
    revised: tuple[RevisionPacket, ...]
    final: PrivatePacket | None
    calls: tuple[CallRecord, ...]
    readout_low_trust_tokens: int = 0
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReplayPair(Record):
    pair_id: str
    trajectory_id: str
    task_id: str
    split: str
    dataset_revision: str
    source_hash: str
    attack_id: str
    snapshot: str
    agent: int
    initial_correct: bool
    candidates: tuple[PrivatePacket, ...]
    status: str
    reason: str | None
    positive_index: int | None
    negative_index: int | None
    length_matched: bool | None
    suffix_seeds: tuple[int, ...]
    positive_suffixes: tuple[Trajectory, ...]
    negative_suffixes: tuple[Trajectory, ...]
    paired_differences: tuple[int, ...]
    q_plus: float | None
    q_minus: float | None
    delta: float | None


@dataclass(frozen=True)
class PreferencePair(Record):
    # Eligibility probe only: no optimizer/reference scores are implemented at M0–2.
    trajectory_id: str
    task_id: str
    agent: int
    stratum: str
    context_hash: str
    candidates: tuple[RevisionPacket, ...]
    positive_index: int | None
    negative_index: int | None
    status: str
    provenance: str = "natural delivered same-task peers; answer checks do not verify rationale"


@dataclass(frozen=True)
class ResponsibilityRecord(Record):
    task_id: str
    snapshot: str
    status: str = "not_implemented"


@dataclass(frozen=True)
class RunManifest(Record):
    run_id: str
    config_hash: str
    code: dict[str, Any]
    model_identity: dict[str, Any]
    data_manifest_hash: str
    seed: int
    stage_status: dict[str, str]
    expected_records: int
    completed_records: int
    invocation: tuple[str, ...]
    scientific_status: str
    runtime_fingerprint: str


@dataclass(frozen=True)
class Rate(Record):
    numerator: int
    denominator: int
    value: float | None
    reason: str | None = None


def task_from_dict(data: dict) -> TaskInput:
    data = dict(data)
    data.pop("schema_version", None)
    options = []
    for option in data.pop("options"):
        option = dict(option)
        option.pop("schema_version", None)
        options.append(Option(**option))
    return TaskInput(**data, options=tuple(options))
