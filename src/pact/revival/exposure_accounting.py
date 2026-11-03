"""Inactive, bounded CPU decision packets; no discovery or execution interface."""
import argparse
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json

from ..util import canonical, digest, file_hash, write_json
from .allocation_v3 import evidence as e, design as d
from .gpqa_source import graph, contracts

VERSION = 'stage2_exposure_accounting_proposal_v2'
MAX_BYTES = 64 * 1024**2
REPO = Path(__file__).resolve().parents[3]
FIELDS = ('task_ids', 'group_ids', 'content_groups', 'cross_dataset_fingerprints')
REPORTED = {
    'provenance': 'user_returned_aggregates_not_locally_reverified_remote_bytes',
    'source_jobs': [1112958, 1112981, 1113022],
    'gpqa': {'records': 448, 'diamond_protected_records': 198,
             'scope_only_unresolved_unique_groups': 249},
    'logiqa': {'items': 7376, 'denied_items': 1335, 'unknown_items': 6041,
               'unique_eligible_groups': None},
    'slurm': {'job': 1114278, 'files_seen': 147646, 'json_inspected': 30707,
              'matching_candidates': 0, 'unopened_archives': 14},
    'drive': {'json_inspected': 1, 'time_limit_reached': True},
    'original_retained': {'sha256': '8371bafc49022ae2d8e344696be465fcb8410a39712e348a0715530a0a455e4c',
        'stage_I_intents': 2438, 'stage_II_intents': 0, 'completed_calls_established_by_this_inspection': None},
    'replacement': {'recovery_safe': False, 'probe_artifact_entries': 0},
    'continuation': {'recovery_safe': True, 'probe_artifact_entries': 0},
    'user_execution_attestation': 'unsure',
}


def bounded_json(path, expected=None, digest_type='file_sha256'):
    path = Path(path)
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('symlink_evidence')
    with path.open('rb') as stream:
        raw = stream.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('evidence_size_bound')
    value = json.loads(raw)
    if digest_type not in ('file_sha256', 'canonical_json'):
        raise ValueError('unknown_digest_type')
    actual = hashlib.sha256(raw).hexdigest() if digest_type == 'file_sha256' else digest(value)
    if expected is not None and expected != actual:
        raise ValueError('evidence_digest_conflict')
    return value, {'digest_type': digest_type, 'digest': actual,
                   'provenance': 'locally_verified_bytes', 'bytes': len(raw), 'location': str(path)}


def physical_accounting(events):
    """Deduplicate exports by a physical execution identity, never logical request."""
    physical = {}
    unbound = 0
    for event in events:
        if event.get('kind') not in ('generation', 'optimizer_update', 'supervised_forward', 'scoring_forward'):
            raise ValueError('physical_kind')
        if event.get('status') not in ('intent_only', 'attempt_confirmed', 'completed', 'unresolved'):
            raise ValueError('physical_status')
        if not event.get('physical_id') or not event.get('execution_origin'):
            unbound += 1
            continue
        identity = (event['execution_origin'], event['physical_id'])
        projection = {k: event.get(k) for k in ('kind', 'logical_id', 'status', 'payload_digest')}
        if not projection['payload_digest']:
            raise ValueError('physical_evidence_binding_required')
        if identity in physical and physical[identity] != projection:
            raise ValueError('physical_identity_conflict')
        physical[identity] = projection
    counts = Counter((v['kind'], v['status']) for v in physical.values())
    return {'unique_bound_records': len(physical), 'unbound_records': unbound,
            'records_by_kind_and_status': {'/'.join(k): v for k, v in sorted(counts.items())},
            'logical_requests': len({v['logical_id'] for v in physical.values() if v['logical_id']}),
            'unknown_history': True, 'verified_remaining_balance': None,
            'late_discovery_refund': 0}


