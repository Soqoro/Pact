#!/usr/bin/env python3
"""Validate the proposed pack's arithmetic and safety defaults; not PACT runtime tests."""
from __future__ import annotations
import json
from pathlib import Path

def main() -> None:
    root = Path(__file__).resolve().parents[1]
    d = json.loads((root / 'configs' / 'pact_training_revival_design.json').read_text())
    sp = d['splits']
    assert sum(sp.values()) == 960
    assert all(v % 2 == 0 for v in sp.values())
    q = d['data']['source_quotas']
    assert d['data']['allocation_version'] == 'arc400_logiqa560_v2'
    assert d['data']['equal_source_allocation'] is False
    assert {f:sum(v.values()) for f,v in q.items()} == {'arc_challenge':400,'logiqa':560}
    assert {k:sum(v[k] for v in q.values()) for k in sp} == sp
    for f, blocks in d['stage_ii']['blocks_by_source'].items():
        assert q[f]['main_fit'] == blocks * 64
        assert q[f]['allocation_probe'] == blocks * 8
    n_fit, n_val, n_eval, n_probe = (sp[k] for k in ('main_fit', 'validation', 'source_evaluation', 'allocation_probe'))
    assert (n_fit, n_val, n_eval, n_probe) == (512, 128, 256, 64)
    i = {
        'fit_private': n_fit * 3,
        'attack_acquisition': n_fit + n_val + n_eval,
        'live_evaluation': 3 * (n_val + n_eval) * (3 + 2*3 + 2),
        'extra_fixed_context': 64*2*3*2 + 64*3*3*2,
        'scratch_generation': 2*3,
    }
    assert i == d['stage_i']['generation_components']
    assert sum(i.values()) == d['stage_i']['max_generation_calls'] == 17030
    assert 17030 * 512 == d['stage_i']['reserved_output_tokens'] == 8719360
    assert n_fit // 8 * 2 == 128
    assert 128 * 3 * 2 == d['stage_i']['main_optimizer_steps'] == 768
    assert 3 * 16 == d['stage_i']['scratch_optimizer_steps'] == 48
    assert 6 * 2 * n_fit * 3 == d['stage_i']['main_supervised_forwards'] == 18432
    assert 3 * 16 == d['stage_i']['scratch_supervised_forwards'] == 48
    ii = {
        'probe_attack_acquisition': n_probe,
        'baseline_two_seeds': 2*n_probe*11,
        'updated_branches_two_seeds': 2*n_probe*3*(1+2*4),
    }
    assert ii == d['stage_ii']['generation_components']
    assert sum(ii.values()) == d['stage_ii']['max_generation_calls'] == 4928
    assert 4928 * 512 == d['stage_ii']['reserved_output_tokens'] == 2523136
    assert 8*3*8 == d['stage_ii']['temporary_optimizer_steps'] == 192
    assert 8*3*64 == d['stage_ii']['temporary_supervised_forwards'] == 1536
    assert 64*2*4*2 + 64*3*2*2 == d['stage_ii']['diagnostic_score_forwards'] == 1792
    assert 17030 + 4928 == d['bounded_portfolio']['max_generation_calls'] == 21958
    assert (17030+4928)*512 == d['bounded_portfolio']['reserved_output_tokens'] == 11242496
    assert d['execution']['default'] == 'offline_plan'
    assert d['execution']['local_real_inference'] is False
    assert d['execution']['automatic_stage_ii'] is False
    assert d['execution']['automatic_stage_iii'] is False
    assert d['stage_iii']['real_execution_plan'] is None
    assert d['models']['readout']['trainable'] is False
    assert d['training']['dpo'] is False
    assert d['training']['same_prompt_pair_requirement'] is False
    assert d['training']['supervise_generated_rationales_as_gold'] is False
    print(json.dumps({'status':'PASS', 'checked':'design arithmetic and defaults only',
                      'stage_i': i, 'stage_ii': ii,
                      'portfolio_generation_cap':21958,
                      'repository_code_tests_executed':False,
                      'new_model_calls':0}, indent=2))

if __name__ == '__main__':
    main()
