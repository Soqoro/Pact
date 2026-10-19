import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from pact.revival import persistence, retention, runtime
from pact.util import write_json, read_json, file_hash


class Retention(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root, self.drive = self.base/'run', self.base/'drive'
        write_json(self.root/'plan.json', {'source': {'fixture': True}, 'storage_retention': retention.POLICY})

    def step(self, n):
        f = self.root/'training/Q/checkpoints'/f'step-{n:06d}'/'tensors.safetensors'
        f.parent.mkdir(parents=True)
        f.write_bytes(bytes([n])*1024)
        write_json(f.parent/'metadata.json', {'step': n})
        return f

    def test_long_sequence_bounded_tensors_and_restore(self):
        initial = self.step(0)
        persistence.persist_files(self.root, self.drive)
        epoch = None
        for n in range(1, 21):
            f = self.step(n)
            if n == 8:
                write_json(self.root/'training/Q/epoch1.json', {'step': n})
                epoch = f
            persistence.persist_files(self.root, self.drive)
        idx = read_json(sorted((self.drive/'snapshots').iterdir())[-1]/'index.json')
        self.assertTrue((self.drive/'objects'/file_hash(initial)).exists())
        self.assertTrue((self.drive/'objects'/file_hash(epoch)).exists())
        # Initial + epoch + previous + latest, regardless of total update count.
        tensors = [x for x in (self.drive/'objects').iterdir() if x.stat().st_size == 1024]
        self.assertEqual(len(tensors), 4)
        self.assertEqual(len(list((self.drive/'snapshots').iterdir())), 21)
        runtime.restore_latest(self.drive, self.base/'restored')
        self.assertEqual(file_hash(self.base/'restored/training/Q/checkpoints/step-000020/tensors.safetensors'), file_hash(f))
        self.assertTrue((self.base/'restored/training/Q/checkpoints/step-000001/metadata.json').exists())
        self.assertFalse((self.base/'restored/training/Q/checkpoints/step-000001/tensors.safetensors').exists())

    def test_unknown_objects_and_shared_metadata_protected(self):
        f = self.step(0)
        persistence.persist_files(self.root, self.drive)
        unknown = self.drive/'objects'/('f'*64)
        unknown.write_bytes(b'unknown evidence')
        one = self.step(1)
        # This byte identity is also non-tensor metadata: never prune it.
        (self.root/'evidence.bin').write_bytes(one.read_bytes())
        for n in range(1,5):
            if n > 1:self.step(n)
            persistence.persist_files(self.root, self.drive)
        self.assertTrue(unknown.exists())
        self.assertTrue((self.drive/'objects'/file_hash(one)).exists())

    def test_interrupted_pruning_blocks_restore_and_retry(self):
        for n in range(3):
            self.step(n); persistence.persist_files(self.root, self.drive)
        self.step(3)
        original = Path.unlink
        def fail(path, *a, **kw):
            if path.parent == self.drive/'objects':raise OSError('simulated deletion failure')
            return original(path, *a, **kw)
        with patch.object(Path, 'unlink', fail):
            with self.assertRaisesRegex(OSError, 'deletion'):
                persistence.persist_files(self.root, self.drive)
        with self.assertRaisesRegex(ValueError, 'Unfinished'):
            runtime.restore_latest(self.drive, self.base/'restored')
        with self.assertRaisesRegex(ValueError, 'Unfinished'):
            persistence.persist_files(self.root, self.drive)

    def test_missing_old_object_is_not_inferred_as_pruned(self):
        for n in range(3):
            self.step(n); persistence.persist_files(self.root, self.drive)
        first = read_json(sorted((self.drive/'snapshots').iterdir())[0]/'index.json')
        (self.drive/'objects'/first['files']['recovery.json']).unlink()
        self.step(3)
        with self.assertRaises((ValueError, OSError)):
            persistence.persist_files(self.root, self.drive)
        self.assertTrue((self.drive/'SNAPSHOT_PENDING.json').exists())

    def test_policy_change_rejected(self):
        self.step(0); persistence.persist_files(self.root, self.drive)
        plan = read_json(self.root/'plan.json')
        plan['storage_retention']['keep_latest_snapshots'] = 1
        write_json(self.root/'plan.json', plan)
        with self.assertRaises(ValueError):persistence.persist_files(self.root, self.drive)

    def test_unsafe_latest_is_preserved_not_made_resumable(self):
        for n in range(3):
            self.step(n); persistence.persist_files(self.root, self.drive)
        f = self.step(3)
        write_json(self.root/'intents/unresolved.json', {'work_id': 'unresolved'})
        persistence.persist_files(self.root, self.drive)
        self.assertTrue((self.drive/'objects'/file_hash(f)).exists())
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            runtime.restore_latest(self.drive, self.base/'restored')

    def test_replacement_builder_rejects_unreviewed_bundle(self):
        from pact.revival.replacement_review import proposal
        bundle = self.base/'wrong.zip'
        bundle.write_bytes(b'not the audited bank')
        with self.assertRaisesRegex(ValueError, 'Exact reviewed'):
            proposal(bundle)

    def test_local_tensors_pruned_only_after_durable_success(self):
        self.step(0)
        for n in range(1,5):self.step(n)
        with patch.object(persistence,'_sync_run',side_effect=OSError('copy failed')):
            with self.assertRaises(OSError):persistence.persist_files(self.root,self.drive)
        self.assertTrue((self.root/'training/Q/checkpoints/step-000001/tensors.safetensors').exists())
        # Independent successful store used only by this fixture.
        runtime.checkpoint(self.root,self.base/'good-drive')
        self.assertFalse((self.root/'training/Q/checkpoints/step-000001/tensors.safetensors').exists())
        self.assertTrue((self.root/'training/Q/checkpoints/step-000003/tensors.safetensors').exists())
        self.assertTrue((self.root/'training/Q/checkpoints/step-000004/tensors.safetensors').exists())
