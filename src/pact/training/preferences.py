"""Same-prompt receiver preference construction with explicit missingness."""
from __future__ import annotations

import dataclasses
from collections import Counter

from ..parsing import parse_answer
from ..util import digest


def build_preferences(bank, *, allow_synthetic=False, length_bin=32):
    bank.validate(allow_synthetic=allow_synthetic)
    if type(length_bin) is not int or length_bin < 1:
        raise ValueError("Length bin must be a positive integer")
    rows = {r.row_id: r for r in bank.rows}
    pairs, accounting = [], []
    for context in bank.receivers:
        row = rows[context.row_id]
        stratum = ("hold" if row.initial_correct[context.agent] and context.has_misleading_peer
                   else "repair" if not row.initial_correct[context.agent] and context.has_helpful_peer
                   else "ineligible_context")
        parsed = [parse_answer(c.raw, row.allowed_answers, stop_reason=c.stop_reason) for c in context.candidates]
        positive = [i for i, (answer, _, status) in enumerate(parsed) if status == "ok" and answer == row.gold]
        negative = [i for i, (answer, _, status) in enumerate(parsed) if status == "ok" and answer != row.gold]
        record = {"context_id": digest(context), "row_id": row.row_id, "agent": context.agent,
                  "stratum": stratum, "candidate_count": len(parsed),
                  "parser_counts": dict(Counter(p[2] for p in parsed)),
                  "correct_count": len(positive), "incorrect_count": len(negative)}
        reason = ("ineligible_context" if stratum == "ineligible_context" else
                  "missing_both" if not positive and not negative else
                  "missing_correct" if not positive else "missing_incorrect" if not negative else None)
        record["missing_reason"] = reason
        accounting.append(record)
        if reason:
            continue
        def rank(pair):
            a, b = (len(context.candidates[i].completion_ids) for i in pair)
            return (a // length_bin != b // length_bin, abs(a - b), *pair)
        p, n = min(((p, n) for p in positive for n in negative), key=rank)
        reference = next(r for r in bank.warmstart_references if r.agent == context.agent)
        pairs.append({**record, "prompt": context.prompt, "prompt_ids": context.prompt_ids,
                      "positive_index": p, "negative_index": n, "length_matched": not rank((p, n))[0],
                      "positive": dataclasses.asdict(context.candidates[p]),
                      "negative": dataclasses.asdict(context.candidates[n]),
                      "reference": dataclasses.asdict(reference)})
    counts = {s: sum(p["stratum"] == s for p in pairs) for s in ("hold", "repair")}
    ready = all(counts.values())
    # Full revision loss gives equal total mass to each stratum. A missing stratum
    # does not silently turn the requested objective into a different ablation.
    for pair in pairs:
        pair["revision_coefficient"] = 0.5 / counts[pair["stratum"]] if ready else None
    return {"schema_version": 1, "kind": bank.kind, "bank_hash": bank.identity,
            "actor_snapshot": bank.actor_snapshot, "training_executed": False,
            "length_bin": length_bin, "eos_in_length": True, "pairs": pairs,
            "contexts": accounting, "pair_counts": counts, "full_revision_ready": ready,
            "missing_strata": [s for s, count in counts.items() if not count]}
