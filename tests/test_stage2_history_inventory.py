import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('history', Path(__file__).resolve().parents[1]/'tools/stage2_history_inventory.py')
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


class HistoryTests(unittest.TestCase):
    def test_prompt_strings_are_not_execution_signals(self):
        self.assertFalse(h.identity_signal({'request': {'owner': 'pact-stage2-fake'}, 'text': 'budget_stage II'}))
        self.assertTrue(h.identity_signal({'identity': {'budget_stage': 'II'}}))
        self.assertTrue(h.identity_signal({'intent': {'identity': {'owner': 'pact-update-allocation-fixture'}}}))

    def test_metadata_discovery_privacy_and_preservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'intents').mkdir()
            attempt = root/'intents/private-id.json'
            attempt.write_text(json.dumps({'identity': {'budget_stage': 'II'}, 'prompt': 'SECRET_FIXTURE'}))
            child = root/'pact-stage2-fixture'
            child.mkdir()
            (child/'plan.json').write_text('{}')
            (child/'private.zip').write_bytes(b'archive not opened')
            before = {p: p.read_bytes() for p in root.rglob('*') if p.is_file()}
            private, public = h.inspect([root])
            self.assertEqual(public['candidate_counts']['possible_attempt_record'], 1)
            self.assertEqual(public['candidate_counts']['plan_only_not_execution_proof'], 1)
            self.assertEqual(public['counts']['archives_not_opened'], 1)
            self.assertNotIn('SECRET_FIXTURE', json.dumps(private))
            self.assertNotIn('private-id', json.dumps(public))
            self.assertIsNone(public['spent_budget'])
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_limits_missing_roots_and_unreadable_json_are_gaps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'plan.json').write_text('not json')
            (root/'cache').mkdir()
            (root/'cache/plan.json').write_text('{}')
            _, public = h.inspect([root, root/'absent'])
            self.assertEqual(public['gap_counts']['root_missing_or_symlink'], 1)
            self.assertEqual(public['gap_counts']['metadata_read_or_parse_failed'], 1)
            self.assertEqual(public['gap_counts']['directory_not_inspected'], 1)
            _, limited = h.inspect([root], max_files=0)
            self.assertEqual(limited['gap_counts']['global_limit_reached'], 1)

    def test_symlinks_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'plan.json').symlink_to('/does/not/exist')
            _, public = h.inspect([root])
            self.assertEqual(public['gap_counts']['file_symlink_not_followed'], 1)


if __name__ == '__main__':
    unittest.main()
