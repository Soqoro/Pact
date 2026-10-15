#!/usr/bin/env python3
"""Verify this prompt pack's design arithmetic; this is not a PACT data audit."""
from __future__ import annotations
import json
import math
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    d = json.loads((root / 'configs' / 'gate_diagnostics_design.json').read_text())
    s = d['selector']
    require(s['views'] == s['clean_tasks'] + s['accepted_variants'] == 202,
            'The 202 fixed views do not reconcile.')
    calls = s['views'] * len(s['arms'])
    require(calls == s['call_ceiling'] == 404, 'Selector call ceiling mismatch.')
    tokens = calls * s['max_output_tokens']
    require(tokens == s['reserved_output_tokens'] == 206848, 'Output ceiling mismatch.')
    smoke = s['smoke']
    smoke_calls = (smoke['tasks_per_dataset'] * smoke['datasets'] *
                   smoke['max_views_per_task'] * len(s['arms']))
    require(smoke_calls == smoke['max_calls'] == 16, 'Smoke budget mismatch.')
    require(smoke_calls * s['max_output_tokens'] == smoke['reserved_output_tokens'] == 8192,
            'Smoke token ceiling mismatch.')
    require(smoke['included_in_main'], 'Smoke must be included, not additional.')
    require(d['offline']['model_calls'] == d['offline']['gate_fits'] == 0,
            'Offline work cannot run models or fit gates.')
    require(d['offline']['policy_selection_authorized'] is False,
            'Diagnostic sensitivity cannot select a replacement policy.')
    require(d['offline']['sensitivity_splits'] == ['fit', 'threshold_tuning'],
            'Sensitivity must exclude development data.')
    require(s['llm_updates'] == s['gate_fits'] == s['teacher_forced_forwards'] == 0,
            'Unexpected learning/scoring work in selector experiment.')
    # Algebraic fixture checks, not scores from the user's trained models.
    for logits in [(0., 0., 0.), (0., -1., 2.), (2., 1., -2.), (-1., 2., 0.)]:
        a = max(logits)
        terms = [math.exp(z-a) for z in logits]
        p = [t/sum(terms) for t in terms]  # harm, neutral, improve
        u2 = p[2] - 2*p[0]
        require((u2 > 0) == ((logits[2]-logits[0]) > math.log(2)),
                'Zero-threshold log-odds fixture failed.')
    for name in ['docs/PACT_Codex_Gate_Diagnostics_and_Selector_Repair.md',
                 'docs/PACT_Gate_Diagnostics_Next_Phase_Plan.md',
                 'prompts/PACT_Gate_Diagnostics_Codex_Start.md']:
        require((root/name).is_file(), f'Missing pack file: {name}')
    print('Design checks passed: 0 offline calls/fits; 404 prospective calls; '
          '206,848 reserved output tokens; <=16-call included smoke.')
    print('Four synthetic log-odds fixtures passed. No real artifacts, models, '
          'API endpoints or repository implementation were evaluated.')

if __name__ == '__main__':
    main()
