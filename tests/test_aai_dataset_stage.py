"""Local filesystem checks for private AAI copies; no cluster/data access."""
import hashlib
import importlib.util
import os
from pathlib import Path
import stat
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1] / 'tools'
sys.path.insert(0, str(TOOLS))
try:
    spec = importlib.util.spec_from_file_location('dataset_stage', TOOLS / 'aai_dataset_stage.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
finally:
    sys.path.pop(0)


class DatasetCopyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.write_bytes(b'private fixture')
        self.sha = hashlib.sha256(self.source.read_bytes()).hexdigest()
        self.oldmask = os.umask(0o077)
        self.addCleanup(os.umask, self.oldmask)

    def test_private_copy_preserves_source(self):
        dest = self.root / 'private/copy'
        module.write_copy(self.source, dest, self.sha)
        self.assertEqual(dest.read_bytes(), self.source.read_bytes())
        self.assertEqual(stat.S_IMODE(dest.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(dest.parent.stat().st_mode), 0o700)

    def test_existing_copy_not_overwritten(self):
        dest = self.root / 'copy'
        dest.write_bytes(b'original')
        with self.assertRaises(FileExistsError):
            module.write_copy(self.source, dest, self.sha)
        self.assertEqual(dest.read_bytes(), b'original')

    def test_corruption_rejected(self):
        with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
            module.write_copy(self.source, self.root / 'bad', '0' * 64)
        self.assertEqual(self.source.read_bytes(), b'private fixture')

    def test_symlink_parent_rejected(self):
        (self.root / 'alias').symlink_to(self.root, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'Symlink'):
            module.write_copy(self.source, self.root / 'alias/copy', self.sha)
        self.assertFalse((self.root / 'copy').exists())


if __name__ == '__main__':
    unittest.main()
