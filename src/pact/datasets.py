"""Validation-only authoritative loaders. Labels never enter TaskInput."""
from __future__ import annotations

import hashlib
import re
import urllib.request
from pathlib import Path

from .config import Config
from .schemas import Option, TaskInput, TaskLabel
from .util import atomic_write, digest, file_hash, read_json, write_json, canonical

ARC_REVISION = "210d026faf9955653af8916fad021475a3f00453"
LOGIQA_REVISION = "ff6c4cbca47627b3ac2da94a29fa28204a167b41"
SOURCES = {
    "arc_challenge": {
        "url": f"https://huggingface.co/datasets/allenai/ai2_arc/resolve/{ARC_REVISION}/ARC-Challenge/validation-00000-of-00001.parquet",
        "revision": ARC_REVISION, "filename": "arc_validation.parquet",
        "sha256": "395a5c88d1580d69855fbaee9450270578df1ad5af6259771cd0a42c20e99f05",
        "license": "CC-BY-SA-4.0 (AllenAI dataset card)", "official_split": "validation", "expected_rows": 299,
    },
    "logiqa": {
        "url": f"https://raw.githubusercontent.com/lgw863/LogiQA-dataset/{LOGIQA_REVISION}/Eval.txt",
        "revision": LOGIQA_REVISION, "filename": "logiqa_eval.txt",
        "sha256": "4c49e6753b7262c001506b9151135abf722247035ab075dad93acdea5789c01f",
        "license": "No license file or explicit grant found in original repository; unresolved",
        "official_split": "Eval.txt (English validation)", "expected_rows": 651,
    },
}


def normalize(*, family: str, source_id: str, revision: str, source_hash: str,
              question: str, choices: list[tuple[str, str]], answer: str,
              context: str = "", split: str = "validation") -> tuple[TaskInput, TaskLabel]:
    if split != "validation":
        raise ValueError("This loader permits validation only")
    if not isinstance(question, str) or not question.strip() or not isinstance(context, str):
        raise ValueError("Question/context must be text and question nonempty")
    if not 2 <= len(choices) <= 26:
        raise ValueError("Expected 2–26 choices")
    if any(not isinstance(k, str) or not k or not isinstance(v, str) or not v.strip() for k, v in choices):
        raise ValueError("Invalid option")
    labels = [k for k, _ in choices]
    if len(set(labels)) != len(labels) or answer not in labels:
        raise ValueError("Duplicate option labels or unknown gold answer")
    options = tuple(Option(chr(65 + i), text, label) for i, (label, text) in enumerate(choices))
    task_id = f"{family}:{source_id}"
    task = TaskInput(task_id, family, split, source_id, revision, source_hash, question, options, context)
    return task, TaskLabel(task_id, options[labels.index(answer)].answer_id)


def parse_arc(rows: list[dict], source_hash: str) -> list[tuple[TaskInput, TaskLabel]]:
    result = []
    for row in rows:
        if set(row) != {"id", "question", "choices", "answerKey"}:
            raise ValueError("Unexpected ARC row schema")
        choices = row["choices"]
        if set(choices) != {"label", "text"} or len(choices["label"]) != len(choices["text"]):
            raise ValueError("Invalid ARC choices")
        result.append(normalize(family="arc_challenge", source_id=str(row["id"]),
                                revision=ARC_REVISION, source_hash=source_hash,
                                question=row["question"], choices=list(zip(choices["label"], choices["text"])),
                                answer=row["answerKey"]))
    if len({t.task_id for t, _ in result}) != len(result):
        raise ValueError("Duplicate ARC IDs")
    return result


def parse_logiqa(text: str, source_hash: str) -> list[tuple[TaskInput, TaskLabel]]:
    lines = text.splitlines()
    if not lines or len(lines) % 8:
        raise ValueError("Original English LogiQA requires exactly 8 lines per record")
    result = []
    for start in range(0, len(lines), 8):
        blank, answer, context, question, *options = lines[start:start + 8]
        if blank.strip() or answer not in ("a", "b", "c", "d"):
            raise ValueError(f"Invalid LogiQA block {start // 8}")
        choices = []
        for letter, option in zip("ABCD", options):
            if not option.strip():
                raise ValueError(f"Empty LogiQA option at block {start // 8}")
            # The original release defines options by LINE POSITION, and contains
            # translated/misplaced prefixes (e.g. 'In the B.NEC ...') and lowercase d.
            # Strip only an unambiguous matching leading prefix; preserve all other text.
            match = re.fullmatch(rf"{letter}(?:\.\s*|\s+)(.+)", option, flags=re.IGNORECASE)
            choices.append((letter.lower(), match.group(1) if match else option))
        result.append(normalize(family="logiqa", source_id=f"eval-{start // 8:04d}",
                                revision=LOGIQA_REVISION, source_hash=source_hash,
                                question=question, context=context, choices=choices, answer=answer))
    return result


def content_group(task: TaskInput) -> str:
    def norm(text):
        return " ".join(re.findall(r"\w+", text.casefold()))
    return digest([norm(task.context), norm(task.question), sorted(norm(o.text) for o in task.options)])


def overlaps(*collections: list[TaskInput]) -> list[dict]:
    groups: dict[str, list[TaskInput]] = {}
    for collection in collections:
        for task in collection:
            groups.setdefault(content_group(task), []).append(task)
    return [{"group": k, "task_ids": [t.task_id for t in v], "splits": sorted({t.split for t in v})}
            for k, v in sorted(groups.items()) if len(v) > 1]


