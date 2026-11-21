import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import aai_documented_policy_lock as lock
from pact.revival.allocation_v3 import runner


class PolicyLockChecks(unittest.TestCase):
    def test_lock_matches_native_team_paths_hashes_and_analysis(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keys = [f'{p}/{s}' for p in lock.training.POLICIES for s in lock.training.SEEDS]
            allocation = {'aliases': {k: k for k in keys}}
            plan = {'s0': lock.b.S0, 'analysis': {'primary': 'frozen'},
                    'parent_path': tmp, 'prospective_hash': 'sealed'}
            lock.b.save(root/'policies.json', allocation)
            jobs = [(p, s, f, []) for p in lock.training.POLICIES for s in lock.training.SEEDS for f in 'QLM']
            with patch('pact.revival.stage1.weights.tensor_inventory',
                       side_effect=lambda _, fit: ({}, {'adapter_hash': lock.b.S0[fit[-1]]})), \
                 patch.object(lock.training, 'jobs', return_value=jobs), \
                 patch.object(lock.training, 'checkpoint', side_effect=lambda path, *args:
                              ({}, {'adapter_hash_recorded': str(path)})), \
                 patch.object(runner.models, 'checkpoint_values', side_effect=lambda path: ({}, str(path))):
                runner.lock_policies(root, plan)
                expected = lock.expected_lock(root, plan, allocation)
                self.assertEqual(expected, lock.b.read(root/'policy-lock.json'))
                self.assertEqual(len(expected['teams']), 11)
                with self.assertRaises(lock.b.CheckFailed):
                    lock.expected_lock(root, {**plan, 's0': {}}, allocation)

    def test_prior_evaluation_files_stop_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock.check_evaluation_absent(root)
            for name in ('attacks/policy/a.json', 'policy_results.json', 'stages/evaluate.json'):
                path = root/name
                path.parent.mkdir(exist_ok=True, parents=True)
                path.touch()
                with self.assertRaises(lock.b.CheckFailed):
                    lock.check_evaluation_absent(root)
                path.unlink()
