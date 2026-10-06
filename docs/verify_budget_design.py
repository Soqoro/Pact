"""Validate the PROMPT PACK's budget design; no PACT/model/dataset code is run."""
from __future__ import annotations
import json
from pathlib import Path


def main() -> None:
    path = Path(__file__).with_name('benchmark_breadth_design.json')
    spec = json.loads(path.read_text(encoding='utf-8'))
    totals = {'phase_a_calls': 0, 'phase_a_output_tokens': 0,
              'phase_b_calls': 0, 'phase_b_output_tokens': 0}
    for dataset in spec['datasets']:
        n = dataset['characterization_tasks']
        p = dataset['private_revision_output_cap']
        f = dataset['readout_output_cap']
        assert all(isinstance(v, int) and v > 0 for v in (n, p, f))
        core = dataset['phase_b_in_initial_plan']
        expected = {
            'phase_a_calls': 9*n,
            'phase_a_output_tokens': 9*n*p,
            'phase_b_calls': 21*n if core else 0,
            'phase_b_output_tokens': n*(12*p+9*f) if core else 0,
        }
        assert expected == dataset['ceilings'], (dataset['key'], expected)
        for key, value in expected.items():
            totals[key] += value
    assert totals == spec['stage_totals'], (totals, spec['stage_totals'])
    assert totals['phase_a_calls'] == 5058
    assert totals['phase_b_calls'] == 9030
    assert totals['phase_a_output_tokens'] == 3898368
    assert totals['phase_b_output_tokens'] == 5846400
    assert totals['phase_a_calls'] + totals['phase_b_calls'] == spec['portfolio_generation_calls'] == 14088
    assert totals['phase_a_output_tokens'] + totals['phase_b_output_tokens'] == spec['portfolio_output_token_reservation'] == 9744768
    assert sum(d['characterization_tasks'] for d in spec['datasets']) == 562
    assert sum(d['characterization_tasks'] for d in spec['datasets'] if d['phase_b_in_initial_plan']) == 430
    assert spec['new_optimizer_updates'] == 0
    assert spec['phase_a_smoke_tasks'] * 9 == spec['phase_a_smoke_max_calls'] == 18
    print('PASS: six dataset budgets, phase totals, 18-call included smoke, and zero training.')
    print('This verifies design arithmetic only, not loaders, scoring, isolation, GPU fit, or experiments.')


if __name__ == '__main__':
    main()
