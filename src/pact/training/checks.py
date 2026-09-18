"""Explicit synthetic CPU round trip, never a training or benchmark result."""
from __future__ import annotations

from pathlib import Path

from ..schemas import TaskLabel
from ..util import canonical, digest, write_json
from .bank import BankRow, Candidate, ReceiverContext, ScoredBank, WarmstartReference, assign_bank, read_bank
from .losses import dpo_loss
from .preferences import build_preferences
from .reference import ReferenceCache, reference_request


def fixture_bank():
    rows = []
    for index, (correct, nll, credit) in enumerate([
            ((True, False, False), (0.2, 1.1, 0.8), (1., None, 0.)),
            ((False, True, True), (1.3, 0.3, 0.5), (0.5, 0., None)),
            ((False, False, False), (1.5, 1.2, 1.4), (None, None, None))]):
        task_id = f"synthetic-training-fixture:{index}"
        rows.append(BankRow(digest(task_id), task_id, "train", digest(["synthetic", index]),
                            digest(TaskLabel(task_id, "A")), ("A", "B"), "A", correct, nll, credit,
                            tuple(digest([index, i, "pair"]) if d is not None else None for i, d in enumerate(credit))))
    receivers = []
    for index, agent, answers in [(0, 0, ("A", "B")), (0, 1, ("B", "A")), (1, 1, ("A", "A"))]:
        prompt = f"Synthetic receiver context {index}/{agent}. Respond with a packet."
        ids = tuple(ord(c) + 1 for c in prompt)
        candidates = []
        for answer in answers:
            raw = canonical({"answer": answer, "justification": "Synthetic test explanation."})
            candidates.append(Candidate(raw, digest(prompt), ids, tuple(ord(c) + 1 for c in raw) + (0,), "eos"))
        receivers.append(ReceiverContext(rows[index].row_id, agent, prompt, ids, True, True, tuple(candidates)))
    return ScoredBank(1, "synthetic_fixture", "train", digest("fixture-actor"), digest("fixture-base"),
                      digest("fixture-training-manifest"), "0" * 40, digest("fixture-template"), "float32",
                      digest("fixture-runtime"), 0,
                      tuple(WarmstartReference(i, "warm_start_adapter", digest(["fixture-warm-start", i])) for i in range(3)),
                      tuple(rows), tuple(receivers))


def training_check(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=False)
    bank = fixture_bank()
    write_json(output_dir / "bank.json", bank)
    bank = read_bank(output_dir / "bank.json", allow_synthetic=True)
    assignments = assign_bank(bank, allow_synthetic=True)
    if assignments["solver"]["status"] != "converged":
        raise RuntimeError("Synthetic assignment check did not converge")
    preferences = build_preferences(bank, allow_synthetic=True)
    cache = ReferenceCache(output_dir / "synthetic-reference-cache")
    loss = 0.0
    for pair in preferences["pairs"]:
        requests = [reference_request(bank, pair, side) for side in ("positive", "negative")]
        # Deliberately invented log probabilities; no model is called.
        for request, score in zip(requests, (-4., -5.)):
            cache.put(request, score)
        refs = [cache.get(request) for request in requests]
        loss += pair["revision_coefficient"] * dpo_loss(-3., -6., *refs)
    write_json(output_dir / "assignments.json", assignments)
    write_json(output_dir / "preferences.json", preferences)
    summary = {"status": "cpu_fixture_only_no_model_training", "training_executed": False,
               "bank_hash": bank.identity, "assignment_status": assignments["solver"]["status"],
               "eligible_rows": len(assignments["solver"]["eligible_rows"]),
               "base_only_rows": len(assignments["base_only_rows"]),
               "pair_counts": preferences["pair_counts"], "synthetic_revision_loss": loss,
               "output_dir": str(output_dir)}
    write_json(output_dir / "summary.json", summary)
    return summary
