"""Compile an inactive development-standard amendment. No execution interface."""
import argparse
import copy
from pathlib import Path

from ..util import canonical, digest, file_hash, write_json
from . import exposure_accounting as prior
from .gpqa_source import contracts, graph
from .allocation_v3 import design

VERSION = 'stage2_documented_exclusions_proposal_v1'
PROPOSAL = 'pact-stage2-documented-exclusions-amendment-001'
SUMMARY_SHA = 'f71f912bc116f1936f8861d7a7661caa56d03a715a3bdbcf906c39d73942657e'
TRAINING_HASH = 'd01160bb00a9da7292a305331275139d026d4c21dc5cc274609ab272afbfaf49'

# These are proposed screening requirements, not manufactured review flags.
FACTS = (
    'official_bytes_verified', 'source_mapping_verified', 'applicable_source_use_evidence',
    'historical_partitions_verified', 'documented_exclusion_union_bound',
    'lexical_component_checks_complete', 'preview_exclusions_accounted',
    'candidate_specific_exposure_resolved', 'known_material_cases_resolved',
)
EXCLUSIONS = frozenset((
    'diamond_protected', 'historical_partition', 'historical_or_protected_overlap',
    'option_integrity', 'schema_integrity', 'duplicate_alias',
    'duplicate_training_group', 'conflicting_answer_keys', 'validation_overlap',
    'cross_source_overlap', 'recorded_preview',
))
DISCLOSED_LIMITATIONS = frozenset((
    'exposure_scope_unverified', 'semantic_review_not_performed',
    'pretraining_exposure_unknown', 'historical_spending_unknown',
))


def proposed_screen(facts, reasons):
    """Decision table only; never selects data or returns legacy eligibility.

    Unknown reason codes fail closed. Only the enumerated scope/absence-of-review
    limitations are relaxed. Concrete ambiguity cannot be waived by that rule.
    """
    if not isinstance(facts, dict) or not isinstance(reasons, list) or any(
            not isinstance(r, str) for r in reasons):
        raise ValueError('screen_schema')
    why = set(reasons)
    missing = [k for k in FACTS if facts.get(k) is not True]
    if why & EXCLUSIONS:
        state = 'excluded'
    elif missing or why - DISCLOSED_LIMITATIONS:
        state = 'unresolved'
    else:
        state = 'proposed_documented_exclusion_screen_pass'
    return {'state': state, 'missing_facts': missing,
            'freshness_certified': False, 'semantic_decontamination': False,
            'execution_authorized': False}


