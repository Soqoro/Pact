"""Train-only source preparation, conservative grouping, and frozen task manifests.

No model calls, final-test sources, split relabeling, or dataset-script execution.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import re
import urllib.request

from ..datasets import (ARC_REVISION, LOGIQA_REVISION, SOURCES, _parse_arc,
                        _parse_logiqa, content_group, parse_arc, parse_logiqa)
from ..schemas import TaskLabel, task_from_dict
from ..util import atomic_write, digest, file_hash, read_json, write_json


TRAIN_SOURCES = {
    "arc_challenge": {
        "url": f"https://huggingface.co/datasets/allenai/ai2_arc/resolve/{ARC_REVISION}/ARC-Challenge/train-00000-of-00001.parquet",
        "revision": ARC_REVISION, "filename": "arc_train.parquet",
        "sha256": "e488c1587ffdcfc8443f916c53488a95cd471c5790e0746c6bfe4cecf20962cb",
        "expected_rows": 1119, "official_split": "train", "license": SOURCES["arc_challenge"]["license"],
    },
    "logiqa": {
        "url": f"https://raw.githubusercontent.com/lgw863/LogiQA-dataset/{LOGIQA_REVISION}/Train.txt",
        "revision": LOGIQA_REVISION, "filename": "logiqa_train.txt",
        "sha256": "7d5bb1f58278e33b395744cd2ad8d7600faa0b3c4d615c659a44ec1181d759fa",
        "expected_rows": 7376, "official_split": "Train.txt (English training)", "license": SOURCES["logiqa"]["license"],
    },
}
MAX_SOURCE_BYTES = 20 * 1024**2
ARTIFACT_FILES = ("manifest.json", "tasks.json", "labels.json", "overlap_audit.json")


def parse_arc_train(rows, source_hash):
    return _parse_arc(rows, source_hash, split="train")


def parse_logiqa_train(text, source_hash):
    return _parse_logiqa(text, source_hash, split="train")


def _source_file(cache_dir, source, *, download):
    path = cache_dir / source["filename"]
    if not path.exists():
        if not download:
            raise FileNotFoundError(f"Missing pinned source {path}; use --download explicitly to fetch train/validation files")
        with urllib.request.urlopen(source["url"], timeout=60) as response:
            data = response.read(MAX_SOURCE_BYTES + 1)
        if len(data) > MAX_SOURCE_BYTES or hashlib.sha256(data).hexdigest() != source["sha256"]:
            raise ValueError(f"Downloaded source size/checksum mismatch: {source['filename']}")
        atomic_write(path, data)
    if path.stat().st_size > MAX_SOURCE_BYTES or file_hash(path) != source["sha256"]:
        raise ValueError(f"Cached source size/checksum mismatch: {path}")
    return path


def load_training_sources(cache_dir: Path, *, download=False):
    """Load ALL pinned train/validation records; validation slices are insufficient."""
    records = {"train": [], "validation": []}
    for split, sources in (("train", TRAIN_SOURCES), ("validation", SOURCES)):
        for family, source in sorted(sources.items()):
            path = _source_file(cache_dir, source, download=download)
            if family == "arc_challenge":
                try:
                    import pyarrow.parquet as pq
                except ImportError as exc:
                    raise RuntimeError("Install pact-research[data] to load ARC parquet") from exc
                parser = parse_arc_train if split == "train" else parse_arc
                rows = parser(pq.read_table(path).to_pylist(), source["sha256"])
            else:
                parser = parse_logiqa_train if split == "train" else parse_logiqa
                rows = parser(path.read_text(encoding="utf-8"), source["sha256"])
            if len(rows) != source["expected_rows"]:
                raise ValueError(f"Unexpected {family}/{split} row count: {len(rows)}")
            records[split].extend(rows)
    return records["train"], records["validation"]


def _norm(text):
    return " ".join(re.findall(r"\w+", text.casefold()))


def _shingles(task):
    # Options sorted by normalized text: reordering answer labels cannot hide a copy.
    words = " ".join([_norm(task.context), _norm(task.question),
                      *sorted(_norm(o.text) for o in task.options)]).split()
    return {tuple(words[i:i+3]) for i in range(max(1, len(words)-2))}


def audit_training_overlap(training, validation):
    """Group exact IDs/content and >=0.9 Jaccard word-trigram copies transitively.

    This reproducible lexical screen is not a semantic paraphrase detector.
    Labels only diagnose inconsistent exact duplicates, never control similarity.
    """
    records = sorted([*training, *validation], key=lambda p: (p[0].split, p[0].task_id))
    for pool, split in ((training, "train"), (validation, "validation")):
        if not pool or any(t.split != split for t, _ in pool):
            raise ValueError(f"Expected a nonempty {split} pool; no split conversion")
        if len({t.task_id for t, _ in pool}) != len(pool):
            raise ValueError(f"Duplicate task IDs within {split}")
    for task, label in records:
        if label.task_id != task.task_id or label.answer_id not in [o.answer_id for o in task.options]:
            raise ValueError("Task/evaluator label mismatch")
    parent = list(range(len(records)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(a, b):
        a, b = find(a), find(b)
        parent[max(a, b)] = min(a, b)
    edges, conflicts = [], []
    ids, contents = {}, {}
    def key(i):
        t = records[i][0]
        return {"split": t.split, "task_id": t.task_id}
    def gold_text(i):
        t, label = records[i]
        return _norm(next(o.text for o in t.options if o.answer_id == label.answer_id))
    for i, (task, _) in enumerate(records):
        for index, group, reason in ((ids, (task.family, task.source_id), "source_id"),
                                     (contents, content_group(task), "normalized_content")):
            if group in index:
                j = index[group]
                union(i, j)
                edges.append({"left": key(j), "right": key(i), "reason": reason})
                if reason == "normalized_content" and gold_text(i) != gold_text(j):
                    conflicts.append({"left": key(j), "right": key(i), "reason": "conflicting_exact_duplicate_labels"})
            else:
                index[group] = i
    # Inverted index yields intersection counts without comparing every pair of sets.
    postings, sizes = defaultdict(list), []
    for i, (task, _) in enumerate(records):
        grams = _shingles(task)
        sizes.append(len(grams))
        intersections = Counter()
        for gram in grams:
            for j in postings[gram]:
                if 10 * min(len(grams), sizes[j]) >= 9 * max(len(grams), sizes[j]):
                    intersections[j] += 1
        for j, intersection in sorted(intersections.items()):
            union_size = len(grams) + sizes[j] - intersection
            if find(i) != find(j) and 10 * intersection >= 9 * union_size:
                union(i, j)
                edges.append({"left": key(j), "right": key(i), "reason": "lexical_near_duplicate",
                              "intersection": intersection, "union": union_size})
        for gram in grams:
            postings[gram].append(i)
    components = defaultdict(list)
    for i in range(len(records)):
        components[find(i)].append(i)
    conflict_keys = {(x[s]["split"], x[s]["task_id"]) for x in conflicts for s in ("left", "right")}
    groups, exclusions, representatives = [], [], []
    for members in components.values():
        train = [i for i in members if records[i][0].split == "train"]
        if not train:
            continue
        group_id = digest([key(i) for i in members])
        validation_overlap = any(records[i][0].split == "validation" for i in members)
        conflict = any((records[i][0].split, records[i][0].task_id) in conflict_keys for i in members)
        reason = "validation_overlap" if validation_overlap else "conflicting_duplicate_labels" if conflict else None
        kept = None if reason else min(train, key=lambda i: records[i][0].task_id)
        if len(members) > 1:
            groups.append({"group_id": group_id, "members": [key(i) for i in members],
                           "validation_overlap": validation_overlap, "label_conflict": conflict,
                           "representative": records[kept][0].task_id if kept is not None else None})
        for i in train:
            if i == kept:
                representatives.append((records[i], group_id))
            else:
                exclusions.append({"task_id": records[i][0].task_id, "group_id": group_id,
                                   "reason": reason or "duplicate_training_group"})
    audit = {"schema_version": 1, "policy": "exclude train components touching validation; quarantine label conflicts; one train representative per component",
             "exact": "source ID or normalized context/question/sorted option texts",
             "lexical": "word-trigram set Jaccard >= 9/10; transitive components; case/punctuation insensitive",
             "semantic_paraphrase_audit": "not_run; lexical screening does not establish absence of semantic paraphrases",
             "final_test_accessed": False, "training_rows": len(training), "validation_rows": len(validation),
             "eligible_rows": len(representatives), "groups": groups, "edges": edges,
             "label_conflicts": conflicts, "exclusions": sorted(exclusions, key=lambda x: x["task_id"])}
    return representatives, audit


def _validate_selection_settings(items, seed):
    if type(items) is not int or items < 2 or items > 1200 or items % 2:
        raise ValueError("Training selection requires an even item count in [2,1200]")
    if type(seed) is not int or not 0 <= seed < 2**31:
        raise ValueError("Seed must be an integer in [0,2**31)")


def select_training(training, validation, *, items, seed):
    _validate_selection_settings(items, seed)
    for pool in (training, validation):
        if {t.family for t, _ in pool} != set(TRAIN_SOURCES):
            raise ValueError("Both original QA families are required in train and full validation")
    representatives, audit = audit_training_overlap(training, validation)
    selected = []
    for family in sorted(TRAIN_SOURCES):
        eligible = [(record, group) for record, group in representatives if record[0].family == family]
        eligible.sort(key=lambda pair: (digest([seed, pair[1]]), pair[0][0].task_id))
        if len(eligible) < items // 2:
            raise ValueError(f"Insufficient eligible {family} training tasks after overlap exclusions")
        selected.extend(eligible[:items // 2])
    selected.sort(key=lambda pair: (digest([seed, pair[0][0].task_id]), pair[0][0].task_id))
    def entries(pool):
        return [{"task_id": t.task_id, "input_hash": digest(t), "label_hash": digest(l)}
                for t, l in sorted(pool, key=lambda p: p[0].task_id)]
    manifest = {"schema_version": 1, "kind": "frozen_training_tasks", "split": "train", "seed": seed,
                "requested": items, "realized": len(selected), "training_executed": False,
                "selection": "SHA256(seed, audited component); family-balanced prefixes; no outcome filtering",
                "training_pool_hash": digest(entries(training)), "validation_pool_hash": digest(entries(validation)),
                "overlap_audit_hash": digest(audit),
                "family_counts": {f: sum(t.family == f for (t, _), _g in selected) for f in sorted(TRAIN_SOURCES)},
                "selected": [{"task_id": t.task_id, "source_id": t.source_id, "group_id": g,
                              "content_group": content_group(t), "input_hash": digest(t), "label_hash": digest(l)}
                             for (t, l), g in selected]}
    return [t for (t, _), _g in selected], {l.task_id: l for (_, l), _g in selected}, manifest, audit


def prepare_training_data(cache_dir: Path, output_dir: Path, *, items, seed, download=False):
    _validate_selection_settings(items, seed)
    if output_dir.exists():
        raise ValueError("Training output exists; choose a new path to preserve the frozen manifest")
    training, validation = load_training_sources(cache_dir, download=download)
    tasks, labels, manifest, audit = select_training(training, validation, items=items, seed=seed)
    manifest["sources"] = {"train": TRAIN_SOURCES, "validation": SOURCES}
    output_dir.mkdir(parents=True, exist_ok=False)
    for name, value in zip(ARTIFACT_FILES, (manifest, tasks, labels, audit)):
        write_json(output_dir / name, value)
    checksums = {name: file_hash(output_dir / name) for name in ARTIFACT_FILES}
    # Verify the written payloads before publishing the last completion marker.
    for name in ARTIFACT_FILES:
        read_json(output_dir / name)
        if file_hash(output_dir / name) != checksums[name]:
            raise ValueError("Training artifact changed during preparation")
    _validate_payloads(*[read_json(output_dir / name) for name in ARTIFACT_FILES])
    write_json(output_dir / "checksums.json", checksums)
    read_training_data(output_dir)
    return {"status": "training_data_prepared_no_model_training", "output_dir": str(output_dir),
            "manifest_hash": digest(manifest), "realized": len(tasks), "family_counts": manifest["family_counts"],
            "excluded_rows": len(audit["exclusions"]), "semantic_paraphrase_audit": audit["semantic_paraphrase_audit"]}


def read_training_data(root: Path):
    checksums = read_json(root / "checksums.json")
    if set(checksums) != set(ARTIFACT_FILES):
        raise ValueError("Unexpected/incomplete training artifact inventory")
    for name in ARTIFACT_FILES:
        if (root / name).stat().st_size > MAX_SOURCE_BYTES or file_hash(root / name) != checksums[name]:
            raise ValueError(f"Training artifact checksum/size mismatch: {name}")
    return _validate_payloads(*[read_json(root / name) for name in ARTIFACT_FILES])


def _validate_payloads(manifest, task_data, label_data, audit):
    if (manifest.get("schema_version") != 1 or manifest.get("kind") != "frozen_training_tasks"
            or manifest.get("split") != "train" or manifest.get("sources") != {"train": TRAIN_SOURCES, "validation": SOURCES}
            or manifest.get("overlap_audit_hash") != digest(audit) or manifest.get("training_executed") is not False):
        raise ValueError("Training manifest provenance mismatch")
    _validate_selection_settings(manifest["requested"], manifest["seed"])
    tasks = [task_from_dict(t) for t in task_data]
    labels = {key: TaskLabel(v["task_id"], v["answer_id"]) for key, v in label_data.items()}
    if (len(tasks) != manifest["requested"] or len(tasks) != manifest["realized"]
            or len(tasks) != len(manifest["selected"]) or len({t.task_id for t in tasks}) != len(tasks)
            or set(labels) != {t.task_id for t in tasks}):
        raise ValueError("Incomplete or duplicate training task/label inventory")
    excluded = {r["task_id"] for r in audit["exclusions"]}
    for task, entry in zip(tasks, manifest["selected"]):
        source = TRAIN_SOURCES.get(task.family)
        label = labels[task.task_id]
        if (not source or task.split != "train" or task.source_hash != source["sha256"]
                or task.dataset_revision != source["revision"] or task.task_id in excluded
                or label.task_id != task.task_id or label.answer_id not in [o.answer_id for o in task.options]
                or (entry["task_id"], entry["source_id"], entry["input_hash"], entry["label_hash"], entry["content_group"])
                != (task.task_id, task.source_id, digest(task), digest(label), content_group(task))):
            raise ValueError("Selected training task/label provenance mismatch")
    counts = {f: sum(t.family == f for t in tasks) for f in sorted(TRAIN_SOURCES)}
    if counts != manifest["family_counts"] or len(set(counts.values())) != 1:
        raise ValueError("Training family balance mismatch")
    return tasks, labels, manifest, audit
