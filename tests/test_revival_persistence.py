import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pact.revival import persistence as p, runtime
from pact.util import write_json, read_json, file_hash


class Persistence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base/'run'
        self.drive = self.base/'drive'
        write_json(self.root/'plan.json', {'source': {'fixture': True}})
        (self.root/'fixed.bin').write_bytes(b'fixed tensor stand-in' * 100)

    def test_dedup_roundtrip_and_repeated_checkpoint(self):
        p.persist_files(self.root, self.drive)
        first = {x.name for x in (self.drive/'objects').iterdir()}
        p.persist_files(self.root, self.drive)
        self.assertEqual(first, {x.name for x in (self.drive/'objects').iterdir()})
        write_json(self.root/'status.json', {'step': 1})
        p.persist_files(self.root, self.drive)
        self.assertEqual(len(list((self.drive/'objects').iterdir())), len(first)+2)
        restored = self.base/'restored'
        runtime.restore_latest(self.drive, restored)
        self.assertEqual(read_json(restored/'status.json'), {'step': 1})
        self.assertEqual(file_hash(restored/'fixed.bin'), file_hash(self.root/'fixed.bin'))
        self.assertFalse(list(self.drive.rglob('state.zip')))

    def test_capacity_stops_before_copy_and_blocks_fallback(self):
        p.persist_files(self.root, self.drive)
        before = {x.name: file_hash(x) for x in (self.drive/'objects').iterdir()}
        write_json(self.root/'status.json', {'step': 2})
        with patch.object(p, 'MAX_OBJECT_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'capacity'):
                p.persist_files(self.root, self.drive)
        self.assertEqual(before, {x.name: file_hash(x) for x in (self.drive/'objects').iterdir()})
        with self.assertRaisesRegex(ValueError, 'Unfinished'):
            runtime.restore_latest(self.drive, self.base/'restored')
        with self.assertRaisesRegex(ValueError, 'Unfinished'):
            p.persist_files(self.root, self.drive)

    def test_failed_copy_preserves_pending(self):
        with patch.object(p, '_sync_run', side_effect=OSError('mount failed')):
            with self.assertRaises(OSError):
                p.persist_files(self.root, self.drive)
        self.assertTrue((self.drive/'SNAPSHOT_PENDING.json').exists())

    def test_unresolved_optimizer_stays_unsafe(self):
        write_json(self.root/'training/Q/update_attempt.json', {'step': 1})
        p.persist_files(self.root, self.drive)
        with self.assertRaisesRegex(ValueError, 'unsafe'):
            runtime.restore_latest(self.drive, self.base/'restored')
        self.assertFalse((self.base/'restored').exists())

    def test_missing_newest_object_and_incomplete_directory_do_not_fallback(self):
        p.persist_files(self.root, self.drive)
        (self.drive/'objects'/file_hash(self.root/'fixed.bin')).unlink()
        with self.assertRaises((ValueError, OSError)):
            runtime.restore_latest(self.drive, self.base/'restored')
        with self.assertRaises((ValueError, OSError)):
            p.persist_files(self.root, self.drive)
        (self.drive/'snapshots'/'9999999999999999999-empty').mkdir()
        with self.assertRaises((ValueError, OSError)):
            runtime.restore_latest(self.drive, self.base/'restored')

    def test_legacy_restore_but_no_implicit_migration(self):
        from pact.artifacts import _sync_run
        from pact.util import digest
        stage = self.base/'legacy'
        r = runtime.package(self.root, stage/'state.zip', weights=True)
        write_json(stage/'receipt.json', {'sha256': r['sha256'], 'recovery_safe': True,
                                         'plan_hash': digest(read_json(self.root/'plan.json'))})
        _sync_run(stage, self.drive)
        runtime.restore_latest(self.drive, self.base/'restored')
        with self.assertRaisesRegex(ValueError, 'migration'):
            p.persist_files(self.root, self.drive)

    def test_symlink_rejected(self):
        (self.root/'link').symlink_to(self.root/'fixed.bin')
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            p.persist_files(self.root, self.drive)

    def test_worker_roundtrip(self):
        runtime.checkpoint(self.root, self.drive)
        runtime.restore_latest(self.drive, self.base/'restored')
        self.assertTrue((self.base/'restored'/'fixed.bin').exists())

    def test_changed_plan_cannot_overwrite_history(self):
        p.persist_files(self.root, self.drive)
        write_json(self.root/'plan.json', {'source': {'fixture': True}, 'changed': True})
        with self.assertRaisesRegex(ValueError, 'plan mismatch'):
            p.persist_files(self.root, self.drive)

    def test_generation_and_scoring_intents_remain_unsafe(self):
        for directory in ('intents', 'score_intents'):
            with self.subTest(directory=directory):
                intent = self.root/directory/'unfinished.json'
                write_json(intent, {'work_id': 'unfinished'})
                p.persist_files(self.root, self.drive)
                with self.assertRaisesRegex(ValueError, 'unsafe'):
                    runtime.restore_latest(self.drive, self.base/'restored')
                intent.unlink()

    def test_completed_marker_interruption_blocks_restore(self):
        from pact.artifacts import _sync_run
        def interrupted(source, dest, **kw):
            return _sync_run(source, dest, interrupt_before_marker=True, **kw)
        with patch.object(p, '_sync_run', side_effect=interrupted):
            with self.assertRaises(InterruptedError):
                p.persist_files(self.root, self.drive)
        with self.assertRaisesRegex(ValueError, 'Unfinished'):
            runtime.restore_latest(self.drive, self.base/'restored')
