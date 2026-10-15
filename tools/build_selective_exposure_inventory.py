"""Build a private exclusion inventory from the already audited metadata only.

No dataset download, question parsing, label access or generation. Plan files are
read as opaque bytes solely to check historical hashes and embedded metadata.
"""
import argparse
import hashlib
from pathlib import Path

from pact.benchmarks.data import exposure_index
from pact.selective.data import LEDGER, REPO, prior_selections, validate_exposure
from pact.util import canonical, digest, file_hash, read_json, write_json

BREADTH = (
    ('mmlu-pro', 'pact-mmlu-phase-b-audit-1791270113690429538', '516dcaba5ba4200e2e194c55b7470a774c116c733b06a912fb514937b0b088a9'),
    ('musr', 'pact-musr-complete-audit-1791278710347362192', 'a706c424665a7feec213c5864a2bd591c5781c5136bbeba16b365f96e75166ae'),
    ('math-500', 'pact-math-ab-audit-1791412685067931571', 'e27e7c6db74ac478ddfb90c6255ac8254be2c1d9da7fcf09070914c563ecc5c6'),
    ('mbpp-plus', 'pact-mbpp-smoke-audit-1791443310313931697', '72a10bbf296c6210cc5645ceeacc520dd15f6dfe8409e2d8217f8a890a3c0ae9'),
    ('gpqa', 'pact-gpqa-complete-1791449632230724762', '28798ee286711224cc311de51212dd3efce7074a944cb32c6bef7a3f291fdadf'),
)
TRAINING = {
    'proposal-1200': '92771b288958e6a1c23b731936dedb4db6285803465fb468bb05e5e2f497c62a',
    'engineering-12': '2cdbd6a37e89c5ceacaab08d2a43e53561a727c52458dc715b29dca0cf91eb0e',
}
PILOT = '8a8a9515244b2ded3e2eba801b99adaa107547ee02470991946d5ff7b8216495'
REVIEWED_LEDGER = '6daac2d8daf1ee830db044c0117363aa319d43ab221def2a75b612032d780dd1'


def verified_manifest(root, expected):
    raw = (root / 'plan.json').read_bytes().removesuffix(b'\n')
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('Historical plan bytes differ from audited identity')
    path = root / 'dataset_group_exposure_manifest.json'
    manifest = read_json(path)
    if b'"manifest":' + canonical(manifest).encode() not in raw:
        raise ValueError('Manifest is not bound to the audited plan')
    validate_manifest(manifest)
    return manifest


def validate_manifest(m):
    ids = set(m['group_by_id'])
    if m['training_allowed'] is not False or len(ids) != m['source_rows']:
        raise ValueError('Unexpected source inventory')
    if ids != set(m['cross_dataset_fingerprints']) or ids != set(m['variant_partition_by_id']):
        raise ValueError('Incomplete source hash/partition inventory')
    members = [tid for group in m['group_members'].values() for tid in group]
    if len(members) != len(ids) or set(members) != ids:
        raise ValueError('Group siblings missing or duplicated')
    for group, members in m['group_members'].items():
        if any(m['group_by_id'][tid] != group for tid in members):
            raise ValueError('Group membership mismatch')
    if set(m['partitions']) != {'characterization_dev', 'confirmation_locked', 'reserve_locked'}:
        raise ValueError('Unknown partition contract')
    selected = [tid for part in m['partitions'].values() for tid in part]
    if len(selected) != len(set(selected)) or not set(selected) <= ids:
        raise ValueError('Overlapping or unknown partition IDs')