def fixtures(items: int) -> list[tuple[TaskInput, TaskLabel]]:
    scenarios = ("erasure", "repair", "construction", "readout_failure", "positive", "negative", "zero", "missing")
    result = []
    for i in range(items):
        scenario = scenarios[i % len(scenarios)]
        family = "mock_arc" if i % 2 == 0 else "mock_logiqa"
        result.append(normalize(family=family, source_id=f"{i:03d}-{scenario}", revision="synthetic-v1",
                                source_hash=digest([i, scenario]), question="What is 1 + 1?",
                                context=f"Synthetic test fixture {i}: {scenario}. No benchmark claim.",
                                choices=[("1", "2"), ("2", "3"), ("3", "4")], answer="1"))
    return result


def prepare(config: Config, cache_dir: Path) -> tuple[list[TaskInput], dict[str, TaskLabel], dict]:
    if getattr(config, "selection", None):
        return prepare_selection(config, cache_dir)
    records = fixtures(config.items) if config.backend == "mock" else []
    if config.backend != "mock":
        cache_dir.mkdir(parents=True, exist_ok=True)
        for family, source in SOURCES.items():
            path = cache_dir / source["filename"]
            if not path.exists():
                with urllib.request.urlopen(source["url"], timeout=60) as response:
                    data = response.read(10 * 1024 * 1024 + 1)
                if len(data) > 10 * 1024 * 1024 or hashlib.sha256(data).hexdigest() != source["sha256"]:
                    raise ValueError(f"Source checksum/size mismatch: {family}")
                atomic_write(path, data)
            if file_hash(path) != source["sha256"]:
                raise ValueError(f"Cached source checksum mismatch: {path}")
            if family == "arc_challenge":
                try:
                    import pyarrow.parquet as pq
                except ImportError as exc:
                    raise RuntimeError("Install pact-research[data] to load ARC parquet") from exc
                rows = parse_arc(pq.read_table(path).to_pylist(), source["sha256"])
            else:
                rows = parse_logiqa(path.read_text(encoding="utf-8"), source["sha256"])
            if len(rows) != source["expected_rows"]:
                raise ValueError(f"Unexpected {family} validation count: {len(rows)}")
            records.extend(rows)
    all_tasks = [t for t, _ in records]
    selected = []
    for family in sorted({t.family for t in all_tasks}):
        rows = [(t, l) for t, l in records if t.family == family]
        # No local re-partitioning. Exact duplicate groups contribute one representative.
        unique = {}
        for task, label in sorted(rows, key=lambda pair: pair[0].task_id):
            group = content_group(task)
            # Synthetic scenarios intentionally share a QA but have distinct permitted contexts.
            if group in unique and unique[group][1].answer_id != label.answer_id:
                raise ValueError("Conflicting labels in a duplicate group")
            unique.setdefault(group, (task, label))
        ordered = sorted(unique.values(), key=lambda pair: digest([config.seed, content_group(pair[0])]))
        if len(ordered) < config.items // 2:
            raise ValueError("Insufficient unique validation items")
        selected.extend(ordered[:config.items // 2])
    selected.sort(key=lambda pair: digest([config.seed, pair[0].task_id]))
    manifest = {
        "schema_version": 1, "split": "validation", "seed": config.seed, "requested": config.items,
        "realized": len(selected), "selection": "SHA256(seed, normalized-content-group); family-balanced; nested prefixes",
        "sources": SOURCES if config.backend != "mock" else {"synthetic": "explicit mock fixtures"},
        "selected": [{"task_id": t.task_id, "source_id": t.source_id, "content_group": content_group(t),
                      "input_hash": digest(t), "label_hash": digest(l)} for t, l in selected],
        "duplicate_groups": overlaps(all_tasks),
        "cross_split_audit": "not_run: validation-only pilot does not fetch test data",
        "paraphrase_audit": "not_run; required before training/local repartitioning",
        "family_counts": {f: sum(t.family == f for t, _ in selected) for f in sorted({t.family for t, _ in selected})},
    }
    return [t for t, _ in selected], {l.task_id: l for _, l in selected}, manifest


def prepare_selection(config: Config, cache_dir: Path) -> tuple[list[TaskInput], dict[str, TaskLabel], dict]:
    """Reconstruct the original pool before selecting; never renumber attack sites."""
    import dataclasses
    from .config import config_from_dict
    selection = config.selection
    config.validate()
    parent = dataclasses.asdict(config)
    parent.pop("selection")
    parent.update(purpose="diagnostic_pilot", items=selection.source_items)
    tasks, labels, manifest = prepare(config_from_dict(parent), cache_dir)
    if digest(manifest) != selection.source_manifest_hash:
        raise ValueError("Source data manifest mismatch; do not silently reselect tasks")
    selected_tasks, entries = [], []
    for chosen in selection.tasks:
        task = tasks[chosen.source_position]
        entry = manifest["selected"][chosen.source_position]
        if (task.task_id, digest(task), digest(labels[task.task_id])) != (chosen.task_id, chosen.input_hash, chosen.label_hash):
            raise ValueError("Selected task position/input/label mismatch")
        selected_tasks.append(task)
        entries.append({**entry, "source_position": chosen.source_position})
    return selected_tasks, {t.task_id: labels[t.task_id] for t in selected_tasks}, {
        **manifest, "requested": config.items, "realized": len(selected_tasks), "selected": entries,
        "selection": "post-hoc mixed-initial tasks; selected engineering feasibility only; not representative performance",
        "selection_provenance": dataclasses.asdict(selection),
        "family_counts": {family: sum(t.family == family for t in selected_tasks)
                          for family in sorted({t.family for t in selected_tasks})},
    }
