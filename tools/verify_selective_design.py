#!/usr/bin/env python3
"""Check this DESIGN pack's arithmetic and toy accounting; does not implement PACT."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def check() -> None:
    d = json.loads((ROOT / 'configs/selective_correction_design.json').read_text())
    c, x = d['core'], d['ceilings']
    f, k, e = c['fit'], c['threshold_tuning'], c['heldout_source_development']
    assert (f,k,e) == (128,32,64)
    assert all(n % 2 == 0 for n in (f,k,e))
    a, pair_calls = c['maximum_alternatives'], c['calls_per_pair_bank']
    train_styles, test_styles = len(c['fit_tuning_rewrites']),len(c['evaluation_rewrites'])
    assert set(c['fit_tuning_rewrites']).isdisjoint(c['evaluation_rewrites'])
    fit_tune = (f+k)*(4 + a*pair_calls + train_styles*(1+pair_calls))
    heldout = e*(4 + a*pair_calls + test_styles*(1+pair_calls)
                 + (1+test_styles) + c['independent_reconsideration_calls'])
    core = fit_tune + heldout
    n_t = sum(d['transfer']['datasets'].values())
    r_t = d['transfer']['accepted_parent_rewrites']
    transfer = n_t*a*pair_calls + r_t*pair_calls + n_t+r_t + n_t*6
    cap = d['inference']['max_new_tokens']
    for key,val in [('fit_tuning',fit_tune),('heldout_source_evaluation',heldout),
                    ('core',core),('transfer',transfer),('portfolio',core+transfer)]:
        assert x[key+'_calls'] == val, (key,val)
        assert x[key+'_output_tokens'] == val*cap, key
    assert x['source_only_two_fit_task_smoke_calls_included'] == 2*4
    assert d['inference']['llm_optimizer_updates'] == 0
    assert d['inference']['paid_api_calls'] == 0
    assert d['gate']['formal_risk_certificate'] is False
    # Exhaust all simple correctness/route states: final = baseline + rescue - harm.
    for base in (0,1):
        for alternative in (0,1):
            for switch in (0,1):
                final = alternative if switch else base
                rescue = int(switch and not base and alternative)
                harm = int(switch and base and not alternative)
                assert final == base + rescue - harm
                delta = alternative-base
                assert delta in (-1,0,1)
    # Numerical illustrations must not be confused with measured new outcomes.
    assert 58+15-28 == 45
    assert 58+15-6 == 67  # illustrative bookkeeping only, not a forecast
    print(json.dumps({'design_arithmetic_checked':True,
                      'core_calls':core,'transfer_calls':transfer,
                      'portfolio_calls':core+transfer,
                      'portfolio_reserved_output_tokens':(core+transfer)*cap,
                      'toy_transition_accounting_checked':True,
                      'repository_implementation_tested':False,
                      'gpu_or_model_execution':False},indent=2))

if __name__ == '__main__':
    check()