def compile_proposal(source, lineage, summary, bindings, *, fixture=False):
    training = contracts.training_contract(source, lineage['S0'])
    if not fixture and (digest(training) != TRAINING_HASH or
                        summary.get('training_dependency_hash') != TRAINING_HASH):
        raise ValueError('unchanged_training_identity_required')
    if summary.get('version') != prior.VERSION or summary.get('fixture') is not fixture:
        raise ValueError('decision_packet_version_or_fixture_conflict')
    if summary.get('candidate_exists') is not False or summary.get('candidate_frozen') is not False:
        raise ValueError('different_candidate_requires_new_review')
    if summary.get('execution_authorized') is not False or summary.get('new_real_work') != 0:
        raise ValueError('inactive_evidence_required')
    arithmetic = graph.budget_reconciliation(source)
    if arithmetic != summary['conditional_future']['arithmetic']:
        raise ValueError('budget_reconciliation_conflict')
    required = {'generation': 23728, 'reserved_tokens': 12148736,
                'updates': 3072, 'training_forwards': 24576, 'scores': 2640}
    if any(design.BUDGET[k] != v for k, v in required.items()):
        raise ValueError('inherited_ceiling_changed')
    # Explicit public schema: never forward raw source records or arbitrary input fields.
    return {
        'version': VERSION, 'proposal_id': PROPOSAL, 'status': 'INACTIVE_PROPOSAL',
        'fixture': fixture, 'input_bindings': dict(bindings),
        'training_dependency_hash': digest(training),
        'inherited_contract': graph.contract(),
        'changes': {
            'evaluation_claim': 'documented-exclusion-screened development; residual contamination unknown',
            'semantic_review': 'absence_of_blanket_review_disclosed_not_certified',
            'missing_interval': 'conditional_original_frozen_source_scope; later_enforcement_unknown',
            'accounting': 'new_finite_future_physical_allowance_requested; not_old_remaining_balance',
            'probe_interpretation': 'training_use; possible_prior_adaptation_disclosed',
        },
        'screening': {'required_facts': list(FACTS), 'hard_exclusions': sorted(EXCLUSIONS),
                      'disclosed_limitations': sorted(DISCLOSED_LIMITATIONS),
                      'unknown_reason_action': 'unresolved',
                      'known_material_cases_action': 'unresolved_until_resolved; no_silent_waiver'},
        'unchanged': {
            'fitting_blocks': {'arc_challenge': 3, 'logiqa': 5},
            'probes': {'arc_challenge': 24, 'logiqa': 40},
            'evaluation_groups': {'gpqa_main': 64, 'logiqa': 64},
            'policies': list(design.POLICIES), 'continuation_seeds': list(design.SEEDS),
            'selection_seed': graph.SEED, 'selection_namespace': graph.NAMESPACE,
            'training': copy.deepcopy(design.TRAIN), 'analysis': copy.deepcopy(design.ANALYSIS),
            'allocation_source_weights': copy.deepcopy(design.SOURCE_WEIGHTS),
            'evaluation_source_weights': {'gpqa_main': .5, 'logiqa': .5},
        },
        'future_work': {'basis': 'conditional_schema_arithmetic', 'arithmetic': arithmetic,
                        'ceiling': copy.deepcopy(design.BUDGET),
                        'model_preflight_extra_forwards': 0,
                        'real_request_ids': None, 'graph_hash': None},
        'historical_spending': None, 'old_remaining_balance': None,
        'cumulative_past_plus_future_bound': None,
        'physical_rules': {
            'separate_executions_count_separately': True,
            'repeated_exports_not_new_executions': True,
            'late_duplicate_refund': False, 'unknown_attempt_automatic_retry': False,
            'accepted_historical_reuses': 0,
            'fresh_assay_may_repeat_unobserved_historical_work': True,
            'unsafe_optimizer_resume': False,
        },
        'approval': {'accepted': None, 'signature': None, 'effective_boundary': None},
        'candidate_exists': False, 'candidate_frozen': False,
        'current_authorized_work': {'generation': 0, 'training_forwards': 0, 'updates': 0, 'scores': 0},
        'execution_enabled': False, 'wallet_created': False,
        'runner_integration': {
            'implemented': False,
            'required': ['versioned_source_policy_without_forged_legacy_flags',
                         'real_candidate_and_graph_freeze',
                         'new_approval_boundary_bound_to_existing_physical_wallet',
                         'GPQA_policy_smoke_source_parameterization',
                         'exact_checkpoint_runtime_and_safe_resume',
                         'matched_source_reporting_and_private_exports'],
        },
    }


def build(config):
    summary, sref = prior.bounded_json(config['summary'], SUMMARY_SHA)
    receipt, rref = prior.bounded_json(config['receipt'])
    if (receipt.get('version') != prior.VERSION or
        receipt.get('status') != 'inactive_packet_written' or
        receipt.get('active_receipts_written') is not False or receipt.get('model_calls') != 0 or
        receipt.get('files', {}).get('summary.sanitized.json') != sref['digest']):
        raise ValueError('decision_receipt_conflict')
    cfg, _ = prior.bounded_json(config['lineage_config'])
    source, lineage, _, _, refs, _ = prior.read_inputs(cfg)
    bindings = {'decision_summary_sha256': sref['digest'],
                'decision_receipt_sha256': rref['digest'],
                'executed_source_canonical': digest(source),
                'lineage_sha256': refs['lineage.private.json']['digest'],
                'implementation_sha256': file_hash(Path(__file__))}
    proposal = compile_proposal(source, lineage, summary, bindings)
    destination = Path(config['output'])
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise ValueError('symlink_output')
    expected = (canonical(proposal)+'\n').encode()
    if destination.exists():
        if (destination/'proposal.sanitized.json').read_bytes() != expected:
            raise ValueError('proposal_changed_use_new_destination')
    else:
        destination.mkdir(parents=True, mode=0o700)
        write_json(destination/'proposal.sanitized.json', proposal)
    return {'status': 'INACTIVE_PROPOSAL', 'proposal_hash': digest(proposal),
            'proposal_sha256': file_hash(destination/'proposal.sanitized.json'),
            'candidate_exists': False, 'execution_enabled': False, 'model_calls': 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config, _ = prior.bounded_json(args.config)
        print(canonical(build(config)))
        return 0
    except Exception as exc:
        print(canonical({'status': 'proposal_stopped', 'exception_type': type(exc).__name__,
                         'model_calls': 0}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