def reuse_projection(requests, reuse_receipts, past_events, newly_executed=()):
    """Hypothetical future dispatch arithmetic, not an active reuse approval.

    Caller supplies full validated contract digests, never just filenames/seeds.
    A newly executed logical request stays spent even if older reuse is found later.
    """
    required = {r['logical_id']: r for r in requests}
    if len(required) != len(requests):
        raise ValueError('duplicate_logical_request')
    completed_new = set(newly_executed)
    if not completed_new <= set(required):
        raise ValueError('unowned_new_execution')
    reusable = set()
    for receipt in reuse_receipts:
        target = required.get(receipt.get('logical_id'))
        if target is None:
            raise ValueError('unowned_reuse')
        fields = ('request_digest', 'contract_digest', 'lineage_digest')
        if (receipt.get('status') != 'complete' or receipt.get('reuse_decision') != 'accepted'
            or not receipt.get('decision_digest') or not receipt.get('result_digest')
            or any(not target.get(k) or receipt.get(k) != target[k] for k in fields)):
            raise ValueError('exact_reuse_unverified')
        reusable.add(receipt['logical_id'])
    return {'past_physical': physical_accounting(past_events),
            'future_logical_dispatches': len(set(required)-completed_new-reusable),
            'avoided_future_dispatches': len(reusable-completed_new),
            'already_executed_new_logical': len(completed_new),
            'refund': 0, 'execution_authorized': False}


def classify_groups(records):
    """Mutually exclusive group states; retain overlapping reasons privately."""
    groups = defaultdict(list)
    ungrouped = 0
    for row in records:
        if not row.get('group_id') or not row.get('family'):
            ungrouped += 1
            continue
        groups[row['family'], row['group_id']].append(row)
    result = []
    for (family, gid), rows in sorted(groups.items()):
        reasons = sorted({reason for row in rows for reason in row.get('reasons', [])})
        excluded = any(row.get('definite_exclusion') is True for row in rows)
        factual = all(row.get('factual_inclusion_verified') is True for row in rows)
        accepted = all(row.get('scope_acceptance_verified') is True for row in rows)
        state = 'excluded' if excluded else ('eligible_within_reviewed_scope' if factual and accepted else 'unresolved')
        result.append({'family': family, 'group_id': gid, 'state': state, 'reasons': reasons,
                       'factual_inclusion_verified': factual,
                       'acceptance_only_gap': factual and not accepted and not excluded})
    return result, {'records': len(records), 'grouped_unique_groups': len(groups),
                    'ungrouped_records': ungrouped,
                    'unique_group_statuses': dict(Counter(x['state'] for x in result))}


def scope_relation(allowed, prospective, *, source_verified, enforcement_bound=False):
    if not source_verified or prospective is None:
        return 'unresolved'
    if set(allowed) & set(prospective):
        return 'supported_overlap'
    return ('supported_nonintersection_within_bound_run_scope' if enforcement_bound
            else 'conditional_nonintersection_requires_review')


def future_work(source, candidate=None, lineage=None, reuses=()):
    arithmetic = graph.budget_reconciliation(source)
    compiled = graph.compile_graph(source, candidate, lineage) if candidate else None
    if reuses:
        # Reuse can be proposed, but no contract-complete authorized real result is
        # supplied in this decision task. Never subtract filenames or logical IDs.
        raise ValueError('validated_reuse_decision_not_available')
    return {'basis': 'compiled_proposed_graph' if compiled else 'conditional_schema_arithmetic',
            'graph_digest': digest(compiled) if compiled else None,
            'real_request_ids': None, 'dispatchable': False,
            'dependency_counts': compiled['counts'] if compiled else None,
            'arithmetic': arithmetic, 'proposed_future_physical_ceiling': d.BUDGET,
            'validated_exact_reuse_count': 0, 'runnable_balance': None,
            'late_bound_payloads_and_checkpoint_identities_required': True}


