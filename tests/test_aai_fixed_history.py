"""CPU guards for the AAI entry point. No model imports or network."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
try:
    spec = importlib.util.spec_from_file_location('fixed_history', TOOLS / 'aai_fixed_history.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
finally:
    sys.path.pop(0)


class FixedHistoryEntryTests(unittest.TestCase):
    def test_exact_single_stage_command(self):
        cmd = m.invocation(Path('/run'), Path('/durable'), Path('/cache'))
        self.assertEqual(cmd[cmd.index('-m') + 1:cmd.index('--run-dir')],
                         ['pact.revival.stage1', 'fixed_history'])
        self.assertEqual(cmd[-2:], ['--plan-hash', m.transport.PLAN])
        self.assertNotIn('--mock', cmd)
        self.assertIn('--execute', cmd)

    def test_token_permissions_and_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'token'
            p.write_text('fixture-token\n')
            p.chmod(0o600)
            self.assertEqual(m.load_token(p), 'fixture-token')
            p.chmod(0o644)
            with self.assertRaisesRegex(ValueError, 'private'):
                m.load_token(p)
            alias = Path(tmp) / 'alias'
            alias.symlink_to(p)
            with self.assertRaisesRegex(ValueError, 'Symlink'):
                m.load_token(alias)

    def test_changed_plan_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'plan.json').write_text('{}')
            with self.assertRaisesRegex(ValueError, 'Plan changed'):
                m.boundary(root)

    def test_completed_fixed_history_cannot_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'plan.json').write_text('{}')
            (root / 'contract_resolution.json').write_text('{}')
            (root / 'stages').mkdir()
            for stage in ('smoke', 'validation', 'source_evaluation'):
                (root / 'stages' / (stage + '.json')).write_text(json.dumps({
                    'execution_complete': True, 'fixture': False, 'plan_hash': m.transport.PLAN}))
            (root / 'stages/fixed_history.json').write_text('{}')
            with patch.object(m.transport, 'digest', side_effect=[m.transport.PLAN, m.transport.RESOLUTION]):
                with self.assertRaisesRegex(ValueError, 'already recorded'):
                    m.boundary(root)


if __name__ == '__main__':
    unittest.main()
