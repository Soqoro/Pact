#!/usr/bin/env python3
"""Check prompt-pack arithmetic and fictional metric identities, not PACT code.

This script uses no model, benchmark, network, external dependency, or private
trace. It does not verify that the repository implements the proposed study.
"""
from __future__ import annotations

import json
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_design(path: Path) -> dict[str, int]:
    config = json.loads(path.read_text(encoding="utf-8"))
    parent = config["parent"]
    review = config["review"]
    study = config["optional_intervention"]
    datasets = len(parent["dataset_tasks"])

    require(sum(parent["dataset_tasks"].values()) == 230, "Task count mismatch")
    require(sum(parent["mixed_tasks"].values()) == 80, "Mixed count mismatch")
    require(parent["clean_dispatched_calls"] + parent["clean_deterministic_no_call_failures"]
            == parent["clean_scored_outcomes"], "Clean accounting mismatch")
    require(parent["accepted_rewrites"] + parent["rejected_rewrites"] == parent["rewrite_attempts"],
            "Rewrite accounting mismatch")
    require(parent["accepted_rewrites"] * parent["victim_configurations"] == parent["victim_calls"],
            "Victim accounting mismatch")
    require(parent["rejected_rewrites"] * parent["victim_configurations"] == parent["unavailable_victim_slots"],
            "Missing-slot mismatch")
    require(parent["clean_dispatched_calls"] + parent["rewrite_attempts"] + parent["victim_calls"]
            == parent["total_dispatched_calls"], "Total dispatch mismatch")

    main_tasks = datasets * review["main_tasks_per_dataset"]
    main_pairs = main_tasks * review["scheduled_styles_per_task"]
    sentinel_pairs = datasets * review["enriched_categories_per_dataset"]
    require(main_tasks == review["main_total_tasks"], "Main task ceiling mismatch")
    require(main_pairs == review["main_pair_units_ceiling"], "Main pair ceiling mismatch")
    require(sentinel_pairs == review["enriched_primary_pairs_ceiling"], "Sentinel count mismatch")
    require(main_pairs + 2 * sentinel_pairs == review["total_pair_display_ceiling_before_deduplication"],
            "Display ceiling mismatch")

    units = datasets * len(study["source_styles"]) * study["slots_per_dataset_style"]
    per_unit = len(study["variants"]) * len(study["judge_keys"]) * len(study["modes"])
    calls = units * per_unit
    tokens = calls * study["max_output_tokens_per_call"]
    require(units == study["max_source_units"], "Source-unit ceiling mismatch")
    require(calls == study["max_new_generation_calls"], "Call ceiling mismatch")
    require(tokens == study["max_reserved_output_tokens"], "Token ceiling mismatch")
    require(study["smoke_units"] * per_unit == study["max_included_smoke_calls"], "Smoke mismatch")
    require(not study["execution_enabled"], "Optional execution must default off")
    require(all(v == 0 for v in config["other_budgets"].values()), "Unexpected extra budget")
    require(all(p["model_id"] is None and not p["execution_enabled"]
                for p in config["future_frontier_profiles"]), "Frontier profile activated")
    return {"main_review_tasks": main_tasks, "main_review_pairs_max": main_pairs,
            "span_units_max": units, "optional_calls_max": calls, "optional_tokens_max": tokens}


def verify_fictional_metrics() -> None:
    # (independent correctness T, candidate coverage O, selected correctness Y)
    rows = [(0, 1, 1), (0, 1, 0), (1, 1, 1), (1, 1, 0), (1, 0, 0), (0, 0, 0)]
    opportunities = sum(t == 0 and o == 1 for t, o, y in rows)
    rescues = sum(t == 0 and o == 1 and y == 1 for t, o, y in rows)
    regressions = sum(t == 1 and y == 0 for t, o, y in rows)
    covered_regressions = sum(t == 1 and o == 1 and y == 0 for t, o, y in rows)
    structural_conflicts = sum(t == 1 and o == 0 for t, o, y in rows)
    gain_count = sum(t == 0 and y == 1 for t, o, y in rows)
    require(opportunities == 2 and rescues == 1, "Rescue fixture failure")
    require(regressions == 2 and covered_regressions == 1 and structural_conflicts == 1,
            "Regression separation fixture failure")
    require(gain_count - regressions == sum(y - t for t, o, y in rows), "Net identity failure")
    require(all(y <= o for t, o, y in rows), "Constrained selection ceiling fixture failure")
    # Cue/sham difference equals the difference of their changes from reference.
    reference = [0, 1, 0, 1]
    cue = [1, 1, 0, 0]
    sham = [0, 0, 1, 1]
    require(sum(c - s for c, s in zip(cue, sham)) ==
            sum(c - r for c, r in zip(cue, reference)) -
            sum(s - r for s, r in zip(sham, reference)), "Span contrast identity failure")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    summary = verify_design(root / "config" / "semantic_forensics_design.json")
    verify_fictional_metrics()
    print(json.dumps({"status": "passed", "scope": "design_arithmetic_and_fictional_fixtures_only", **summary}, indent=2))


if __name__ == "__main__":
    main()