def gaps():
    return [
        {'field': 'experiment_ledger_sha256', 'validator': 'evaluation_source.sources.exposure_status',
         'gap_kind': 'missing_binding_and_coverage_review', 'affected_scope': 'all later project exposures',
         'support': 'historical 12-receipt inventory; current ledger; job1113032 draft',
         'owner': 'project reviewer', 'smallest_action': 'Map later ledger allocations/preview exclusions to the bound receipts; accept only the covered scope.'},
        {'field': 'parent_source_sha256', 'validator': 'evaluation_source.sources.exposure_status',
         'gap_kind': 'mechanical_binding', 'affected_scope': '960 executed allocations',
         'support': 'exact executed source canonical digest and conservative exclusion union',
         'owner': 'CPU worker', 'smallest_action': 'Record verified source digest in the derived proposal; do not change the old inventory.'},
        {'field': 'coverage', 'validator': 'evaluation_source.sources.exposure_status',
         'gap_kind': 'conditional_scope_requires_acceptance', 'affected_scope': 'prospective groups outside prior exclusions',
         'support': 'scoped inventories and original source allowlist; later enforcement not proven',
         'owner': 'project reviewer', 'smallest_action': 'Decide whether original-contract nonintersection covers the missing interval; retain any material exception.'},
        {'field': 'material_overlap_review', 'validator': 'evaluation_source.sources.exposure_status',
         'gap_kind': 'absent_scope_review_not_blanket_item_review', 'affected_scope': 'remaining prospective GPQA/LogiQA groups',
         'support': 'existing lexical exclusion machinery and historical receipt limitations',
         'owner': 'authorized private reviewer', 'smallest_action': 'Reuse an applicable accepted overlap receipt or resolve this precise scope decision; inspect concrete pairs only if identified.'},
        {'field': 'reviewed_history', 'validator': 'allocation_v3.evidence.reviewed_history',
         'gap_kind': 'active_zero_history_schema_cannot_accept_uncertainty', 'affected_scope': 'GPU spending/reuse/adaptation claims only',
         'support': 'completed bounded history assessment with missing later interval',
         'owner': 'user methodological decision', 'smallest_action': 'Review inactive scoped-uncertainty alternative and finite future allowance; do not attest non-execution.'},
    ]


