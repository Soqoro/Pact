"""Offline evidence draft, NOT a reviewed exposure inventory or spending receipt."""
import argparse
from pathlib import Path

from pact.util import canonical, digest, file_hash, read_json, write_json
from pact.selective.data import REPO, LEDGER, prior_selections, validate_exposure
from pact.revival.allocation_v3 import evidence
from pact.revival.evaluation_source import review as parent_review
from pact.revival.gpqa_source import review, sources, graph

FIELDS = ('task_ids', 'group_ids', 'content_groups', 'cross_dataset_fingerprints')
ROW_FIELDS = ('task_id', 'group_id', 'content_group', 'cross_dataset_fingerprint')


def union_evidence(exposure, source, historical, selections):
    """Monotone private exclusion union; never infer semantic or global coverage."""
    pools = {key: set(exposure[key]) for key in FIELDS}
    baseline = {key: len(values) for key, values in pools.items()}
    additions = {}

    def record(name, operation):
        before = {key: len(values) for key, values in pools.items()}
        operation()
        additions[name] = {key: len(pools[key]) - before[key] for key in FIELDS}

    def inherited():
        for key in FIELDS:
            pools[key].update(source.get('exposure', {}).get(key, []))

    def rows(values):
        for row in values:
            for key, field in zip(FIELDS, ROW_FIELDS):
                value = row.get('task', {}).get('task_id') if field == 'task_id' and 'task' in row else row.get(field)
                if value is not None:
                    if not isinstance(value, str) or not value:
                        raise ValueError('invalid_exclusion_identity')
                    pools[key].add(value)

    def partitions():
        for history in historical:
            manifest = history['manifest']
            for key in ('selected_ids', 'protected_ids', 'excluded_ids'):
                pools['task_ids'].update(manifest[key])
            pools['task_ids'].update(manifest['group_by_id'])
            pools['group_ids'].update(manifest['group_by_id'].values())

    record('executed_source_inherited_exclusions', inherited)
    record('all_executed_source_allocations', lambda: rows(source['records']))
    record('repository_selections', lambda: rows(selections))
    record('both_historical_gpqa_partitions', partitions)
    result = {key: sorted(values) for key, values in pools.items()}
    return result, {'baseline_counts': baseline, 'incremental_additions': additions,
                    'union_counts': {key: len(values) for key, values in pools.items()}}


def verified_audit(root, config):
    if read_json(root / 'audit-input.json')['sha256'] != digest(config):
        raise ValueError('audit_config_changed')
    manifest = read_json(root / 'manifest.json')
    required = {'source.private.json', 'lineage.private.json', 'audit.private.json'}
    if not required <= set(manifest):
        raise ValueError('missing_audit_evidence')
    for name, sha in manifest.items():
        if Path(name).name != name or file_hash(root / name) != sha:
            raise ValueError('audit_evidence_changed')
    audit = read_json(root / 'audit.private.json')
    if audit['fixture']:
        raise ValueError('real_audit_required')
    return read_json(root / 'source.private.json'), read_json(root / 'lineage.private.json')


def build(config_path, destination):
    config = read_json(config_path)
    root = Path(config['run_dir'])
    saved_source, saved_lineage = verified_audit(root, config)
    # Re-verify authoritative parent bytes, completion, S0 registry and scoped history.
    source, lineage = parent_review.lineage(Path(config['parent_dir']),
        config.get('history_roots', []), config.get('parent_bundle'))
    if digest(source) != evidence.EXECUTED_SOURCE_HASH or source != saved_source or lineage['S0'] != saved_lineage['S0']:
        raise ValueError('executed_lineage_conflict')
    conflicts = set(lineage['local_history_conflicts'])
    for history_root in [config['parent_dir'], *config.get('history_roots', [])]:
        for path in Path(history_root).glob('**/attempts/*.json'):
            if read_json(path).get('identity', {}).get('owner') in (graph.ASSAY, graph.POLICY, graph.CHILD):
                conflicts.add(str(path))
    lineage['local_history_conflicts'] = sorted(conflicts)
    exposure = read_json(Path(config['exposure']))
    validate_exposure(exposure)
    inventory = read_json(Path(config['inventory']))
    historical, covered = review.history_files(inventory)
    if not covered:
        raise ValueError('historical_partition_coverage_unverified')
    exclusions, counts = union_evidence(exposure, source, historical,
                                        list(prior_selections(REPO / 'experiments')))
    inputs = {'config': file_hash(config_path), 'audit_manifest': file_hash(root / 'manifest.json'),
              'prior_exposure': file_hash(Path(config['exposure'])),
              'historical_inventory': file_hash(Path(config['inventory'])),
              'benchmark_ledger': file_hash(LEDGER),
              'experiment_ledger': file_hash(REPO / 'docs/experiment_ledger.md'),
              'parent_source': digest(source), 'parent_archive': evidence.PARENT_SHA}
    selection_files = {p.name: file_hash(p) for p in sorted((REPO / 'experiments').glob('*selection.json'))}
    unresolved = ['all_project_history_coverage_not_certified',
                  'semantic_overlap_review_unresolved',
                  'external_stage2_consumption_not_reconciled']
    # This intentionally is NOT shaped like an accepted exposure or history receipt.
    draft = {'version': 'stage2_exposure_reconciliation_draft_v1',
             'status': 'UNREVIEWED_EVIDENCE_DRAFT', 'reviewed_complete': False,
             'exclusion_union': exclusions, 'original_source_receipts': exposure['source_receipts'],
             'input_hashes': inputs, 'selection_files': selection_files,
             'historical_manifest_hashes': [entry['sha256'] for entry in inventory['files']],
             'scoped_history_roots': [config['parent_dir'], *config.get('history_roots', [])],
             'local_history_conflicts': lineage['local_history_conflicts'],
             'unresolved': unresolved,
             'review_questions': [
                 'Reconcile experiment-ledger entries and manual/preview exposures with the bound exclusion sources; record uncovered evidence explicitly.',
                 'Review material semantic overlap under the existing policy; lexical identities alone do not certify absence.',
                 'Identify any Stage II probes, temporary updates, scoring or attempts in known remote roots/user execution records; preserve unknown spending.'],
             'historical_consumption': 'unresolved', 'remaining_budget': None,
             'execution_authorized': False}
    summary = {'version': draft['version'], 'status': draft['status'], **counts,
               'input_hashes': inputs, 'private_draft_digest': digest(draft),
               'local_conflict_records': len(lineage['local_history_conflicts']),
               'original_receipt_count': len(exposure['source_receipts']),
               'historical_partitions_verified': True, 'unresolved': unresolved,
               'eligibility_certified': False, 'candidate_frozen': False,
               'execution_authorized': False, 'historical_consumption': 'unresolved',
               'remaining_budget': None, 'pretraining_exposure': 'unknown',
               'model_calls': 0, 'existing_evidence_modified': False}
    destination = sources.private_path(destination)
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    write_json(destination / 'reconciliation.private.json', draft)
    write_json(destination / 'summary.sanitized.json', summary)
    write_json(destination / 'checksums.json', {name: file_hash(destination / name) for name in
               ('reconciliation.private.json', 'summary.sanitized.json')})
    return summary


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        print(canonical(build(args.config, args.output)))
        return 0
    except Exception as exc:
        print(canonical({'status': 'reconciliation_stopped', 'exception_type': type(exc).__name__,
                         'model_calls': 0, 'action': 'preserve_inputs_and_output; no automatic retry'}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
