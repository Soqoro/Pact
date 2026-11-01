"""Invented identifiers only; no sources, model, network or scheduler calls."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from pact.util import digest, write_json, read_json, file_hash

spec = importlib.util.spec_from_file_location('reconcile', Path(__file__).resolve().parents[1] / 'tools/aai_stage2_exposure_reconcile.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class ReconciliationTests(unittest.TestCase):
    def data(self):
        old = {key: ['private-old-' + key] for key in r.FIELDS}
        old['source_receipts'] = [{'name': 'private-receipt', 'sha256': 'a' * 64}]
        old['reviewed_complete'] = True
        source = {'exposure': {key: ['private-inherited-' + key] for key in r.FIELDS},
                  'records': [{'task': {'task_id': 'private-task'}, 'group_id': 'private-group',
                               'content_group': 'private-content', 'cross_dataset_fingerprint': 'private-fingerprint'}]}
        history = [{'manifest': {'selected_ids': ['private-selected'], 'protected_ids': ['private-locked'],
                    'excluded_ids': ['private-invalid'], 'group_by_id': {'private-locked': 'private-gpqa-group'}}}]
        return old, source, history

    def test_monotone_deduplicated_union_without_mutation(self):
        old, source, history = self.data()
        original = copy.deepcopy((old, source, history))
        union, counts = r.union_evidence(old, source, history, [{'task_id': 'private-task'}])
        for key in r.FIELDS:
            self.assertTrue(set(old[key]) <= set(union[key]))
            self.assertTrue(set(source['exposure'][key]) <= set(union[key]))
        self.assertTrue({'private-locked', 'private-invalid'} <= set(union['task_ids']))
        self.assertEqual(counts['incremental_additions']['repository_selections']['task_ids'], 0)
        self.assertEqual(original, (old, source, history))

    def test_invalid_identity_fails(self):
        old, source, history = self.data()
        source['records'][0]['group_id'] = ['not a string']
        with self.assertRaises(ValueError):
            r.union_evidence(old, source, history, [])

    def test_audit_tamper_and_config_binding(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {'run_dir': str(root)}
            for name, value in {'source.private.json': {}, 'lineage.private.json': {},
                                'audit.private.json': {'fixture': False}}.items():
                write_json(root / name, value)
            write_json(root / 'manifest.json', {p.name: file_hash(p) for p in root.glob('*.private.json')})
            write_json(root / 'audit-input.json', {'sha256': digest(cfg)})
            self.assertEqual(r.verified_audit(root, cfg), ({}, {}))
            with self.assertRaises(ValueError):
                r.verified_audit(root, {**cfg, 'changed': True})
            write_json(root / 'source.private.json', {'altered': True})
            with self.assertRaises(ValueError):
                r.verified_audit(root, cfg)

    def test_private_draft_cannot_certify_and_summary_has_no_identifiers(self):
        old, source, historical = self.data()
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'docs').mkdir()
            (base / 'experiments').mkdir()
            (base / 'docs/experiment_ledger.md').write_text('invented ledger')
            (base / 'ledger.md').write_text('invented exposure ledger')
            cfg = {'run_dir': str(base / 'audit'), 'parent_dir': str(base / 'parent'),
                   'exposure': str(base / 'old.json'), 'inventory': str(base / 'inventory.json')}
            write_json(base / 'config.json', cfg)
            write_json(base / 'old.json', old)
            write_json(base / 'inventory.json', {'files': [{'sha256': 'a' * 64}]})
            (base / 'audit').mkdir()
            write_json(base / 'audit/manifest.json', {})
            before = {p: p.read_bytes() for p in base.rglob('*') if p.is_file()}
            lineage = {'S0': {'Q': 'fixture'}, 'local_history_conflicts': []}
            with patch.object(r, 'verified_audit', return_value=(source, lineage)), \
                 patch.object(r.parent_review, 'lineage', return_value=(source, lineage)), \
                 patch.object(r.evidence, 'EXECUTED_SOURCE_HASH', digest(source)), \
                 patch.object(r, 'validate_exposure'), \
                 patch.object(r.review, 'history_files', return_value=(historical, True)), \
                 patch.object(r, 'REPO', base), patch.object(r, 'LEDGER', base / 'ledger.md'), \
                 patch.object(r.sources, 'private_path', side_effect=Path):
                summary = r.build(base / 'config.json', base / 'output')
                with self.assertRaises(FileExistsError):
                    r.build(base / 'config.json', base / 'output')
            draft = read_json(base / 'output/reconciliation.private.json')
            self.assertFalse(draft['reviewed_complete'])
            self.assertNotIn('coverage', draft)
            self.assertNotIn('task_ids', draft)  # Not accepted exposure-file schema.
            self.assertFalse(summary['eligibility_certified'])
            self.assertIsNone(summary['remaining_budget'])
            self.assertNotIn('private-task', json.dumps(summary))
            self.assertNotIn('private-receipt', json.dumps(summary))
            self.assertEqual(before, {p: p.read_bytes() for p in before})
            for name, sha in read_json(base / 'output/checksums.json').items():
                self.assertEqual(sha, file_hash(base / 'output' / name))


if __name__ == '__main__':
    unittest.main()
