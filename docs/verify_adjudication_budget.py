#!/usr/bin/env python3
"""Verify ONLY the proposed design arithmetic. No model/data/network execution."""
from __future__ import annotations
import argparse
import json
from pathlib import Path


def verify(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    for item in d["datasets"]:
        n, e = item["tasks"], item["audit_reported_eligible_attack_tasks"]
        if not isinstance(n, int) or not isinstance(e, int) or not 0 <= e <= n:
            raise ValueError("Invalid task/eligibility design count")
    judges = len(d["judges"])
    modes = len(d["clean_modes"])
    variants = len(d["attack_types"]) + len(d["control_types"])
    victims = judges * len(d["attacked_modes_per_judge"])
    cap = d["max_new_tokens_all_calls"]
    rows = []
    for item in d["datasets"]:
        n, e = item["tasks"], item["audit_reported_eligible_attack_tasks"]
        clean = n * judges * modes
        acquire = e * variants * d["attempts_per_perturbation_type"]
        evaluate = e * variants * victims
        rows.append({"dataset": item["key"], "clean_calls": clean,
                     "acquisition_calls": acquire, "perturbed_victim_calls": evaluate,
                     "max_calls": clean + acquire + evaluate,
                     "reserved_output_tokens": (clean + acquire + evaluate) * cap})
    clean = sum(r["clean_calls"] for r in rows)
    acquire = sum(r["acquisition_calls"] for r in rows)
    evaluate = sum(r["perturbed_victim_calls"] for r in rows)
    totals = {
        "maximum_clean_calls": clean,
        "maximum_perturbation_generation_calls": acquire,
        "maximum_perturbed_victim_calls": evaluate,
        "maximum_generation_calls": clean + acquire + evaluate,
        "maximum_reserved_output_tokens": (clean + acquire + evaluate) * cap,
    }
    for key, value in totals.items():
        if d[key] != value:
            raise ValueError(f"Mismatch for {key}: declared {d[key]}, computed {value}")
    for key in ("training_updates", "new_proposer_calls", "new_receiver_revision_calls",
                "counterfactual_suffix_calls", "teacher_forced_scoring_forwards"):
        if d[key] != 0:
            raise ValueError(f"Unexpected budget authorization: {key}")
    if d["victim_feedback_to_generator"] or d["natural_candidate_answers_may_change"]:
        raise ValueError("Design no longer matches fixed rationale-only pool")
    if d["control_types"] != ["ordinary_rephrase"] or len(d["attack_types"]) != 4:
        raise ValueError("Four attacks and one separate control are required")
    if d["defender_query_prefixes"] != [1, 2, 4]:
        raise ValueError("Unexpected query-prefix design")
    return {"status": "design_arithmetic_verified_not_experiment_results",
            "per_dataset": rows, "totals": totals,
            "included_two_task_full_clean_smoke_calls": 2 * judges * modes,
            "included_two_task_j8_clean_smoke_calls": 2 * modes}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--design", type=Path,
                        default=Path(__file__).with_name("adjudication_design.json"))
    args = parser.parse_args()
    try:
        out = verify(args.design)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(f"Design verification failed: {exc}") from exc
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
