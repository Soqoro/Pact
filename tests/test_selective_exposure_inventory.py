"""Fictional metadata-only inventory validation; no benchmark data needed."""
import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest

from pact.util import digest, write_json

spec = importlib.util.spec_from_file_location('exposure_builder', Path(__file__).resolve().parents[1] / 'tools/build_selective_exposure_inventory.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class InventoryTests(unittest.TestCase):
    def test_new_ledger_cannot_recertify_old_scope(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'ledger.md'; path.write_text('newly executed cohort')
            with patch.object(builder, 'LEDGER', path):
                with self.assertRaisesRegex(ValueError, 'ledger advanced'):
                    builder.build(Path(d), Path(d))

    def manifest(self):
        return {'training_allowed': False, 'source_rows': 3,
                'group_by_id': {'a': 'x', 'b': 'y', 'c': 'z'},
                'group_members': {'x': ['a'], 'y': ['b'], 'z': ['c']},
                'cross_dataset_fingerprints': {'a': '1', 'b': '2', 'c': '3'},
                'variant_partition_by_id': {'a': 'characterization_dev', 'b': 'confirmation_locked', 'c': 'reserve_locked'},
                'partitions': {'characterization_dev': ['a'], 'confirmation_locked': ['b'], 'reserve_locked': ['c']}}

    def test_all_partitions_and_siblings_required(self):
        builder.validate_manifest(self.manifest())
        for field in ('group_members', 'cross_dataset_fingerprints', 'variant_partition_by_id'):
            m = self.manifest(); m[field].pop(next(iter(m[field])))
            with self.assertRaises(ValueError): builder.validate_manifest(m)
        m = self.manifest(); m['partitions']['reserve_locked'].append('a')
        with self.assertRaises(ValueError): builder.validate_manifest(m)

    def test_plan_hash_and_metadata_binding(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); m = self.manifest(); plan = {'manifest': m, 'fixture': True}
            write_json(root / 'plan.json', plan)
            write_json(root / 'dataset_group_exposure_manifest.json', m)
            self.assertEqual(builder.verified_manifest(root, digest(plan)), m)
            with self.assertRaises(ValueError): builder.verified_manifest(root, '0' * 64)
            changed = copy.deepcopy(m); changed['cross_dataset_fingerprints']['a'] = 'tampered'
            write_json(root / 'dataset_group_exposure_manifest.json', changed)
            with self.assertRaisesRegex(ValueError, 'not bound'): builder.verified_manifest(root, digest(plan))

    def test_no_plan_text_json_parsing(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); m = self.manifest(); plan = {'manifest': m, 'unparsed_payload': 'fictional task text'}
            write_json(root / 'plan.json', plan)
            write_json(root / 'dataset_group_exposure_manifest.json', m)
            reader = builder.read_json
            def metadata_only(path):
                self.assertEqual(Path(path).name, 'dataset_group_exposure_manifest.json')
                return reader(path)
            with patch.object(builder, 'read_json', side_effect=metadata_only):
                self.assertEqual(builder.verified_manifest(root, digest(plan)), m)
