import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pact.revival import persistence, retention
from pact.util import write_json, read_json, digest, file_hash


class Transactions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)/'run'
        self.drive = Path(self.tmp.name)/'drive'
        write_json(self.root/'plan.json', {'source': {'fixture': True}})
        self.fit = self.root/'training/independent_adversarial_sft/Q'
        write_json(self.fit/'contract.json', {'test': True})
        write_json(self.fit/'update_attempt.json', {'step': 1, 'contract_hash': digest({'test': True})})
        self.boundary = dict(phase='pre_update', step=1, arm='independent_adversarial_sft', family='Q')

    def test_failed_pre_and_post_have_distinct_evidence(self):
        for phase, committed in [('pre_update', 0), ('post_update', 1)]:
            with self.subTest(phase=phase):
                write_json(self.fit/'status.json', {'completed_steps': committed})
                drive = self.drive/phase
                with patch.object(persistence, '_sync_run', side_effect=OSError('interrupted')):
                    with self.assertRaises(OSError):
                        persistence.persist_files(self.root, drive, boundary={**self.boundary, 'phase': phase})
                marker = read_json(drive/'SNAPSHOT_PENDING.json')
                self.assertEqual(marker['boundary']['phase'], phase)
                self.assertEqual(marker['boundary']['committed_steps'], committed)
                self.assertEqual(marker['boundary']['status_sha256'], file_hash(self.fit/'status.json'))
                with self.assertRaisesRegex(ValueError, 'Unfinished'):
                    persistence.persist_files(self.root, drive)

    def test_completion_binds_index_and_has_unique_transaction(self):
        # Do not infer resume eligibility from transaction completion.
        for _ in range(2):persistence.persist_files(self.root, self.drive, boundary=self.boundary)
        records = list((self.drive/'transactions').glob('*.json'))
        self.assertEqual(len(records), 2)
        for p in records:
            r = read_json(p)
            self.assertFalse(r['recovery_safe'])
            self.assertEqual(r['index_sha256'], file_hash(self.drive/'snapshots'/r['snapshot']/'index.json'))
        self.assertFalse((self.drive/'SNAPSHOT_PENDING.json').exists())

    def test_boundary_mismatch_rejected_before_pending(self):
        with self.assertRaises(ValueError):
            persistence.persist_files(self.root, self.drive, boundary={**self.boundary, 'phase':'post_update'})
        self.assertFalse((self.drive/'SNAPSHOT_PENDING.json').exists())

    def test_completion_write_failure_keeps_marker(self):
        original = persistence.write_json
        def fail(path, value):
            if path.parent.name == 'transactions':raise OSError('completion failed')
            return original(path, value)
        with patch.object(persistence, 'write_json', fail):
            with self.assertRaises(OSError):persistence.persist_files(self.root, self.drive, boundary=self.boundary)
        self.assertTrue((self.drive/'SNAPSHOT_PENDING.json').exists())

    def test_retention_hashes_each_object_once_per_invocation(self):
        # Remove synthetic unresolved training state for this independent fixture.
        write_json(self.root/'plan.json', {'source': {'fixture': True}, 'storage_retention': retention.POLICY})
        for _ in range(4):persistence.persist_files(self.root, self.drive)
        hashes = []
        original = retention.file_hash
        def record(path):
            if path.parent.name == 'objects':hashes.append(path.name)
            return original(path)
        with patch.object(retention, 'file_hash', record):
            retention.retention_plan(self.drive, digest(read_json(self.root/'plan.json')))
        self.assertEqual(len(hashes), len(set(hashes)))
        # Cache does not survive this invocation: corruption must still fail.
        obj = self.drive/'objects'/hashes[0]
        obj.write_bytes(b'corrupt')
        with self.assertRaises((ValueError, OSError)):
            retention.retention_plan(self.drive, digest(read_json(self.root/'plan.json')))

class NeuralBoundary(unittest.TestCase):
    def test_pre_failure_prevents_forward_and_post_failure_preserves_checkpoint(self):
        try:
            import torch, safetensors
        except ImportError:
            self.skipTest('Optional local torch/safetensors required')
        from pact.revival import neural
        from pact.revival.mock import model, Tokenizer
        torch.set_num_threads(1)
        target = neural.prefix_target(Tokenizer(), 'fixture:', 'A', ['A'])
        groups = [{'task_id':'fixture', 'contexts':[{'target':target,'weight':1.}]}]
        for failing_phase in ('pre_update', 'post_update'):
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                m = model(); neural.attach(m)
                seen = []
                def boundary(phase, step):
                    seen.append((phase, step))
                    if phase == failing_phase:raise OSError('boundary interruption')
                with patch.object(neural, 'loss', wraps=neural.loss) as loss:
                    with self.assertRaises(OSError):
                        neural.train(m, groups, root, {'family':'fixture'}, epochs=1,
                                     batch=1, boundary_callback=boundary)
                    self.assertEqual(loss.call_count, 0 if failing_phase=='pre_update' else 1)
                self.assertEqual(read_json(root/'update_attempt.json')['step'], 1)
                if failing_phase == 'post_update':
                    self.assertEqual(read_json(root/'status.json')['completed_steps'], 1)
                    self.assertTrue((root/'checkpoints/step-000001/checksums.json').exists())
                    self.assertEqual(seen, [('pre_update',1),('post_update',1)])
                else:
                    self.assertFalse((root/'status.json').exists())
                    self.assertEqual(seen, [('pre_update',1)])
