"""Offline planning for broader receiver feasibility; this module never loads models."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path

from ..config import Limits, ModelConfig, Sampling
from ..util import digest, read_json
from .bank import sha
from .data import read_training_data

FAMILIES = ("arc_challenge", "logiqa")
SELECTION_POLICY = "hash audited groups; exclude warmstart IDs/groups/content; 12 per family; interleave"


@dataclass(frozen=True)
class ReceiverFeasibilityConfig:
    data_manifest_hash: str
    warmstart_data_manifest_hash: str
    reference_manifest_hash: str
    reference_hashes: tuple[str, ...]
    base_snapshot: str
    runtime_fingerprint: str
    schema_version: int = 1
    purpose: str = "broader_train_only_receiver_feasibility"
    selection_seed: int = 20260919
    generation_seed: int = 1729
    items: int = 24
    conditions: tuple[str, ...] = ("clean", "exchange")
    receiver_candidates: int = 4

    def validate(self):
        for value in (self.data_manifest_hash, self.warmstart_data_manifest_hash,
                      self.reference_manifest_hash, self.base_snapshot, self.runtime_fingerprint,
                      *self.reference_hashes):
            sha(value)
        if len(self.reference_hashes) != 3 or len(set(self.reference_hashes)) != 3:
            raise ValueError("Three distinct ordered warm-start adapter hashes required")
        if (type(self.schema_version) is not int or self.schema_version != 1
                or self.purpose != "broader_train_only_receiver_feasibility"
                or type(self.items) is not int or self.items != 24
                or self.conditions != ("clean", "exchange")
                or type(self.receiver_candidates) is not int or self.receiver_candidates != 4):
            raise ValueError("This design fixes 24 tasks, clean/exchange and four receiver candidates")
        for seed in (self.selection_seed, self.generation_seed):
            if type(seed) is not int or not 0 <= seed < 2**31:
                raise ValueError("Seeds must be integers in [0,2**31)")
        return self


def load_receiver_config(path):
    data = read_json(Path(path))
    for field in ("reference_hashes", "conditions"):
        if field in data:
            data[field] = tuple(data[field])
    return ReceiverFeasibilityConfig(**data).validate()


def receiver_feasibility_plan(config, data_dir, warmstart_data_dir, selection_path=None):
    """Verify existing data locally and select by IDs/groups only, never outcomes.

    The CLI requires an already frozen selection. Omitting selection_path is only
    for producing that design artifact before publication or for offline tests.
    """
    config.validate()
    tasks, _, manifest, _ = read_training_data(Path(data_dir))
    warm_tasks, _, warm_manifest, _ = read_training_data(Path(warmstart_data_dir))
    if digest(manifest) != config.data_manifest_hash or digest(warm_manifest) != config.warmstart_data_manifest_hash:
        raise ValueError("Source/warm-start training manifest differs from recipe")
    for key in ("training_pool_hash", "validation_pool_hash", "overlap_audit_hash", "sources"):
        if manifest[key] != warm_manifest[key]:
            raise ValueError("Training selections do not share the same audited source pools")
    if (len(tasks) != 1200 or len(warm_tasks) != 12
            or Counter(t.family for t in tasks) != {f:600 for f in FAMILIES}
            or Counter(t.family for t in warm_tasks) != {f:6 for f in FAMILIES}
            or any(t.split != "train" for t in [*tasks, *warm_tasks])):
        raise ValueError("Expected the balanced 1200-task pool and 12-task train-only warm start")
    entries = {e['task_id']:e for e in manifest['selected']}
    for entry in warm_manifest['selected']:
        if entries.get(entry['task_id']) != entry:
            raise ValueError("Warm-start selection is not an unchanged subset of the source pool")
    if len({e['group_id'] for e in entries.values()}) != len(entries):
        raise ValueError("Pool contains repeated audited groups")
    excluded_ids = {t.task_id for t in warm_tasks}
    excluded_groups = {e['group_id'] for e in warm_manifest['selected']}
    excluded_content = {e['content_group'] for e in warm_manifest['selected']}
    eligible = {f:[] for f in FAMILIES}
    for task in tasks:
        entry = entries[task.task_id]
        if (task.task_id in excluded_ids or entry['group_id'] in excluded_groups
                or entry['content_group'] in excluded_content):
            continue
        eligible[task.family].append((task, entry))
    selected_by_family = {}
    for family in FAMILIES:
        ranked = sorted(eligible[family], key=lambda pair:
            (digest([config.selection_seed, 'receiver-feasibility-v1', pair[1]['group_id']]), pair[0].task_id))
        if len(ranked) < 12:
            raise ValueError("Insufficient eligible training groups; no replacement sampling")
        selected_by_family[family] = ranked[:12]
    selected = []
    for rank in range(12):
        for family in FAMILIES:
            task, entry = selected_by_family[family][rank]
            position = len(selected)
            selected.append({**entry, 'family':family, 'split':'train',
                             'position':position, 'exchange_sender':position % 3})
    selection = {'schema_version':1, 'kind':'receiver_feasibility_selection',
        'data_manifest_hash':digest(manifest), 'warmstart_data_manifest_hash':digest(warm_manifest),
        'selection_seed':config.selection_seed, 'selection_policy':SELECTION_POLICY,
        'excluded_warmstart_task_ids':sorted(excluded_ids), 'selected':selected}
    if selection_path is not None and read_json(Path(selection_path)) != selection:
        raise ValueError("Frozen task selection differs from reconstructed design")
    records = len(selected) * len(config.conditions)
    contexts = records * 3
    packet_calls = records * 6 + contexts * config.receiver_candidates
    final_calls = records
    limits = Limits()
    budget = {'tasks':len(selected), 'records':records, 'receiver_contexts_maximum':contexts,
        'main_generation_calls':records*7, 'receiver_generation_calls_upper_bound':contexts*4,
        'generation_calls_upper_bound':packet_calls+final_calls,
        'generated_tokens_upper_bound':packet_calls*limits.packet+final_calls*limits.final,
        'input_tokens_upper_bound':packet_calls*(limits.context-limits.packet)+final_calls*(limits.context-limits.final),
        'private_alternative_calls':0, 'suffix_replay_calls':0, 'teacher_forced_forwards':0,
        'optimizer_steps':0}
    return {'status':'receiver_feasibility_plan_only', 'execution_implemented':True,
        'gpu_verified':False, 'model_calls_executed':0, 'training_executed':False,
        'training_pairs_exported':False, 'config_hash':digest(config), 'config':asdict(config),
        'selection_hash':digest(selection), 'selection':selection, 'budget':budget,
        'runtime':{'model':asdict(ModelConfig()), 'limits':asdict(limits), 'sampling':asdict(Sampling())},
        'candidate_policy':'four fresh samples per eligible exact original receiver prompt; original revision excluded',
        'pair_rule':'valid correct and valid wrong; 32-token length-bin priority, distance, then indices; one per context',
        'decision_gate':{'per_stratum_minimum_pairs':6, 'per_stratum_minimum_distinct_tasks':3,
                         'per_stratum_required_families':list(FAMILIES),
                         'consequence':'review a separate bounded reference-scoring check; never auto-train'},
        'scope':'train-only diagnostic; no prompt changes, curated peers, actor updates or base-control arm'}