def assess(source, lineage, audit, exposure, provenance, *, candidate=None, fixture=False):
    contract = e.source_contract(source)
    if contract['status'] != 'ready':
        raise ValueError('inherited_contract_conflict')
    counts = Counter((r['family'], r['split']) for r in source['records'])
    union = {(r['family'], r['content_group']) for r in source['records']}
    exclusions = {k:set(exposure.get(k, [])) for k in FIELDS}
    before_counts = {k:len(v) for k,v in exclusions.items()}
    for k in FIELDS:
        exclusions[k].update(source.get('exposure', {}).get(k, []))
    for row in source['records']:
        for key,value in zip(FIELDS,(row['task']['task_id'],row['group_id'],row['content_group'],row['cross_dataset_fingerprint'])):
            exclusions[key].add(value)
    exclusion_counts = {'baseline': before_counts, 'union': {k:len(v) for k,v in exclusions.items()},
        'additions': {k:len(v)-before_counts[k] for k,v in exclusions.items()},
        'four_fields_are_not_four_exposure_events': True}
    scientific = contracts.training_contract(source, lineage['S0'])
    bindings = {'parent_source_sha256': digest(source),
                'coverage': 'all_prior_used_and_protected_project_groups',
                'material_overlap_review': 'no_unresolved_cases',
                'experiment_ledger_sha256': file_hash(REPO/'docs/experiment_ledger.md')}
    table = gaps()
    for row in table:
        field = row['field']
        row['present_in_supplied_inventory'] = field in exposure
        if field in bindings:
            row['matches_current_binding'] = exposure.get(field) == bindings[field]
    # Do not infer GPQA eligibility from 249 or unique LogiQA groups from 6041.
    eligibility = audit.get('eligibility') or {}
    ga = eligibility.get('gpqa_main') or {}
    group_records = []
    for row in ga.get('records', []):
        reasons = row.get('reasons', [])
        group_records.append({'family': 'gpqa_main', 'group_id': row.get('group_id'),
            'reasons': reasons, 'definite_exclusion': bool(set(reasons) & {
                'diamond_protected', 'historical_partition', 'option_integrity', 'duplicate_alias', 'conflicting_answer_keys'}),
            'factual_inclusion_verified': False, 'scope_acceptance_verified': False})
    states, grouped = classify_groups(group_records)
    candidate_allowed = candidate is not None and not any(
        b != 'relevant_external_consumption_unresolved' for b in audit.get('blockers', []))
    if candidate is not None and not candidate_allowed:
        raise ValueError('candidate_with_unresolved_source_facts')
    # Candidate comes only from an existing manifest-bound audit/inherited selector;
    # this report never overwrites or reselects it to bypass the live acceptance gate.
    work = future_work(source, candidate if candidate_allowed else None, lineage)
    queue = [{'kind': 'scope_decision', 'field': x['field'], 'evidence': x['support'],
              'reason': x['gap_kind'], 'action': x['smallest_action'], 'accepted': None}
             for x in table if x['field'] in ('coverage', 'material_overlap_review')
             and not x.get('matches_current_binding', False)]
    history = {'status': 'scoped_assessment_complete_with_residual_uncertainty',
        'accepted_reviewed_history': False, 'reported_evidence': REPORTED,
        'unknown_interval': 'after retained original step28 boundary through later missing/incomplete snapshots',
        'observed_stage_II_in_inspected_scope': 'none_found_not_zero_certified',
        'confirmed_physical_stage_II_work': None, 'researcher_use_of_probe_outcomes': 'unknown',
        'finite_cumulative_past_bound': None,
        'possible_probe_use': 'training_use_adaptation_and_spending; not automatically evaluation contamination',
        'replacement_unsafe_preserved': True, 'original_terminal_closure': False,
        'allowlist_exhausted_for_this_packet': True}
    proposal = {'version': VERSION, 'status': 'INACTIVE_PROPOSAL', 'accepted': None,
        'signature': None, 'effective_boundary': None, 'execution_authorized': False,
        'current_authorized_real_work': {'generation': 0, 'updates': 0, 'forwards': 0},
        'known_evidence': {'reported_original_stage_I_intents': 2438,
            'stage_I_completions_not_inferred_from_intents': True,
            'known_stage_II_physical_total': None},
        'unknown_interval': history['unknown_interval'], 'verified_remaining_budget': None,
        'finite_cumulative_past_plus_future_bound': None,
        'future_request': work,
        'why_separate_decision': 'Existing remaining ownership cannot be reconstructed; full graph is requested conditionally as future work, not granted or inferred unspent.',
        'scope_limit': 'same S0, fitting/probe groups, five policies, seeds and evaluation contract; no new cohort selection rule',
        'reuse_repeat_rules': [
            'Exports of one physical record count once; independent executions count separately even with identical logical IDs.',
            'Only full contract/payload/lineage validation plus a separate reuse decision can avoid a future dispatch.',
            'Unknown dispatch or optimizer attempt is not retryable; possible repeat requires explicit disposition and a newly reserved physical attempt.',
            'Late duplicate discovery never refunds executed work, rewrites history or selects a favorable result.',
            'No old unsafe optimizer/checkpoint state becomes resumable.'],
        'proposed_acceptance_text': 'Accept only the stated scoped history assessment with residual uncertainty, not zero spending. Consider a separate finite future allowance conditional on fresh evaluation eligibility, probe adaptation/repeat disposition, checkpoint/runtime checks and runner integration.',
        'separate_decisions': ['exposure scope and material overlap', 'training-probe adaptation/reuse claims',
            'finite future accounting allowance with approval boundary', 'candidate review/freeze', 'runtime and actual execution'],
        'scientific_limitations': ['possible prior development adaptation not independent first exposure',
            'unknown cumulative cost prevents total-efficiency claim', 'accounting cannot certify prospective freshness'],
        'active_schema_unchanged': 'allocation_v3.evidence.reviewed_history still requires certified zero Stage II history'}
    readiness = {
        'source_integrity': 'fixture_only' if fixture else {
            'supplied_audit_statuses': {f: v.get('status') for f,v in audit.get('sources', {}).items()},
            'raw_bytes_reverified_by_this_packet': False,
            'newer_remote_verification': 'user_reported_job1112958'},
        'exposure_facts': 'unresolved', 'review_acceptance': 'unset',
        'candidate': 'proposed_fixture' if fixture and candidate else 'proposed' if candidate else 'absent',
        'candidate_frozen': False, 'accounting_ownership': 'unresolved',
        'checkpoint_runtime': 'historical_S0_binding_only; current_preflight_deferred',
        'runner_integration': 'GPQA_child_GPU_path_unconnected', 'gpu_permission': False}
    private = {'version': VERSION, 'fixture': fixture, 'evidence_provenance': provenance,
        'training_dependency_hash': digest(scientific), 'binding_gap_table': table,
        'derived_binding_proposal': {'mechanically_supported_values': {k:bindings[k] for k in ('parent_source_sha256', 'experiment_ledger_sha256')},
            'policy_required_values_not_certified': {k:bindings[k] for k in ('coverage','material_overlap_review')}, 'accepted': None},
        'allocation_unique_content_groups': len(union),
        'derived_exclusion_union': {k:sorted(v) for k,v in exclusions.items()},
        'exclusion_union_counts': exclusion_counts,
        'allocation_split_counts': {'/'.join(k): v for k, v in sorted(counts.items())},
        'allocation_semantics': 'conservative exclusion; not proof every allocation entered gradients',
        'missing_interval_relation': {
            'existing_960': 'supported_overlap_with_allowed_group_set; observed_later_use_unknown',
            'allocation_probes_64': 'training_use_possible; observed_use_not_established',
            'gpqa_main_outside_protections': 'conditional_nonintersection_if_original_source_contract_remained_in_force',
            'logiqa_outside_full_exclusion_union': 'conditional_nonintersection_if_original_source_contract_remained_in_force',
            'enforcement_for_missing_interval_verified': False},
        'group_statuses': states, 'group_status_counts': grouped,
        'logiqa_group_counts': None, 'raw_source_eligibility_recomputed': False,
        'review_queue': queue, 'review_queue_total': len(queue), 'pair_queue_total': 0,
        'pair_queue_note': 'No concrete semantic pair evidence supplied; no claim that no material pairs exist.',
        'history': history, 'accounting_proposal': proposal, 'readiness': readiness,
        'finite_evidence_allowlist': [{'role':role, 'location':ref.get('location'),
            'identity':ref.get('digest'), 'digest_type':ref.get('digest_type'),
            'inspection_status':ref.get('provenance'), 'reader_limit_bytes':MAX_BYTES,
            'question': ('Which groups and splits were allocated?' if role=='source.private.json'
                         else 'Does this exact bound record support the exposure, source or S0 claim?')}
            for role,ref in provenance.items()],
        'remote_only_already_reported_allowlist': [
            {'location':'original retained step28 object', 'identity':REPORTED['original_retained']['sha256'],
             'question':'Were Stage II intents/probe artifacts recorded at the retained boundary?',
             'inspection_status':'user_reported_verified; no repeated inspection requested'},
            {'location':'Slurm inventory job1114278', 'identity':'b5bd4163d7f9401b6b592e5e4666ba28a4b03da6cdb80e7dd538c07ea29a08b7',
             'question':'Were Stage II artifacts found within the four recorded roots?',
             'inspection_status':'user_reported; completed scope reused'}]}
    public = {key: private[key] for key in ('version', 'fixture', 'training_dependency_hash',
        'allocation_unique_content_groups', 'allocation_split_counts', 'allocation_semantics', 'exclusion_union_counts',
        'missing_interval_relation', 'group_status_counts', 'logiqa_group_counts',
        'raw_source_eligibility_recomputed', 'review_queue_total', 'pair_queue_total', 'pair_queue_note', 'readiness')}
    public.update(history_status=history['status'], reported_source_counts=REPORTED,
        proposal_status='INACTIVE_PROPOSAL', candidate_exists=candidate is not None,
        candidate_frozen=False, remaining_budget=None, new_real_work=0,
        conditional_future=work, execution_authorized=False,
        evidence_provenance={k: {f:v[f] for f in ('digest_type','digest','provenance','bytes') if f in v}
                             for k,v in provenance.items()})
    return private, public