def build(audit_root, imports):
    if file_hash(LEDGER) != REVIEWED_LEDGER:
        raise ValueError('Exposure ledger advanced: review new cohorts before certifying another inventory')
    ids, groups, contents, fingerprints = set(), set(), set(), set()
    receipts, counts, previous = [], {}, []

    def receipt(path, **extra):
        receipts.append({'name': str(path), 'sha256': file_hash(path), **extra})

    def selected(rows):
        for r in rows:
            ids.add(r['task_id'])
            if r.get('group_id'): groups.add(r['group_id'])
            if r.get('content_group'): contents.add(r['content_group'])

    for dataset, directory, expected in BREADTH:
        root = audit_root / directory
        m = verified_manifest(root, expected)
        if m['dataset'] != dataset: raise ValueError('Dataset identity changed')
        if previous and m['prior_exposure'] != exposure_index(previous):
            raise ValueError('Prior exposure chain differs from audited predecessors')
        ids.update(m['group_by_id']); groups.update(m['group_by_id'].values())
        fingerprints.update(m['cross_dataset_fingerprints'].values())
        if dataset == 'gpqa':
            parent = m['parent_partition']
            parts = [parent[k] for k in ('selected_ids', 'protected_ids', 'excluded_ids')]
            union = {tid for part in parts for tid in part}
            if list(map(len, parts)) != [32, 164, 2] or len(union) != 198 or union != set(parent['group_by_id']):
                raise ValueError('Original parent partition changed')
            if set(m['group_by_id']) != set(parent['protected_ids']):
                raise ValueError('Child pool differs from original protected inventory')
            ids.update(union); groups.update(parent['group_by_id'].values())
        receipt(root / 'dataset_group_exposure_manifest.json', audited_plan_hash=expected)
        counts[dataset] = {'source_rows': m['source_rows'], 'partitions': {k: len(v) for k, v in m['partitions'].items()}}
        previous.append({'dataset': dataset, 'manifest': m})

    for name, expected in TRAINING.items():
        path = imports / 'training-data-001' / name / 'manifest.json'
        m = read_json(path)
        if digest(m) != expected: raise ValueError('Historical training manifest changed')
        selected(m['selected']); receipt(path, audited_manifest_hash=expected)
        counts[name] = len(m['selected'])

    path = imports / 'heterogeneity-return-1791189410949196090' / 'source_exposure_manifest.json'
    exposed = read_json(path)
    if exposed['training_allowed'] is not False or digest(exposed['manifest']) != PILOT:
        raise ValueError('Historical validation pilot identity changed')
    selected(exposed['manifest']['selected']); receipt(path, audited_manifest_hash=PILOT)
    counts['validation_pilot'] = len(exposed['manifest']['selected'])

    selections = list(prior_selections(REPO / 'experiments'))
    selected(selections)
    for path in sorted((REPO / 'experiments').glob('*selection.json')): receipt(path)
    counts['explicit_selection_rows'] = len(selections)

    out = {'schema_version': 1, 'reviewed_complete': True, 'ledger_sha256': file_hash(LEDGER),
           'task_ids': sorted(ids), 'group_ids': sorted(groups), 'content_groups': sorted(contents),
           'cross_dataset_fingerprints': sorted(fingerprints), 'source_receipts': receipts,
           'review': {'scope': 'Recorded prior and locked metadata in the audited project inventories; no claim about unknown external exposure.',
                     'checks': ['historical plan hashes', 'manifest binding', 'all source siblings and partitions',
                                'four-link breadth exposure chain', 'original GPQA 32/164/2 metadata',
                                'historical training/pilot manifest hashes', 'repository selection IDs'],
                     'loader_supplement': 'Pinned loader reconstructs previous1200 and excludes full validation-connected groups before new allocation.',
                     'limitations': 'Only already recorded cross-dataset fingerprints are included; original GPQA parent is covered by its recorded IDs/groups. No new protected text is opened to manufacture fingerprints. Lexical exclusion is not semantic decontamination.',
                     'source_counts': counts, 'model_calls': 0}}
    validate_exposure(out)
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--audit-root', type=Path, default=Path('/var/tmp'))
    p.add_argument('--imports', type=Path, default=REPO / 'results_import')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    output = a.output.resolve()
    if any((parent / '.git').exists() for parent in (output.parent, *output.parents)):
        raise ValueError('Private inventory must remain outside every Git checkout')
    if output.exists(): raise ValueError('Refuse to replace an existing reviewed inventory')
    value = build(a.audit_root, a.imports)
    write_json(output, value)
    print(canonical({'path': str(output), 'sha256': file_hash(output), 'ledger_sha256': value['ledger_sha256'],
                     'counts': {k: len(value[k]) for k in ('task_ids', 'group_ids', 'content_groups', 'cross_dataset_fingerprints', 'source_receipts')}}))


if __name__ == '__main__': main()
