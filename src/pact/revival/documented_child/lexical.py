"""Child-only lexical components; original splits retained, no GPQA training conversion.

Uses the existing exact-ID/content and trigram >=0.9 transitive algorithm.
The historical training validator is unchanged.
"""
from collections import defaultdict, Counter
from ...datasets import content_group
from ...training.data import _norm, _shingles
from ...util import digest

def audit_components(training, validation):
    """Group exact IDs/content and >=0.9 Jaccard word-trigram copies transitively.

    This reproducible lexical screen is not a semantic paraphrase detector.
    Labels only diagnose inconsistent exact duplicates, never control similarity.
    """
    records = sorted([*training, *validation], key=lambda p: (p[0].split, p[0].task_id))
    for pool, split in ((training, "train"), (validation, "validation")):
        if not pool or any(t.split not in (("train", "prospective_development") if split == "train" else ("validation",)) for t, _ in pool):
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
        train = [i for i in members if records[i][0].split in ("train", "prospective_development")]
        if not train:
            continue
        group_id = digest([key(i) for i in members])
        validation_overlap = any(records[i][0].split == "validation" for i in members)
        conflict = any((records[i][0].split, records[i][0].task_id) in conflict_keys for i in members)
        reason = "validation_overlap" if validation_overlap else "conflicting_duplicate_labels" if conflict else None
        kept = None if reason else min(train, key=lambda i: records[i][0].task_id)
        if members:
            groups.append({"group_id": group_id, "members": [key(i) for i in members],
                           "validation_overlap": validation_overlap, "label_conflict": conflict,
                           "representative": records[kept][0].task_id if kept is not None else None})
        for i in train:
            if i == kept:
                representatives.append((records[i], group_id))
            else:
                exclusions.append({"task_id": records[i][0].task_id, "group_id": group_id,
                                   "reason": reason or "duplicate_training_group"})
    audit = {"schema_version": 1, "policy": "exclude candidate components touching validation; quarantine label conflicts; one candidate representative per component",
             "exact": "source ID or normalized context/question/sorted option texts",
             "lexical": "word-trigram set Jaccard >= 9/10; transitive components; case/punctuation insensitive",
             "semantic_paraphrase_audit": "not_run; lexical screening does not establish absence of semantic paraphrases",
             "final_test_accessed": False, "source_candidate_rows": len(training), "validation_rows": len(validation),
             "eligible_rows": len(representatives), "groups": groups, "edges": edges,
             "label_conflicts": conflicts, "exclusions": sorted(exclusions, key=lambda x: x["task_id"])}
    return representatives, audit