def read_inputs(config):
    root = Path(config['audit_root'])
    manifest, mref = bounded_json(root/'manifest.json')
    values, refs = {}, {'audit_manifest': mref}
    for name in ('source.private.json', 'lineage.private.json', 'audit.private.json'):
        values[name], refs[name] = bounded_json(root/name, manifest[name])
    if values['audit.private.json'].get('fixture') is not False:
        raise ValueError('real_audit_required')
    source = values['source.private.json']
    if digest(source) != e.EXECUTED_SOURCE_HASH:
        raise ValueError('exact_executed_source_required')
    # These fixed known records verify S0 and executed provenance without scanning.
    parent = Path(config['parent_dir'])
    authoritative = {}
    for name, sha in e.AUTHORITATIVE_FILES.items():
        authoritative[name], refs['parent/'+name] = bounded_json(parent/name, sha)
    if authoritative['plan.json']['source'] != source:
        raise ValueError('parent_source_conflict')
    lineage = values['lineage.private.json']
    expected = {f:authoritative['checkpoint_inventory.private.json']['uniform_joint_sft/'+f] for f in d.FAMILIES}
    if lineage['S0'] != expected:
        raise ValueError('S0_binding_conflict')
    exposure, refs['exposure'] = bounded_json(Path(config['exposure']))
    # Optional exact draft binds newly returned evidence, not an approval.
    if config.get('exposure_draft'):
        draft, refs['exposure_draft'] = bounded_json(config['exposure_draft'],
            'fb31284ac87bc76cc55153b98fb78715413bb54865f9a601b07c9dae3c04722f', 'canonical_json')
        if draft['input_hashes']['prior_exposure'] != refs['exposure']['digest'] or draft['input_hashes']['parent_source'] != digest(source):
            raise ValueError('draft_input_binding_changed')
        for key in FIELDS:
            if not set(exposure[key]) <= set(draft['exclusion_union'][key]):
                raise ValueError('draft_dropped_exclusion')
    candidate = None
    if 'candidate.private.json' in manifest:
        candidate, refs['candidate'] = bounded_json(root/'candidate.private.json', manifest['candidate.private.json'])
    refs['decision_implementation'] = {'digest_type':'file_sha256', 'digest':file_hash(Path(__file__)),
        'provenance':'current_inactive_report_code'}
    refs['current_input_scope_code'] = {'digest_type':'file_sha256', 'digest':file_hash(REPO/'src/pact/revival/probe.py'),
        'provenance':'current_code_not_proof_of_missing_interval_enforcement'}
    refs['active_exposure_policy'] = {'digest_type':'file_sha256', 'digest':file_hash(REPO/'src/pact/revival/evaluation_source/sources.py'),
        'provenance':'current_policy_read_only'}
    refs['active_history_policy'] = {'digest_type':'file_sha256', 'digest':file_hash(Path(e.__file__)),
        'provenance':'current_policy_read_only'}
    return source, lineage, values['audit.private.json'], exposure, refs, candidate


def save(destination, private, public):
    destination = Path(destination)
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise ValueError('symlink_output')
    values = {'exposure-history.private.json': private,
              'accounting-proposal.sanitized.json': private['accounting_proposal'],
              'summary.sanitized.json': public}
    # Bind exact deterministic contents; a rerun never rescans or overwrites history.
    checks = {name: hashlib.sha256((canonical(value)+'\n').encode()).hexdigest() for name,value in values.items()}
    if destination.exists():
        saved, _ = bounded_json(destination/'checksums.json')
        if saved != checks:
            raise ValueError('evidence_changed_use_versioned_destination')
        for name, sha in checks.items():
            bounded_json(destination/name, sha)
        return {'status': 'identical_packet_reused', 'files': checks, 'model_calls': 0}
    destination.mkdir(parents=True, mode=0o700)
    for name, value in values.items():
        write_json(destination/name, value)
    write_json(destination/'checksums.json', checks)
    receipt = {'version': VERSION, 'status': 'inactive_packet_written', 'files': checks,
               'private_return_allowed': False, 'model_calls': 0, 'active_receipts_written': False}
    write_json(destination/'cpu-receipt.json', receipt)
    return receipt


def build(config):
    source, lineage, audit, exposure, refs, candidate = read_inputs(config)
    private, public = assess(source, lineage, audit, exposure, refs, candidate=candidate)
    # No raw content exported into Git. Existing ignored results_import is permitted
    # for local metadata-only packets; real cluster packets stay outside repository.
    original_output = Path(config['output'])
    if any(p.is_symlink() for p in (original_output, *original_output.parents)):
        raise ValueError('symlink_output')
    output = original_output.resolve()
    if output.is_relative_to(REPO) and not output.is_relative_to(REPO/'results_import'):
        raise ValueError('private_output_in_repository')
    return save(output, private, public), public


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--exposure-draft', type=Path)
    args = parser.parse_args(argv)
    try:
        config, _ = bounded_json(args.config)
        if 'audit_root' not in config and 'run_dir' in config:
            config['audit_root'] = config['run_dir']
        if args.output:config['output'] = str(args.output)
        if args.exposure_draft:config['exposure_draft'] = str(args.exposure_draft)
        receipt, summary = build(config)
        print(canonical({'receipt': receipt, 'summary': summary}))
        return 0
    except Exception as exc:
        print(canonical({'status': 'decision_packet_stopped', 'exception_type': type(exc).__name__, 'model_calls': 0}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
